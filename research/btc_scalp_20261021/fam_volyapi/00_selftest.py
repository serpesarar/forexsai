"""Motor öz-sınaması: resolve() ↔ kaba döngü (rastgele 3.000 giriş × 2 yön × 4 geometri) + ATR5 nedensellik (önek) testi."""
import time
import numpy as np
import common as C

t0 = time.time()
g = C.Grid()
g.precompute()
print(f"yükleme+ön-hesap {time.time()-t0:.0f} s; geçerli giriş {g.valid.sum():,} / {g.N:,}")
rng = np.random.default_rng(3)
ev = np.where(g.valid)[0]
E = rng.choice(ev, 3000, replace=False)
bad = 0
tot = 0
for gname, (r, H) in C.GEOMS.items():
    for d in (1, -1):
        res = C.Grid.resolve(g, E, np.full(len(E), d), r, H)
        for i, e in enumerate(E):
            ent = g.O[e]; s = g.s_bp[e]
            Leff = min(H, g.rollleft[e])
            sl = ent * (1 - d * s / 1e4); tp = ent * (1 + d * r * s / 1e4)
            out = None
            for k in range(Leff):
                j = e + k
                hh, ll = g.H[j], g.L[j]
                if np.isnan(hh):
                    continue
                slh = (ll <= sl) if d == 1 else (hh >= sl)
                tph = (hh >= tp) if d == 1 else (ll <= tp)
                if slh:
                    f = min(sl, g.O[j]) if d == 1 else max(sl, g.O[j])
                    out = d * (f / ent - 1) * 1e4 - g.slip_bp[j]
                    break
                if tph:
                    out = r * s
                    break
            if out is None:
                out = d * (g.CF[e + Leff - 1] / ent - 1) * 1e4
            tot += 1
            if abs(out - res["g"][i]) > 1e-6:
                bad += 1
print(f"kaba döngü uyuşmazlık: {bad}/{tot}")

# önek testi: geleceği bozunca geçmiş ATR5/s_bp değişmemeli
cut = ev[len(ev) // 2]
s_before = g.s_bp[cut - 5000:cut + 1].copy()
g.H[cut + 1:] *= 1.5; g.L[cut + 1:] *= 0.5; g.C[cut + 1:] *= 1.3
g._atr5()
same = np.allclose(s_before, g.s_bp[cut - 5000:cut + 1], equal_nan=True)
print(f"önek testi ATR5/s_bp (karar ≤ cut aynı): {'OK' if same else 'HATA'}")
