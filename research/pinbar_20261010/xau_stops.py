"""XAU 1h yeni tepe BUY: koruyucu stoplu sürümler (ön kayıt: SL ∈ {yok, 1,5, 2, 3}×ATR, çıkış 20 mum veya stop;
stop aynı mumda → stop fiyatı, boşlukta açılış). R birimi: SL varsa SL mesafesi, yoksa ATR. Tek pozisyon."""
import importlib.util as u
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
d = pd.read_parquet(HERE / "data/XAUUSD_1h.parquet"); d = d[d.ts < "2026-09-03"].reset_index(drop=True); F = S.features(d)
o, h, l, c, seg, atr = F["o"], F["h"], F["l"], F["c"], F["seg"], F["atr"]; n = len(o); SPR, H = 0.25, 20
idx = np.where(D.pin_mask(F, kind="hepsi"))[0]
for k in (None, 1.5, 2.0, 3.0):
    res, busy, yrs = [], -1, []
    for i in idx:
        e = i + 1
        if i <= busy or e + H - 1 >= n or seg[e] != seg[i] or seg[e + H - 1] != seg[i]: continue
        A = atr[i]; ent = o[e] + SPR; unit = (k * A) if k else A; out = None
        for j in range(e, e + H):
            if k and l[j] <= ent - k * A:
                out = (min(o[j], ent - k * A) if j > e else ent - k * A); last = j; break
        if out is None: out, last = c[e + H - 1], e + H - 1
        res.append((out - ent) / unit); busy = last; yrs.append(pd.Timestamp(F["ts"].iat[i]).year)
    r = np.array(res); s = pd.Series(r).groupby(yrs).mean()
    print(f"SL {'yok' if k is None else f'{k}×ATR':7} n={len(r)} ortR {r.mean():+.3f} WR %{100*(r>0).mean():.1f} en kötü {r.min():+.2f}R "
          f"pozitif yıl {(s>0).sum()}/{len(s)}  yıllar {dict(s.round(2))}")
