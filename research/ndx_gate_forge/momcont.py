"""Reflex mom_cont — sızıntılı (araştırma) vs sızıntısız (üretim) sürüm, 4 dönem, dürüst icra.

Araştırma dedektörü (ndx_reflex_engine/triggers/detect.py) 15m barı sol-etiketle
örnekler ve 1m teyidini AYNI 15m diliminin içinde arar → gerilme kararı teyitten
sonraki 15m kapanışını kullanır. Üretim servisi (reflex_engine_service) ise teyidi
bir SONRAKİ dilimde arar. İkisi de burada birebir yeniden kurulur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import load_1m, simulate, atr, OUT, block_boot
from evaluate import PER

STRETCH = 2.0
REFRACT_MIN = 30
WIN_UTC = (13, 20)


def events(b: pd.DataFrame, leaky: bool) -> pd.DataFrame:
    x = b[["ts", "t", "high", "low", "close", "period"]].copy()
    x["bin"] = x.ts.dt.floor("15min")
    g = x.groupby("bin").agg(h=("high", "max"), l=("low", "min"), c=("close", "last"), n=("t", "size"))
    g = g[g.n >= 12]
    ema = g.c.ewm(span=20, adjust=False).mean()
    a15 = (g.h - g.l).rolling(14).mean()
    st = ((g.c - ema) / a15).dropna()
    st = st[st.abs() >= STRETCH]
    ts_idx = pd.Series(np.arange(len(x)), index=x.ts)
    hi, lo, cl = x.high.to_numpy(), x.low.to_numpy(), x.close.to_numpy()
    tt = x.t.to_numpy()
    out = []
    for T, s in st.items():
        # sızıntılı: aynı dilim (T, T+15]; sızıntısız: dilim kapandıktan sonra [T+15, T+30)
        a = T + pd.Timedelta(minutes=1 if leaky else 15)
        z = T + pd.Timedelta(minutes=15 if leaky else 29)
        i0 = ts_idx.index.searchsorted(a)
        i1 = ts_idx.index.searchsorted(z, side="right")
        if i1 - i0 < 3:
            continue
        d = 1 if s > 0 else -1
        for k in range(2, i1 - i0):
            j = i0 + k - 1
            w = slice(i0, j)            # önceki barlar (teyit barı hariç)
            if tt[j] - tt[i0] > (k - 1) * 60 + 120:
                break
            if d == 1 and cl[j] > hi[w].max() and lo[i0:j + 1].min() < cl[i0]:
                out.append((j, d, s)); break
            if d == -1 and cl[j] < lo[w].min() and hi[i0:j + 1].max() > cl[i0]:
                out.append((j, d, s)); break
    e = pd.DataFrame(out, columns=["i", "side", "stretch"])
    dec = pd.to_datetime(b.t.to_numpy()[e.i] + 60, unit="s", utc=True)
    e = e[(dec.hour >= WIN_UTC[0]) & (dec.hour < WIN_UTC[1])].reset_index(drop=True)
    keep, last = [], {}
    for r in e.itertuples():
        tt_ = b.t.iat[r.i]
        if r.side not in last or tt_ - last[r.side] >= REFRACT_MIN * 60:
            keep.append(r.Index); last[r.side] = tt_
    return e.loc[keep].reset_index(drop=True)


def run() -> pd.DataFrame:
    b = load_1m()
    a1 = atr(b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy(), 14)
    rows = []
    for leaky in (True, False):
        e = events(b, leaky)
        idx = e.i.to_numpy()
        sd = e.side.to_numpy()
        A = a1[idx]
        e["period"] = b.period.to_numpy()[idx]
        e["day"] = b.ts.dt.date.to_numpy()[idx]
        e["wd"] = (b.ts + pd.Timedelta(minutes=1)).dt.tz_convert("America/New_York").dt.weekday.to_numpy()[idx]
        geoms = {"prod_ts15_sl1.5": (np.full(len(idx), 1e6), 1.5 * A, 15),
                 "res_tp1.5_sl1.0_ts30": (1.5 * A, 1.0 * A, 30),
                 "res_tp1.5_sl1.5_ts60": (1.5 * A, 1.5 * A, 60)}
        for gname, (tp, sl, hold) in geoms.items():
            R, dur, why = simulate(b, idx, sd, tp, sl, maxhold_min=hold)
            e[gname] = R
        e["leaky"] = leaky
        rows.append(e)
    E = pd.concat(rows, ignore_index=True)
    E.to_parquet(OUT / "momcont_events.parquet")
    return E


if __name__ == "__main__":
    E = run()
    pd.set_option("display.width", 250)
    for g in ["prod_ts15_sl1.5", "res_tp1.5_sl1.0_ts30", "res_tp1.5_sl1.5_ts60"]:
        t = E.groupby(["leaky", "period", "side"])[g].agg(["size", "mean", lambda x: (x > 0).mean()]).unstack("side")
        print("\n", g); print(t.round(3).to_string())
        for lk in (True, False):
            x = E[(E.leaky == lk) & E.period.isin(["D25b", "C26", "M26"])]
            bs = block_boot(x[g].to_numpy(), x.day.astype(str).to_numpy(), 2000)
            print(f"  leaky={lk} D25b+2026 n={len(x)} EV={x[g].mean():.3f} P(EV>0)={np.mean(bs>0):.3f}")
