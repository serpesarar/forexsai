import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
from importlib import import_module
H=import_module("11_h10_bot")
DAX="GDAXI.INDX"; rng=np.random.default_rng(21)
t=load_bot(); t=t[t.symbol==DAX]
j=pd.read_parquet(BASE+"journal.parquet"); j=j[(j.symbol==DAX)&j.dir.isin(["BUY","SELL"])].sort_values("ts")
x=pd.read_parquet(BASE+"h7.parquet"); x=x[x.symbol==DAX]
print("=== DAX popülasyonları"); print(t.groupby(["family","direction"]).agg(n=("R","size"),R=("R","mean"),net=("net","sum"),lot=("volume","median")).round(3))
def bbneg(v,d):
    s=pd.Series(v).groupby(np.asarray(d)).apply(list); ks=list(s.index)
    return np.mean([np.mean(sum((s[ks[k]] for k in rng.choice(len(ks),len(ks))),[]))<0 for _ in range(2000)])
# D2
print("\n=== D2 tahsis/engel")
rows=[]
for (f,dr),g in t.groupby(["family","direction"]):
    w=g[g.open_utc>="2026-08-13"]; pre=g[g.open_utc<"2026-08-13"]
    if len(g)<10: continue
    mid=g.open_utc.median()
    rows.append((f"bot {f} {dr}",len(g),g.R.mean(),g[g.open_utc<mid].R.mean(),g[g.open_utc>=mid].R.mean(),bbneg(g.R.values,g.day.values),len(pre),pre.R.mean(),g.net.sum()))
op=x[x.cls=="OPEN"].copy(); op["day"]=op.ts.dt.date
allop=episodes(j[j.action=="OPEN"].assign(dir=j.dir)); allop["day"]=allop.ts.dt.date
for dr,g in allop.dropna(subset=["cf_net"]).groupby("dir"):
    w=g[g.ts>="2026-08-13"]; pre=g[g.ts<"2026-08-13"]; mid=w.ts.median()
    rows.append((f"decider journal OPEN {dr} (3ay)",len(w),w.cf_net.mean(),w[w.ts<mid].cf_net.mean(),w[w.ts>=mid].cf_net.mean(),bbneg(w.cf_net.values,w.day.values),len(pre),pre.cf_net.mean(),np.nan))
print(pd.DataFrame(rows,columns=["grup","n","R","h1","h2","P_neg","pre_n","pre_R","net$"]).round(3).to_string())
# D3 icra açığı
print("\n=== D3 icra açığı (decider DAX icraları vs aynı kararın simülasyonu)")
de=t[t.family=="DECIDER"].copy(); jo=j[j.action=="OPEN"]
m=[]
for r in de.itertuples():
    c=jo[(jo.dir==r.direction)&((jo.ts-r.open_utc).abs()<=pd.Timedelta(minutes=2))]
    if c.empty: m.append((r.open_utc,r.R,np.nan,np.nan,np.nan,np.nan,np.nan,r.net,r.close_utc)); continue
    c=c.iloc[((c.ts-r.open_utc).abs()).argmin()]
    sg=1 if r.direction=="BUY" else -1
    slip=sg*(r.open_price-c.entry)/c.atr if c.atr else np.nan
    sl_ratio=abs(r.open_price-r.sl0)/abs(c.entry-c.sl) if c.sl else np.nan
    m.append((r.open_utc,r.R,c.cf_pnl_r,c.cf_net,slip,sl_ratio,c.spread_atr,r.net,r.close_utc))
M=pd.DataFrame(m,columns=["t","R_real","cf","cf_net","slip_atr","sl_oran","spread_atr","net","t_close"])
M["hold"]=(M.t_close-M.t).dt.total_seconds()/60; M["gap"]=M.R_real-M.cf_net; M["day"]=M.t.dt.date
print(M.describe().round(3).T[["count","mean","50%"]])
mm=M.dropna(subset=["gap"]); print("eşleşen",len(mm),"açık ort",round(mm.gap.mean(),3),"P(açık<0)",round(bbneg(mm.gap.values,mm.day.values),3))
print(mm.groupby(pd.cut(mm.R_real,[-9,-0.9,-0.05,0.05,0.9,9])).agg(n=("gap","size"),cf=("cf_net","mean")).round(3))
M.to_parquet("research/ortak_kapi_dax_20261113/d3.parquet")
