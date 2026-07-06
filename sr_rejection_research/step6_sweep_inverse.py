"""
Liquidity Sweep TERSİ — devam (continuation) yönü.
bull-sweep (alt swing low kırıldı) → devam AŞAĞI = SELL sinyali kazanır mı?
bear-sweep (üst swing high kırıldı) → devam YUKARI = BUY sinyali kazanır mı?
Yüksek çıkarsa: placebo + walk-forward OOS + per-sembol + per-yön ile DOĞRULA.
"""
import json, random
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
recs = [json.loads(l) for l in open(ROOT / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m", "1h"]


def inv_aligned(r, tf):
    """Devam yönü: BUY sinyali ↔ bear_sweep (üst kırıldı, yukarı devam);
    SELL sinyali ↔ bull_sweep (alt kırıldı, aşağı devam)."""
    f = r["f"].get(tf)
    if not f or not f.get("sweep"):
        return None
    return f["sweep"]["bear"] if r["dir"] == "BUY" else f["sweep"]["bull"]


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) if rs else 0.0


by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

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
        al = [r for r in uni if inv_aligned(r, tf)]
        if len(al) >= 100:
            results.append({"model": model, "tf": tf, "n": len(al),
                            "wr": wr(al), "base": base, "lift": wr(al) - base})
results.sort(key=lambda x: -x["lift"])
wins = [r["win"] for r in recs]
idx = {}
for r in results:
    k = (r["model"], r["tf"])
    uni = [i for i, x in enumerate(recs) if x["model"] == r["model"] and x["f"].get(r["tf"]) and x["f"][r["tf"]].get("sweep")]
    al = [i for i in uni if inv_aligned(recs[i], r["tf"])]
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
print(f"LIQUIDITY SWEEP TERSİ (devam yönü) | placebo p95 = +{p95*100:.1f}pp\n")
print(f"{'model':10s}{'tf':4s}{'n':>6s}{'WR':>7s}{'base':>7s}{'lift':>7s}{'OOS':>7s}{'plcb':>5s}")
for r in results[:12]:
    k = (r["model"], r["tf"]); uni, al = idx.get(k, ([], []))
    at = [i for i in al if i in test]; ut = [i for i in uni if i in test]
    oos = (sum(wins[i] for i in at)/len(at) - sum(wins[i] for i in ut)/len(ut))*100 if len(at) >= 30 else None
    os = f"{oos:+.1f}" if oos is not None else "—"
    pf = "✅" if r["lift"] > p95 else "·"
    print(f"{r['model']:10s}{r['tf']:4s}{r['n']:>6d}{r['wr']*100:>6.1f}%{r['base']*100:>6.1f}%{r['lift']*100:>+6.1f}{os:>7s}{pf:>5s}")

# en iyi varsa per-sembol + per-yön doğrula
if results and results[0]["lift"] > p95:
    bm, btf = results[0]["model"], results[0]["tf"]
    print(f"\n>>> DOĞRULAMA: {bm} {btf} (en iyi) per-sembol + per-yön:")
    sub = [r for r in by_model[bm] if r["f"].get(btf) and r["f"][btf].get("sweep")]
    for sym in ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]:
        u = [r for r in sub if r["symbol"] == sym]
        a = [r for r in u if inv_aligned(r, btf)]
        if len(a) >= 25:
            print(f"   {sym:12s} WR {wr(a)*100:5.1f}% vs base {wr(u)*100:5.1f}% (+{(wr(a)-wr(u))*100:+.1f}, n={len(a)})")
    for d in ("BUY", "SELL"):
        u = [r for r in sub if r["dir"] == d]
        a = [r for r in u if inv_aligned(r, btf)]
        if len(a) >= 25:
            print(f"   {d:4s}         WR {wr(a)*100:5.1f}% vs base {wr(u)*100:5.1f}% (n={len(a)})")
