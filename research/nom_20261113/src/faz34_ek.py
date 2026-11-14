"""Faz 3 + Faz 4 tamamlama (.venv_ext ile): (a) Purged K-Fold (6 kat, ufuk + 1 g ambargo) LightGBM, (b) CatBoost, (c) LGB+XGB+Cat
ortalaması (ensemble), (d) derin modeller — LSTM ve TCN (son 120 dk 1m dizisi + 132 tablo özelliği). Hepsi Faz 4 ile AYNI WF katlarında,
aynı isotonic kalibrasyon, saat-iklimine göre Brier becerisi. Final dönem kullanılmaz (assert_not_final).

Prompt Faz 4 kuralı: derin modeller ancak boosting'i WF'de geçerlerse dahil edilir; geçemezlerse raporlanıp bırakılır.
python src/faz34_ek.py → results/faz34_ek.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'src'))
import faz4_train as T  # noqa: E402
import validation as V  # noqa: E402

TARGETS = [('1h', 'long', '1x1'), ('4h', 'long', '1x1')]
DEEP_FOLDS = ('2024H2', '2025H1', '2025H2')
DEEP = '--deep' in sys.argv   # varsayılan: derin modeller ayrı süreçte (src/faz4_deep.py) — OpenMP kilitlenmesi
SEQ = 120
EPOCHS = 6
RES = H / 'results'


def skill(p, y, c):
    return 1 - T.brier(p, y) / T.brier(c, y)


from deep_nets import seq_tensor, train_deep  # noqa: E402,F401


def main() -> None:
    import catboost as cb
    import lightgbm as lgb
    b = pd.read_parquet(H / 'data/ndx_1m_v1.parquet')
    b = b[b.t >= pd.Timestamp('2021-11-01', tz='UTC').timestamp()].reset_index(drop=True)
    F = pd.read_parquet(H / 'data/features_v1.parquet', columns=['_i0', '_atr_H1'])
    out = {}
    for hz, d, gk in TARGETS:
        t0 = time.time()
        X, L, cols = T.load_horizon(hz)
        y_all = L[f'{d}_{gk}_cls'].to_numpy()
        ok = y_all >= 0
        Xo, Lo, y = X[ok].reset_index(drop=True), L[ok].reset_index(drop=True), y_all[ok].astype(int)
        t = Lo.t.to_numpy()
        hr = T.ny_hour(t)
        Xm = Xo[cols].astype(np.float32)
        res = {'purged_kfold': [], 'wf': []}
        # (a) Purged K-Fold
        for k, (tr, te) in enumerate(V.purged_kfold(t, hz, 6)):
            V.assert_not_final(t[tr | te])
            cut = np.quantile(t[tr], 0.8)
            fit, cal = tr & (t < cut), tr & (t >= cut)
            m = T.fit_lgb(Xm, y, fit, cal)
            p, _ = T.calibrate(m.predict(Xm[cal]), y[cal], m.predict(Xm[te]))
            c = T.climate(y[tr], hr[tr], hr[te])
            res['purged_kfold'].append({'kat': k, 'n': int(te.sum()), 'bss': skill(p, y[te], c)})
        # (b)(c)(d) WF katları
        i0 = F._i0.to_numpy()[Lo.row.to_numpy()]
        a1 = F._atr_H1.to_numpy()[Lo.row.to_numpy()]
        for fd in V.walk_forward(t, hz):
            c = T.climate(y[fd.fit | fd.cal], hr[fd.fit | fd.cal], hr[fd.test])
            yt = y[fd.test]
            row = {'kat': fd.name, 'n': int(fd.test.sum())}
            m = T.fit_lgb(Xm, y, fd.fit, fd.cal)
            p_l, _ = T.calibrate(m.predict(Xm[fd.cal]), y[fd.cal], m.predict(Xm[fd.test]))
            row['lgb'] = skill(p_l, yt, c)
            cbm = cb.CatBoostClassifier(loss_function='MultiClass', iterations=1500, learning_rate=0.05, depth=6,
                                        l2_leaf_reg=5, random_seed=7, verbose=False, thread_count=8, od_type='Iter', od_wait=100)
            cbm.fit(Xm[fd.fit], y[fd.fit], eval_set=(Xm[fd.cal], y[fd.cal]))
            p_c, _ = T.calibrate(cbm.predict_proba(Xm[fd.cal]), y[fd.cal], cbm.predict_proba(Xm[fd.test]))
            row['catboost'] = skill(p_c, yt, c)
            row['ensemble_lgb_cat'] = skill((p_l + p_c) / 2, yt, c)
            if fd.name in DEEP_FOLDS and DEEP:
                tab_mu, tab_sd = np.nanmean(Xm[fd.fit], 0), np.nanstd(Xm[fd.fit], 0) + 1e-6   # ölçekleyici yalnız eğitimde
                tab = lambda m_: np.nan_to_num(((Xm[m_] - tab_mu) / tab_sd).to_numpy(np.float32))
                S = {k_: seq_tensor(i0[m_] - 1, b, a1[m_]) for k_, m_ in (('fit', fd.fit), ('cal', fd.cal), ('test', fd.test))}
                for kind in ('lstm', 'tcn'):
                    pv, pt = train_deep(kind, S['fit'], tab(fd.fit), y[fd.fit], S['cal'], tab(fd.cal), y[fd.cal], S['test'], tab(fd.test))
                    p_d, _ = T.calibrate(pv, y[fd.cal], pt)
                    row[kind] = skill(p_d, yt, c)
            res['wf'].append(row)
            print(hz, d, gk, row, round(time.time() - t0), flush=True)
        w = pd.DataFrame(res['wf'])
        res['ozet'] = {k: float(w[k].mean()) for k in ('lgb', 'catboost', 'ensemble_lgb_cat') if k in w}
        for kind in ('lstm', 'tcn'):
            if kind in w:
                dd = w.dropna(subset=[kind])
                res['ozet'][kind] = float(dd[kind].mean())
                res['ozet'][f'lgb_ayni_katlar_{kind}'] = float(dd.lgb.mean())
        res['ozet']['purged_kfold_ort'] = float(np.mean([x['bss'] for x in res['purged_kfold']]))
        out[f'{hz}_{d}_{gk}'] = res
        print('OZET', hz, d, gk, json.dumps(res['ozet']), flush=True)
    (RES / 'faz34_ek.json').write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
