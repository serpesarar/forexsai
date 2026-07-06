"""Trigger detectors — primary signals of the Reflex Engine.

Every detector works on time-sorted 1m mid bars (one day at a time, with the
previous day appended as lookback context) and returns event rows:

    ts         confirm-bar timestamp (entry happens on the NEXT bar)
    direction  BUY | SELL
    family     chan_rev | vwap_rev | sr_react | sweep | orb | mom_cont
    meta_*     family-specific diagnostics (kept as features later)

Design rules:
  * detectors are parameter-light; parameters live in config.py and are frozen
    before ML training — they are NOT tuned against labels
  * events only inside EVENT_WINDOW_UTC
  * per-family refractory period suppresses double-firing on one episode
  * definitions intentionally mirror validated live logic (claude_decider
    rev_chan/rev_vwap, bot sr_zones) so evidence transfers
"""
from __future__ import annotations

import os
import sys
from datetime import date

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402


# ── shared helpers ───────────────────────────────────────────────────────────

def ny_open_utc(d: date) -> pd.Timestamp:
    """NY cash open in UTC for a 2025 date (DST-aware)."""
    h, m = (13, 30) if config.DST_2025[0] <= d < config.DST_2025[1] else (14, 30)
    return pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=h, minutes=m)


def _in_window(ts: pd.Series) -> pd.Series:
    lo, hi = config.EVENT_WINDOW_UTC
    return (ts.dt.hour >= lo) & (ts.dt.hour < hi)


def _apply_refractory(events: pd.DataFrame) -> pd.DataFrame:
    """Keep the first event per (family, direction) inside each refractory window."""
    if events.empty:
        return events
    keep = []
    last: dict[tuple[str, str], pd.Timestamp] = {}
    for _, ev in events.sort_values("ts").iterrows():
        key = (ev["family"], ev["direction"])
        prev = last.get(key)
        if prev is None or (ev["ts"] - prev) >= pd.Timedelta(minutes=config.FAMILY_REFRACTORY_MIN):
            keep.append(ev)
            last[key] = ev["ts"]
    return pd.DataFrame(keep).reset_index(drop=True)


def _rolling_linreg_z(close: pd.Series, window: int) -> pd.Series:
    """Residual z-score of price vs rolling linear-regression channel
    (claude_decider rev_chan definition: WIN_N-bar linreg, z of last residual)."""
    x = np.arange(window, dtype=float)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()

    def _z(win: np.ndarray) -> float:
        y_mean = win.mean()
        beta = ((x - x_mean) * (win - y_mean)).sum() / x_var
        resid = win - (y_mean + beta * (x - x_mean))
        sd = resid.std()
        return resid[-1] / sd if sd > 0 else 0.0

    return close.rolling(window).apply(_z, raw=True)


# ── detectors ────────────────────────────────────────────────────────────────

def detect_chan_rev(bars: pd.DataFrame) -> pd.DataFrame:
    z = _rolling_linreg_z(bars["mid_c"], config.CHAN_WINDOW)
    ev = bars.loc[z.abs() >= config.CHAN_Z_TRIGGER, ["ts"]].copy()
    ev["direction"] = np.where(z[z.abs() >= config.CHAN_Z_TRIGGER] <= 0, "BUY", "SELL")
    ev["family"] = "chan_rev"
    ev["meta_z"] = z[z.abs() >= config.CHAN_Z_TRIGGER].values
    return ev


def detect_vwap_rev(bars: pd.DataFrame) -> pd.DataFrame:
    w = bars["n_ticks"].clip(lower=1).astype(float)
    pv = (bars["mid_c"] * w).rolling(config.CHAN_WINDOW).sum()
    vwap = pv / w.rolling(config.CHAN_WINDOW).sum()
    dev = bars["mid_c"] - vwap
    sd = dev.rolling(config.CHAN_WINDOW).std()
    z = dev / sd.replace(0, np.nan)
    mask = z.abs() >= config.VWAP_Z_TRIGGER
    ev = bars.loc[mask, ["ts"]].copy()
    ev["direction"] = np.where(z[mask] <= 0, "BUY", "SELL")
    ev["family"] = "vwap_rev"
    ev["meta_z"] = z[mask].values
    return ev


