"""Decision-time prefix invariance and delayed-entry synthetic tests."""
import numpy as np
import pandas as pd
from data import OUT, lab, datasets, context
from experiment import definitions, candidates, delayed

def run():
    d=datasets()["mt5"]
    # An arbitrary intrabar cutoff, including incomplete 3m/5m/M15 bins.
    cutoff=lab.stamp("2026-06-03 14:07")
    ds=d[(d.t>=lab.stamp("2026-05-20")) & (d.t<lab.stamp("2026-06-05"))].copy()
    prefix=ds[ds.t<cutoff].copy()
    for tf in [1,3,5]:
        full,pre=context(ds,tf),context(prefix,tf)
        ff=full[full.decision<=cutoff].reset_index(drop=True)
        pd.testing.assert_frame_equal(ff,pre.reset_index(drop=True))
        for spec in definitions():
            a=candidates(ds,full,spec);a=a[a.decision<=cutoff].reset_index(drop=True)
            b=candidates(prefix,pre,spec).reset_index(drop=True)
            pd.testing.assert_frame_equal(a,b)
    # Future price changes must never alter earlier decisions.
    altered=ds.copy();altered.loc[altered.t>=cutoff,["open","high","low","close"]]*=1.2
    a=context(ds,1);b=context(altered,1)
    pd.testing.assert_frame_equal(a[a.decision<=cutoff].reset_index(drop=True),b[b.decision<=cutoff].reset_index(drop=True))
    ts=np.arange(1000,1600,60)
    toy=pd.DataFrame({"t":ts,"open":100.,"close":100.,"high":101.,"low":99.})
    x=pd.DataFrame({"origin":[1000],"decision":[1000],"side":[1],"close":[100.],"atr70":[2.],"atr14":[2.],
                    "lo60":[90.],"hi60":[110.],"reclaimed_level":[98.]})
    z=delayed(toy.iloc[:5],x,5)
    assert len(z)==1 and z.decision.iloc[0]==1300 and z.level_held.iloc[0] and z.band_alive.iloc[0]
    toy.loc[2,"close"]=97.
    assert not delayed(toy,x,5).level_held.iloc[0]
    toy.loc[2,"low"]=90.
    assert not delayed(toy,x,5).band_alive.iloc[0]
    toy.loc[4,"close"]=102.
    assert not delayed(toy,x,5).fair_price.iloc[0]
    assert delayed(toy.drop(index=2).reset_index(drop=True),x,5).empty
    ny=pd.Series(pd.date_range("2025-01-01",periods=10000,freq="h",tz="UTC")).dt.tz_convert("America/New_York")
    assert ny.dt.strftime("%Y-%m-%d").equals(ny.dt.tz_localize(None).dt.strftime("%Y-%m-%d"))
    lab.save_json(OUT/"verification.json",{"prefix_checks":"20 definitions × 3 timeframes passed",
        "future_price_perturbation":"passed","delay_fixtures":5,"date_format_equivalence":10000})
    print("20 definitions × 3 timeframes: prefix invariance; future perturbation; 5 wait fixtures; 10000 date checks passed",flush=True)

if __name__=="__main__":run()
