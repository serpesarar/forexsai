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
    "DXY":    "DX-Y.NYB",   # ICE US Dollar Index — XAU + USOIL inverse
    "VIX":    "^VIX",        # Volatility — risk-on/off proxy for indices
    "US10Y":  "^TNX",        # 10-yr yield (%) — XAU + tech rate-sensitivity
    "US3M":   "^IRX",        # 13-week T-bill — short end of curve (10Y-3M term spread)
    "SPX":    "^GSPC",       # S&P 500 cash — broader US equity tape
    "NQ":     "^IXIC",       # Nasdaq Composite — NDX correlation
    "STOXX":  "^STOXX50E",   # Euro Stoxx 50 — DAX peer
    "SPY":    "SPY",         # S&P 500 ETF — risk-on numerator
    "GLD":    "GLD",         # Gold ETF — risk-off denominator
    # — Credit risk appetite (institutional risk-parity desks watch this) —
    "HYG":    "HYG",         # High-yield corporate bond ETF
    "IEF":    "IEF",          # 7-10Y Treasury ETF — credit-spread denominator
    # — 2024-2026 risk indicators (post-2020 regime additions) —
    "BTC":    "BTC-USD",      # Bitcoin — became correlated tech-beta proxy
    "USDJPY": "JPY=X",        # USD/JPY — carry trade barometer (Aug-2024 unwind)
    "COPPER": "HG=F",         # Copper futures — global growth/China demand
    # — FX pairs used by the panel macro-context block —
    "EURUSD": "EURUSD=X",     # Euro / USD — DAX export sensitivity
    "USDTRY": "USDTRY=X",     # USD / Turkish Lira — local context
}

# Legacy panel keys → macro_data_service snapshot names. Used by the context
# builders (background_scheduler / data_hub) that previously queried dead
# vendor symbols like DXY.INDX/VIX.INDX. vdax (VDAX-NEW) has no reliable Yahoo
# ticker, so the panel now surfaces US10Y (10-yr yield) in its place.
PANEL_MACRO_KEYS = {
    "dxy": "DXY",
    "vix": "VIX",
    "us10y": "US10Y",
    "eurusd": "EURUSD",
    "usdtry": "USDTRY",
}


def _preferred_history(name: str):
    """Return the best available history for a macro name: H1 if present,
    else D1. On some hosts (e.g. Railway IPs) yfinance's 60m interval returns
    empty while daily works, so callers must not assume H1 exists."""
    h1 = _history_h1.get(name)
    if h1 is not None and not h1.empty:
        return h1, "H1"
    d1 = _history_d1.get(name)
    if d1 is not None and not d1.empty:
        return d1, "D1"
    return None, None


def get_macro_dict() -> dict:
    """Legacy-shape macro dict for the panel/context builders:
        {"dxy": {"symbol": "DXY", "price": <float|None>, "change_1h_pct": ..}, ...}
    Reads H1 history, falling back to D1 (matches the macro-gauges panel which
    is D1-based). Keys not fetched yet return price=None so callers degrade.
    """
    out: dict = {}
    for panel_key, macro_name in PANEL_MACRO_KEYS.items():
        df, tf = _preferred_history(macro_name)
        if df is None:
            out[panel_key] = {"symbol": macro_name, "price": None}
            continue
        close = df["close"]
        price = float(close.iloc[-1])
        chg = ((price - float(close.iloc[-2])) / float(close.iloc[-2]) * 100) \
            if len(close) >= 2 and float(close.iloc[-2]) else None
        d1 = _history_d1.get(macro_name)
        chg_1d = None
        if d1 is not None and len(d1) >= 2 and float(d1["close"].iloc[-2]):
            chg_1d = (price - float(d1["close"].iloc[-2])) / float(d1["close"].iloc[-2]) * 100
        out[panel_key] = {
            "symbol": macro_name,
            "price": price,
            "change_1h_pct": chg if tf == "H1" else None,
            "change_1d_pct": chg_1d,
        }
    return out

REFRESH_INTERVAL_SECONDS = 3600   # 1 hour
H1_LOOKBACK_DAYS = 90              # rolling 90-day H1 window kept in memory
D1_LOOKBACK_DAYS = 365             # 1-year D1 window

_history_h1: dict[str, pd.DataFrame] = {}
_history_d1: dict[str, pd.DataFrame] = {}
_last_refresh: dict[str, datetime] = {}
_started: bool = False
_refresh_task: Optional[asyncio.Task] = None
_refresh_lock = asyncio.Lock()

# ── Canlı VIX override (Pepperstone → Supabase vix_live → buradaki TÜM VIX okuyucular) ──
# Bulut backend yerel MT5'e bağlanamaz; vix_recorder.py Pepperstone VIX'i Supabase'e yazar,
# bu döngü 60s'de okuyup in-memory VIX serisinin SON kapanışına basar → get_macro_dict /
# get_snapshot / get_history hepsi canlı değeri döndürür (bot VIX-regime scope, meta Layer4b,
# scheduler vol-sizing). Supabase boş/bayat/erişilemez → DOKUNMAZ, yfinance kalır (kırılmaz).
LIVE_VIX_MAX_AGE_S = 900     # 15dk'dan eski → canlı sayma, yfinance'e bırak
LIVE_VIX_POLL_S = 60
_live_vix: dict = {"value": None, "ts": 0.0}


