"""NOM Faz 0 — makro seriler (yfinance, günlük) + ekonomik takvim + mega-cap bilanço tarihleri.

Çıktılar data/macro/:
  macro_daily.parquet : date (NY işlem günü), <sym>_close/_open/_high/_low (+QQQ volume)
  calendar.parquet    : ts_utc, event (FOMC/CPI/NFP/JH/EARN_<TICKER>), date
Sızıntı notu (E99): günlük kapanışlar NY 16:00-16:15 sonrası kesinleşir → özellikler YALNIZ
ÖNCEKİ işlem gününün kapanışını kullanır (features.py sorumluluğu).
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
import pandas as pd
import yfinance as yf

H = Path(__file__).resolve().parents[1]
OUT = H / 'data' / 'macro'
REPO = H.parents[1]
SYMS = {'VIX': '^VIX', 'VIX9D': '^VIX9D', 'VIX3M': '^VIX3M', 'SPX': '^GSPC', 'ES': 'ES=F',
        'NDX': '^NDX', 'QQQ': 'QQQ', 'DXY': 'DX-Y.NYB', 'TNX': '^TNX'}
EARN = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA']
START = '2012-01-01'
# 2026 FOMC karar günleri (federalreserve.gov 2026 takvimi; 03_calendar.py listesi 06-17'de bitiyor)
FOMC_2026_EXTRA = ['2026-07-29', '2026-09-16', '2026-10-28', '2026-12-09']
# BLS 2026 takvimi (bls.gov/schedule/2026, 2026-11-13'te doğrulandı; kaynak liste CPI 09-11'de bitiyordu)
CPI_2026_EXTRA = ['2026-10-14', '2026-11-10', '2026-12-10']
NFP_2026_EXTRA = ['2026-10-02', '2026-11-06', '2026-12-04']


def fetch_macro() -> pd.DataFrame:
    frames = []
    for k, s in SYMS.items():
        for attempt in range(3):
            try:
                d = yf.download(s, start=START, progress=False, auto_adjust=False, threads=False)
                break
            except Exception as ex:  # noqa: BLE001
                print('retry', s, ex, flush=True); time.sleep(5)
        if d is None or d.empty:
            print('BOS', k, s, flush=True); continue
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        cols = {'Open': f'{k}_open', 'High': f'{k}_high', 'Low': f'{k}_low', 'Close': f'{k}_close'}
        if k == 'QQQ':
            cols['Volume'] = 'QQQ_volume'
        x = d[list(cols)].rename(columns=cols)
        x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
        frames.append(x)
        print(k, s, len(x), x.index.min().date(), x.index.max().date(), flush=True)
    m = pd.concat(frames, axis=1).sort_index()
    m.index.name = 'date'
    return m.reset_index()


def build_calendar() -> pd.DataFrame:
    src = REPO / 'research/xau_best_days_20261015/makro/out/calendar.csv'
    c = pd.read_csv(src)
    c = c[['event', 'date', 'et']]
    extra = pd.concat([pd.DataFrame({'event': 'FOMC', 'date': FOMC_2026_EXTRA, 'et': '14:00'}),
                       pd.DataFrame({'event': 'CPI', 'date': CPI_2026_EXTRA, 'et': '08:30'}),
                       pd.DataFrame({'event': 'NFP', 'date': NFP_2026_EXTRA, 'et': '08:30'})])
    c = pd.concat([c, extra]).drop_duplicates(['event', 'date'])
    rows = []
    for t in EARN:
        try:
            e = yf.Ticker(t).get_earnings_dates(limit=100)
        except Exception as ex:  # noqa: BLE001
            print('earn fail', t, ex, flush=True); continue
        if e is None or e.empty:
            continue
        for ts in e.index:
            tny = pd.Timestamp(ts).tz_convert('America/New_York')
            # bilanço çoğu kapanış sonrası (16:00+) ya da açılış öncesi; zaman damgası yfinance'tan
            rows.append(('EARN_' + t, tny.strftime('%Y-%m-%d'), tny.strftime('%H:%M')))
        print('earn', t, len(e), flush=True)
    c = pd.concat([c, pd.DataFrame(rows, columns=['event', 'date', 'et'])])
    c['ts_utc'] = pd.to_datetime(c.date + ' ' + c.et).dt.tz_localize('America/New_York').dt.tz_convert('UTC')
    return c.sort_values('ts_utc').reset_index(drop=True)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    if '--calendar-only' not in sys.argv:
        m = fetch_macro(); m.to_parquet(OUT / 'macro_daily.parquet', index=False)
    c = build_calendar(); c.to_parquet(OUT / 'calendar.parquet', index=False)
    c.to_csv(REPO / 'backend/data/nom/calendar.csv', index=False)          # canlı servisin okuduğu kopya
    print(c.event.str.split('_').str[0].value_counts().to_dict())
    print('cal range', c.ts_utc.min(), c.ts_utc.max())
