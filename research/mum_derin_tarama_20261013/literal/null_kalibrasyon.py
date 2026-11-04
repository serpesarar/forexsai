"""Null kalibrasyon denetimi: hafta kaydırmalı null'da aktif yapılandırmaların ORTALAMA fazlası gerçektekine benziyor mu?
(Seçim düzeltmesinin muhafazakâr/serbest olup olmadığını gösterir.) Çalıştır: python3 null_kalibrasyon.py"""
import numpy as np, pandas as pd
from _lit import RES, load
from evaluate import TFS, WEEK, shifted_sign, R_NULL
fam = pd.read_csv(RES / "aile.csv"); rng = np.random.default_rng(777); weeks = rng.integers(2, 10**6, size=R_NULL)[:20]
rows = []
for tf in TFS:
    D = load(tf); Q = np.load(RES / f"q_{tf}.npz"); Z = np.load(RES / f"calls_{tf}.npz"); C, Hc = Z["C"], Z["H"]; tq = Q["tq"]
    f = fam[(fam.tf == tf) & fam.cid.notna()].sort_values("cid"); nW = int((tq[-1] - tq[0]) // WEEK) + 1
    for h in np.unique(Hc):
        rr = np.flatnonzero(Hc == h)
        real = f.fazla.to_numpy()[rr]
        S = np.stack([shifted_sign(D, tq, int(2 + w % max(nW - 4, 1)), h) for w in weeks], 1)
        Sp = (S == 1).astype(np.float32); Sn = (S == -1).astype(np.float32); Snz = Sp + Sn
        bcs = [((B[:, None] == S) & (S != 0)).astype(np.float32) + 0.5 * ((B[:, None] == 0) & (S != 0)) for B in (Q["B0"][h], Q["BH"][h])]
        Cp = (C[rr] == 1).astype(np.float32); Cn = (C[rr] == -1).astype(np.float32); Cz = Cp + Cn
        called = np.maximum(Cz @ Snz, 1); acc = (Cp @ Sp + Cn @ Sn) / called
        exc = 100 * (acc - np.maximum((Cz @ bcs[0]) / called, (Cz @ bcs[1]) / called))
        rows.append(dict(tf=tf, ufuk=f.ufuk.iloc[rr[0]], yapi=len(rr), gercek_ort=real.mean(), null_ort=exc.mean(),
                         gercek_p95=np.percentile(real, 95), null_p95=np.percentile(exc, 95), gercek_max=real.max(),
                         null_max_med=np.median(exc.max(0)), gercek_pay_ge2=(real >= 2).mean(), null_pay_ge2=(exc >= 2).mean()))
out = pd.DataFrame(rows); out.to_csv(RES / "null_kalibrasyon.csv", index=False); print(out.round(2).to_string())
