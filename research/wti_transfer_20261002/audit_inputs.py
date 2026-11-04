"""Clock and price-basis audit; no PnL selection before valid input clocks."""
import json,hashlib
import numpy as np
import pandas as pd
from pull import DATA,OUT

def aligned_cache(tf,minute):
    step={'5m':5,'15m':15,'30m':30,'1h':60}[tf]
    z=pd.read_parquet(DATA/f'cache_{tf}.parquet')
    z['ts']=pd.to_datetime(z.candle_time,utc=True)
    z=z[(z.ts.dt.second==0)&(z.ts.dt.microsecond==0)].sort_values('fetched_at').drop_duplicates('ts',keep='last')
    ref=minute.set_index('ts').resample(f'{step}min').agg(close=('close','last'),n=('t','size'))
    ref=ref[ref.n==step].reset_index()
    # Old bulk import dates versus recent UTC feed. Never assume one clock for all rows.
    z['cohort']=np.where(pd.to_datetime(z.fetched_at,utc=True)<pd.Timestamp('2026-07-30',tz='UTC'),'legacy','recent')
    out=[];audit={}
    for cohort,a in z.groupby('cohort'):
        scans=[];variants={}
        for mode in ['UTC','-1h','-2h','-3h','NY_PLUS7']:
            b=a.copy()
            if mode=='NY_PLUS7':
                b['ts']=(b.ts.dt.tz_localize(None)-pd.Timedelta(hours=7)).dt.tz_localize('America/New_York',ambiguous='NaT',nonexistent='NaT').dt.tz_convert('UTC')
            elif mode!='UTC':b['ts']-=pd.Timedelta(hours=int(mode[1]))
            b=b.dropna(subset=['ts']);q=b.merge(ref[['ts','close']],on='ts',suffixes=('_native','_m1'))
            if len(q)<100:continue
            diff=q.close_native-q.close_m1
            days=q.ts.dt.strftime('%Y-%m-%d')
            # Different CFD quote/roll bases are audited separately from clock alignment.
            e=(diff-diff.groupby(days).transform('median')).abs()
            scans.append(dict(mode=mode,n=len(q),median_error=float(e.median()),p90=float(e.quantile(.9)),absolute_price_error=float(diff.abs().median())))
            variants[mode]=b
        if not scans:
            audit[cohort]={'status':'NO_OVERLAP','rows':len(a)};continue
        best=min(scans,key=lambda k:k['median_error'])
        assert best['median_error']<.025 and best['p90']<.1,(tf,cohort,scans)
        out.append(variants[best['mode']]);audit[cohort]={'status':'PASS','selected':best,'scans':scans}
    a=pd.concat(out,ignore_index=True).sort_values(['ts','fetched_at']).drop_duplicates('ts',keep='last')
    a=a[a.ts<pd.Timestamp('2026-10-02',tz='UTC')]
    a=a[['ts','open','high','low','close','volume']].sort_values('ts').reset_index(drop=True)
    a['t']=a.ts.dt.as_unit('s').astype('int64');a['spread_px']=.03
    a.to_parquet(DATA/f'clean_{tf}.parquet',index=False)
    a.to_csv(DATA/f'clean_{tf}.csv',index=False)
    return audit

def main():
    raw=pd.read_parquet(DATA/'cache_1m.parquet');raw['ts']=pd.to_datetime(raw.candle_time,utc=True)
    clean=raw[(raw.ts.dt.second==0)&(raw.ts.dt.microsecond==0)].sort_values('fetched_at').drop_duplicates('ts',keep='last')
    clean=clean[clean.ts<pd.Timestamp('2026-10-02',tz='UTC')]
    # Never import the Nasdaq early-cache DST correction into oil without a price audit.
    clean=clean[['ts','open','high','low','close','volume']].sort_values('ts').reset_index(drop=True)
    clean['t']=clean.ts.dt.as_unit('s').astype('int64');clean['spread_px']=.03
    assert(clean.high>=clean[['open','close']].max(axis=1)-1e-6).all()
    assert(clean.low<=clean[['open','close']].min(axis=1)+1e-6).all()
    result={'cache_1m':{'raw':len(raw),'clean':len(clean),'first':str(clean.ts.min()),'last':str(clean.ts.max()),'spread_proxy':.03},'clocks':{}}
    for tf in ['5m','15m','30m','1h']:result['clocks'][tf]=aligned_cache(tf,clean);print('clock',tf,result['clocks'][tf],flush=True)
    clean.to_parquet(DATA/'clean_1m.parquet',index=False)
    clean.to_csv(DATA/'clean_1m.csv',index=False)
    # Bar-end16:00 synthetic CFD reference, never a futures settlement claim.
    h=pd.read_parquet(DATA/'clean_1h.parquet')
    ny=(h.ts+pd.Timedelta(hours=1)).dt.tz_convert('America/New_York')
    h['day']=ny.dt.tz_localize(None).dt.normalize();h['end_min']=ny.dt.hour*60+ny.dt.minute
    close=h[h.end_min==960].groupby('day').close.last()
    result['daily_reference']={'n':len(close),'first':str(close.index.min()),'last':str(close.index.max()),'cutoff':'16:00 NY CFD bar-close proxy','daily_return_extremes':close.pct_change().sort_values().head(5).to_dict()}
    macro=pd.DataFrame({'OIL_close':close})
    for name in ['VIX','OVX','DXY','WTI_REFERENCE']:
        z=pd.read_csv(DATA/f'macro_{name}.csv');z['date']=pd.to_datetime(z.iloc[:,0].str[:10]);macro[name+'_close']=z.set_index('date').Close
    macro.to_csv(DATA/'macro_daily.csv',index_label='date')
    # JSON timestamp-key normalization.
    result['daily_reference']['daily_return_extremes']={str(k):float(v)for k,v in result['daily_reference']['daily_return_extremes'].items()}
    (OUT/'input_audit.json').write_text(json.dumps(result,indent=2));print('PASS input audit',flush=True)

if __name__=='__main__':main()
