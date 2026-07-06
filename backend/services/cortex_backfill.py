"""CORTEX historical backfill + walk-forward validation ("time machine").

CORRECTED TARGET (2026-07-03, per user): this is NOT next-day and NOT the cash
open->close. Agents decide at an INTRADAY moment T (NY open 09:30 / 10:00 /
11:00 ET) and we predict the FORWARD net direction from T over a horizon that
spans the rest of the NY session AND the following overnight (Asia + Europe):
  * +6h  — next ~6 hours (rest of session momentum)
  * +24h — to the same time next trading day (through Asia/Europe overnight)

Because the horizon crosses hours when NDX cash is closed, BOTH the outcome and
the intraday situation are measured on continuous NQ futures (the user's 5m
file). We test every (decision_time x horizon) combo to see which the analog
memory actually predicts — this also answers the original "best run-hour" goal.

LEAK RULES (enforced + tested):
  * situation at T uses only daily series <= D-1 and NQ bars with et <= T.
  * outcome (NQ close at T+H vs at T) never feeds the situation.
  * walk-forward: predicting (D,T) consults only earlier same-T episodes.

TIMEZONE: the NQ file mixes conventions across its span; each month's UTC
offset is solved from twin volume anchors (09:30 open + 16:00 close spikes);
ambiguous months are dropped. Only ~2019-2024 has NQ, so the forward target is
validated on that window (~1250 trading days x 3 decision times).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

import pandas as pd

from services.cortex_memory import _vix_regime   # single source of truth

logger = logging.getLogger(__name__)

DATA = {
    "ndx_daily": "/Users/melihcanodacioglu/Desktop/nasdaq/nasdaq100_2010_2024_daily.csv",
    "vix_daily": "/Users/melihcanodacioglu/Desktop/XAUUSDDATA/fundamental/vix-daily.csv",
    "dxy_daily": "/Users/melihcanodacioglu/Desktop/nasdaq/fundamental/DXY.csv",
    "us10y_daily": "/Users/melihcanodacioglu/Desktop/nasdaq/fundamental/DGS10.csv",
    "nq_5m": "/Users/melihcanodacioglu/Desktop/nasdaq/NQ_5Years_8_11_2024.csv",
}

DECISION_TIMES = {"0930": 9 * 60 + 30, "1000": 10 * 60, "1100": 11 * 60}  # ET minutes
HORIZONS_MIN = {"6h": 6 * 60}          # 24h handled specially (next trading day, same T)
_FLAT = {"6h": 0.10, "24h": 0.20}       # % flat band per horizon
_OFFSET_CANDIDATES = list(range(-6, 7))

# Forward-target distance weights (self-contained — validate before touching live).
_FWD_W = {"vix_regime": 2.0, "market_regime": 1.5, "overnight_change": 2.0,
          "first_hour_move": 1.5, "prior_day_dir": 1.0, "vix_chg": 0.8,
          "us10y_chg": 0.8, "dxy_chg": 0.6, "range_position": 0.8, "day_of_week": 0.5}
_FWD_SCALE = {"overnight_change": 0.8, "first_hour_move": 0.6, "vix_chg": 8.0,
              "us10y_chg": 3.0, "dxy_chg": 0.5, "range_position": 0.5}
_FWD_CAT = {"vix_regime", "market_regime", "prior_day_dir", "day_of_week"}


# ── Daily loaders ─────────────────────────────────────────────────────────────
def load_ndx_daily(path=None):
    df = pd.read_csv(path or DATA["ndx_daily"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df.set_index("Date")[["Open", "High", "Low", "Close"]].sort_index()


def load_vix_daily(path=None):
    df = pd.read_csv(path or DATA["vix_daily"])
    df.columns = [c.strip().upper() for c in df.columns]
    dcol = "OBSERVATION_DATE" if "OBSERVATION_DATE" in df.columns else df.columns[0]
    df[dcol] = pd.to_datetime(df[dcol], format="%m/%d/%Y", errors="coerce")
    df = df.dropna(subset=[dcol])
    s = pd.to_numeric(df["CLOSE"], errors="coerce"); s.index = df[dcol].dt.date
    return s.dropna().sort_index()


def load_dxy_daily(path=None):
    df = pd.read_csv(path or DATA["dxy_daily"])
    df.columns = [c.strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip(), format="%m/%d/%y", errors="coerce")
    df = df.dropna(subset=["Date"])
    s = pd.to_numeric(df["Close"], errors="coerce"); s.index = df["Date"].dt.date
    return s.dropna().sort_index()


def load_us10y_daily(path=None):
    df = pd.read_csv(path or DATA["us10y_daily"])
    df.columns = [c.strip() for c in df.columns]
    dcol, vcol = df.columns[0], df.columns[-1]
    df[dcol] = pd.to_datetime(df[dcol], errors="coerce")
    s = pd.to_numeric(df[vcol], errors="coerce"); s.index = df[dcol].dt.date
    return s.dropna().sort_index()


# ── NQ load + per-month TZ solving ────────────────────────────────────────────
def load_nq_5m(path=None):
    df = pd.read_csv(path or DATA["nq_5m"])
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y %H:%M")
    return df.sort_values("Time").reset_index(drop=True)


def _month_offset_score(g, utc_off):
    import numpy as np
    from zoneinfo import ZoneInfo
    utc = g["Time"] - pd.Timedelta(hours=utc_off)
    et = utc.dt.tz_localize("UTC").dt.tz_convert(ZoneInfo("America/New_York"))
    mod = et.dt.hour * 60 + et.dt.minute
    vol = g["Volume"].to_numpy(dtype=float); total = vol.sum() or 1.0
    return (vol[np.isin(mod, [570, 575, 580])].sum() + vol[np.isin(mod, [955, 960, 965])].sum()) / total


def solve_monthly_offsets(nq):
    out = {}
    for month, g in nq.groupby(nq["Time"].dt.strftime("%Y-%m")):
        if len(g) < 500:
            out[month] = None; continue
        ranked = sorted({k: _month_offset_score(g, k) for k in _OFFSET_CANDIDATES}.items(),
                        key=lambda kv: kv[1], reverse=True)
        best, second = ranked[0], ranked[1]
        out[month] = best[0] if (second[1] == 0 or best[1] / max(second[1], 1e-9) >= 1.25) else None
    return out


def nq_to_et(nq, offsets):
    from zoneinfo import ZoneInfo
    frames = []
    for month, g in nq.groupby(nq["Time"].dt.strftime("%Y-%m")):
        off = offsets.get(month)
        if off is None:
            continue
        utc = g["Time"] - pd.Timedelta(hours=off)
        g = g.copy()
        g["et"] = utc.dt.tz_localize("UTC").dt.tz_convert(ZoneInfo("America/New_York"))
        frames.append(g)
    if not frames:
        return pd.DataFrame(columns=["et", "Close"])
    return pd.concat(frames).sort_values("et").reset_index(drop=True)[["et", "Open", "High", "Low", "Close", "Volume"]]


# ── NQ intraday lookup (O(1) after one-time day index) ────────────────────────
def _day_index(nq_et):
    if "cortex_by_day" not in nq_et.attrs:
        d = nq_et["et"].dt.date.to_numpy()
        mod = (nq_et["et"].dt.hour * 60 + nq_et["et"].dt.minute).to_numpy()
        close = nq_et["Close"].to_numpy(dtype=float)
        idx = {}
        for day_val in pd.unique(d):
            m = d == day_val
            idx[day_val] = (mod[m], close[m])
        nq_et.attrs["cortex_by_day"] = idx
    return nq_et.attrs["cortex_by_day"]


def nq_close_at(nq_et, day: date, minute_of_day: int, tol_min: int = 30) -> Optional[float]:
    """Last NQ close at/just-before `minute_of_day` ET on `day` (within tol)."""
    if nq_et.empty:
        return None
    import numpy as np
    entry = _day_index(nq_et).get(day)
    if entry is None:
        return None
    mods, closes = entry
    mask = (mods <= minute_of_day) & (mods > minute_of_day - tol_min)
    return float(closes[np.where(mask)[0][-1]]) if mask.any() else None


# ── Trading calendar helpers (NDX index = trading days) ───────────────────────
def _prev_td(trading_days: list[date], day: date) -> Optional[date]:
    import bisect
    i = bisect.bisect_left(trading_days, day)
    return trading_days[i - 1] if i > 0 else None


def _next_td(trading_days: list[date], day: date) -> Optional[date]:
    import bisect
    i = bisect.bisect_right(trading_days, day)
    return trading_days[i] if i < len(trading_days) else None


# ── Daily lagged features ─────────────────────────────────────────────────────
def _lag_pct(s, day):
    past = s[s.index < day]
    if len(past) < 2 or past.iloc[-2] == 0:
        return None
    return round((past.iloc[-1] - past.iloc[-2]) / past.iloc[-2] * 100.0, 3)


def _last_before(s, day):
    past = s[s.index < day]
    return float(past.iloc[-1]) if len(past) else None


def market_regime_approx(ndx, day):
    past = ndx[ndx.index < day]
    if len(past) < 60:
        return None
    close = past["Close"]
    ema20, ema50, c = close.ewm(span=20).mean().iloc[-1], close.ewm(span=50).mean().iloc[-1], close.iloc[-1]
    if c > ema50 and ema20 > ema50:
        return "STRONG_TREND_UP"
    if c < ema50 and ema20 < ema50:
        return "STRONG_TREND_DOWN"
    return "RANGING"


@dataclass
class Sources:
    ndx: pd.DataFrame
    vix: pd.Series
    dxy: pd.Series
    us10y: pd.Series
    nq_et: pd.DataFrame
    trading_days: list


def load_sources() -> Sources:
    nq = load_nq_5m()
    offsets = solve_monthly_offsets(nq)
    logger.info("[backfill] NQ months resolved: %d/%d",
                sum(1 for v in offsets.values() if v is not None), len(offsets))
    ndx = load_ndx_daily()
    return Sources(ndx=ndx, vix=load_vix_daily(), dxy=load_dxy_daily(),
                   us10y=load_us10y_daily(), nq_et=nq_to_et(nq, offsets),
                   trading_days=sorted(ndx.index.tolist()))


# ── Situation @ T + forward outcomes ──────────────────────────────────────────
def _dir(pct: Optional[float], flat: float) -> Optional[str]:
    if pct is None:
        return None
    return "positive" if pct > flat else "negative" if pct < -flat else "flat"


def build_day_episodes(src: Sources, day: date) -> list[dict]:
    """Up to 3 episodes (one per decision time) for trading day D. Leak-free."""
    if day not in src.ndx.index:
        return []
    prev = _prev_td(src.trading_days, day)
    nxt = _next_td(src.trading_days, day)
    if prev is None:
        return []

    prev_close_1600 = nq_close_at(src.nq_et, prev, 16 * 60)   # yesterday cash close (NQ)
    open_0930 = nq_close_at(src.nq_et, day, 9 * 60 + 30)      # today's open (NQ)
    overnight = (round((open_0930 - prev_close_1600) / prev_close_1600 * 100, 3)
                 if (open_0930 and prev_close_1600) else None)

    # daily lagged (<= D-1)
    vix_close = _last_before(src.vix, day)
    prow = src.ndx.loc[prev]
    prior_pct = round((prow["Close"] - prow["Open"]) / prow["Open"] * 100, 3) if prow["Open"] else None
    prior_dir = ("up" if prior_pct > 0 else "down") if prior_pct is not None else None
    range_pos = None
    past5 = src.ndx[src.ndx.index < day].iloc[-5:]
    if len(past5) == 5:
        hi, lo = past5["High"].max(), past5["Low"].min()
        if hi > lo:
            range_pos = round((past5["Close"].iloc[-1] - lo) / (hi - lo), 3)
    base_sit = {
        "vix_regime": _vix_regime(vix_close), "vix_price": vix_close,
        "vix_chg": _lag_pct(src.vix, day), "dxy_chg": _lag_pct(src.dxy, day),
        "us10y_chg": _lag_pct(src.us10y, day), "market_regime": market_regime_approx(src.ndx, day),
        "prior_day_dir": prior_dir, "prior_day_change_pct": prior_pct,
        "range_position": range_pos, "day_of_week": day.weekday(),
        "overnight_change": overnight,
    }

    episodes = []
    for tlabel, tmin in DECISION_TIMES.items():
        px_T = nq_close_at(src.nq_et, day, tmin)
        if px_T is None:
            continue
        first_hour = (round((px_T - open_0930) / open_0930 * 100, 3)
                      if (open_0930 and tmin > 570) else 0.0 if open_0930 else None)
        # forward outcomes
        px_6h = nq_close_at(src.nq_et, day, tmin + HORIZONS_MIN["6h"])
        out6 = round((px_6h - px_T) / px_T * 100, 3) if px_6h else None
        px_24h = nq_close_at(src.nq_et, nxt, tmin) if nxt else None
        out24 = round((px_24h - px_T) / px_T * 100, 3) if px_24h else None

        episodes.append({
            "ny_date": day.isoformat(), "decision_time": tlabel,
            **base_sit, "first_hour_move": first_hour,
            "px_at_T": px_T,
            "out_6h_pct": out6, "out_6h_dir": _dir(out6, _FLAT["6h"]),
            "out_24h_pct": out24, "out_24h_dir": _dir(out24, _FLAT["24h"]),
        })
    return episodes


def build_all(src: Sources, start: date, end: date) -> list[dict]:
    out = []
    for d in src.trading_days:
        if start <= d <= end:
            out.extend(build_day_episodes(src, d))
    return out


# ── Distance (forward-target fields) ──────────────────────────────────────────
def distance_fwd(q: dict, c: dict) -> Optional[float]:
    num = den = 0.0
    for f, w in _FWD_W.items():
        a, b = q.get(f), c.get(f)
        if a is None or b is None:
            continue
        if f in _FWD_CAT:
            d = 0.0 if a == b else 1.0
        else:
            try:
                d = min(1.0, abs(float(a) - float(b)) / _FWD_SCALE.get(f, 1.0))
            except (TypeError, ValueError):
                continue
        num += w * d; den += w
    return (num / den) if den > 0 else None


# ── Walk-forward per (decision_time x horizon) ────────────────────────────────
def walk_forward(episodes: list[dict], horizon: str, decision_time: str,
                 k: int = 8, min_pool: int = 60) -> dict:
    dcol, pcol = f"out_{horizon}_dir", f"out_{horizon}_pct"
    eps = sorted([e for e in episodes if e["decision_time"] == decision_time
                  and e.get(dcol) is not None], key=lambda e: e["ny_date"])
    rows, ups, dirs, pool = [], 0, 0, []
    for ep in eps:
        if len(pool) >= min_pool and dirs > 20:
            prior = ups / dirs
            scored = [(distance_fwd(ep, p), p) for p in pool]
            scored = [(d, p) for d, p in scored if d is not None]
            scored.sort(key=lambda x: x[0])
            top = [p for _, p in scored[:k]]
            if top:
                up = sum(1 for p in top if p[dcol] == "positive")
                p_up = (up + 6.0 * prior) / (len(top) + 6.0)
                rows.append({"ny_date": ep["ny_date"], "p_up": p_up, "actual": ep[dcol],
                             "vix_regime": ep.get("vix_regime"),
                             "overnight_change": ep.get("overnight_change")})
        pool.append(ep)
        if ep[dcol] in ("positive", "negative"):
            dirs += 1; ups += ep[dcol] == "positive"

    d_rows = [r for r in rows if r["actual"] in ("positive", "negative")]
    n = len(d_rows)
    if n < 100:
        return {"decision_time": decision_time, "horizon": horizon, "n": n, "insufficient": True}
    up_rate = sum(1 for r in d_rows if r["actual"] == "positive") / n
    # calibration quartile spread (does p_up rank the forward direction?)
    d_rows.sort(key=lambda r: r["p_up"]); q = n // 4
    q1 = sum(1 for r in d_rows[:q] if r["actual"] == "positive") / q
    q4 = sum(1 for r in d_rows[-q:] if r["actual"] == "positive") / q
    # momentum baseline: forward continues the overnight direction sign
    mom = [r for r in d_rows if r.get("overnight_change") is not None]
    mom_hit = sum(1 for r in mom if (r["overnight_change"] > 0) == (r["actual"] == "positive"))
    return {
        "decision_time": decision_time, "horizon": horizon, "n": n,
        "base_up_rate_pct": round(up_rate * 100, 1),
        "q1_up_pct": round(q1 * 100, 1), "q4_up_pct": round(q4 * 100, 1),
        "calibration_spread_pp": round((q4 - q1) * 100, 1),
        "momentum_baseline_acc_pct": round(mom_hit / len(mom) * 100, 1) if mom else None,
    }


def run(start: str = "2019-08-12", end: str = "2024-08-09",
        out_dir: str = "research/cortex_backfill", k: int = 8) -> dict:
    import os
    src = load_sources()
    episodes = build_all(src, date.fromisoformat(start), date.fromisoformat(end))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "episodes_fwd.json"), "w") as f:
        json.dump(episodes, f)
    grid = []
    for dt in DECISION_TIMES:
        for hz in ("6h", "24h"):
            grid.append(walk_forward(episodes, hz, dt, k=k))
    with open(os.path.join(out_dir, "walkforward_fwd.json"), "w") as f:
        json.dump(grid, f, indent=2)
    return {"episodes": len(episodes),
            "days": len({e["ny_date"] for e in episodes}),
            "grid": grid}
