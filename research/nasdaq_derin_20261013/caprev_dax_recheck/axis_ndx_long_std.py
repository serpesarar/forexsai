"""NDX long_1h: ay bazında, hangi etiket kayması nakit 16:00 kapanışıyla EN KARARLI (en düşük std) farkı veriyor?
Sabit baz farkını (vadeli-nakit) ortadan kaldırdığı için |fark| oylamasından sağlam. Kayma +60 = etiket 60 dk geç."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge")
from long_data import load_long, macro
d = load_long("1h"); ny = d.ts.dt.tz_convert("America/New_York")
d["date"] = pd.to_datetime(ny.dt.date.values); d["m"] = (ny.dt.hour * 60 + ny.dt.minute).values
p = d.pivot_table(index="date", columns="m", values="close", aggfunc="last")
cash = macro().NDXCASH_close.reindex(p.index)
e = pd.DataFrame({s: (p[900 + s] - cash) / cash * 1e4 for s in (-60, 0, 60)}).dropna()
g = e.groupby(e.index.strftime("%Y-%m")).std()
best = g.idxmin(axis=1)
print("std(bp) en düşük kayma — ay sayısı:", best.value_counts().to_dict())
print(pd.concat([g.round(1), best.rename("en_iyi")], axis=1)[best != 0].to_string())
