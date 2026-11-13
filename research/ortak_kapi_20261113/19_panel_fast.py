import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
p=pd.read_parquet("research/ortak_kapi_20261113/data/panel.parquet").dropna(subset=["R","t_close"])
p["key"]=p.model+" "+p.epoch+" "+p.symbol+" "+p.dir
keep=[]
for _,g in p.sort_values("t_open").groupby("key"):
    last=None
    for i,r in g.iterrows():
        if last is None or r.t_open>=last: keep.append(i); last=r.t_close
t=p.loc[keep].sort_values("t_open"); t=t[t.groupby("key").R.transform("size")>=15]
print("tek-poz panel dizisi", len(t), "anahtar", t.key.nunique())
rng=np.random.default_rng(6); mid=t.t_open.median()
def rule(df,k):
    prev=df.groupby("key").R.transform(lambda s: s.shift(1).rolling(k).mean()); m=prev.notna()
    return m&(prev<=0), m&(prev>0)
for k in (3,5,10):
    a,b=rule(t,k); d=t.R[a].mean()-t.R[b].mean()
    h=[t.R[a&(t.t_open<mid)].mean()-t.R[b&(t.t_open<mid)].mean(), t.R[a&(t.t_open>=mid)].mean()-t.R[b&(t.t_open>=mid)].mean()]
    pl=[]
    for _ in range(500):
        y=t.assign(R=t.groupby("key").R.transform(lambda s: rng.permutation(s.values))); aa,bb=rule(y,k); pl.append(y.R[aa].mean()-y.R[bb].mean())
    fam=t.assign(a=a,b=b).groupby("key").apply(lambda g: g.R[g.a].mean()-g.R[g.b].mean())
    print(f"k={k}: al {t.R[a].mean():+.3f} (n={a.sum()}) atla {t.R[b].mean():+.3f} (n={b.sum()}) Δ{d:+.3f} yarılar {h[0]:+.3f}/{h[1]:+.3f} plasebo %{(np.array(pl)<d).mean()*100:.0f} anahtar +{(fam>0).sum()}/{fam.notna().sum()}")
