"""Reuse frozen Nasdaq signal definitions, with explicit oil units and own macro."""
import sys,importlib.util,json
from pathlib import Path
import numpy as np
import pandas as pd
from pull import HERE,ROOT,DATA,OUT
sys.path.insert(0,str(ROOT/'research/ndx_mechanism_round2_20260930'))
import data as olddata
import experiment as mechanism
lab=olddata.lab;old2=olddata.old2

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
synth=module('oil_ndx_synthesis_adapter',ROOT/'research/ndx_synthesis_20261002/run.py')
sys.path.insert(0,str(ROOT/'research/ndx_caprev_paths_20261002'))
import paths as cap_paths
import overnight as cap_overnight

PERIODS={'DISC_A':('2026-02-11','2026-04-01'),'DISC_B':('2026-04-01','2026-05-16'),
         'VALID_A':('2026-05-20','2026-07-01'),'VALID_B':('2026-07-01','2026-08-29'),
         'FINAL_A':('2026-09-01','2026-09-16'),'FINAL_B':('2026-09-16','2026-10-02')}
LONG_PERIODS={'L16_20':('2016-01-01','2021-01-01'),'L21_23':('2021-01-01','2024-01-01'),
              'L24_25':('2024-01-01','2026-01-01'),'L26_DISC':('2026-01-01','2026-05-16'),
              'L26_VALID':('2026-05-20','2026-08-29'),'L26_FINAL':('2026-09-01','2026-10-02')}
lab.PERIODS.update(PERIODS);synth.PERIODS=PERIODS

