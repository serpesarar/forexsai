"""Nominal-scale and 1:1 controls; not additional oil-selected winners."""
from core import *
from micro import FROZEN1,FROZEN2,get_grid,replay_events
from oil_execution import simulate_grid

def main():
    result={'results':{},'evaluation_cells':0,'literal_Nasdaq_not_equivalent':True}
    for source,d in datasets().items():
        f=features(d,1,source)
        grids={'symmetric':get_grid(d,source,'symmetric'),
               'literal_min35':simulate_grid(d,min_stop=35),
               'literal_80_110':simulate_grid(d,risk_mult=0,min_stop=110,reward_ratio=80/110)}
        for spec in FROZEN1+FROZEN2:
            ts,side=old2.detect(f,spec,1)
            for rule,g in grids.items():
                a,by=replay_events(ts,side,g,source,True);name=f'{source}/{rule}/{spec["id"]}'
                a.to_csv(OUT/f'diagnostic_{source}_{rule}_{spec["id"]}.csv',index=False)
                result['results'][name]={'aggregate':stats(a,True),'periods':by};result['evaluation_cells']+=len(by)
        print('diagnostics',source,flush=True)
    lab.save_json(OUT/'diagnostics.json',result)
if __name__=='__main__':main()