def _find_zones(bars: pd.DataFrame) -> list[tuple[float, float, int]]:
    """Pivot-cluster S/R zones from the lookback: [(lo, hi, touches)].
    Mirrors bot sr_zones: cluster pivots within SR_ZONE_WIDTH_PTS, need ≥ min touches."""
    h, l = bars["mid_h"].to_numpy(), bars["mid_l"].to_numpy()
    piv = []
    for i in range(2, len(bars) - 2):
        if h[i] == max(h[i - 2:i + 3]):
            piv.append(h[i])
        if l[i] == min(l[i - 2:i + 3]):
            piv.append(l[i])
    zones = []
    for p in sorted(piv):
        for z in zones:
            if abs(p - z[0]) <= config.SR_ZONE_WIDTH_PTS:
                z[0] = (z[0] * z[1] + p) / (z[1] + 1)  # running mean center
                z[1] += 1
                break
        else:
            zones.append([p, 1])
    return [
        (c - config.SR_ZONE_WIDTH_PTS / 2, c + config.SR_ZONE_WIDTH_PTS / 2, n)
        for c, n in zones if n >= config.SR_ZONE_MIN_TOUCHES
    ]


def detect_sr_react_and_sweep(bars: pd.DataFrame) -> pd.DataFrame:
    """S/R rejection (close back off the zone) and liquidity sweep (pierce + reclaim).
    Zones are rebuilt each bar from the trailing SR_ZONE_LOOKBACK window (causal)."""
    out = []
    atr = (bars["mid_h"] - bars["mid_l"]).rolling(config.ATR_PERIOD).mean()
    lb = config.SR_ZONE_LOOKBACK
    zones: list[tuple[float, float, int]] = []
    for i in range(lb, len(bars)):
        if i % 15 == 0:  # zones change slowly; rebuild every 15 bars for speed
            zones = _find_zones(bars.iloc[i - lb:i])
        b = bars.iloc[i]
        a = atr.iloc[i]
        if not zones or not np.isfinite(a) or a <= 0:
            continue
        for lo, hi, touches in zones:
            # support rejection: dip into zone, close back above it
            if lo <= b["mid_l"] <= hi and b["mid_c"] > hi:
                out.append({"ts": b["ts"], "direction": "BUY", "family": "sr_react",
                            "meta_touches": touches, "meta_dist_atr": (b["mid_c"] - hi) / a})
            # resistance rejection
            elif lo <= b["mid_h"] <= hi and b["mid_c"] < lo:
                out.append({"ts": b["ts"], "direction": "SELL", "family": "sr_react",
                            "meta_touches": touches, "meta_dist_atr": (lo - b["mid_c"]) / a})
            # sweep below support then reclaim within SWEEP_RECLAIM_BARS
            elif b["mid_l"] < lo and (lo - b["mid_l"]) <= config.SWEEP_MAX_PIERCE_ATR * a:
                for j in range(i, min(i + config.SWEEP_RECLAIM_BARS, len(bars))):
                    if bars.iloc[j]["mid_c"] > hi:
                        out.append({"ts": bars.iloc[j]["ts"], "direction": "BUY", "family": "sweep",
                                    "meta_touches": touches,
                                    "meta_pierce_atr": (lo - b["mid_l"]) / a})
                        break
            elif b["mid_h"] > hi and (b["mid_h"] - hi) <= config.SWEEP_MAX_PIERCE_ATR * a:
                for j in range(i, min(i + config.SWEEP_RECLAIM_BARS, len(bars))):
                    if bars.iloc[j]["mid_c"] < lo:
                        out.append({"ts": bars.iloc[j]["ts"], "direction": "SELL", "family": "sweep",
                                    "meta_touches": touches,
                                    "meta_pierce_atr": (b["mid_h"] - hi) / a})
                        break
    return pd.DataFrame(out)


