"""
Faz 5 — derinleştirme: (a) per-symbol, (b) kanal-tek-başına vs model-koşullu,
(c) model başına en iyi config. Channel kaynağı kazanan → ona odak.
"""
import json
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m", "1h", "4h"]; TOLS = [0.06, 0.1, 0.15, 0.2, 0.3]


def chan_aligned(rec, tf, tol):
    f = rec["f"].get(tf)
    if not f:
        return None
    return (0 <= f["d_chan_low"] < tol) if rec["dir"] == "BUY" else (0 <= f["d_chan_up"] < tol)


def wr(rows):
    return sum(1 for r in rows if r["win"]) / len(rows) if rows else 0.0


print("=" * 74)
print("(b) KANAL-TEK-BAŞINA (tüm modeller havuz) — model gerekli mi?")
print("=" * 74)
allrows = recs
for tf in TFS:
    uni = [r for r in allrows if tf in r["f"]]
    base = wr(uni)
    for tol in (0.1, 0.2):
        al = [r for r in uni if chan_aligned(r, tf, tol)]
        if len(al) >= 100:
            print(f"  {tf:4s} tol{tol}: kanal-aligned WR={wr(al)*100:.1f}% vs base {base*100:.1f}% "
                  f"(+{(wr(al)-base)*100:.1f}pp, n={len(al)})")

print("\n" + "=" * 74)
print("(c) MODEL BAŞINA EN İYİ CHANNEL CONFIG (n≥150, IS lift)")
print("=" * 74)
by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)
print(f"{'model':16s}{'en iyi TF/tol':14s}{'n':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}")
for model in ["pulse1", "pulse2", "pulse3", "meta", "emel", "smc", "ml:main",
              "ml:balanced", "ml:full_power", "ml:ultra_safe", "ai_panel"]:
    rows = by_model.get(model, [])
    if len(rows) < 200:
        continue
    best = None
    for tf in TFS:
        uni = [r for r in rows if tf in r["f"]]
        if len(uni) < 100:
            continue
        b = wr(uni)
        for tol in TOLS:
            al = [r for r in uni if chan_aligned(r, tf, tol)]
            if len(al) >= 150:
                lift = wr(al) - b
                if best is None or lift > best[0]:
                    best = (lift, tf, tol, len(al), wr(al), b)
    if best:
        lift, tf, tol, n, w, b = best
        print(f"{model:16s}{tf+'/'+str(tol):14s}{n:>6d}{w*100:>6.1f}%{b*100:>6.1f}%{lift*100:>+6.1f}")

print("\n" + "=" * 74)
print("(a) PER-SYMBOL — pulse3 30m channel tol0.2 (tek sembol mü sürüklüyor?)")
print("=" * 74)
p3 = [r for r in recs if r["model"] == "pulse3"]
for sym in ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]:
    uni = [r for r in p3 if r["symbol"] == sym and "30m" in r["f"]]
    if len(uni) < 50:
        continue
    al = [r for r in uni if chan_aligned(r, "30m", 0.2)]
    if len(al) >= 20:
        print(f"  {sym:12s} WR={wr(al)*100:5.1f}% vs base {wr(uni)*100:5.1f}% "
              f"(+{(wr(al)-wr(uni))*100:+.1f}pp, n={len(al)}/{len(uni)})")

print("\n" + "=" * 74)
print("DİREKTİF: BUY (alt-band) vs SELL (üst-band) ayrı — yön asimetrisi?")
print("=" * 74)
for model in ["pulse1", "pulse3", "meta"]:
    rows = [r for r in by_model[model] if "30m" in r["f"]]
    for d in ("BUY", "SELL"):
        uni = [r for r in rows if r["dir"] == d]
        al = [r for r in uni if chan_aligned(r, "30m", 0.2)]
        if len(al) >= 30:
            print(f"  {model:8s} {d:4s}: WR={wr(al)*100:5.1f}% vs base {wr(uni)*100:5.1f}% "
                  f"(n={len(al)}/{len(uni)})")
