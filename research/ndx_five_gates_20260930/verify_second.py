"""Causality checks for the additional statistical features and exact ask fills."""
from __future__ import annotations

import numpy as np
import pandas as pd
import lab
from second_search import extra_features, detect, definitions
from transfer import duka
from verify import fixture


def main() -> None:
    d=fixture()
    # Ask is not approximated as bid OHLC + a constant median when exact ask
    # extrema exist. Spread extrema and bid extrema need not occur together.
    for a,b in [("ask_open","open"),("ask_high","high"),("ask_low","low"),("ask_close","close")]:
        d[a]=d[b]+3.
    t=int(d.t.iloc[1])
    r=lab.simulate_grid(d)[1].loc[t]
    assert abs(r.entry-1003.2)<1e-8
    d.loc[2,"ask_high"]=1060.
    r=lab.simulate_grid(d)[-1].loc[t]
    assert r.reason=="stop" and r.R < -1
    d=fixture();r=lab.simulate_grid(d,hold_minutes=15,risk_mult=2,reward_ratio=2)[1].loc[t]
    assert r.exit_ix==16 and r.risk==35.
    print("Exact ask and alternative horizon/risk checks passed",flush=True)
    d=duka()
    # Limit the check to a six-week segment; future observations are changed by
    # removing them, and all preceding values must remain byte-equivalent.
    d=d[(d.t>=lab.stamp("2025-05-01"))&(d.t<lab.stamp("2025-06-15"))].reset_index(drop=True)
    cutoff=lab.stamp("2025-06-03 14:07")
    pre=d[d.t<cutoff]
    for tf in [1,3,5]:
        full=extra_features(d,tf);prefix=extra_features(pre,tf)
        full=full[full.decision<=cutoff].reset_index(drop=True)
        prefix=prefix[prefix.decision<=cutoff].reset_index(drop=True)
        pd.testing.assert_frame_equal(full,prefix)
        for spec in definitions():
            if spec["family"] not in ["innovation_revert","variance_switch","shock_continuation"]:continue
            ta,sa=detect(full,spec,tf);tb,sb=detect(prefix,spec,tf)
            assert np.array_equal(ta,tb) and np.array_equal(sa,sb)
        print("Additional-feature prefix causality passed",tf,"minute",flush=True)


if __name__=="__main__":main()
