import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
C={s:pd.read_parquet(BASE+f"close_{s.replace('.','_')}.parquet").close for s in ["NDX.INDX","GDAXI.INDX","XAUUSD","USOIL.FOREX"]}
PEER={"NDX.INDX":"GDAXI.INDX","GDAXI.INDX":"NDX.INDX","USOIL.FOREX":"NDX.INDX","XAUUSD":"NDX.INDX"}
def ret(sym,t,w):
    s=C[sym]; a=s.asof(t-pd.Timedelta(minutes=1)); b=s.asof(t-pd.Timedelta(minutes=1+w))
    ia=s.index.asof(t-pd.Timedelta(minutes=1))
    if pd.isna(a) or pd.isna(b) or pd.isna(ia) or (t-ia)>pd.Timedelta(minutes=10): return np.nan
    return a/b-1
def feats(df,w=30):
    sg=np.where(df.dir=="BUY",1,-1); own=[];peer=[];xau=[]
    for (s,t) in zip(df.symbol,df.t):
        own.append(ret(s,t,w)); peer.append(ret(PEER[s],t,w)); xau.append(ret("XAUUSD",t,w) if s in ("NDX.INDX","GDAXI.INDX") else np.nan)
    df=df.copy(); df["own"]=sg*np.array(own); df["peer"]=sg*np.array(peer); df["riskoff"]=-sg*np.array(xau)
    df["F1"]=df.peer>0; df["F2"]=(df.peer-df.own)>0; df["F3"]=df.riskoff>0
    return df.dropna(subset=["own","peer"])
# populations
t=load_bot(); t=t[~t.family.isin(["MANUEL","DECIDER"])&t.symbol.isin(PEER)]
A=pd.DataFrame(dict(symbol=t.symbol,dir=t.direction,t=t.open_utc,R=t.R)).dropna()
p=pd.read_parquet(BASE+"panel.parquet").dropna(subset=["R","t_close"]); p["key"]=p.model+" "+p.epoch+" "+p.symbol+" "+p.dir
keep=[]
for _,g in p.sort_values("t_open").groupby("key"):
    last=None
    for i,r in g.iterrows():
        if last is None or r.t_open>=last: keep.append(i); last=r.t_close
pp=p.loc[keep]; B=pd.DataFrame(dict(symbol=pp.symbol,dir=pp.dir,t=pp.t_open,R=pp.R,model=pp.model))
B=B[B.symbol.isin(PEER)]
x=pd.read_parquet(BASE+"h7.parquet"); Cc=pd.DataFrame(dict(symbol=x.symbol,dir=x.dir,t=x.ts,R=x.cf_net)).dropna()
rng=np.random.default_rng(12); out={}
for w in (30,15,60):
    for lab,df in (("A_bot",A),("B_panel",B),("C_decider",Cc)):
        f=feats(df,w); f["day"]=f.t.dt.date; mid=f.t.median()
        for F in ("F2","F1","F3"):
            g=f.dropna(subset=["R"]); 
            if F=="F3": g=g[g.symbol.isin(["NDX.INDX","GDAXI.INDX"])]
            a=g[g[F]]; b=g[~g[F]]
            if len(a)<10 or len(b)<10: continue
            d=a.R.mean()-b.R.mean(); h=[g[g[F]&(g.t<mid)].R.mean()-g[~g[F]&(g.t<mid)].R.mean(), g[g[F]&(g.t>=mid)].R.mean()-g[~g[F]&(g.t>=mid)].R.mean()]
            P=np.nan
            if lab=="B_panel" or w==30:
                P,_=block_boot(a.R.values,a.day.values,b.R.values,b.day.values,n=600)
            bysym=g.groupby("symbol").apply(lambda z: z.R[z[F]].mean()-z.R[~z[F]].mean()).round(3).to_dict()
            print(f"w{w} {lab:9s} {F}: n={len(a)}/{len(b)} R {a.R.mean():+.3f} vs {b.R.mean():+.3f} Δ{d:+.3f} yarılar {h[0]:+.3f}/{h[1]:+.3f} P={P:.3f} sembol {bysym}")
        if w==30: f.to_parquet(BASE+f"h12_{lab}.parquet")
