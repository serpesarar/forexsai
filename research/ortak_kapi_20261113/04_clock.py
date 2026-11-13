import pandas as pd, numpy as np
t = pd.read_parquet("research/ortak_kapi_20261113/data/trades.parquet")
j = pd.read_parquet("research/ortak_kapi_20261113/data/journal.parquet")
d = t[t.family=="DECIDER"].copy()
jo = j[j.action=="OPEN"].sort_values("ts")
res=[]
for _,r in d.iterrows():
    c = jo[(jo.symbol==r.symbol)&(jo.direction==r.direction)]
    for off in (2,3):
        ut = r.open_raw - pd.Timedelta(hours=off)
        dt = (c.ts-ut).dt.total_seconds().abs()
        if len(dt): res.append((r.open_raw, off, dt.min()/60))
x = pd.DataFrame(res, columns=["t","off","min"])
x["post"] = x.t>=pd.Timestamp("2026-11-01 08:00",tz="UTC")
print(x.groupby(["post","off"])["min"].describe()[["count","50%","75%"]])
