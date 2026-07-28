import numpy as np, pandas as pd
from audit_res import load, resolve, ev, FRIC

GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(2.5,1.0),(3.0,1.0),(4.0,1.0)]
m1=load("bars_1m.csv")

def rs(d,rule):
    o=(d.set_index("ts").resample(rule,label="left",closed="left")
        .agg({"open":"first","high":"max","low":"min","close":"last"}).dropna().reset_index())
    return o

b15=rs(m1,"15min"); b1h=rs(m1,"1h")
pc=b1h.close.shift(1)
tr=pd.concat([b1h.high-b1h.low,(b1h.high-pc).abs(),(b1h.low-pc).abs()],axis=1).max(axis=1)
b1h["atr_pct"]=(tr.ewm(alpha=1/14,adjust=False).mean()/b1h.close).shift(1)

HI=m1.ts.max()
e=b1h[(b1h.ts<=HI-pd.Timedelta(hours=26))&b1h.atr_pct.gt(0)].copy()
ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
print(f"TEK BESLEME (MT5 1m) — girisler={len(e)}, donem {e.ts.min()} -> {e.ts.max()}")
print("Tum cozunurlukler AYNI 1m barlardan yeniden ornekleme. Tek degisken: yol cozunurlugu.\n")

res={}
for lbl,bars in [("1h",b1h),("15m",b15),("1m",m1)]:
    rows=[]
    for tp_a,sl_a in GEOMS:
        tp,sl=a*tp_a,a*sl_a
        row=dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2))
        for dr in ("BUY","SELL"):
            w,l,o,er,amb=resolve(bars,ets,epx,tp,sl,24.0,dr,"sl")
            r=ev(w,l,o,er,amb,tp,sl,dr,FRIC,"sl")
            row[f"ev_{dr}"]=r.mean(); row[f"amb_{dr}"]=amb.mean()
        row["ev_TOPLAM"]=row["ev_BUY"]+row["ev_SELL"]
        rows.append(row)
    res[lbl]=pd.DataFrame(rows)
    print(f"--- {lbl} cozunurluk ---"); print(res[lbl].round(4).to_string(index=False)); print()

c=res["1h"][["geom","rr"]].copy()
c["ev_1h"]=res["1h"].ev_BUY; c["ev_15m"]=res["15m"].ev_BUY; c["ev_1m"]=res["1m"].ev_BUY
c["duzeltme_1h->1m"]=c.ev_1m-c.ev_1h
c["belirsiz_1h_%"]=(res["1h"].amb_BUY*100).round(2)
print("=== COZUNURLUK DUZELTMESI (BUY) ===")
print(c.round(4).to_string(index=False))
