"""POST-HOC (verdikt DEĞİL): R0B_G1 tek-pozisyon R dağılımı, düşüş, yıllık toplamlar, SL$ yıl medyanı → results/posthoc_onepos.txt"""
import os, numpy as np, pandas as pd
from run_main import load_main, sim_cell
from rules import events, GEOM
from mech import one_position
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
d = load_main(); ev = events(d, "R0", +1); tp, sl, hold = GEOM["R0"][0]
R, xi, code, hl = sim_cell(d, ev, tp, sl, hold, +1, 0.12); m = np.isfinite(R)
k = one_position(ev.ent.to_numpy()[m], xi[m]); r = R[m][k]; e = ev[m][k]
cum = np.cumsum(r); L = []
L.append(f"R0B_G1 tek-poz n={len(r)} sd={r.std():.3f} p10/50/90={np.percentile(r,[10,50,90]).round(2).tolist()} maks={r.max():.2f} WR={(r>0).mean():.3f}")
L.append(f"toplam R={cum[-1]:.1f} maks düşüş R={(cum-np.maximum.accumulate(cum)).min():.1f}")
L.append("yıllık toplam R: " + pd.Series(r).groupby(e.year.to_numpy()).sum().round(1).to_string().replace("\n", " | "))
w = pd.Series(r).groupby(pd.to_datetime(e.date).dt.to_period("W").to_numpy()).sum()
L.append(f"pozitif hafta oranı={(w>0).mean():.3f} haftalık sd={w.std():.2f}R")
L.append("SL$ (1,5×ATR_H1) yıl medyanı: " + str(pd.Series(ev.atr.to_numpy()[m][k]*1.5).groupby(e.year.to_numpy()).median().round(1).to_dict()))
open(os.path.join(RES, "posthoc_onepos.txt"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
