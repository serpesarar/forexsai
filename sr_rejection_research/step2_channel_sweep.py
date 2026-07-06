"""
Adım 2+3 — kanal parametre sweep (n=30/50/80, z-eşik) + 1m dahil tüm TF.
z = (price-mid)/sd = pm/spp (trend çizgisinden σ-uzaklık). BUY: z≤-zt, SELL: z≥zt.
Temiz tek-parametre (band-width k yerine). Placebo ile en iyiyi doğrula.
"""
import json, random
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["1m", "5m", "15m", "30m", "1h", "4h"]
NS = [30, 50, 80]
ZTS = [1.0, 1.5, 2.0, 2.5]
MIN_N = 100


def zscore(rec, tf, n):
    f = rec["f"].get(tf)
    if not f or "chan" not in f:
        return None
    c = f["chan"].get(str(n)) or f["chan"].get(n)
    if not c or c["spp"] <= 1e-9:
        return None
    return c["pm"] / c["spp"]


def aligned(rec, tf, n, zt):
    z = zscore(rec, tf, n)
    if z is None:
        return None
    return (z <= -zt) if rec["dir"] == "BUY" else (z >= zt)


def wr(rows):
    return sum(1 for r in rows if r["win"]) / len(rows) if rows else 0.0


by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

results = []
for model in ["pulse1", "pulse2", "pulse3", "meta", "smc", "emel", "ml:main", "ml:balanced"]:
    rows = by_model.get(model, [])
    if len(rows) < 300:
        continue
    for tf in TFS:
        uni = [r for r in rows if tf in r["f"] and "chan" in r["f"][tf]]
        if len(uni) < MIN_N:
            continue
        base = wr(uni)
        for n in NS:
            for zt in ZTS:
                al = [r for r in uni if aligned(r, tf, n, zt)]
                if len(al) >= MIN_N:
                    results.append({"model": model, "tf": tf, "n": n, "zt": zt,
                                    "na": len(al), "wr": wr(al), "base": base,
                                    "lift": wr(al) - base})
results.sort(key=lambda x: -x["lift"])

# placebo (çoklu-test eşiği)
combos = [(r["model"], r["tf"], r["n"], r["zt"]) for r in results]
masks = {}
for model in by_model:
    pass
# basit placebo: en iyi 40 combo için etiket-karıştır max-lift
top = results[:200]
idx_cache = {}
for r in top:
    key = (r["model"], r["tf"], r["n"], r["zt"])
    uni = [i for i, x in enumerate(recs) if x["model"] == r["model"] and r["tf"] in x["f"] and "chan" in x["f"][r["tf"]]]
    al = [i for i in uni if aligned(recs[i], r["tf"], r["n"], r["zt"])]
    idx_cache[key] = (uni, al)
wins = [r["win"] for r in recs]
M = 50
pmax = []
shuf = wins[:]
for _ in range(M):
    random.shuffle(shuf)
    best = 0
    for key, (uni, al) in idx_cache.items():
        if al and uni:
            lift = sum(shuf[i] for i in al) / len(al) - sum(shuf[i] for i in uni) / len(uni)
            best = max(best, lift)
    pmax.append(best)
pmax.sort()
p95 = pmax[int(0.95 * len(pmax))]

print(f"PLACEBO p95 (top-200 combo) = +{p95*100:.1f}pp\n")
print("=== KANAL z-SKORU SWEEP — en iyi 22 (model × TF × n × z-eşik) ===")
print(f"{'model':12s}{'tf':4s}{'n':>4s}{'zt':>5s}{'na':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}{'plcb':>6s}")
for r in results[:22]:
    pf = "✅" if r["lift"] > p95 else "·"
    print(f"{r['model']:12s}{r['tf']:4s}{r['n']:>4d}{r['zt']:>5}{r['na']:>6d}"
          f"{r['wr']*100:>6.1f}%{r['base']*100:>6.1f}%{r['lift']*100:>+6.1f}{pf:>5s}")

# 1m özel
print("\n=== 1m TF sonuçları (yeni eklendi) ===")
for r in [x for x in results if x["tf"] == "1m"][:8]:
    print(f"  {r['model']:10s} n={r['n']} z={r['zt']} → WR {r['wr']*100:.1f}% vs {r['base']*100:.1f}% "
          f"(+{r['lift']*100:.1f}pp, n={r['na']})")

json.dump(results[:100], open(ROOT / "step2_results.json", "w"), indent=1)
