"""Finite loss-veto rules, discovery-only selection and chronological validation."""
from features import *
import itertools
sys.path.insert(0,str(ROOT/'research/wti_transfer_20261002'));from oil_variants import calendar
PERIODS={'DISC':('2026-06-29','2026-08-01'),'VALID':('2026-08-01','2026-09-01'),'FINAL':('2026-09-01','2026-10-02')}

def singles(a):
    side=a.side;wave=a.wave_valid;dir15=a.m15_dir*side;dir60=a.m60_dir*side;dir5=a.m5_dir*side
    rr=a.initial_risk_verified if 'initial_risk_verified'in a else a.risk_cash.gt(0)
    c={
    'T_M15':dir15<0,'T_H1':dir60<0,'T_BOTH':(dir15<0)&(dir60<0),'T_M5M15':(dir5<0)&(dir15<0),
    'C_STRETCH1':wave&(a.m5_stretch_dir>=1)&(a.drift60_dir>=1)&(a.pos_dir>=.8),
    'C_STRETCH2':wave&(a.m5_stretch_dir>=2)&(a.drift60_dir>=1)&(a.pos_dir>=.8),
    'C_EXHAUST':wave&(a.drift60_dir>=1)&(a.m1_body*side<=-.4)&(a.m1_clv*side<=-.4),
    'C_BREAK_FAIL':np.where(side>0,a.m1_break_fail_buy.eq(1),a.m1_break_fail_sell.eq(1)),
    'V_QUIET06':a.m5_vol_ratio<.6,'V_QUIET08':a.m5_vol_ratio<.8,'V_SHOCK2':a.m5_vol_ratio>=2,
    'V_SHOCK3':a.m5_vol_ratio>=3,'V_SHOCK_OPPOSE':(a.m5_vol_ratio>=2)&(a.m5_body*side<0),
    'V_SEASON_SHOCK':(a.m5_vol_ratio>=1.5)&(a.m5_season_vol>=1.5),
    'Q_CHOP15':wave&(a.m1_er60<.15)&(a.m1_vr15<.8),'Q_CHOP20':wave&(a.m1_er60<.2)&(a.m1_vr15<.8),
    'Q_ADX15':a.m5_adx<15,'Q_ADX20':a.m5_adx<20,
    'G_RR07':rr&(a.rr0<.7),'G_RR1':rr&(a.rr0<1),'G_SL05':rr&(a.sl_atr5<.5),'G_SL1':rr&(a.sl_atr5<1),
    'G_FRICTION10':rr&(a.spread_risk>.1),'G_FRICTION20':rr&(a.spread_risk>.2),
    'I_MACD_BOTH':(a.m5_macd*side<0)&(a.m15_macd*side<0),
    'I_RSI70':np.where(side>0,a.m5_rsi>70,a.m5_rsi<30),
    'I_VWAP':(a.m1_close-a.m1_vwap)*side/a.m5_atr<-1,
    'I_CROSS':np.where(side>0,a.m1_cross_buy.eq(1),a.m1_cross_sell.eq(1)),
    'S_OFF_ENERGY':(a.ny_min<540)|(a.ny_min>870),
    'S_BUY_OLD':(side>0)&(a.utc_hour<13),
    }
    release=a.day.map(calendar());delta=a.ny_min-release
    c['S_EIA15']=release.notna()&delta.abs().le(15);c['S_EIA30']=release.notna()&delta.abs().le(30)
    return {k:pd.Series(v,index=a.index).fillna(False)&a.feature_valid for k,v in c.items()}

def definitions():
    sample=pd.read_csv(OUT/'oil_decisions.csv').iloc[:0]
    keys=list(singles(sample));pairs=[(a,b)for a,b in itertools.combinations(keys,2)if a[0]!=b[0]]
    return [{'id':k,'terms':[k]}for k in keys]+[{'id':a+'&'+b,'terms':[a,b]}for a,b in pairs]

def masks(a,defs):
    base=singles(a);return {s['id']:np.logical_and.reduce([base[k].to_numpy()for k in s['terms']])for s in defs}

def period(a,name):
    lo,hi=PERIODS[name];l=int(pd.Timestamp(lo,tz='UTC').timestamp());h=int(pd.Timestamp(hi,tz='UTC').timestamp())
    return a[(a.entry_t>=l)&(a.exit_t<h)].copy().reset_index(drop=True)

def boot_delta(a,mask,n=5000):
    v=a.assign(saved=np.where(mask,-a.net,0)).groupby('day').saved.sum().to_numpy();rng=np.random.default_rng(211)
    if not len(v):return {'n_days':0,'p_positive':0.,'ci95_total':[0.,0.]}
    total=v[rng.integers(0,len(v),size=(n,len(v)))].sum(axis=1)
    return {'n_days':len(v),'p_positive':float((total>0).mean()),'ci95_total':np.quantile(total,[.025,.975]).tolist()}

