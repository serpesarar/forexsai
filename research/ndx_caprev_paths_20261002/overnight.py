"""Audit the attached v2 opening/overnight combination under one total position."""
from __future__ import annotations
import hashlib
import json
import numpy as np
import pandas as pd
from paths import HERE, OUT, prior, lab, native, context, detect, replay, macro, metrics, M1_PERIODS, LONG_PERIODS

RULES = ['OPEN_SAME','DIP_SAME','DIP_NEXT','OPEN_NEXT','UNION_SAME','UNION_MIXED']

def opening(f, step):
    # At the bar open only previous-day features are used; never the opening bar close.
    om = 540 if step == 60 else 570
    mask = (f.minute == om) & (f.weekday < 4) & f.stress & (f.vix >= 18.4) & (f.dvol > 0) & f.level.notna()
    e = f[mask].copy()
    e['minute'] = om
    return e.groupby('day', sort=False).head(1)

def overnight_replay(d, ev, step, spread_mult=1., slip=.2):
    t = d.t.to_numpy()
    op, low, close = [d[c].to_numpy() for c in ['open','low','close']]
    if 'native' in d:
        ask = op * (1+.00006*spread_mult)
        bidop, bidlow, bidclose = [x*(1-.00006*spread_mult) for x in [op,low,close]]
    else:
        sp = d.spread_px.to_numpy()
        ask = (d.ask_open.to_numpy() if 'ask_open' in d else op+sp)+(spread_mult-1)*sp
        bidop, bidlow, bidclose = op, low, close
    days = macro().NDXCASH_close.dropna().index.strftime('%Y-%m-%d').to_numpy()
    rows=[]
    for e in ev.itertuples():
        i = int(np.searchsorted(t,e.decision))
        if i >= len(t) or t[i] != e.decision: continue
        nxt = int(np.searchsorted(days,e.day,side='right'))
        if nxt >= len(days): continue
        cutoff = int(pd.Timestamp(days[nxt]+' 16:00',tz='America/New_York').timestamp())
        entry = ask[i]+slip; risk = entry*e.dvol; stop=entry-risk
        last = int(np.searchsorted(t+step*60,cutoff,side='right')-1)
        # Missing terminal session is unresolved rather than fabricated as a known loss/win.
        terminal_ok = last >= i and t[last]+step*60 == cutoff
        gap_count=0; max_gap=0; exitpx=None; reason='unresolved'; exit_t=cutoff
        stopgap=False
        for k in range(i,min(last+1,len(t))):
            gap = int(t[k]-t[k-1]-step*60) if k>i else 0
            if gap>0: gap_count+=1; max_gap=max(max_gap,gap)
            if bidop[k] <= stop:
                exitpx=bidop[k]-slip; reason='gap_stop' if gap>0 else 'stop'; stopgap=gap>0
                exit_t=int(t[k])+step*60;break
            if bidlow[k] <= stop:
                exitpx=stop-slip;reason='stop';exit_t=int(t[k])+step*60;break
        if exitpx is None and terminal_ok:
            exitpx=bidclose[last]-slip;reason='time';exit_t=cutoff
        endday = pd.Timestamp(exit_t,unit='s',tz='UTC').tz_convert('America/New_York').date()
        nights=max(0,(endday-pd.Timestamp(e.day).date()).days)
        rows.append(dict(decision=e.decision,entry_t=e.decision,exit_t=exit_t,entry=entry,exit=exitpx,risk=risk,
                         R=(exitpx-entry)/risk if exitpx is not None else np.nan,points=exitpx-entry if exitpx is not None else np.nan,
                         reason=reason,day=e.day,side=1,candidate='NEXT',vix=e.vix,vix_change=e.vix_change,
                         level=e.level,entry_minute=e.minute,overnights=nights,quote_gaps=gap_count,max_gap_seconds=max_gap,
                         gap_stop=stopgap,terminal_complete=terminal_ok))
    return pd.DataFrame(rows)

def one_position(a):
    a=a.sort_values(['decision','priority'],kind='stable')
    accepted=[]; busy=-1; previous=-1e15
    for r in a.itertuples():
        if r.entry_t < busy or r.decision-previous < 600: continue
        accepted.append(r.Index);busy=r.exit_t;previous=r.decision
    return a.loc[accepted].copy().sort_values('decision').reset_index(drop=True)

def fill_columns(a, candidate):
    a=a.copy();a['candidate']=candidate
    if 'ambiguous' not in a:a['ambiguous']=False
    if 'overnights' not in a:a['overnights']=0
    if 'quote_gaps' not in a:a['quote_gaps']=a.reason.eq('data_gap').astype(int)
    if 'gap_stop' not in a:a['gap_stop']=False
    a['priority']=0 if candidate.startswith('OPEN') else 1
    return a

