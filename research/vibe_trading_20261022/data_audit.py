"""Read-only audit and deterministic local OHLCV adapters."""
from pathlib import Path
import sys
import hashlib
import json
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi.data import normalize_snapshot_clock
HERE = Path(__file__).resolve().parent
SYMBOLS = ['NDX.INDX','GDAXI.INDX','XAUUSD','USOIL.FOREX']
LONG = dict(zip(SYMBOLS, ['research/ndx_gate_forge/data/long_1h_utc.parquet','research/ndx_gate_forge/data/dax_1h.parquet','research/pinbar_20261010/data/XAUUSD_1h.parquet','research/pinbar_20261010/data/USOIL_1h.parquet']))
SPREAD = dict(zip(SYMBOLS, [1.5,1.5,.25,.03]))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def recent(sym):
 p=ROOT/'output/islem_otopsi/_cache'/f'{sym.replace(".","_")}_1m_raw.parquet'
 d=normalize_snapshot_clock(pd.read_parquet(p)).iloc[:-1].copy()
 d.index.name='ts'
 return d

def aggregate(d, minutes):
 rule=f'{minutes}min'
 a=d.resample(rule,closed='left',label='right',origin='epoch').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
 counts=d.close.resample(rule,closed='left',label='right',origin='epoch').count()
 a=a.loc[counts==minutes].dropna()
 a['start_ts']=a.index-pd.Timedelta(minutes=minutes)
 return a

def long(sym):
 d=pd.read_parquet(ROOT/LONG[sym]);d['ts']=pd.to_datetime(d.ts,utc=True)
 if 'src' in d: d=d[d.src=='broker'].copy()
 if sym=='GDAXI.INDX':d=d[d.ts>=pd.Timestamp('2019-01-01',tz='UTC')].copy()
 d=d.sort_values('ts').drop_duplicates('ts').set_index('ts')
 d['start_ts']=d.index
 d.index=d.index+pd.Timedelta(hours=1)
 return d.iloc[:-1].copy()

def audit():
 out=[]
 for sym in SYMBOLS:
  rawpath=ROOT/'output/islem_otopsi/_cache'/f'{sym.replace(".","_")}_1m_raw.parquet'
  raw=pd.read_parquet(rawpath); r=recent(sym)
  for name,d,p in [('recent_m1',r,rawpath),('recent_5m',aggregate(r,5),rawpath),('long_1h',long(sym),ROOT/LONG[sym])]:
   delta=d.index.to_series().diff().dt.total_seconds()
   bad=(d.high<d[['open','close','low']].max(axis=1))|(d.low>d[['open','close','high']].min(axis=1))|(d[['open','high','low','close']]<=0).any(axis=1)
   out.append(dict(symbol=sym,dataset=name,rows=len(d),start=str(d.index.min()),end=str(d.index.max()),source=str(p.relative_to(ROOT)),source_sha256=sha(p),duplicates=int(d.index.duplicated().sum()),invalid_ohlc=int(bad.sum()),median_interval_seconds=float(delta.median()),gaps_over_3_intervals=int((delta>3*delta.median()).sum()),volume_available='volume' in d,raw_rows=len(raw),spread_assumed=SPREAD[sym],clock_rule='existing normalized UTC; old snapshots -3h; transition excluded' if name.startswith('recent') else 'existing audited UTC file; broker only'))
   assert d.index.is_monotonic_increasing and not d.index.duplicated().any()
   if bad.any(): raise ValueError(f'invalid OHLC {sym} {name}: {bad.sum()}')
 (HERE/'results/data_audit.json').write_text(json.dumps(out,indent=2))
 pd.DataFrame(out).to_csv(HERE/'results/data_audit.csv',index=False)
 print(pd.DataFrame(out)[['symbol','dataset','rows','start','end','invalid_ohlc']].to_string(index=False))
if __name__=='__main__':audit()
