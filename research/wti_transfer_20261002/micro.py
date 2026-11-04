"""All prior micro search definitions plus frozen selections, mechanisms and gates."""
import sys,json,time,hashlib
import numpy as np
import pandas as pd
from core import *
from oil_execution import simulate_grid

FROZEN1=json.loads((ROOT/'research/ndx_five_gates_20260930/results/frozen_five.json').read_text())['candidates']
FROZEN2=synth.SPECS
GEOMS={**old2.GEOMETRIES,'fixed':{'geometry':'fixed'},'symmetric':{'geometry':'symmetric'}}

def get_grid(d,source,geom,case='base'):
    p=OUT/f'grids_{source}_{geom}_{case}.pkl'
    if p.exists():return pd.read_pickle(p)
    kw={'base':{},'spread3':{'spread_mult':3},'slip1':{'slip':.01},'delay1':{'delay':1}}[case]
    g=simulate_grid(d,**GEOMS[geom],**kw);pd.to_pickle(g,p);return g

def replay_events(ts,sd,g,source,full=False):
    rows=[];byperiod={}
    for p in periods(source):
        a=lab.replay(ts,sd,g,p);a['period']=p;rows.append(a);byperiod[p]=stats(a,full)
    return pd.concat(rows,ignore_index=True).sort_values('decision'),byperiod

def discovery():
    """Only discovery labels are evaluated in this first phase."""
    d=datasets(False)['cache'];d=d[d.t<lab.stamp('2026-05-16')].copy();f=features(d,1,'discovery',False)
    allspec=old2.definitions();result={'unique_strategy_geometry_definitions':1620,'original432_included_in_core':True,'results':[]}
    best=[]
    for geom in ['fast','core','slow']:
        g=simulate_grid(d,**GEOMS[geom])
        for n,s in enumerate(allspec):
            ts,sd=old2.detect(f,s,1)
            aa=[lab.replay(ts,sd,g,p)for p in ['DISC_A','DISC_B']]
            info={p:stats(a)for p,a in zip(['DISC_A','DISC_B'],aa)}
            result['results'].append({'id':s['id']+'_'+geom,'spec':s,'geometry':geom,'metrics':info})
        print('discovery complete',geom,len(allspec),flush=True)
    result['evaluation_cells']=len(result['results'])*2
    lab.save_json(OUT/'micro_discovery.json',result)
    for fam in lab.FAMILIES+old2.EXTRA:
        recs=[z for z in result['results']if z['spec']['family']==fam]
        for z in recs:
            z['rank']=min(v['ev']for v in z['metrics'].values())
            z['enough']=all(v['n']>=30 for v in z['metrics'].values())
        recs=sorted(recs,key=lambda z:(z['enough'],z['rank']),reverse=True)
        best.append(recs[0])
    lab.save_json(OUT/'discovery_family_summary.json',best)
    print('discovery-only family summary',[(r['spec']['family'],r['id'],round(r['rank'],3),r['enough'])for r in best],flush=True)

def scan_all():
    ds=datasets();results=json.loads((OUT/'micro_all.json').read_text())if(OUT/'micro_all.json').exists()else{'sources':{},'evaluation_cells':0,'definition_count':1620}
    spec=old2.definitions()
    for source,d in ds.items():
        if source in results['sources']:continue
        f=features(d,1,source);events={s['id']:old2.detect(f,s,1)for s in spec};records=[]
        for geom in ['fast','core','slow']:
            g=get_grid(d,source,geom)
            for s in spec:
                a,info=replay_events(*events[s['id']],g,source)
                records.append({'id':s['id']+'_'+geom,'spec':s,'geometry':geom,'metrics':info})
                results['evaluation_cells']+=len(info)
            print('all transfer scan',source,geom,len(records),flush=True)
        results['sources'][source]=records;lab.save_json(OUT/'micro_all.json',results)
    print('scan complete cells',results['evaluation_cells'],flush=True)

def named_event_rows(f,tf):return synth.events(f,tf)

def execute(x,grids,source):
    rows=[];by={}
    for p in periods(source):
        a=synth.execute(x,grids,p);a['period']=p;rows.append(a);by[p]=stats(a,True)
    return pd.concat(rows,ignore_index=True).sort_values('decision'),by

