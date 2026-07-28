import numpy as np, pandas as pd
from audit_res import load, h1_atr, resolve, ev, FRIC

d=load("long_1h.csv"); d["atr_pct"]=h1_atr(d)
e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=26))&d.atr_pct.gt(0)].copy()
ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
yr=pd.DatetimeIndex(e.ts).year
GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(2.5,1.0),(3.0,1.0),(4.0,1.0)]
print(f"11 YIL 1h — n={len(e)}  {e.ts.min().date()} -> {e.ts.max().date()}")
print("Beraberlik kurali duyarliligi (belirsiz = TP+SL ayni 1h barda)\n")
rows=[]
for tp_a,sl_a in GEOMS:
    tp,sl=a*tp_a,a*sl_a
    row=dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2))
    for dr in ("BUY","SELL"):
        for tie in ("sl","split","tp"):
            w,l,o,er,amb=resolve(d,ets,epx,tp,sl,24.0,dr,tie)
            r=ev(w,l,o,er,amb,tp,sl,dr,FRIC,tie)
            row[f"{dr}_{tie}"]=round(r.mean(),4)
            if tie=="sl":
                row[f"{dr}_belirsiz%"]=round(amb.mean()*100,2)
                pos=sum(1 for y in sorted(set(yr)) if r[yr==y].mean()>0)
                row[f"{dr}_pozyil_sl"]=pos
            if tie=="split":
                pos=sum(1 for y in sorted(set(yr)) if r[yr==y].mean()>0)
                row[f"{dr}_pozyil_split"]=pos
    rows.append(row)
df=pd.DataFrame(rows)
print(df[["geom","rr","BUY_belirsiz%","BUY_sl","BUY_split","BUY_tp","BUY_pozyil_sl","BUY_pozyil_split"]].to_string(index=False))
print()
print(df[["geom","rr","SELL_sl","SELL_split","SELL_tp"]].to_string(index=False))
print("\n=== SIMETRI TESTI: EV_BUY + EV_SELL (saf yapisal maliyet; drift birbirini gotururur) ===")
df["TOPLAM_sl"]=df.BUY_sl+df.SELL_sl; df["TOPLAM_split"]=df.BUY_split+df.SELL_split
df["FARK_BUY_eksi_SELL"]=df.BUY_sl-df.SELL_sl
print(df[["geom","rr","TOPLAM_sl","TOPLAM_split","FARK_BUY_eksi_SELL"]].to_string(index=False))
