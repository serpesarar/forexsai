"""trade_eval_null.py — 'seçimde en iyi K model → sınama' sonucunun plasebo dağılımı (ön kayıt: K=20 ve 50,
30 plasebo tekrarı; her tekrarda her modelin girişleri aynı sayıda rastgele zamanla değiştirilir, seçim aynı).
Tek-taraflı p = plasebo top-K sınama ortalamasının gerçekteki değerden ≥ olma oranı. Ayrıca top-K'nın
TF/yön/geometri dağılımı ve zaman kümelenmesi (kaç farklı gün)."""
import json, sys, time
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import trade_eval as E
from run_seq import TF
from seq_engine import run_lengths

REPS, KS = 30, (20, 50)
o = json.loads((HERE / "results" / "seq_scan.json").read_text())
cache = []          # (tf, T, entries, R_real_result)
for t in o["tfs"]:
    T = TF(t["tf"]); run = run_lengths(T.brk)
    vi = np.where(np.r_[T.seg[1:] == T.seg[:-1], False])[0]
    for m in [m for m in t["exact"]["motifs"] + t.get("partial", {}).get("motifs", []) if m["fwd"]["n"] >= E.MIN_OCC]:
        occ = E.occurrences(T, run, m); ent = occ + m["k"]; ent = ent[ent < len(T.o)]; ent = ent[T.seg[ent] == T.seg[ent - 1]]
        R = E.trade_R(T.o, T.h, T.l, T.c, T.seg, ent, E.atr_at(T, ent), E.TPS, E.SLS, E.MAX_HOLD, E.SPREAD)
        r = E.select_and_test(R, ent)
        if r is not None:
            pool = vi[(vi >= ent.min()) & (vi <= ent.max())]
            cache.append((t["tf"], T, len(ent), pool, r, ent))
print("model:", len(cache))

def topk(results, K):
    top = sorted(results, key=lambda r: -r["is_R"])[:K]
    return float(np.mean([r["oos_R"] for r in top])), top

real = [c[4] for c in cache]
obs = {K: topk(real, K)[0] for K in KS}
rng = np.random.default_rng(7); null = {K: [] for K in KS}; t0 = time.time()
for rep in range(REPS):
    res = []
    for tf, T, n, pool, r, ent in cache:
        pe = np.sort(rng.choice(pool, size=min(n, len(pool)), replace=False))
        Rp = E.trade_R(T.o, T.h, T.l, T.c, T.seg, pe, E.atr_at(T, pe), E.TPS, E.SLS, E.MAX_HOLD, E.SPREAD)
        rp = E.select_and_test(Rp, pe)
        if rp is not None: res.append(rp)
    for K in KS: null[K].append(topk(res, K)[0])
print(f"plasebo süresi {time.time()-t0:.0f}s")
out = {}
for K in KS:
    nv = np.array(null[K]); p = float((nv >= obs[K]).mean())
    out[K] = {"gercek": round(obs[K], 3), "plasebo_ort": round(float(nv.mean()), 3), "plasebo_%95": round(float(np.percentile(nv, 95)), 3), "p": p}
    print(f"seçimde en iyi {K}: gerçek sınama ortR {obs[K]:+.3f} | plasebo ort {nv.mean():+.3f}, %95 üst {np.percentile(nv,95):+.3f}, max {nv.max():+.3f} | p={p:.2f}")
(HERE / "results" / "trade_eval_null.json").write_text(json.dumps(out, indent=1))
_, top = topk(real, 20)
from collections import Counter
print("top-20 TF:", Counter(c[0] for c in cache if c[4] in top), " yön:", Counter(r["dir"] for r in top), " geometri:", Counter(f"TP{r['tp']}/SL{r['sl']}" for r in top))
