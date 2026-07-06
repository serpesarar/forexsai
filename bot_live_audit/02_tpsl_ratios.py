"""
02 — Gerçek TP/SL mesafeleri ve implied RR (FİYAT VERİSİ GEREKMEZ).
Kullanıcının asıl sorusu: 'işlemlerde görünen TP/SL oranları kaç?'
[tp X] ve [sl X] yorumlarından entry'ye mesafe → puan + %fiyat.
Ayrıca XAUUSD'nin günlük dağılımı (devre dışı bırakma teyidi).
"""
import json, statistics as st
from collections import defaultdict
from datetime import datetime
from pathlib import Path

P = json.loads((Path("/Users/melihcanodacioglu/Desktop/panel/bot_live_audit/positions.json")).read_text())

def med(xs): return st.median(xs) if xs else float('nan')

print("=== GERÇEK TP/SL MESAFELERİ (entry→tetiklenen seviye) ===")
print(f"{'sembol/yön':22s} {'tp_n':>4s} {'tpMed_pt':>9s} {'tp%':>6s} | {'sl_n':>4s} {'slMed_pt':>9s} {'sl%':>6s} | {'RR(tp/sl)':>9s}")
agg=defaultdict(lambda: {"tp":[], "sl":[], "tp_pct":[], "sl_pct":[]})
for p in P:
    if p["close_reason"] not in ("tp","sl") or not p["trig_dist"]: continue
    key=(p["symbol"], p["direction"])
    agg[key][p["close_reason"]].append(p["trig_dist"])
    agg[key][p["close_reason"]+"_pct"].append(p["trig_dist"]/p["entry_px"]*100)

for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    for d in ("BUY","SELL"):
        a=agg.get((sym,d))
        if not a or (not a["tp"] and not a["sl"]): continue
        tpm=med(a["tp"]); slm=med(a["sl"])
        rr = tpm/slm if (a["tp"] and a["sl"] and slm) else float('nan')
        print(f"{sym+' '+d:22s} {len(a['tp']):4d} {tpm:9.2f} {med(a['tp_pct']):5.2f}% | "
              f"{len(a['sl']):4d} {slm:9.2f} {med(a['sl_pct']):5.2f}% | {rr:8.2f}")
    # sembol toplamı
    at={"tp":[],"sl":[],"tp_pct":[],"sl_pct":[]}
    for d in ("BUY","SELL"):
        a=agg.get((sym,d),{})
        for k in at: at[k]+= a.get(k,[])
    tpm=med(at["tp"]); slm=med(at["sl"]); rr=tpm/slm if slm else float('nan')
    print(f"{'  → '+sym+' TOPLAM':22s} {len(at['tp']):4d} {tpm:9.2f} {med(at['tp_pct']):5.2f}% | "
          f"{len(at['sl']):4d} {slm:9.2f} {med(at['sl_pct']):5.2f}% | {rr:8.2f}   <<")
    print()

print("=== XAUUSD GÜNLÜK (devre dışı bırakma 06-16 teyidi) ===")
day=defaultdict(lambda:{"n":0,"pnl":0.0})
for p in P:
    if p["symbol"]!="XAUUSD": continue
    d=p["entry_time"][:10]
    day[d]["n"]+=1; day[d]["pnl"]+=p["pnl"]
for d in sorted(day):
    print(f"  {d}: n={day[d]['n']:3d}  netP/L={day[d]['pnl']:9.1f}")

print("\n=== TÜM SEMBOLLER GÜNLÜK net P/L ===")
day2=defaultdict(lambda:defaultdict(float))
for p in P:
    day2[p["entry_time"][:10]][p["symbol"]]+=p["pnl"]
syms=["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]
print(f"{'gün':12s}"+"".join(f"{s.split('.')[0]:>11s}" for s in syms)+f"{'GÜNLÜK':>11s}")
for d in sorted(day2):
    tot=sum(day2[d].values())
    print(f"{d:12s}"+"".join(f"{day2[d].get(s,0):11.0f}" for s in syms)+f"{tot:11.0f}")
