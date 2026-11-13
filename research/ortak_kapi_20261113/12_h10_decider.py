import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,".")
from common import *
from importlib import import_module
H=import_module("11_h10_bot")
from scripts.islem_otopsi import data as D
rows=D.fetch_table(D.get_client(),"decider_journal","id,bto:raw->cf_path->>bars_to_outcome,ebt:raw->trade->>entry_bar_time,ebt_cf:raw->counterfactual->>entry_bar_time",[("ts","gte","2026-06-25")],"ts")
b=pd.DataFrame(rows)[["id","bto","ebt","ebt_cf"]]
x=pd.read_parquet(BASE+"h7.parquet").merge(b,on="id",how="left")
ebt=pd.to_numeric(x.ebt.fillna(x.ebt_cf),errors="coerce"); bto=pd.to_numeric(x.bto,errors="coerce")
x["t_open"]=x.ts
x["t_close"]=np.where(ebt.notna()&bto.notna(), pd.to_datetime(ebt+300*(bto+1),unit="s",utc=True), x.ts+pd.Timedelta(minutes=120))
x["t_close"]=pd.to_datetime(x.t_close,utc=True)
x["t_close"]=np.maximum(x.t_close, x.ts+pd.Timedelta(minutes=5))
print("bto bilinen oranı", bto.notna().mean().round(3), "medyan süre dk", ((x.t_close-x.ts).dt.total_seconds()/60).median())
x["key"]=x.symbol+" "+x.dir; x["R"]=x.cf_net
mech=x[["key","t_open","t_close","R"]].dropna()
op=x[x.cls=="OPEN"][["key","t_open","t_close","R"]].dropna()
r1=H.evaluate(mech,"decider_mekanik_tum",nperm=300)
r2=H.evaluate(op,"decider_OPEN",nperm=300)
r=pd.concat([r1,r2]); print(r.round(3).to_string()); r.to_csv("research/ortak_kapi_20261113/results_h10_decider.csv",index=False)
