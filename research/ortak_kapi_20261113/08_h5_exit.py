import sys, json; sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,".")
import pandas as pd, numpy as np
from common import *
from scripts.islem_otopsi import data as D
cl=D.get_client()
rows=D.fetch_table(cl,"decider_journal","id,raw->exit_grades",[("ts","gte","2026-06-25")],"ts")
eg={r["id"]:r["exit_grades"] for r in rows if r.get("exit_grades")}
op=pd.read_parquet(BASE+"dec_ep_h2.parquet")
op=op[op.id.isin(eg)].copy()
E=pd.DataFrame([eg[i] for i in op.id],index=op.index)
pols=[c for c in E.columns if E[c].notna().mean()>0.8]
op=pd.concat([op,E[pols]],axis=1); op["spread_atr"]=op.spread_atr.fillna(op.spread_atr.median())
print("epizod", len(op), "politikalar", pols)
def cells(df, dayperm=None):
    out=[]
    for (s,d),g in df.groupby(["symbol","dir"]):
        if len(g)<40: continue
        w=g[g.ts>="2026-08-13"]; pre=g[g.ts<"2026-08-13"]
        if dayperm is not None: pass
        mid=w.ts.median()
        for p in pols:
            if p=="fixed_1.0/1.5": continue
            x=g[[p,"fixed_1.0/1.5","spread_atr","ts","day"]].dropna()
            ww=x[x.ts>="2026-08-13"]; pp=x[x.ts<"2026-08-13"]
            if len(ww)<30: continue
            dlt=ww[p]-ww["fixed_1.0/1.5"]
            h1=dlt[ww.ts<mid].mean(); h2=dlt[ww.ts>=mid].mean()
            out.append(dict(grp=f"{s} {d}",pol=p,n=len(ww),base=(ww["fixed_1.0/1.5"]-ww.spread_atr).mean(),
               net=(ww[p]-ww.spread_atr).mean(),d=dlt.mean(),h1=h1,h2=h2,pre_n=len(pp),pre_d=(pp[p]-pp["fixed_1.0/1.5"]).mean() if len(pp) else np.nan,
               _v=dlt.values,_days=ww.day.values))
    return out
cs=cells(op)
rng=np.random.default_rng(3)
for c in cs:
    s=pd.Series(c["_v"]).groupby(c["_days"]).apply(list); ks=list(s.index)
    bs=[np.mean(sum((s[ks[k]] for k in rng.choice(len(ks),len(ks))),[])) for _ in range(1000)]
    c["P"]=(np.array(bs)>0).mean()
r=pd.DataFrame(cs).drop(columns=["_v","_days"])
r["GECER"]=(r.h1>0)&(r.h2>0)&(r.P>=0.95)&(r.pre_d>0)&(r.net>0)
print(r.round(3).sort_values(["grp","d"],ascending=[True,False]).to_string())
print("geçen hücre:", r.GECER.sum(), "/", len(r))
r.to_csv("research/ortak_kapi_20261113/results_h5.csv",index=False)
op.to_parquet(BASE+"dec_ep_exit.parquet")
