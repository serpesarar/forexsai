"""Causal prefix, fill-path, clock and one-position audits for WTI research."""
from core import *
from oil_execution import simulate_grid
from oil_daily_execution import replay
from oil_variants import calendar,stress_features,stress_events

def fixtures():
    t=int(pd.Timestamp('2026-06-01 09:00',tz='America/New_York').timestamp())
    d=prepare(pd.DataFrame({'t':t+np.arange(361)*60,'open':100.,'high':100.1,'low':99.9,'close':100.,'volume':10,'spread_px':.02}),'fixture')
    d['atr70']=.1;d['valid60']=True
    e=pd.DataFrame({'decision':[t],'day':['2026-06-01'],'dvol':[.01],'level':[99.5],'side':[1],'minute':[540],'vix':[20.],'vix_change':[1.]})
    checks=[]
    b=d.copy();b.loc[1,'low']=98;z=replay(b,e);assert z.iloc[0].reason=='stop';assert abs(z.iloc[0].R+1+.002/z.iloc[0].risk)<1e-9;checks.append('long spread+stop')
    e.side=-1;b=d.copy();b.loc[1,'high']=102;z=replay(b,e);assert z.iloc[0].reason=='stop';checks.append('short ask stop')
    e.side=1;b=d.copy();b.loc[1,['high','low']]=[102,98];z=replay(b,e,'FULL_TP1');assert z.iloc[0].ambiguous and z.iloc[0].reason=='stop';checks.append('ambiguous stop first')
    b=d.copy();b.loc[1,['open','high','low','close']]=[102,102,98,100];z=replay(b,e,'FULL_TP1');assert z.iloc[0].reason=='target';checks.append('target at open precedes later stop')
    b=d.copy();b.loc[1,'high']=102;b.loc[2,'low']=98
    h=replay(b,e,'HALF_RUNNER').iloc[0];full=replay(b,e,'FULL_TP1').iloc[0];base=replay(b,e).iloc[0]
    assert abs(h.R-(full.R+base.R)/2)<1e-9;checks.append('half payoff identity while remainder busy')
    b=d.copy();b.loc[1,['open','high','low','close']]=[97,97.1,96.9,97];assert replay(b,e).iloc[0].R<-3;checks.append('stop opening gap worse than -1R')
    # Known10:00 exit ignores excursions later in that minute.
    b=d.copy();b.loc[60,['high','low']]=[120,80];z=replay(b,e,'ALWAYS_10');assert z.iloc[0].reason=='time';checks.append('10:00 quote no future extremes')
    e['end_min']=870;b=d.iloc[::60].copy().reset_index(drop=True);b.loc[5,['high','low']]=[120,80]
    z=replay(b,e,step=60);assert z.iloc[0].reason=='native_time_proxy';checks.append('H1 14:00 proxy no future14:30 excursions')
    e=e.drop(columns='end_min');b=d.drop(index=1).reset_index(drop=True);assert replay(b,e).iloc[0].reason=='data_gap';checks.append('unknown gaps flagged')
    e.decision=t+1;assert replay(d,e).empty;checks.append('missing exact entry rejected');e.decision=t
    # Audited Nasdaq daily path implementation must give identical BASE on same numeric data/fees.
    old=cap_paths.replay(d,e,'BASE',1,slip=.002);new=replay(d,e,'BASE',1,slip=.002)
    assert np.allclose(old.R,new.R);checks.append('BASE identity against audited original daily engine')
    # Frozen oil nominal-risk scale is previous completed quote; expiry intrabar cannot hit barriers.
    d.loc[91,['high','low']]=[120,80];g=simulate_grid(d,geometry='fixed',hold_minutes=90)
    row=g[1].loc[t+60];assert abs(row.risk-1.49)<1e-12 and row.reason=='time';checks.append('fixed oil risk and causal expiry')
    return checks

