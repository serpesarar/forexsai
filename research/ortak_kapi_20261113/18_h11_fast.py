import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,"research/ndx_sell_dusus_20261008"); sys.path.insert(0,".")
import numpy as np, pandas as pd, run as P
from importlib import import_module
S=import_module("17_h11_proxy".replace("17_h11_proxy","common"))
exec(open("research/ortak_kapi_20261113/17_h11_proxy.py").read().split("out=[]")[0].split("H=import_module")[0])
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
# tek pozisyon dizisinde önceki işlem girişten önce kapanmış olur → nedensel önceki k = shift(1..k)
def rule(g,k):
    prev=g.R.shift(1).rolling(k).mean(); m=prev.notna(); return g.R[m&(prev<=0)], g.R[m&(prev>0)]
rng=np.random.default_rng(4); allres=[]
for name,bh,lab in (("long_30m_utc",0.5,"ANA_30m_2021-26"),("long_1h_utc",1.0,"IKINCIL_1h_2016-21")):
    d=P.regimes(P.bars(name)); sg=P.signals(d)
    ses=sg["S0 taban SELL"][0]; c,e20,e50=(d[k].to_numpy() for k in ("close","ema20","ema50")); r2=d.close.pct_change(2).to_numpy()
    sg["S2b momentum BUY"]=(ses&(c>e50)&(e20>e50)&(r2>0),1); sg["S0b taban BUY"]=(ses,1)
    print("\n###",lab)
    for sn,(sig,s) in sg.items():
        g=simulate(d,sig,s,bh)
        if name=="long_1h_utc": g=g[g.t_open<pd.Timestamp("2021-06-29",tz="UTC")]
        g=g.reset_index(drop=True); g["key"]=sn; allres.append(g.assign(lab=lab))
        line=f"{sn:28s} n={len(g):5d} ortR={g.R.mean():+.3f} |"
        for k in (3,5,10):
            a,b=rule(g,k)
            pl=[]
            for _ in range(300):
                y=g.assign(R=rng.permutation(g.R.values)); aa,bb=rule(y,k); pl.append(aa.mean()-bb.mean())
            dd=a.mean()-b.mean(); line+=f" k{k}: al {a.mean():+.3f}/{len(a)} atla {b.mean():+.3f} Δ{dd:+.3f} pl%{(np.array(pl)<dd).mean()*100:.0f} |"
        print(line)
pd.concat(allres).to_parquet("research/ortak_kapi_20261113/data/proxy_trades.parquet")
