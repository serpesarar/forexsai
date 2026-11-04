"""POST-HOC (verdikt DEĞİL): F2 yıllık ayrışma, F1 DiD bileşenleri, F5 yıl-karışımı. → results/posthoc.txt"""
import os, numpy as np, pandas as pd
from common import RES, one_position
ev = pd.read_parquet(os.path.join(RES, "events.parquet")); L = []
base = []
for per, e in ev.groupby("per"):
    e = e.sort_values("ent"); k = one_position(e.ent.to_numpy(), (e.ent + e.dur).to_numpy()); base.append(e[k])
b = pd.concat(base)
for f in ("F2", "F10", "F7", "F1"):
    g = b.groupby(["year", f]).R.agg(["mean", "size"]).unstack(f)
    diff = (g[("mean", True)] - g[("mean", False)])
    L.append(f"{f} yıl bazında ortR(bayraklı) − ortR(bayraksız), taban tek-poz:")
    L.append("  " + " ".join(f"{y}:{v:+.2f}(n{int(g.loc[y, ('size', True)]) if np.isfinite(g.loc[y, ('size', True)]) else 0})" for y, v in diff.items()))
    L.append(f"  pozitif yıl: 2008-16 {int((diff[diff.index <= 2016] > 0).sum())}/{int(diff[diff.index <= 2016].notna().sum())}, "
             f"2017-26 {int((diff[diff.index >= 2017] > 0).sum())}/{int(diff[diff.index >= 2017].notna().sum())}")
for per, e in ev.groupby("per"):
    for f in ("F1", "F9", "F3", "F6"):
        F = e[f].to_numpy()
        L.append(f"[{per}] {f}: R in/out {e.R[F].mean():+.3f}/{e.R[~F].mean():+.3f} | haftalık sürüklenme W in/out "
                 f"{e.W[F].mean():+.3f}/{e.W[~F].mean():+.3f} | fazla in/out {e.exc[F].mean():+.3f}/{e.exc[~F].mean():+.3f}")
# kuralın kendisi haftalık sürüklenmenin üstünde mi (bilgi)
for per, e in ev.groupby("per"):
    L.append(f"[{per}] kural ham ortR {e.R.mean():+.3f}, aynı-hafta tüm-bar BUY ortR (olay ağırlıklı) {e.W.mean():+.3f}, fazla {e.exc.mean():+.3f}")
open(os.path.join(RES, "posthoc.txt"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
