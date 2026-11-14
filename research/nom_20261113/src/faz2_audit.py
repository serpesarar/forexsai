"""NOM Faz 2 — gerçek veride sızıntı/eşdeğerlik denetimi, canlı pencere yeterliliği, özellik kataloğu ve önem.

Önem yalnız GELİŞTİRME döneminde: eğitim 2021-12 → 2024-12, değerlendirme 2025 (final test 2026-05+ dokunulmaz).
Permütasyon önemi (log-loss artışı) + TreeSHAP (LightGBM pred_contrib, |katkı| ortalaması).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
from services.nom import features as FE  # noqa: E402

DATA, RES = H / 'data', H / 'results'
RNG = np.random.default_rng(20261113)
PARAMS = dict(objective='multiclass', num_class=3, learning_rate=0.05, num_leaves=31, max_depth=6,
              min_child_samples=200, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0,
              verbosity=-1, seed=7, num_threads=8)


def real_leak_test(m, mac, cal, F) -> dict:
    cols = FE.feature_columns(F)
    td = F._t.to_numpy()
    pick = np.sort(RNG.choice(np.arange(len(td) // 3, len(td)), 25, replace=False))
    bad_trunc, bad_window, maxdev = [], {}, {}
    for k in pick:
        t = td[k]
        cut = m[(m.t < t) & (m.t >= t - 400 * 86400)].reset_index(drop=True)      # 400 gün önek
        one = FE.compute_features(cut, np.array([t]), mac, cal)
        win = m[(m.t < t) & (m.t >= t - FE.LIVE_HISTORY_DAYS * 86400)].reset_index(drop=True)
        w1 = FE.compute_features(win, np.array([t]), mac, cal)
        full = F.iloc[k]
        for c in cols:
            a, b, w = float(full[c]), float(one[c].iloc[0]), float(w1[c].iloc[0])
            if not ((np.isnan(a) and np.isnan(b)) or np.isclose(a, b, rtol=1e-6, atol=1e-6)):
                bad_trunc.append(c)
            if not (np.isnan(a) and np.isnan(w)):
                d = abs(a - w) / (abs(a) + 1e-9) if np.isfinite(a) and np.isfinite(w) else (0.0 if np.isnan(a) == np.isnan(w) else 1.0)
                maxdev[c] = max(maxdev.get(c, 0.0), d)
    return {'n_points': len(pick), 'trunc_400d_mismatch_cols': sorted(set(bad_trunc)),
            'window_days': FE.LIVE_HISTORY_DAYS,
            'window_reldev_gt_1pct': {c: round(v, 4) for c, v in sorted(maxdev.items(), key=lambda x: -x[1]) if v > 0.01}}


def importance(F, hz: str, d: str, gk: str) -> pd.DataFrame:
    L = pd.read_parquet(DATA / f'labels_{hz}.parquet', columns=['row', 't', f'{d}_{gk}_cls'])
    y = L[f'{d}_{gk}_cls'].to_numpy()
    ok = y >= 0
    L, y = L[ok], y[ok]
    X = F.iloc[L.row.to_numpy()][FE.feature_columns(F)].reset_index(drop=True)
    t = L.t.to_numpy()
    tr = t < pd.Timestamp('2024-12-31', tz='UTC').timestamp()
    va = (t >= pd.Timestamp('2025-01-02', tz='UTC').timestamp()) & (t < pd.Timestamp('2026-01-01', tz='UTC').timestamp())
    mdl = lgb.train(PARAMS, lgb.Dataset(X[tr], y[tr]), num_boost_round=400)
    Xv, yv = X[va].reset_index(drop=True), y[va]
    base = log_loss(yv, mdl.predict(Xv), labels=[0, 1, 2])
    clim = np.bincount(y[tr], minlength=3) / tr.sum()
    clim_ll = log_loss(yv, np.tile(clim, (len(yv), 1)), labels=[0, 1, 2])
    sub = RNG.choice(len(Xv), min(30000, len(Xv)), replace=False)
    Xs, ys = Xv.iloc[sub].reset_index(drop=True), yv[sub]
    b2 = log_loss(ys, mdl.predict(Xs), labels=[0, 1, 2])
    rows = []
    contrib = mdl.predict(Xs.iloc[:8000], pred_contrib=True)        # [n, 3*(p+1)]
    p = X.shape[1]
    shap_abs = np.abs(contrib.reshape(len(contrib), 3, p + 1)[:, :, :p]).mean(axis=(0, 1))
    for j, c in enumerate(X.columns):
        Xp = Xs.copy()
        Xp[c] = Xp[c].to_numpy()[RNG.permutation(len(Xp))]
        rows.append({'feature': c, 'perm_dlogloss': log_loss(ys, mdl.predict(Xp), labels=[0, 1, 2]) - b2,
                     'shap_mean_abs': float(shap_abs[j])})
    df = pd.DataFrame(rows).sort_values('perm_dlogloss', ascending=False)
    df.attrs['skill'] = 1 - base / clim_ll
    return df


DESC = {
    'atr_ratio': ('ATR14 / ATR14 kayan medyanı (rejim)', 'son kapanmış bar'),
    'rsi14': ('RSI 14 (Wilder)', 'son kapanmış bar'), 'rsi7': ('RSI 7', 'son kapanmış bar'),
    'rsi21': ('RSI 21', 'son kapanmış bar'), 'rsi14_slope3': ('RSI14 − 3 bar önceki', 'son kapanmış bar'),
    'div_bear': ('ayı uyumsuzluğu: 20-bar kapanış tepesi ama RSI tepeden ≥5 düşük', 'son kapanmış bar'),
    'div_bull': ('boğa uyumsuzluğu (ayna)', 'son kapanmış bar'),
    'macd_hist_atr': ('MACD(12,26,9) histogram / ATR', 'son kapanmış bar'),
    'stoch_k': ('Stokastik %K(14,3)', 'son kapanmış bar'), 'adx14': ('ADX 14', 'son kapanmış bar'),
    'er20': ('Kaufman verimlilik oranı 20', 'son kapanmış bar'),
    'bb_width_atr': ('Bollinger(20,2) genişliği / ATR', 'son kapanmış bar'), 'bb_pctb': ('Bollinger %B', 'son kapanmış bar'),
    'bb_squeeze': ('BB genişliği / 120-bar medyanı (sıkışma)', 'son kapanmış bar'),
    'ema_stack': ('EMA20/50/200 dizilimi (−2…+2)', 'son kapanmış bar'),
    'roc3_atr': ('3-bar değişim / ATR', 'son kapanmış bar'), 'roc12_atr': ('12-bar değişim / ATR', 'son kapanmış bar'),
    'roc4_atr': ('4-bar değişim / ATR', 'son kapanmış bar'),
    'psar_dir': ('Parabolic SAR yönü', 'son kapanmış bar'), 'psar_dist_atr': ('fiyat − SAR / ATR', 'son kapanmış bar'),
    'ret1': ('günlük getiri (önceki seans)', 'son kapanmış D1'), 'ret5': ('5 günlük getiri', 'son kapanmış D1'),
}


def describe(c: str) -> tuple[str, str, str]:
    tf = c.split('_')[0] if c.split('_')[0] in ('M5', 'M15', 'H1', 'H4', 'D1') else '1m/karma'
    rest = c[len(tf) + 1:] if tf != '1m/karma' else c
    for k, (d, lag) in DESC.items():
        if rest == k:
            return tf, d, lag
    if rest.startswith('ema') and ('dist' in rest or 'slope' in rest):
        return tf, f'{rest.split("_")[0].upper()} {"uzaklık" if "dist" in rest else "10-bar eğim"} / ATR', 'son kapanmış bar'
    if c.startswith('mac_'):
        return 'günlük makro', f'{c[4:]} (yfinance)', 'd günü değeri yalnız d 17:15 ET sonrası'
    if c.startswith('min_to_') or c.startswith('min_since_'):
        return 'takvim', f'{c} (dk, ±3 gün tavan)', 'önceden ilan edilmiş takvim'
    if c.startswith('lvl_'):
        return 'seviye', f'{c[4:-5]} seviyesine işaretli uzaklık / ATR(H1)', 'kapanmış D1 / gün-içi kümülatif'
    if c.startswith('sr_'):
        return 'seviye', f'pivot+sabit seviye kümesi: {c[3:]}', 'teyitli pivotlar (k bar sonra)'
    if c.startswith('round'):
        return 'seviye', f'en yakın {c[5:-5]} yuvarlak seviyeye uzaklık / ATR(H1)', 'anlık fiyat (kapanmış 1m)'
    return '1m/karma', c, 'kapanmış 1m barlar'


def main() -> None:
    m = pd.read_parquet(DATA / 'ndx_1m_v1.parquet')
    m = m[m.t >= pd.Timestamp('2021-11-01', tz='UTC').timestamp()].reset_index(drop=True)
    mac = pd.read_parquet(DATA / 'macro/macro_daily.parquet')
    cal = pd.read_parquet(DATA / 'macro/calendar.parquet')
    F = pd.read_parquet(DATA / 'features_v1.parquet')
    leak = real_leak_test(m, mac, cal, F)
    print(json.dumps(leak, indent=1)[:3000], flush=True)
    imps = {}
    for hz, d, gk in (('1h', 'long', '1x1'), ('1h', 'short', '1x1'), ('4h', 'long', '1x1'), ('15m', 'long', '1x1')):
        df = importance(F, hz, d, gk)
        imps[f'{hz}_{d}_{gk}'] = df
        df.to_csv(RES / f'faz2_importance_{hz}_{d}_{gk}.csv', index=False)
        print(hz, d, gk, 'skill', round(df.attrs['skill'], 4), df.head(12)[['feature', 'perm_dlogloss', 'shap_mean_abs']].round(5).to_dict('records'), flush=True)
    cols = FE.feature_columns(F)
    nan = F[cols].isna().mean()
    cat = []
    for c in cols:
        tf, d, lag = describe(c)
        r = {'feature': c, 'tf': tf, 'tanim': d, 'gecikme': lag, 'nan_frac': round(float(nan[c]), 4),
             'sizinti_testi': 'GEÇTİ' if c not in leak['trunc_400d_mismatch_cols'] else 'KALDI'}
        for k, df in imps.items():
            r[f'perm_{k}'] = float(df.set_index('feature').perm_dlogloss.get(c, np.nan))
        cat.append(r)
    pd.DataFrame(cat).to_csv(RES / 'faz2_feature_catalog.csv', index=False)
    (RES / 'faz2_leak_real.json').write_text(json.dumps(leak, indent=1))
    (RES / 'faz2_skill.json').write_text(json.dumps({k: v.attrs['skill'] for k, v in imps.items()}, indent=1))


if __name__ == '__main__':
    main()
