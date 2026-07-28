import numpy as np, pandas as pd
from audit_res import load, resolve

d=load("long_1h.csv")
pc=d.close.shift(1)
tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
d["atr_pct"]=(tr.ewm(alpha=1/14,adjust=False).mean()/d.close).shift(1)
e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=26))&d.atr_pct.gt(0)]
ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
bts=d.ts.values; bh=d.high.to_numpy(); bl=d.low.to_numpy()
i0=np.searchsorted(bts,ets,"left"); i1=np.searchsorted(bts,ets+np.timedelta64(24*60,"m"),"left")
W=int((i1-i0).max()); cols=np.arange(W)[None,:]
idx=np.minimum(i0[:,None]+cols,len(bts)-1); valid=cols<(i1-i0)[:,None]
up=np.where(valid,bh[idx]/epx[:,None]-1,-np.inf); dn=np.where(valid,bl[idx]/epx[:,None]-1,np.inf)

# saatlik ortalama log-getiri (11 yil)
mu=np.log(d.close).diff().mean()
print(f"NDX 2016-2026 saatlik ortalama log-getiri (surukleme) = {mu*1e4:.3f} bp/saat")
print(f"  -> 24 saatte {mu*24*1e4:.2f} bp;  medyan 1h ATR = {np.median(a)*1e4:.1f} bp\n")

rows=[]
for tp_a,sl_a in [(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(2.5,1.0),(3.0,1.0),(4.0,1.0)]:
    tp,sl=a*tp_a,a*sl_a
    ht,hs=up>=tp[:,None],dn<=-sl[:,None]
    at,as_=ht.any(1),hs.any(1); BIG=10**7
    t_tp=np.where(at,ht.argmax(1),BIG); t_sl=np.where(as_,hs.argmax(1),BIG)
    hold=np.minimum(np.minimum(t_tp,t_sl)+1,(i1-i0))     # saat cinsinden piyasada kalma
    c=1.0/epx
    rr_=[]
    for t in ("sl","tp"):
        w,l,o,er,amb=resolve(d,ets,epx,tp,sl,24.0,"BUY",t)
        r=np.where(w,(tp-c)/sl,np.where(l,-(sl+c)/sl,0.0)); rr_.append(np.where(o,(er-c)/sl,r))
    r=np.mean(rr_,axis=0)
    # BETA TAHMINI: sadece "piyasada gecen sure x surukleme / stop" — geometriden BAGIMSIZ
    beta_pred=float((hold.mean()*mu-np.mean(c))/np.median(sl))
    rows.append(dict(rr=round(tp_a/sl_a,2),ort_sure_saat=round(float(hold.mean()),2),
        olculen_EV=round(float(r.mean()),4),
        beta_beklentisi=round(beta_pred,4),
        artik=round(float(r.mean())-beta_pred,4)))
t=pd.DataFrame(rows)
print("Piyasada kalma suresi ile SADECE surukleme'den beklenen EV vs GERCEK olculen EV:")
print(t.to_string(index=False))
print(f"\nkorelasyon(olculen, beta_beklentisi) = {np.corrcoef(t.olculen_EV,t.beta_beklentisi)[0,1]:.4f}")
print(f"artiklarin ortalamasi = {t.artik.mean():+.4f}R  (geometriye ozgu ARTIK edge)")
