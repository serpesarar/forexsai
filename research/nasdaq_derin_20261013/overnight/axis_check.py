"""Saat ekseni denetimi (getiriye bakmaz): en büyük medyan aralığın NY/Berlin saati + saat kapsamı."""
import sys, pandas as pd, numpy as np
R = '/Users/melihcanodacioglu/Desktop/panel/research'
sys.path.insert(0, R + '/ndx_gate_forge')
from long_data import load_long
b = pd.read_parquet(R + '/ndx_pattern_motifs/data/bars_1m.parquet')
ny = b.ts.dt.tz_convert('America/New_York')
b['m'] = ny.dt.strftime('%Y-%m'); b['hm'] = ny.dt.hour * 60 + ny.dt.minute; b['r'] = b.high - b.low
g = b.groupby(['m', 'hm']).r.median().reset_index()
pk = g.loc[g.groupby('m').r.idxmax()]
print('1m peak NY dakika / ay:'); print(' '.join(f"{m}:{h//60:02d}:{h%60:02d}" for m, h in zip(pk.m, pk.hm)))
for tf in ['1h', '30m']:
    d = load_long(tf); ny = d.ts.dt.tz_convert('America/New_York')
    d['y'] = ny.dt.year; d['hm'] = ny.dt.hour * 60 + ny.dt.minute; d['r'] = d.high - d.low
    g = d.groupby(['y', 'hm']).r.median().reset_index(); pk = g.loc[g.groupby('y').r.idxmax()]
    print(tf, 'peak NY / yıl:', ' '.join(f"{y}:{h//60:02d}:{h%60:02d}" for y, h in zip(pk.y, pk.hm)))
    print(tf, 'NY saat kapsamı (bar sayısı):', d.groupby(ny.dt.hour).size().to_dict())
for f in ['dax_1h', 'dax_30m']:
    d = pd.read_parquet(R + f'/ndx_gate_forge/data/{f}.parquet'); be = d.ts.dt.tz_convert('Europe/Berlin')
    d['y'] = be.dt.year; d['hm'] = be.dt.hour * 60 + be.dt.minute; d['r'] = d.high - d.low
    g = d.groupby(['y', 'hm']).r.median().reset_index(); pk = g.loc[g.groupby('y').r.idxmax()]
    print(f, 'peak Berlin / yıl:', ' '.join(f"{y}:{h//60:02d}:{h%60:02d}" for y, h in zip(pk.y, pk.hm)))
    cov = d[d.ts >= '2016-01-01'].groupby(be[d.ts >= '2016-01-01'].dt.hour).size().to_dict()
    print(f, 'Berlin saat kapsamı 2016+:', cov)
    yr = d.groupby(d.ts.dt.year).size().to_dict(); print(f, 'yıl başına bar:', yr)
