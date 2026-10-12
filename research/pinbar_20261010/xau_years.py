import sys, importlib.util as u
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
def yearly(F, spr, mask, side):
    o, c, seg, atr = F["o"], F["c"], F["seg"], F["atr"]; n = len(o)
    def tx(ix):
        e = ix + 1; ok = e + 19 < n; e, ix = e[ok], ix[ok]; ok = (seg[e] == seg[ix]) & (seg[e + 19] == seg[ix]); e, ix = e[ok], ix[ok]
        return side * (c[e + 19] - o[e]) / atr[ix] - spr / atr[ix], ix
    R, ii = tx(np.where(mask)[0]); B, bi = tx(np.where(F["ok"])[0][::3])
    y = pd.to_datetime(F["ts"].to_numpy()[ii], utc=True).year; yb = pd.to_datetime(F["ts"].to_numpy()[bi], utc=True).year
    base = pd.Series(B).groupby(yb).mean()
    no = D.nonoverlap(ii, 20)
    s = pd.DataFrame({"y": y, "R": R}); s["fark"] = s.R - s.y.map(base)
    t = pd.DataFrame({"y": y[no], "R": R[no]}); t["fark"] = t.R - t.y.map(base)
    return s.groupby("y").fark.agg(["size", "mean"]).round(3), t.groupby("y").fark.mean().round(3)
d = pd.read_parquet(HERE / "data/XAUUSD_1h.parquet"); d = d[d.ts < "2026-09-03"].reset_index(drop=True); F = S.features(d)
lo = np.nan_to_num(F["l"] <= pd.Series(F["l"]).shift(1).rolling(20).min().to_numpy(), nan=0).astype(bool) & F["ok"]
for name, m, side in (("XAU 1h yeni tepe BUY", D.pin_mask(F, kind="hepsi"), 1), ("XAU 1h yeni dip SELL", lo, -1)):
    a, b = yearly(F, 0.25, m, side)   # taban: o YILIN rastgele aynı-yön girişi (yıl içi sürüklenme ayrı)
    a["tek_poz"] = b
    print(f"\n{name} — yıl başına (taban = aynı yılın aynı yönlü rastgele girişi):\n{a.to_string()}\npozitif yıl: {(a['mean']>0).sum()}/{len(a)}, tek-poz pozitif yıl: {(b>0).sum()}/{len(b)}")
