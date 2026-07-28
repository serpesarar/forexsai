import numpy as np, pandas as pd
from audit_res import load, h1_atr, resolve, ev, FRIC

GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(3.0,1.0),(4.0,1.0)]
d1h=load("long_1h.csv"); d1h["atr_pct"]=h1_atr(d1h)
d15=load("long_15m.csv"); d1m=load("bars_1m.csv")

def table(bars,label,lo,hi,horizon=24.0,tie="sl",fric=FRIC,dirs=("BUY","SELL")):
    e=d1h[(d1h.ts>=lo)&(d1h.ts<=hi-pd.Timedelta(hours=horizon+2))&d1h.atr_pct.gt(0)].copy()
    e=e[e.ts>=bars.ts.min()]
    ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
    out=[]
    for tp_a,sl_a in GEOMS:
        tp,sl=a*tp_a,a*sl_a
        row=dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2),n=len(e))
        for dr in dirs:
            w,l,o,er,amb=resolve(bars,ets,epx,tp,sl,horizon,dr,tie)
            r=ev(w,l,o,er,amb,tp,sl,dr,fric,tie)
            row[f"ev_{dr}"]=r.mean(); row[f"wr_{dr}"]=w.mean()
            row[f"amb_{dr}"]=amb.mean(); row[f"acik_{dr}"]=o.mean()
        if len(dirs)==2: row["ev_TOPLAM"]=row["ev_BUY"]+row["ev_SELL"]
        out.append(row)
    df=pd.DataFrame(out); print(f"\n=== {label} ===");
    print(df.round(4).to_string(index=False)); return df

LO=pd.Timestamp("2023-03-08",tz="UTC"); HI=pd.Timestamp("2026-07-28",tz="UTC")
print("A) ORTUSEN DONEM 2023-03 -> 2026-07 : SADECE COZUNURLUK DEGISIYOR")
t1=table(d1h,"1h cozunurluk (iddianin yontemi)",LO,HI)
t2=table(d15,"15m cozunurluk (ayni girisler)",LO,HI)
LO2=pd.Timestamp("2026-02-11",tz="UTC")
print("\n\nB) 1m DONEMI 2026-02 -> 2026-07")
u1=table(d1h,"1h cozunurluk",LO2,HI)
u2=table(d15,"15m cozunurluk",LO2,HI)
u3=table(d1m,"1m cozunurluk (en dogru)",LO2,HI)
