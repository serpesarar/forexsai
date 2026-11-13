"""FX-01 hipotezleri H1/H1b/H3/H3b/H8a/H8b/H2 — PROTOCOL.md + EK-1. Çalıştır: ../../.venv/bin/python -I hyp.py"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import holidays
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402

USD_BASKET = {"EURUSD": +1, "GBPUSD": +1, "AUDUSD": +1, "USDJPY": -1, "USDCHF": -1, "USDCAD": -1}  # +1 = USD kısa yönü
JPY_PAIRS = ["USDJPY", "EURJPY", "AUDJPY", "GBPJPY"]
STRESS = 1.5
_CACHE: dict = {}


def bars(pair: str, tf: str = "H1") -> pd.DataFrame:
    k = (pair, tf)
    if k not in _CACHE:
        x = f.load(pair, tf)
        x["spb"] = f.spread_bp(x, f.meta()[pair]["point"])
        _CACHE[k] = x.set_index("utc")
    return _CACHE[k]


def trade(pair: str, t_in: pd.Timestamp, t_out: pd.Timestamp, side: int, tf: str = "H1") -> dict | None:
    """side +1 uzun / −1 kısa (çiftin kendisi). Giriş t_in bar AÇILIŞI, çıkış t_out bar AÇILIŞI (UTC naif)."""
    x = bars(pair, tf)
    if t_in not in x.index or t_out not in x.index or t_out <= t_in:
        return None
    a, b = x.loc[t_in], x.loc[t_out]
    i = x.index.get_loc(t_in)
    prev_c = x.c.iloc[i - 1] if i > 0 else np.nan
    gross = side * np.log(b.o / a.o) * 1e4
    cost = (a.spb + b.spb) / 2
    return {"pair": pair, "t": t_in, "gross": gross, "net": gross - cost, "net15": gross - STRESS * cost,
            "icra_fark": side * np.log(a.o / prev_c) * 1e4 if prev_c == prev_c else np.nan}


@lru_cache(maxsize=None)
def _local(day: int, hh: int, tz: str) -> pd.Timestamp:
    return pd.Timestamp.fromordinal(day).replace(hour=hh).tz_localize(tz).tz_convert("UTC").tz_localize(None)


def london(d: pd.Timestamp, hh: int) -> pd.Timestamp:
    return _local(pd.Timestamp(d).toordinal(), hh, "Europe/London")


def ny(d: pd.Timestamp, hh: int) -> pd.Timestamp:
    return _local(pd.Timestamp(d).toordinal(), hh, "America/New_York")


def report(rows: list[dict], label: str, ctrl: list[dict] | None = None) -> dict:
    d = pd.DataFrame([r for r in rows if r])
    if d.empty:
        return {"hucre": label, "n": 0}
    d = d.sort_values("t").reset_index(drop=True)
    ev = d.groupby("t").agg(net=("net", "mean"), net15=("net15", "mean"), gross=("gross", "mean"), icra=("icra_fark", "mean")).reset_index()
    out = {"hucre": label, **f.summ(ev.net, ev.t), "brut": round(ev.gross.mean(), 2), "net15": round(ev.net15.mean(), 2),
           "icra_fark": round(ev.icra.mean(), 2), "yil": {int(y): round(g.net.mean(), 1) for y, g in ev.groupby(ev.t.dt.year)}}
    if ctrl:
        c = pd.DataFrame([r for r in ctrl if r]).groupby("t").net.mean()
        out["kontrol"] = {"n": int(len(c)), "ort": round(c.mean(), 2)}
        rng = np.random.default_rng(11)
        a, b = ev.net.values, c.values
        diff = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(3000)])
        out["fark"] = round(a.mean() - b.mean(), 2)
        out["P_fark"] = round(float((diff > 0).mean()), 3)
    return out


# ---------- takvimler ----------
def bdays(start: str, end: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start, end)


def gotobi_days(start: str, end: str) -> tuple[set, set]:
    jp = holidays.JP(years=range(2009, 2027))
    days = pd.date_range(start, end)
    jbd = [d for d in days if d.dayofweek < 5 and d.date() not in jp]
    jbd_set = set(jbd)
    got = set()
    for d in days:
        last_bd_month = max((x for x in jbd if x.year == d.year and x.month == d.month), default=None)
        if d.day in (5, 10, 15, 20, 25, 30) or (d == last_bd_month):
            e = d
            while e not in jbd_set and e >= days[0]:
                e -= pd.Timedelta(days=1)
            got.add(e)
    return got, jbd_set


def last_bdays(start: str, end: str) -> list[pd.Timestamp]:
    b = bdays(start, end)
    s = pd.Series(b, index=b)
    return list(s.groupby([b.year, b.month]).max())


# ---------- hipotezler ----------
def h8(tf: str = "H1") -> list[dict]:
    got, jbd = gotobi_days("2010-10-08", "2026-11-12")
    out = []
    exit_h = (0, 45) if tf == "M15" else (1, 0)
    for pair in JPY_PAIRS:
        rows_a, rows_b, ctrl_a, ctrl_b = [], [], [], []
        for d in sorted(jbd):
            if d.dayofweek >= 5:
                continue
            t0 = d - pd.Timedelta(hours=1)          # 23:00 UTC önceki gün = 08:00 JST
            t1 = d + pd.Timedelta(hours=exit_h[0], minutes=exit_h[1])
            r = trade(pair, t0, t1, +1, tf)
            rb = trade(pair, d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=6), -1, tf)
            if d in got:
                rows_a.append(r)
                rows_b.append(rb)
            else:
                ctrl_a.append(r)
                ctrl_b.append(rb)
        out.append(report(rows_a, f"H8a {pair} {tf} gotobi 08:00→fiks uzun", ctrl_a))
        out.append(report(rows_b, f"H8b {pair} {tf} gotobi 10:00→15:00 JST kısa", ctrl_b))
    return out


def macro() -> pd.DataFrame:
    m = pd.read_csv(f.DATA / "macro_daily.csv", index_col=0, parse_dates=True)
    return m[m.index < "2026-11-13"]


def h1() -> list[dict]:
    m = macro()
    rows, rows_b = [], []
    for d in last_bdays("2010-11-01", "2026-10-31"):
        prev = m[m.index < d]
        mstart = prev[prev.index < d.replace(day=1)]
        if len(prev) == 0 or len(mstart) == 0:
            continue
        spx = prev.SPX.iloc[-1] / mstart.SPX.iloc[-1] - 1
        dax = prev.DAX.iloc[-1] / mstart.DAX.iloc[-1] - 1
        s = 1 if spx - dax > 0 else -1          # +1 → USD sat
        for pair, usd_short in USD_BASKET.items():
            rows.append(trade(pair, london(d, 10), london(d, 16), s * usd_short))
            rows_b.append(trade(pair, london(d, 16), london(d, 20), -s * usd_short))
    return [report(rows, "H1 ay sonu 10→16 Londra hedge-akışı sepet"), report(rows_b, "H1b ay sonu 16→20 Londra ters")]


def fomc_days() -> list[pd.Timestamp]:
    t = pd.read_csv(f.ROOT / "research/kt02_takvim_seans_20261111/takvim.csv")
    return sorted(pd.to_datetime(t.loc[t.event == "FOMC", "date"]).unique())


def h3() -> list[dict]:
    F = [d for d in fomc_days() if d >= pd.Timestamp("2010-10-12")]
    Fs = set(F)
    rows, rows_b, ctrl = [], [], []
    for d in bdays("2010-10-12", "2026-11-12"):
        p = d - pd.offsets.BDay(1)
        for pair, usd_short in USD_BASKET.items():
            r = trade(pair, ny(p, 18), ny(d, 16), usd_short)
            if d in Fs:
                rows.append(r)
                rows_b.append(trade(pair, ny(p, 18), ny(d, 14), usd_short))
            elif d.dayofweek in {x.dayofweek for x in F}:
                ctrl.append(r)
    return [report(rows, "H3 FOMC USD sepeti kısa 18:00 ET→16:00 ET", ctrl), report(rows_b, "H3b FOMC duyuru öncesi →14:00 ET")]


def h2() -> list[dict]:
    cells = {"EURUSD": [(7, 12, -1), (13, 20, +1)], "GBPUSD": [(7, 12, -1), (13, 20, +1)], "USDJPY": [(0, 6, +1), (13, 20, -1)]}
    out = []
    for pair, segs in cells.items():
        for a, b, side in segs:
            rows = [trade(pair, d + pd.Timedelta(hours=a), d + pd.Timedelta(hours=b), side) for d in bdays("2010-10-11", "2026-11-12")]
            out.append(report(rows, f"H2 {pair} {a:02d}-{b:02d} UTC {'uzun' if side > 0 else 'kısa'}"))
    return out


if __name__ == "__main__":
    which = sys.argv[1:] or ["h1", "h3", "h8", "h2"]
    res = []
    for w in which:
        r = globals()[w]() if w != "h8m15" else h8("M15")
        res += r
        for x in r:
            print(json.dumps(x, ensure_ascii=False, default=str), flush=True)
    (f.RES / f"hyp_{'_'.join(which)}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
