"""Sızıntı (önek) testi: cut'tan sonraki fiyat/hacmi boz → cut−1'e kadar olan tetikler birebir aynı kalmalı."""
import numpy as np
import common as C
import signals as S

g = C.Grid()
cut = C.tm("2023-06-15 13:37")
V0 = S.all_variants(g)
rng = np.random.default_rng(5)
f = np.exp(np.cumsum(rng.normal(0, 0.002, g.N - cut)))
for a in (g.O, g.H, g.L, g.C, g.CF):
    a[cut:] = a[cut:] * f
g.H[cut:] *= 1.001; g.L[cut:] *= 0.999
g.V[cut:] *= rng.uniform(0.2, 5, g.N - cut); g.Q[cut:] = g.V[cut:] * g.C[cut:]
n5 = g.N // 5
g._atr5()
V1 = S.all_variants(g)
bad = 0
for k in V0:
    t0, d0, *_ = V0[k]; t1, d1, *_ = V1[k]
    a = sorted(zip(t0[t0 < cut - 1], d0[t0 < cut - 1])); b = sorted(zip(t1[t1 < cut - 1], d1[t1 < cut - 1]))
    ok = a == b
    bad += not ok
    print(f"{k:16s} n_before={len(a):6d} {'OK' if ok else 'FARK'}")
print("SONUÇ:", "OK" if bad == 0 else f"{bad} varyant farklı")
