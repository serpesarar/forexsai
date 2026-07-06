"""
VWAP testi — kanal/VP ile aynı titizlik. Hacim-ağırlıklı ortalama (rolling z) +
günlük-anchored uzaklık. Soru: edge var mı VE kanala EK DEĞER katıyor mu (yoksa
kanal/VP gibi redundant mı)?
"""
import json, random
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m", "1h"]
ZTS = [1.0, 1.5, 2.0, 2.5]


def vwap_z(r, tf):
    f = r["f"].get(tf)
    return f["vwap"]["vwap_z"] if f and f.get("vwap") else None


def vwap_aligned(r, tf, zt):
    z = vwap_z(r, tf)
    return None if z is None else ((z <= -zt) if r["dir"] == "BUY" else (z >= zt))


def chan_aligned(r, tf, zt=2.5, n=50):
    f = r["f"].get(tf)
    if not f or "chan" not in f:
        return None
    c = f["chan"].get(str(n)) or f["chan"].get(n)
    if not c or c["spp"] <= 1e-9:
        return None
    z = c["pm"] / c["spp"]
    return (z <= -zt) if r["dir"] == "BUY" else (z >= zt)


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) if rs else 0.0


by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

print("=" * 76)
print("VWAP REVERSION (rolling z) — BUY z≤−zt / SELL z≥zt (per model × TF × eşik)")
print("=" * 76)
results = []
for model in ["pulse1", "pulse2", "pulse3", "meta", "smc"]:
    rows = by_model.get(model, [])
    if len(rows) < 300:
        continue
    for tf in TFS:
        uni = [r for r in rows if r["f"].get(tf) and r["f"][tf].get("vwap")]
        if len(uni) < 150:
            continue
        base = wr(uni)
        for zt in ZTS:
            al = [r for r in uni if vwap_aligned(r, tf, zt)]
            if len(al) >= 100:
                results.append({"model": model, "tf": tf, "zt": zt, "n": len(al),
                                "wr": wr(al), "base": base, "lift": wr(al) - base})
results.sort(key=lambda x: -x["lift"])
wins = [r["win"] for r in recs]
idx = {}
for r in results[:120]:
    k = (r["model"], r["tf"], r["zt"])
    uni = [i for i, x in enumerate(recs) if x["model"] == r["model"] and x["f"].get(r["tf"]) and x["f"][r["tf"]].get("vwap")]
    al = [i for i in uni if vwap_aligned(recs[i], r["tf"], r["zt"])]
    idx[k] = (uni, al)
pmax = []; sh = wins[:]
for _ in range(50):
    random.shuffle(sh)
    best = 0
    for uni, al in idx.values():
        if al and uni:
            best = max(best, sum(sh[i] for i in al)/len(al) - sum(sh[i] for i in uni)/len(uni))
    pmax.append(best)
pmax.sort(); p95 = pmax[int(0.95*len(pmax))]
cut = int(0.6*len(recs)); test = set(range(cut, len(recs)))
print(f"placebo p95 = +{p95*100:.1f}pp\n")
print(f"{'model':10s}{'tf':4s}{'zt':>5s}{'n':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}{'OOS':>7s}{'plcb':>5s}")
for r in results[:12]:
    k = (r["model"], r["tf"], r["zt"]); uni, al = idx.get(k, ([], []))
    at = [i for i in al if i in test]; ut = [i for i in uni if i in test]
    oos = (sum(wins[i] for i in at)/len(at) - sum(wins[i] for i in ut)/len(ut))*100 if len(at) >= 30 else None
    os = f"{oos:+.1f}" if oos is not None else "—"
    pf = "✅" if r["lift"] > p95 else "·"
    print(f"{r['model']:10s}{r['tf']:4s}{r['zt']:>5}{r['n']:>6d}{r['wr']*100:>6.1f}%{r['base']*100:>6.1f}%{r['lift']*100:>+6.1f}{os:>7s}{pf:>5s}")

print("\n" + "=" * 76)
print("VWAP, KANALA EK DEĞER KATIYOR MU? (pulse3 30m)")
print("=" * 76)
p3 = [r for r in by_model["pulse3"] if r["f"].get("30m") and r["f"]["30m"].get("vwap")]
base = wr(p3)
chan = [r for r in p3 if chan_aligned(r, "30m")]
vw = [r for r in p3 if vwap_aligned(r, "30m", 2.0)]
# kanal ATEŞLEMEYEN ama VWAP ateşleyen (VWAP'ın YENİ yakaladıkları)
vw_not_chan = [r for r in p3 if vwap_aligned(r, "30m", 2.0) and not chan_aligned(r, "30m")]
print(f"  base                    : WR {base*100:.1f}% (n={len(p3)})")
print(f"  yalnız KANAL z≥2.5      : WR {wr(chan)*100:.1f}% (n={len(chan)})")
print(f"  yalnız VWAP z≥2.0       : WR {wr(vw)*100:.1f}% (n={len(vw)})")
print(f"  VWAP var AMA kanal YOK  : WR {wr(vw_not_chan)*100:.1f}% (n={len(vw_not_chan)})  ← VWAP'ın YENİ yakaladıkları")
add = len(vw_not_chan) >= 50 and wr(vw_not_chan) > base + 0.10
print(f"  → VWAP kanala EK katıyor mu: {'EVET (kanalın kaçırdıklarını yakalıyor)' if add else 'HAYIR/marjinal (kanalla örtüşüyor)'}")
