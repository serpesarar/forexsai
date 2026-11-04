"""Verify upstream source against Git tree objects and retain a compact snapshot."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
from data_audit import HERE
UP=HERE/'upstream'
paths=['LICENSE','pyproject.toml']+[str(p.relative_to(UP)) for p in UP.glob('agent/backtest/**/*.py')]+[str(p.relative_to(UP)) for p in UP.glob('agent/src/skills/*/example_signal_engine.py')]
manifest=[]
for rel in paths:
 p=UP/rel;blob=p.read_bytes();actual=hashlib.sha1(f'blob {len(blob)}\0'.encode()+blob).hexdigest()
 tree=subprocess.check_output(['git','-C',str(UP),'ls-tree','HEAD','--',rel],text=True).split()
 expected=tree[2]
 assert actual==expected, f'modified upstream file: {rel}'
 manifest.append(dict(path=rel,git_blob=actual,sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)))
with tarfile.open(HERE/'source_snapshot.tar.gz','w:gz') as out:
 for rel in paths:out.add(UP/rel,arcname=rel)
(HERE/'results/source_manifest.json').write_text(json.dumps(manifest,indent=2))
reasons={
 'technical-basic':'performance: unmodified default; long XAU/OIL missing volume',
 'candlestick':'performance: unmodified default',
 'ichimoku':'performance: unmodified default; target=0 closes position',
 'volatility':'performance: unmodified default',
 'seasonal':'performance: unmodified default; UTC calendar',
 'harmonic':'performance: built-in fallback; right-confirmation audited',
 'elliott-wave':'performance: right-confirmation audited',
 'cross-market-strategy':'REJECTED: future-dependent weights; unrecognized CFD symbols route to a_share',
 'minute-analysis':'analysis-only: no SignalEngine',
 'event-driven':'unsupported: no point-in-time historical event_score',
 'fundamental-filter':'unsupported: CFD symbols lack stock PE/PB/ROE statements',
 'options-strategy':'unsupported: no historical options chain/contract/fills',
 'pair-trading':'not scored: no preregistered pair/hedge; default does not evaluate all 4 symbols',
 'multi-factor':'not scored: cross-sectional allocation; default top_n=5 >= universe=4; not a single-symbol directional engine',
 'smc':'not executed: optional smartmoneyconcepts missing; retrospective BOS/FVG assignment needs separate PIT audit',
 'chanlun':'not executed: optional czsc missing; separate incremental detector dependency',
}
items=[]
for name,reason in reasons.items():items.append(dict(example=name,status=reason))
(HERE/'results/example_inventory.json').write_text(json.dumps(items,indent=2))
print(f'{len(manifest)} source files verified; 16 examples inventoried')
