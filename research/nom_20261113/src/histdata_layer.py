"""HistData.com NSXUSD M1 (2018–2021) → UTC 1m barlar + Dukascopy ile çakışan dönemlerde besleme/saat ekseni denetimi.

HistData belgesi "yaz saatsiz EST (UTC−5 sabit)" der; NSXUSD için bu YANLIŞ (E135, 2026-11-14): Dukascopy 2018 ile kışta gecikme 0
(r 0,97), yazda −60 dk (r 0,993) → damgalar ET'dir ama yaz saati geçişi YILA göre farklı: 2018 dosyası ABD takvimi (New York yerel), 2019–2021
dosyaları AB takvimi (son Pazar Mart → son Pazar Ekim arası UTC−4, dışı UTC−5). Kanıt: geçiş pencerelerindeki FOMC/NFP anları
(2018-03-21 FOMC etiket 14:00; 2019-03-20, 2019-10-30, 2021-03-17, 2021-11-03 FOMC etiket 13:00; 2019-11-01 / 2021-11-05 NFP 07:30;
yaz ortası FOMC'ler her yıl 14:00). İlk sürüm sabit +5 sa kullanıyordu; doğrulama yalnız kış pencerelerinde yapıldığı için yaz
kayması görülmedi. Doğrulama artık kış VE yaz penceresinde ayrı ayrı gecikme 0
ister (E2/E78/E93 dersi: saat ekseni ölçülmeden varsayılmaz; mevsimlere ayrı bakılır). Temizlik: NOM data_layer kuralları (R1 kapalı saat, R2 OHLC).
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
NY_TZ = 'America/New_York'   # DST geçişleri Pazar 02:00 ET — piyasa kapalı, belirsiz/olmayan saat yok (NaT düşer)


def _eu_summer(t_utc: np.ndarray) -> np.ndarray:
    """AB yaz saati: son Pazar Mart 01:00 UTC ≤ t < son Pazar Ekim 01:00 UTC."""
    ts = pd.DatetimeIndex(pd.to_datetime(np.asarray(t_utc), unit="s", utc=True))
    out = np.zeros(len(ts), bool)
    for y in np.unique(ts.year):
        def last_sun(m: int) -> pd.Timestamp:
            e = pd.Timestamp(year=int(y), month=m, day=31, tz='UTC')
            return (e - pd.Timedelta(days=(e.weekday() + 1) % 7)).replace(hour=1)
        out |= np.asarray((ts >= last_sun(3)) & (ts < last_sun(10)))
    return out


def load() -> pd.DataFrame:
    parts = []
    for f in sorted(SRC.glob('HISTDATA_COM_ASCII_NSXUSD_M1*/DAT_ASCII_NSXUSD_M1_*.csv')):
        d = pd.read_csv(f, sep=';', header=None, names=['ts', 'open', 'high', 'low', 'close', 'vol'])
        t = pd.to_datetime(d.ts, format='%Y%m%d %H%M%S')
        year = int(f.stem[-4:])
        if year <= 2018:   # ABD yaz saati takvimi
            tu = t.dt.tz_localize(NY_TZ, ambiguous='NaT', nonexistent='NaT')
            d = d[tu.notna().to_numpy()].copy()
            d['t'] = (tu.dropna().dt.tz_convert('UTC').astype('int64') // 10**9).astype('int64').to_numpy()
        else:              # AB yaz saati takvimi: etiket + 4 sa (AB yazı) / + 5 sa
            naive = t.astype('int64') // 10**9
            off = np.where(_eu_summer(naive + 5 * 3600), 4 * 3600, 5 * 3600)
            d['t'] = (naive + off).astype('int64')
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
    kis = duka_new[duka_new.t < pd.Timestamp('2018-03-11', tz='UTC').timestamp()]
    yaz = duka_new[duka_new.t >= pd.Timestamp('2018-03-12', tz='UTC').timestamp()]
    for name, ref in (('dukascopy_2021_11_12', v3[(v3.t >= 1635724800) & (v3.t < 1640995200)]), ('dukascopy_2018_kis', kis),
                      ('dukascopy_2018_yaz', yaz)):
        c = F0.compare(h, ref, 'histdata', name)
        out[name] = {k: c.get(k) for k in ('overlap_bars', 'best_lag_min', 'best_lag_corr', 'ret_corr_lag0',
                                            'agree_within_tol_frac', 'level_offset_median_pts', 'days_agree_lt80pct', 'days_total')}
    yr = pd.to_datetime(h.t, unit='s', utc=True).dt.year
    out['yil_bar'] = h.groupby(yr).size().to_dict()
    (H / 'results/faz0_histdata_denetim.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
