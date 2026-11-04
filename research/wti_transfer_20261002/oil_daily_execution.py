"""Side-symmetric fixed-risk partial/whole exits on available observed OHLC paths."""
import numpy as np
import pandas as pd

def replay(d,ev,rule='BASE',step=1,spread_mult=1.,slip=.002,delay=0):
    t=d.t.to_numpy();op,hi,low,cl=[d[c].to_numpy()for c in ['open','high','low','close']];sp=d.spread_px.to_numpy()
    ask={c:d['ask_'+c].to_numpy()if 'ask_'+c in d else d[c].to_numpy()+sp for c in ['open','high','low','close']}
    rows=[]
    for e in ev.itertuples():
        entry_t=e.decision+delay*step*60;i=int(np.searchsorted(t,entry_t))
        if i>=len(t)or t[i]!=entry_t:continue
        side=getattr(e,'side',1);end_min=getattr(e,'end_min',960)
        cutoff=int(pd.Timestamp(e.day+' 00:00',tz='America/New_York').timestamp())+end_min*60
        if entry_t>=cutoff:continue
        entry=op[i]-slip if side<0 else ask['open'][i]+(spread_mult-1)*sp[i]+slip
        risk=entry*(.0149 if rule=='CAP_FIXED'else e.dvol)
        stop=entry-side*risk;rr=.0104/.0149 if rule=='CAP_FIXED'else 1.
        target=entry+side*rr*risk
        full_target=rule in ['FULL_TP1','TP1_RISING','CAP_FIXED','OVX_TP1','MIRROR']
        half_target=rule in ['HALF_RUNNER','HALF_RISING','OVX_HALF']
        ten=int(pd.Timestamp(e.day+' 10:00',tz='America/New_York').timestamp())
        realized=0.;fraction=1.;target_done=False;partial_t=None;reason=None;ambiguous=False;k=i
        while k<len(t)and t[k]<=cutoff:
            if t[k]!=entry_t+(k-i)*step*60:
                k-=1;px=cl[k]-slip if side>0 else ask['close'][k]+(spread_mult-1)*sp[k]+slip;reason='data_gap';break
            o,h,l=(op[k],hi[k],low[k])if side>0 else tuple(ask[c][k]+(spread_mult-1)*sp[k]for c in ['open','high','low'])
            if side*(o-stop)<=0:px=o-side*slip;reason='stop';break
            has=(full_target or half_target)and not target_done
            if has and side*(o-target)>=0:
                qty=.5 if half_target else 1.;realized+=qty*side*(target-side*slip-entry)/risk;fraction-=qty;target_done=True;partial_t=int(t[k])
                if fraction==0:px=target-side*slip;reason='target';break
            fail=rule=='FAIL_10'and t[k]==ten and entry_t<ten and cl[k-1]<=e.level
            early=rule=='ALWAYS_10'and t[k]==ten and entry_t<ten
            if t[k]==cutoff or fail or early:px=o-side*slip;reason='time';break
            # Never inspect excursions after a native bar straddles the planned cutoff.
            if t[k]<cutoff<t[k]+step*60:px=o-side*slip;reason='native_time_proxy';break
            hs=l<=stop if side>0 else h>=stop
            ht=has and not target_done and (h>=target if side>0 else l<=target)
            if hs:px=stop-side*slip;reason='stop';ambiguous=bool(ht);break
            if ht:
                qty=.5 if half_target else 1.;realized+=qty*side*(target-side*slip-entry)/risk;fraction-=qty;target_done=True;partial_t=int(t[k])
                if fraction==0:px=target-side*slip;reason='target';break
            k+=1
        if reason is None:
            k=min(k-1,len(t)-1);px=cl[k]-slip if side>0 else ask['close'][k]+(spread_mult-1)*sp[k]+slip;reason='data_gap'
        net=realized+fraction*side*(px-entry)/risk
        rows.append(dict(decision=e.decision,entry_t=entry_t,exit_t=int(t[k])+step*60,entry=entry,exit=px,risk=risk,R=net,points=net*risk,
                         reason=reason,ambiguous=ambiguous,day=e.day,side=side,candidate=rule,priority=0,target_done=target_done,partial_t=partial_t))
    return pd.DataFrame(rows,columns=['decision','entry_t','exit_t','entry','exit','risk','R','points','reason','ambiguous','day','side','candidate','priority','target_done','partial_t'])
