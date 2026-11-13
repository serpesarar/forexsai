import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
from importlib import import_module
H=import_module("11_h10_bot")
def thin(df):
    keep=[]
    for _,g in df.sort_values("t_open").groupby("key"):
        last=None
        for i,r in g.iterrows():
            if last is None or r.t_open>=last: keep.append(i); last=r.t_close
    return df.loc[keep]
p=pd.read_parquet(BASE+"panel.parquet").dropna(subset=["R","t_close"])
p["key"]=p.model+" "+p.epoch+" "+p.symbol+" "+p.dir
p=p[p.groupby("key").R.transform("size")>=15][["key","t_open","t_close","R"]]
pt=thin(p); pt=pt[pt.groupby("key").R.transform("size")>=15]
print("panel ham", len(p), "inceltilmiş", len(pt), "anahtar", pt.key.nunique())
res=[H.evaluate(p,"panel_ham",nperm=200), H.evaluate(pt,"panel_tekpoz",nperm=300)]
# decider inceltilmiş


r=pd.concat(res); print(r.round(3).to_string()); r.to_csv("research/ortak_kapi_20261113/results_h10_panel.csv",index=False)
