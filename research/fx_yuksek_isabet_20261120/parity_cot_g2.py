"""COT-G2 gölge modülü (yeni deneme/cot_g2_shadow.py) ↔ araştırma (ek23.g2) birebirlik: aynı TFF verisinden haftalık karar (çift, yön)."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "yeni deneme"))
import cot_g2_shadow as sh
import core, ek18b, ek23

# modül: ham dosyalardan kendi ayrıştırıcısıyla
S = {c: {} for c in sh.CODES.values()}
for f in sorted(glob.glob(str(core.HERE / "data/cot_tff_hist/h/*.txt"))) + sorted(glob.glob(str(core.HERE / "data/cot_raw/fut_fin_txt_*/*.txt"))):
    part = sh.parse_tff(Path(f).read_text(encoding="utf-8", errors="replace"))
    for c, s in part.items():
        S[c].update(s)
reps = sorted(set().union(*[set(s) for s in S.values()]))
mod = {}
for r in reps:
    sel = sh.select({c: sh.zscore_last(S[c], r) for c in sh.CODES.values()})
    if sel:
        mod[pd.Timestamp(r)] = sel[:2]
# araştırma: ek23.g2'nin karar adımını yeniden üret (işlem simülasyonundan önce)
ek18b.HIST = True
Z = ek18b.tff()
W = Z[Z.code.isin(ek23.CCY)].pivot_table(index="rep", columns="code", values="zP")
W.columns = [ek23.CCY[c] for c in W.columns]; W["USD"] = 0.0
res = {}
for rep, row in W.dropna(thresh=6).iterrows():
    row = row.dropna(); hi, lo = row.idxmax(), row.idxmin()
    if row[hi] - row[lo] < 2.0: continue
    if hi + lo in ek23.AV: res[rep] = (hi + lo, -1)
    elif lo + hi in ek23.AV: res[rep] = (lo + hi, 1)
    else:
        k = hi if abs(row[hi]) >= abs(row[lo]) else lo; p, s = ek23.usd_pair(k); res[rep] = (p, -s if k == hi else s)
skipped = set(pd.Timestamp(x) for x in reps) - set(Z.rep)   # araştırmanın atladığı kapanma haftaları
common = sorted((set(mod) | set(res)) - skipped)
same = sum(mod.get(d) == res.get(d) for d in common)
diff = [(str(d.date()), mod.get(d), res.get(d)) for d in common if mod.get(d) != res.get(d)]
print("hafta", len(common), "aynı", same, "farklı", len(diff)); print(diff[:15])
