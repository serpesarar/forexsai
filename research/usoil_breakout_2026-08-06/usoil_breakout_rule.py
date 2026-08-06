"""
BUY kirilimlari icin esik/kural optimizasyonu: breakout_bar_range_atr + vol_ratio
DUSUK olani GENUINE'e daha yakin bulundu (TRAIN). Esikleri TRAIN'de ara, TEST'te
OOS dogrula. SELL icin ayni sey + ek kombinasyonlar (RSI+DI+dist_ema20) denenir.
"""
import json
import statistics as st

SC = "/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/7df45e44-1b5f-4bfc-bd93-c236cdbc275f/scratchpad"
with open(f"{SC}/usoil_breakout_events.json") as f:
    events = json.load(f)
events = [e for e in events if e["outcome"] in ("GENUINE", "FAKE")]
events.sort(key=lambda e: e["time"])
split = int(len(events) * 0.7)
train, test = events[:split], events[split:]


def wr(rs):
    g = sum(1 for r in rs if r["outcome"] == "GENUINE")
    return 100 * g / len(rs) if rs else 0, g, len(rs)


print("=== BUY: range_atr / vol_ratio esik taramasi (TRAIN) ===")
buy_tr = [e for e in train if e["direction"] == "BUY"]
buy_te = [e for e in test if e["direction"] == "BUY"]
base_tr = wr(buy_tr); base_te = wr(buy_te)
print(f"taban: TRAIN WR={base_tr[0]:.1f}% (n={base_tr[2]})  TEST WR={base_te[0]:.1f}% (n={base_te[2]})\n")

best = None
for r_thr in [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2, 2.5]:
    for v_thr in [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]:
        sub = [e for e in buy_tr if e["breakout_bar_range_atr"] <= r_thr and e["vol_ratio"] <= v_thr]
        if len(sub) < 30:
            continue
        w, g, tot = wr(sub)
        if best is None or w > best[0]:
            best = (w, g, tot, r_thr, v_thr)
print(f"TRAIN'de en iyi (n>=30): WR={best[0]:.1f}% (n={best[2]})  range_atr<={best[3]}  vol_ratio<={best[4]}")

r_thr, v_thr = best[3], best[4]
sub_te = [e for e in buy_te if e["breakout_bar_range_atr"] <= r_thr and e["vol_ratio"] <= v_thr]
w_te, g_te, tot_te = wr(sub_te)
print(f"AYNI esik TEST/OOS'ta: WR={w_te:.1f}% (n={tot_te})\n")

# daha az esnek/tek-esikli basit kural: SADECE range_atr, ya da SADECE vol_ratio
for feat, thr_list in [("breakout_bar_range_atr", [1.0,1.2,1.4,1.5,1.6,1.8,2.0]),
                        ("vol_ratio", [1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.8,2.0])]:
    print(f"--- TEK ESIK: {feat} ---")
    best1 = None
    for thr in thr_list:
        sub = [e for e in buy_tr if e[feat] <= thr]
        if len(sub) < 40: continue
        w,g,tot = wr(sub)
        if best1 is None or w > best1[0]:
            best1 = (w,g,tot,thr)
    print(f"  TRAIN en iyi: WR={best1[0]:.1f}% (n={best1[2]}) esik<={best1[3]}")
    sub_te = [e for e in buy_te if e[feat] <= best1[3]]
    w_te,g_te,tot_te = wr(sub_te)
    print(f"  TEST/OOS ayni esik: WR={w_te:.1f}% (n={tot_te})\n")

print("\n=== SELL: kombinasyon denemeleri (TRAIN) — rsi14 / plus_di / dist_ema20_atr ===")
sell_tr = [e for e in train if e["direction"] == "SELL"]
sell_te = [e for e in test if e["direction"] == "SELL"]
base_tr_s = wr(sell_tr); base_te_s = wr(sell_te)
print(f"taban: TRAIN WR={base_tr_s[0]:.1f}% (n={base_tr_s[2]})  TEST WR={base_te_s[0]:.1f}% (n={base_te_s[2]})\n")

best_s = None
for rsi_thr in [20,22,24,26,28,30,32,34,36]:
    sub = [e for e in sell_tr if e["rsi14"] <= rsi_thr]
    if len(sub) < 40: continue
    w,g,tot = wr(sub)
    if best_s is None or w > best_s[0]:
        best_s = (w,g,tot,rsi_thr)
print(f"TEK ESIK rsi14<=X TRAIN en iyi: WR={best_s[0]:.1f}% (n={best_s[2]}) esik={best_s[3]}")
sub_te = [e for e in sell_te if e["rsi14"] <= best_s[3]]
w_te,g_te,tot_te = wr(sub_te)
print(f"TEST/OOS ayni esik: WR={w_te:.1f}% (n={tot_te})")
