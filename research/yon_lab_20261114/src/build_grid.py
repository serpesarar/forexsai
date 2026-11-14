"""Faz 2-3: bir fiyat yolu (gerçek veya martingal sentetik) için ızgara + NOM özellikleri + referanslar + ek durumlar +
etiketler + ilk-geçiş tabloları. python src/build_grid.py real | mart <seed>  →  data/run_<etiket>/"""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

import core as C
import extras as X
import refs as R

OUT = C.H / 'data'


def build(b: pd.DataFrame, tag: str) -> None:
    t0 = time.time()
    d = OUT / f'run_{tag}'
    d.mkdir(parents=True, exist_ok=True)
    mac, cal = C.load_macro()
    td, i1 = C.grid(b)
    F = C.nom_features(b, td, mac, cal)
    print(tag, 'feat', len(td), round(time.time() - t0), flush=True)
    a15, a1 = F._atr_M15.to_numpy(), F._atr_H1.to_numpy()
    lab = pd.DataFrame(C.dir_labels(b, td, i1))
    lab['sym_1'] = C.sym_race(b, td, i1, a15, 60, 1.0)
    lab['t'] = td
    lab['i1'] = i1
    lab['price'] = b.close.to_numpy()[i1]
    lab['atr15'], lab['atr1'] = a15, a1
    lab['period'] = C.period(td)
    lab['day'] = td // 86400
    ret15 = F.ret15_atr.to_numpy() if 'ret15_atr' in F else np.zeros(len(td))
    lab['ret15'] = ret15
    lab['volr'] = F.H1_atr_ratio.to_numpy()
    Rf = R.build_refs(b, td, i1)
    print(tag, 'refs', Rf.shape, round(time.time() - t0), flush=True)
    Xf = X.build_extras(b, td)
    print(tag, 'extras', Xf.shape, round(time.time() - t0), flush=True)
    FU, FD = C.first_hit_tables(b, td, i1, a1)
    print(tag, 'FU/FD', round(time.time() - t0), flush=True)
    F.drop(columns=[c for c in F.columns if c.startswith('_')]).to_parquet(d / 'features.parquet', index=False)
    lab.to_parquet(d / 'labels.parquet', index=False)
    Rf.astype('float32').to_parquet(d / 'refs.parquet', index=False)
    Xf.to_parquet(d / 'extras.parquet', index=False)
    np.savez_compressed(d / 'fh.npz', FU=FU, FD=FD)
    print(tag, 'bitti', round(time.time() - t0), flush=True)


if __name__ == '__main__':
    b = C.load_ndx()
    if sys.argv[1] == 'real':
        build(b, 'real')
    else:
        seed = int(sys.argv[2])
        build(C.martingale_path(b, seed), f'mart{seed}')