def day_gates(x,rule):
    block=pd.Series(False,index=x.index)
    if rule=='K1':block=(x.side<0)&x.weekday.eq(0)
    elif rule=='K2':
        fomc=pd.to_datetime(['2025-01-29','2025-03-19','2025-05-07','2025-06-18','2025-07-30','2025-09-17','2025-10-29','2025-12-10',
                            '2026-01-28','2026-03-18','2026-04-29','2026-06-17','2026-07-29','2026-09-16'])
        date=pd.to_datetime(x.day)
        block=(x.side<0)&((date.isin(fomc-pd.Timedelta(days=1))&(x.minute>=840))|(date.isin(fomc)&(x.minute<840)))
    elif rule=='K3':
        # Known weekday calendar, not future observed prices/available trading days.
        date=pd.to_datetime(x.day);monthend=date+pd.offsets.BMonthEnd(0)
        priorend=monthend-pd.offsets.BDay(1);end2=date.isin(pd.concat([monthend,priorend]).unique())
        block=end2&(((x.side>0)&(x.mtd>=.04))|((x.side<0)&(x.mtd<=-.04)))
    elif rule=='K4a':block=x.vr15_240>1.2
    elif rule=='K4b':block=(x.vr15_240>1.2)&(x.drift60_m1*x.side<0)
    elif rule=='CHASE':block=(x.side<0)&(x.chase_sell>=3)
    elif rule=='DAY_COMBINED':
        z=x
        for r in ['K1','K3','K5','K6']:z=day_gates(z,r)if r in ['K1','K3']else synth.apply_overlay(None,z,r)
        return z
    return x[~block].copy()

def detailed():
    result=json.loads((OUT/'micro_detailed.json').read_text())if(OUT/'micro_detailed.json').exists()else{'evaluation_cells':0,'sources':{},'rules':{}}
    controls=synth.OVERLAYS+synth.RECLAIMS+['CHASE','K1','K2','K3','K4a','K4b','DAY_COMBINED']
    for source,d in datasets().items():
        if source in result['sources']:continue
        sr={};result['sources'][source]={'rows':len(d),'first':str(d.ts.min()),'last':str(d.ts.max())}
        for tf in [1,3,5,15]:
            f=features(d,tf,source);parent=named_event_rows(f,tf)
            candidates={r:synth.apply_overlay(d,parent,r)for r in synth.OVERLAYS}
            candidates.update({r:synth.reclaim(f,tf,r)for r in synth.RECLAIMS})
            candidates.update({r:day_gates(parent,r)for r in ['CHASE','K1','K2','K3','K4a','K4b','DAY_COMBINED']})
            for case in (['base','spread3','slip1','delay1']if tf==1 else ['base']):
                grids={g:get_grid(d,source,g,case)for g in ['fast','core','slow','fixed']}
                b,_=execute(parent,grids,source)
                for rule,x in candidates.items():
                    a,info=execute(x,grids,source);key=f'{source}/{tf}/{case}/overlay_{rule}'
                    a.to_csv(OUT/f'micro_{source}_{tf}_{case}_overlay_{rule}.csv',index=False)
                    sr[key]={'aggregate':compare(a,b),'periods':info};result['evaluation_cells']+=len(info)
                for spec in FROZEN1+FROZEN2:
                    geom=spec.get('geometry','core');ts,sd=old2.detect(f,spec,tf)
                    a,info=replay_events(ts,sd,grids[geom],source,True)
                    key=f'{source}/{tf}/{case}/frozen_{spec["id"]}'
                    a.to_csv(OUT/f'micro_{source}_{tf}_{case}_frozen_{spec["id"]}.csv',index=False)
                    sr[key]={'aggregate':stats(a,True),'periods':info};result['evaluation_cells']+=len(info)
                for spec in mechanism.definitions():
                    geom=spec['geometry'];gg=grids['core'if geom=='core'else 'fixed']
                    for mode in ['candidate','parent']+(['blind']if spec['family']in ['D2','D3']else ['macro_only','micro_only']if spec['family']=='D4'else []):
                        x=mechanism.candidates(d,f,spec,mode)
                        a,info=replay_events(x.decision.to_numpy(),x.side.to_numpy(),gg,source,True)
                        key=f'{source}/{tf}/{case}/mechanism_{spec["id"]}_{mode}'
                        a.to_csv(OUT/f'micro_{source}_{tf}_{case}_mechanism_{spec["id"]}_{mode}.csv',index=False)
                        sr[key]={'aggregate':stats(a,True),'periods':info};result['evaluation_cells']+=len(info)
                print('detailed',source,tf,case,len(sr),flush=True)
        result['rules'].update(sr);lab.save_json(OUT/'micro_detailed.json',result)
    print('detailed complete cells',result['evaluation_cells'],flush=True)

if __name__=='__main__':
    {'discovery':discovery,'scan':scan_all,'detailed':detailed}[sys.argv[1]]()
