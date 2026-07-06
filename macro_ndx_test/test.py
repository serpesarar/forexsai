"""
MAKRO → NDX testi. VIX/US10Y(TNX)/DXY, NDX sinyallerine hizalanır.
Soru: makro NDX WR'ını/yönünü öngörüyor mu? (XAU'da çökmüştü — NDX farklı mı?)
Titizlik: DEDUP (60dk/kurulum) + AUC + yön-koşullu + placebo.
"""
import json, bisect, random, statistics as st
from datetime import datetime
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
M = ROOT / "macro_ndx_test"
import sys
sys.path.insert(0, str(ROOT / "yeni deneme"))  # discrimination yok; auc'yi inline yazıyoruz


def ep(t):
    return datetime.fromisoformat(t).timestamp()


# makro serileri
macro = {}
for nm in ["VIX", "TNX", "DXY"]:
    rows = json.loads((M / f"{nm}.json").read_text())
    rows.sort(key=lambda r: r["t"])
    macro[nm] = ([r["t"] for r in rows], [r["close"] for r in rows])


def val_at(nm, epoch):
    ts, cs = macro[nm]
    i = bisect.bisect_right(ts, epoch) - 1
    return cs[i] if i >= 0 else None


def chg(nm, epoch, hours):
    now = val_at(nm, epoch); prev = val_at(nm, epoch - hours * 3600)
    if now is None or prev is None or prev == 0:
        return None
    return (now - prev) / abs(prev) * 100


# sinyaller (resolved), dedup — sembol argümandan (vars. NDX)
SYM = sys.argv[1] if len(sys.argv) > 1 else "NDX.INDX"
print(f"### SEMBOL: {SYM} ###")
sig = [s for s in json.loads((ROOT / "sr_rejection_research" / "data" / "signals.json").read_text())
       if s["symbol"] == SYM and s["ml_direction"] in ("BUY", "SELL")]
sig.sort(key=lambda s: s["created_at"])
last = {}; dedup = []
for s in sig:
    k = s["ml_direction"]
    t = ep(s["created_at"])
    if k not in last or t - last[k] > 3600:
        dedup.append(s); last[k] = t
print(f"NDX resolved: {len(sig)} → dedupe: {len(dedup)}\n")

rows = []
for s in dedup:
    t = ep(s["created_at"])
    f = {"vix": val_at("VIX", t), "vix_chg1d": chg("VIX", t, 24), "vix_chg6h": chg("VIX", t, 6),
         "tnx_chg1d": chg("TNX", t, 24), "dxy_chg1d": chg("DXY", t, 24), "dxy_chg6h": chg("DXY", t, 6)}
    if any(v is None for v in f.values()):
        continue
    rows.append({"win": s["status"] == "completed", "dir": s["ml_direction"], "ind": f})
print(f"{len(rows)} sinyal makro ile hizalandı.\n")


def auc(wins, losses):
    nw, nl = len(wins), len(losses)
    if nw == 0 or nl == 0:
        return 0.5
    comb = sorted(wins + losses); rank = {}; i = 0
    while i < len(comb):
        j = i
        while j + 1 < len(comb) and comb[j + 1] == comb[i]:
            j += 1
        for k in range(i, j + 1):
            rank[comb[k]] = (i + j) / 2 + 1
        i = j + 1
    return (sum(rank[v] for v in losses) - nl * (nl + 1) / 2) / (nw * nl)


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) * 100 if rs else 0


keys = list(rows[0]["ind"].keys())
print("=== MAKRO → NDX win/loss AYRIMI (AUC, dedup) ===")
print(f"{'makro':12s}{'AUC':>7s}{'ayrım':>7s}{'WIN ort':>10s}{'LOSS ort':>10s}")
disc = []
for k in keys:
    w = [r["ind"][k] for r in rows if r["win"]]; l = [r["ind"][k] for r in rows if not r["win"]]
    a = auc(w, l); disc.append((abs(a - 0.5), k, a, st.mean(w), st.mean(l)))
disc.sort(reverse=True)
for sep, k, a, mw, ml in disc:
    arrow = "↑→LOSS" if a > 0.5 else "↑→WIN"
    print(f"{k:12s}{a:7.3f}{sep:7.3f}{mw:10.3f}{ml:10.3f}  {arrow}")

# placebo (etiket karıştır, max ayrım)
pl = []
labels = [r["win"] for r in rows]
for _ in range(200):
    random.shuffle(labels)
    best = 0
    for k in keys:
        w = [rows[i]["ind"][k] for i in range(len(rows)) if labels[i]]
        l = [rows[i]["ind"][k] for i in range(len(rows)) if not labels[i]]
        best = max(best, abs(auc(w, l) - 0.5))
    pl.append(best)
pl.sort()
print(f"\nplacebo p95 ayrım = {pl[int(0.95*len(pl))]:.3f} (gerçek bunu geçmeli)")

print("\n=== YÖN-KOŞULLU: makro YÖN öngörüyor mu? ===")
base = wr(rows)
print(f"NDX base WR={base:.1f}% | BUY={wr([r for r in rows if r['dir']=='BUY']):.1f}% SELL={wr([r for r in rows if r['dir']=='SELL']):.1f}%")
top = disc[0][1]
vals = sorted(r["ind"][top] for r in rows)
med = vals[len(vals)//2]
print(f"\nEn ayırt edici '{top}' medyan={med:.3f} ile böl:")
for lab, cond in [("DÜŞÜK", lambda v: v < med), ("YÜKSEK", lambda v: v >= med)]:
    sub = [r for r in rows if cond(r["ind"][top])]
    b = [r for r in sub if r["dir"] == "BUY"]; sl = [r for r in sub if r["dir"] == "SELL"]
    print(f"  {top} {lab:6s}: BUY WR={wr(b):.1f}% (n={len(b)}) | SELL WR={wr(sl):.1f}% (n={len(sl)})")
