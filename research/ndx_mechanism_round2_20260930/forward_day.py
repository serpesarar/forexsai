"""No re-selection: evaluate the same frozen derivatives on a later full day."""
import hashlib
import json
import numpy as np
import pandas as pd
from data import HERE, OUT, lab, datasets, prepare, context
from experiment import GEOM, candidates, parent, replay, sequential, PERIODS

def run():
    payload=json.loads((OUT/"fresh_day.json").read_text())
    new=pd.DataFrame(payload["rows"],columns=["t","open","high","low","close","volume","spread"])
    new["spread_px"]=new.spread*payload["point"]
    old=datasets()["mt5"]
    overlap=old[["t","close"]].merge(new[["t","close"]],on="t",suffixes=("_old","_new"))
    err=np.abs(overlap.close_old-overlap.close_new)
    assert len(overlap)>500 and err.median()<1, "New-day clock/price overlap failed"
    bad=(new.high<new[["open","close"]].max(axis=1))|(new.low>new[["open","close"]].min(axis=1))|(new.high<new.low)
    assert not bad.any() and not new.t.duplicated().any()
    d=prepare(pd.concat([old.drop(columns=["ts"]),new],ignore_index=True),"mt5_extended")
    # prepare drops timestamp duplicates. Prefer the already frozen warmup on overlap.
    PERIODS["new_day"]=("2026-09-30","2026-10-01");lab.PERIODS.update(PERIODS)
    frozen=json.loads((OUT/"frozen_derivatives.json").read_text())
    fs={tf:context(d,tf)for tf in [1,3,5]}
    grids={geom:lab.simulate_grid(d,**kw)for geom,kw in GEOM.items()}
    rows=[];raws=[]
    for priority,spec in enumerate(frozen["candidates"]):
        a=candidates(d,fs[1],spec);g=grids[spec["geometry"]]
        r=replay(a,g,"new_day");raw=replay(a,g,"new_day",False);raw["priority"]=priority;raw["candidate"]=spec["id"];raws.append(raw)
        r.to_csv(OUT/f"forward_{spec['id']}.csv",index=False)
        tf_metrics={str(tf):lab.stats(replay(candidates(d,fs[tf],spec),g,"new_day"))for tf in [3,5]}
        rows.append({"id":spec["id"],"stats":lab.stats(r),"parent":lab.stats(replay(parent(fs[1],spec),g,"new_day")),
                     "tf_transfer":tf_metrics})
    p=sequential(pd.concat(raws,ignore_index=True));p.to_csv(OUT/"forward_portfolio.csv",index=False)
    day=new[(new.t>=lab.stamp("2026-09-30"))&(new.t<lab.stamp("2026-10-01"))]
    audit={"new_day_rows":len(day),"overlap_rows":len(overlap),"overlap_median_close_error":float(err.median()),
           "overlap_max_close_error":float(err.max()),"spread_points":{str(k):int(v)for k,v in day.spread_px.value_counts().items()},
           "bad_ohlc":int(bad.sum()),"frozen_sha256":hashlib.sha256((OUT/"frozen_derivatives.json").read_bytes()).hexdigest()}
    lab.save_json(OUT/"forward_day.json",{"day":"2026-09-30","audit":audit,"candidates":rows,"portfolio":lab.stats(p),
        "interpretation":"One later calendar day, frozen rules unchanged. Not enough independent days or resolved events for profitability claims."})
    print("NEW DAY",rows,"PORTFOLIO",lab.stats(p),flush=True)

if __name__=="__main__":run()
