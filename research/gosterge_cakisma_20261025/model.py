"""Tüm-gösterge modeli (PROTOCOL §7.10): HistGradientBoosting, KEŞİF'te eğit → DOĞRULAMA'da iterasyon → KASA'da oku."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

import config as C
import data
import engine as E
import indicators

MAX_TRAIN = 250_000
TOP_FRAC = 0.10


def _features(book) -> np.ndarray:
    f = [book.feats[k] for k in sorted(book.feats)] + [book.states[k].astype(np.float32) for k in sorted(book.states)]
    return np.column_stack(f).astype(np.float32)


def _bucket_rate(y, b, train):
    rate = pd.Series(y[train]).groupby(b[train]).mean()
    return pd.Series(b).map(rate).fillna(y[train].mean()).values


def _fit(F, y, tr, va, rng):
    idx = np.flatnonzero(tr)
    if len(idx) > MAX_TRAIN:
        idx = np.sort(rng.choice(idx, MAX_TRAIN, replace=False))
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=200,
                                         l2_regularization=1.0, early_stopping=False, random_state=C.SEED)
    clf.fit(F[idx], y[idx])
    vidx = np.flatnonzero(va)
    best, best_it = -1.0, 1
    for it, p in enumerate(clf.staged_predict_proba(F[vidx]), 1):
        if it % 10 == 0:
            auc = roc_auc_score(y[vidx], p[:, 1])
            if auc > best:
                best, best_it = auc, it
    return clf, best_it, best


def _staged(clf, X, it):
    for k, p in enumerate(clf.staged_predict_proba(X), 1):
        if k == it:
            return p[:, 1]
    return clf.predict_proba(X)[:, 1]


def run_h(d, tf, h, F, cost_px, rng) -> dict:
    L = E.labels(d, data.bucket(d, tf), h, cost_px)
    y = (L["r"] > 0).astype(np.int8)
    sp, v = L["split"], L["valid"]
    tr, va, te = (sp == 0) & v, (sp == 1) & v, (sp == 2) & v
    if min(tr.sum(), va.sum(), te.sum()) < 200:
        return dict(h=h, olculemez=True, n_train=int(tr.sum()), n_val=int(va.sum()), n_test=int(te.sum()))
    clf, it, auc_val = _fit(F, y, tr, va, rng)
    tidx = np.flatnonzero(te)
    p = _staged(clf, F[tidx], it)
    base_score = _bucket_rate(y.astype(float), data.bucket(d, tf), tr)[tidx]
    auc_m, auc_b = roc_auc_score(y[tidx], p), roc_auc_score(y[tidx], base_score)
    conf = np.abs(p - 0.5)
    top = conf >= np.quantile(conf, 1 - TOP_FRAC)
    sel = tidx[top]
    dirn = np.where(p[top] > 0.5, 1, -1)
    hit = np.mean((L["r"][sel] * dirn) > 0)
    base = np.mean(np.where(dirn > 0, L["pu"][sel], L["pd"][sel]))
    thin = sel[np.r_[True, np.diff(sel) >= h]] if h > 1 else sel        # bağımsız karar sayısı (yaklaşık)
    return dict(h=h, best_iter=it, auc_val=round(auc_val, 4), auc_test=round(auc_m, 4), auc_test_base=round(auc_b, 4),
                auc_lift=round(auc_m - auc_b, 4), top10_n=int(top.sum()), top10_n_indep=int(len(thin)),
                top10_hit=round(float(hit), 4), top10_base=round(float(base), 4), top10_lift=round(float(hit - base), 4),
                top10_ret_bp=round(float(np.mean(L["r"][sel] * dirn) * 1e4), 3), cost_bp=round(float(L["cost"][2] * 1e4), 3))


def run_cell(sym: str, tf: str) -> list[dict]:
    d = data.load(sym, tf)
    F = _features(indicators.compute(d, tf))
    rng = np.random.default_rng(C.SEED)
    rows = []
    for h in C.HORIZONS:
        r = run_h(d, tf, h, F, C.SPREAD[sym], rng)
        rows.append(r)
        if r.get("olculemez"):
            print(f"  model {sym} {tf} h={h}: ölçülemez (n eğitim/doğr./kasa {r['n_train']}/{r['n_val']}/{r['n_test']})")
        else:
            print(f"  model {sym} {tf} h={h}: AUC {r['auc_test']} (taban {r['auc_test_base']}), "
                  f"en emin %10 isabet {r['top10_hit']} vs {r['top10_base']}", flush=True)
    out = C.RES / sym / tf
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "model.csv", index=False)
    json.dump(rows, open(out / "model.json", "w"), indent=1)
    return rows
