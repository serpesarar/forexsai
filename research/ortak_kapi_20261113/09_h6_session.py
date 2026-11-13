import sys; sys.path.insert(0,"research/ortak_kapi_20261113")
import pandas as pd, numpy as np
from common import *
j=pd.read_parquet(BASE+"journal.parquet")
# gate_fired for WAIT lives in counterfactual.live -> fetch quickly
sys.path.insert(0,"."); from scripts.islem_otopsi import data as D
rows=D.fetch_table(D.get_client(),"decider_journal","id,raw->counterfactual->live->>gate_fired",[("ts","gte","2026-06-25")],"ts")
g=pd.DataFrame(rows); g.columns=["id","gf_cf"]
j=j.merge(g,on="id",how="left")
j["gf"]=pd.Series(np.where(j.action=="OPEN", j.gate_fired.astype(str), j.gf_cf.astype(str))).str.lower().eq("true").values
x=j[j.gf & j.dir.isin(["BUY","SELL"]) & j.cf_net.notna()].copy()
x=episodes(x); x["day"]=x.ts.dt.date; x["blk"]=(x.ts.dt.hour//4)*4
x["era"]=np.select([x.ts<"2026-08-13", x.ts<"2026-10-01"],[0,1],2)
print("mekanik tetik epizod:", len(x)); print(x.groupby(["symbol","dir"]).agg(n=("cf_net","size"),R=("cf_net","mean")).round(3))
rng=np.random.default_rng(5)
def evalcells(df):
    res=[]
    for (s,d,b),gg in df.groupby(["symbol","dir","blk"]):
        if len(gg)<40: continue
        e=[gg[gg.era==k].cf_net.mean() for k in range(3)]
        res.append(dict(cell=f"{s} {d} {b:02d}-{b+4:02d}",n=len(gg),R=gg.cf_net.mean(),e0=e[0],e1=e[1],e2=e[2],ok3=all((np.nan_to_num(v,nan=-1)>0) for v in e)))
    return pd.DataFrame(res)
r=evalcells(x)
for i,row in r[r.ok3].iterrows():
    s,d,b=row.cell.split(); gg=x[(x.symbol==s)&(x.dir==d)&(x.blk==int(b[:2]))]
    sr=gg.groupby("day").cf_net.apply(list); ks=list(sr.index)
    bs=[np.mean(sum((sr[ks[k]] for k in rng.choice(len(ks),len(ks))),[])) for _ in range(1000)]
    r.loc[i,"P"]=(np.array(bs)>0).mean()
print(r.round(3).sort_values("R",ascending=False).to_string())
print("3 çağda da + hücre:", int(r.ok3.sum()), "/", len(r))
# plasebo: saat bloklarını gün içinde karıştır
cnt=[]
for _ in range(200):
    y=x.copy(); y["blk"]=y.groupby("day").blk.transform(lambda s: rng.permutation(s.values))
    cnt.append(int(evalcells(y).ok3.sum()))
print("plasebo ok3 sayısı ort/%95:", np.mean(cnt), np.percentile(cnt,95))
