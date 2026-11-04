"""Execution and causal opening checks for phase4; no market data mutation."""
import json
import numpy as np
import pandas as pd
from overnight import overnight_replay, one_position, opening, fill_columns
from paths import OUT, native, prior, context

def fixtures():
    ts=pd.date_range('2026-09-21 09:30','2026-09-22 15:59',freq='1min',tz='America/New_York').tz_convert('UTC')
    d=pd.DataFrame(dict(t=ts.as_unit('s').asi8,open=100.,high=100.,low=100.,close=100.,spread_px=0.))
    e=pd.DataFrame([dict(decision=d.t.iat[0],day='2026-09-21',dvol=.1,vix=25.,vix_change=1.,level=99.,minute=570)])
    a=overnight_replay(d,e,1,slip=0).iloc[0]
    assert a.R==0 and a.overnights==1 and a.reason=='time'
    x=d.copy();k=1000;x.loc[k,'low']=89.
    a=overnight_replay(x,e,1,slip=0).iloc[0]
    assert a.R==-1 and a.reason=='stop' and a.overnights==1
    x=d.drop(index=range(800,1000)).reset_index(drop=True);x.loc[800,['open','low']]=[80.,79.]
    a=overnight_replay(x,e,1,slip=0).iloc[0]
    assert a.R==-2 and a.gap_stop and a.quote_gaps==1
    a=overnight_replay(d.iloc[:-10],e,1,slip=0).iloc[0]
    assert pd.isna(a.R) and a.reason=='unresolved'
    # Overnight position prevents tomorrow's opening order; boundary reuse is allowed.
    led=pd.DataFrame([dict(decision=1000,entry_t=1000,exit_t=90000,priority=1),dict(decision=86000,entry_t=86000,exit_t=91000,priority=0),dict(decision=90000,entry_t=90000,exit_t=91000,priority=0)])
    assert one_position(led).decision.tolist()==[1000,90000]
    led.loc[0,'exit_t']=1001;led.loc[1,['decision','entry_t']]=[1200,1200]
    assert one_position(led).decision.tolist()==[1000,90000]
    return 6

def main():
    n=fixtures();checked=[]
    ds=prior.load_data()
    for source,d,step in [('mt5',ds['mt5'],1)]+[(f'native{x}',native(x),x)for x in [15,30,60]]:
        full=opening(context(d,step,step),step)
        cutoff=int(pd.Timestamp('2026-03-23 09:30',tz='America/New_York').timestamp())
        prefix=opening(context(d[d.t+step*60<=cutoff].copy(),step,step),step)
        cols=['decision','day','dvol','level','vix','vix_change','stress']
        pd.testing.assert_frame_equal(full[full.decision<=cutoff][cols].reset_index(drop=True),prefix[cols].reset_index(drop=True))
        checked.append(source)
    ledgers=list(OUT.glob('overnight_*.csv'))
    for p in ledgers:
        if not any(s in p.name for s in ['UNION','DIP_NEXT','OPEN_NEXT']):continue
        a=pd.read_csv(p).sort_values('decision')
        if len(a)>1:
            assert (a.entry_t.iloc[1:].to_numpy()>=a.exit_t.iloc[:-1].to_numpy()).all(),p
            assert (a.decision.diff().dropna()>=600).all(),p
    (OUT/'overnight_verification.json').write_text(json.dumps(dict(status='PASS',fixtures=n,opening_prefix_sources=checked,ledgers=len(ledgers)),indent=2))
    print('PASS',n,'overnight fixtures;',len(checked),'opening prefixes;',len(ledgers),'ledgers',flush=True)

if __name__=='__main__':main()
