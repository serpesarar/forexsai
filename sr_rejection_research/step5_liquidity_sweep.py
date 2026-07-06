"""
Liquidity Sweep testi — kanal/VP/VWAP ile aynı titizlik (placebo + OOS).
Sweep: fiyat prior swing low/high'ı süpürdü + geri döndü (stop-hunt reversal).
Soru: edge var mı VE kanal/VWAP'a EK DEĞER katıyor mu (yoksa redundant mı)?
"""
import json, random
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m", "1h"]


def sweep_aligned(r, tf):
    f = r["f"].get(tf)
    if not f or not f.get("sweep"):
        return None
    return f["sweep"]["bull"] if r["dir"] == "BUY" else f["sweep"]["bear"]


def chan_aligned(r, tf, zt=2.5, n=50):
    f = r["f"].get(tf)
    if not f or "chan" not in f:
        return None
    c = f["chan"].get(str(n)) or f["chan"].get(n)
    if not c or c["spp"] <= 1e-9:
        return None
    z = c["pm"] / c["spp"]
    return (z <= -zt) if r["dir"] == "BUY" else (z >= zt)


def vwap_aligned(r, tf, zt=2.0):
    f = r["f"].get(tf)
    if not f or not f.get("vwap"):
        return None
    z = f["vwap"]["vwap_z"]
    return (z <= -zt) if r["dir"] == "BUY" else (z >= zt)


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) if rs else 0.0


by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

print("=" * 72)
print("LIQUIDITY SWEEP REVERSION — BUY:alt-süpürme / SELL:üst-süpürme (per model × TF)")
print("=" * 72)
results = []
for model in ["pulse1", "pulse2", "pulse3", "meta", "smc"]:
    rows = by_model.get(model, [])
    if len(rows) < 300:
        continue
    for tf in TFS:
        uni = [r for r in rows if r["f"].get(tf) and r["f"][tf].get("sweep")]
        if len(uni) < 150:
            continue
        base = wr(uni)
        al = [r for r in uni if sweep_aligned(r, tf)]
        if len(al) >= 100:
            results.append({"model": model, "tf": tf, "n": len(al),
                            "wr": wr(al), "base": base, "lift": wr(al) - base})
results.sort(key=lambda x: -x["lift"])
wins = [r["win"] for r in recs]
idx = {}
for r in results:
    k = (r["model"], r["tf"])
    uni = [i for i, x in enumerate(recs) if x["model"] == r["model"] and x["f"].get(r["tf"]) and x["f"][r["tf"]].get("sweep")]
    al = [i for i in uni if sweep_aligned(recs[i], r["tf"])]
    idx[k] = (uni, al)
pmax = []; sh = wins[:]
for _ in range(50):
    random.shuffle(sh)
    best = 0
    for uni, al in idx.values():
        if al and uni:
            best = max(best, sum(sh[i] for i in al)/len(al) - sum(sh[i] for i in uni)/len(uni))
    pmax.append(best)
pmax.sort(); p95 = pmax[int(0.95*len(pmax))] if pmax else 0
cut = int(0.6*len(recs)); test = set(range(cut, len(recs)))
print(f"placebo p95 = +{p95*100:.1f}pp\n")
print(f"{'model':10s}{'tf':4s}{'n':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}{'OOS':>7s}{'plcb':>5s}")
for r in results[:12]:
    k = (r["model"], r["tf"]); uni, al = idx.get(k, ([], []))
    at = [i for i in al if i in test]; ut = [i for i in uni if i in test]
    oos = (sum(wins[i] for i in at)/len(at) - sum(wins[i] for i in ut)/len(ut))*100 if len(at) >= 30 else None
    os = f"{oos:+.1f}" if oos is not None else "—"
    pf = "✅" if r["lift"] > p95 else "·"
    print(f"{r['model']:10s}{r['tf']:4s}{r['n']:>6d}{r['wr']*100:>6.1f}%{r['base']*100:>6.1f}%{r['lift']*100:>+6.1f}{os:>7s}{pf:>5s}")

print("\n" + "=" * 72)
print("SWEEP, KANAL/VWAP'A EK DEĞER KATIYOR MU? (pulse3 30m)")
print("=" * 72)
p3 = [r for r in by_model["pulse3"] if r["f"].get("30m") and r["f"]["30m"].get("sweep")]
base = wr(p3)
sw = [r for r in p3 if sweep_aligned(r, "30m")]
# sweep ateşler AMA kanal&vwap ATEŞLEMEZ → sweep'in YENİ yakaladıkları
sw_new = [r for r in p3 if sweep_aligned(r, "30m") and not chan_aligned(r, "30m") and not vwap_aligned(r, "30m")]
print(f"  base                         : WR {base*100:.1f}% (n={len(p3)})")
print(f"  yalnız SWEEP                 : WR {wr(sw)*100:.1f}% (n={len(sw)})")
print(f"  SWEEP var AMA kanal&vwap YOK : WR {wr(sw_new)*100:.1f}% (n={len(sw_new)})  ← sweep'in YENİSİ")
add = len(sw_new) >= 50 and wr(sw_new) > base + 0.10
print(f"  → Sweep EK katıyor mu: {'EVET' if add else 'HAYIR/marjinal (kanal&vwap zaten kapsıyor)'}")
