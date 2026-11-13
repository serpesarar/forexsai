import pandas as pd, numpy as np
df = pd.read_parquet("research/ortak_kapi_20261113/data/trades.parquet")
df = df[df.open_raw >= "2026-08-13"].copy()
sgn = np.where(df.direction=="BUY",1,-1)
risk = (df.open_price-df.sl0).abs()
df["R"] = np.where(risk>0, sgn*(df.close_price-df.open_price)/risk, np.nan)
df["hold_min"] = (df.close_raw-df.open_raw).dt.total_seconds()/60
df["win"] = df.net>0
df["agent"] = np.where(df.family=="DECIDER","DECIDER",np.where(df.family=="MANUEL","MANUEL","BOT"))
df["month"] = df.open_raw.dt.strftime("%m")
df.to_parquet("research/ortak_kapi_20261113/data/trades_3m.parquet")
print("toplam", len(df), "net", round(df.net.sum()), "R ort", round(df.R.mean(),3))
g = df.groupby(["agent","family","symbol","direction"])
t = g.agg(n=("R","size"),wr=("win","mean"),R=("R","mean"),Rsum=("R","sum"),net=("net","sum"),lot=("volume","median"),hold=("hold_min","median"),sl_none=("sl0",lambda s:(s.fillna(0)==0).sum()))
print(t.round(3).to_string())
print(df.groupby(["agent","month"]).agg(n=("R","size"),R=("R","mean"),net=("net","sum")).round(3).to_string())
print(df[df.R.isna()|(df.R.abs()>10)][["family","symbol","direction","open_price","sl0","close_price","net"]].head(20))
