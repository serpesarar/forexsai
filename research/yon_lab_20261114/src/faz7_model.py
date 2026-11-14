"""Faz 7 — şansın üstüne öğren: LightGBM ikili, init_score = logit(eşlenmiş taban), NOM WF şeması (KÖR 2026 hariç),
isotonic; zorunlu yön testi (NOM ile aynı satırlarda) + P2 karıştırılmış etiket plasebosu.

python src/faz7_model.py → results/faz7_*.csv/json
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

import atlas as A
import core as C

RES = C.H / 'results'
NOM_OOS = C.REPO / 'research/nom_20261113/results/oos'
BLOCKS = [('2023H1', '2023-01-01', '2023-07-01'), ('2023H2', '2023-07-01', '2024-01-01'), ('2024H1', '2024-01-01', '2024-07-01'),
          ('2024H2', '2024-07-01', '2025-01-01'), ('2025H1', '2025-01-01', '2025-07-01'), ('2025H2', '2025-07-01', '2026-01-01')]
PARAMS = dict(objective='binary', learning_rate=0.03, num_leaves=15, max_depth=5, min_child_samples=300, feature_fraction=0.7,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbosity=-1, seed=7, num_threads=8)
XS = (0.03, 0.05, 0.08, 0.10)
EMB = 86400 + 4 * 3600
EPS = 1e-4


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def design(run: A.Run) -> tuple[pd.DataFrame, list[str]]:
    sel = pd.read_csv(RES / 'faz5_dogrulama.csv')
    sel = sel[sel.gecti]
    fl = A.family_levels(run)
    Cm = A.conditions(run, fl)
    X = run.F.copy()
    for c in run.X.columns:
        if not c.startswith('_'):
            X['x_' + c] = run.X[c].to_numpy()
    for k in sel.kosul:
        m = np.ones(len(Cm), bool)
        for p in k.split(' & '):
            m &= Cm[p].to_numpy()
        X['cell_' + k.replace(' ', '')[:60]] = m.astype(float)
    for f, (U, D) in fl.items():
        X[f'U_{f}'], X[f'D_{f}'] = U, D
    return X, list(X.columns)


def baseline(run: A.Run, y_up: np.ndarray, valid: np.ndarray, train: np.ndarray) -> np.ndarray:
    """Eşlenmiş taban: eğitim satırlarından NY saati × oynaklık ondalığı (yarıyıl yok — ileriye taşınabilir) oranı."""
    key = C.ny_hour(run.td) * 10 + np.searchsorted(run.edges, np.nan_to_num(run.lab.volr.to_numpy(), nan=1.0))
    m = train & valid
    g = pd.Series(y_up[m]).groupby(key[m]).agg(['sum', 'size'])
    glob = y_up[m].mean()
    p = ((g['sum'] + 50 * glob) / (g['size'] + 50)).reindex(key).to_numpy()
    return np.where(np.isfinite(p), p, glob)


def run_wf(run: A.Run, X: pd.DataFrame, lab: str, shuffle_seed: int | None = None) -> pd.DataFrame:
    y = run.lab[lab].to_numpy()
    valid = np.isfinite(y) & (y != 0)
    up = (y > 0).astype(float)
    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        days = np.unique(run.day)
        mp = dict(zip(days, rng.permutation(days)))
        # gün blokları arası karıştırma: her günün etiket dizisi başka bir günün dizisiyle (uzunluk kırpılarak) değişir
        df = pd.DataFrame({'d': run.day, 'u': up, 'v': valid})
        g = {d: s for d, s in df.groupby('d')}
        newu, newv = up.copy(), valid.copy()
        for d, s in g.items():
            src = g[mp[d]]
            k = min(len(s), len(src))
            newu[s.index[:k]] = src.u.to_numpy()[:k]
            newv[s.index[:k]] = src.v.to_numpy()[:k]
        up, valid = newu, newv
    out = []
    td = run.td
    for name, a, b in BLOCKS:
        A_, B_ = C.ts(a), C.ts(b)
        train = (td < A_ - EMB) & valid
        test = (td >= A_) & (td < B_) & valid & (run.per != 'X')
        if train.sum() < 5000 or test.sum() < 500:
            continue
        p0 = baseline(run, up, valid, train)
        tt = td[train]
        cut = np.quantile(tt, 0.8)
        fit = train & (td < cut - EMB)
        cal = train & (td >= cut)
        dtr = lgb.Dataset(X[fit], up[fit], init_score=logit(p0[fit]))
        dva = lgb.Dataset(X[cal], up[cal], init_score=logit(p0[cal]), reference=dtr)
        m = lgb.train(PARAMS, dtr, 1500, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
        raw_cal = 1 / (1 + np.exp(-(m.predict(X[cal], raw_score=True) + logit(p0[cal]))))
        iso = IsotonicRegression(out_of_bounds='clip').fit(raw_cal, up[cal])
        raw = 1 / (1 + np.exp(-(m.predict(X[test], raw_score=True) + logit(p0[test]))))
        out.append(pd.DataFrame({'t': td[test], 'y': up[test], 'p': iso.predict(raw), 'p0': p0[test], 'blok': name,
                                 'iters': m.best_iteration}))
    return pd.concat(out, ignore_index=True)


def forced_test(o: pd.DataFrame, pcol: str = 'p') -> list[dict]:
    rows = []
    for X_ in XS:
        d = o[(o[pcol] - 0.5).abs() >= X_]
        if len(d) == 0:
            rows.append({'X': X_, 'n': 0})
            continue
        hit = ((d[pcol] > 0.5) == (d.y == 1)).astype(float)
        day = d.t.to_numpy() // 86400
        rng = np.random.default_rng(1)
        u, inv = np.unique(day, return_inverse=True)
        s = np.bincount(inv, weights=hit.to_numpy())
        n = np.bincount(inv)
        bs = [s[ix].sum() / n[ix].sum() for ix in rng.integers(0, len(u), (1000, len(u)))]
        rows.append({'X': X_, 'n': int(len(d)), 'isabet': float(hit.mean()), 'lo95': float(np.quantile(bs, 0.025)),
                     'hi95': float(np.quantile(bs, 0.975))})
    return rows


def nom_compare(o: pd.DataFrame) -> pd.DataFrame:
    """NOM 1s 1/1 WF OOS: yön skoru = P(long TP) − P(short TP); aynı t'lerde sym_1 etiketiyle."""
    L = pd.read_parquet(NOM_OOS / '1h_long_1x1.parquet')[['t', 'p_tp']].rename(columns={'p_tp': 'pl'})
    S = pd.read_parquet(NOM_OOS / '1h_short_1x1.parquet')[['t', 'p_tp']].rename(columns={'p_tp': 'ps'})
    m = o.merge(L, on='t').merge(S, on='t')
    m['p_nom'] = 0.5 + (m.pl - m.ps) / 2          # ±X puan karşılaştırması için 0,5 merkezli
    return m


