import numpy as np, pandas as pd
from audit_res import load, h1_atr, resolve, ev, FRIC

d1h=load("long_1h.csv"); d1h["atr_pct"]=h1_atr(d1h)
d15=load("long_15m.csv")
GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(2.5,1.0),(3.0,1.0),(4.0,1.0)]

# --- KALIBRASYON: 2023-2026 ortusen donem, 1h-belirsizler 15m'de nasil bitti ---
LO=pd.Timestamp("2023-03-08",tz="UTC")
e=d1h[(d1h.ts>=LO)&(d1h.ts<=d1h.ts.max()-pd.Timedelta(hours=26))&d1h.atr_pct.gt(0)].copy()
ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
print("KALIBRASYON (2023-03 -> 2026-07, ayni besleme, n=%d giris)"%len(e))
print("1h'te belirsiz olan islemlerin 15m'de GERCEK sonucu:\n")
cal={}
rows=[]
for tp_a,sl_a in GEOMS:
    tp,sl=a*tp_a,a*sl_a
    for dr in ("BUY","SELL"):
        w1,l1,o1,_,amb=resolve(d1h,ets,epx,tp,sl,24.0,dr,"sl")
        wf,lf,of_,_,_=resolve(d15,ets,epx,tp,sl,24.0,dr,"sl")
        k=int(amb.sum())
        p=float(wf[amb].mean()) if k else np.nan
        cal[(tp_a,sl_a,dr)]=(p,k)
        if dr=="BUY":
            rows.append(dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2),
                belirsiz_n=k,belirsiz_pay_pct=round(amb.mean()*100,2),
                TP_once_pay=round(p,3) if k else np.nan))
print(pd.DataFrame(rows).to_string(index=False))

# --- 11 YIL: kalibre edilmis EV ---
f=d1h[(d1h.ts<=d1h.ts.max()-pd.Timedelta(hours=26))&d1h.atr_pct.gt(0)].copy()
fts=f.ts.values; fpx=f.open.to_numpy(); fa=f.atr_pct.to_numpy()
yr=pd.DatetimeIndex(f.ts).year; years=sorted(set(yr))
print("\n\n=== 11 YIL BUY — IDDIA (SL-once) vs KALIBRE EDILMIS (olculen TP-once orani) ===")
out=[]
for tp_a,sl_a in GEOMS:
    tp,sl=fa*tp_a,fa*sl_a
    w,l,o,er,amb=resolve(d1h,fts,fpx,tp,sl,24.0,"BUY","sl")
    r_sl=ev(w,l,o,er,amb,tp,sl,"BUY",FRIC,"sl")
    wt,lt,ot,ert,ambt=resolve(d1h,fts,fpx,tp,sl,24.0,"BUY","tp")
    r_tp=ev(wt,lt,ot,ert,ambt,tp,sl,"BUY",FRIC,"tp")
    p=cal[(tp_a,sl_a,"BUY")][0]
    if not np.isfinite(p): p=0.5
    r_cal=r_sl+p*(r_tp-r_sl)          # belirsizlerin p kadari aslinda TP
    pos_sl=sum(1 for y in years if r_sl[yr==y].mean()>0)
    pos_cal=sum(1 for y in years if r_cal[yr==y].mean()>0)
    out.append(dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2),
        ev_iddia=round(r_sl.mean(),4),poz_yil_iddia=pos_sl,
        p_TP=round(p,3),ev_kalibre=round(r_cal.mean(),4),poz_yil_kalibre=pos_cal,
        duzeltme=round(r_cal.mean()-r_sl.mean(),4)))
o=pd.DataFrame(out); print(o.to_string(index=False))
