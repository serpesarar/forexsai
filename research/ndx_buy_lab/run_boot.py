import numpy as np, pandas as pd
from audit_res import load, resolve

rng=np.random.default_rng(7)
base=load("long_1h.csv")
def atr_of(d):
    pc=d.close.shift(1)
    tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    return (tr.ewm(alpha=1/14,adjust=False).mean()/d.close).shift(1)
def demean(d,mode):
    d=d.copy(); lr=np.log(d.close).diff()
    mu=pd.Series(np.repeat(lr.mean(),len(d)),index=d.index) if mode=="global" \
       else lr.groupby(pd.DatetimeIndex(d.ts).year).transform("mean")
    f=np.exp(-mu.fillna(0).cumsum())
    for c in ("open","high","low","close"): d[c]=d[c]*f
    return d

def series(d, tp_a, sl_a, cost=1.0):
    d=d.copy(); d["atr_pct"]=atr_of(d)
    e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=26))&d.atr_pct.gt(0)]
    ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
    tp,sl=a*tp_a,a*sl_a; c=cost/epx
    rr_=[]
    for t in ("sl","tp"):
        w,l,o,er,amb=resolve(d,ets,epx,tp,sl,24.0,"BUY",t)
        r=np.where(w,(tp-c)/sl,np.where(l,-(sl+c)/sl,0.0))
        rr_.append(np.where(o,(er-c)/sl,r))
    r=np.mean(rr_,axis=0)
    wk=pd.DatetimeIndex(e.ts).to_period("W").astype(str)
    return r, wk

def boot(r, wk, B=3000):
    df=pd.DataFrame({"r":r,"wk":wk})
    g=df.groupby("wk").r.agg(["sum","count"])
    S,C=g["sum"].to_numpy(),g["count"].to_numpy(); K=len(S)
    idx=rng.integers(0,K,size=(B,K))
    return (S[idx].sum(1)/C[idx].sum(1))

def report(lbl,d):
    r073,wk=series(d,0.727,1.0); r300,_=series(d,3.0,1.0)
    b073=boot(r073,wk); b300=boot(r300,wk)
    diff=b300-b073
    print(f"\n--- {lbl} (HAFTA-bloklu bootstrap, 3000) ---")
    for nm,v,bb in [("RR 0.73",r073.mean(),b073),("RR 3.00",r300.mean(),b300)]:
        print(f"  {nm}: EV={v:+.4f}R  %95GA=[{np.percentile(bb,2.5):+.4f},{np.percentile(bb,97.5):+.4f}]"
              f"  P(EV>0)={np.mean(bb>0)*100:5.1f}%")
    print(f"  FARK (3.0 - 0.73): {r300.mean()-r073.mean():+.4f}R  "
          f"%95GA=[{np.percentile(diff,2.5):+.4f},{np.percentile(diff,97.5):+.4f}]  "
          f"P(fark>0)={np.mean(diff>0)*100:5.1f}%")

print("Adil beraberlik (split) + fiyat-duyarli 1 puan surtunme, ufuk 24s, 2016-2026")
report("HAM SERI", base)
report("SURUKLEME CIKARILMIS (global)", demean(base,"global"))
report("SURUKLEME CIKARILMIS (yillik)", demean(base,"yillik"))