def prefix():
    d=datasets(False)['cache'];cut=lab.stamp('2026-04-09')+15*3600
    tail=d[d.t<cut+86400].copy();short=tail[tail.t<cut].copy();checks=[]
    for tf in [1,3,5,15]:
        a=features(tail,tf,'prefix_full',False);b=features(short,tf,'prefix_short',False);aa=a[a.decision<=cut].reset_index(drop=True)
        cols=['close','ret1','ret5','z5','dvol','vix','ovx','extension','mtd','prev_rth_low','shock','vr15_240','channel5','chase_sell']
        pd.testing.assert_frame_equal(aa[cols],b[cols],check_exact=False,atol=1e-8,rtol=1e-8)
        for spec in old2.definitions():
            at,sd=old2.detect(aa,spec,tf);bt,bsd=old2.detect(b,spec,tf);assert np.array_equal(at,bt)and np.array_equal(sd,bsd)
        ca=cap_context(tail,tf);cb=cap_context(short,tf);ca=ca[ca.decision<=cut].reset_index(drop=True)
        for rule in cap_paths.RULES:assert np.array_equal(cap_paths.detect(ca,rule).decision,cap_paths.detect(cb,rule).decision)
        fa=stress_features(tail,tf);fb=stress_features(short,tf);fa=fa[fa.decision<=cut].reset_index(drop=True)
        for fam,vs in [('O4',['BASE','OVX','OVX_TP1','OVX_HALF']),('O5',['LONG','SHORT','BOTH','CONTINUE'])]:
            for v in vs:assert np.array_equal(stress_events(fa,fam,v).decision,stress_events(fb,fam,v).decision)
        checks.append({'tf':tf,'signal_definitions':540,'macro_and_daily_prefix':True})
    return checks

def clock():
    ds=datasets()
    if 'direct'not in ds:return {'status':'NOT_AVAILABLE'}
    c,dr=ds['cache'],ds['direct'];res=[]
    for off in [-3600,0,3600]:
        a=c[['t','close']].merge(dr[['t','close']].assign(t=lambda x:x.t+off),on='t',suffixes=('_cache','_direct'))
        a['day']=pd.to_datetime(a.t,unit='s',utc=True).dt.date
        diff=a.close_direct-a.close_cache;r=diff-diff.groupby(a.day).transform('median')
        dc=a.groupby('day').close_cache.diff();dd=a.groupby('day').close_direct.diff();cont=a.t.diff().eq(60)
        res.append({'offset_extra':off,'n':len(a),'demeaned_MAD':float(r.abs().median()),'movement_corr':float(dc[cont].corr(dd[cont])),'median_basis':float(diff.median())})
    winner=min(res,key=lambda x:x['demeaned_MAD']);assert winner['offset_extra']==0 and winner['demeaned_MAD']<.02
    assert min(x['demeaned_MAD']for x in res if x['offset_extra']!=0)>10*winner['demeaned_MAD']
    a=c[['t','close']].merge(dr[['t','close']],on='t',suffixes=('_cache','_direct'));a['basis']=a.close_direct-a.close_cache
    jumps=a.t.diff().eq(60)&a.basis.diff().abs().gt(.1)
    a.assign(basis_jump=jumps).to_csv(OUT/'price_basis_overlap.csv',index=False)
    return {'status':'PASS_CLOCK_ONLY','sources_kept_separate':True,'tested':res,'price_integrity':'CACHE_MIXED_QUOTE_BASES','basis_jumps_over_10c':int(jumps.sum()),'first_jump_utc':str(pd.to_datetime(a.loc[jumps,'t'].min(),unit='s',utc=True)),'identical_closes':int(a.basis.abs().lt(1e-5).sum()),'overlap':len(a)}

def ledgers():
    count=0;events=0
    for p in list(OUT.glob('micro_*.csv'))+list(OUT.glob('oil_*.csv'))+list(OUT.glob('daily_*.csv'))+list(OUT.glob('capital_*.csv'))+list(OUT.glob('diagnostic_*.csv')):
        a=pd.read_csv(p)
        if a.empty:continue
        a=a.sort_values('decision');assert (a.entry_t.to_numpy()[1:]>=a.exit_t.to_numpy()[:-1]).all(),p.name
        assert (a.decision.diff().dropna()>=600).all(),p.name
        count+=1;events+=len(a)
    return {'ledgers':count,'event_rows_not_independent':events,'one_position':True,'cooldown_seconds':600}

def main():
    x={'status':'PASS','fixtures':fixtures(),'prefix':prefix(),'clock':clock(),'ledgers':ledgers(),
       'scope':'offline candle research; recorded bar spread is not historical actual fill spread'}
    lab.save_json(OUT/'verification.json',x);print(json.dumps(x,indent=2))
if __name__=='__main__':main()
