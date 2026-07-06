"""
04 — COUNTERFACTUAL CONFIG SWEEP: her sembolü nasıl kâra geçiririz?
4 config first-touch sim (entry'den, adverse-first muhafazakar):
  A orig      : yön D, TP=tpm, SL=slm        (şu anki)
  B inv-dir   : yön -D, TP=tpm, SL=slm        (sinyali ters çevir)
  C inv-tpsl  : yön D,  TP=slm, SL=tpm        (tp/sl mesafe takası — kullanıcının fikri)
  D inv-both  : yön -D, TP=slm, SL=tpm
+ SL-genişletme testi (NDX/GDAXI: SL sonrası fiyat dönüyordu → SL çok mu dar?)
$/lot brüt + tahmini maliyet (swap gerçek + spread) düşülmüş net.
"""
import json, statistics as st, bisect
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); B=ROOT/"bot_live_audit"/"bars"
P=json.loads((ROOT/"bot_live_audit"/"positions.json").read_text())
def ts(s): return datetime.fromisoformat(s).timestamp()

PV   ={"NDX.INDX":1.028,"GDAXI.INDX":1.145,"USOIL.FOREX":100.0,"XAUUSD":102.69}
SPREAD={"NDX.INDX":2.0,"GDAXI.INDX":2.0,"USOIL.FOREX":0.03,"XAUUSD":0.30}  # round-trip puan

# tpm/slm
tp=defaultdict(list); sl=defaultdict(list); sw=defaultdict(list)
for p in P:
    if p["close_reason"]=="tp" and p["trig_dist"]: tp[p["symbol"]].append(p["trig_dist"])
    if p["close_reason"]=="sl" and p["trig_dist"]: sl[p["symbol"]].append(p["trig_dist"])
    sw[p["symbol"]].append((p["pnl_net"]-p["pnl"])/p["lot"])  # swap/lot (pnl_net=raw+swap)
TPM={s:st.median(v) for s,v in tp.items()}; SLM={s:st.median(v) for s,v in sl.items()}
SWAP={s:st.median(v) for s,v in sw.items()}

# marks füzyonu (03 ile aynı)
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

def sim(trs, sym, flip_dir, tp_d, sl_d):
    """flip_dir: False=orig yön, True=ters. tp_d/sl_d: mesafe. Dönüş: WR, brüt$/lot, net$/lot, n."""
    pv=PV[sym]; cost=SPREAD[sym]*pv + abs(SWAP.get(sym,0))  # round-trip $/lot
    w=l=cov=0; pnl=[]
    for p in trs:
        D=1 if p["direction"]=="BUY" else -1
        if flip_dir: D=-D
        E=p["entry_px"]; t0=ts(p["entry_time"])
        if D>0: up,dn,fav=E+tp_d,E-sl_d,"up"
        else:   up,dn,fav=E+sl_d,E-tp_d,"dn"
        ft=first_touch(sym,t0,up,dn)
        if ft is None: continue
        cov+=1
        if ft=="both": ft="up" if fav=="dn" else "dn"   # adverse-first
        if ft==fav: w+=1; pnl.append(tp_d*pv)
        else:       l+=1; pnl.append(-sl_d*pv)
    if not cov: return None
    gross=st.mean(pnl); net=gross-cost
    return (w/cov*100, gross, net, cov, cost)

print("="*92)
print("CONFIG SWEEP — brüt & net $/lot beklenti (first-touch, adverse-first; maliyet=spread+swap)")
print(f"{'sembol':12s} {'config':10s} {'WR%':>6s} {'brüt$/lot':>10s} {'net$/lot':>9s} {'n':>5s}  yorum")
print("="*92)
for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    trs=[p for p in P if p["symbol"]==sym and p["close_reason"] in ("tp","sl") and p["trig_dist"]]
    tpm,slm=TPM[sym],SLM[sym]
    if not trs: continue
    cfgs=[("A orig",False,tpm,slm),("B inv-dir",True,tpm,slm),
          ("C inv-tpsl",False,slm,tpm),("D inv-both",True,slm,tpm)]
    base=None
    for name,fd,td,sd in cfgs:
        r=sim(trs,sym,fd,td,sd)
        if not r: continue
        wr,g,n,cov,cost=r
        tag = " ← KÂRLI" if n>0 else (" (zarar)" if n<0 else "")
        print(f"{sym:12s} {name:10s} {wr:6.1f} {g:10.1f} {n:9.1f} {cov:5d}{tag}")
    print(f"{'':12s} (tpm={tpm:.3f} slm={slm:.3f} pv={PV[sym]} spread_cost≈{SPREAD[sym]*PV[sym]:.1f} swap/lot≈{SWAP.get(sym,0):.1f})")
    print()

print("="*92)
print("SL-GENİŞLETME TESTİ — TP sabit(tpm), SL∈{slm,1.5×,2×,3×}. 'SL çok dar mı?' (indeksler için)")
print(f"{'sembol/yön':16s} {'SL×':>5s} {'WR%':>6s} {'brüt$/lot':>10s} {'net$/lot':>9s} {'n':>5s}")
print("="*92)
for sym in ["NDX.INDX","GDAXI.INDX"]:
    for d in ("BUY","SELL"):
        trs=[p for p in P if p["symbol"]==sym and p["direction"]==d and p["close_reason"] in ("tp","sl") and p["trig_dist"]]
        if len(trs)<15: continue
        tpm,slm=TPM[sym],SLM[sym]
        for mult in (1.0,1.5,2.0,3.0):
            r=sim(trs,sym,False,tpm,slm*mult)
            if not r: continue
            wr,g,n,cov,cost=r
            print(f"{sym+' '+d:16s} {mult:5.1f} {wr:6.1f} {g:10.1f} {n:9.1f} {cov:5d}")
        print()
