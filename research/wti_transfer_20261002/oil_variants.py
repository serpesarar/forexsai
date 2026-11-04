"""Twenty frozen WTI-specific derivatives; validation never rewrites definitions."""
import sys,json,hashlib
import numpy as np
import pandas as pd
from core import *
from oil_execution import simulate_grid
from oil_daily_execution import replay as daily_replay

DEFS={
 'O1':['LEGACY','ENERGY','ENERGY_5D','ENERGY_NO_EIA'],
 'O2':['BASE','SPREAD10','SPREAD20','WAIT3'],
 'O3':['BREAK5','BREAK15','FADE5','FADE15'],
 'O4':['BASE','OVX','OVX_TP1','OVX_HALF'],
 'O5':['LONG','SHORT','BOTH','CONTINUE']}

def calendar():
    dates=pd.date_range('2025-01-01','2026-10-01',freq='W-WED')
    x={t.strftime('%Y-%m-%d'):630 for t in dates}
    shifts={'2025-01-01':('2025-01-02',660),'2025-01-22':('2025-01-23',720),'2025-02-19':('2025-02-20',720),
            '2025-05-28':('2025-05-29',720),'2025-09-03':('2025-09-04',720),'2025-10-15':('2025-10-16',720),
            '2025-11-12':('2025-11-13',720),'2025-12-24':('2025-12-29',1020),
            '2026-01-21':('2026-01-22',720),'2026-02-18':('2026-02-19',720),'2026-05-27':('2026-05-28',720),
            '2026-09-09':('2026-09-10',720)}
    for old,(day,minute)in shifts.items():x.pop(old,None);x[day]=minute
    # First January2026 release not explicitly covered by the retrieved exception table.
    x.pop('2025-12-31',None);x.pop('2026-01-07',None)
    return x

def energy_features(d,tf,source):
    f=features(d,tf,source).copy()
    f['valid']=f.valid60&f.atr70.gt(0)&f.weekday.lt(5)&f.minute.between(540,840)
    release=f.day.map(calendar());f['eia_release_min']=release
    f['eia_block']=release.notna()&(f.minute>=release-15)&(f.minute<=release+15)
    return f

def event_frame(f,spec,tf):
    ts,side=old2.detect(f,spec,tf);ix=np.searchsorted(f.decision,ts)
    x=f.iloc[ix].copy();x['origin']=ts;x['side']=side;return x.reset_index(drop=True)

def micro_events(d,f,family,variant,tf):
    spec={'family':'midpoint_reclaim'if family=='O1'else 'efficient_pullback','lookback':15 if family=='O1'else 30,
          'context':'efficiency','side':'both'}
    if family=='O1'and variant=='LEGACY':
        f=f.copy();f['valid']=f.valid60&f.atr70.gt(0)&f.weekday.lt(4)&f.minute.between(180,930)
    elif family=='O1'and variant=='ENERGY':f=f.copy();f['valid']&=f.weekday.lt(4)
    x=event_frame(f,spec,tf)
    if family=='O1'and variant=='ENERGY_NO_EIA':x=x[~x.eia_block]
    if family=='O2':
        if variant.startswith('SPREAD'):
            j=np.searchsorted(d.t,x.decision);ok=(j<len(d));j=np.minimum(j,len(d)-1)
            ratio=d.spread_px.to_numpy()[j]/np.maximum(.05,8*x.atr70.to_numpy())
            x=x[ok&(ratio<=int(variant[6:])/100)]
        elif variant=='WAIT3':
            x=mechanism.delayed(d,x,3);x=x[x.band_alive&x.fair_price]
            minute=pd.to_datetime(x.decision,unit='s',utc=True).dt.tz_convert('America/New_York')
            x=x[(minute.dt.hour*60+minute.dt.minute)<=840]
    return x

def eia_events(d,f,variant):
    rows=[];wait=int(variant[-2:])if variant.endswith('15')else 5
    for day,minute in calendar().items():
        release=int(pd.Timestamp(day+' 00:00',tz='America/New_York').timestamp())+minute*60
        z=d[(d.t>=release-3600)&(d.t<release)]
        if len(z)!=60 or not(z.t.diff().dropna()==60).all():continue
        hi,lo=z.high.max(),z.low.min()
        q=f[(f.day==day)&(f.decision>=release+wait*60)&(f.decision<=release+45*60)&f.valid]
        if variant.startswith('BREAK'):
            bu=(q.close>hi)&(q.body>=.5)&(q.clv>=.5)
            se=(q.close<lo)&(q.body<=-.5)&(q.clv<=-.5)
        else:
            bu=(q.low<lo)&(q.close>lo)&(q.clv>=.4)
            se=(q.high>hi)&(q.close<hi)&(q.clv<=-.4)
        good=q[bu|se]
        if len(good):
            a=good.head(1).copy();a['side']=np.where(bu.loc[a.index],1,-1);a['origin']=a.decision;rows.append(a)
    return pd.concat(rows,ignore_index=True)if rows else f.iloc[:0].assign(side=pd.Series(dtype=int),origin=pd.Series(dtype=int))

