"""NOM Faz 0 tamamlama + bağımsız eski dönem sınaması (2018-01 → 2021-10, 2020 çöküşü dahil).

1) data/ndx_1m_v3.parquet: NOM data_layer (aynı kurallar) + 2018–21 bi5 + 2026-01 dolgusu; spread bp × fiyat (puan modeli
   farklı fiyat düzeylerinde sürtünmeyi şişirir/küçültür — Faz 0 EK-2). v1'e DOKUNMAZ (paket veri sürümü sabit).
2) Eski dönem envanteri: gün kapsamı, eksik/ince gün.
3) Etkin NOM paketi (2021-11 → 2026-11 ile eğitildi) eski dönemde HİÇ görmediği veride: saat-iklimine göre Brier becerisi, AUC,
   kalibrasyon eğimi; 2020-02-15 → 2020-05-15 çöküş dilimi ayrıca. Eşik/ayar YOK (salt değerlendirme).

python src/faz0_v3_eski_donem.py → results/faz0_v3_eski_donem.json
"""
from __future__ import annotations

import datetime as D
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(H / 'src'))
sys.path.insert(0, str(REPO / 'backend'))
import data_layer as DL  # noqa: E402
import faz12_build as B12  # noqa: E402
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
from services.nom import model_store as MS  # noqa: E402

OLD = ('2018-01-01', '2021-11-01')
CRASH = ('2020-02-15', '2020-05-15')
GRID_S = 900


def build_v3() -> pd.DataFrame:
    m, stats, sm = DL.build_master()
    jan, _ = DL.load_bi5_range(DL.RAW_NEW, D.date(2026, 1, 1), D.date(2026, 2, 7), 'duka_bi5_2026jan')
    if len(jan):
        h = pd.to_datetime(jan.t, unit='s', utc=True).dt.tz_convert(DL.NY).dt.hour.to_numpy()
        jan['spr'] = sm.to_numpy()[h]
        jan['spr_obs'] = np.nan
        m = pd.concat([m, jan[m.columns.intersection(jan.columns)]]).sort_values('t').drop_duplicates('t', keep='first')
    print('spread modeli: v3 bp × fiyat (v1 puan modeli NOM paketi için korunur)', flush=True)
    m = m.reset_index(drop=True)
    # Eski dönem TEK besleme: HistData NSXUSD (2018-01 → 2021-10); Dukascopy 2018 günleri bu dönemde kullanılmaz (karışık besleme, E88)
    hd = pd.read_parquet(H / 'data/histdata_ndx_1m.parquet')
    a, b = (int(pd.Timestamp(x, tz='UTC').timestamp()) for x in OLD)
    hd = hd[(hd.t >= a) & (hd.t < b)].assign(spr=np.nan, spr_obs=np.nan, src='histdata_nsxusd')
    m = pd.concat([m[(m.t < a) | (m.t >= b)], hd[[c for c in m.columns if c in hd.columns]]]).sort_values('t').reset_index(drop=True)
    print('eski dönem kaynağı: HistData NSXUSD', len(hd), 'bar', flush=True)
    # Spread modeli puan cinsindendi (2025 fiyat düzeyi). Fiyat düzeyi farklı dönemlere bp × fiyat olarak taşınır:
    # bp(saat) = max(Dukascopy 2025 gözlenen spread / fiyat, Pepperstone MT5 spread / fiyat) NY-saati medyanı.
    h = pd.to_datetime(m.t, unit='s', utc=True).dt.tz_convert(DL.NY).dt.hour.to_numpy()
    obs = (m.spr_obs.notna() & (m.spr_obs > 0)).to_numpy() if 'spr_obs' in m else np.zeros(len(m), bool)
    bp_duka = pd.Series((m.spr_obs / m.close).to_numpy()[obs]).groupby(h[obs]).median().reindex(range(24)).ffill().bfill()
    g = DL.load_mt5_gold()
    gh = pd.to_datetime(g.t, unit='s', utc=True).dt.tz_convert(DL.NY).dt.hour.to_numpy()
    bp_mt5 = pd.Series((g.spr / g.close).to_numpy()).groupby(gh).median().reindex(range(24)).ffill().bfill()
    bp = np.fmax(bp_duka.to_numpy(), bp_mt5.to_numpy())
    model_spr = bp[h] * m.close.to_numpy()
    m['spr'] = np.where(obs, np.fmax(m.spr_obs.to_numpy(), model_spr), model_spr)
    keep = m[['t', 'open', 'high', 'low', 'close', 'spr', 'src']].copy()
    keep['src'] = keep.src.astype(str)
    keep.to_parquet(H / 'data/ndx_1m_v3.parquet', index=False)
    return keep


