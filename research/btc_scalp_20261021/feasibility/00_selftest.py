"""first_hit'i kaba döngüyle karşılaştır (rastgele 3.000 giriş × 3 seviye × 2 yön) + önek (sızıntı) testi."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

g = lib.load_grid()
e_all = lib.entries(g)
rng = np.random.default_rng(7)
e = np.sort(rng.choice(e_all, 3000, replace=False))
MX, MN = lib.sparse_tables(g["high"], g["low"])
p0 = g["open"][e]
bad = 0
for b in [5, 30, 150]:
    f = b / 1e4
    ku = lib.first_hit(MX, e, p0 * (1 + f), lib.LMAX, True)
    kd = lib.first_hit(MN, e, p0 * (1 - f), lib.LMAX, False)
    for i, ei in enumerate(e):
        hh = g["high"][ei:ei + lib.LMAX]
        ll = g["low"][ei:ei + lib.LMAX]
        wu = np.where(hh >= p0[i] * (1 + f))[0]
        wd = np.where(ll <= p0[i] * (1 - f))[0]
        bu = wu[0] if len(wu) else lib.LMAX
        bd = wd[0] if len(wd) else lib.LMAX
        bad += (bu != ku[i]) + (bd != kd[i])
print("uyuşmazlık:", bad, "/", 3000 * 6)

# önek testi: gelecekteki barları değiştirmek, karar anındaki ATR/RV özelliklerini değiştirmemeli
a1 = lib.atr_1m(g); a5 = lib.atr_5m(g); rv = lib.rv_24h(g)
cut = e_all[len(e_all) // 2]
g2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in g.items()}
for c in ["open", "high", "low", "close", "close_ff"]:
    g2[c][cut:] = g2[c][cut:] * 1.37
b1 = lib.atr_1m(g2); b5 = lib.atr_5m(g2); rv2 = lib.rv_24h(g2)
sl = slice(cut - 5000, cut + 1)  # karar anı e=cut dahil (bilgi e-1'e kadar)
for nm, x, y in [("atr1", a1, b1), ("atr5", a5, b5), ("rv", rv, rv2)]:
    same = np.allclose(x[sl], y[sl], equal_nan=True)
    print(f"önek {nm}: {'OK' if same else 'SIZINTI'}")
