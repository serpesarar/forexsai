"""Frozen daily-vol paths, CAP controls, overnight and capital occupancy on oil."""
from core import *
from micro import get_grid,named_event_rows
from oil_daily_execution import replay
cap=module('oil_cap_controls',ROOT/'research/ndx_synthesis_20261002/caprev.py')
CASES={'base':{},'spread3':{'spread_mult':3},'slip1':{'slip':.01},'delay1':{'delay':1}}

def summarize(a,source,step):
    pp=LONG_PERIODS if step>1 else periods(source)
    rows=[];by={}
    for p,(lo,hi) in pp.items():
        z=a[(a.decision>=lab.stamp(lo))&(a.exit_t<lab.stamp(hi))].copy();z['period']=p;rows.append(z)
        by[p]=stats(z[z.R.notna()],True);by[p]['unresolved']=int(z.R.isna().sum())
    a=pd.concat(rows,ignore_index=True).sort_values('decision')
    return a,{'aggregate':stats(a[a.R.notna()],True),'periods':by,'unresolved':int(a.R.isna().sum())}

def overnight(d,e,step,kw):
    e=e.copy();e.decision+=kw.get('delay',0)*step*60
    before=cap_overnight.macro;cap_overnight.macro=lambda:macro_for(d,step).rename(columns={'OIL_close':'NDXCASH_close'})
    try:a=cap_overnight.overnight_replay(d,e,step,slip=kw.get('slip',.002),spread_mult=kw.get('spread_mult',1))
    finally:cap_overnight.macro=before
    if a.empty:a=replay(d,e.iloc[:0],step=step).assign(overnights=0)
    a['priority']=0;a['ambiguous']=False;return a

def main():
    result={'results':{},'evaluation_cells':0,'paths':cap_paths.RULES+['HALF_RISING','TP1_RISING']+cap.RULES,'overnight':cap_overnight.RULES}
    ds=datasets();sources=[(s,d,1,[1,5,15])for s,d in ds.items()]+[(f'native{step}',native(step),step,[step])for step in [15,30,60]]
    for source,d,step,tfs in sources:
        for tf in tfs:
            f=cap_context(d,tf,step)
            if step==1:
                extra=features(d,tf,source);f['low15_m1']=extra.low15_m1;f['atr70']=extra.atr70;f['clv']=extra.clv
            else:
                f['low15_m1']=d.low.rolling(max(1,15//step)).min().to_numpy();f['atr70']=d.atr70.to_numpy();f['clv']=(2*f.close-f.high-f.low)/(f.high-f.low).replace(0,np.nan)
            ev={r:cap_paths.detect(f,'VIX_RISING'if r.endswith('_RISING')and r!='VIX_RISING'else r)for r in cap_paths.RULES+['HALF_RISING','TP1_RISING']}
            ev.update({r:cap.detect(f,tf,r)for r in cap.RULES})
            for case,kw in (CASES.items()if tf==1 or step>1 else [('base',{})]):
                frames={}
                for rule,e in ev.items():
                    a=sequential(replay(d,e,rule,step,**kw));a,info=summarize(a,source,step)
                    key=f'{source}/{tf}/{case}/{rule}';a.to_csv(OUT/f'daily_{source}_{tf}_{case}_{rule}.csv',index=False)
                    result['results'][key]=info;result['evaluation_cells']+=len(info['periods']);frames[rule]=a
                if tf==step:
                    op=cap_overnight.opening(f,step);dip=ev['BASE']
                    legs={'OPEN_SAME':replay(d,op,'BASE',step,**kw),'DIP_SAME':replay(d,dip,'BASE',step,**kw),
                          'DIP_NEXT':overnight(d,dip,step,kw),'OPEN_NEXT':overnight(d,op,step,kw)}
                    for r,a in legs.items():a['priority']=0 if r.startswith('OPEN')else 1;a['candidate']=r
                    legs['UNION_SAME']=sequential(pd.concat([legs['OPEN_SAME'],legs['DIP_SAME']],ignore_index=True))
                    legs['UNION_MIXED']=sequential(pd.concat([legs['OPEN_SAME'],legs['DIP_NEXT']],ignore_index=True))
                    for r,a in legs.items():
                        a,info=summarize(sequential(a),source,step);key=f'{source}/{tf}/{case}/ON_{r}'
                        a.to_csv(OUT/f'daily_{source}_{tf}_{case}_ON_{r}.csv',index=False)
                        if 'overnights'in a:
                            funded=a[a.R.notna()].copy();funded.R-=.0005*funded.entry/funded.risk*funded.overnights.fillna(0)
                            info['funding5bp']=stats(funded,True)
                        result['results'][key]=info;result['evaluation_cells']+=len(info['periods'])
                if tf==1:
                    x=named_event_rows(features(d,1,source),1);grids={g:get_grid(d,source,g,case)for g in ['core','slow','fast','fixed']}
                    raw=[]
                    for p in periods(source):
                        for (prio,name,g),z in x.groupby(['priority','candidate','geometry']):
                            a=lab.replay(z.decision.to_numpy(),z.side.to_numpy(),grids[g],p,False);a['priority']=int(prio)+1;a['candidate']=name;raw.append(a)
                    raw=pd.concat(raw,ignore_index=True);base=sequential(raw)
                    for rule in ['NONE','BASE','HALF_RISING','TP1_RISING']:
                        if rule=='NONE':a=base.copy()
                        else:
                            c=frames[rule].copy();c['priority']=0;c['candidate']='CAP_'+rule;a=sequential(pd.concat([raw,c],ignore_index=True))
                        a,info=summarize(a,source,1);info['aggregate'].update(delta_R=float(a.R.sum()-base.R.sum()),paired=mechanism.delta_boot(a,base))
                        a.to_csv(OUT/f'capital_{source}_{case}_{rule}.csv',index=False);result['results'][f'{source}/1/{case}/PORT_{rule}']=info;result['evaluation_cells']+=len(info['periods'])
                lab.save_json(OUT/'daily.json',result);print('daily',source,tf,case,flush=True)
    lab.save_json(OUT/'daily.json',result);print('DAILY DONE',result['evaluation_cells'],flush=True)
if __name__=='__main__':main()
