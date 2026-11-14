"""Faz 5 seçim (KEŞİF, ön-kayıtlı ölçüt) + DOĞRULAMA (yalnız seçilenler) + deneme sayacı.

python src/faz5_validate.py → results/faz5_secilen.csv, results/faz5_dogrulama.csv, results/deneme_sayaci.csv
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import atlas as A
import core as C

RES = C.H / 'results'
MAX_SEL = 30
MAX_PER_FAMILY = 5
MIN_FAZLA = 0.01


def thresholds() -> dict:
    out = {}
    for name in ('family', 'members', 'reaction', 'singles', 'combos'):
        mx, mx100 = [], []
        for s in range(1, 11):
            d = pd.read_parquet(RES / f'atlas_mart{s}/{name}.parquet')
            d = d[d.donem == 'K']
            mx.append(d.t.abs().max())
            mx100.append(d[d.n_indep >= 100].t.abs().max())
        out[name] = {'tum': float(np.nanmax(mx)), 'indep100': float(np.nanmax(mx100)), 'tekrarlar_indep100': [round(x, 2) for x in mx100]}
    return out


def family_of(cell: str) -> str:
    first = cell.split(' & ')[0]
    return first.split('#')[0].split('==')[0]


def counter(th: dict) -> pd.DataFrame:
    rows = []
    for name in ('family', 'members', 'reaction', 'singles', 'combos'):
        d = pd.read_parquet(RES / f'atlas_real/{name}.parquet')
        d = d.assign(atlas=name, T_star=th[name]['indep100'])
        rows.append(d)
    out = pd.concat(rows, ignore_index=True)
    out['deneme_no'] = np.arange(1, len(out) + 1)
    return out


def main() -> None:
    th = thresholds()
    cnt = counter(th)
    cnt.to_csv(RES / 'deneme_sayaci.csv', index=False)
    s = pd.read_parquet(RES / 'atlas_real/singles.parquet')
    c = pd.read_parquet(RES / 'atlas_real/combos.parquet')
    cand = []
    for d, T in ((s, th['singles']['indep100']), (c, th['combos']['indep100'])):
        ok = (d.donem == 'K') & (d.t.abs() > T) & d.same_sign & (d.n_indep >= 100) & (d.fazla.abs() >= MIN_FAZLA)
        cand.append(d[ok])
    cand = pd.concat(cand, ignore_index=True)
    cand['abst'] = cand.t.abs()
    cand['aile'] = cand.kosul.map(family_of)
    cand = cand.sort_values('abst', ascending=False)
    sel = cand.groupby(['aile']).head(MAX_PER_FAMILY).head(MAX_SEL).reset_index(drop=True)
    sel.to_csv(RES / 'faz5_secilen.csv', index=False)
    # DOĞRULAMA
    run = A.Run('real')
    fl = A.family_levels(run)
    Cm = A.conditions(run, fl)
    res = A.label_residuals(run)
    rows = []
    for _, r in sel.iterrows():
        parts = r.kosul.split(' & ')
        m = np.ones(len(Cm), bool)
        for p in parts:
            m &= Cm[p].to_numpy()
        cell = pd.DataFrame({r.kosul: m})
        for per in ('D',):
            v = A.scan_cells(run, cell, {r.etiket: res[r.etiket]}, per)
            if len(v):
                x = v.iloc[0].to_dict()
                x.update({'fazla_K': r.fazla, 't_K': r.t,
                          'gecti': bool(np.sign(x['fazla']) == np.sign(r.fazla) and abs(x['t']) >= 2.0
                                        and abs(x['fazla']) >= 0.5 * abs(r.fazla))})
                rows.append(x)
    val = pd.DataFrame(rows)
    val.to_csv(RES / 'faz5_dogrulama.csv', index=False)
    summ = {'esikler': th, 'aday_sayisi': int(len(cand)), 'secilen': int(len(sel)),
            'dogrulamayi_gecen': int(val.gecti.sum()) if len(val) else 0, 'toplam_deneme': int(len(cnt))}
    (RES / 'faz5_ozet.json').write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps(summ, indent=1, default=float))
    pd.set_option('display.width', 250)
    print(val[['kosul', 'etiket', 'n', 'n_indep', 'fazla_K', 't_K', 'fazla', 't', 'same_sign', 'gecti']].round(4).to_string())


if __name__ == '__main__':
    main()
