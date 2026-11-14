"""Yön Lab veri katmanı v2: NOM data_layer (aynı temizlik kuralları) + bu oturumda inen 2026-01 → 02-07 Dukascopy günleri.
NOM'un ndx_1m_v1.parquet'ine DOKUNMAZ (NOM paketinin veri sürümü sabit kalır). Çıktı: data/ndx_1m_v2.parquet (2021-11 →)."""
import sys
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H.parent / 'nom_20261113/src'))
import data_layer as DL  # noqa: E402

if __name__ == '__main__':
    import datetime as D
    import numpy as np
    m, stats, sm = DL.build_master()
    jan, st = DL.load_bi5_range(DL.RAW_NEW, D.date(2026, 1, 1), D.date(2026, 2, 7), 'duka_bi5_2026jan')
    print('2026-01 boşluk dolgusu', st)
    if len(jan):
        h = pd.to_datetime(jan.t, unit='s', utc=True).dt.tz_convert(DL.NY).dt.hour.to_numpy()
        jan['spr'] = sm.to_numpy()[h]
        jan['spr_obs'] = np.nan
        m = pd.concat([m, jan[m.columns.intersection(jan.columns)]]).sort_values('t').drop_duplicates('t', keep='first')
        m, nspk = DL.spike_filter(m.reset_index(drop=True))
        print('spike', nspk)
    m = m[m.t >= pd.Timestamp('2021-11-01', tz='UTC').timestamp()].reset_index(drop=True)
    keep = m[['t', 'open', 'high', 'low', 'close', 'spr', 'src']].copy()
    keep['src'] = keep.src.astype(str)
    keep.to_parquet(H / 'data/ndx_1m_v2.parquet', index=False)
    ts = pd.to_datetime(keep.t, unit='s', utc=True)
    print(len(keep), ts.min(), ts.max())
    print(keep.groupby(ts.dt.strftime('%Y-%m')).size().loc['2025-11':].to_dict())
