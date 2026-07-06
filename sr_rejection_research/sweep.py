"""
Faz 3 — SWEEP: model × TF × tolerans × kaynak(S/R, channel) → rejection-uyumlu WR.
Her sinyal: yön-uyumlu rejection mı (destek+BUY / direnç+SELL, tolerans içinde, touched)?
Çıktı: sweep_results.json + ekrana en iyi lift'ler.
"""
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
TFS = ["5m", "15m", "30m", "1h", "4h"]
TOLS = [0.03, 0.06, 0.10, 0.15, 0.20, 0.30, 0.50]   # fiyatın %'si
MIN_N = 80

recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
print(f"{len(recs)} özellikli sinyal yüklendi.\n")


def aligned(rec, tf, tol, source):
    f = rec["f"].get(tf)
    if not f:
        return None                      # bu TF yok → universe dışı
    d = rec["dir"]
    if source == "sr":
        if d == "BUY":
            ok = f["d_sup"] is not None and f["d_sup"] < tol and f["touched_sup"]
        else:
            ok = f["d_res"] is not None and f["d_res"] < tol and f["touched_res"]
    else:  # channel
        if d == "BUY":
            ok = 0 <= f["d_chan_low"] < tol
        else:
            ok = 0 <= f["d_chan_up"] < tol
    return bool(ok)


def wr(rows):
    return sum(1 for r in rows if r["win"]) / len(rows) if rows else 0.0


# model bazında grupla
by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

results = []
for model, rows in by_model.items():
    if len(rows) < 200:
        continue
    for tf in TFS:
        universe = [r for r in rows if tf in r["f"]]   # bu TF özelliği olanlar
        if len(universe) < MIN_N:
            continue
        base = wr(universe)
        for source in ("sr", "channel"):
            for tol in TOLS:
                al = [r for r in universe if aligned(r, tf, tol, source)]
                if len(al) < MIN_N:
                    continue
                w = wr(al)
                results.append({"model": model, "tf": tf, "source": source,
                                "tol": tol, "n": len(al), "wr": round(w, 4),
                                "base_wr": round(base, 4), "lift": round(w - base, 4),
                                "n_universe": len(universe)})

results.sort(key=lambda x: -x["lift"])
json.dump(results, open(ROOT / "sweep_results.json", "w"), indent=1)
print(f"{len(results)} kombinasyon tarandı (n≥{MIN_N}).\n")
print("=== EN İYİ 25 LİFT (rejection-uyumlu WR > baseline) ===")
print(f"{'model':16s}{'tf':4s}{'kaynak':8s}{'tol%':6s}{'n':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}")
for r in results[:25]:
    print(f"{r['model']:16s}{r['tf']:4s}{r['source']:8s}{r['tol']:<6}{r['n']:>6d}"
          f"{r['wr']*100:>6.1f}%{r['base_wr']*100:>6.1f}%{r['lift']*100:>+6.1f}")

print("\n=== EN KÖTÜ 8 (rejection ZARAR veriyor — ters sinyal adayı) ===")
for r in results[-8:]:
    print(f"{r['model']:16s}{r['tf']:4s}{r['source']:8s}{r['tol']:<6}{r['n']:>6d}"
          f"{r['wr']*100:>6.1f}%{r['base_wr']*100:>6.1f}%{r['lift']*100:>+6.1f}")
