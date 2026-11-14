"""NOM drift izleme: özellik dağılımı kayması (PSI) + canlı kalibrasyon bozulması.

Üç özellik sınıfı (14 günlük pencere için doğru ölçü farklıdır):
  * takvim-belirli (saat, seans fazı, gün, olay dakikası) → ölçülmez (dağılımı takvim belirler, kayma değil);
  * yavaş (günlük/H4/makro/20 günlük seviye) → 14 günde birkaç farklı değer alır, PSI anlamsız şekilde patlar →
    **destek dışı oranı**: son değerlerin eğitim [q01, q99] aralığı dışındaki payı; ≥ %50 → KAYMA;
  * hızlı (gün-içi) → PSI (referans: meta['feature_ref'] ondalıkları); < 0,10 sabit · 0,10–0,25 izle · ≥ 0,25 KAYMA.
Önemli özelliklerde (meta['top_features']) KAYMA veya kalibrasyon drift uyarısı → `alarm=True`.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import calibration as CB
from . import features as FE
from . import live_data as LD
from . import model_store as MS

PSI_WARN, PSI_ALARM = 0.10, 0.25
OOS_ALARM = 0.50
CALENDAR_PREFIX = ('ny_mod_', 'session_phase', 'dow', 'is_', 'month_', 'min_to_', 'min_since_')
SLOW_PREFIX = ('D1_', 'H4_', 'mac_', 'lvl_pd', 'lvl_hi20d', 'lvl_lo20d', 'atr_H1_pct', 'H1_ema200', 'h1_structure')
SLOW_SUFFIX = ('_ema_stack', '_psar_dir', '_div_bear', '_div_bull')   # ayrık, günlerce kalıcı durumlar


def feature_class(c: str) -> str:
    if c.startswith(CALENDAR_PREFIX):
        return 'takvim'
    if c.startswith(SLOW_PREFIX) or c.endswith(SLOW_SUFFIX):
        return 'yavas'
    return 'hizli'


RECENT_DAYS = 14
STEP_S = 900


def psi(ref_q: list[float], x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    edges = np.unique(np.asarray(ref_q, float))
    if len(x) < 50 or len(edges) < 3:
        return float('nan')
    exp = np.full(len(edges) + 1, 1.0 / (len(edges) + 1))
    cnt = np.bincount(np.searchsorted(edges, x, side='right'), minlength=len(edges) + 1) / len(x)
    cnt = np.clip(cnt, 1e-4, None)
    exp = np.clip(exp, 1e-4, None)
    return float(((cnt - exp) * np.log(cnt / exp)).sum())


def feature_drift(bars: pd.DataFrame | None = None, macro=None, calendar=None) -> dict:
    b = MS.load_bundle()
    ref = b.meta.get('feature_ref', {})
    bars = LD.load_bars() if bars is None else bars
    macro = LD.load_macro() if macro is None else macro
    calendar = LD.load_calendar() if calendar is None else calendar
    end = int(bars.t.iloc[-1]) + 60
    td = np.arange(end - RECENT_DAYS * 86400, end, STEP_S)
    td = td[np.isin(td - 60, bars.t.to_numpy())]
    F = FE.compute_features(bars, td, macro, calendar)
    rows = []
    wide = b.meta.get('feature_ref_wide', {})
    for c, q in ref.items():
        if c not in F:
            continue
        cls = feature_class(c)
        x = F[c].to_numpy(dtype=float)
        if cls == 'takvim':
            continue
        if cls == 'yavas':
            lo, hi = wide.get(c, (q[0], q[-1]))
            xf = x[np.isfinite(x)]
            v = float(((xf < lo) | (xf > hi)).mean()) if len(xf) else float('nan')
            rows.append({'ozellik': c, 'sinif': cls, 'olcu': 'destek_disi_orani', 'deger': None if np.isnan(v) else round(v, 3),
                         'durum': 'KAYMA' if v >= OOS_ALARM else 'sabit'})
        else:
            v = psi(q, x)
            rows.append({'ozellik': c, 'sinif': cls, 'olcu': 'psi', 'deger': None if np.isnan(v) else round(v, 4),
                         'durum': 'KAYMA' if v >= PSI_ALARM else 'izle' if v >= PSI_WARN else 'sabit'})
    rank = {'KAYMA': 2, 'izle': 1, 'sabit': 0}
    rows.sort(key=lambda r: (-rank[r['durum']], -(r['deger'] or 0)))
    top = set(b.meta.get('top_features', []))
    alarm_feats = [r['ozellik'] for r in rows if r['durum'] == 'KAYMA' and r['ozellik'] in top]
    return {'n_karar': int(len(td)), 'pencere_gun': RECENT_DAYS, 'ozellikler': rows[:25],
            'kayan_onemli_ozellikler': alarm_feats}


def report(horizon: str = '1h', gk: str = '1x1') -> dict:
    out = {'ts': time.time(), 'surum': MS.active_version()}
    try:
        out['ozellik'] = feature_drift()
    except Exception as e:  # noqa: BLE001
        out['ozellik'] = {'hata': str(e)}
    try:
        cal = CB.live_report(horizon, gk, 56)
        out['kalibrasyon'] = {s: {'drift_uyarisi': cal[s].get('drift_uyarisi'), 'son14_beceri': cal[s].get('son14_beceri'),
                                  'brier_beceri': cal[s].get('brier_beceri'), 'n': cal[s].get('n')} for s in ('long', 'short')}
    except Exception as e:  # noqa: BLE001
        out['kalibrasyon'] = {'hata': str(e)}
    cal_alarm = any(v.get('drift_uyarisi') for v in out['kalibrasyon'].values() if isinstance(v, dict))
    out['alarm'] = bool(out['ozellik'].get('kayan_onemli_ozellikler') or cal_alarm)
    return out
