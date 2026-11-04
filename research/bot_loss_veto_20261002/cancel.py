"""Calibrated original-geometry replay and closed-bar post-entry invalidation."""
from features import *
from veto import PERIODS,period,boot_delta
RULES=['BASE','P1_M5_OPPOSE','P2_BREAK_FAIL','P3_EMA_TWO','P4_VOL_OPPOSE','P5_TIME15','P6_TIME30','P7_ADVERSE5','P8_ADVERSE10','TIME5','TIME10','TIME15','TIME30']

def replay(d,f,r,rule):
    if not r.initial_risk_verified or not r.feature_valid:return {'status':'missing_initial_risk_or_context'}
    entry=r.entry;side=r.side;risk=r.risk;tp=r.tp0;sl=r.sl0
    t=d.t.to_numpy();first=(int(r.entry_t)+59)//60*60;start=np.searchsorted(t,first)
    # A partial entry minute cannot tell whether its barrier touch happened before or after fill.
    if int(r.entry_t)%60:
        j=np.searchsorted(t,int(r.entry_t)//60*60)
        if j<len(d)and t[j]==int(r.entry_t)//60*60:
            bar=d.iloc[j];hh,ll=bar.high,bar.low
            if side<0:hh+=bar.spread_px;ll+=bar.spread_px
            if (ll<=sl or hh>=tp)if side>0 else(hh>=sl or ll<=tp):return {'status':'partial_entry_barrier_ambiguous'}
    if start>=len(d)or t[start]!=first:return {'status':'missing_first_full_bar'}
    last=(int(r.exit_t)//60)*60
    mfe=0.;mae=0.;opposite=0;price=None;exit_t=None;status='unresolved_original';trigger=None
    boundary=r.m1_hi60 if side>0 else r.m1_lo60
    breakout=side*(entry-boundary)>=-.25*r.m5_atr
    for k in range(start,len(d)):
        now=int(t[k])
        if now>last:break
        if now!=first+(k-start)*60:return {'status':'path_gap'}
        bar=d.iloc[k];quote=bar.open+(bar.spread_px if side<0 else 0)
        hi=bar.high+(bar.spread_px if side<0 else 0);lo=bar.low+(bar.spread_px if side<0 else 0)
        hs=lo<=sl if side>0 else hi>=sl;ht=hi>=tp if side>0 else lo<=tp
        os=side*(quote-sl)<=0;ot=side*(quote-tp)>=0
        if os:price=quote;status='sl';exit_t=now;break
        if ot:price=tp;status='tp';exit_t=now;break
        if hs:price=sl;status='sl';exit_t=now+60;break
        if ht:price=tp;status='tp';exit_t=now+60;break
        available=now+60
        if available>=r.exit_t:break # Never make a later close signal earlier than actual exit.
        close=bar.close+(bar.spread_px if side<0 else 0);progress=side*(close-entry)/risk
        fav=(hi-entry)/risk if side>0 else(entry-lo)/risk;adv=(lo-entry)/risk if side>0 else(entry-hi)/risk
        mfe=max(mfe,fav);mae=min(mae,adv);elapsed=(available-r.entry_t)/60
        ff=f.loc[now]if now in f.index else None
        if ff is None:continue
        against=side*(bar.close-ff.m5_ema20)<0
        opposite=opposite+1 if against else 0
        fire=False
        if rule=='P1_M5_OPPOSE':fire=ff.m5_dir*side<0 and progress<=-.1
        elif rule=='P2_BREAK_FAIL':fire=breakout and side*(bar.close-boundary)<0 and progress<=-.1
        elif rule=='P3_EMA_TWO':fire=opposite>=2 and progress<=-.1
        elif rule=='P4_VOL_OPPOSE':fire=ff.m5_vol_ratio>=2 and ff.m1_body*side<=-.4 and progress<=-.1
        elif rule in ['P5_TIME15','P6_TIME30']:
            wait=15 if rule=='P5_TIME15'else 30;fire=wait<=elapsed<wait+1 and mfe<.2 and progress<0
        elif rule=='P7_ADVERSE5':fire=5<=elapsed<6 and progress<=-.25
        elif rule=='P8_ADVERSE10':fire=10<=elapsed<11 and mae<=-.3 and progress<=-.15
        elif rule.startswith('TIME'):wait=int(rule[4:]);fire=wait<=elapsed<wait+1
        if fire:
            if k+1>=len(d)or t[k+1]!=available:return {'status':'missing_next_open'}
            if available>=r.exit_t:continue
            nxt=d.iloc[k+1];price=nxt.open+(nxt.spread_px if side<0 else 0)-side*.002;exit_t=available;status='cancel';trigger=available;break
    if price is None:return {'status':status}
    # Conservative funding for earlier exit: retain all negative actual swap, discard any positive swap.
    pv=100.;net=side*(price-entry)*r.lot*pv+r.commission+(min(0,r.swap)if status=='cancel'else r.swap)
    return {'status':status,'exit_px':price,'exit_t':exit_t,'net':net,'R':net/r.risk_cash,'trigger':trigger,'mfe_R_before_trigger':mfe,'mae_R_before_trigger':mae}

def main():
    d=pd.read_csv(DATA/'broker_1m.csv');r=pd.read_csv(OUT/'oil_position_features.csv');f=map_rows(compute(d),d.assign(entry_t=d.t,risk=np.nan,reward=np.nan,side=1));f=f.set_index('t');info={};rows=[]
    for rr in r.itertuples():
        base=replay(d,f,rr,'BASE');row={'pid':rr.pid,'entry_t':rr.entry_t,'exit_t_actual':rr.exit_t,'actual_net':rr.net,'actual_R':rr.R_actual,'actual_reason':rr.comment,'base':base};row['rules']={rule:replay(d,f,rr,rule)for rule in RULES[1:]};rows.append(row)
    save(OUT/'cancel_replays.json',rows)
    disc=[x for x in rows if x['entry_t']>=int(pd.Timestamp(PERIODS['DISC'][0],tz='UTC').timestamp())and x['exit_t_actual']<int(pd.Timestamp(PERIODS['DISC'][1],tz='UTC').timestamp())]
    valid=[x for x in disc if x['base']['status']in ['tp','sl']]
    errors=np.asarray([abs(x['base']['R']-x['actual_R'])for x in valid]);correct=[(x['base']['status']=='tp')==('[tp' in str(x['actual_reason']).lower())for x in valid]
    passed=len(valid)>=20 and np.mean(correct)>=.9 and np.median(errors)<=.05 and np.quantile(errors,.9)<=.15
    calibration={'status':'PASS'if passed else'FAIL','discovery_trades':len(disc),'resolved_comparable':len(valid),'class_agreement':float(np.mean(correct))if valid else None,'median_abs_R_error':float(np.median(errors))if valid else None,'p90_abs_R_error':float(np.quantile(errors,.9))if valid else None,'exclusions':pd.Series([x['base']['status']for x in disc]).value_counts().to_dict(),'thresholds':{'min20':True,'class90':True,'median05':True,'p90_15':True}}
    result={'calibration':calibration,'rules':{},'evaluation_cells':len(RULES)*3,'not_actual_executed_cancel':'counterfactual fixed-initial-geometry replay; unknown bot replacement and future management'}
    for p,(lo,hi)in PERIODS.items():
        l=int(pd.Timestamp(lo,tz='UTC').timestamp());h=int(pd.Timestamp(hi,tz='UTC').timestamp());cohort=[x for x in rows if l<=x['entry_t'] and x['exit_t_actual']<h and x['base']['status']in ['tp','sl']]
        for rule in RULES:
            a=[]
            for x in cohort:
                v=x['base']if rule=='BASE'else x['rules'][rule]
                if v['status']not in ['tp','sl','cancel']:continue
                z={'pid':x['pid'],'decision':x['entry_t'],'actual_exit_t':x['exit_t_actual'],'day':str(pd.Timestamp(x['entry_t'],unit='s',tz='UTC').tz_convert('America/New_York').date()),'actual_net':x['actual_net'],'base_net':x['base']['net'],'base_R':x['base']['R'],**v};z['delta_net']=z['net']-z['base_net'];a.append(z)
            a=pd.DataFrame(a);a.to_csv(OUT/f'cancel_{p}_{rule}.csv',index=False)
            info={'n':len(a),'triggered':int((a.status=='cancel').sum())if len(a)else 0,'delta_vs_simulated_original':float(a.delta_net.sum())if len(a)else 0,'calibration_passed':bool(passed)}
            if len(a):
                v=a.groupby('day').delta_net.sum().to_numpy();rng=np.random.default_rng(214);boot=v[rng.integers(0,len(v),size=(5000,len(v)))].sum(axis=1);info.update(bootstrap={'p_positive':float((boot>0).mean()),'ci95_total':np.quantile(boot,[.025,.975]).tolist()},worse_n=int((a.delta_net<0).sum()),better_n=int((a.delta_net>0).sum()),actual_baseline_net=float(a.actual_net.sum()),original_simulated_net=float(a.base_net.sum()),candidate_simulated_net=float(a.net.sum()))
            result['rules'].setdefault(rule,{})[p]=info
        print('cancel',p,len(cohort),flush=True)
    save(OUT/'cancel_validation.json',result);print('CALIBRATION',calibration,flush=True)
if __name__=='__main__':main()
