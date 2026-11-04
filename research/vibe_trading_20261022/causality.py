"""Audit unmodified upstream signal engines without broker/network calls."""
from pathlib import Path
import importlib.util
import json
import sys
import socket
import numpy as np
import pandas as pd
from data_audit import HERE, SYMBOLS, recent, aggregate, sha
UP = HERE/'upstream'
STRATEGIES=['technical-basic','candlestick','ichimoku','volatility','seasonal','harmonic','elliott-wave']

def load_engine(name):
 p=UP/'agent/src/skills'/name/'example_signal_engine.py'
 spec=importlib.util.spec_from_file_location('vibe_'+name.replace('-','_'),p)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 engine=mod.SignalEngine()
 if name=='harmonic':
  assert not engine.use_pyharmonics, 'Protocol requires built-in detector'
 return engine

def generate(name,data):
 return load_engine(name).generate(data)

def check(name, data):
 full=generate(name,data); n=min(len(x) for x in data.values())
 cuts=set(np.linspace(160,n-1,12,dtype=int).tolist())
 if name in ('harmonic','elliott-wave'):
  for s in full.values(): cuts.update((np.flatnonzero(s.to_numpy()!=0)[:12]+1).tolist())
 errors=[];checks=0
 # All frames have same index in cross-market test, otherwise one-symbol call.
 for cut in sorted(cuts):
  if cut<1:continue
  pref={k:v.iloc[:cut].copy() for k,v in data.items()}
  got=generate(name,pref)
  for k,s in got.items():
   target=full[k].reindex(s.index)
   mismatch=~np.isclose(s.values,target.values,atol=1e-12,rtol=1e-12,equal_nan=True)
   checks+=len(s)
   if mismatch.any():errors.append(dict(type='prefix',symbol=k,cut=cut,mismatches=int(mismatch.sum()),first=str(s.index[np.flatnonzero(mismatch)[0]])))
 cut=n//2; changed={k:v.copy() for k,v in data.items()}
 for d in changed.values():
  d.iloc[cut:,d.columns.get_indexer(['open','high','low','close'])]*=5
  if 'volume' in d:d.iloc[cut:,d.columns.get_loc('volume')]*=3
 alt=generate(name,changed)
 for k,s in full.items():
  a=s.iloc[:cut];b=alt[k].reindex(a.index)
  mismatch=~np.isclose(a.values,b.values,atol=1e-12,rtol=1e-12,equal_nan=True)
  checks+=len(a)
  if mismatch.any(): errors.append(dict(type='future_mutation',symbol=k,cut=cut,mismatches=int(mismatch.sum()),first=str(a.index[np.flatnonzero(mismatch)[0]])))
 return dict(strategy=name,symbols=list(data),checks=checks,passed=not errors,errors=errors)

def main():
 # Deny networking even if an example unexpectedly calls an external API.
 socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline audit: networking denied'))
 rows=[]
 for name in STRATEGIES:
  for sym in SYMBOLS:
   d=aggregate(recent(sym),5).iloc[:800].drop(columns='start_ts')
   try:r=check(name,{sym:d})
   except Exception as e:r=dict(strategy=name,symbols=[sym],passed=False,error=repr(e))
   rows.append(r);print(name,sym,r['passed'],flush=True)
 # Intersect timestamps avoids confusing missing-calendar semantics with leakage.
 ds={s:aggregate(recent(s),5).drop(columns='start_ts') for s in SYMBOLS}
 idx=next(iter(ds.values())).index
 for d in ds.values():idx=idx.intersection(d.index)
 data={s:d.loc[idx[:800]] for s,d in ds.items()}
 rows.append(check('cross-market-strategy',data))
 manifest={'commit':'11cff3f3a2d89605c89148b03dcc2dd0fcfb60db','files':{str(p.relative_to(UP)):sha(p) for p in UP.glob('agent/src/skills/*/example_signal_engine.py')},'audits':rows}
 (HERE/'results/causality.json').write_text(json.dumps(manifest,indent=2))
 print('CROSS-MARKET',rows[-1],flush=True)
if __name__=='__main__':main()