def stress_features(d,tf,step=1):
    f=cap_context(d,tf,step)
    start,end=540,(840 if step==60 else 870)
    rth=d[d.ny_min.between(start,end-step)].groupby('day').agg(lo=('low','min'),hi=('high','max'),n=('t','size'))
    rth=rth[rth.n==(end-start)//step]
    f['energy_low']=f.previous_day.map(rth.lo);f['energy_high']=f.previous_day.map(rth.hi)
    f['normalized_down']=(f.ret1<=-f.dvol)|(f.ret5<=-np.sqrt(5)*f.dvol)
    f['normalized_up']=(f.ret1>=f.dvol)|(f.ret5>=np.sqrt(5)*f.dvol)
    ovx=macro_for(d,step).OVX_close.dropna().sort_index();med=ovx.rolling(252,min_periods=252).median()
    dates=pd.to_datetime(f.day).to_numpy();j=np.searchsorted(ovx.index.to_numpy(),dates,side='left')-1;k=np.maximum(j,0)
    f['ovx_above_median']=(j>=0)&(f.ovx>=med.to_numpy()[k])
    f['energy_valid']=f.valid60 if 'valid60'in f else f.valid
    f['energy_valid']&=f.weekday.lt(4)&f.minute.between(540+tf,840)&f.dvol.gt(0)
    f['end_min']=870
    return f

def stress_events(f,family,variant):
    ok=f.energy_valid
    if family=='O4':
        mask=ok&f.normalized_down&(f.close<f.energy_low)
        if variant!='BASE':mask&=f.ovx_above_median
        e=f[mask].groupby('day',sort=False).head(1).copy();e['side']=1;e['level']=e.energy_low;return e
    ok&=f.ovx_above_median
    bu=ok&f.normalized_down&(f.close<f.energy_low)
    se=ok&f.normalized_up&(f.close>f.energy_high)
    if variant=='LONG':se&=False
    elif variant=='SHORT':bu&=False
    e=f[bu|se].groupby('day',sort=False).head(1).copy()
    e['side']=np.where(bu.loc[e.index],1,-1)
    if variant=='CONTINUE':e['side']*=-1
    e['level']=np.where(e.side>0,e.energy_low,e.energy_high)
    return e

def summarize(a,source):
    parts=[slice_period(a,p).assign(period=p)for p in periods(source)]
    allrows=pd.concat(parts,ignore_index=True).sort_values('decision')
    return allrows,{'aggregate':stats(allrows,True),'periods':{p:stats(z,True)for p,z in zip(periods(source),parts)}}

def main():
    result={'definitions':DEFS,'configurations':20,'protocol_sha256':hashlib.sha256((HERE/'PROTOCOL_OIL_VARIANTS.md').read_bytes()).hexdigest(),'evaluation_cells':0,'results':{}}
    for source,d in datasets().items():
        for tf in [1,3,5,15]:
            f=energy_features(d,tf,source);sf=stress_features(d,tf)
            for case,kw in (dict(base={},spread3={'spread_mult':3},slip1={'slip':.01},delay1={'delay':1}).items()if tf==1 else [('base',{})]):
                legacy=simulate_grid(d,risk_mult=8,hold_minutes=240,reward_ratio=2,**kw)
                energy=simulate_grid(d,risk_mult=8,hold_minutes=240,reward_ratio=2,window_start=540,window_end=840,deadline=870,allowed_weekdays=5,**kw)
                eia=simulate_grid(d,risk_mult=5,hold_minutes=90,reward_ratio=1.5,window_start=540,window_end=840,deadline=870,allowed_weekdays=5,**kw)
                for family,variants in DEFS.items():
                    for variant in variants:
                        if family in ['O1','O2','O3']:
                            ev=eia_events(d,f,variant)if family=='O3'else micro_events(d,f,family,variant,tf)
                            g=eia if family=='O3'else legacy if family=='O1'and variant=='LEGACY'else energy
                            chunks=[lab.replay(ev.decision.to_numpy(),ev.side.to_numpy(),g,p)for p in periods(source)]
                            a=pd.concat(chunks,ignore_index=True).sort_values('decision')
                        else:
                            ev=stress_events(sf,family,variant)
                            r=variant if family=='O4'else'MIRROR';a=sequential(daily_replay(d,ev,r,**kw))
                        a,info=summarize(a,source)
                        name=family+'_'+variant;key=f'{source}/{tf}/{case}/{name}'
                        a.to_csv(OUT/f'oil_{source}_{tf}_{case}_{name}.csv',index=False)
                        result['results'][key]=info;result['evaluation_cells']+=len(info['periods'])
                print('oil derivatives',source,tf,case,flush=True)
                lab.save_json(OUT/'oil_variants.json',result)
    for step in [15,30,60]:
        d=native(step);f=stress_features(d,step,step)
        for family in ['O4','O5']:
            for variant in DEFS[family]:
                ev=stress_events(f,family,variant);a=sequential(daily_replay(d,ev,variant if family=='O4'else'MIRROR',step))
                key=f'native{step}/{step}/base/{family}_{variant}';by={};parts=[]
                for p,(lo,hi)in LONG_PERIODS.items():
                    z=a[(a.decision>=lab.stamp(lo))&(a.exit_t<lab.stamp(hi))].copy();z['period']=p;parts.append(z);by[p]=stats(z,True)
                a=pd.concat(parts,ignore_index=True).sort_values('decision');a.to_csv(OUT/f'oil_native{step}_{step}_base_{family}_{variant}.csv',index=False)
                result['results'][key]={'aggregate':stats(a,True),'periods':by};result['evaluation_cells']+=len(by)
        print('oil native stress',step,flush=True)
    lab.save_json(OUT/'oil_variants.json',result);print('WTI VARIANTS DONE',result['evaluation_cells'],flush=True)

if __name__=='__main__':main()