def inventory_old(m: pd.DataFrame) -> dict:
    a, b = (int(pd.Timestamp(x, tz='UTC').timestamp()) for x in OLD)
    o = m[(m.t >= a) & (m.t < b)]
    ny = pd.to_datetime(o.t, unit='s', utc=True).dt.tz_convert(DL.NY).dt.date
    per = o.groupby(ny).size()
    wd = [d for d in pd.date_range(OLD[0], OLD[1], inclusive='left').date if d.weekday() < 5]
    return {'bar': int(len(o)), 'gun': int(len(per)), 'beklenen_hafta_ici': len(wd),
            'eksik_hafta_ici': int(len(set(wd) - set(per.index))), 'ince_gun_lt600': int((per < 600).sum()),
            'ilk': str(pd.to_datetime(o.t.min(), unit='s', utc=True)) if len(o) else None,
            'son': str(pd.to_datetime(o.t.max(), unit='s', utc=True)) if len(o) else None}


def brier(p, y):
    return float(((p - np.eye(3)[y]) ** 2).sum(1).mean())


def evaluate_old(m: pd.DataFrame) -> dict:
    mac = pd.read_parquet(H / 'data/macro/macro_daily.parquet')
    cal = pd.read_parquet(H / 'data/macro/calendar.parquet')
    a, b = (int(pd.Timestamp(x, tz='UTC').timestamp()) for x in OLD)
    sub = m[(m.t >= a - 60 * 86400) & (m.t < b + 2 * 86400)].reset_index(drop=True)   # 60 gün ısınma
    td, i0 = B12.decision_grid(sub)
    keep = (td >= a + 30 * 86400) & (td < b) & (td % GRID_S == 0)
    td, i0 = td[keep], i0[keep]
    F = FE.compute_features(sub, td, mac, cal)
    bundle = MS.load_bundle()
    cols = bundle.meta['feature_columns']
    path = LB.Path1m(t=sub.t.to_numpy(), o=sub.open.to_numpy(), h=sub.high.to_numpy(), l=sub.low.to_numpy(),
                     c=sub.close.to_numpy(), spr=sub.spr.to_numpy())
    hr = pd.to_datetime(td, unit='s', utc=True).tz_convert(DL.NY).hour.to_numpy()
    crash = (td >= pd.Timestamp(CRASH[0], tz='UTC').timestamp()) & (td < pd.Timestamp(CRASH[1], tz='UTC').timestamp())
    out = {}
    for hz, spec in LB.HORIZONS.items():
        if hz == 'session':
            te = B12.session_end(td)
            sel = te > 0
        else:
            te = td + spec['minutes'] * 60
            sel = np.ones(len(td), bool)
        idx = np.where(sel)[0]
        atr = F[f"_atr_{spec['atr_tf']}"].to_numpy()[idx]
        L = LB.label_frame(path, i0[idx], atr, te[idx], expected_min=B12.expected_open_minutes(td[idx], te[idx]))
        for d in ('long', 'short'):
            gk = '1x1'
            booster, calb, tm = bundle.target(hz, d, gk)
            y = L[f'{d}_{gk}_cls'].to_numpy()
            ok = y >= 0
            p = calb.apply(booster.predict(F[cols].iloc[idx[ok]]))
            yy = y[ok].astype(int)
            h_ = hr[idx[ok]]
            # iklim: eski dönemin KENDİ saat oranları (eşlenmiş taban; modele avantaj vermez)
            cl = pd.DataFrame({'h': h_, 'y': yy}).groupby('h').y.value_counts(normalize=True).unstack(fill_value=0)
            cl = cl.reindex(columns=[0, 1, 2], fill_value=0).reindex(h_).to_numpy()
            res = {}
            for name, msk in (('tum', np.ones(len(yy), bool)), ('cokus_2020', crash[idx[ok]])):
                if msk.sum() < 100:
                    continue
                bm, bc = brier(p[msk], yy[msk]), brier(cl[msk], yy[msk])
                tp = (yy[msk] == 0).astype(float)
                slope = float(np.polyfit(p[msk][:, 0], tp, 1)[0])
                res[name] = {'n': int(msk.sum()), 'brier_beceri_vs_saat_iklimi': 1 - bm / bc, 'kalibrasyon_egimi_ptp': slope,
                             'ort_p_tp': float(p[msk][:, 0].mean()), 'tp_orani': float(tp.mean()),
                             'ev_r_her_an': float(np.nanmean(L[f'{d}_{gk}_r'].to_numpy()[ok][msk]))}
            out[f'{hz}_{d}_{gk}'] = res
            print(hz, d, json.dumps(res, default=float), flush=True)
    return out


if __name__ == '__main__':
    m = build_v3()
    inv = inventory_old(m)
    print('envanter', inv, flush=True)
    ev = evaluate_old(m) if inv['gun'] > 100 else {'not': 'yetersiz eski dönem verisi'}
    (H / 'results/faz0_v3_eski_donem.json').write_text(json.dumps({'envanter': inv, 'degerlendirme': ev}, indent=1, default=float))
