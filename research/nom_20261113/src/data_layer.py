"""NOM Faz 0 — temiz, versiyonlanmış NDX 1m veri katmanı.

Birleşik seri (UTC, bar AÇILIŞ zamanı `t` epoch sn), BID OHLC + spread (ask−bid, puan):
  2018-01 → 2021-10 : Dukascopy USATECHIDXUSD 1m BID bi5 (bu çalışmada indirildi, data/duka_m1)
  2021-11 → 2023-12 : Dukascopy 1m BID bi5 (research/ndx_seans_tasima_20261103/denetim/data/duka_m1)
  2024-01 → 2026-11 : research/haber_derin_20261105/data/NDX_1m.parquet (Dukascopy; 2025 gerçek bid/ask,
                      2024 ve 2026 ask'ı 2025 NY-saati medyan spread'inden türetilmiş)
  2026-11-04 → bugün: data/duka_m1 (bu çalışmada indirilen BID uzatma, varsa)

Temizlik kuralları (sırayla, sayaçlarla raporlanır):
  R1 kapalı saat: NY 17:00-17:59 günlük ara, Cuma 17:00 → Pazar 18:00 hafta sonu
  R2 OHLC tutarsızlığı (high < max(o,c) veya low > min(o,c))
  R3 düz sıfır-hacim bar (Dukascopy işlem olmayan dakikayı düz bar olarak doldurur) — yalnız bi5'te
  R4 sıçrama: |log getiri| > SPIKE_K × (gün içi 1m getiri MAD) VE sonraki barda ≥%80 geri dönüş → bar silinir
  R5 tatil/yarım gün: NYSE takvimi (static, nyse_calendar.py) — barlar silinmez, `session_flag` ile işaretlenir
Spread: tüm dönemlere tek bir koruyucu model uygulanır: max(Dukascopy 2025 gerçek, Pepperstone MT5) NY-saati medyanı.
"""
from __future__ import annotations

import datetime as D
import lzma
import struct
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
NY = 'America/New_York'
RAW_NEW = H / 'data' / 'duka_m1'
RAW_OLD = REPO / 'research/ndx_seans_tasima_20261103/denetim/data/duka_m1'
NDX_1M_2024 = REPO / 'research/haber_derin_20261105/data/NDX_1m.parquet'
MT5_GOLD = REPO / 'nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv'
SPIKE_K = 25.0
SPIKE_REVERT = 0.8
PIP_MT5 = 0.1           # NAS100 MT5 'spread' alanı puan cinsinden 0.1 adım


def parse_bi5(f: Path, day: D.date) -> list[tuple]:
    """Dukascopy günlük 1m candle bi5 → (t, o, h, l, c, vol). Kayıt: ms_offset?, O, C, L, H (×1000), vol."""
    if not f.exists() or f.stat().st_size == 0:
        return []
    base = int(D.datetime(day.year, day.month, day.day, tzinfo=D.timezone.utc).timestamp())
    raw = lzma.decompress(f.read_bytes())
    return [(base + r[0], r[1] / 1000., r[4] / 1000., r[3] / 1000., r[2] / 1000., r[5])
            for r in struct.iter_unpack('>IIIIIf', raw)]


def closed_mask(ts: pd.Series) -> np.ndarray:
    """R1: NY 17:00 saati + hafta sonu kapalı."""
    ny = ts.dt.tz_convert(NY)
    wd, hr = ny.dt.weekday, ny.dt.hour
    c = (hr == 17) | (wd == 5) | ((wd == 6) & (hr < 18)) | ((wd == 4) & (hr >= 17))
    return c.to_numpy()


def load_bi5_range(raw: Path, start: D.date, end: D.date, src: str) -> tuple[pd.DataFrame, dict]:
    rows: list[tuple] = []
    d = start
    nfiles = nempty = 0
    while d <= end:
        if d.weekday() != 5:
            f = raw / f'{d:%Y%m%d}_BID.bi5'
            if f.exists():
                nfiles += 1
                r = parse_bi5(f, d)
                nempty += int(not r)
                rows += r
        d += D.timedelta(1)
    b = pd.DataFrame(rows, columns=['t', 'open', 'high', 'low', 'close', 'vol'])
    st = {'src': src, 'files': nfiles, 'empty_files': nempty, 'raw_rows': len(b)}
    if b.empty:
        return b.assign(spr=np.nan, src=src), st
    b = b.sort_values('t')
    st['dup_t'] = int(b.t.duplicated().sum())
    b = b.drop_duplicates('t')
    ts = pd.to_datetime(b.t, unit='s', utc=True)
    r1 = closed_mask(ts)
    r2 = ((b.high < b[['open', 'close']].max(axis=1)) | (b.low > b[['open', 'close']].min(axis=1))).to_numpy()
    r3 = ((b.vol == 0) & (b.high == b.low)).to_numpy()
    st.update({'R1_closed': int(r1.sum()), 'R2_bad_ohlc': int((r2 & ~r1).sum()),
               'R3_flat_zero_vol': int((r3 & ~r1 & ~r2).sum())})
    b = b[~(r1 | r2 | r3)].copy()
    b['spr'] = np.nan
    b['src'] = src
    return b[['t', 'open', 'high', 'low', 'close', 'vol', 'spr', 'src']], st


