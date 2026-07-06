"""
05 — inv-tpsl iddiasının ROBUSTLUK testi (XAU & USOIL). Kullanıcı 'tp/sl ters çevir' önerdi.
(a) Zaman-split: ilk yarı (in-sample) vs ikinci yarı (OOS) — edge OOS'ta hayatta kalıyor mu?
(b) Maliyet duyarlılığı: spread×1/2/3 — kâr maliyet varsayımına ne kadar bağımlı?
(c) Sim sadakat kontrolü: config-A sim WR vs gerçek WR.
"""
import json, statistics as st, bisect
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); B=ROOT/"bot_live_audit"/"bars"
P=json.loads((ROOT/"bot_live_audit"/"positions.json").read_text())
def ts(s): return datetime.fromisoformat(s).timestamp()
PV={"USOIL.FOREX":100.0,"XAUUSD":102.69}; SPREAD={"USOIL.FOREX":0.03,"XAUUSD":0.30}

tp=defaultdict(list); sl=defaultdict(list)
for p in P:
    if p["close_reason"]=="tp" and p["trig_dist"]: tp[p["symbol"]].append(p["trig_dist"])
    if p["close_reason"]=="sl" and p["trig_dist"]: sl[p["symbol"]].append(p["trig_dist"])
TPM={s:st.median(v) for s,v in tp.items()}; SLM={s:st.median(v) for s,v in sl.items()}

def load_marks(sym):
    marks=[]
    f1=B/f"{sym}_1m.json"
    if f1.exists():
        for b in json.loads(f1.read_text()): marks.append((ts(b["candle_time"]),b["low"],b["high"]))
    f2=B/f"{sym}_1h.json"
    if f2.exists():
        rows=json.loads(f2.read_text()); tl=[ts(r["candle_time"]) for r in rows]
        gap=st.median([tl[i+1]-tl[i] for i in range(min(300,len(tl)-1))]) if len(rows)>2 else 3600
        for r in rows:
            if gap<900: marks.append((ts(r["candle_time"]),r["close"],r["close"]))
            else:       marks.append((ts(r["candle_time"]),r["low"],r["high"]))
    return marks
MARKS=defaultdict(list)
for s in PV: MARKS[s]+=load_marks(s)
for p in P:
    if p["symbol"] in PV:
        MARKS[p["symbol"]].append((ts(p["entry_time"]),p["entry_px"],p["entry_px"]))
        MARKS[p["symbol"]].append((ts(p["exit_time"]),p["exit_px"],p["exit_px"]))
for s in MARKS: MARKS[s].sort()
KEYS={s:[m[0] for m in MARKS[s]] for s in MARKS}
def first_touch(sym,t0,up,dn,maxmin=1440):
    arr=MARKS[sym]; i=bisect.bisect_right(KEYS[sym],t0); j=bisect.bisect_right(KEYS[sym],t0+maxmin*60)
    for t,lo,hi in arr[i:j]:
        u=hi>=up; d=lo<=dn
        if u and d: return "both"
        if u: return "up"
        if d: return "dn"
    return None

def sim(trs,sym,td,sd,cost_mult=1.0):
    pv=PV[sym]; cost=SPREAD[sym]*pv*cost_mult
    w=cov=0; pnl=[]
    for p in trs:
        D=1 if p["direction"]=="BUY" else -1
        E=p["entry_px"]; t0=ts(p["entry_time"])
        if D>0: up,dn,fav=E+td,E-sd,"up"
        else:   up,dn,fav=E+sd,E-td,"dn"
        ft=first_touch(sym,t0,up,dn)
        if ft is None: continue
        cov+=1
        if ft=="both": ft="up" if fav=="dn" else "dn"
        if ft==fav: w+=1; pnl.append(td*pv)
        else:       pnl.append(-sd*pv)
    if not cov: return None
    return (w/cov*100, st.mean(pnl)-cost, cov)

for sym in ["XAUUSD","USOIL.FOREX"]:
    trs=[p for p in P if p["symbol"]==sym and p["close_reason"] in ("tp","sl") and p["trig_dist"]]
    trs.sort(key=lambda p:p["entry_time"])
    tpm,slm=TPM[sym],SLM[sym]
    mid=len(trs)//2
    half1,half2=trs[:mid],trs[mid:]
    print(f"\n{'='*70}\n{sym}  (tpm={tpm:.3f} slm={slm:.3f}, n={len(trs)})\n{'='*70}")
    # sadakat
    realW=sum(1 for p in trs if p['pnl']>0)/len(trs)*100
    a=sim(trs,sym,tpm,slm); print(f"  SADAKAT: gerçek WR={realW:.1f}% | config-A sim WR={a[0]:.1f}%  (fark={a[0]-realW:+.1f})")
    print(f"  (a) ZAMAN-SPLIT  net$/lot  [config C: inv-tpsl, TP={slm:.2f}/SL={tpm:.2f}]")
    for lbl,h in [("TÜM",trs),("1.YARI(in-samp)",half1),("2.YARI(OOS)",half2)]:
        c=sim(h,sym,slm,tpm); a2=sim(h,sym,tpm,slm)
        d1=h[0]['entry_time'][:10]; d2=h[-1]['entry_time'][:10]
        print(f"     {lbl:16s} [{d1}→{d2}] A_orig={a2[1]:+7.1f}  C_invtpsl={c[1]:+7.1f}  (n={c[2]})")
    print(f"  (b) MALİYET DUYARLILIĞI (config C net$/lot):")
    for cm in (1,2,3,5):
        c=sim(trs,sym,slm,tpm,cost_mult=cm)
        print(f"     spread×{cm}: net={c[1]:+7.1f}$/lot  (spread_cost={SPREAD[sym]*PV[sym]*cm:.1f})")
