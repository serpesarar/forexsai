# journal'a karar yönü (OPEN: direction, WAIT: counterfactual.dir) ekle
import sys, json, pandas as pd
sys.path.insert(0,".")
from scripts.islem_otopsi import data as D
cl=D.get_client()
rows=D.fetch_table(cl,"decider_journal","id,raw->counterfactual->>dir,raw->>cf_pnl_r_net",[("ts","gte","2026-06-25")],"ts")
x=pd.DataFrame(rows); print(x.columns.tolist()); x.columns=["id","cf_dir","cf_net"]
j=pd.read_parquet("research/ortak_kapi_20261113/data/journal.parquet").merge(x,on="id",how="left")
j["dir"]=j.direction.where(j.action=="OPEN", j.cf_dir)
j["cf_net"]=pd.to_numeric(j.cf_net,errors="coerce")
j.to_parquet("research/ortak_kapi_20261113/data/journal.parquet")
print(j.groupby(["symbol","action","dir"],dropna=False).agg(n=("id","size"),cf=("cf_pnl_r","mean"),net=("cf_net","mean")).round(3))