def detect_orb(bars: pd.DataFrame, day: date) -> pd.DataFrame:
    """NY opening-range break (continuation) and failure-back-inside (reversal)."""
    open_ts = ny_open_utc(day)
    orb_end = open_ts + pd.Timedelta(minutes=config.ORB_MINUTES)
    rng = bars[(bars["ts"] >= open_ts) & (bars["ts"] < orb_end)]
    if len(rng) < config.ORB_MINUTES // 2:
        return pd.DataFrame()
    hi, lo = rng["mid_h"].max(), rng["mid_l"].min()
    post = bars[bars["ts"] >= orb_end].reset_index(drop=True)
    out = []
    broke = None  # ("up"|"dn", positional index of break)
    for i, b in post.iterrows():
        if broke is None:
            if b["mid_c"] > hi:
                broke = ("up", i)
                out.append({"ts": b["ts"], "direction": "BUY", "family": "orb",
                            "meta_kind": 1.0, "meta_or_width": hi - lo})
            elif b["mid_c"] < lo:
                broke = ("dn", i)
                out.append({"ts": b["ts"], "direction": "SELL", "family": "orb",
                            "meta_kind": 1.0, "meta_or_width": hi - lo})
        else:
            side, bi = broke
            if i - bi > 5:
                break  # failure window over; one ORB episode per day
            if side == "up" and b["mid_c"] < hi:  # failed break → fade
                out.append({"ts": b["ts"], "direction": "SELL", "family": "orb",
                            "meta_kind": -1.0, "meta_or_width": hi - lo})
                break
            if side == "dn" and b["mid_c"] > lo:
                out.append({"ts": b["ts"], "direction": "BUY", "family": "orb",
                            "meta_kind": -1.0, "meta_or_width": hi - lo})
                break
    return pd.DataFrame(out)


def detect_mom_cont(bars: pd.DataFrame) -> pd.DataFrame:
    """Momentum continuation: 15m stretch > MOM_STRETCH_ATR × ATR15 in trend
    direction, then a 1m pullback-and-resume confirm bar."""
    b15 = (
        bars.set_index("ts")
        .resample("15min")
        .agg(mid_h=("mid_h", "max"), mid_l=("mid_l", "min"), mid_c=("mid_c", "last"))
        .dropna()
    )
    if len(b15) < 25:
        return pd.DataFrame()
    ema20 = b15["mid_c"].ewm(span=20, adjust=False).mean()
    atr15 = (b15["mid_h"] - b15["mid_l"]).rolling(14).mean()
    stretch = (b15["mid_c"] - ema20) / atr15.replace(0, np.nan)

    out = []
    for ts15, s in stretch.dropna().items():
        if abs(s) < config.MOM_STRETCH_ATR:
            continue
        direction = "BUY" if s > 0 else "SELL"
        # 1m confirm inside the NEXT 15m block: pullback then close beyond prior 1m extreme
        blk = bars[(bars["ts"] > ts15) & (bars["ts"] <= ts15 + pd.Timedelta(minutes=15))]
        for k in range(2, len(blk)):
            w = blk.iloc[:k]
            b = blk.iloc[k - 1]
            if direction == "BUY" and b["mid_c"] > w["mid_h"].iloc[:-1].max() and w["mid_l"].min() < w["mid_c"].iloc[0]:
                out.append({"ts": b["ts"], "direction": "BUY", "family": "mom_cont", "meta_stretch": s})
                break
            if direction == "SELL" and b["mid_c"] < w["mid_l"].iloc[:-1].min() and w["mid_h"].max() > w["mid_c"].iloc[0]:
                out.append({"ts": b["ts"], "direction": "SELL", "family": "mom_cont", "meta_stretch": s})
                break
    return pd.DataFrame(out)


