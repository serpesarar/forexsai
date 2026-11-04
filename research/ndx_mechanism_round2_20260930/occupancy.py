"""Does the previous portfolio's variance subset beat neutral busy calendars?"""
import numpy as np
import pandas as pd
from data import HERE, OUT, lab, old2, datasets
from experiment import cached_features, sequential

def run():
    d=datasets()["mt5"];f=cached_features(d,"mt5",1);grid=lab.simulate_grid(d)
    lab.PERIODS["old_september"]=("2026-09-01","2026-09-30")
    spec={"family":"variance_switch","lookback":30,"context":"quiet","side":"both"}
    t,s=old2.detect(f,spec)
    raw=lab.replay(t,s,grid,"old_september",False)
    p=pd.read_csv(HERE.parent/"ndx_five_gates_20260930/results/second_portfolio_trades.csv")
    actual=p[p.candidate.eq("variance_switch_30_quiet_both_core")].copy()
    keys=set(zip(actual.decision,actual.side))
    raw["accepted"]=[v in keys for v in zip(raw.decision,raw.side)]
    assert raw.accepted.sum()==len(actual)==22
    k=np.searchsorted(f.decision.to_numpy(),raw.decision.to_numpy())
    for col in ["vr30","vr120","h1_dir","m15_dir","er60_m1","drift60_m1"]:raw[col]=f[col].to_numpy()[k]
    raw["branch"]=np.where(raw.vr30>1.25,"breakout","fade")
    table={str(key):{**lab.stats(x),"h1_aligned":float((x.h1_dir*x.side>0).mean()),
                   "m15_aligned":float((x.m15_dir*x.side>0).mean()),"vr120":float(x.vr120.mean())}
           for key,x in raw.groupby(["accepted","branch"])}
    # Descriptive availability placebo: shift known non-variance busy masks within
    # each day. This is a retrospective schedule diagnostic, not a trading rule.
    times=grid[1];lo,hi=map(lab.stamp,lab.PERIODS["old_september"])
    times=times[(times.decision>=lo)&(times.exit_t<hi)]
    other=p[~p.candidate.eq("variance_switch_30_quiet_both_core")]
    masks={}
    for day,x in times.groupby("day"):
        ts=x.decision.to_numpy();busy=np.zeros(len(ts),bool)
        for r in other[other.day.eq(day)].itertuples():busy |= (ts>=r.decision)&(ts<r.exit_t)
        masks[day]=(ts,busy)
    rng=np.random.default_rng(935);ev=[];tot=[];n=[]
    for rep in range(500):
        keep=np.zeros(len(raw),bool)
        for day,x in raw.groupby("day"):
            if day not in masks:continue
            ts,busy=masks[day];shift=int(rng.integers(len(ts)));bm=np.roll(busy,shift)
            k=np.searchsorted(ts,x.decision.to_numpy());safe=np.minimum(k,len(ts)-1)
            good=(k<len(ts))&(ts[safe]==x.decision.to_numpy())&~bm[safe]
            keep[x.index]=good
        r=sequential(raw[keep]);ev.append(float(r.R.mean()) if len(r) else 0.)
        tot.append(float(r.R.sum()));n.append(len(r))
    res={"raw_opportunities":len(raw),"actual_variance_subset":lab.stats(actual),"branch_table":table,
         "neutral_shifted_busy_calendars":{"repetitions":500,"n_q05_q50_q95":np.quantile(n,[.05,.5,.95]).tolist(),
             "EV_q05_q50_q95":np.quantile(ev,[.05,.5,.95]).tolist(),
             "total_R_q05_q50_q95":np.quantile(tot,[.05,.5,.95]).tolist(),
             "fraction_total_at_least_actual":float(np.mean(np.asarray(tot)>=actual.R.sum())),
             "fraction_EV_at_least_actual":float(np.mean(np.asarray(ev)>=actual.R.mean()))},
         "interpretation":"Selection/path dependence diagnostic; same observed month, not independent evidence or an ex-ante rule."}
    raw.to_csv(OUT/"variance_raw_occupancy.csv",index=False)
    lab.save_json(OUT/"occupancy.json",res);print(res,flush=True)

if __name__=="__main__":run()
