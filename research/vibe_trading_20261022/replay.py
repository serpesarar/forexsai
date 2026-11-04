"""Causal CFD replay of unchanged Vibe-Trading example engines.

No broker/DB access. Position 0 is flat, as in the upstream target-position API.
R uses decision-time 2*ATR14 as a reporting unit, not an enforced stop.
"""
from pathlib import Path
import json
import socket
import sys
import time
import numpy as np
import pandas as pd
from data_audit import HERE, SYMBOLS, SPREAD, recent, aggregate, long
from causality import STRATEGIES, generate
OUT=HERE/'results'
SEED=20261022

def atr(d):
 pc=d.close.shift(1)
 tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
 return tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()

def replay(d, signals, execution, start, end, tf_min, spread):
 """Execute only a fresh closed-bar target at the next available open.

 A decision at 10:05 is based on [10:00,10:05) and can fill at the M1 open
 stamped 10:05. No same-bar close fill; absent open means no stale entry.
 Large gaps force an existing position out at the first observed open.
 """
 a=atr(d)*2
 sig=pd.DataFrame({'target':signals,'risk':a,'signal_i':np.arange(len(d))})
 sig=sig.iloc[160:]
 sig=sig[(sig.index>=start)&(sig.index<end)]
 ex=execution[(execution.index>=start)&(execution.index<end)]
 if len(ex)==0:return pd.DataFrame()
 # Restrict work to target timestamps plus all first opens after data gaps.
 ix=ex.index
 event_times=ix.intersection(sig.index)
 gap=ix.to_series().diff()>pd.Timedelta(minutes=3*tf_min)
 event_times=event_times.union(ix[gap]).sort_values()
 pos=None; rows=[]
 def close(px,ts,why):
  nonlocal pos
  if pos is None:return
  gross=pos['side']*(px-pos['entry'])
  cost=1.2*spread
  rows.append({**pos,'exit':px,'exit_ts':ts,'reason':why,'gross_px':gross,'cost_px':cost,'net_px':gross-cost,'gross_R':gross/pos['risk'],'cost_R':cost/pos['risk'],'net_R':(gross-cost)/pos['risk'],'stress_R':(gross-1.5*cost)/pos['risk'],'net_bp':(gross-cost)/pos['entry']*1e4,'gross_bp':gross/pos['entry']*1e4,'hold_minutes':(ts-pos['entry_ts']).total_seconds()/60})
  pos=None
 for ts in event_times:
  px=float(ex.at[ts,'open'])
  if bool(gap.at[ts]) and pos is not None:close(px,ts,'data_gap')
  if ts not in sig.index:continue
  row=sig.loc[ts];target=int(np.sign(row.target))
  if pos is not None and pos['side']!=target:close(px,ts,'signal')
  if target and pos is None and np.isfinite(row.risk) and row.risk>0:
   pos=dict(entry=px,entry_ts=ts,decision_ts=ts,side=target,risk=float(row.risk),decision_i=int(row.signal_i))
 if pos is not None:
  close(float(ex.close.iloc[-1]),ex.index[-1]+pd.Timedelta(minutes=1 if tf_min==5 else 60),'evaluation_end')
 return pd.DataFrame(rows)

def summarize(t):
 if t.empty:return dict(n=0)
 x=t.net_R.values;n=len(x);wins=int((x>0).sum());p=wins/n;z=1.959964
 den=1+z*z/n;center=(p+z*z/(2*n))/den
 width=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 eq=np.r_[0,np.cumsum(x)]
 dates=t.entry_ts.dt.floor('D')
 sums=t.groupby(dates).net_R.agg(['sum','count'])
 rng=np.random.default_rng(SEED)
 boot=[]
 for _ in range(20):
  ii=rng.integers(0,len(sums),size=(100,len(sums)))
  boot.extend((sums['sum'].values[ii].sum(1)/sums['count'].values[ii].sum(1)).tolist())
 boot=np.array(boot)
 # Day-block random direction control, identical entries/exits and all costs.
 grp=t.groupby(dates).agg(gross=('gross_R','sum'),cost=('cost_R','sum'))
 signs=rng.choice([-1,1],size=(10000,len(grp)))
 null=(signs@grp.gross.values-grp.cost.sum())/n
 pnull=(1+int((null>=x.mean()).sum()))/10001
 return dict(n=n,days=len(sums),wins=wins,win_rate=100*p,wr_low=100*(center-width),wr_high=100*(center+width),mean_R=float(x.mean()),total_R=float(x.sum()),dd_R=float((np.maximum.accumulate(eq)-eq).max()),mean_bp=float(t.net_bp.mean()),stress_R=float(t.stress_R.mean()),gross_R=float(t.gross_R.mean()),p_ev_positive=float((boot>0).mean()),ci_low=float(np.quantile(boot,.025)),ci_high=float(np.quantile(boot,.975)),control_mean_R=float(null.mean()),control_p=pnull,forced_end=int((t.reason=='evaluation_end').sum()),gap_exits=int((t.reason=='data_gap').sum()),hold_median_min=float(t.hold_minutes.median()),hold_max_min=float(t.hold_minutes.max()),buy_n=int((t.side==1).sum()),sell_n=int((t.side==-1).sum()))

