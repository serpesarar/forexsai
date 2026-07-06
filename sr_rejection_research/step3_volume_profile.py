"""
Volume Profile testi — kanal-rejection ile AYNI titizlik (placebo + walk-forward).
Hipotez: fiyat value-area DIŞINDA (below VAL → BUY / above VAH → SELL) = hacme göre
aşırı → POC'a dönüş. + VP kanala EK DEĞER katıyor mu (yoksa kanal zaten yetiyor mu)?
"""
import json, random
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m", "1h"]
ZTS = [0.4, 0.6, 0.8, 1.0, 1.3]      # vp_pos eşiği (value-area-width birimi)


def vp_pos(r, tf):
    f = r["f"].get(tf)
    if not f or not f.get("vp"):
        return None
    return f["vp"]["vp_pos"]


def vp_aligned(r, tf, zt):
    p = vp_pos(r, tf)
    if p is None:
        return None
    return (p <= -zt) if r["dir"] == "BUY" else (p >= zt)


def chan_z(r, tf, n=50):
    f = r["f"].get(tf)
    if not f or "chan" not in f:
        return None
    c = f["chan"].get(str(n)) or f["chan"].get(n)
    return c["pm"] / c["spp"] if c and c["spp"] > 1e-9 else None


def chan_aligned(r, tf, zt=2.5):
    z = chan_z(r, tf)
    return None if z is None else ((z <= -zt) if r["dir"] == "BUY" else (z >= zt))


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) if rs else 0.0


by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

# ── VP-reversion sweep ──
print("=" * 76)
print("VOLUME PROFILE REVERSION — BUY<VAL / SELL>VAH (per model × TF × eşik)")
print("=" * 76)
results = []
for model in ["pulse1", "pulse2", "pulse3", "meta", "smc"]:
    rows = by_model.get(model, [])
    if len(rows) < 300:
        continue
    for tf in TFS:
        uni = [r for r in rows if r["f"].get(tf) and r["f"][tf].get("vp")]
        if len(uni) < 150:
            continue
        base = wr(uni)
        for zt in ZTS:
            al = [r for r in uni if vp_aligned(r, tf, zt)]
            if len(al) >= 100:
                results.append({"model": model, "tf": tf, "zt": zt, "n": len(al),
                                "wr": wr(al), "base": base, "lift": wr(al) - base})
results.sort(key=lambda x: -x["lift"])
# placebo
wins = [r["win"] for r in recs]
idx = {}
for r in results[:120]:
    k = (r["model"], r["tf"], r["zt"])
    uni = [i for i, x in enumerate(recs) if x["model"] == r["model"] and x["f"].get(r["tf"]) and x["f"][r["tf"]].get("vp")]
    al = [i for i in uni if vp_aligned(recs[i], r["tf"], r["zt"])]
    idx[k] = (uni, al)
pmax = []
sh = wins[:]
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
for r in results[:14]:
    k = (r["model"], r["tf"], r["zt"]); uni, al = idx.get(k, ([], []))
    at = [i for i in al if i in test]
    ut = [i for i in uni if i in test]
    oos = (sum(wins[i] for i in at)/len(at) - sum(wins[i] for i in ut)/len(ut))*100 if len(at) >= 30 else None
    pf = "✅" if r["lift"] > p95 else "·"
    os = f"{oos:+.1f}" if oos is not None else "—"
    print(f"{r['model']:10s}{r['tf']:4s}{r['zt']:>5}{r['n']:>6d}{r['wr']*100:>6.1f}%{r['base']*100:>6.1f}%{r['lift']*100:>+6.1f}{os:>7s}{pf:>5s}")

# ── VP kanala EK DEĞER katıyor mu? ──
print("\n" + "=" * 76)
print("VP, KANALA EK DEĞER KATIYOR MU? (pulse3 30m)")
print("=" * 76)
p3 = [r for r in by_model["pulse3"] if r["f"].get("30m") and r["f"]["30m"].get("vp")]
base = wr(p3)
chan = [r for r in p3 if chan_aligned(r, "30m")]
vp = [r for r in p3 if vp_aligned(r, "30m", 0.8)]
both = [r for r in p3 if chan_aligned(r, "30m") and vp_aligned(r, "30m", 0.8)]
print(f"  base                : WR {base*100:.1f}% (n={len(p3)})")
print(f"  yalnız KANAL z≥2.5  : WR {wr(chan)*100:.1f}% (n={len(chan)})")
print(f"  yalnız VP (zt0.8)   : WR {wr(vp)*100:.1f}% (n={len(vp)})")
print(f"  KANAL + VP birlikte : WR {wr(both)*100:.1f}% (n={len(both)})")
print(f"  → VP kanala ek katıyor mu: {'EVET' if len(both)>30 and wr(both)>wr(chan)+0.02 else 'HAYIR/marjinal (kanal yetiyor)' }")