def _read_live_vix() -> Optional[float]:
    import os
    url = os.environ.get("SUPABASE_URL")
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
           or os.environ.get("SUPABASE_KEY"))
    if not url or not key:
        return None
    try:
        import requests
        r = requests.get(
            f"{url.rstrip('/')}/rest/v1/vix_live?symbol=eq.VIX&select=value,ts_utc&limit=1",
            headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=8)
        if r.status_code == 200 and r.json():
            row = r.json()[0]
            ts = datetime.fromisoformat(str(row["ts_utc"]).replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - ts).total_seconds() < LIVE_VIX_MAX_AGE_S:
                return float(row["value"])
    except Exception as e:
        logger.warning(f"[macro] live VIX read failed: {e}")
    return None


def _inject_live_vix(value: float) -> None:
    """Canlı VIX'i in-memory VIX serisinin son kapanışına yaz → tüm okuma yolları canlı döner."""
    for store in (_history_h1, _history_d1):
        df = store.get("VIX")
        if df is not None and not df.empty and "close" in df.columns:
            df.iloc[-1, df.columns.get_loc("close")] = float(value)


async def _live_vix_loop() -> None:
    loop = asyncio.get_running_loop()
    while True:
        try:
            v = await loop.run_in_executor(None, _read_live_vix)
            if v is not None:
                _live_vix.update(value=v, ts=datetime.now(timezone.utc).timestamp())
                _inject_live_vix(v)
        except Exception as e:
            logger.warning(f"[macro] live VIX loop error: {e}")
        await asyncio.sleep(LIVE_VIX_POLL_S)


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
    asyncio.create_task(_live_vix_loop(), name="macro_live_vix_loop")   # Pepperstone canlı VIX
    logger.info("Macro data service started — refresh %ds + canlı VIX (Supabase vix_live) takibi",
                REFRESH_INTERVAL_SECONDS)


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


# Panel/legacy symbol → macro snapshot name (e.g. "DXY.INDX" → "DXY").
_PANEL_SYMBOL_TO_MACRO = {
    "DXY.INDX": "DXY", "DXY": "DXY",
    "VIX.INDX": "VIX", "VIX": "VIX",
    "V1X.INDX": "VIX",            # VDAX unavailable on Yahoo — fall back to VIX
    "US10Y": "US10Y", "^TNX": "US10Y",
    "EURUSD": "EURUSD", "EURUSD.FOREX": "EURUSD",
    "USDTRY": "USDTRY", "USDTRY.FOREX": "USDTRY",
}


def _resolve_macro_name(symbol: str) -> Optional[str]:
    return _PANEL_SYMBOL_TO_MACRO.get((symbol or "").upper().strip())


def get_candles_list(symbol: str, timeframe: str = "H1", limit: int = 240) -> list[dict]:
    """Macro candles as a list of OHLCV dicts (yfinance-backed), for callers that
    previously fetched DXY.INDX/VIX.INDX intraday candles. Accepts panel symbols
    (e.g. 'DXY.INDX') or macro names ('DXY'). Returns [] if not loaded yet.

    Note: macro history is H1/D1 only (yfinance), so 5m requests are served at H1.
    """
    name = _resolve_macro_name(symbol) or (symbol or "").upper().strip()
    if timeframe.upper() in ("D1", "1D"):
        df = get_history(name, "D1")
    else:
        df, _ = _preferred_history(name)  # H1, else D1 fallback
    if df is None or df.empty:
        return []
    out = []
    for ts, row in df.tail(limit).iterrows():
        out.append({
            "date": ts.isoformat(),
            "timestamp": int(ts.timestamp() * 1000),
            "open": float(row.get("open", row["close"])),
            "high": float(row.get("high", row["close"])),
            "low": float(row.get("low", row["close"])),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0) or 0),
        })
    return out


def macro_ta_snapshot(symbol: str) -> dict:
    """Lightweight TA snapshot for a macro instrument, derived from the yfinance
    H1 history. Drop-in replacement for compute_ta_snapshot('DXY.INDX'/'VIX.INDX')
    for the fields consumers actually read: trend / confidence / current_price.
    """
    name = _resolve_macro_name(symbol) or (symbol or "").upper().strip()
    df, _ = _preferred_history(name)  # H1, else D1 fallback
    if df is None or df.empty:
        return {"trend": "NEUTRAL", "confidence": 50.0, "current_price": None}
    close = df["close"]
    price = float(close.iloc[-1])
    ema = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    dist_pct = ((price - ema) / ema * 100) if ema else 0.0
    if dist_pct > 0.15:
        trend = "BULLISH"
    elif dist_pct < -0.15:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    confidence = max(50.0, min(95.0, 50.0 + abs(dist_pct) * 10.0))
    return {"trend": trend, "confidence": round(confidence, 1), "current_price": price}
