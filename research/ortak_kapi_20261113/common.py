import pandas as pd, numpy as np
BASE="research/ortak_kapi_20261113/data/"
def to_utc(s):
    off = np.where(s < pd.Timestamp("2026-11-01 05:00", tz="UTC"), 3, 2)
    return s - pd.to_timedelta(off, unit="h")
def load_bot():
    t = pd.read_parquet(BASE+"trades.parquet")
    t["open_utc"]=to_utc(t.open_raw); t["close_utc"]=to_utc(t.close_raw)
    t = t[t.open_utc>="2026-06-25"].copy()
    sgn=np.where(t.direction=="BUY",1,-1); risk=(t.open_price-t.sl0).abs()
    t["R"]=np.where(risk>0, sgn*(t.close_price-t.open_price)/risk, np.nan)
    t["day"]=t.open_utc.dt.date
    return t
def load_journal():
    j = pd.read_parquet(BASE+"journal.parquet")
    import json
    return j
def episodes(df, gap_min=30):
    df=df.sort_values("ts").copy(); keep=[]; last={}
    for i,r in df.iterrows():
        k=(r.symbol,r.dir)
        if k not in last or (r.ts-last[k]).total_seconds()>gap_min*60: keep.append(i)
        last[k]=r.ts
    return df.loc[keep]
def block_boot(vals_a, days_a, vals_b, days_b, n=2000, seed=0):
    """P(mean_a - mean_b > 0) gün-blok bootstrap."""
    rng=np.random.default_rng(seed)
    da=pd.Series(vals_a).groupby(np.asarray(days_a)).apply(list); db=pd.Series(vals_b).groupby(np.asarray(days_b)).apply(list)
    alld=sorted(set(da.index)|set(db.index)); out=[]
    for _ in range(n):
        s=rng.choice(len(alld),len(alld)); A=[];B=[]
        for k in s:
            d=alld[k]
            if d in da.index: A+=da[d]
            if d in db.index: B+=db[d]
        if A and B: out.append(np.mean(A)-np.mean(B))
    out=np.array(out); return (out>0).mean(), np.percentile(out,[2.5,97.5])
