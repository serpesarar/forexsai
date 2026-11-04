"""Engine.outcome'u kaba döngüyle karşılaştır (rastgele 3.000 giriş × 6 geometri × 2 yön × 3 aynı-bar modu)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofl  # noqa: E402

N = ofl.N
df = ofl.load_frame()
g = ofl.build_grid(df)
del df
fc_next, blocked = ofl.rollover_cap()
hcap = fc_next - np.arange(N)
entry_ok = ofl.valid_entries(g) & ~blocked & (hcap >= 5)
atr5 = ofl.lib.atr_5m(g)
entry_ok &= ~np.isnan(atr5)
absret = np.abs(np.diff(np.log(g["close_ff"]), prepend=np.nan)) * 1e4
thr = 30.0
eng = ofl.Engine(g, atr5, entry_ok, hcap, thr)
E = np.where(entry_ok)[0]
rng = np.random.default_rng(1)
e = np.sort(rng.choice(E, 3000, replace=False))
O, H, L, C = g["open"], g["high"], g["low"], g["close_ff"]
bad = 0
tot = 0
for geom in [("S1", 1.0, 15), ("S1", 2.0, 60), ("S2", 1.5, 30), ("S1", 1.5, 60), ("S2", 1.0, 15), ("S2", 2.0, 60)]:
    sname, r, Hh = geom
    flo, mult = ofl.SL_RULES[sname]
    for s in (1, -1):
        sd = np.full(len(e), s, dtype=np.int8)
        for mode in ("sl", "tp", "heur"):
            o = eng.outcome(e, sd, geom, amb_mode=mode, slip=True)
            for j, ei in enumerate(e):
                p0 = O[ei]
                sl = max(flo, mult * atr5[ei] / p0 * 1e4)
                Hp = min(Hh, hcap[ei])
                tpl = p0 * (1 + s * r * sl / 1e4)
                sll = p0 * (1 - s * sl / 1e4)
                res = None
                for k in range(Hp):
                    b = ei + k
                    hit_tp = (H[b] >= tpl) if s == 1 else (L[b] <= tpl)
                    hit_sl = (L[b] <= sll) if s == 1 else (H[b] >= sll)
                    if hit_tp and hit_sl:
                        if mode == "tp":
                            hit_sl = False
                        elif mode == "sl":
                            hit_tp = False
                        else:
                            if abs(O[b] - tpl) < abs(O[b] - sll):
                                hit_sl = False
                            else:
                                hit_tp = False
                    if hit_tp:
                        res = r * sl
                        break
                    if hit_sl:
                        gap = s * (O[b] / p0 - 1) * 1e4
                        res = min(-sl, gap) - (5.0 if absret[b] > thr else 1.0)
                        break
                if res is None:
                    res = s * (C[ei + Hp - 1] / p0 - 1) * 1e4
                tot += 1
                if abs(res - o["ret"][j]) > 1e-6:
                    bad += 1
print("uyuşmazlık", bad, "/", tot)
# rollover: hiçbir işlem RO-2'yi geçmemeli
print("hcap min", hcap[E].min(), "blocked giriş", blocked[E].sum())
