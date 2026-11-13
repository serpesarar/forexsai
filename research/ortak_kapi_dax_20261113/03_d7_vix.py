import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,"research/ortak_kapi_20261113"); sys.path.insert(0,".")
from common import *
from scripts.islem_otopsi import data as D
DAX="GDAXI.INDX"; T=18.4
vx=pd.read_csv("research/ndx_gate_forge/data/macro_daily_patched.csv",parse_dates=["date"]).set_index("date")["VIX_close"].dropna()
try:
    v2=D.load_vix(pd.Timestamp("2026-06-01",tz="UTC"),pd.Timestamp("2026-11-14",tz="UTC")); v2.index=pd.to_datetime(v2.index).tz_localize(None).normalize()
    vx=pd.concat([vx,v2[~v2.index.isin(vx.index)]]).sort_index()
except Exception as e: print("load_vix",e)
def prev_vix(ts):
    d=pd.DatetimeIndex(pd.to_datetime(ts).dt.tz_convert(None).dt.normalize())
    s=vx.copy(); s.index=s.index+pd.Timedelta(days=1)   # önceki günün kapanışı ertesi gün bilinir
    return s.reindex(d,method="ffill").to_numpy()
print("VIX son", vx.index.max(), vx.iloc[-1])
rng=np.random.default_rng(31)
def rep(lab,R,v,ts,days):
    calm=v<T; fear=v>=T; ok=~np.isnan(v)
    a=R[calm&ok]; b=R[fear&ok]
    mid=np.median(ts[ok].astype("int64"))
    h=[R[calm&ok&(ts.astype("int64")<mid)].mean()-R[fear&ok&(ts.astype("int64")<mid)].mean(), R[calm&ok&(ts.astype("int64")>=mid)].mean()-R[fear&ok&(ts.astype("int64")>=mid)].mean()]
    P,_=block_boot(a,days[calm&ok],b,days[fear&ok],n=1000) if len(a)>4 and len(b)>4 else (np.nan,None)
    print(f"{lab}: SAKİN n={len(a)} {np.mean(a):+.3f} | KORKU n={len(b)} {np.mean(b):+.3f} | fark {np.mean(a)-np.mean(b):+.3f} yarılar {h[0]:+.3f}/{h[1]:+.3f} P(fark>0)={P:.3f}")
t=load_bot(); t=t[(t.symbol==DAX)&(t.direction=="BUY")&t.family.isin(["MOMSR","CHREV"])].dropna(subset=["R"])
rep("(a) bot DAX BUY",t.R.values,prev_vix(t.open_utc),t.open_utc.values,t.day.values)
j=pd.read_parquet(BASE+"dec_ep_h2.parquet"); j=j[(j.symbol==DAX)&(j.dir=="BUY")].dropna(subset=["cf_net"])
rep("(b) decider DAX BUY OPEN",j.cf_net.values,prev_vix(j.ts),j.ts.values,j.ts.dt.date.values)
x=pd.read_parquet(BASE+"h7.parquet"); x=x[(x.symbol==DAX)&(x.dir=="BUY")].dropna(subset=["cf_net"])
rep("(b2) decider DAX BUY mekanik",x.cf_net.values,prev_vix(x.ts),x.ts.values,x.ts.dt.date.values)
# (c) vekil
sys.path.insert(0,"research/ndx_sell_dusus_20261008"); import run as P
def sim(d,bar_h):
    o,hi,lo,c=(d[k].to_numpy() for k in ("open","high","low","close")); n=len(d); maxk=int(P.MAX_HOLD_H/bar_h); rows=[]; busy=-1
    for i in np.flatnonzero(d.index.dayofweek<5):
        j=i+1
        if j>=n or i<=busy: continue
        e=o[j]*(1+P.HALF_SPREAD_PCT); tp,sl=e*(1+P.TP_PCT),e*(1-P.SL_PCT)
        kt=np.flatnonzero(hi[j:j+maxk]>=tp); ks=np.flatnonzero(lo[j:j+maxk]<=sl); a=kt[0] if kt.size else np.inf; b=ks[0] if ks.size else np.inf
        if np.isinf(a) and np.isinf(b): k=min(maxk,n-j)-1; R=(c[j+k]-e)/(e*P.SL_PCT)
        else: k=int(min(a,b)); R=-1.0 if b<=a else P.TP_PCT/P.SL_PCT
        busy=j+k; rows.append((d.index[i],R))
    return pd.DataFrame(rows,columns=["ts","R"])
for f,bh,lo_,hi_ in (("dax_30m",0.5,"2021-03-17","2026-10-03"),("dax_1h",1.0,"2016-01-01","2021-03-17")):
    d=pd.read_parquet(f"research/ndx_gate_forge/data/{f}.parquet"); d["ts"]=pd.to_datetime(d.ts,utc=True); d=d.set_index("ts").sort_index()
    d=d[(d.index>=lo_)&(d.index<hi_)]
    r=sim(d,bh); ts=pd.Series(r.ts)
    rep(f"(c) vekil {f} {lo_[:4]}-{hi_[:4]}",r.R.values,prev_vix(ts),r.ts.values,ts.dt.date.values)
