"""
USOIL kirilim tespiti: rolling N-bar Donchian kanal kirilimi (5m).
Her kirilim icin: GERCEK (devam) / SAHTE (donus) etiketi + tam gosterge seti.
"""
import json
import numpy as np
from datetime import datetime

SC = "/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/7df45e44-1b5f-4bfc-bd93-c236cdbc275f/scratchpad"
d = np.load(f"{SC}/usoil_5m_indicators.npz")
o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]
atr14, adx, plus_di, minus_di = d["atr14"], d["adx"], d["plus_di"], d["minus_di"]
rsi14, macd_hist, dist_ema20_atr, vol_ratio = d["rsi14"], d["macd_hist"], d["dist_ema20_atr"], d["vol_ratio"]
with open(f"{SC}/usoil_5m_times.json") as f:
    times = json.load(f)
n = len(c)

N = 48          # 4 saatlik Donchian kanal (48x5m) — 4h dalga kapisiyla ayni olcek
RACE_BARS = 36  # yaris penceresi: 3 saat
TARGET_ATR = 1.0

roll_max = np.array([h[max(0, i - N):i].max() if i > 0 else np.nan for i in range(n)])
roll_min = np.array([l[max(0, i - N):i].min() if i > 0 else np.nan for i in range(n)])

events = []
for i in range(N + 1, n - RACE_BARS - 1):
    if atr14[i] <= 0 or np.isnan(roll_max[i]) or np.isnan(roll_max[i - 1]):
        continue
    up_break = c[i] > roll_max[i] and c[i - 1] <= roll_max[i - 1]
    dn_break = c[i] < roll_min[i] and c[i - 1] >= roll_min[i - 1]
    if not (up_break or dn_break):
        continue
    direction = "BUY" if up_break else "SELL"
    level = roll_max[i] if up_break else roll_min[i]

    # yaris: devam hedefi (TARGET_ATR ilerisi) vs donus hedefi (kirilim seviyesinin GERISI, TARGET_ATR)
    cont_target = c[i] + TARGET_ATR * atr14[i] if direction == "BUY" else c[i] - TARGET_ATR * atr14[i]
    rev_target = level - TARGET_ATR * atr14[i] if direction == "BUY" else level + TARGET_ATR * atr14[i]

    outcome = "AMBIGUOUS"
    for j in range(i + 1, min(i + 1 + RACE_BARS, n)):
        if direction == "BUY":
            hit_cont = h[j] >= cont_target
            hit_rev = l[j] <= rev_target
        else:
            hit_cont = l[j] <= cont_target
            hit_rev = h[j] >= rev_target
        if hit_cont and hit_rev:
            outcome = "AMBIGUOUS"; break
        if hit_cont:
            outcome = "GENUINE"; break
        if hit_rev:
            outcome = "FAKE"; break

    events.append({
        "idx": i, "time": times[i], "direction": direction, "level": round(level, 4),
        "close": round(c[i], 4), "outcome": outcome,
        "adx": round(float(adx[i]), 2), "plus_di": round(float(plus_di[i]), 2),
        "minus_di": round(float(minus_di[i]), 2), "rsi14": round(float(rsi14[i]), 2),
        "macd_hist": round(float(macd_hist[i]), 4), "dist_ema20_atr": round(float(dist_ema20_atr[i]), 3),
        "vol_ratio": round(float(vol_ratio[i]), 3), "atr14": round(float(atr14[i]), 4),
        "breakout_bar_range_atr": round(float((h[i] - l[i]) / atr14[i]), 3) if atr14[i] > 0 else None,
        "breakout_body_ratio": round(float(abs(c[i] - o[i]) / max(h[i] - l[i], 1e-9)), 3),
    })

print(f"toplam kirilim olayi: {len(events)}")
from collections import Counter
print(Counter(e["outcome"] for e in events))
print(f"  BUY: {sum(1 for e in events if e['direction']=='BUY')}  SELL: {sum(1 for e in events if e['direction']=='SELL')}")

with open(f"{SC}/usoil_breakout_events.json", "w") as f:
    json.dump(events, f, indent=1)
print("kaydedildi: usoil_breakout_events.json")
