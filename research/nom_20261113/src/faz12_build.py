"""NOM Faz 1 + Faz 2 — karar ızgarası, özellikler (tek kod yolu) ve triple-barrier etiketleri.

python src/faz12_build.py → data/features_v1.parquet, data/labels_<ufuk>.parquet, results/faz1_*.csv|json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
from services.nom import nyse_calendar as CAL  # noqa: E402

NY = 'America/New_York'
DATA = H / 'data'
RES = H / 'results'
START = pd.Timestamp('2021-11-01', tz='UTC')
WARMUP_DAYS = 30            # özellik ısınması: ilk 30 gün karar yok
CHUNK = 40000
SESSION_MIN_LEFT = 30


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m = pd.read_parquet(DATA / 'ndx_1m_v1.parquet')
    m = m[m.t >= START.timestamp()].reset_index(drop=True)
    mac = pd.read_parquet(DATA / 'macro' / 'macro_daily.parquet')
    cal = pd.read_parquet(DATA / 'macro' / 'calendar.parquet')
    return m, mac, cal


def decision_grid(m: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """t_dec = 5 dk sınırı; giriş barı (açılışı t_dec olan 1m bar) mevcut olmalı."""
    t = m.t.to_numpy()
    pos = {v: i for i, v in enumerate(t)}
    cand = t[(t % 300 == 0) & (t >= t[0] + WARMUP_DAYS * 86400)]
    i0 = np.array([pos[x] for x in cand])
    # karar anından hemen önce kapanmış bar olmalı (en çok 5 dk önce)
    prev_ok = (i0 > 0) & (t[np.maximum(i0 - 1, 0)] >= cand - 300)
    return cand[prev_ok], i0[prev_ok]


def expected_open_minutes(t0: np.ndarray, t_end: np.ndarray) -> np.ndarray:
    """Pencerede NY 17:00-18:00 günlük ara dışındaki dakika sayısı (hafta sonu zaten etiket dışı)."""
    total = (t_end - t0) / 60.0
    ny0 = pd.to_datetime(t0, unit='s', utc=True).tz_convert(NY)
    mod0 = (ny0.hour * 60 + ny0.minute).to_numpy()
    dur = total
    # 17:00 (1020) — 18:00 (1080) ile kesişim (pencere ≤ 1 gün)
    a = np.maximum(mod0, 1020)
    b = np.minimum(mod0 + dur, 1080)
    ov = np.clip(b - a, 0, None)
    a2 = np.maximum(mod0, 1020 + 1440)
    b2 = np.minimum(mod0 + dur, 1080 + 1440)
    ov += np.clip(b2 - a2, 0, None)
    return total - ov


def session_end(t0: np.ndarray) -> np.ndarray:
    ny = pd.to_datetime(t0, unit='s', utc=True).tz_convert(NY)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    dates = [x.date() for x in ny.tz_localize(None).normalize()]
    close = np.array([CAL.cash_close_minutes(d) for d in dates])
    day0 = (ny.tz_localize(None).normalize().tz_localize(NY).tz_convert('UTC').asi8 // 10**9)
    ok = (mod >= 570) & (mod <= close - SESSION_MIN_LEFT) & np.array([not CAL.is_holiday(d) for d in dates]) \
        & (ny.dayofweek.to_numpy() < 5)
    return np.where(ok, day0 + close * 60, -1)


def main() -> None:
    RES.mkdir(exist_ok=True)
    t_all = time.time()
    m, mac, cal = load()
    print('bars', len(m), flush=True)
    ctx = FE.build_context(m)
    print('ctx', round(time.time() - t_all, 1), flush=True)
    td, i0 = decision_grid(m)
    print('decisions', len(td), flush=True)
    parts = []
    for s in range(0, len(td), CHUNK):
        parts.append(FE.compute_features(m, td[s:s + CHUNK], mac, cal, ctx=ctx))
        print('feat', s, round(time.time() - t_all, 1), flush=True)
    F = pd.concat(parts, ignore_index=True)
    F['_i0'] = i0
    F.to_parquet(DATA / 'features_v1.parquet', index=False)
    cols = FE.feature_columns(F)
    cat = pd.DataFrame({'feature': cols, 'nan_frac': F[cols].isna().mean().round(4).to_numpy()})
    cat.to_csv(RES / 'faz2_feature_nan.csv', index=False)
    path = LB.Path1m(t=m.t.to_numpy(), o=m.open.to_numpy(), h=m.high.to_numpy(), l=m.low.to_numpy(),
                     c=m.close.to_numpy(), spr=m.spr.to_numpy())
    base_rows = []
    for hz, spec in LB.HORIZONS.items():
        sel = (td % spec['grid_s'] == 0)
        if hz == 'session':
            te = session_end(td)
            sel &= te > 0
        else:
            te = td + spec['minutes'] * 60
        idx = np.where(sel)[0]
        atr = F[f"_atr_{spec['atr_tf']}"].to_numpy()[idx]
        exp = expected_open_minutes(td[idx], te[idx])
        L = LB.label_frame(path, i0[idx], atr, te[idx], expected_min=exp)
        L.insert(0, 'row', idx)
        L.insert(1, 't', td[idx])
        L.to_parquet(DATA / f'labels_{hz}.parquet', index=False)
        yr = pd.to_datetime(td[idx], unit='s', utc=True).year
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                c = L[f'{d}_{gk}_cls']
                r = L[f'{d}_{gk}_r']
                v = c >= 0
                be = 1.0 / (1.0 + tp / sl)
                for y in ['ALL'] + sorted(set(yr)):
                    vv = v & ((yr == y) if y != 'ALL' else True)
                    if vv.sum() == 0:
                        continue
                    base_rows.append({'horizon': hz, 'dir': d, 'geom': gk, 'year': y, 'n': int(vv.sum()),
                                      'p_tp': float((c[vv] == 0).mean()), 'p_sl': float((c[vv] == 1).mean()),
                                      'p_to': float((c[vv] == 2).mean()), 'ev_r': float(r[vv].mean()),
                                      'breakeven_wr_tp_vs_sl': be,
                                      'amb_frac': float(L[f'{d}_{gk}_amb'][vv].mean())})
        print('labels', hz, len(idx), round(time.time() - t_all, 1), flush=True)
    base = pd.DataFrame(base_rows)
    base.to_csv(RES / 'faz1_base_rates.csv', index=False)
    print(base[base.year == 'ALL'].round(4).to_string())


if __name__ == '__main__':
    main()
