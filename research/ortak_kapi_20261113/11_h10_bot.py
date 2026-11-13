import sys; sys.path.insert(0,"research/ortak_kapi_20261113")
from common import *
def causal_prev(df, k, key="key", t_open="t_open", t_close="t_close", val="R"):
    out=np.full(len(df),np.nan); df=df.reset_index(drop=True)
    for _,g in df.groupby(key):
        g=g.sort_values(t_open)
        closes=g[[t_close,val]].sort_values(t_close)
        cc=closes[t_close].values; cv=closes[val].values
        for i,r in g.iterrows():
            idx=np.searchsorted(cc, np.datetime64(r[t_open]), side="left")
            if idx>=k: out[i]=cv[idx-k:idx].mean()
    return out, df
def evaluate(df, label, ks=(1,3,5,10), nperm=1000, seed=0):
    rng=np.random.default_rng(seed); res=[]
    mid=df.t_open.quantile(0.5)
    for k in ks:
        prev,d=causal_prev(df,k)
        m=~np.isnan(prev); take=m&(prev<=0); skip=m&(prev>0)
        diff=d.R[take].mean()-d.R[skip].mean()
        h=[d.R[take&(d.t_open<mid)].mean()-d.R[skip&(d.t_open<mid)].mean(), d.R[take&(d.t_open>=mid)].mean()-d.R[skip&(d.t_open>=mid)].mean()]
        fam=d[m].assign(tk=take[m]).groupby("key").apply(lambda g: g.R[g.tk].mean()-g.R[~g.tk].mean() if g.tk.any() and (~g.tk).any() else np.nan)
        pl=[]
        for _ in range(nperm):
            y=d.copy(); y["R"]=y.groupby("key").R.transform(lambda s: rng.permutation(s.values))
            # permute outcomes but keep timing → R moves with trade
            p2,_=causal_prev(y,k); mm=~np.isnan(p2)
            pl.append(y.R[mm&(p2<=0)].mean()-y.R[mm&(p2>0)].mean())
        pct=(np.array(pl)<diff).mean()
        res.append(dict(pop=label,k=k,n_take=int(take.sum()),R_take=d.R[take].mean(),n_skip=int(skip.sum()),R_skip=d.R[skip].mean(),
                        R_all=d.R[m].mean(),diff=diff,h1=h[0],h2=h[1],plasebo_pct=pct,
                        fam_pos=int((fam>0).sum()),fam_n=int(fam.notna().sum()),SumR_rule=d.R[take].sum(),SumR_all=d.R[m].sum()))
    return pd.DataFrame(res)
if __name__=="__main__":
    t=load_bot(); t=t[~t.family.isin(["MANUEL","DECIDER"])]
    t["key"]=t.family+" "+t.symbol+" "+t.direction; t=t[t.groupby("key").R.transform("size")>=15]
    t=t.rename(columns={"open_utc":"t_open","close_utc":"t_close"})
    r=evaluate(t[["key","t_open","t_close","R"]].dropna(),"bot",nperm=300)
    print(r.round(3).to_string()); r.to_csv("research/ortak_kapi_20261113/results_h10_bot.csv",index=False)
