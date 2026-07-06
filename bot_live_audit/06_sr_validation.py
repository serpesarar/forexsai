"""
06 — S/R-girişi mimarisinin GERÇEK işlemlerle validasyonu (1m kapsamı: XAU+USOIL).
Soru: S/R filtresi kötü işlemleri eler mi? Daha iyi (destek/dirençten) giriş verir mi?
Tam outcome-sim yerine düşük-serbestlik validasyon:
  (1) skip-oranı: kaç gerçek işlemi S/R 'uygun seviye yok' diye REDDEDER?
  (2) giriş kalitesi: aldıklarında giriş, gerçek girişten daha mı iyi (BUY<, SELL>)?
  (3) taken-trade WR: S/R'nin aldığı işlemlerin gerçekteki sonucu (kazanç/kayıp).
"""
import json, sys, statistics as st
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path("/Users/melihcanodacioglu/Desktop/panel/yeni deneme")))
from sr_zones import detect_zones, plan_sr_entry

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); B=ROOT/"bot_live_audit"/"bars"
P=json.loads((ROOT/"bot_live_audit"/"positions.json").read_text())
def ts(s): return datetime.fromisoformat(s).timestamp()

WIDTH={"XAUUSD":3.0,"USOIL.FOREX":0.12}
SLD  ={"XAUUSD":5.0,"USOIL.FOREX":None}   # XAU sabit SL; USOIL %1.49 (fiyata göre)

bars={}
for s in WIDTH:
    rows=json.loads((B/f"{s}_1m.json").read_text())
    bars[s]=[(ts(r["candle_time"]), r["high"], r["low"], r["close"]) for r in rows]
    bars[s].sort()

import bisect
for sym in ["XAUUSD","USOIL.FOREX"]:
    arr=bars[sym]; keys=[b[0] for b in arr]
    last_1m=arr[-1][0]
    trs=[p for p in P if p["symbol"]==sym and ts(p["entry_time"])<=last_1m
         and p["close_reason"] in ("tp","sl")]
    print(f"\n{'='*72}\n{sym}  (1m-kapsamındaki tp/sl işlemi: {len(trs)})  width={WIDTH[sym]}")
    print("="*72)
    skip=0; taken=[]; better=0; worse=0; entry_impr=[]
    for p in trs:
        t0=ts(p["entry_time"]); i=bisect.bisect_right(keys,t0)
        win=[{"high":h,"low":l,"close":c} for (_,h,l,c) in arr[max(0,i-100):i]]
        if len(win)<30: continue
        price=win[-1]["close"]
        sld = SLD[sym] if SLD[sym] else price*0.0149
        tpd = 6.0 if sym=="XAUUSD" else price*0.0104
        med = price*0.012 if sym=="USOIL.FOREX" else 15.0  # max_entry_dist
        plan=plan_sr_entry(detect_zones(win,WIDTH[sym]), p["direction"], price,
                           fixed_tp_dist=tpd, fixed_sl_dist=sld, max_entry_dist=med, min_tp_dist=(0.3 if sym=='XAUUSD' else 0.05))
        if plan is None:
            skip+=1; continue
        taken.append(p)
        # giriş kalitesi: BUY için daha düşük giriş iyi; SELL için daha yüksek iyi
        d=1 if p["direction"]=="BUY" else -1
        impr = d*(p["entry_px"]-plan.entry)   # >0 → S/R girişi daha iyi (BUY daha ucuz / SELL daha pahalı)
        entry_impr.append(impr)
        if impr>0: better+=1
        else: worse+=1
    n=len(trs)
    if n:
        tw=sum(1 for p in taken if p["pnl"]>0)
        print(f"  GERÇEK: n={n} WR={sum(1 for p in trs if p['pnl']>0)/n*100:.1f}% netΣ={sum(p['pnl'] for p in trs):.0f}")
        print(f"  S/R REDDETTİĞİ (skip): {skip}/{n} = {skip/n*100:.0f}%  ← bu işlemler hiç açılmazdı")
        if taken:
            print(f"  S/R ALDIĞI: {len(taken)}  → gerçekteki WR={tw/len(taken)*100:.1f}%  netΣ={sum(p['pnl'] for p in taken):.0f}")
            print(f"  GİRİŞ KALİTESİ: daha iyi {better} / daha kötü {worse}  med iyileşme={st.median(entry_impr):+.3f} (fiyat birimi)")
