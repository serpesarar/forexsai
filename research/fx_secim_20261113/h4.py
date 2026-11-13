"""FX-01 H4: taşıma çözülmesi = korku dönüşü (PROTOCOL.md §3 H4). Çalıştır: ../../.venv/bin/python -I h4.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
import hyp  # noqa: E402

VIX_TH = 18.4
RSI_LO, RSI_HI = 10, 90
MAX_DAYS = 5
PAIRS = ["AUDJPY", "NZDJPY", "CADJPY", "AUDUSD", "NZDUSD", "EURJPY"]
N_PLACEBO = 300


def rsi2(c: pd.Series) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 2, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / 2, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def daily(pair: str) -> pd.DataFrame:
    """Broker D1: bar etiketi S (sunucu tarihi) = ET 17:00'de (S günü) kapanır."""
    d = f.load(pair, "D1")
    d["day"] = d.srv.dt.normalize()
    d = d[d.day.dt.dayofweek < 5].set_index("day")
    d["rsi"] = rsi2(d.c)
    d["up"] = d.c > d.c.shift()
    return d


def swap_cost(pair: str, side: int, nights: list[pd.Timestamp], px: float) -> float:
    m = f.meta()[pair]
    pts = m["swap_long"] if side > 0 else m["swap_short"]
    mult = sum(3 if n.dayofweek == 2 else 1 for n in nights)
    return -pts * m["point"] / px * 1e4 * mult      # pozitif = maliyet


def run_rule(pair: str, entries: list[pd.Timestamp], side: int, d: pd.DataFrame) -> list[dict]:
    """entries: sinyal günü S; giriş S günü 18:00 ET H1 açılışı; çıkış ilk 'side yönünde' günlük kapanış günü E'nin 18:00 ET'si."""
    out, busy_until = [], pd.Timestamp.min
    days = d.index
    for s in entries:
        if s <= busy_until:
            continue                                   # tek pozisyon
        i = days.get_loc(s)
        exit_day = None
        for j in range(i + 1, min(i + 1 + MAX_DAYS, len(days))):
            exit_day = days[j]
            if (d.up.iloc[j] and side > 0) or ((not d.up.iloc[j]) and side < 0):
                break
        if exit_day is None:
            continue
        r = hyp.trade(pair, hyp.ny(s, 18), hyp.ny(exit_day, 18), side)
        if r is None:
            continue
        nights = list(days[i:days.get_loc(exit_day)])
        sc = swap_cost(pair, side, nights, d.c.iloc[i])
        r.update(net=r["net"] - sc, net15=r["net15"] - sc, gun=len(nights), swap=sc)
        out.append(r)
        busy_until = exit_day
    return out


def placebo(pair: str, d: pd.DataFrame, n_trades: int, side: int, rng: np.random.Generator) -> float:
    pool = d[(d.index >= "2010-10-12") & (d.index < "2026-11-06")].index
    picks = sorted(pd.DatetimeIndex(rng.choice(pool, n_trades, replace=False)))
    rows = run_rule(pair, list(picks), side, d)
    return float(np.mean([r["net"] for r in rows])) if rows else np.nan


def main() -> list[dict]:
    vix = hyp.macro().VIX
    res = []
    for pair in PAIRS:
        d = daily(pair)
        vprev = vix.reindex(d.index - pd.offsets.BDay(1)).values
        d["vix_prev"] = vprev
        long_sig = d[(d.vix_prev >= VIX_TH) & (d.rsi < RSI_LO) & (d.index >= "2010-10-12")].index
        short_sig = d[(d.vix_prev < VIX_TH) & (d.rsi > RSI_HI) & (d.index >= "2010-10-12")].index
        for lab, sig, side in (("H4 uzun stres∧RSI2<10", long_sig, +1), ("H4 ayna kısa sakin∧RSI2>90", short_sig, -1)):
            rows = run_rule(pair, list(sig), side, d)
            rep = hyp.report(rows, f"{lab} {pair}")
            if rows:
                rng = np.random.default_rng(5)
                pl = np.array([placebo(pair, d, len(rows), side, rng) for _ in range(N_PLACEBO)])
                rep["plasebo_ort"] = round(float(np.nanmean(pl)), 2)
                rep["plasebo_yuzdelik"] = round(float((pl < rep["ort"]).mean()), 3)
                rep["ort_gun"] = round(float(np.mean([r["gun"] for r in rows])), 2)
                rep["ort_swap_bp"] = round(float(np.mean([r["swap"] for r in rows])), 2)
            res.append(rep)
            print(json.dumps(rep, ensure_ascii=False, default=str), flush=True)
    (f.RES / "h4.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return res


if __name__ == "__main__":
    main()
