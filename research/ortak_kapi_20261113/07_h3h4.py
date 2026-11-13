import sys; sys.path.insert(0,"research/ortak_kapi_20261113")
import pandas as pd, numpy as np
from common import *
rng=np.random.default_rng(1)
def bb_mean(v,d,n=2000):
    s=pd.Series(v).groupby(np.asarray(d)).apply(list); ks=list(s.index); out=[]
    for _ in range(n):
        x=sum((s[ks[k]] for k in rng.choice(len(ks),len(ks))),[]); out.append(np.mean(x))
    return (np.array(out)<0).mean()
rows=[]
t=load_bot(); t=t[~t.family.isin(["MANUEL"])]
for (f,s,d),g in t.groupby(["family","symbol","direction"]):
    w=g[g.open_utc>="2026-08-13"]; pre=g[g.open_utc<"2026-08-13"]
    if len(w)<15: continue
    mid=w.open_utc.median()
    rows.append(dict(src="icra",grp=f"{f} {s} {d}",n=len(w),R=w.R.mean(),h1=w[w.open_utc<mid].R.mean(),h2=w[w.open_utc>=mid].R.mean(),
        P_neg=bb_mean(w.R.values,w.day.values),pre_n=len(pre),pre_R=pre.R.mean() if len(pre) else np.nan,net=w.net.sum()))
op=pd.read_parquet(BASE+"dec_ep_h2.parquet").dropna(subset=["cf_net"])
for (s,d),g in op.groupby(["symbol","dir"]):
    w=g[g.ts>="2026-08-13"]; pre=g[g.ts<"2026-08-13"]
    if len(w)<15: continue
    mid=w.ts.median()
    rows.append(dict(src="journal_net",grp=f"DECIDER {s} {d}",n=len(w),R=w.cf_net.mean(),h1=w[w.ts<mid].cf_net.mean(),h2=w[w.ts>=mid].cf_net.mean(),
        P_neg=bb_mean(w.cf_net.values,w.day.values),pre_n=len(pre),pre_R=pre.cf_net.mean() if len(pre) else np.nan,net=np.nan))
r=pd.DataFrame(rows)
r["ENGEL"]=(r.n>=30)&(r.h1<0)&(r.h2<0)&(r.P_neg>=0.90)
r["sinif"]=np.where(r.ENGEL&(r.pre_R<0),"B",np.where(r.ENGEL,"C","-"))
print(r.round(3).to_string())
r.to_csv("research/ortak_kapi_20261113/results_h3.csv",index=False)
# H4 gate_fired
print("\nH4 gate_fired (OPEN epizod, net R):")
for (s,d),g in op.groupby(["symbol","dir"]):
    g=g.dropna(subset=["gate_fired"])
    a=g[g.gate_fired==True]; b=g[g.gate_fired==False]
    if len(a)<15 or len(b)<15: 
        print(s,d,"yetersiz",len(a),len(b)); continue
    mid=g.ts.median()
    h=[a[a.ts<mid].cf_net.mean()-b[b.ts<mid].cf_net.mean(), a[a.ts>=mid].cf_net.mean()-b[b.ts>=mid].cf_net.mean()]
    p,ci=block_boot(a.cf_net.values,a.day.values,b.cf_net.values,b.day.values)
    print(f"{s} {d}: fired n={len(a)} {a.cf_net.mean():+.3f} | not n={len(b)} {b.cf_net.mean():+.3f} | yarılar {h[0]:+.3f}/{h[1]:+.3f} P(Δ>0)={p:.3f}")
