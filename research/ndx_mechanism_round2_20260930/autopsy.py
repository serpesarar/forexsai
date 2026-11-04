"""Descriptive common mechanisms; no candidate selection from these tables."""
from __future__ import annotations
import numpy as np
import pandas as pd
from data import lab, HERE, OUT, datasets, context, bot_decisions
from experiment import cached_features

def describe(x, value, masks):
    out = {}
    for name, mask in masks.items():
        mask=pd.Series(mask,index=x.index).astype("boolean")
        yes, no = x[mask.fillna(False)], x[(~mask).fillna(False)]
        out[name] = {"yes_n": len(yes), "no_n": len(no), "yes_days": int(yes.day.nunique()),
                     "yes_mean": float(yes[value].mean()) if len(yes) else 0.,
                     "no_mean": float(no[value].mean()) if len(no) else 0.,
                     "yes_sum": float(yes[value].sum()), "no_sum": float(no[value].sum()),
                     "yes_wr": float((yes[value]>0).mean()) if len(yes) else 0.,
                     "no_wr": float((no[value]>0).mean()) if len(no) else 0.,"unknown_n":int(mask.isna().sum())}
    return out

def run():
    d = datasets()["mt5"]
    f = cached_features(d,"mt5",1)
    # Actual seconds use only the most recent fully closed M1 feature row.
    g = bot_decisions()
    k = np.searchsorted(f.decision.to_numpy(), g.decision.to_numpy(), side="right")-1
    ok = (k >= 0) & ((g.decision.to_numpy()-f.decision.to_numpy()[np.maximum(k,0)]) < 120)
    g = g[ok].reset_index(drop=True)
    k = k[ok]
    for col in ["close","atr70","h1_dir","h1_fresh","m15_dir","m5_body","vr120","er60_m1","drift60_m1","pos240","cont240","valid60","ret1","ret5","z5","day"]:
        g[col] = f[col].to_numpy()[k]
    err = np.abs(g.open_price - g.close)
    assert err.median()<10, "Trade/bar clock mismatch"
    masks = {"h1_aligned":(g.h1_dir*g.side>0).astype("boolean").where(g.h1_fresh),
             "m15_aligned":(g.m15_dir*g.side>0).astype("boolean").where(g.m15_dir.notna()),
             "m5_body_aligned":(g.m5_body*g.side>.5).astype("boolean").where(g.m5_body.notna()),
             "coherent_h1_m15":((g.h1_dir*g.side>0)&(g.m15_dir*g.side>0)).astype("boolean").where(g.h1_fresh & g.m15_dir.notna()),
             "persistent_path_aligned":((g.vr120>1.2)&(g.drift60_m1*g.side>0)).astype("boolean").where(g.cont240),
             "room_in_4h_range":pd.Series(np.where(g.side>0,g.pos240<.6,g.pos240>.4)).astype("boolean").where(g.cont240),
             "stress_sell":(g.side<0)&((g.ret1<=-.015)|(g.ret5<=-.04))}
    records = {"actual_bot": {"input_decisions":len(bot_decisions()),"n":len(g),"excluded_stale_or_missing":len(bot_decisions())-len(g),
               "days":g.day.nunique(),"usd":g.usd.sum(),
               "median_price_error":err.median(),"descriptive":describe(g,"points",masks)}}
    records["by_magic"] = {str(m):{"n":len(x),"days":x.day.nunique(),"usd":x.usd.sum(),
            "mean_points":x.points.mean(),"wr":(x.points>0).mean(),
            "descriptive":describe(x,"points",{name:np.asarray(mask)[x.index] for name,mask in masks.items()})}
            for m,x in g.groupby("magic")}
    g.to_csv(OUT/"actual_bot_asof.csv",index=False)
    old = HERE.parent / "ndx_five_gates_20260930/results"
    p = pd.read_csv(old/"second_portfolio_trades.csv")
    allv = pd.read_csv(old/"second_trades_variance_switch_30_quiet_both_core.csv")
    accepted = p[p.candidate.eq("variance_switch_30_quiet_both_core")]
    keys = set(zip(accepted.decision,accepted.side))
    k = np.searchsorted(f.decision.to_numpy(), allv.decision.to_numpy(),side="right")-1
    for col in ["vr30","vr120","h1_dir","m15_dir","er60_m1","drift60_m1","day"]:
        allv[col] = f[col].to_numpy()[k]
    allv["accepted"] = [v in keys for v in zip(allv.decision,allv.side)]
    allv["branch"] = np.where(allv.vr30>1.25,"breakout","fade")
    records["variance_occupancy"] = {str(key):{"n":len(x),"EV":x.R.mean(),"sum_R":x.R.sum(),
            "h1_alignment":float((x.h1_dir*x.side>0).mean()),
            "m15_alignment":float((x.m15_dir*x.side>0).mean()),
            "vr120":x.vr120.mean(),"ER60":x.er60_m1.mean()}
            for key,x in allv.groupby(["accepted","branch"])}
    records["variance_occupancy_note"]="This table intersects two different sequential subsets; occupancy.json uses all raw opportunities and is the authoritative occupancy analysis."
    allv.to_csv(OUT/"variance_occupancy.csv",index=False)
    lab.save_json(OUT/"autopsy.json",records)
    print(records,flush=True)

if __name__=="__main__":run()
