"""NOM Faz 5 — ekonomik test, stres, plasebo, bootstrap, dilimler, final test (tek kez), bot çapraz kontrolü,
üretim paketi.

python src/faz5_econ.py dev      → geliştirme WF ekonomisi + eşik seçimi (seçim blokları) + teyit
python src/faz5_econ.py final    → final test (KİLİT AÇILIR, tek kez) + bot çapraz kontrolü
python src/faz5_econ.py bundle   → üretim paketi (tüm veriyle yeniden eğitim, dev'de donmuş eşikler) + ACTIVE
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
sys.path.insert(0, str(H / 'src'))
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
from services.nom import model_store as MS  # noqa: E402
import faz4_train as T  # noqa: E402
import validation as V  # noqa: E402

DATA, RES = H / 'data', H / 'results'
OOS = RES / 'oos'
FIN = RES / 'final'
RULES = [('exp_r', x) for x in (0.0, 0.05, 0.10, 0.15, 0.20)] + [('p_tp', x) for x in (0.50, 0.55, 0.60, 0.65)]
MIN_INDEP = 30
NY = 'America/New_York'
FINAL_LOCK_FILE = RES / 'FINAL_OPENED.json'


def friction_r(hz: str, gk: str, rows: np.ndarray) -> np.ndarray:
    """Satır başına sürtünme (R): (giriş spread + 2 kayma) / SL mesafesi — 2× stres için ek maliyet."""
    F = pd.read_parquet(DATA / 'features_v1.parquet', columns=['_i0', f"_atr_{LB.HORIZONS[hz]['atr_tf']}"])
    m = pd.read_parquet(DATA / 'ndx_1m_v1.parquet', columns=['spr'])
    sl = float(gk.split('x')[1])
    i0 = F._i0.to_numpy()[rows]
    a = F.iloc[:, 1].to_numpy()[rows]
    return (m.spr.to_numpy()[i0] + 2 * LB.SLIP_PTS) / (sl * a)


def attach_rows(hz: str, df: pd.DataFrame) -> pd.DataFrame:
    L = pd.read_parquet(DATA / f'labels_{hz}.parquet', columns=['row', 't'])
    return df.merge(L, on='t', how='left')


def trade_stats(t: np.ndarray, r: np.ndarray, y: np.ndarray) -> dict:
    o = np.argsort(t)
    t, r, y = t[o], r[o], y[o]
    if len(r) == 0:
        return {'n': 0}
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, eq])[1:] - eq).max())
    loss = r < 0
    streak = mx = 0
    for v in loss:
        streak = streak + 1 if v else 0
        mx = max(mx, streak)
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    return {'n': int(len(r)), 'n_indep': V.independent_count(t), 'wr_tp': float((y == 0).mean()),
            'win_frac': float((r > 0).mean()), 'ev_r': float(r.mean()), 'pf': float(gp / gl) if gl > 0 else np.inf,
            'max_dd_r': dd, 'max_loss_streak': int(mx), 'sum_r': float(r.sum())}


def select_mask(df: pd.DataFrame, rule: tuple[str, float]) -> np.ndarray:
    k, x = rule
    if k == 'exp_r':
        return (df.exp_r >= x).to_numpy()
    return ((df.p_tp >= x) & (df.exp_r >= 0)).to_numpy()


def slices(df: pd.DataFrame, X: pd.DataFrame) -> dict:
    ny = pd.to_datetime(df.t, unit='s', utc=True).dt.tz_convert(NY)
    ev_day = np.zeros(len(df), bool)
    for c in ('FOMC', 'CPI', 'NFP'):
        a = X[f'min_to_{c}'].to_numpy()
        b = X[f'min_since_{c}'].to_numpy()
        ev_day |= (a <= 600) | (b <= 600)
    keys = {'yil': ny.dt.year.to_numpy(),
            'vix': np.where(X.mac_vix.to_numpy() >= 18.4, 'VIX>=18.4', 'VIX<18.4'),
            'rejim': np.where(X.H1_adx14.to_numpy() >= 25, 'trend', 'yatay'),
            'seans': np.array([FE.SESSION_PHASES[int(s)] for s in X.session_phase.fillna(0)]),
            'gun': ny.dt.dayofweek.to_numpy(), 'olay_gunu': np.where(ev_day, 'olay±10s', 'normal')}
    out = {}
    for name, k in keys.items():
        g = pd.DataFrame({'k': k, 'r': df.r.to_numpy()}).groupby('k').r.agg(['size', 'mean'])
        out[name] = {str(i): {'n': int(v['size']), 'ev_r': round(float(v['mean']), 4)} for i, v in g.iterrows()}
    return out


def calib_table(p: np.ndarray, y01: np.ndarray, nb: int = 10) -> list[dict]:
    q = np.unique(np.quantile(p, np.linspace(0, 1, nb + 1)))
    out = []
    for i in range(len(q) - 1):
        m = (p >= q[i]) & (p <= q[i + 1]) if i == len(q) - 2 else (p >= q[i]) & (p < q[i + 1])
        n = int(m.sum())
        if n == 0:
            continue
        k = y01[m].sum()
        ph = k / n
        z = 1.96
        den = 1 + z * z / n
        c = (ph + z * z / (2 * n)) / den
        h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
        out.append({'lo': float(q[i]), 'hi': float(q[i + 1]), 'n': n, 'pred': float(p[m].mean()),
                    'obs': float(ph), 'ci_lo': float(c - h), 'ci_hi': float(c + h)})
    return out


def r_bins(e: np.ndarray, r: np.ndarray, day: np.ndarray, nb: int = 10) -> list[dict]:
    q = np.unique(np.quantile(e, np.linspace(0, 1, nb + 1)))
    out = []
    for i in range(len(q) - 1):
        m = (e >= q[i]) & (e <= q[i + 1]) if i == len(q) - 2 else (e >= q[i]) & (e < q[i + 1])
        if m.sum() == 0:
            continue
        bs = V.day_block_bootstrap(r[m], day[m], n_boot=500)
        out.append({'lo': float(q[i]), 'hi': float(q[i + 1]), 'n': int(m.sum()), 'pred': float(e[m].mean()),
                    'obs': bs['ev'], 'ci_lo': bs['lo'], 'ci_hi': bs['hi']})
    return out


def evaluate_target(df: pd.DataFrame, hz: str, d: str, gk: str, X: pd.DataFrame, rule=None) -> dict:
    """df: OOS satırları (t, y, r, p_*, exp_r, fold, row). rule=None → seçim (dev), aksi hâlde verilen kural."""
    fr = friction_r(hz, gk, df.row.to_numpy())
    df = df.assign(r2=df.r.to_numpy() - fr, day=df.t.to_numpy() // 86400)
    res = {'target': f'{hz}_{d}_{gk}', 'base_ev_r': float(df.r.mean()), 'base_ev_r_2x': float(df.r2.mean()),
           'n_rows': len(df)}
    grid = []
    sel_blk = df.fold.isin(V.SELECT_BLOCKS).to_numpy() if rule is None else np.ones(len(df), bool)
    con_blk = df.fold.isin(V.CONFIRM_BLOCKS).to_numpy() if rule is None else np.ones(len(df), bool)
    for rl in (RULES if rule is None else [rule]):
        m = select_mask(df, rl)
        a = trade_stats(df.t.to_numpy()[m & sel_blk], df.r.to_numpy()[m & sel_blk], df.y.to_numpy()[m & sel_blk])
        b = trade_stats(df.t.to_numpy()[m & con_blk], df.r.to_numpy()[m & con_blk], df.y.to_numpy()[m & con_blk])
        grid.append({'rule': f'{rl[0]}>={rl[1]}', 'select': a, 'confirm': b, '_rl': rl})
    res['grid'] = [{k: v for k, v in g.items() if k != '_rl'} for g in grid]
    if rule is None:
        ok = [g for g in grid if g['select'].get('n_indep', 0) >= MIN_INDEP]
        best = max(ok, key=lambda g: g['select']['ev_r']) if ok else None
        chosen = best['_rl'] if best and best['select']['ev_r'] > 0 else None
    else:
        chosen = rule
    res['chosen_rule'] = None if chosen is None else list(chosen)
    if chosen is not None:
        m = select_mask(df, chosen)
        ev_blk = con_blk if rule is None else np.ones(len(df), bool)
        mm = m & ev_blk
        tt, rr, yy = df.t.to_numpy()[mm], df.r.to_numpy()[mm], df.y.to_numpy()[mm]
        res['eval_stats'] = trade_stats(tt, rr, yy)
        res['eval_stats_2x'] = trade_stats(tt, df.r2.to_numpy()[mm], yy)
        res['bootstrap'] = V.day_block_bootstrap(rr, tt // 86400)
        pool = ev_blk
        pl = V.hour_matched_placebo(tt, df.t.to_numpy()[pool], df.r.to_numpy()[pool], n_rep=500) if len(tt) \
            else {'p50': float('nan'), 'p95': float('nan')}
        res['placebo_P1'] = {'p50': pl['p50'], 'p95': pl['p95'], 'beats_p95': bool(rr.mean() > pl['p95']) if len(rr) else False}
        yrs = pd.to_datetime(tt, unit='s', utc=True).year
        ys = pd.Series(rr).groupby(yrs).mean()
        res['years_positive'] = f'{int((ys > 0).sum())}/{len(ys)}'
        res['by_year'] = {int(k): round(float(v), 4) for k, v in ys.items()}
        res['slices'] = slices(df[mm].reset_index(drop=True), X.iloc[np.where(mm)[0]].reset_index(drop=True))
        es, bs = res['eval_stats'], res['bootstrap']
        res['passes'] = bool(es.get('n_indep', 0) >= MIN_INDEP and es.get('ev_r', -1) > 0
                             and (bs.get('p_pos') or 0) >= 0.90 and res['eval_stats_2x'].get('ev_r', -1) > 0
                             and res['placebo_P1']['beats_p95'] and len(ys) and (ys > 0).mean() >= 2 / 3)
    else:
        res['passes'] = False
    res['calibration_p_tp'] = calib_table(df.p_tp.to_numpy(), (df.y.to_numpy() == 0).astype(float))
    res['calibration_p_tp_clim'] = calib_table(df.c_tp.to_numpy(), (df.y.to_numpy() == 0).astype(float))
    res['exp_r_bins'] = r_bins(df.exp_r.to_numpy(), df.r.to_numpy(), df.day.to_numpy())
    return res


def features_for(hz: str, df: pd.DataFrame) -> pd.DataFrame:
    F = pd.read_parquet(DATA / 'features_v1.parquet')
    return F.iloc[df.row.to_numpy()].reset_index(drop=True)


def dev() -> None:
    out = []
    for hz in LB.HORIZONS:
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                df = attach_rows(hz, pd.read_parquet(OOS / f'{hz}_{d}_{gk}.parquet'))
                X = features_for(hz, df)
                r = evaluate_target(df, hz, d, gk, X)
                out.append(r)
                print(r['target'], 'base', round(r['base_ev_r'], 3), 'rule', r['chosen_rule'],
                      'confirm', {k: round(v, 3) if isinstance(v, float) else v for k, v in r.get('eval_stats', {}).items()},
                      'pass', r['passes'], flush=True)
    (RES / 'faz5_dev.json').write_text(json.dumps(out, indent=1, default=float))


def train_final_models(hz: str, d: str, gk: str, X: pd.DataFrame, L: pd.DataFrame, cols: list[str],
                       final: bool) -> tuple:
    """final=True: eğitim = FINAL_START öncesi (dev), test = final dönem.
    final=False: üretim — tüm veri (dev + final), test yok."""
    y_all = L[f'{d}_{gk}_cls'].to_numpy()
    ok = y_all >= 0
    Xo, Lo = X[ok].reset_index(drop=True), L[ok].reset_index(drop=True)
    y = y_all[ok].astype(int)
    t = Lo.t.to_numpy()
    if final:
        fd = V.walk_forward(t, hz, final=True)[0]
        fit, cal, test = fd.fit, fd.cal, fd.test
    else:
        hs = V.HORIZON_S[hz]
        cut = np.quantile(t, 1 - V.CALIB_FRAC)
        fit = t < cut - hs - V.EMBARGO_S
        cal = t >= cut
        test = np.zeros(len(t), bool)
    mdl = T.fit_lgb(Xo[cols], y, fit, cal)
    p_cal = mdl.predict(Xo[cols][cal])
    _, isos = T.calibrate(p_cal, y[cal], p_cal[:5])
    r = Lo[f'{d}_{gk}_r'].to_numpy()
    trn = fit | cal
    stats = {'r_sl': float(r[trn][y[trn] == 1].mean()), 'r_to': float(r[trn][y[trn] == 2].mean()),
             'tp_r': float(gk.split('x')[0]) / float(gk.split('x')[1]),
             'base_p_tp': float((y[trn] == 0).mean()), 'base_ev_r': float(r[trn].mean()),
             'best_iter': int(mdl.best_iteration or 0), 'n_train': int(trn.sum())}
    return mdl, isos, stats, Xo, Lo, y, t, test, trn


def final() -> None:
    if FINAL_LOCK_FILE.exists() and (RES / 'faz5_final.json').exists():
        raise SystemExit('Final test ZATEN açıldı (FINAL_OPENED.json) — yeniden ayar yasak; sonuç dosyası: faz5_final.json')
    dev_res = {r['target']: r for r in json.loads((RES / 'faz5_dev.json').read_text())}
    FIN.mkdir(parents=True, exist_ok=True)
    prev = json.loads(FINAL_LOCK_FILE.read_text()) if FINAL_LOCK_FILE.exists() else None
    FINAL_LOCK_FILE.write_text(json.dumps({'opened_at': time.time(), 'note': 'tek seferlik açılış',
                                           'previous_attempt': prev and (prev | {
                                               'outcome': 'ilk hedefte KeyError (işlem yokken n_indep) — hiçbir final metriği '
                                                          'hesaplanmadan/görülmeden düştü; yalnız çökme düzeltildi, ayar değişmedi'})}))
    out = []
    models_1h = {}
    for hz in LB.HORIZONS:
        X, L, cols = T.load_horizon(hz)
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                mdl, isos, st, Xo, Lo, y, t, test, trn = train_final_models(hz, d, gk, X, L, cols, final=True)
                cal = MS.Calibrator.from_isotonic(isos)
                p = cal.apply(mdl.predict(Xo[cols][test]))
                hr = T.ny_hour(t)
                pc = T.climate(y[trn], hr[trn], hr[test])
                rs = T.rule_state(Xo) * 100 + hr
                pu = T.climate(y[trn], rs[trn], rs[test])
                df = pd.DataFrame({'t': t[test], 'y': y[test], 'r': Lo[f'{d}_{gk}_r'].to_numpy()[test], 'fold': 'FINAL',
                                   'p_tp': p[:, 0], 'p_sl': p[:, 1], 'p_to': p[:, 2], 'c_tp': pc[:, 0], 'c_sl': pc[:, 1],
                                   'c_to': pc[:, 2], 'u_tp': pu[:, 0], 'u_sl': pu[:, 1], 'u_to': pu[:, 2],
                                   'row': Lo.row.to_numpy()[test]})
                df['exp_r'] = df.p_tp * st['tp_r'] + df.p_sl * st['r_sl'] + df.p_to * st['r_to']
                df.to_parquet(FIN / f'{hz}_{d}_{gk}.parquet', index=False)
                met = T.metrics(df, hz, d, gk, 'FINAL')
                key = f'{hz}_{d}_{gk}'
                rule = dev_res[key]['chosen_rule']
                Xf = features_for(hz, df)
                ev = evaluate_target(df, hz, d, gk, Xf, rule=tuple(rule) if rule else ('exp_r', 9.99))
                ev['metrics'] = met
                ev['dev_rule'] = rule
                ev['dev_passes'] = dev_res[key]['passes']
                out.append(ev)
                if hz in ('1h', '4h') and gk == '1x1':
                    models_1h[(hz, d)] = (mdl, cal, cols)
                print(key, 'FINAL bss', round(met['brier_skill_vs_clim'], 4), 'auc', round(met['auc_tp_model'], 4),
                      'clim', round(met['auc_tp_clim'], 4), 'rule', rule,
                      'ev', round(ev.get('eval_stats', {}).get('ev_r', np.nan), 4) if rule else None, flush=True)
    (RES / 'faz5_final.json').write_text(json.dumps(out, indent=1, default=float))
    bot_crosscheck(models_1h)


def bot_crosscheck(models: dict) -> None:
    """Bot'un gerçek NAS100 işlemleri (2026-06-30 → 08-28, final dönem): giriş anındaki model P(TP) TP/SL'yi ayırıyor mu?
    + 28k kapı kaydı: atlanan kararların 1s 1/1 etiketiyle ayrım."""
    m = pd.read_parquet(DATA / 'ndx_1m_v1.parquet')
    m = m[m.t >= pd.Timestamp('2025-11-01', tz='UTC').timestamp()].reset_index(drop=True)
    mac = pd.read_parquet(DATA / 'macro/macro_daily.parquet')
    cal = pd.read_parquet(DATA / 'macro/calendar.parquet')
    ctx = FE.build_context(m)
    tr = pd.read_csv(REPO / 'nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv')
    tr = tr[tr.exit_reason.isin(['tp', 'sl'])].copy()
    tr['t'] = (pd.to_datetime(tr.open_time_utc, utc=True).astype('int64') // 10**9 // 60) * 60   # içinde bulunulan dakika başı
    td = tr.t.to_numpy()          # karar anı = giriş dakikası başı (o ana kadar kapanmış barlar)
    F = FE.compute_features(m, td, mac, cal, ctx=ctx)
    res = {'n_trades': int(len(tr)), 'tp': int((tr.exit_reason == 'tp').sum()), 'sl': int((tr.exit_reason == 'sl').sum())}
    yb = (tr.exit_reason == 'tp').astype(int).to_numpy()
    for (hz, d), (mdl, calb, cols) in models.items():
        p_long = calb.apply(mdl.predict(F[cols]))[:, 0] if d == 'long' else None
        if d == 'long':
            res[f'_pl_{hz}'] = p_long
        else:
            res[f'_ps_{hz}'] = calb.apply(mdl.predict(F[cols]))[:, 0]
    for hz in ('1h', '4h'):
        p = np.where(tr.direction.to_numpy() == 'BUY', res.pop(f'_pl_{hz}'), res.pop(f'_ps_{hz}'))
        res[f'auc_p_tp_{hz}_1x1'] = float(roc_auc_score(yb, p)) if 0 < yb.sum() < len(yb) else None
        res[f'mean_p_tp_{hz}_on_tp'] = float(p[yb == 1].mean())
        res[f'mean_p_tp_{hz}_on_sl'] = float(p[yb == 0].mean())
        # günlere göre (bağımsızlık): gün-blok permütasyon p-değeri
        rng = np.random.default_rng(1)
        day = td // 86400
        aucs = []
        for _ in range(500):
            perm = rng.permutation(np.unique(day))
            mp = dict(zip(np.unique(day), perm))
            yy = pd.Series(yb).groupby(day).transform(lambda s: s.sample(frac=1, random_state=int(rng.integers(1e9))).values)
            aucs.append(roc_auc_score(yy, p))
        res[f'auc_perm_p95_{hz}'] = float(np.quantile(aucs, .95))
    (RES / 'faz5_bot_crosscheck.json').write_text(json.dumps(res, indent=1, default=float))
    print('bot', res, flush=True)


def bundle() -> None:
    dev_res = {r['target']: r for r in json.loads((RES / 'faz5_dev.json').read_text())}
    fin_res = {r['target']: r for r in json.loads((RES / 'faz5_final.json').read_text())}
    version = sys.argv[2] if len(sys.argv) > 2 else 'nom_v1_' + time.strftime('%Y%m%d')
    models, cals, targets = {}, {}, {}
    cols_all = None
    for hz in LB.HORIZONS:
        X, L, cols = T.load_horizon(hz)
        cols_all = cols
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                key = f'{hz}_{d}_{gk}'
                mdl, isos, st, *_ = train_final_models(hz, d, gk, X, L, cols, final=False)
                models[key] = mdl
                cals[key] = MS.Calibrator.from_isotonic(isos)
                dr, fr = dev_res[key], fin_res[key]
                rule = dr['chosen_rule']
                proven = bool(dr['passes'] and fr.get('eval_stats', {}).get('ev_r', -1) > 0)
                thr = None
                if rule and rule[0] == 'exp_r':
                    thr = float(rule[1])
                targets[key] = st | {'p_tp_bins': dr['calibration_p_tp'], 'exp_r_bins': dr['exp_r_bins'],
                                     'rule': rule, 'threshold': thr if proven else None, 'proven': proven,
                                     'dev_passes': dr['passes'],
                                     'final_ev_r': fr.get('eval_stats', {}).get('ev_r'),
                                     'final_bss': fr['metrics']['brier_skill_vs_clim']}
                print('bundle', key, 'proven', proven, flush=True)
    Fall = pd.read_parquet(DATA / 'features_v1.parquet')
    recent = Fall[Fall._t >= Fall._t.max() - 365 * 86400]
    feature_ref = {c: [float(x) for x in np.nanquantile(recent[c].to_numpy(dtype=float), np.linspace(.1, .9, 9))]
                   for c in cols_all if recent[c].notna().mean() > 0.5}
    feature_ref_wide = {c: [float(x) for x in np.nanquantile(recent[c].to_numpy(dtype=float), [0.01, 0.99])]
                        for c in feature_ref}
    imp = pd.read_csv(RES / 'faz2_importance_1h_long_1x1.csv')
    top_features = imp.sort_values('perm_dlogloss', ascending=False).feature.head(15).tolist()
    meta = {'feature_ref': feature_ref, 'feature_ref_wide': feature_ref_wide, 'top_features': top_features, 'version': version, 'data_version': 'ndx_1m_v1 (Dukascopy 2021-11 → ' + pd.Timestamp(int(Fall._t.max()), unit='s', tz='UTC').strftime('%Y-%m-%d') + ')',
            'trained_until': pd.Timestamp(int(Fall._t.max()), unit='s', tz='UTC').strftime('%Y-%m-%d'), 'feature_columns': cols_all, 'targets': targets,
            'params': T.PARAMS, 'grid_s': T.GRID_S, 'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    MS.save_bundle(version, meta, models, cals)
    MS.promote(version, sys.argv[3] if len(sys.argv) > 3 else 'üretim paketi (Faz 5 sonrası)')
    print('ACTIVE', version)


if __name__ == '__main__':
    {'dev': dev, 'final': final, 'bundle': bundle}[sys.argv[1]]()
