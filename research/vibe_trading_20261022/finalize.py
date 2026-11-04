"""Recompute saved trades under the predeclared Monte Carlo resolution fix."""
import json
import pandas as pd
from data_audit import HERE, SYMBOLS, SPREAD, recent, long
from replay import summarize
OUT=HERE/'results'
def main():
 t=pd.read_csv(OUT/'trades.csv',parse_dates=['entry_ts','exit_ts','decision_ts'])
 s=pd.read_csv(OUT/'summary.csv');rows=[]
 keys=['dataset','symbol','strategy','epoch']
 for _,row in s.iterrows():
  q=t
  for k in keys:q=q[q[k]==row[k]]
  rows.append({k:row[k] for k in keys}|summarize(q))
 s=pd.DataFrame(rows);s['holm_pass']=False
 ix=s.index[(s.epoch=='test') & s.control_p.notna()];cont=True
 for k,i in enumerate(s.loc[ix].sort_values('control_p').index):
  cont=cont and bool(s.at[i,'control_p']<=.05/(54-k));s.at[i,'holm_pass']=cont
 s.to_csv(OUT/'summary.csv',index=False)
 detail=[]
 for kvals,g in t.groupby(keys+['side']):detail.append(dict(zip(keys+['side'],kvals))|summarize(g))
 pd.DataFrame(detail).to_csv(OUT/'by_side.csv',index=False)
 # Calendar-period buy-and-hold; a baseline, no strategy selection.
 base=[]
 for sym in SYMBOLS:
  for dataset,split in [('recent_5m','2026-09-01'),('long_1h','2024-01-01')]:
   d=recent(sym) if dataset=='recent_5m' else long(sym)
   ix=d.index if dataset=='recent_5m' else pd.DatetimeIndex(d.start_ts)
   for epoch,mask in [('development',ix<pd.Timestamp(split,tz='UTC')),('test',ix>=pd.Timestamp(split,tz='UTC'))]:
    q=d.loc[mask]
    if len(q)<2:continue
    entry=q.open.iloc[0];exit=q.close.iloc[-1];cost=1.2*SPREAD[sym]
    base.append(dict(symbol=sym,dataset=dataset,epoch=epoch,start=str(q.index[0]),end=str(q.index[-1]),long_net_bp=(exit-entry-cost)/entry*1e4,short_net_bp=(entry-exit-cost)/entry*1e4,warning='continuous hold includes unmeasured swap; not like-for-like exposure'))
 pd.DataFrame(base).to_csv(OUT/'buy_hold.csv',index=False)
 # Every cell assessed without selecting a winner from test.
 cards=[]
 for keys2,g in s.groupby(['dataset','symbol','strategy']):
  dev=g[g.epoch=='development'].iloc[0];test=g[g.epoch=='test'].iloc[0]
  checks={'test_150':bool(test.n>=150),'development_positive':bool(dev.get('mean_R',0)>0),'test_positive':bool(test.get('mean_R',0)>0),'test_bootstrap_90':bool(test.get('p_ev_positive',0)>=.9),'stress_positive':bool(test.get('stress_R',0)>0),'control_holm':bool(test.get('holm_pass',False)),'real_historical_spread':False,'independent_forward_shadow':False,'actual_m1_execution':keys2[0]=='recent_5m'}
  cards.append(dict(zip(['dataset','symbol','strategy'],keys2))|{'status':'RESEARCH_ONLY','research_candidate':all(checks[k] for k in ['test_150','development_positive','test_positive','test_bootstrap_90','stress_positive','control_holm']),'checks':checks})
 (OUT/'research_cards.json').write_text(json.dumps(cards,indent=2))
 print(s[s.epoch=='test'][['dataset','symbol','strategy','n','win_rate','mean_R','mean_bp','stress_R','control_p','holm_pass']].to_string(index=False))
 print('CANDIDATES',sum(c['research_candidate'] for c in cards),'/',len(cards))
if __name__=='__main__':main()
