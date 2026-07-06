"""
Faz 4 — TİTİZLİK: walk-forward (zaman OOS) + placebo (çoklu-test şişmesi).
In-sample lift'ler güzel ama (a) zamanda tutuyor mu, (b) 697 combo taramasının
şansı mı? Placebo: etiketleri karıştırıp aynı taramada en iyi lift dağılımı.
"""
import json, random
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
TFS = ["5m", "15m", "30m", "1h", "4h"]
TOLS = [0.03, 0.06, 0.10, 0.15, 0.20, 0.30, 0.50]
MIN_N = 80

recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])               # zaman sırası (walk-forward için)
wins = [r["win"] for r in recs]


def is_aligned(rec, tf, tol, source):
    f = rec["f"].get(tf)
    if not f:
        return None
    d = rec["dir"]
    if source == "sr":
        return (f["d_sup"] is not None and f["d_sup"] < tol and f["touched_sup"]) if d == "BUY" \
            else (f["d_res"] is not None and f["d_res"] < tol and f["touched_res"])
    return (0 <= f["d_chan_low"] < tol) if d == "BUY" else (0 <= f["d_chan_up"] < tol)


# --- her combo için universe & aligned index listeleri (bir kez) ---
by_model = defaultdict(list)
for idx, r in enumerate(recs):
    by_model[r["model"]].append(idx)

combos = {}     # key -> (universe_idx[], aligned_idx[])
for model, idxs in by_model.items():
    if len(idxs) < 200:
        continue
    for tf in TFS:
        uni = [i for i in idxs if tf in recs[i]["f"]]
        if len(uni) < MIN_N:
            continue
        for source in ("sr", "channel"):
            for tol in TOLS:
                al = [i for i in uni if is_aligned(recs[i], tf, tol, source)]
                if len(al) >= MIN_N:
                    combos[(model, tf, source, tol)] = (uni, al)


def wr(idxs, labels):
    return sum(labels[i] for i in idxs) / len(idxs) if idxs else 0.0


def lift(uni, al, labels):
    return wr(al, labels) - wr(uni, labels)


# --- gerçek lift ---
real = {k: lift(u, a, wins) for k, (u, a) in combos.items()}

# --- PLACEBO: etiket karıştır, tüm combo'larda en iyi lift dağılımı ---
M = 60
placebo_max = []
shuf = wins[:]
for _ in range(M):
    random.shuffle(shuf)
    best = max(lift(u, a, shuf) for (u, a) in combos.values())
    placebo_max.append(best)
placebo_max.sort()
p95 = placebo_max[int(0.95 * len(placebo_max))]
p99 = placebo_max[-1]
print(f"PLACEBO (etiket karışık, {len(combos)} combo): en iyi-lift şans dağılımı "
      f"p50={placebo_max[len(placebo_max)//2]*100:+.1f}  p95={p95*100:+.1f}  max={p99*100:+.1f}")
print(f"→ Gerçek lift bu eşiği geçmeli; geçmeyen = şans.\n")

# --- WALK-FORWARD: zaman 60/40 split, test döneminde lift ---
cut = int(0.60 * len(recs))
test_set = set(range(cut, len(recs)))


def split_lift(uni, al):
    ut = [i for i in uni if i in test_set]
    at = [i for i in al if i in test_set]
    if len(at) < 30 or len(ut) < 30:
        return None, len(at)
    return wr(at, wins) - wr(ut, wins), len(at)


rows = []
for k, (u, a) in combos.items():
    tl, tn = split_lift(u, a)
    rows.append({"k": k, "n": len(a), "real": real[k], "test_lift": tl, "test_n": tn,
                 "passes_placebo": real[k] > p95})

# sıralama: placebo'yu geçen + test'te pozitif + yüksek n
rows.sort(key=lambda r: -(r["real"] if r["real"] else -9))
print("=== EN İYİ COMBO'LAR — in-sample + OOS + placebo ===")
print(f"{'model':16s}{'tf':4s}{'kayn':8s}{'tol':5s}{'n':>6s}{'IS-lift':>8s}{'OOS-lift':>9s}{'placebo':>9s}")
shown = 0
for r in rows:
    if r["n"] < 150:
        continue
    m, tf, src, tol = r["k"]
    oos = f"{r['test_lift']*100:+.1f}" if r["test_lift"] is not None else "  —"
    pl = "✅geçti" if r["passes_placebo"] else "❌şans"
    print(f"{m:16s}{tf:4s}{src:8s}{str(tol):5s}{r['n']:>6d}{r['real']*100:>+7.1f}{oos:>9s}{pl:>9s}")
    shown += 1
    if shown >= 22:
        break

json.dump([{"combo": list(r["k"]), **{x: r[x] for x in ("n", "real", "test_lift", "passes_placebo")}}
           for r in rows], open(ROOT / "rigor_results.json", "w"), indent=1, default=str)
