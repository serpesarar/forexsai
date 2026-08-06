"""
USOIL kirilim olaylari: GENUINE/FAKE ayrimini hangi gostergeler acikliyor?
Kronolojik train/test + placebo + esik optimizasyonu (yalniz TRAIN'de).
"""
import json, random
import statistics as st

SC = "/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/7df45e44-1b5f-4bfc-bd93-c236cdbc275f/scratchpad"
with open(f"{SC}/usoil_breakout_events.json") as f:
    events = json.load(f)

events = [e for e in events if e["outcome"] in ("GENUINE", "FAKE")]
events.sort(key=lambda e: e["time"])
split = int(len(events) * 0.7)
train, test = events[:split], events[split:]
print(f"toplam={len(events)}  train={len(train)} ({train[0]['time'][:10]}->{train[-1]['time'][:10]})  "
      f"test={len(test)} ({test[0]['time'][:10]}->{test[-1]['time'][:10]})\n")

FEATS = ["adx", "plus_di", "minus_di", "rsi14", "macd_hist", "dist_ema20_atr",
         "vol_ratio", "breakout_bar_range_atr", "breakout_body_ratio", "atr14"]


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


for direction in ("BUY", "SELL"):
    tr = [e for e in train if e["direction"] == direction]
    print(f"=== {direction} kirilimlari (TRAIN, n={len(tr)}) — GENUINE ayrimi (AUC) ===")
    g = [e for e in tr if e["outcome"] == "GENUINE"]
    fk = [e for e in tr if e["outcome"] == "FAKE"]
    print(f"  taban GENUINE orani: {100*len(g)/len(tr):.1f}%  (n_genuine={len(g)} n_fake={len(fk)})")
    disc = []
    for feat in FEATS:
        wv = [e[feat] for e in g]; lv = [e[feat] for e in fk]
        a = auc(wv, lv)
        disc.append((abs(a - 0.5), feat, a, st.mean(wv), st.mean(lv)))
    disc.sort(reverse=True)
    for sep, feat, a, mw, ml in disc:
        arrow = "yuksek->GENUINE" if a > 0.5 else "yuksek->FAKE"
        print(f"    {feat:<24s} AUC={a:.3f} ayrim={sep:.3f}  GENUINE_ort={mw:8.3f}  FAKE_ort={ml:8.3f}  {arrow}")

    # placebo (etiket karistir)
    labels = [e["outcome"] == "GENUINE" for e in tr]
    pl = []
    for _ in range(300):
        random.shuffle(labels)
        best = 0
        for feat in FEATS:
            wv = [tr[k][feat] for k in range(len(tr)) if labels[k]]
            lv = [tr[k][feat] for k in range(len(tr)) if not labels[k]]
            best = max(best, abs(auc(wv, lv) - 0.5))
        pl.append(best)
    pl.sort()
    print(f"  placebo p95 ayrim = {pl[int(0.95*len(pl))]:.3f}  (gercek en iyi ayrim {disc[0][0]:.3f} -> "
          f"{'GECTI' if disc[0][0] > pl[int(0.95*len(pl))] else 'GECEMEDI'})\n")
