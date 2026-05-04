"""
Macro Data Service — DXY / VIX / US10Y central provider.

Fetches macro instruments from Yahoo Finance hourly and caches them in-memory
for any model in the system that needs macro context (XAUUSD v2 ML model is
the primary consumer; PULSE/EMEL/SMC can read snapshots via get_snapshot()).

Public API:
    await ensure_started()                 -> idempotent: starts the refresh loop
    get_snapshot()                         -> dict of latest values (for any model)
    get_history(name, timeframe="H1")      -> pandas.DataFrame or None
    align_to_index(name, idx, tf="H1")     -> pandas.Series re-indexed onto idx (ffill)

Thread-safety: refresh runs in a single asyncio task; readers access the dicts
directly (atomic dict-key assignment in CPython is fine for our usage).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Yahoo tickers — feed for ALL models that need macro context
TICKERS = {
    "DXY":   "DX-Y.NYB",   # ICE US Dollar Index — XAU + USOIL inverse
    "VIX":   "^VIX",        # Volatility — risk-on/off proxy for indices
    "US10Y": "^TNX",        # 10-yr yield (%) — XAU + tech rate-sensitivity
    "SPX":   "^GSPC",       # S&P 500 cash — broader US equity tape
    "NQ":    "^IXIC",       # Nasdaq Composite — NDX correlation
    "STOXX": "^STOXX50E",   # Euro Stoxx 50 — DAX peer
}

REFRESH_INTERVAL_SECONDS = 3600   # 1 hour
H1_LOOKBACK_DAYS = 90              # rolling 90-day H1 window kept in memory
D1_LOOKBACK_DAYS = 365             # 1-year D1 window

_history_h1: dict[str, pd.DataFrame] = {}
_history_d1: dict[str, pd.DataFrame] = {}
_last_refresh: dict[str, datetime] = {}
_started: bool = False
_refresh_task: Optional[asyncio.Task] = None
_refresh_lock = asyncio.Lock()


@dataclass
class MacroSnapshot:
    """Latest values + 1h/1d % change for one macro instrument."""
    name: str
    price: float
    change_1h_pct: Optional[float]
    change_1d_pct: Optional[float]
    timestamp: datetime
    age_minutes: float


def _df_from_yf(ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
    """Pull ticker history from yfinance, normalize to UTC index, OHLCV columns."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed — macro service disabled")
        return None
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    except Exception as e:
        logger.warning(f"yfinance fetch failed for {ticker} {interval}: {e}")
        return None
    if df is None or df.empty:
        return None
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df = df.rename(columns=str.lower)
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    df = df[keep].dropna(subset=["close"])
    return df


async def _refresh_once() -> None:
    """Fetch each ticker's H1 and D1 history. Runs sequentially (yfinance is thread-blocking)."""
    loop = asyncio.get_running_loop()
    for name, ticker in TICKERS.items():
        try:
            h1 = await loop.run_in_executor(None, _df_from_yf, ticker, f"{H1_LOOKBACK_DAYS}d", "60m")
            if h1 is not None and not h1.empty:
                _history_h1[name] = h1
            d1 = await loop.run_in_executor(None, _df_from_yf, ticker, f"{D1_LOOKBACK_DAYS}d", "1d")
            if d1 is not None and not d1.empty:
                _history_d1[name] = d1
            _last_refresh[name] = datetime.now(timezone.utc)
            logger.info(f"[macro] {name}: H1={len(h1) if h1 is not None else 0}  "
                        f"D1={len(d1) if d1 is not None else 0}")
        except Exception as e:
            logger.warning(f"[macro] refresh failed for {name}: {e}")


async def _refresh_loop() -> None:
    while True:
        async with _refresh_lock:
            try:
                await _refresh_once()
            except Exception as e:
                logger.exception(f"[macro] refresh loop error: {e}")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


async def ensure_started() -> None:
    """Idempotent — call from FastAPI lifespan startup."""
    global _started, _refresh_task
    if _started:
        return
    _started = True
    # Run an initial fetch synchronously (under lock) so first predicts have data
    async with _refresh_lock:
        await _refresh_once()
    _refresh_task = asyncio.create_task(_refresh_loop(), name="macro_data_refresh_loop")
    logger.info("Macro data service started — refresh interval %ds", REFRESH_INTERVAL_SECONDS)


def get_history(name: str, timeframe: str = "H1") -> Optional[pd.DataFrame]:
    name = name.upper()
    if timeframe.upper() in ("H1", "1H", "60M"):
        return _history_h1.get(name)
    if timeframe.upper() in ("D1", "1D"):
        return _history_d1.get(name)
    return None


def align_to_index(name: str, idx: pd.DatetimeIndex,
                   timeframe: str = "H1", column: str = "close") -> Optional[pd.Series]:
    """Forward-fill macro series onto a target datetime index. Returns None if data missing."""
    df = get_history(name, timeframe)
    if df is None or df.empty:
        return None
    s = df[column].reindex(idx, method="ffill")
    return s


def get_snapshot() -> dict[str, MacroSnapshot]:
    """Latest values + recent change for every loaded macro. Use freely from any model."""
    out: dict[str, MacroSnapshot] = {}
    now = datetime.now(timezone.utc)
    for name, df in _history_h1.items():
        if df is None or df.empty:
            continue
        last_ts = df.index[-1]
        last_close = float(df["close"].iloc[-1])
        prev_h = float(df["close"].iloc[-2]) if len(df) >= 2 else last_close
        change_1h = ((last_close - prev_h) / prev_h * 100) if prev_h else None
        d1 = _history_d1.get(name)
        change_1d = None
        if d1 is not None and len(d1) >= 2:
            prev_d = float(d1["close"].iloc[-2])
            change_1d = ((last_close - prev_d) / prev_d * 100) if prev_d else None
        age_min = (now - last_ts.to_pydatetime()).total_seconds() / 60
        out[name] = MacroSnapshot(name=name, price=last_close,
                                  change_1h_pct=change_1h, change_1d_pct=change_1d,
                                  timestamp=last_ts.to_pydatetime(), age_minutes=age_min)
    return out


def is_ready() -> bool:
    """True if at least one macro has been fetched at least once."""
    return any(name in _history_h1 for name in TICKERS)