def summary(a,b):
    good=a[a.R.notna()].copy();base=b[b.R.notna()].copy()
    if len(good)==0:return {'n':0,'unresolved':len(a)}
    return {**metrics(good,base),'unique_days':int(good.day.nunique()),'unresolved':int(a.R.isna().sum()),
            'overnights':int(good.overnights.sum()),'gap_trades':int(good.quote_gaps.gt(0).sum()),
            'gap_stops':int(good.gap_stop.sum()),'max_active_legs':1,
            'funding_break_even_bp_per_night':float(good.R.sum()/((good.entry/good.risk)*good.overnights).sum()*1e4)
                if good.overnights.sum()>0 else None}

def main():
    snapshot=HERE/'ATTACHED_V2_SNAPSHOT.md'
    if not snapshot.exists():snapshot.write_bytes((HERE.parent/'ndx_gate_forge/NIHAI_RAPOR.md').read_bytes())
    ds=prior.load_data();sources=[(s,d,1) for s,d in ds.items()]+[(f'native{tf}',native(tf),tf)for tf in [15,30,60]]
    result={'configurations':RULES,'sources':{},'evaluation_cells':0,'protocol_sha256':hashlib.sha256((HERE/'PROTOCOL_OVERNIGHT.md').read_bytes()).hexdigest()}
    m1frames={}
    for source,d,step in sources:
        f=context(d,step,step);dip=detect(f,'BASE');op=opening(f,step)
        periods=LONG_PERIODS if step>1 else {k:v for k,v in M1_PERIODS.items()if k.startswith('D25')==(source=='duka')}
        sr={};frames={}
        for case,kw in [('base',{}),('spread3',{'spread_mult':3}),('slip1',{'slip':1}),('funding5bp',{})]:
            legs={
                'OPEN_SAME':fill_columns(replay(d,op,'BASE',step,**kw),'OPEN_SAME'),
                'DIP_SAME':fill_columns(replay(d,dip,'BASE',step,**kw),'DIP_SAME'),
                'DIP_NEXT':fill_columns(overnight_replay(d,dip,step,**kw),'DIP_NEXT'),
                'OPEN_NEXT':fill_columns(overnight_replay(d,op,step,**kw),'OPEN_NEXT')}
            if case=='funding5bp':
                for a in legs.values():a['R']-=.0005*a.entry/a.risk*a.overnights
            legs['UNION_SAME']=one_position(pd.concat([legs['OPEN_SAME'],legs['DIP_SAME']],ignore_index=True))
            legs['UNION_MIXED']=one_position(pd.concat([legs['OPEN_SAME'],legs['DIP_NEXT']],ignore_index=True))
            for rule,a in legs.items():
                if rule in ['DIP_NEXT','OPEN_NEXT']:a=one_position(a)
                # Crop only predeclared cohorts; exclude outcomes crossing each boundary.
                chunks=[]
                for p,(start,end)in periods.items():
                    z=a[(a.decision>=lab.stamp(start))&(a.exit_t<lab.stamp(end))].copy();z['period']=p;chunks.append(z)
                    sr[f'{case}/{rule}/{p}']=summary(z,legs['DIP_SAME'][(legs['DIP_SAME'].decision>=lab.stamp(start))&(legs['DIP_SAME'].exit_t<lab.stamp(end))])
                    result['evaluation_cells']+=1
                full=pd.concat(chunks,ignore_index=True).sort_values('decision')
                full.to_csv(OUT/f'overnight_{source}_{case}_{rule}.csv',index=False)
                frames[(case,rule)]=full
            dual=legs['OPEN_SAME'].set_index('day').R.add(legs['DIP_NEXT'].set_index('day').R,fill_value=0)
            sr[f'{case}/raw_mixed_sum']={'unique_days':len(dual),'sum_R':float(dual.sum()),'mean_R':float(dual.mean()),
                                       'equal_half_risk_mean_R':float(.5*dual.mean()),'may_overlap':True}
        for case in ['base','spread3','slip1','funding5bp']:
            for rule in RULES:sr[f'{case}/{rule}/aggregate']=summary(frames[(case,rule)],frames[(case,'DIP_SAME')])
        result['sources'][source]={'rows':len(d),'opening_minute':540 if step==60 else 570,'results':sr}
        if step==1:
            for key,a in frames.items():m1frames.setdefault(key,[]).append(a)
        print(source,'overnight audit done',flush=True)
    result['M1']={f'{case}/{rule}':summary(pd.concat(v,ignore_index=True).sort_values('decision'),pd.concat(m1frames[(case,'DIP_SAME')],ignore_index=True))for(case,rule),v in m1frames.items()}
    lab.save_json(OUT/'overnight.json',result)
    print('cells',result['evaluation_cells'],flush=True)

if __name__=='__main__':main()
