"""NOM — canlı veri: NDX 1m (Supabase candle_cache, kutudaki MT5 kaydedicisinin yazdığı broker barları),
günlük makro (yfinance) ve olay takvimi (paketli parquet).

Neden candle_cache: MT5 köprüsünün 1m çıktısı oraya yazılıyor (data_recorder.py, besleme kilidi 2026-11-04).
Faz 0: 2026-03-08 sonrası candle_cache ↔ MT5 altın standart gecikme 0, r=0,994. Öncesi (E4: −60 dk) PENCERE DIŞI
(LIVE_HISTORY_DAYS = 240 → en eski bar ≈ 2026-03-18 bugün itibarıyla; tarih ilerledikçe sorun büyümez).
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .features import LIVE_HISTORY_DAYS

logger = logging.getLogger(__name__)
BACKEND = Path(__file__).resolve().parents[2]
CACHE = BACKEND / 'data' / 'nom_cache'
CAL_FILE = BACKEND / 'data' / 'nom' / 'calendar.csv'          # git'te (parquet .gitignore'da)
SYMBOL = 'NDX.INDX'
PAGE = 1000
REFRESH_S = 30
MACRO_REFRESH_S = 6 * 3600
MACRO_SYMS = {'VIX': '^VIX', 'VIX9D': '^VIX9D', 'VIX3M': '^VIX3M', 'SPX': '^GSPC', 'NDX': '^NDX', 'QQQ': 'QQQ',
              'DXY': 'DX-Y.NYB', 'TNX': '^TNX'}
NY = 'America/New_York'
_lock = threading.Lock()
_state: dict = {'bars': None, 'bars_ts': 0.0, 'macro': None, 'macro_ts': 0.0}


def _fetch_rows(since_iso: str) -> list[dict]:
    from database.supabase_client import get_supabase_client
    db = get_supabase_client()
    if db is None:
        raise RuntimeError('veritabanı bağlantısı yok')
    rows: list[dict] = []
    since = since_iso
    while True:
        res = (db.table('candle_cache').select('candle_time,open,high,low,close').eq('symbol', SYMBOL)
               .eq('timeframe', '1m').gt('candle_time', since).order('candle_time').limit(PAGE).execute())
        chunk = getattr(res, 'data', None) or (res.get('data') if isinstance(res, dict) else None) or []
        rows += chunk
        if len(chunk) < PAGE:
            break
        since = chunk[-1]['candle_time']
    return rows


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Faz 0 kuralları: kapalı saat (R1), OHLC tutarsızlığı (R2), duplike; yalnız KAPANMIŞ barlar."""
    df = df.drop_duplicates('t').sort_values('t')
    ts = pd.to_datetime(df.t, unit='s', utc=True).dt.tz_convert(NY)
    closed = (ts.dt.hour == 17) | (ts.dt.weekday == 5) | ((ts.dt.weekday == 6) & (ts.dt.hour < 18)) | \
             ((ts.dt.weekday == 4) & (ts.dt.hour >= 17))
    bad = (df.high < df[['open', 'close']].max(axis=1)) | (df.low > df[['open', 'close']].min(axis=1))
    done = df.t + 60 <= time.time()
    return df[~closed.to_numpy() & ~bad.to_numpy() & done.to_numpy()].reset_index(drop=True)


def load_bars(force: bool = False) -> pd.DataFrame:
    """Son LIVE_HISTORY_DAYS günün 1m barları (disk önbelleği + artımlı çekim)."""
    with _lock:
        now = time.time()
        if not force and _state['bars'] is not None and now - _state['bars_ts'] < REFRESH_S:
            return _state['bars']
        CACHE.mkdir(parents=True, exist_ok=True)
        f = CACHE / 'ndx_1m.parquet'
        old = pd.read_parquet(f) if f.exists() else pd.DataFrame(columns=['t', 'open', 'high', 'low', 'close'])
        start = datetime.now(timezone.utc) - timedelta(days=LIVE_HISTORY_DAYS)
        if len(old):
            since = datetime.fromtimestamp(int(old.t.max()) - 3600, tz=timezone.utc)   # son saati yeniden çek
            since = max(since, start)
        else:
            since = start
        rows = _fetch_rows(since.isoformat())
        new = pd.DataFrame(rows)
        if len(new):
            new['t'] = (pd.to_datetime(new.candle_time, utc=True).astype('int64') // 10**9).astype('int64')
            new = new[['t', 'open', 'high', 'low', 'close']].astype({'open': float, 'high': float, 'low': float, 'close': float})
            keep = old[old.t < new.t.min()]
            old = pd.concat([keep, new], ignore_index=True) if len(keep) else new.reset_index(drop=True)
        old = old[old.t >= start.timestamp()]
        b = _clean(old)
        b.to_parquet(f, index=False)
        _state['bars'], _state['bars_ts'] = b, now
        return b


def load_macro(force: bool = False) -> pd.DataFrame | None:
    with _lock:
        now = time.time()
        if not force and _state['macro'] is not None and now - _state['macro_ts'] < MACRO_REFRESH_S:
            return _state['macro']
        f = CACHE / 'macro_daily.parquet'
        try:
            import yfinance as yf
            frames = []
            for k, s in MACRO_SYMS.items():
                d = yf.download(s, period='2y', progress=False, auto_adjust=False, threads=False)
                if d is None or d.empty:
                    continue
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                cols = {'Close': f'{k}_close'}
                if k == 'QQQ':
                    cols['Volume'] = 'QQQ_volume'
                x = d[list(cols)].rename(columns=cols)
                x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
                frames.append(x)
            m = pd.concat(frames, axis=1).sort_index()
            m.index.name = 'date'
            m = m.reset_index()
            CACHE.mkdir(parents=True, exist_ok=True)
            m.to_parquet(f, index=False)
        except Exception as e:  # noqa: BLE001 — makro yoksa özellikler NaN olur (model NaN'ı eğitimde gördü)
            logger.warning('NOM makro indirilemedi: %s', e)
            m = pd.read_parquet(f) if f.exists() else None
        _state['macro'], _state['macro_ts'] = m, now
        return m


def load_calendar() -> pd.DataFrame | None:
    try:
        c = pd.read_csv(CAL_FILE)
        c['ts_utc'] = pd.to_datetime(c.ts_utc, utc=True)
        return c
    except Exception as e:  # noqa: BLE001
        logger.warning('NOM takvim yok: %s', e)
        return None


def market_open(now: float | None = None) -> bool:
    ts = pd.Timestamp(now or time.time(), unit='s', tz='UTC').tz_convert(NY)
    wd, hr = ts.weekday(), ts.hour
    return not (hr == 17 or wd == 5 or (wd == 6 and hr < 18) or (wd == 4 and hr >= 17))


def bars_from_rows(rows: list[dict]) -> pd.DataFrame:
    """Test/araç yardımcı: candle_cache satırları → temiz 1m DataFrame."""
    df = pd.DataFrame(rows)
    df['t'] = (pd.to_datetime(df.candle_time, utc=True).astype('int64') // 10**9).astype('int64')
    return _clean(df[['t', 'open', 'high', 'low', 'close']].astype({'open': float, 'high': float, 'low': float, 'close': float}))


__all__ = ['load_bars', 'load_macro', 'load_calendar', 'market_open', 'bars_from_rows', 'np']