def main():
 socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline replay: networking denied'))
 audits=json.loads((OUT/'causality.json').read_text())['audits']
 allowed={s for s in STRATEGIES if all(x.get('passed',False) for x in audits if x['strategy']==s)}
 rows=[];all_trades=[];errors=[];extra=[]
 for dataset in ['recent_5m','long_1h']:
  for sym in SYMBOLS:
   if dataset=='recent_5m':
    ex=recent(sym);d=aggregate(ex,5);tf=5;split=pd.Timestamp('2026-09-01',tz='UTC')
   else:
    d=long(sym);ex=d.copy();ex.index=ex.start_ts;tf=60;split=pd.Timestamp('2024-01-01',tz='UTC')
   inp=d.drop(columns='start_ts')
   for strategy in STRATEGIES:
    if strategy not in allowed:continue
    if strategy=='technical-basic' and 'volume' not in inp:
     errors.append(dict(dataset=dataset,symbol=sym,strategy=strategy,status='unsupported',reason='missing historical volume'));continue
    now=time.monotonic();print('START',dataset,sym,strategy,flush=True)
    try:
     signals=generate(strategy,{sym:inp})[sym]
     # Confirm all earlier outputs at early/mid/late prefixes on actual full data.
     ok=True
     for cut in sorted(set([min(len(inp),800),len(inp)//2,len(inp)-1])):
      sub=generate(strategy,{sym:inp.iloc[:cut]})[sym]
      mismatch=~np.isclose(sub.values,signals.reindex(sub.index).values,atol=1e-12,rtol=1e-12,equal_nan=True)
      extra.append(dict(dataset=dataset,symbol=sym,strategy=strategy,cut=cut,passed=not mismatch.any(),mismatches=int(mismatch.sum())))
      ok=ok and not mismatch.any()
     if not ok:
      errors.append(dict(dataset=dataset,symbol=sym,strategy=strategy,status='causality_failed'));continue
     for epoch,start,end in [('development',pd.Timestamp('2000-01-01',tz='UTC'),split),('test',split,pd.Timestamp('2100-01-01',tz='UTC'))]:
      t=replay(d,signals,ex,start,end,tf,SPREAD[sym])
      keys=dict(dataset=dataset,symbol=sym,strategy=strategy,epoch=epoch)
      rows.append({**keys,**summarize(t)})
      if not t.empty:
       for k,v in keys.items():t[k]=v
       all_trades.append(t)
     print('DONE',round(time.monotonic()-now,2),'sec',flush=True)
    except Exception as e:
     errors.append(dict(dataset=dataset,symbol=sym,strategy=strategy,status='error',reason=repr(e)));print('ERROR',repr(e),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False)
    (OUT/'errors.json').write_text(json.dumps(errors,indent=2))
    (OUT/'full_prefix_checks.json').write_text(json.dumps(extra,indent=2))
    if all_trades:pd.concat(all_trades,ignore_index=True).to_csv(OUT/'trades.csv',index=False)
 s=pd.DataFrame(rows)
 # All 54 planned test cells count in multiplicity, including missing/failed cells.
 ix=s.index[(s.epoch=='test') & s.control_p.notna()]
 rejected={i:False for i in ix};cont=True
 for k,i in enumerate(s.loc[ix].sort_values('control_p').index):
  cont=cont and bool(s.at[i,'control_p']<=.05/(54-k));rejected[i]=cont
 s['holm_pass']=False
 for i,v in rejected.items():s.at[i,'holm_pass']=v
 s.to_csv(OUT/'summary.csv',index=False)
 t=pd.concat(all_trades,ignore_index=True)
 detail=[]
 for keys,g in t.groupby(['dataset','symbol','strategy','epoch','side']):
  detail.append(dict(zip(['dataset','symbol','strategy','epoch','side'],keys))|summarize(g))
 pd.DataFrame(detail).to_csv(OUT/'by_side.csv',index=False)
 yearly=t.assign(year=t.entry_ts.dt.year).groupby(['dataset','symbol','strategy','epoch','year']).net_R.agg(['count','mean','sum'])
 yearly.to_csv(OUT/'by_year.csv')
 print(s[(s.epoch=='test')][['dataset','symbol','strategy','n','mean_R','mean_bp','stress_R','holm_pass']].to_string(index=False),flush=True)
if __name__=='__main__':main()
