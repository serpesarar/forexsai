"""MOM-H bağımsız piyasa sınavı — PROTOCOL_MOMH.md'ye birebir."""
import sys, importlib.util as u
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
SPR = {"XAUUSD": 0.25, "USOIL": 0.03}

def low_mask(F, look=20):
    lo = pd.Series(F["l"]).shift(1).rolling(look).min().to_numpy()
    return np.nan_to_num(F["l"] <= lo, nan=0).astype(bool) & F["ok"]

def run(F, spr, mask, side):
    idx = np.where(mask)[0]
    o, c, seg, atr = F["o"], F["c"], F["seg"], F["atr"]; n = len(o)
    def tx(ix):
        e = ix + 1; ok = e + 19 < n; e, ix = e[ok], ix[ok]
        ok = (seg[e] == seg[ix]) & (seg[e + 19] == seg[ix]); e, ix = e[ok], ix[ok]
        return side * (c[e + 19] - o[e]) / atr[ix] - spr / atr[ix], ix
    R, ii = tx(idx); B, _ = tx(np.where(F["ok"])[0][::3])
    no = D.nonoverlap(ii, 20)
    day = pd.Series(R - B.mean(), index=pd.to_datetime(F["ts"].to_numpy()[ii], utc=True).date).groupby(level=0).sum().sort_values(ascending=False)
    h = len(R) // 2
    return {"n": len(R), "fark": R.mean() - B.mean(), "tekpoz_fark": R[no].mean() - B.mean(), "ex5": day.sum() - day.head(5).sum(),
            "y1": (R[:h] - B.mean()).mean(), "y2": (R[h:] - B.mean()).mean()}

rows = []
for cut in (None, "2026-09-03"):
    for sym in ("XAUUSD", "USOIL"):
        for tf in ("15m", "30m", "1h"):
            d = pd.read_parquet(HERE / "data" / f"{sym}_{tf}.parquet")
            if cut: d = d[d.ts < cut].reset_index(drop=True)
            F = S.features(d)
            for name, mask, side in (("H1 yeni tepe BUY", D.pin_mask(F, kind="hepsi"), 1), ("H1b güçlü kapanış", D.pin_mask(F, kind="guclu"), 1),
                                     ("Ayna yeni dip SELL", low_mask(F), -1)):
                r = run(F, SPR[sym], mask, side); r.update(set=f"{sym} {tf}", kural=name, veri="Yahoo hariç" if cut else "tümü"); rows.append(r)
x = pd.DataFrame(rows)
for (veri, kural), g in x.groupby(["veri", "kural"], sort=False):
    ok = (g.fark > 0).all() and (g.tekpoz_fark > 0).all() and (g.ex5 > 0).all() and g.y1.mean() > 0 and g.y2.mean() > 0
    print(f"\n[{veri}] {kural}: {'GEÇTİ' if ok else 'GEÇMEDİ'}")
    for r in g.itertuples():
        print(f"   {r.set:12} n={r.n:5} fark {r.fark:+.3f}  tek-poz {r.tekpoz_fark:+.3f}  5gün-hariç {r.ex5:+7.1f}  yarılar {r.y1:+.3f}/{r.y2:+.3f}")
x.to_csv(HERE / "results" / "momh.csv", index=False)