def detect_vol_compress(bars: pd.DataFrame) -> pd.DataFrame:
    """Volatility compression → expansion breakout. 20-bar realized range in the
    bottom quintile of its trailing 600-bar distribution for ≥10 bars, then a
    close beyond the compression box → trade the breakout direction."""
    width = (bars["mid_h"].rolling(20).max() - bars["mid_l"].rolling(20).min())
    pctl = width.rolling(600, min_periods=200).rank(pct=True)
    squeezed = (pctl < 0.20).rolling(10).sum() >= 10
    box_hi = bars["mid_h"].rolling(20).max().shift(1)
    box_lo = bars["mid_l"].rolling(20).min().shift(1)
    out = []
    armed = False
    for i in range(len(bars)):
        if squeezed.iloc[i]:
            armed = True
        if not armed:
            continue
        c = bars["mid_c"].iloc[i]
        if c > box_hi.iloc[i]:
            out.append({"ts": bars["ts"].iloc[i], "direction": "BUY", "family": "vol_compress",
                        "meta_z": float(pctl.iloc[i])})
            armed = False
        elif c < box_lo.iloc[i]:
            out.append({"ts": bars["ts"].iloc[i], "direction": "SELL", "family": "vol_compress",
                        "meta_z": float(pctl.iloc[i])})
            armed = False
    return pd.DataFrame(out)


def detect_trend_exhaust(bars: pd.DataFrame) -> pd.DataFrame:
    """Trend exhaustion fade: ≥5 consecutive same-direction closes, displacement
    over the run ≥ 2×ATR, RSI-14 extreme → fade the climax."""
    c = bars["mid_c"]
    d = np.sign(c.diff())
    atr = (bars["mid_h"] - bars["mid_l"]).rolling(config.ATR_PERIOD).mean()
    delta = c.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    run = d.groupby((d != d.shift()).cumsum()).cumcount() + 1
    out = []
    for i in range(10, len(bars)):
        if run.iloc[i] < 5 or not np.isfinite(atr.iloc[i]) or atr.iloc[i] <= 0:
            continue
        disp = abs(c.iloc[i] - c.iloc[i - int(run.iloc[i])])
        if disp < 2.0 * atr.iloc[i]:
            continue
        if d.iloc[i] > 0 and rsi.iloc[i] >= 75:
            out.append({"ts": bars["ts"].iloc[i], "direction": "SELL", "family": "trend_exhaust",
                        "meta_z": float(rsi.iloc[i])})
        elif d.iloc[i] < 0 and rsi.iloc[i] <= 25:
            out.append({"ts": bars["ts"].iloc[i], "direction": "BUY", "family": "trend_exhaust",
                        "meta_z": float(rsi.iloc[i])})
    return pd.DataFrame(out)


# ── day-level driver ─────────────────────────────────────────────────────────

def detect_day(bars_day: pd.DataFrame, bars_prev: pd.DataFrame | None, day: date) -> pd.DataFrame:
    """Run all detectors for one day. `bars_prev` provides causal lookback."""
    ctx = pd.concat([bars_prev, bars_day]) if bars_prev is not None else bars_day
    ctx = ctx.sort_values("ts").reset_index(drop=True)

    frames = [
        detect_chan_rev(ctx),
        detect_vwap_rev(ctx),
        detect_sr_react_and_sweep(ctx),
        detect_orb(ctx, day),
        detect_mom_cont(ctx),
    ]
    ev = pd.concat([f for f in frames if not f.empty], ignore_index=True) if any(
        not f.empty for f in frames) else pd.DataFrame(columns=["ts", "direction", "family"])
    if ev.empty:
        return ev
    ev = ev[ev["ts"].dt.date == day]          # only events on the target day
    ev = ev[_in_window(ev["ts"])]             # trading window only
    return _apply_refractory(ev)
