import pandas as pd, numpy as np
from sim import simulate, path_stats
df=pd.read_pickle("paths.pkl")
st=[path_stats(p, rr) for p,rr in zip(df.path, df.rr)]
df=df.join(pd.DataFrame(st,index=df.index))
ok=df[df.exit.isin(["tp","sl"])]
print(pd.crosstab(ok.exit, ok.sim_exit))
simclose=[pd.Timestamp(p["t"][i]) for p,i in zip(ok.path,ok.sim_idx)]
d2=(pd.Series(simclose,index=ok.index)-ok.close_utc.dt.floor("min").dt.tz_convert(None)).dt.total_seconds()/60
print("kapanış ±1dk isabet:",(d2.abs()<=1).mean().round(3))
bad=ok[ok.exit!=ok.sim_exit]
print(bad[["sym","dir","open_utc","close_utc","exit","sim_exit","rr","mfe","mae"]].to_string())
df.to_pickle("paths_stats.pkl")
