import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,"research/ndx_sell_dusus_20261008"); sys.path.insert(0,".")
import numpy as np, pandas as pd
import run as P
from importlib import import_module
H=import_module("11_h10_bot")
def simulate(d,sig,s,bar_h):
    o,hi,lo,c=(d[k].to_numpy() for k in ("open","high","low","close")); n,maxk=len(d),int(P.MAX_HOLD_H/bar_h); rows=[]; busy=-1
    for i in np.flatnonzero(sig):
        j=i+1
        if j>=n or i<=busy: continue
        e=o[j]*(1+s*P.HALF_SPREAD_PCT); tp,sl=e*(1+s*P.TP_PCT), e*(1-s*P.SL_PCT)
        ht=(hi[j:j+maxk]>=tp) if s>0 else (lo[j:j+maxk]<=tp); hs=(lo[j:j+maxk]<=sl) if s>0 else (hi[j:j+maxk]>=sl)
        kt=np.flatnonzero(ht); ks=np.flatnonzero(hs); a=kt[0] if kt.size else np.inf; b=ks[0] if ks.size else np.inf
        if np.isinf(a) and np.isinf(b): k=min(maxk,n-j)-1; R=s*(c[j+k]-e)/(e*P.SL_PCT)
        else: k=int(min(a,b)); R=-1.0 if b<=a else P.TP_PCT/P.SL_PCT
        busy=j+k; rows.append((d.index[i], d.index[min(j+k,n-1)]+pd.Timedelta(hours=bar_h), R))
    return pd.DataFrame(rows,columns=["t_open","t_close","R"])
out=[]
for name,bh,lab in (("long_30m_utc",0.5,"ANA_30m_2021-26"),("long_1h_utc",1.0,"IKINCIL_1h_2016-21")):
    d=P.regimes(P.bars(name)); sg=P.signals(d)
    ses=sg["S0 taban SELL"][0]; c,e20,e50=(d[k].to_numpy() for k in ("close","ema20","ema50")); r2=d.close.pct_change(2).to_numpy()
    sg["S2b momentum BUY"]=(ses&(c>e50)&(e20>e50)&(r2>0),1); sg["S0b taban BUY"]=(ses,1)
    allr=[]
    for sn,(sig,s) in sg.items():
        r=simulate(d,sig,s,bh); r["key"]=sn
        if name=="long_1h_utc": r=r[r.t_open<pd.Timestamp("2021-06-29",tz="UTC")]
        allr.append(r)
    R=pd.concat(allr,ignore_index=True)
    print(lab, R.groupby("key").R.agg(["size","mean"]).round(3).to_string())
    res=H.evaluate(R[["key","t_open","t_close","R"]],lab,ks=(3,5,10),nperm=200)
    print(res.round(3).to_string()); out.append(res)
    for sn,g in R.groupby("key"):
        rr=H.evaluate(g[["key","t_open","t_close","R"]],f"{lab}|{sn}",ks=(5,),nperm=0) if False else None
    # strateji başına k=5 fark
    for sn,g in R.groupby("key"):
        prev,dd=H.causal_prev(g[["key","t_open","t_close","R"]].reset_index(drop=True),5); m=~np.isnan(prev)
        print(f"   {sn}: al {dd.R[m&(prev<=0)].mean():+.3f} (n={int((m&(prev<=0)).sum())}) atla {dd.R[m&(prev>0)].mean():+.3f} (n={int((m&(prev>0)).sum())})")
pd.concat(out).to_csv("research/ortak_kapi_20261113/results_h11_proxy.csv",index=False)
