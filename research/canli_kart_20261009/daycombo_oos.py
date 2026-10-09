"""DAYCOMBO — seçimde görülmemiş veride bar yeniden kurulumu (PROTOCOL.md §B, ön kayıtlı).

Veri: research/ndx_pattern_motifs/data/bars_1m.parquet (UTC, bar başlangıç etiketli; 2025 Dukascopy bid,
2026 broker). Çıktı: results/daycombo_trades.parquet + konsol kartı.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BARS = ROOT / "research/ndx_pattern_motifs/data/bars_1m.parquet"
SPREAD, TP, SL = 1.5, 80.0, 110.0
WIN_LO, WIN_HI = 14 * 60, 19 * 60 + 30
MAX_HOLD = pd.Timedelta(days=3)
PERIODS = {"OOS-A": ("2025-01-01", "2025-12-31"), "IS": ("2026-02-10", "2026-07-29"),
           "OOS-B": ("2026-07-29", "2026-10-03")}
RNG = np.random.default_rng(3)


def resample(b: pd.DataFrame, m: int) -> pd.DataFrame:
    g = b.set_index("ts").groupby([pd.Grouper(freq=f"{m}min"), "seg"])
    o = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
    return o.reset_index().sort_values("ts").reset_index(drop=True)


def signals(b1: pd.DataFrame, friday: bool) -> pd.DataFrame:
    b5, b15 = resample(b1, 5), resample(b1, 15)
    b5["end"] = b5.ts + pd.Timedelta(minutes=5)
    b15["end"] = b15.ts + pd.Timedelta(minutes=15)
    b15["ema"] = b15.groupby("seg").close.transform(lambda s: s.ewm(span=20, adjust=False).mean())
    b15["ema3"] = b15.groupby("seg").ema.shift(3)
    b15["trend"] = (b15.close > b15.ema) & (b15.ema > b15.ema3)
    # gece pozitif: günün 00:00 UTC ilk 5m açılışı (dakika<10) vs başlangıcı ≤13:20 son 5m kapanışı
    b5["day"] = b5.ts.dt.floor("D")
    mins = b5.ts.dt.hour * 60 + b5.ts.dt.minute
    first = b5[mins < 10].groupby("day").open.first()
    pre = b5[mins <= 13 * 60 + 20].groupby("day").close.last()
    gece = (pre > first.reindex(pre.index)).rename("gece")
    em = b5.end.dt.hour * 60 + b5.end.dt.minute
    rng = b5.high - b5.low
    cand = b5[(em >= WIN_LO) & (em <= WIN_HI) & (b5.close > b5.open) & (rng > 0) & ((b5.close - b5.open) / rng > 0.5)]
    cand = cand[cand.day.map(gece).fillna(False).astype(bool)]
    if not friday:
        cand = cand[cand.end.dt.weekday != 4]
    # son kapalı 15m (bitişi ≤ karar anı)
    tr = pd.merge_asof(cand[["end", "seg"]].sort_values("end"), b15[["end", "trend", "seg"]].rename(columns={"end": "e15", "seg": "s15"}),
                       left_on="end", right_on="e15", direction="backward")
    tr = tr[(tr.trend == True) & (tr.seg == tr.s15)]  # noqa: E712
    return tr[["end", "seg"]].reset_index(drop=True)


def simulate(b1: pd.DataFrame, sig: pd.DataFrame, spread: float) -> pd.DataFrame:
    ts = b1.ts.dt.tz_convert(None).to_numpy().astype("datetime64[ns]")
    o, h, l, c, seg = (b1[k].to_numpy() for k in ("open", "high", "low", "close", "seg"))
    out, busy_until = [], np.datetime64("1970-01-01T00:00", "ns")
    for r in sig.itertuples():
        t = np.datetime64(r.end.tz_convert(None), "ns")
        if t < busy_until:
            continue
        k = int(np.searchsorted(ts, t))
        if k >= len(ts) or seg[k] != r.seg or ts[k] - t > np.timedelta64(5, "m"):
            continue
        e = o[k] + spread
        tp, sl = e + TP, e - SL
        end_t = t + np.timedelta64(int(MAX_HOLD.total_seconds()), "s")
        res, j = None, k
        while j < len(ts) and seg[j] == seg[k] and ts[j] <= end_t:
            if l[j] <= sl:
                res = -SL; break
            if h[j] >= tp:
                res = TP; break
            j += 1
        if res is None:
            if j >= len(ts) or seg[min(j, len(ts) - 1)] != seg[k]:
                continue                       # veri boşluğu: işlem atılır
            res = c[j - 1] - e
        out.append({"entry": pd.Timestamp(ts[k], tz="UTC"), "exit": pd.Timestamp(ts[min(j, len(ts) - 1)], tz="UTC"),
                    "pts": res, "R": res / SL})
        busy_until = ts[min(j, len(ts) - 1)]
    return pd.DataFrame(out)


def period_of(t: pd.Timestamp) -> str:
    for k, (a, b) in PERIODS.items():
        if pd.Timestamp(a, tz="UTC") <= t < pd.Timestamp(b, tz="UTC"):
            return k
    return "-"


def card(x: pd.DataFrame, x15: pd.DataFrame, name: str) -> dict:
    R = x.R.to_numpy()
    days = x.entry.dt.strftime("%F").to_numpy()
    u, inv = np.unique(days, return_inverse=True)
    s, k = np.bincount(inv, weights=R), np.bincount(inv)
    pick = RNG.integers(0, len(u), (4000, len(u)))
    m = s[pick].sum(1) / k[pick].sum(1)
    h = len(R) // 2
    chk = {"1_hacim": len(R) >= 150, "2_beklenti": bool(R.mean() > 0 and (m > 0).mean() >= .9),
           "3_kararlilik": bool(R[:h].mean() >= 0 and R[h:].mean() >= 0), "4_surtunme": bool(x15.R.mean() > 0),
           "5_icra": True, "6_sira_bagimli": bool(R.mean() > 0)}
    v = "RED" if not chk["1_hacim"] else ("LIVE" if all(chk.values()) else "SHADOW")
    d = {"ad": name, "n": len(R), "wr": round(100 * float((R > 0).mean()), 1), "ortR": round(float(R.mean()), 3),
         "toplamR": round(float(R.sum()), 1), "P": round(float((m > 0).mean()), 3),
         "CI": [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)],
         "yarilar": [round(float(R[:h].mean()), 3), round(float(R[h:].mean()), 3)],
         "spread15_ortR": round(float(x15.R.mean()), 3), "checks": chk, "verdikt": v}
    print(f"{name:34} n={d['n']:4} WR %{d['wr']} ortR {d['ortR']:+.3f} top {d['toplamR']:+.1f}R P %{100 * d['P']:.0f} "
          f"CI{d['CI']} yarılar {d['yarilar']} ×1,5spr {d['spread15_ortR']:+.3f} → {v}")
    return d


def main() -> None:
    b1 = pd.read_parquet(BARS).sort_values("ts").reset_index(drop=True)
    res = {}
    for fri in (False, True):
        sig = signals(b1, friday=fri)
        x = simulate(b1, sig, SPREAD)
        x15 = simulate(b1, sig, SPREAD * 1.5)
        for df in (x, x15):
            df["period"] = df.entry.map(period_of)
        tag = "" if not fri else " (Cuma dahil)"
        if not fri:
            x.to_parquet(HERE / "results" / "daycombo_trades.parquet")
        for p in ["OOS-A", "IS", "OOS-B"]:
            res[p + tag] = card(x[x.period == p], x15[x15.period == p], p + tag)
        oos = x.period.isin(["OOS-A", "OOS-B"])
        res["OOS-A+B" + tag] = card(x[oos], x15[x15.period.isin(["OOS-A", "OOS-B"])], "KART: OOS-A+B" + tag)
    (HERE / "results" / "daycombo_oos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    (HERE / "results").mkdir(exist_ok=True)
    main()