def load_2024plus() -> tuple[pd.DataFrame, dict]:
    a = pd.read_parquet(NDX_1M_2024)
    st = {'src': 'haber_derin_NDX_1m', 'raw_rows': len(a), 'dup_t': int(a.t.duplicated().sum())}
    a = a.drop_duplicates('t').sort_values('t')
    ts = pd.to_datetime(a.t, unit='s', utc=True)
    r1 = closed_mask(ts)
    r2 = ((a.high < a[['open', 'close']].max(axis=1)) | (a.low > a[['open', 'close']].min(axis=1))).to_numpy()
    st.update({'R1_closed': int(r1.sum()), 'R2_bad_ohlc': int((r2 & ~r1).sum())})
    a = a[~(r1 | r2)].copy()
    a['spr'] = np.where(a.src == 'duka25_ba', (a.ask_open - a.open).clip(lower=0), np.nan)
    a['vol'] = np.nan
    return a[['t', 'open', 'high', 'low', 'close', 'vol', 'spr', 'src']], st


def spike_filter(m: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """R4: tek-bar sıçrama (git-gel) silinir. Ölçek: aynı UTC günündeki 1m |getiri| medyanı."""
    lr = np.log(m.close.to_numpy())
    r = np.diff(lr, prepend=lr[0])
    day = (m.t.to_numpy() // 86400)
    med = pd.Series(np.abs(r)).groupby(day).transform('median').to_numpy() + 1e-9
    nxt = np.r_[r[1:], 0.0]
    spike = (np.abs(r) > SPIKE_K * med) & (np.sign(nxt) == -np.sign(r)) & (np.abs(nxt) >= SPIKE_REVERT * np.abs(r))
    return m[~spike].reset_index(drop=True), int(spike.sum())


def spread_model(m: pd.DataFrame, mt5_hourly: pd.Series | None) -> pd.Series:
    """NY saati (0-23) → koruyucu spread (puan) = max(Dukascopy 2025 gerçek medyan, Pepperstone MT5 medyan)."""
    x = m.dropna(subset=['spr'])
    h = pd.to_datetime(x.t, unit='s', utc=True).dt.tz_convert(NY).dt.hour
    duka = x.spr.groupby(h).median().reindex(range(24)).ffill().bfill()
    if mt5_hourly is None:
        return duka
    return pd.concat([duka, mt5_hourly.reindex(range(24)).ffill().bfill()], axis=1).max(axis=1)


def load_mt5_gold() -> pd.DataFrame:
    g = pd.read_csv(MT5_GOLD)
    g['t'] = (pd.to_datetime(g.time_utc, utc=True).astype('int64') // 10**9).astype('int64')
    g['spr'] = g.spread * PIP_MT5
    return g[['t', 'open', 'high', 'low', 'close', 'tick_volume', 'spr']]


def mt5_spread_hourly(g: pd.DataFrame) -> pd.Series:
    h = pd.to_datetime(g.t, unit='s', utc=True).dt.tz_convert(NY).dt.hour
    return g.spr.groupby(h).median()


def build_master() -> tuple[pd.DataFrame, list[dict], pd.Series]:
    stats = []
    parts = []
    b1, s1 = load_bi5_range(RAW_NEW, D.date(2018, 1, 1), D.date(2021, 10, 31), 'duka_bi5_2018_2021')
    stats.append(s1); parts.append(b1)
    b2, s2 = load_bi5_range(RAW_OLD, D.date(2021, 11, 1), D.date(2023, 12, 31), 'duka_bi5_2021_2023')
    stats.append(s2); parts.append(b2)
    a, s3 = load_2024plus()
    stats.append(s3); parts.append(a)
    last = pd.to_datetime(a.t.max(), unit='s', utc=True).date()
    b4, s4 = load_bi5_range(RAW_NEW, last + D.timedelta(1), D.date.today(), 'duka_bi5_ext_2026')
    stats.append(s4); parts.append(b4)
    m = pd.concat([p for p in parts if len(p)]).sort_values('t').drop_duplicates('t', keep='last')
    m = m.reset_index(drop=True)
    m, nspk = spike_filter(m)
    stats.append({'src': 'ALL', 'R4_spikes_removed': nspk, 'rows': len(m)})
    gold = load_mt5_gold()
    sm = spread_model(m, mt5_spread_hourly(gold))
    h = pd.to_datetime(m.t, unit='s', utc=True).dt.tz_convert(NY).dt.hour.to_numpy()
    m['spr_model'] = sm.to_numpy()[h]
    m['spr_obs'] = m.spr
    m['spr'] = np.fmax(m.spr.fillna(0).to_numpy(), m.spr_model.to_numpy())   # koruyucu: gözlenen ile model maks.
    return m, stats, sm
