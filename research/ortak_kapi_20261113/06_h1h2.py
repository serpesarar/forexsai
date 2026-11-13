import sys; sys.path.insert(0,"research/ortak_kapi_20261113")
import pandas as pd, numpy as np
from common import *
t=load_bot(); j=pd.read_parquet(BASE+"journal.parquet")
j=j[j.dir.isin(["BUY","SELL"])].sort_values("ts")
bot=t[~t.family.isin(["DECIDER","MANUEL"])].copy()
# ---- H1
def lab_h1(r, shift=pd.Timedelta(0)):
    c=j[(j.symbol==r.symbol)&(j.ts<=r.open_utc+shift)&(j.ts>r.open_utc+shift-pd.Timedelta(minutes=30))]
    if c.empty: return "NONE"
    l=c.iloc[-1]; same=l.dir==r.direction
    return ("AGREE" if same else "OPPOSE") if l.action=="OPEN" else ("WAIT_SAME" if same else "WAIT_OPP")
bot["h1"]=[lab_h1(r) for r in bot.itertuples()]
print("H1 bot pozisyonları (06-25→):", len(bot))
print(bot.groupby(["h1"]).agg(n=("R","size"),R=("R","mean"),net=("net","sum")).round(3))
print(bot.groupby(["symbol","direction","h1"]).agg(n=("R","size"),R=("R","mean")).round(3))
mid=bot.open_utc.median()
for lab in ["AGREE","OPPOSE"]:
    a=bot[bot.h1==lab]; b=bot[bot.h1!=lab]
    if len(a)<5: continue
    h=[(a[a.open_utc<mid].R.mean()-b[b.open_utc<mid].R.mean()),(a[a.open_utc>=mid].R.mean()-b[b.open_utc>=mid].R.mean())]
    p,ci=block_boot(a.R.values,a.day.values,b.R.values,b.day.values)
    print(f"H1 {lab}: n={len(a)} Δ={a.R.mean()-b.R.mean():+.3f} yarılar {h[0]:+.3f}/{h[1]:+.3f} P(Δ>0)={p:.3f} CI {ci.round(3)}")
bot.to_parquet(BASE+"bot_h1.parquet")
# ---- H2
op=j[j.action=="OPEN"].copy(); op=episodes(op)
def lab_h2(r):
    s=bot[bot.symbol==r.symbol]
    openpos=s[(s.open_utc<=r.ts)&(s.close_utc>r.ts)]
    recent=s[(s.open_utc<=r.ts)&(s.open_utc>r.ts-pd.Timedelta(minutes=60))]
    cand=pd.concat([openpos,recent])
    if cand.empty: return "BOT_NONE"
    if (cand.direction==r.dir).any() and not (cand.direction!=r.dir).any(): return "BOT_SAME"
    if (cand.direction!=r.dir).any() and not (cand.direction==r.dir).any(): return "BOT_OPP"
    return "BOT_MIX"
op["h2"]=[lab_h2(r) for r in op.itertuples()]
op["day"]=op.ts.dt.date
print("\nH2 decider OPEN epizodları:", len(op))
print(op.groupby(["symbol","dir","h2"]).agg(n=("cf_net","size"),cf=("cf_pnl_r","mean"),net=("cf_net","mean")).round(3))
mid=op.ts.median()
for lab in ["BOT_SAME","BOT_OPP"]:
    a=op[op.h2==lab].dropna(subset=["cf_net"]); b=op[op.h2=="BOT_NONE"].dropna(subset=["cf_net"])
    b=b[b.symbol.isin(a.symbol.unique())]
    h=[(a[a.ts<mid].cf_net.mean()-b[b.ts<mid].cf_net.mean()),(a[a.ts>=mid].cf_net.mean()-b[b.ts>=mid].cf_net.mean())]
    p,ci=block_boot(a.cf_net.values,a.day.values,b.cf_net.values,b.day.values)
    print(f"H2 {lab}: n={len(a)} Δ={a.cf_net.mean()-b.cf_net.mean():+.3f} yarılar {h[0]:+.3f}/{h[1]:+.3f} P(Δ>0)={p:.3f} CI {ci.round(3)}")
op.to_parquet(BASE+"dec_ep_h2.parquet")
