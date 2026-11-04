"""Bağımsız son kasa: broker (Pepperstone) 1m BID 2026-06-17 → 10-14. Göstergeler için Duka H1 geçmişi
2026-06-17 öncesine eklenir (splice); sinyaller broker H1'den, yol 1m çözünürlükte. Ayrıca Duka↔broker kalibrasyonu."""
from __future__ import annotations
import os
import numpy as np, pandas as pd
from mech import prep_h1, path_sim, day_boot_p
from rules import GEOM, events, holds

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "results")
CUT = pd.Timestamp("2026-06-17", tz="UTC")
SPREAD_A = 0.12


def broker_1m() -> pd.DataFrame:
    m = pd.read_csv(os.path.join(ROOT, "..", "data", "xau_1m_utc.csv.gz"))
    m["ts"] = pd.to_datetime(m.t_utc, utc=True)
    return m.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c"})[["ts", "o", "h", "l", "c"]]


def broker_h1(m: pd.DataFrame) -> pd.DataFrame:
    g = m.set_index("ts").resample("1h", label="left", closed="left")
    h = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "k": g.o.size()})
    return h[h.k > 0].reset_index()


def calibrate(duka: pd.DataFrame, bh: pd.DataFrame) -> str:
    j = duka.merge(bh, on="ts", suffixes=("_d", "_b"))
    j = j[j.k >= 50]
    out = [f"ortak tam saat n={len(j)}"]
    for lag in (-2, -1, 0, 1, 2):
        jj = duka.assign(ts=duka.ts + pd.Timedelta(hours=lag)).merge(bh, on="ts", suffixes=("_d", "_b"))
        jj = jj[jj.k >= 50]
        r = np.corrcoef(jj.c_d.diff().dropna(), jj.c_b.diff().dropna())[0, 1]
        out.append(f"  Duka ts+{lag}h: |Δclose| medyan {np.median(np.abs(jj.c_d - jj.c_b)):.3f}$  Δ-getiri korelasyonu {r:.3f}")
    out.append(f"  close farkı (duka−broker) medyan {np.median(j.c_d - j.c_b):+.3f}$, high {np.median(j.h_d - j.h_b):+.3f}, low {np.median(j.l_d - j.l_b):+.3f}")
    out.append(f"  H1 aralık oranı duka/broker medyan {np.median((j.h_d - j.l_d) / (j.h_b - j.l_b)):.3f}")
    return "\n".join(out)


def run(duka: pd.DataFrame) -> pd.DataFrame:
    m = broker_1m(); bh = broker_h1(m)
    cal = calibrate(duka[["ts", "o", "h", "l", "c"]], bh)
    sp = pd.concat([duka[duka.ts < CUT][["ts", "o", "h", "l", "c"]], bh[bh.ts >= CUT][["ts", "o", "h", "l", "c"]]])
    d = prep_h1(sp)
    T = m.ts.dt.tz_convert(None).to_numpy(); O1, H1, L1, C1 = (m[k].to_numpy() for k in "ohlc")
    seg1 = (np.diff(T.astype("datetime64[s]").astype(np.int64), prepend=0) > 3 * 3600).cumsum()  # naive UTC
    hts = d.ts.dt.tz_convert(None).to_numpy()
    rows = []
    for rule in GEOM:
        for side in (+1, -1):
            ev = events(d, rule, side)
            ev = ev[hts[ev.sig.to_numpy()] >= np.datetime64(CUT.tz_convert(None))].reset_index(drop=True)
            if not len(ev):
                continue
            for gi, (tp, sl, hold) in enumerate(GEOM[rule]):
                hl = holds(d, ev.ent.to_numpy(), hold)
                ok = hl > 0
                e2, hl2 = ev[ok], hl[ok]
                if not len(e2):
                    continue
                st = hts[e2.ent.to_numpy()]
                en = hts[np.clip(e2.ent.to_numpy() + hl2 - 1, 0, len(hts) - 1)] + np.timedelta64(1, "h")
                k = np.searchsorted(T, st)
                kend = np.searchsorted(T, en)
                good = (k < len(T)) & (kend > k)
                k, kend, e3 = k[good], kend[good], e2[good]
                # 1m yol: optimistic için sinyal barı kapanışı = broker H1 close
                Csig = d.c.to_numpy()[e3.sig.to_numpy()]
                C1x = C1.copy()
                R1, _, c1 = path_sim(O1, H1, L1, C1x, seg1, np.maximum(k - 1, 0), k, e3.atr.to_numpy(), kend - k, tp, sl, side, SPREAD_A)
                RH, _, _ = path_sim(*(d[c].to_numpy() for c in "ohlc"), d.seg.to_numpy(), e3.sig.to_numpy(), e3.ent.to_numpy(),
                                    e3.atr.to_numpy(), hl2[good], tp, sl, side, SPREAD_A)
                p, ci = day_boot_p(R1, e3.date.to_numpy(), n=2000)
                rows.append(dict(cell=f"{rule}{'B' if side > 0 else 'S'}_G{gi+1}", n=int(np.isfinite(R1).sum()),
                                 ortR_1m=float(np.nanmean(R1)), ortR_H1path=float(np.nanmean(RH)),
                                 wr_1m=float(np.nanmean(R1 > 0)), P=p, ci_lo=ci[0], ci_hi=ci[1],
                                 days=int(e3.date.nunique())))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RES, "holdout.csv"), index=False)
    with open(os.path.join(RES, "calibration.txt"), "w") as f:
        f.write(cal + "\n")
    print(cal)
    return out


if __name__ == "__main__":
    du = pd.read_parquet(os.path.join(ROOT, "data", "duka_h1.parquet"))
    du["ts"] = pd.to_datetime(du.ts, utc=True)
    print(run(du).round(3).to_string())
