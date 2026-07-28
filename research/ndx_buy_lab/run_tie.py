import numpy as np, pandas as pd
from audit_res import load, resolve, ev, FRIC

m1=load("bars_1m.csv")
def rs(d,rule):
    return (d.set_index("ts").resample(rule,label="left",closed="left")
        .agg({"open":"first","high":"max","low":"min","close":"last"}).dropna().reset_index())
b1h=rs(m1,"1h")
pc=b1h.close.shift(1)
tr=pd.concat([b1h.high-b1h.low,(b1h.high-pc).abs(),(b1h.low-pc).abs()],axis=1).max(axis=1)
b1h["atr_pct"]=(tr.ewm(alpha=1/14,adjust=False).mean()/b1h.close).shift(1)
e=b1h[(b1h.ts<=m1.ts.max()-pd.Timedelta(hours=26))&b1h.atr_pct.gt(0)].copy()
ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()

print("1h'te BELIRSIZ (TP+SL ayni barda) olan islemler 1m'de GERCEKTE nasil bitti?")
print("Iddianin kodu bunlarin HEPSINI kayip sayiyor.\n")
rows=[]
for tp_a,sl_a in [(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(3.0,1.0)]:
    tp,sl=a*tp_a,a*sl_a
    for dr in ("BUY","SELL"):
        w1,l1,o1,_,amb=resolve(b1h,ets,epx,tp,sl,24.0,dr,"sl")
        wm,lm,om,_,_=resolve(m1,ets,epx,tp,sl,24.0,dr,"sl")
        k=amb.sum()
        if k==0: continue
        rows.append(dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2),yon=dr,
            belirsiz_n=int(k), belirsiz_pay=round(amb.mean(),4),
            gercekte_TP_once=round(float(wm[amb].mean()),3),
            gercekte_SL_once=round(float(lm[amb].mean()),3)))
print(pd.DataFrame(rows).to_string(index=False))
