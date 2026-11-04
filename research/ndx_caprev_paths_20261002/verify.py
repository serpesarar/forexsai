"""Causal feature/first-event checks and partial-close execution fixtures."""
import json
import numpy as np
import pandas as pd
from paths import OUT, prior, native, context, detect, replay, RULES


def fixture_data(step=1):
    ts=pd.date_range("2026-09-21 03:00","2026-09-21 16:00",freq=f"{step}min",tz="America/New_York").tz_convert("UTC")
    d=pd.DataFrame({"t":ts.as_unit("s").asi8,"open":100.,"high":100.,"low":100.,"close":100.,"spread_px":0.})
    e=pd.DataFrame([{"decision":d.t.iat[1],"day":"2026-09-21","dvol":.1,"vix":25.,"vix_change":-1.,"level":99.,"minute":180+step}])
    return d,e


def fixtures():
    d,e=fixture_data()
    assert replay(d,e,"BASE",slip=0).iloc[0].R==0
    x=d.copy();x.loc[2,"high"]=111.;x.loc[len(x)-1,"open"]=120.
    a=replay(x,e,"HALF_RUNNER",slip=0).iloc[0]
    assert abs(a.R-1.5)<1e-12 and a.target_done
    x.loc[3,"low"]=89.
    a=replay(x,e,"HALF_RUNNER",slip=0).iloc[0]
    assert a.R==0 and a.reason=="stop"
    assert replay(x,e,"FULL_TP1",slip=0).iloc[0].R==1
    # With an ambiguous first bar, stop is assumed to precede any target.
    x=d.copy();x.loc[2,["high","low"]]=[111.,89.]
    a=replay(x,e,"HALF_RUNNER",slip=0).iloc[0]
    assert a.R==-1 and a.ambiguous and not a.target_done
    # A target crossed at open precedes a later intrabar stop.
    x.loc[2,"open"]=112.
    a=replay(x,e,"HALF_RUNNER",slip=0).iloc[0]
    assert a.R==0 and a.target_done and not a.ambiguous
    # Gap stops fill at the worse opening price, including the surviving half.
    x=d.copy();x.loc[2,"high"]=111.;x.loc[3,["open","low"]]=[80.,79.]
    assert replay(x,e,"HALF_RUNNER",slip=0).iloc[0].R==-.5
    # Deadline reads only the close available at 10:00, not that bar's future high/close.
    ten=int(pd.Timestamp("2026-09-21 10:00",tz="America/New_York").timestamp())
    k=np.searchsorted(d.t,ten);x=d.copy();x.loc[k-1,"close"]=98.;x.loc[k,"close"]=1000.
    a=replay(x,e,"FAIL_10",slip=0).iloc[0]
    assert a.reason=="fail10" and a.exit_t==ten+60 and a.R==0
    x.loc[k-1,"close"]=100.
    assert replay(x,e,"FAIL_10",slip=0).iloc[0].reason=="time"
    # Late entry is never liquidated before its entry.
    e.decision=ten+60
    assert replay(x,e,"ALWAYS_10",slip=0).iloc[0].exit_t>e.decision.iat[0]
    e.decision=d.t.iat[1]
    gap=d.drop(index=3).reset_index(drop=True)
    assert replay(gap,e,"BASE",slip=0).iloc[0].reason=="data_gap"
    assert replay(d,e,"BASE",delay=1).iloc[0].entry_t==e.decision.iat[0]+60
    # Native spread is two separate quote adjustments, not measured real spread.
    d["native"]=True
    a=replay(d,e,"BASE",slip=0).iloc[0]
    assert abs(a.entry-100.006)<1e-10 and abs(a.exit-99.994)<1e-10
    return 13


def main():
    n=fixtures();checked=[]
    ds=prior.load_data()
    inputs=[("mt5",ds["mt5"],1,tf)for tf in[1,5,15]]
    inputs += [(f"native{tf}",native(tf),tf,tf)for tf in[15,30,60]]
    cols=["ret1","ret5","dvol","level","vix","vix_change","eligible","fresh"]
    cutoff=int(pd.Timestamp("2026-03-23T15:17Z").timestamp())
    for source,d,step,tf in inputs:
        full=context(d,tf,step)
        # Native candles are available only at start+their duration.
        partial=d[d.t+step*60<=cutoff].copy()
        p=context(partial,tf,step)
        a=full[full.decision<=cutoff]
        pd.testing.assert_frame_equal(a[cols].reset_index(drop=True),p[cols].reset_index(drop=True))
        for rule in RULES:
            af,ap=detect(full,rule),detect(p,rule)
            af=af[af.decision<=cutoff]
            pd.testing.assert_frame_equal(af[["decision"]].reset_index(drop=True),ap[["decision"]].reset_index(drop=True))
        # Actual target/stop fills in that candle are execution, not entry features.
        checked.append({"source":source,"step":step,"trigger_tf":tf})
    (OUT/"verification.json").write_text(json.dumps({"status":"PASS","fixtures":n,"prefix_inputs":checked,"rules":10},indent=2))
    print("PASS",n,"fixtures",len(checked),"prefix inputs",flush=True)

if __name__=="__main__":main()
