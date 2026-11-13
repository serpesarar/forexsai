import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"."); sys.path.insert(0,"backend")
import pandas as pd
from scripts.islem_otopsi import data as D
from services.signal_metrics import signal_outcome
cl=D.get_client(); rows=[]
for m in ["pulse1","pulse2","pulse3","emel","smc","meta","emel_inverse"]:
    rows+=D.fetch_table(cl,"prediction_logs","*",[("created_at","gte","2026-07-28"),("model_type","eq",m),("status","in_",["completed","stopped"])],"created_at")
out=[]
for r in rows:
    o=signal_outcome(r, default_symbol=r.get("symbol"))
    out.append(dict(model=r["model_type"],symbol=r.get("symbol"),dir=r.get("ml_direction") or r.get("direction"),t_open=r["created_at"],t_close=r.get("closed_at") or r.get("exit_time"),R=o.r_multiple,klass=o.klass,epoch=o.epoch))
df=pd.DataFrame(out); df["t_open"]=pd.to_datetime(df.t_open,utc=True,format="mixed"); df["t_close"]=pd.to_datetime(df.t_close,utc=True,format="mixed")
df.to_parquet("research/ortak_kapi_20261113/data/panel.parquet")
print(len(df), df.R.notna().mean()); print(df.groupby(["model","epoch"]).agg(n=("R","size"),R=("R","mean")).round(3))