def prepare(d,source,step=1):
    d=d.copy().sort_values('t').drop_duplicates('t').reset_index(drop=True)
    d=d[d.t<lab.stamp('2026-10-02')].copy().reset_index(drop=True)
    d['ts']=pd.to_datetime(d.t,unit='s',utc=True)
    d['source']=source;d['atr70']=lab.atr(d,max(2,70//step));d['atr14']=lab.atr(d,max(2,14//step))
    ny=d.ts.dt.tz_convert('America/New_York')
    d['ny_min'],d['weekday'],d['day']=ny.dt.hour*60+ny.dt.minute,ny.dt.weekday,ny.dt.tz_localize(None).dt.strftime('%Y-%m-%d')
    d['valid60']=d.t.diff().eq(step*60).rolling(max(1,60//step)).sum().eq(max(1,60//step))
    return d

def datasets(include_direct=True):
    x={'cache':prepare(pd.read_csv(DATA/'clean_1m.csv'),'cache_USOIL')}
    if include_direct and (DATA/'mt5_1m.csv').exists():x['direct']=prepare(pd.read_csv(DATA/'mt5_1m.csv'),'MT5_SpotCrude')
    if (DATA/'duka_2025.csv').exists():x['duka']=prepare(pd.read_csv(DATA/'duka_2025.csv'),'Dukascopy_LIGHT')
    assert x['cache'].valid60.sum()>10000,'Rolling continuity runtime failure'
    return x

def native(step):
    tf={5:'5m',15:'15m',30:'30m',60:'1h'}[step]
    z=prepare(pd.read_csv(DATA/f'clean_{tf}.csv'),'native_'+tf,step)
    return z

def own_daily(d,cutoff=960,step=1):
    z=d.copy();ny=(z.ts+pd.Timedelta(minutes=step)).dt.tz_convert('America/New_York')
    z['endmin']=ny.dt.hour*60+ny.dt.minute;z['date']=ny.dt.tz_localize(None).dt.normalize()
    return z[z.endmin==cutoff].groupby('date').close.last()

def macro_for(d=None,step=1,cutoff=960):
    m=pd.read_csv(DATA/'macro_daily.csv',parse_dates=['date']).set_index('date').sort_index()
    if d is not None and d.source.iat[0]!='cache_USOIL' and not d.source.iat[0].startswith('native'):
        # Separate quote bases never splice. Direct history has its own warmup limitation.
        c=own_daily(d,cutoff,step);m=m.drop(columns=['OIL_close']);m=m.join(c.rename('OIL_close'),how='outer')
    elif cutoff!=960:m['OIL_close']=own_daily(d,cutoff,step)
    return m

def macro_map(f,m):
    c=m.OIL_close.dropna().sort_index();dates=pd.to_datetime(f.day).to_numpy()
    ix=np.searchsorted(c.index.to_numpy(),dates,side='left')-1;j=np.maximum(ix,0)
    ok=(ix>=0)&((dates-c.index.to_numpy()[j])/np.timedelta64(1,'D')<=5)
    ret=c.pct_change();std=ret.rolling(20).std()
    month=c.index.to_period('M');firstprev=c.groupby(month).transform('first')
    for key,val in {'ret1':ret,'ret5':c.pct_change(5),'dvol':std,'z5':c.pct_change(5)/(std*np.sqrt(5)),
                    'extension':c/c.rolling(200).mean()-1,'mtd':c/firstprev-1}.items():f[key]=np.where(ok,val.to_numpy()[j],np.nan)
    f['previous_day']=np.where(ok,c.index.strftime('%Y-%m-%d').to_numpy()[j],None)
    for name in ['VIX','OVX','DXY']:
        v=m[name+'_close'].dropna().sort_index();vi=np.searchsorted(v.index.to_numpy(),dates,side='left')-1;k=np.maximum(vi,0)
        good=(vi>=1)&((dates-v.index.to_numpy()[k])/np.timedelta64(1,'D')<=5)
        for suffix,vals in [('',v),('_change',v.diff()),('_pct',v.pct_change())]:f[name.lower()+suffix]=np.where(good,vals.to_numpy()[k],np.nan)
    f['stress']=(f.ret1<=-.015)|(f.ret5<=-.04)
    return f

def features(d,tf,source,cache=True):
    p=OUT/f'features_{source}_{tf}.pkl'
    if cache and p.exists():return pd.read_pickle(p)
    f=olddata.context(d,tf) # Imported macro values below are ALWAYS replaced with oil.
    f=macro_map(f,macro_for(d))
    rth=d[d.ny_min.between(570,959)].groupby('day').agg(lo=('low','min'),n=('t','size'))
    rth=rth[rth.n==390];f['prev_rth_low']=f.previous_day.map(rth.lo)
    # Tick-volume seasonality must be feed specific; no cache/direct volume pooling.
    v=d.set_index('ts').resample('5min').agg(volume=('volume','sum'),n=('t','size'));v=v[v.n==5].reset_index()
    v['avail']=v.ts.dt.as_unit('s').astype('int64')+300
    ny=v.ts.dt.tz_convert('America/New_York');v['slot']=ny.dt.hour*60+ny.dt.minute
    v['raw_ratio']=v.volume/v.volume.shift().rolling(20).mean()
    v['season_ratio']=v.volume/v.groupby('slot').volume.transform(lambda s:s.shift().rolling(20,min_periods=10).median())
    j=np.searchsorted(v.avail,f.decision,side='right')-1;k=np.maximum(j,0);good=(j>=0)&(f.decision.to_numpy()-v.avail.to_numpy()[k]<300)
    for col in ['raw_ratio','season_ratio']:f[col]=np.where(good,v[col].to_numpy()[k],np.nan)
    f['shock']=(f.raw_ratio>=1.5)&(f.season_ratio>=1.5)
    ix=np.searchsorted(d.t+60,f.decision,side='right')-1
    f['low15_m1']=d.low.rolling(15).min().to_numpy()[ix]
    vr15=d.close.diff(15).rolling(240).var()/(15*d.close.diff().rolling(240).var().replace(0,np.nan))
    f['vr15_240']=vr15.to_numpy()[ix]
    # Closed M5 linear residual channel, fixed50 bars, same as CHASE audit.
    v5=d.set_index('ts').resample('5min').agg(close=('close','last'),n=('t','size'));v5=v5[v5.n==5].reset_index()
    y=v5.close.to_numpy();n=50;sx=np.arange(n,dtype=float)
    sy=np.convolve(y,np.ones(n),'valid');sxy=np.convolve(y,sx[::-1],'valid');sy2=np.convolve(y*y,np.ones(n),'valid')
    mean=sy/n;slope=(sxy/n-sx.mean()*mean)/sx.var();var=np.maximum(sy2/n-mean*mean-slope*slope*sx.var(),0)
    chan=np.full(len(y),np.nan);chan[n-1:]=np.divide(y[n-1:]-(mean+slope*(n-1-sx.mean())),np.sqrt(var),out=np.full(len(var),np.nan),where=var>1e-12)
    avail=v5.ts.dt.as_unit('s').astype('int64').to_numpy()+300;j=np.searchsorted(avail,f.decision,side='right')-1;k=np.maximum(j,0);good=(j>=0)&(f.decision.to_numpy()-avail[k]<300)
    f['channel5']=np.where(good,chan[k],np.nan)
    f['chase_sell']=np.sum(np.vstack([f.channel5<=-1,f.m15_dir<0,f.close<f.prev_rth_low,f.stress]),axis=0)
    if cache:f.to_pickle(p)
    return f

def cap_context(d,tf,step=1):
    # Only the in-memory macro accessor is adapted; original source is unchanged.
    m=macro_for(d,step).rename(columns={'OIL_close':'NDXCASH_close'})
    before=cap_paths.macro;cap_paths.macro=lambda:m
    try:f=cap_paths.context(d,tf,step)
    finally:cap_paths.macro=before
    f=macro_map(f,macro_for(d,step));f['prev_rth_low']=f.level
    return f

def sequential(a):return mechanism.sequential(a)

def stats(a,full=False):
    z=lab.stats(a)
    if full:
        z.update(bootstrap=lab.bootstrap(a,n=4000),halves=[lab.stats(a.iloc[:len(a)//2]),lab.stats(a.iloc[len(a)//2:])],
                 drop_best5=lab.stats(a.sort_values('R').iloc[:-5].sort_values('decision'))if len(a)>5 else None)
        n=len(a);k=int((a.R>0).sum())
        den=1+3.8416/max(1,n);center=(k/max(1,n)+3.8416/(2*max(1,n)))/den
        half=1.96*np.sqrt(k/max(1,n)*(1-k/max(1,n))/max(1,n)+3.8416/(4*max(1,n)**2))/den
        z['wr_ci95']=[center-half,center+half]if n else [0,1]
    return z

def compare(a,b):return {**stats(a,True),'delta_R':float(a.R.sum()-b.R.sum()),'paired':mechanism.delta_boot(a,b)}

def periods(source):return {k:v for k,v in PERIODS.items()if not(source=='direct'and k.startswith('DISC'))}

def slice_period(a,p):
    lo,hi=map(lab.stamp,PERIODS[p]);return a[(a.decision>=lo)&(a.exit_t<hi)].sort_values('decision').reset_index(drop=True)
