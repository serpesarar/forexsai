"""NOM Faz 9 — periyodik yeniden eğitim: yeni veri → özellik → walk-forward → yalnız eskisini geçerse terfi.

Akış (`python src/faz9_retrain.py run`):
  1. Veri: Dukascopy'den eksik son günleri indir (best effort, duka_fetch) → data_layer → ndx_1m_v1.parquet
  2. Özellik + etiket: faz12_build (aynı kod yolu)
  3. Değerlendirme penceresi W = [şampiyonun eğitim sonu + ambargo, veri sonu] (ikisi için de GÖRÜLMEMİŞ)
     Meydan okuyan (challenger) = aynı yapılandırma, W başına kadar veriyle eğitilir.
     Şampiyon = ACTIVE paket. W'de her hedefte saat-iklimine göre Brier becerisi.
  4. Terfi kuralı (hepsi): W'de ≥ MIN_W_ROWS satır; meydan okuyan hedeflerin ≥ %60'ında daha iyi; ortalama beceri
     farkı ≥ 0; hiçbir hedefte beceri farkı < −0,01. Geçerse tüm veriyle yeniden eğitilir, yeni sürüm kaydedilir,
     `model_store.promote`. Geçmezse şampiyon kalır. Karar results/faz9_retrain_<tarih>.json'a yazılır.
  5. Geri alma: `python -c "from services.nom import model_store as M; M.rollback()"` (HISTORY.jsonl).
`python src/faz9_retrain.py dryrun` — mekanizma sınaması: şampiyon 2026-08-01'e, meydan okuyan 2026-09-15'e kadar
eğitilir, W = 2026-09-16 → veri sonu (yalnız 1s hedefleri). Terfi YAPMAZ.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
sys.path.insert(0, str(H / 'src'))
from services.nom import labels as LB  # noqa: E402
from services.nom import model_store as MS  # noqa: E402
import faz4_train as T  # noqa: E402
import validation as V  # noqa: E402

RES = H / 'results'
PY = sys.executable
MIN_W_ROWS = 300
WIN_FRAC = 0.60
WORST_DROP = -0.01


def refresh_data() -> None:
    today = time.strftime('%Y-%m-%d')
    last = pd.to_datetime(pd.read_parquet(H / 'data/ndx_1m_v1.parquet', columns=['t']).t.max(), unit='s').strftime('%Y-%m-%d')
    subprocess.run([PY, str(H / 'src/duka_fetch.py'), f'{last}:{today}', 'BID'], check=False, timeout=6 * 3600)
    subprocess.run([PY, str(H / 'src/faz0_build.py')], check=True)
    subprocess.run([PY, str(H / 'src/faz12_build.py')], check=True)


def _fit(X, y, t, cols, hz, until: int):
    trn_all = t < until - V.HORIZON_S[hz] - V.EMBARGO_S
    tt = t[trn_all]
    cut = np.quantile(tt, 1 - V.CALIB_FRAC)
    fit = trn_all & (t < cut - V.HORIZON_S[hz] - V.EMBARGO_S)
    cal = trn_all & (t >= cut)
    mdl = T.fit_lgb(X[cols], y, fit, cal)
    _, isos = T.calibrate(mdl.predict(X[cols][cal]), y[cal], mdl.predict(X[cols][cal])[:3])
    return mdl, MS.Calibrator.from_isotonic(isos), trn_all


def skill_on_window(mdl, cal, X, y, t, cols, trn, w0: int, w1: int) -> tuple[float, int]:
    w = (t >= w0) & (t < w1)
    if w.sum() == 0:
        return float('nan'), 0
    p = cal.apply(mdl.predict(X[cols][w]))
    hr = T.ny_hour(t)
    c = T.climate(y[trn], hr[trn], hr[w])
    return 1 - T.brier(p, y[w]) / T.brier(c, y[w]), int(w.sum())


def compare(champ_until: int, chall_until: int, w0: int, w1: int, horizons=tuple(LB.HORIZONS),
            champion: MS.Bundle | None = None) -> dict:
    rows = []
    for hz in horizons:
        X, L, cols = T.load_horizon(hz)
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                yv = L[f'{d}_{gk}_cls'].to_numpy()
                ok = yv >= 0
                Xo, y, t = X[ok].reset_index(drop=True), yv[ok].astype(int), L.t.to_numpy()[ok]
                ch_m, ch_c, ch_trn = _fit(Xo, y, t, cols, hz, chall_until)
                if champion is not None:
                    cm, cc, _ = champion.target(hz, d, gk)
                    cp_m, cp_c = cm, cc
                    cp_trn = t < champ_until
                else:
                    cp_m, cp_c, cp_trn = _fit(Xo, y, t, cols, hz, champ_until)
                s_ch, n = skill_on_window(ch_m, ch_c, Xo, y, t, cols, ch_trn, w0, w1)
                s_cp, _ = skill_on_window(cp_m, cp_c, Xo, y, t, cols, cp_trn, w0, w1)
                rows.append({'target': f'{hz}_{d}_{gk}', 'n_window': n, 'skill_challenger': s_ch,
                             'skill_champion': s_cp, 'diff': s_ch - s_cp})
                print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    ok = df.n_window >= MIN_W_ROWS
    d = df[ok]
    decision = bool(len(d) and (d['diff'] > 0).mean() >= WIN_FRAC and d['diff'].mean() >= 0 and d['diff'].min() >= WORST_DROP)
    return {'window': [w0, w1], 'targets': df.to_dict('records'), 'win_frac': float((d['diff'] > 0).mean()) if len(d) else None,
            'mean_diff': float(d['diff'].mean()) if len(d) else None, 'promote': decision}


def run() -> None:
    refresh_data()
    champ = MS.load_bundle()
    champ_until = int(pd.Timestamp(champ.meta['trained_until'], tz='UTC').timestamp()) + 86400
    t_end = int(pd.read_parquet(H / 'data/ndx_1m_v1.parquet', columns=['t']).t.max())
    w0 = champ_until + V.EMBARGO_S
    res = compare(champ_until, w0, w0, t_end + 60, champion=champ)
    res['champion'] = champ.version
    if res['promote']:
        subprocess.run([PY, str(H / 'src/faz5_econ.py'), 'bundle'], check=True)   # tüm veriyle yeniden eğit + terfi
        res['new_version'] = MS.active_version()
    (RES / f"faz9_retrain_{time.strftime('%Y%m%d')}.json").write_text(json.dumps(res, indent=1, default=float))
    print('KARAR', 'TERFİ' if res['promote'] else 'ŞAMPİYON KALIR', flush=True)


def dryrun() -> None:
    a = int(pd.Timestamp('2026-08-01', tz='UTC').timestamp())
    b = int(pd.Timestamp('2026-09-15', tz='UTC').timestamp())
    t_end = int(pd.read_parquet(H / 'data/ndx_1m_v1.parquet', columns=['t']).t.max()) + 60
    res = compare(a, b, b + V.EMBARGO_S, t_end, horizons=('1h',))
    res['note'] = 'dryrun: terfi yapılmaz; mekanizma sınaması'
    (RES / 'faz9_retrain_dryrun.json').write_text(json.dumps(res, indent=1, default=float))
    print('DRYRUN karar (uygulanmadı):', res['promote'], 'win_frac', res['win_frac'], 'mean_diff', res['mean_diff'])


if __name__ == '__main__':
    {'run': run, 'dryrun': dryrun}[sys.argv[1]]()
