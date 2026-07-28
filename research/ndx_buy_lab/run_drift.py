import numpy as np, pandas as pd
from audit_res import load, resolve, ev, FRIC

GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(2.5,1.0),(3.0,1.0),(4.0,1.0)]
base=load("long_1h.csv")

def atr_of(d):
    pc=d.close.shift(1)
    tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    return (tr.ewm(alpha=1/14,adjust=False).mean()/d.close).shift(1)

def demean(d, mode):
    """Bar bazinda log-getiri ortalamasini sifirla. Bar ICI sekil korunur
    (tum OHLC ayni skalerle carpilir) -> sadece barlar-arasi surukleme silinir."""
    d=d.copy()
    lr=np.log(d.close).diff()
    if mode=="global":
        mu=pd.Series(np.repeat(lr.mean(),len(d)),index=d.index)
    elif mode=="yillik":
        y=pd.DatetimeIndex(d.ts).year
        mu=lr.groupby(y).transform("mean")
    mu=mu.fillna(0.0)
    f=np.exp(-mu.cumsum())
    for c in ("open","high","low","close"): d[c]=d[c]*f
    return d

def run(d,label):
    d=d.copy(); d["atr_pct"]=atr_of(d)
    e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=26))&d.atr_pct.gt(0)]
    ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
    yr=pd.DatetimeIndex(e.ts).year; years=sorted(set(yr))
    rows=[]
    for tp_a,sl_a in GEOMS:
        tp,sl=a*tp_a,a*sl_a
        row=dict(geom=f"{tp_a}/{sl_a}",rr=round(tp_a/sl_a,2))
        for dr in ("BUY","SELL"):
            r=None
            for tie,wgt in (("sl",1),):
                w,l,o,er,amb=resolve(d,ets,epx,tp,sl,24.0,dr,"sl")
                rs_=ev(w,l,o,er,amb,tp,sl,dr,FRIC,"sl")
                wt,lt,ot,ert,at_=resolve(d,ets,epx,tp,sl,24.0,dr,"tp")
                rt_=ev(wt,lt,ot,ert,at_,tp,sl,dr,FRIC,"tp")
                r=0.5*(rs_+rt_)     # adil beraberlik (split) - artefakt notrlendi
            row[f"ev_{dr}"]=round(r.mean(),4)
            if dr=="BUY": row["poz_yil"]=sum(1 for y in years if r[yr==y].mean()>0)
        # AL-TUT kiyas olcutu: TP/SL YOK, 24s sonunda kapat, ayni R birimi
        _,_,_,er24,_=resolve(d,ets,epx,a*99,a*99,24.0,"BUY","sl")
        row["ev_ALTUT"]=round(float(((er24-FRIC)/sl).mean()),4)
        row["geom_katkisi"]=round(row["ev_BUY"]-row["ev_ALTUT"],4)
        rows.append(row)
    df=pd.DataFrame(rows); print(f"\n=== {label} ==="); print(df.to_string(index=False)); return df

print("Adil beraberlik kurali (split) kullanildi -> cozunurluk artefakti notrlendi.")
print("ev_ALTUT = ayni girisler, TP/SL YOK, 24s sonunda piyasadan cik (ayni R birimi).")
a1=run(base,"HAM SERI (2016-2026, NDX ~5x artti)")
a2=run(demean(base,"global"),"SURUKLEME CIKARILMIS (global demean)")
a3=run(demean(base,"yillik"),"SURUKLEME CIKARILMIS (yil-bazli demean)")

print("\n\n=== OZET: RR ilerledikce EV artisi drift'ten mi geliyor? ===")
c=pd.DataFrame({"rr":a1.rr,"ham_BUY":a1.ev_BUY,"demean_BUY":a2.ev_BUY,
                "yillik_demean_BUY":a3.ev_BUY,"ham_ALTUT":a1.ev_ALTUT,"demean_ALTUT":a2.ev_ALTUT})
print(c.to_string(index=False))
print("\nRR0.73 -> RR3.0 EV artisi:")
for nm,col in [("ham",a1.ev_BUY),("global demean",a2.ev_BUY),("yillik demean",a3.ev_BUY)]:
    print(f"   {nm:16s} {col.iloc[0]:+.4f} -> {col.iloc[5]:+.4f}   fark {col.iloc[5]-col.iloc[0]:+.4f}")
