"""HistData.com NSXUSD M1 (2018–2021) → UTC 1m barlar + Dukascopy ile çakışan dönemlerde besleme/saat ekseni denetimi.

HistData belgesi: saat dilimi yaz saatsiz EST (UTC−5 sabit). Doğrulama: çakışan dönemde gecikme taraması (±90 dk) en iyi gecikme 0
olmalı (E2/E78/E93 dersi: saat ekseni ölçülmeden varsayılmaz). Temizlik: NOM data_layer kuralları (R1 kapalı saat, R2 OHLC).
Çıktı: data/histdata_ndx_1m.parquet, results/faz0_histdata_denetim.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'src'))
import data_layer as DL  # noqa: E402
import faz0_build as F0  # noqa: E402

SRC = H / 'data/histdata'
EST_OFFSET_S = 5 * 3600


def load() -> pd.DataFrame:
    parts = []
    for f in sorted(SRC.glob('HISTDATA_COM_ASCII_NSXUSD_M1*/DAT_ASCII_NSXUSD_M1_*.csv')):
        d = pd.read_csv(f, sep=';', header=None, names=['ts', 'open', 'high', 'low', 'close', 'vol'])
        t = pd.to_datetime(d.ts, format='%Y%m%d %H%M%S')
        d['t'] = (t.astype('int64') // 10**9 + EST_OFFSET_S).astype('int64')
        parts.append(d[['t', 'open', 'high', 'low', 'close']])
    m = pd.concat(parts).sort_values('t').drop_duplicates('t').reset_index(drop=True)
    ts = pd.to_datetime(m.t, unit='s', utc=True)
    r1 = DL.closed_mask(ts)
    r2 = ((m.high < m[['open', 'close']].max(axis=1)) | (m.low > m[['open', 'close']].min(axis=1))).to_numpy()
    st = {'satir': int(len(m)), 'R1_kapali': int(r1.sum()), 'R2_ohlc': int((r2 & ~r1).sum())}
    m = m[~(r1 | r2)].reset_index(drop=True)
    m, nspk = DL.spike_filter(m)
    st['R4_sicrama'] = nspk
    return m, st


if __name__ == '__main__':
    h, st = load()
    h.to_parquet(H / 'data/histdata_ndx_1m.parquet', index=False)
    v3 = pd.read_parquet(H.parent / 'yon_lab_20261114/data/ndx_1m_v2.parquet')
    duka_new = DL.load_bi5_range(DL.RAW_NEW, __import__('datetime').date(2018, 1, 1), __import__('datetime').date(2018, 12, 31), 'd18')[0]
    out = {'temizlik': st, 'kapsam': [str(pd.to_datetime(h.t.min(), unit='s', utc=True)), str(pd.to_datetime(h.t.max(), unit='s', utc=True))]}
    for name, ref in (('dukascopy_2021_11_12', v3[(v3.t >= 1635724800) & (v3.t < 1640995200)]), ('dukascopy_2018_bas', duka_new)):
        c = F0.compare(h, ref, 'histdata', name)
        out[name] = {k: c.get(k) for k in ('overlap_bars', 'best_lag_min', 'best_lag_corr', 'ret_corr_lag0',
                                            'agree_within_tol_frac', 'level_offset_median_pts', 'days_agree_lt80pct', 'days_total')}
    yr = pd.to_datetime(h.t, unit='s', utc=True).dt.year
    out['yil_bar'] = h.groupby(yr).size().to_dict()
    (H / 'results/faz0_histdata_denetim.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
