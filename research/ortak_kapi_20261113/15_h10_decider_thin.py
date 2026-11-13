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
x["t_close"]=pd.to_datetime(np.where(ebt.notna()&bto.notna(), pd.to_datetime(ebt+300*(bto+1),unit="s",utc=True), x.ts+pd.Timedelta(minutes=120)),utc=True)
x["t_close"]=np.maximum(x.t_close, x.ts+pd.Timedelta(minutes=5))
x["key"]=x.symbol+" "+x.dir; x["R"]=x.cf_net
def thin(df):
    keep=[]
    for _,g in df.sort_values("t_open").groupby("key"):
        last=None
        for i,r in g.iterrows():
            if last is None or r.t_open>=last: keep.append(i); last=r.t_close
    return df.loc[keep]
m=thin(x[["key","t_open","t_close","R"]].dropna())
o=thin(x[x.cls=="OPEN"][["key","t_open","t_close","R"]].dropna())
print("tek-poz mekanik", len(m), "OPEN", len(o))
r=pd.concat([H.evaluate(m,"decider_mek_tekpoz",nperm=300),H.evaluate(o,"decider_OPEN_tekpoz",nperm=300)])
print(r.round(3).to_string()); r.to_csv("research/ortak_kapi_20261113/results_h10_decider_thin.csv",index=False)
