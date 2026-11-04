"""Run the original upstream ForexEngine on local CFD frames with explicit specs.

Overrides only cost/quantity units unsupported by the upstream FX pair defaults.
Not a go-live card; independent smoke of the original execution/artifact pipeline.
"""
import contextlib
from dataclasses import asdict
import io
import json
import socket
import sys
from pathlib import Path
from data_audit import HERE, SYMBOLS, SPREAD, recent, aggregate
from causality import load_engine
sys.path.insert(0,str(HERE/'runtime_deps'))
sys.path.insert(0,str(HERE/'upstream/agent'))
from backtest.engines.forex import ForexEngine

class LocalCFD(ForexEngine):
 def round_size(self, raw_size, price):return max(0.,float(raw_size))
 def apply_slippage_for_symbol(self, symbol, price, direction):return price+direction*.6*SPREAD[symbol]

class MemoryLoader:
 name='forexsai_local_broker_cache'
 def __init__(self,sym,frame):self.sym=sym;self.frame=frame
 def fetch(self,*a,**k):return {self.sym:self.frame.copy()}

def main():
 socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline native smoke: networking denied'))
 results=[]
 for sym in SYMBOLS:
  d=aggregate(recent(sym),5).iloc[-800:].copy()
  d.index=d.pop('start_ts')
  run_dir=HERE/'results/native'/sym.replace('.','_')
  (run_dir/'code').mkdir(parents=True,exist_ok=True)
  src=HERE/'upstream/agent/src/skills/technical-basic/example_signal_engine.py'
  (run_dir/'code/signal_engine.py').write_text(src.read_text())
  config=dict(codes=[sym],start_date=str(d.index.min().date()),end_date=str(d.index.max().date()),interval='5m',source='local',initial_cash=1_000_000,leverage=1,swap_enabled=False,position_adjustment='hold')
  (run_dir/'config.json').write_text(json.dumps(config,indent=2))
  engine=LocalCFD(config)
  try:
   log=io.StringIO()
   with contextlib.redirect_stdout(log):metrics=engine.run_backtest(config,MemoryLoader(sym,d),load_engine('technical-basic'),run_dir,bars_per_year=252*24*12)
   assert len(engine.trades)>0, 'No trades: execution smoke failed'
   (run_dir/'stdout.json').write_text(log.getvalue())
   results.append(dict(symbol=sym,passed=True,bars=len(d),trades=len(engine.trades),fills=len(engine.fill_records),metrics=metrics))
  except Exception as exc:results.append(dict(symbol=sym,passed=False,error=repr(exc)))
  print(sym,results[-1]['passed'],results[-1].get('error',''),flush=True)
 (HERE/'results/native_smoke.json').write_text(json.dumps(results,indent=2,default=str))
if __name__=='__main__':main()
