"""Plasebo: pnl_r sembol içinde karıştırılır, arama aynen tekrarlanır → 'iki yönde geçen' kural sayısının tesadüf dağılımı."""
import re, sys
import numpy as np, pandas as pd
sys.path.insert(0, '.'); sys.path.insert(0, '../..')
from analyze import independent, run

def key(s): return re.sub(r'[-\d.]+(?=\s|$)', '#', s)
def ok(x): return x[(x.sinama_R > 0) & (x.sinama_R > x.sinama_rastgele_R) & (x.sinama_engel >= 10) & (x.egitim_R > 0)]
def both(o):
    f, b = ok(run(o, True)), ok(run(o, False))
    kb = set(b.kapsam + '|' + b.kural.map(key))
    m = (f.kapsam + '|' + f.kural.map(key)).isin(kb)
    return int(m.sum()), f[m].groupby(f[m].kapsam.str.split().str[0]).size().to_dict()

d = pd.read_parquet('data/decisions.parquet')
o = independent(d[d.act == 'OPEN'])
print('gerçek:', both(o), flush=True)
rng = np.random.default_rng(7)
res = []
for i in range(10):
    p = o.copy()
    for sym, idx in p.groupby('symbol').groups.items():
        p.loc[idx, 'pnl_r'] = rng.permutation(p.loc[idx, 'pnl_r'].to_numpy())
    n, per = both(p); res.append(n); print('plasebo', i, n, per, flush=True)
print('plasebo medyan', np.median(res), 'max', max(res))
