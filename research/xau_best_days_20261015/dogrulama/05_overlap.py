"""ADIM 5 (POST-HOC, verdikt girdisi DEĞİL — betimsel): S1 ve S2 örtüşmesi; S2'nin S1 dışındaki ve içindeki etkisi;
ileri kümelerde 2×2. Çıktı: results/05_log.txt"""
import os, numpy as np, pandas as pd
from common import RES, one_position
b = pd.read_parquet(os.path.join(RES, "base.parquet")); fw = pd.read_parquet(os.path.join(RES, "fwd_events.parquet"))
e = pd.read_parquet(os.path.join(RES, "allev.parquet")).sort_values("ent").reset_index(drop=True)
L = []
def say(s=""): L.append(str(s)); print(s)
def tab(B, nm):
    t = B.groupby(["S1", "S2"]).R.agg(["size", "mean", "sum"]).round(3)
    say(f"[{nm}] tek-poz 2×2 (S1=seri≥2, S2=önceki gün>%1):\n{t.to_string()}")
tab(b, "ana"); [tab(X[X.base], s) for s, X in fw.groupby("set")]
say(f"S2'nin S1 içindeki payı: {(b.S1 & b.S2).sum()}/{b.S2.sum()} = {(b.S1 & b.S2).sum()/b.S2.sum():.2f}")
for nm, m in (("S1 içinde", b.S1), ("S1 dışında", ~b.S1)):
    s = b[m]; say(f"  {nm}: S2 farkı {s.R[s.S2].mean() - s.R[~s.S2].mean():+.3f} (n_on={int(s.S2.sum())}/{len(s)})")
for nm, m in (("S2 içinde", b.S2), ("S2 dışında", ~b.S2)):
    s = b[m]; say(f"  {nm}: S1 farkı {s.R[s.S1].mean() - s.R[~s.S1].mean():+.3f} (n_on={int(s.S1.sum())}/{len(s)})")
# S2 değeri neden S1 ile örtüşüyor: önceki gün +%1 olan işlemlerin dens24 dağılımı
say("dens24 medyanı: S2 " + f"{b.dens24[b.S2].median():.0f}" + f" vs ¬S2 {b.dens24[~b.S2].median():.0f}")
# filtre: yalnız S2∧¬S1 atla (S1'den bağımsız kısım)
ent, dur = e.ent.to_numpy(), e.dur.to_numpy()
for nm, F in (("S2∧¬S1", e.S2 & ~e.S1), ("S2", e.S2), ("S1", e.S1)):
    idx = np.where(~F.to_numpy())[0]; k = one_position(ent[idx], ent[idx] + dur[idx]); r = e.R.to_numpy()[idx][k]
    say(f"  ATLA {nm:<7}: n={len(r)} ortR {r.mean():+.4f} toplam {r.sum():.1f}")
# SL / zaman çıkışı oranı bayraklara göre
say("çıkış kodu payları (ana tek-poz):"); say(pd.crosstab([b.S1, b.S2], b.code, normalize="index").round(3).to_string())
# işlem sırası: S1 işlemi bir önceki işlemin SL'inden hemen sonra mı? (önceki tek-poz işlemin çıkışından bu yana bar)
b = b.sort_values("ent"); gap = b.ent.to_numpy()[1:] - b.xi.to_numpy()[:-1]; prevc = b.code.to_numpy()[:-1]
g = pd.DataFrame({"S1": b.S1.to_numpy()[1:], "gap": gap, "prevSL": prevc == "SL"})
say(g.groupby("S1").agg(gap_med=("gap", "median"), prevSL=("prevSL", "mean")).round(3).to_string())
open(os.path.join(RES, "05_log.txt"), "w").write("\n".join(L) + "\n")
