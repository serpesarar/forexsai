"""Motor yansızlık testi: 1m barları (göreli o/h/l/c bütün olarak) karıştırılıp yeniden kurulan yol ≈ martingal.
Spread 0'da stoplu/zaman çıkışlı tabanların ortR'si ≈ 0 olmalı (her iki yön)."""
import sys; sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend")
import numpy as np, lib_trend as lt, run_trend as rt
m1 = lt.M1()
CL = {c["name"]: c for c in rt.cells(rt.frames(m1), m1)}
bases = {nm: CL[nm]["base"] for nm in ("H3-ROD", "R0B-L", "H4D20-L", "MOM-L-G1")}
cp = np.concatenate([[m1.O[0]], m1.C[:-1]])
rel = np.vstack([m1.O / cp, m1.H / cp, m1.L / cp, m1.C / cp]).T
rel[0] = [1, 1, 1, 1]
for rep in range(2):
    rng = np.random.default_rng(rep)
    rr = rel[rng.permutation(len(rel))]
    C = m1.C[0] * np.cumprod(rr[:, 3])
    pc = np.concatenate([[m1.C[0]], C[:-1]])
    m1.O, m1.H, m1.L, m1.C = pc * rr[:, 0], pc * rr[:, 1], pc * rr[:, 2], C
    pad = (1 << m1.levels) + 2
    m1.mn = [np.concatenate([m1.L, np.full(pad, np.inf)])]; m1.mx = [np.concatenate([m1.H, np.full(pad, -np.inf)])]
    for lv in range(1, m1.levels):
        s = 1 << (lv - 1); a, b = m1.mn[-1], m1.mx[-1]
        m1.mn.append(np.minimum(a, np.concatenate([a[s:], np.full(s, np.inf)])))
        m1.mx.append(np.maximum(b, np.concatenate([b[s:], np.full(s, -np.inf)])))
    for nm, b in bases.items():
        for d in (1, -1):
            s = b[b["dir"] == 1].copy(); s["dir"] = d
            # ATR'yi sentetik yolun ölçeğine taşı: SL = mesafe oranı aynı (sl/fiyat), fiyat = sentetik
            k = np.searchsorted(m1.T, s["dec"].to_numpy())
            k = np.minimum(k, m1.N - 1)
            ratio = s["sl"].to_numpy() / CL[nm]["base"]["sig"].to_numpy()[: len(s)] if False else None
            r = m1.simulate(s["dec"], s["dir"], s["sl"] / s["sig"] * m1.O[k], s["tp"] / s["sig"] * m1.O[k],
                            s["end"], m1.O[k], spread=0.0)
            R = r["R"][np.isfinite(r["R"])]
            # swap'ı çıkar: yalnız fiyat kısmı
            print(f"rep{rep} {nm:9s} dir={d:+d} n={len(R)} ortR={R.mean():+.4f} ± {R.std()/np.sqrt(len(R)):.4f}")
