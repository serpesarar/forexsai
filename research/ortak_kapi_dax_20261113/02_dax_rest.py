import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
DAX="GDAXI.INDX"; rng=np.random.default_rng(22)
def rep(lab,a,b,ta,tb,da,db):
    if len(a)<5 or len(b)<5: print(lab,"yetersiz",len(a),len(b)); return
    allt=pd.concat([ta,tb]); mid=allt.median()
    h1=a[ta<mid].mean()-b[tb<mid].mean(); h2=a[ta>=mid].mean()-b[tb>=mid].mean()
    P,ci=block_boot(a.values,da,b.values,db,n=1500)
    print(f"{lab}: n={len(a)}/{len(b)} {a.mean():+.3f} vs {b.mean():+.3f} Δ{a.mean()-b.mean():+.3f} yarılar {h1:+.3f}/{h2:+.3f} P(Δ>0)={P:.3f}")
b1=pd.read_parquet(BASE+"bot_h1.parquet"); b1=b1[b1.symbol==DAX]
print("D1 bot DAX × decider:", b1.groupby("h1").R.agg(["size","mean"]).round(3).to_dict())
for L in ["AGREE","WAIT_SAME","WAIT_OPP"]:
    a=b1[b1.h1==L]; b=b1[b1.h1!=L]; rep(f"  D1 bot {L}",a.R,b.R,a.open_utc,b.open_utc,a.day.values,b.day.values)
h2=pd.read_parquet(BASE+"dec_ep_h2.parquet"); h2=h2[(h2.symbol==DAX)].dropna(subset=["cf_net"])
a=h2[h2.h2=="BOT_SAME"]; b=h2[h2.h2=="BOT_NONE"]; rep("  D1 decider OPEN BOT_SAME vs NONE",a.cf_net,b.cf_net,a.ts,b.ts,a.day.values,b.day.values)
x=pd.read_parquet(BASE+"h7.parquet"); x=x[x.symbol==DAX]; x["day"]=x.ts.dt.date
print("\nD4 mekanik tetik DAX:", x.groupby(["dir","cls"]).cf_net.agg(["size","mean"]).round(3).to_dict())
for dr in ["BUY","SELL"]:
    g=x[x.dir==dr]
    for c in ["SAHTE_WAIT","LLM_WAIT"]:
        a=g[g.cls=="OPEN"]; b=g[g.cls==c]
        # aynı hafta içinde: yalnız iki sınıfın da bulunduğu haftalar
        wk=set(a.ts.dt.strftime("%G-%V"))&set(b.ts.dt.strftime("%G-%V"))
        a=a[a.ts.dt.strftime("%G-%V").isin(wk)]; b=b[b.ts.dt.strftime("%G-%V").isin(wk)]
        rep(f"  D4 {dr} OPEN−{c} (ortak haftalar)",a.cf_net,b.cf_net,a.ts,b.ts,a.day.values,b.day.values)
bt=pd.read_parquet(BASE+"bot_h10.parquet"); bt=bt[bt.key.str.contains("GDAXI")&bt.prev.notna()]; bt["day"]=bt.t_open.dt.date
a=bt[bt.tk]; b=bt[~bt.tk]; rep("\nD5 bot DAX kendi karnesi k=5 al vs atla",a.R,b.R,a.t_open,b.t_open,a.day.values,b.day.values)
for lab in ("A_bot","C_decider"):
    f=pd.read_parquet(BASE+f"h12_{lab}.parquet"); f=f[f.symbol==DAX].dropna(subset=["R"]); f["day"]=f.t.dt.date
    for F in ("F1","F2"):
        a=f[f[F]]; b=f[~f[F]]; rep(f"D6 {lab} {F}",a.R,b.R,a.t,b.t,a.day.values,b.day.values)
