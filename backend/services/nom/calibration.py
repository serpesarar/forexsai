"""NOM canlı kalibrasyon raporu + mezuniyet kontrolü (PROTOCOL.md §G, FAZ_8_RAPOR.md).

Mezuniyet: ≥ GRAD_MIN_DAYS gün ve ≥ GRAD_MIN_INDEP bağımsız (≥60 dk aralıklı) çözülmüş tahmin; her p_tp kovasında
gerçekleşen oran WF bandının (%95 GA) içinde; rolling Brier becerisi (taban oranına göre) ≥ 0; kalibrasyon eğimi
0,7–1,3. Biri tutmazsa 'güvenilir değil'.
Drift: son 14 günün Brier becerisi önceki dönemden ≥ 0,03 düşükse veya bant dışı kova sayısı ≥ 2 → uyarı.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from . import model_store as MS

GRAD_MIN_DAYS = 28
GRAD_MIN_INDEP = 300
SLOPE_BAND = (0.7, 1.3)
DRIFT_DROP = 0.03


def _fetch(horizon: str, gk: str, days: int, source: str | None = None) -> pd.DataFrame:
    from database.supabase_client import get_supabase_client
    db = get_supabase_client()
    if db is None:
        return pd.DataFrame()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows, last = [], since
    while True:
        q = db.table('nom_predictions')
        if source:
            q = q.eq('source', source)
        res = (q.select('t_dec,model_version,p_long_tp,p_short_tp,exp_r_long,exp_r_short,'
                                                  'outcome_long_cls,outcome_long_r,outcome_short_cls,outcome_short_r,status')
               .eq('horizon', horizon).eq('geometry', gk).gt('t_dec', last).raw_filter('outcome_filled_at=not.is.null')
               .order('t_dec').limit(1000).execute())
        chunk = getattr(res, 'data', None) or (res.get('data') if isinstance(res, dict) else None) or []
        rows += chunk
        if len(chunk) < 1000:
            break
        last = chunk[-1]['t_dec']
    return pd.DataFrame(rows)


def side_report(df: pd.DataFrame, side: str, bins: list[dict]) -> dict:
    d = df[df[f'outcome_{side}_cls'] >= 0]
    if d.empty:
        return {'n': 0}
    p = d[f'p_{side}_tp'].astype(float).to_numpy()
    y = (d[f'outcome_{side}_cls'] == 0).astype(float).to_numpy()
    r = d[f'outcome_{side}_r'].astype(float).to_numpy()
    base = y.mean()
    brier = float(((p - y) ** 2).mean())
    brier_base = float(((base - y) ** 2).mean()) or np.nan
    rows, out_band = [], 0
    for b in bins:
        m = (p >= b['lo']) & (p <= b['hi'])
        if m.sum() == 0:
            continue
        obs = float(y[m].mean())
        inside = b['ci_lo'] - 0.02 <= obs <= b['ci_hi'] + 0.02
        out_band += int(not inside and m.sum() >= 20)
        rows.append({'kova': [round(b['lo'], 3), round(b['hi'], 3)], 'n': int(m.sum()), 'beklenen': round(float(p[m].mean()), 4),
                     'gerceklesen': round(obs, 4), 'wf_bandi': [round(b['ci_lo'], 4), round(b['ci_hi'], 4)],
                     'bant_icinde': bool(inside)})
    slope = float(np.polyfit(p, y, 1)[0]) if len(p) > 30 and p.std() > 1e-6 else np.nan
    t = pd.to_datetime(d.t_dec, utc=True)
    wk = pd.DataFrame({'w': t.dt.to_period('W').astype(str), 'e': (p - y) ** 2, 'b': (base - y) ** 2}).groupby('w').mean()
    roll = [{'hafta': i, 'brier_beceri': round(float(1 - v.e / v.b), 4) if v.b > 0 else None} for i, v in wk.iterrows()]
    recent = t >= t.max() - pd.Timedelta(days=14)
    sk_recent = 1 - ((p[recent] - y[recent]) ** 2).mean() / max(((base - y[recent]) ** 2).mean(), 1e-9) if recent.any() else np.nan
    sk_prev = 1 - ((p[~recent] - y[~recent]) ** 2).mean() / max(((base - y[~recent]) ** 2).mean(), 1e-9) if (~recent).any() else np.nan
    ts = np.sort(t.astype('int64').to_numpy() // 10**9)
    indep = int(1 + (np.diff(ts) >= 3600).sum()) if len(ts) else 0   # ≥60 dk aralıklı = bağımsız
    days = float((ts[-1] - ts[0]) / 86400) if len(ts) > 1 else 0.0
    skill = 1 - brier / brier_base if brier_base and brier_base > 0 else np.nan
    grad = {'gun': round(days, 1), 'bagimsiz_n': indep, 'bant_disi_kova': out_band, 'brier_beceri': skill,
            'kalibrasyon_egimi': slope}
    grad['mezun'] = bool(days >= GRAD_MIN_DAYS and indep >= GRAD_MIN_INDEP and out_band == 0
                         and skill >= 0 and SLOPE_BAND[0] <= slope <= SLOPE_BAND[1])
    drift = bool((not np.isnan(sk_recent) and not np.isnan(sk_prev) and sk_prev - sk_recent >= DRIFT_DROP) or out_band >= 2)
    return {'n': int(len(d)), 'tp_orani': round(float(base), 4), 'ort_p_tp': round(float(p.mean()), 4),
            'brier': round(brier, 5), 'brier_beceri': None if np.isnan(skill) else round(float(skill), 4),
            'ort_R': round(float(np.nanmean(r)), 4), 'kovalar': rows, 'haftalik': roll,
            'mezuniyet': grad, 'drift_uyarisi': drift,
            'son14_beceri': None if np.isnan(sk_recent) else round(float(sk_recent), 4)}


def live_report(horizon: str, gk: str, days: int = 56, source: str | None = None) -> dict:
    """source: None = tüm kayıtlar; resmi mezuniyet için 'shadow' (canlı gölge)."""
    try:
        b = MS.load_bundle()
        tm = b.meta['targets']
    except FileNotFoundError:
        tm, b = {}, None
    df = _fetch(horizon, gk, days, source)
    out = {'ufuk': horizon, 'geometri': gk, 'gun': days, 'kaynak': source or 'tümü', 'surum': b.version if b else None, 'n_satir': int(len(df))}
    for side in ('long', 'short'):
        bins = tm.get(f'{horizon}_{side}_{gk}', {}).get('p_tp_bins', [])
        out[side] = side_report(df, side, bins) if len(df) else {'n': 0}
        out[side]['wf_referans'] = bins
    out['mezuniyet_olcutu'] = (f'≥{GRAD_MIN_DAYS} gün, ≥{GRAD_MIN_INDEP} bağımsız tahmin, tüm kovalar WF bandında, '
                               f'Brier becerisi ≥0, eğim {SLOPE_BAND[0]}–{SLOPE_BAND[1]}')
    return out
