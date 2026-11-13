import sys; sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,".")
import pandas as pd, numpy as np
from common import *
from scripts.islem_otopsi import data as D
cl=D.get_client()
rows=D.fetch_table(cl,"decider_journal","id,raw->decision->>reason,raw->counterfactual->live->>gate_fired",[("ts","gte","2026-06-25")],"ts")
g=pd.DataFrame(rows); g.columns=["id","reason","gf_cf"]
j=pd.read_parquet(BASE+"journal.parquet").merge(g,on="id",how="left")
j["gf"]=pd.Series(np.where(j.action=="OPEN", j.gate_fired.astype(str), j.gf_cf.astype(str))).str.lower().eq("true").values
rs=j.reason.fillna("")
j["cls"]=np.select([j.action=="OPEN", rs.str.startswith("claude "), rs.str.contains("kural kapısı|KANIT KURALI|bias=MIXED|kurulum hazır",regex=True)],
                   ["OPEN","SAHTE_WAIT","KURAL_WAIT"],"LLM_WAIT")
x=j[j.gf & j.dir.isin(["BUY","SELL"]) & j.cf_net.notna()].copy()
x=episodes(x); x["wk"]=x.ts.dt.strftime("%G-%V"); x["half"]=(x.ts>=x.ts.median()).astype(int)
print(pd.crosstab([x.symbol,x.dir],x.cls))
print(x.groupby(["symbol","dir","cls"]).cf_net.mean().unstack().round(3))
rng=np.random.default_rng(7)
def wdiff(df,ctrl):
    tot=0;w=0
    for wk,gg in df.groupby("wk"):
        a=gg[gg.cls=="OPEN"].cf_net; b=gg[gg.cls==ctrl].cf_net
        if len(a) and len(b):
            k=min(len(a),len(b)); tot+=k*(a.mean()-b.mean()); w+=k
    return tot/w if w else np.nan, w
for (s,d),gg in x.groupby(["symbol","dir"]):
    for ctrl in ["SAHTE_WAIT","LLM_WAIT"]:
        dd,w=wdiff(gg,ctrl)
        if np.isnan(dd): continue
        hs=[wdiff(gg[gg.half==h],ctrl)[0] for h in (0,1)]
        wks=gg.wk.unique(); bs=[]
        for _ in range(500):
            sm=pd.concat([gg[gg.wk==k].assign(wk=f"{k}_{i}") for i,k in enumerate(rng.choice(wks,len(wks)))])
            bs.append(wdiff(sm,ctrl)[0])
        P=np.nanmean(np.array(bs)>0)
        print(f"{s} {d} OPEN−{ctrl}: Δ={dd:+.3f} (eşli ağırlık {w}) yarılar {hs[0]:+.3f}/{hs[1]:+.3f} P={P:.3f}")
x.to_parquet(BASE+"h7.parquet")
