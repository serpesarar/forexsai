"""NOM Faz 4 — modelleme (WF OOS tahminleri) + tabanlar + kalibrasyon metrikleri.

python src/faz4_train.py main          → 40 hedef × 7 WF katı, results/oos/<hedef>.parquet + results/faz4_metrics.csv
python src/faz4_train.py compare       → yön-koşullu tek model, XGBoost, P2 karıştırılmış-etiket plasebosu
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import log_loss, roc_auc_score

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
sys.path.insert(0, str(H / 'src'))
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
import validation as V  # noqa: E402

DATA, RES = H / 'data', H / 'results'
OOS = RES / 'oos'
GRID_S = 900                     # eğitim/değerlendirme ızgarası (komşu 5 dk satırları neredeyse kopya)
PARAMS = dict(objective='multiclass', num_class=3, learning_rate=0.05, num_leaves=31, max_depth=6,
              min_child_samples=200, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0,
              verbosity=-1, seed=20261113, num_threads=8)
MAX_ROUNDS, EARLY = 1000, 100
EPS = 1e-6


def ny_hour(t: np.ndarray) -> np.ndarray:
    return pd.to_datetime(t, unit='s', utc=True).tz_convert('America/New_York').hour.to_numpy()


def load_horizon(hz: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    F = pd.read_parquet(DATA / 'features_v1.parquet')
    L = pd.read_parquet(DATA / f'labels_{hz}.parquet')
    L = L[L.t % GRID_S == 0].reset_index(drop=True)
    X = F.iloc[L.row.to_numpy()].reset_index(drop=True)
    return X, L, FE.feature_columns(F)


def climate(y_tr: np.ndarray, key_tr: np.ndarray, key_te: np.ndarray, prior_n: float = 50.0) -> np.ndarray:
    """Kova (ör. NY saati) iklim tabanı; az örnekli kovalar genel orana büzülür."""
    glob = np.bincount(y_tr, minlength=3) / len(y_tr)
    out = np.tile(glob, (len(key_te), 1))
    df = pd.DataFrame({'k': key_tr, 'y': y_tr})
    cnt = df.groupby('k').y.value_counts().unstack(fill_value=0).reindex(columns=[0, 1, 2], fill_value=0)
    tot = cnt.sum(1)
    prob = (cnt.to_numpy() + prior_n * glob) / (tot.to_numpy()[:, None] + prior_n)
    m = dict(zip(cnt.index, prob))
    for i, k in enumerate(key_te):
        if k in m:
            out[i] = m[k]
    return out


def rule_state(X: pd.DataFrame) -> np.ndarray:
    """Basit kural tabanı durumu: H1 EMA50 tarafı × M15 RSI14 kovası (<30, 30-70, >70)."""
    tr = np.sign(X['H1_ema50_dist'].fillna(0).to_numpy())
    r = X['M15_rsi14'].fillna(50).to_numpy()
    rb = np.where(r < 30, 0, np.where(r > 70, 2, 1))
    return (tr + 1) * 3 + rb


def calibrate(p_cal: np.ndarray, y_cal: np.ndarray, p_te: np.ndarray) -> tuple[np.ndarray, list]:
    out = np.empty_like(p_te)
    isos = []
    for k in range(3):
        iso = IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1)
        iso.fit(p_cal[:, k], (y_cal == k).astype(float))
        out[:, k] = iso.predict(p_te[:, k])
        isos.append(iso)
    out = np.clip(out, EPS, None)
    return out / out.sum(1, keepdims=True), isos


def brier(p: np.ndarray, y: np.ndarray) -> float:
    oh = np.eye(3)[y]
    return float(((p - oh) ** 2).sum(1).mean())


def fit_lgb(X: pd.DataFrame, y: np.ndarray, fit: np.ndarray, cal: np.ndarray, params=PARAMS):
    dtr = lgb.Dataset(X[fit], y[fit])
    dva = lgb.Dataset(X[cal], y[cal], reference=dtr)
    return lgb.train(params, dtr, MAX_ROUNDS, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(EARLY, verbose=False)])


def run_target(X: pd.DataFrame, L: pd.DataFrame, cols: list[str], hz: str, d: str, gk: str) -> tuple[pd.DataFrame, list]:
    y_all = L[f'{d}_{gk}_cls'].to_numpy()
    ok = y_all >= 0
    Xo, Lo = X[ok].reset_index(drop=True), L[ok].reset_index(drop=True)
    y = y_all[ok].astype(int)
    r = Lo[f'{d}_{gk}_r'].to_numpy()
    t = Lo.t.to_numpy()
    hr = ny_hour(t)
    rs = rule_state(Xo) * 100 + hr
    Xm = Xo[cols]
    rows, mets = [], []
    for fd in V.walk_forward(t, hz):
        trn = fd.fit | fd.cal
        mdl = fit_lgb(Xm, y, fd.fit, fd.cal)
        p_cal_raw = mdl.predict(Xm[fd.cal])
        p_te_raw = mdl.predict(Xm[fd.test])
        p_te, _ = calibrate(p_cal_raw, y[fd.cal], p_te_raw)
        p_clim = climate(y[trn], hr[trn], hr[fd.test])
        p_rule = climate(y[trn], rs[trn], rs[fd.test])
        r_sl = float(r[trn][y[trn] == 1].mean())
        r_to = float(r[trn][y[trn] == 2].mean())
        tp_r = float(gk.split('x')[0]) / float(gk.split('x')[1])
        yt = y[fd.test]
        df = pd.DataFrame({'t': t[fd.test], 'y': yt, 'r': r[fd.test], 'fold': fd.name,
                           'p_tp': p_te[:, 0], 'p_sl': p_te[:, 1], 'p_to': p_te[:, 2],
                           'p_tp_raw': p_te_raw[:, 0], 'c_tp': p_clim[:, 0], 'c_sl': p_clim[:, 1], 'c_to': p_clim[:, 2],
                           'u_tp': p_rule[:, 0], 'u_sl': p_rule[:, 1], 'u_to': p_rule[:, 2]})
        df['exp_r'] = df.p_tp * tp_r + df.p_sl * r_sl + df.p_to * r_to
        df['exp_r_clim'] = df.c_tp * tp_r + df.c_sl * r_sl + df.c_to * r_to
        rows.append(df)
        mets.append(metrics(df, hz, d, gk, fd.name, mdl.best_iteration))
    return pd.concat(rows, ignore_index=True), mets


def metrics(df: pd.DataFrame, hz: str, d: str, gk: str, fold: str, iters: int | None = None) -> dict:
    y = df.y.to_numpy()
    pm = df[['p_tp', 'p_sl', 'p_to']].to_numpy()
    pc = df[['c_tp', 'c_sl', 'c_to']].to_numpy()
    pu = df[['u_tp', 'u_sl', 'u_to']].to_numpy()
    b_m, b_c, b_u = brier(pm, y), brier(pc, y), brier(pu, y)
    l_m = log_loss(y, pm, labels=[0, 1, 2])
    l_c = log_loss(y, pc, labels=[0, 1, 2])
    tp = (y == 0).astype(int)
    auc = lambda s: float(roc_auc_score(tp, s)) if 0 < tp.sum() < len(tp) else np.nan
    return {'horizon': hz, 'dir': d, 'geom': gk, 'fold': fold, 'n': len(y), 'iters': iters,
            'brier_model': b_m, 'brier_clim': b_c, 'brier_rule': b_u, 'brier_skill_vs_clim': 1 - b_m / b_c,
            'brier_skill_rule_vs_clim': 1 - b_u / b_c, 'logloss_skill_vs_clim': 1 - l_m / l_c,
            'auc_tp_model': auc(df.p_tp), 'auc_tp_clim': auc(df.c_tp), 'auc_tp_rule': auc(df.u_tp),
            'p_tp_mean': float(df.p_tp.mean()), 'tp_rate': float(tp.mean())}


def main() -> None:
    OOS.mkdir(parents=True, exist_ok=True)
    allm = []
    t0 = time.time()
    for hz in LB.HORIZONS:
        X, L, cols = load_horizon(hz)
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                df, mets = run_target(X, L, cols, hz, d, gk)
                df.to_parquet(OOS / f'{hz}_{d}_{gk}.parquet', index=False)
                allm += mets
                pooled = metrics(df, hz, d, gk, 'POOLED')
                allm.append(pooled)
                print(hz, d, gk, 'bss', round(pooled['brier_skill_vs_clim'], 4), 'lls',
                      round(pooled['logloss_skill_vs_clim'], 4), 'auc', round(pooled['auc_tp_model'], 4),
                      'clim', round(pooled['auc_tp_clim'], 4), round(time.time() - t0), flush=True)
                pd.DataFrame(allm).to_csv(RES / 'faz4_metrics.csv', index=False)


def compare() -> None:
    """(a) yön-koşullu tek model (1s 1,5/1), (b) XGBoost (1s 1/1 long), (c) P2 plasebo (1s 1/1 long)."""
    import xgboost as xgb
    out = {}
    X, L, cols = load_horizon('1h')
    # (a)
    gk = '1.5x1'
    parts = []
    for d, s in (('long', 1.0), ('short', -1.0)):
        y = L[f'{d}_{gk}_cls'].to_numpy()
        ok = y >= 0
        Z = X[ok][cols].reset_index(drop=True).copy()
        Z['dir_flag'] = s
        parts.append((Z, y[ok].astype(int), L.t.to_numpy()[ok], d))
    Zall = pd.concat([p[0] for p in parts], ignore_index=True)
    yall = np.concatenate([p[1] for p in parts])
    tall = np.concatenate([p[2] for p in parts])
    dall = np.concatenate([[p[3]] * len(p[1]) for p in parts])
    res = []
    for fd in V.walk_forward(tall, '1h'):
        mdl = fit_lgb(Zall, yall, fd.fit, fd.cal)
        pc, _ = calibrate(mdl.predict(Zall[fd.cal]), yall[fd.cal], mdl.predict(Zall[fd.test]))
        for d in ('long', 'short'):
            msk = dall[fd.test] == d
            res.append({'fold': fd.name, 'dir': d, 'brier': brier(pc[msk], yall[fd.test][msk])})
    joint = pd.DataFrame(res).groupby('dir').brier.mean().to_dict()
    sep = {}
    for d in ('long', 'short'):
        o = pd.read_parquet(OOS / f'1h_{d}_{gk}.parquet')
        sep[d] = float(o.groupby('fold').apply(lambda g: brier(g[['p_tp', 'p_sl', 'p_to']].to_numpy(), g.y.to_numpy())).mean())
    out['direction_conditional_vs_separate_brier'] = {'joint': joint, 'separate': sep}
    # (b) XGBoost
    gk = '1x1'
    y = L[f'long_{gk}_cls'].to_numpy()
    ok = y >= 0
    Xo, yo, to = X[ok][cols].reset_index(drop=True), y[ok].astype(int), L.t.to_numpy()[ok]
    xb = []
    for fd in V.walk_forward(to, '1h'):
        m = xgb.XGBClassifier(n_estimators=1000, learning_rate=0.05, max_depth=6, subsample=0.8,
                              colsample_bytree=0.7, min_child_weight=50, reg_lambda=5, objective='multi:softprob',
                              tree_method='hist', n_jobs=8, early_stopping_rounds=EARLY, eval_metric='mlogloss')
        m.fit(Xo[fd.fit], yo[fd.fit], eval_set=[(Xo[fd.cal], yo[fd.cal])], verbose=False)
        pc, _ = calibrate(m.predict_proba(Xo[fd.cal]), yo[fd.cal], m.predict_proba(Xo[fd.test]))
        xb.append(brier(pc, yo[fd.test]))
    o = pd.read_parquet(OOS / f'1h_long_{gk}.parquet')
    lg = o.groupby('fold').apply(lambda g: brier(g[['p_tp', 'p_sl', 'p_to']].to_numpy(), g.y.to_numpy()))
    cl = o.groupby('fold').apply(lambda g: brier(g[['c_tp', 'c_sl', 'c_to']].to_numpy(), g.y.to_numpy()))
    out['xgb_vs_lgb_brier_per_fold'] = {'xgb': xb, 'lgb': lg.tolist(), 'clim': cl.tolist()}
    # (c) P2: gün-blok karıştırılmış etiket (3 son kat, 20 tekrar, 300 tur sabit)
    rng = np.random.default_rng(3)
    day = to // 86400
    folds = [f for f in V.walk_forward(to, '1h') if f.name in ('2024H2', '2025H1', '2025H2')]
    real, plac = [], []
    for fd in folds:
        p = dict(PARAMS)
        mdl = lgb.train(p, lgb.Dataset(Xo[fd.fit], yo[fd.fit]), 300)
        pc, _ = calibrate(mdl.predict(Xo[fd.cal]), yo[fd.cal], mdl.predict(Xo[fd.test]))
        clim = climate(yo[fd.fit | fd.cal], ny_hour(to[fd.fit | fd.cal]), ny_hour(to[fd.test]))
        real.append(1 - brier(pc, yo[fd.test]) / brier(clim, yo[fd.test]))
    for rep in range(20):
        ud = np.unique(day)
        perm = dict(zip(ud, rng.permutation(ud)))
        # gün içindeki sıra korunarak etiket blokları başka günlere taşınır
        ys = yo.copy()
        by_day = pd.Series(np.arange(len(yo))).groupby(day).apply(list).to_dict()
        for a, b in perm.items():
            ia, ib = by_day[a], by_day[b]
            k = min(len(ia), len(ib))
            ys[ia[:k]] = yo[ib[:k]]
        sk = []
        for fd in folds:
            mdl = lgb.train(PARAMS, lgb.Dataset(Xo[fd.fit], ys[fd.fit]), 300)
            pc, _ = calibrate(mdl.predict(Xo[fd.cal]), ys[fd.cal], mdl.predict(Xo[fd.test]))
            clim = climate(ys[fd.fit | fd.cal], ny_hour(to[fd.fit | fd.cal]), ny_hour(to[fd.test]))
            sk.append(1 - brier(pc, yo[fd.test]) / brier(clim, yo[fd.test]))
        plac.append(float(np.mean(sk)))
        print('P2 rep', rep, plac[-1], flush=True)
    out['P2_shuffled_label_placebo'] = {'real_mean_bss_vs_hourclim': float(np.mean(real)), 'real_per_fold': real,
                                        'placebo_p95': float(np.quantile(plac, .95)), 'placebo': plac}
    (RES / 'faz4_compare.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    {'main': main, 'compare': compare}[sys.argv[1]]()