def measure(a,mask,bootstrap=True):
    blocked=a[mask];kept=a[~mask];los=blocked[blocked.net<0];wins=blocked[blocked.net>0];base=a.net.sum();delta=-blocked.net.sum()
    n=len(a);w=int((a.net>0).sum());bw=int((wins.net>0).sum());bl=int((los.net<0).sum())
    x={'n':n,'base_net':float(base),'blocked_n':len(blocked),'blocked_losses':bl,'blocked_winners':bw,'avoided_loss':float(-los.net.sum()),'foregone_win':float(wins.net.sum()),'blocked_net':float(blocked.net.sum()),'delta_net':float(delta),'kept_n':len(kept),'kept_net':float(kept.net.sum()),'winner_retention':float((w-bw)/w)if w else None,'loss_capture':float(bl/(a.net<0).sum())if(a.net<0).any()else None,'kept_wr':float((kept.net>0).mean())if len(kept)else None}
    if bootstrap:x['bootstrap']=boot_delta(a,mask)
    # A subgroup may have no confirmed initial cash risk; don't turn NaN into zero.
    known=a[a.risk_cash.gt(0)];kb=blocked[blocked.risk_cash.gt(0)];x['verified_R_n']=len(known);x['delta_R_verified']=-float(kb.R_actual.sum());x['R_unknown_blocked']=len(blocked)-len(kb)
    return x

def discovery():
    a=period(pd.read_csv(OUT/'oil_decisions.csv'),'DISC');defs=definitions();m=masks(a,defs);rows=[]
    half=len(a)//2
    for spec in defs:
        mask=m[spec['id']];info=measure(a,mask);halves=[measure(a.iloc[:half],mask[:half],False),measure(a.iloc[half:],mask[half:],False)]
        enough=info['blocked_n']>=12 and all(x['blocked_n']>=4 for x in halves)
        qualifies=enough and info['winner_retention']>=.65 and all(x['delta_net']>0 for x in halves)
        rows.append({'spec':spec,'metrics':info,'halves':halves,'qualifies_discovery':qualifies,'rank':min(x['delta_net']for x in halves)})
    ranked=sorted([x for x in rows if x['qualifies_discovery']],key=lambda x:x['rank'],reverse=True);chosen=[];seen=set()
    for x in ranked:
        signature=tuple(a.loc[m[x['spec']['id']],'decision_id'])
        if signature in seen:continue
        seen.add(signature);chosen.append(x)
        if len(chosen)==5:break
    frozen={'definitions':defs,'all_configurations':len(defs),'singles':len(singles(a)),'selected':[x['spec']for x in chosen],'discovery_split':PERIODS['DISC'],'selection':'blocked>=12, each half>=4; retain>=65% winners; saved net>0 each half; rank min-half saved cash, unique masks; no forward outcome ranking','discovery_only_rows':rows}
    save(OUT/'frozen_veto.json',frozen);print('FROZEN',len(defs),'selected',[x['spec']['id']for x in chosen],flush=True)

def controls(a,mask):
    # Shuffle veto labels within side/scope/UTC-hour, preserving each stratum's blocked count.
    groups=a.groupby(['side','family','utc_hour']).indices;rng=np.random.default_rng(212);draw=[]
    for _ in range(3000):
        mb=np.zeros(len(a),bool)
        for ix in groups.values():
            n=int(mask[ix].sum())
            if n:mb[rng.choice(ix,n,replace=False)]=True
        draw.append(float(-a.net.to_numpy()[mb].sum()))
    v=np.asarray(draw);obs=float(-a.net.to_numpy()[mask].sum())
    return {'matched_random_mean_delta':float(v.mean()),'ci95_random_delta':np.quantile(v,[.025,.975]).tolist(),'observed_delta':obs,'p_random_ge_observed':float((1+(v>=obs).sum())/(len(v)+1))}

def validate():
    allrows=pd.read_csv(OUT/'oil_decisions.csv');f=json.loads((OUT/'frozen_veto.json').read_text());result={'configurations_searched':f['all_configurations'],'selected':f['selected'],'periods':{},'rules':{}}
    # Evaluate every frozen veto/control; no new final-period winner is selected.
    for p in PERIODS:
        a=period(allrows,p);mm=masks(a,f['definitions']);result['periods'][p]={'decisions':len(a),'positions':int(a.positions.sum()),'net':float(a.net.sum()),'losses':int((a.net<0).sum()),'feature_valid':int(a.feature_valid.sum())}
        for spec in f['definitions']:
            key=spec['id'];mask=mm[key];info=measure(a,mask,key in [x['id']for x in f['selected']]);result['rules'].setdefault(key,{})[p]=info
            if key in [x['id']for x in f['selected']]:
                info['matched_random']=controls(a,mask);info['by_side']={str(s):measure(z,mask[z.index],False)for s,z in a.groupby('side')};info['by_scope']={str(s):measure(z,mask[z.index],False)for s,z in a.groupby('family')}
                b=a.copy();b['blocked']=mask;b.to_csv(OUT/f'veto_{p}_{key.replace("&","__")}.csv',index=False)
        print('veto validation',p,len(a),flush=True)
    # Union of frozen shortlisted rules is predeclared as a control, not a new selected optimizer.
    for p in PERIODS:
        a=period(allrows,p);mm=masks(a,f['selected']);mask=np.logical_or.reduce(list(mm.values()))if mm else np.zeros(len(a),bool)
        result['rules'].setdefault('UNION_SELECTED',{})[p]=measure(a,mask)
    result['evaluation_cells']=len(f['definitions'])*len(PERIODS)+3;save(OUT/'veto_validation.json',result)
    print('VETO DONE',result['evaluation_cells'],flush=True)
if __name__=='__main__':{'discover':discovery,'validate':validate}[sys.argv[1]]()