def main() -> None:
    run = A.Run('real')
    X, cols = design(run)
    summary = {}
    for lab in ('sym_1', 'dir_1h', 'dir_15m'):
        o = run_wf(run, X, lab)
        o.to_parquet(RES / f'faz7_oos_{lab}.parquet', index=False)
        auc = float(roc_auc_score(o.y, o.p))
        auc0 = float(roc_auc_score(o.y, o.p0))
        brier = float(((o.p - o.y) ** 2).mean())
        brier0 = float(((o.p0 - o.y) ** 2).mean())
        res = {'n': int(len(o)), 'auc': auc, 'auc_taban': auc0, 'brier_beceri_vs_taban': 1 - brier / brier0,
               'zorunlu_yon': forced_test(o), 'blok_auc': o.groupby('blok').apply(lambda g: roc_auc_score(g.y, g.p)).round(4).to_dict()}
        if lab == 'sym_1':
            m = nom_compare(o)
            res['nom_ayni_satir_n'] = int(len(m))
            res['nom_zorunlu_yon'] = forced_test(m.rename(columns={'p_nom': 'pn'}), 'pn')
            res['yeni_ayni_satir_zorunlu_yon'] = forced_test(m)
            res['nom_auc'] = float(roc_auc_score(m.y, m.p_nom))
            # P2
            pl = []
            for s in range(20):
                q = run_wf(run, X, lab, shuffle_seed=100 + s)
                pl.append(float(roc_auc_score(q.y, q.p)))
            res['P2_auc_p95'] = float(np.quantile(pl, 0.95))
            res['P2_auc'] = pl
        summary[lab] = res
        print(lab, json.dumps({k: v for k, v in res.items() if k != 'P2_auc'}, default=float)[:1800], flush=True)
    (RES / 'faz7_ozet.json').write_text(json.dumps(summary, indent=1, default=float))


if __name__ == '__main__':
    main()
