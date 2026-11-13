import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
from importlib import import_module
H=import_module("11_h10_bot")
t=load_bot(); t=t[~t.family.isin(["MANUEL","DECIDER"])]
t["key"]=t.family+" "+t.symbol+" "+t.direction; t=t[t.groupby("key").R.transform("size")>=15]
t=t.rename(columns={"open_utc":"t_open","close_utc":"t_close"}).dropna(subset=["R"]).reset_index(drop=True)
rng=np.random.default_rng(2)
print("plato k=2..12 (fark, alınan ort, atlanan ort, n_al):")
for k in range(1,13):
    prev,d=H.causal_prev(t[["key","t_open","t_close","R"]],k); m=~np.isnan(prev)
    print(k, round(d.R[m&(prev<=0)].mean()-d.R[m&(prev>0)].mean(),3), round(d.R[m&(prev<=0)].mean(),3), round(d.R[m&(prev>0)].mean(),3), int((m&(prev<=0)).sum()))
k=5
prev,_=H.causal_prev(t[["key","t_open","t_close","R"]],k); t["prev"]=prev
m=t.prev.notna(); t["tk"]=t.prev<=0
print("\naile başına (k=5):")
print(t[m].groupby(["key","tk"]).agg(n=("R","size"),R=("R","mean"),net=("net","sum")).round(3).unstack().to_string())
# gün-blok bootstrap
d=t[m]; days=d.t_open.dt.date; ud=days.unique(); out=[]
for _ in range(2000):
    s=rng.choice(ud,len(ud)); y=pd.concat([d[days==x] for x in s])
    out.append(y.R[y.tk].mean()-y.R[~y.tk].mean())
print("\nk=5 gün-blok P(fark>0)=",np.mean(np.array(out)>0).round(3),"CI",np.percentile(out,[2.5,97.5]).round(3))
print("$ etkisi k=5: kural net", round(d.net[d.tk].sum()), "vs hepsi", round(d.net.sum()), "atlanan $", round(d.net[~d.tk].sum()))
# aylara göre
print(d.groupby([d.t_open.dt.strftime('%m'),"tk"]).R.agg(['size','mean']).round(3).unstack().to_string())
t.to_parquet(BASE+"bot_h10.parquet")
