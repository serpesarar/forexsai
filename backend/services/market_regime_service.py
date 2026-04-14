"""
Market Regime Detection Service - XAUUSD Adaptive Trading System

Detects market regime using ADX + ATR + Swing Structure (HH/HL) analysis.
Provides regime-based model weights, RSI threshold overrides, ATH breakout protocol,
session filtering, and fake signal protection.

Regimes:
  STRONG_TREND_UP   - ADX>25, bullish structure → only LONG, RSI>70 = momentum
  STRONG_TREND_DOWN - ADX>25, bearish structure → only SHORT, RSI<30 = momentum
  RANGING           - ADX<20, low volatility → mean reversion, S/R active
  TRANSITION        - everything else → low risk, small positions

Cached per symbol, refreshed every 30 minutes or on-demand.
"""
from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timezone
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Dict, Any, Optional, List, Literal

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# REGIME TYPES
# ═══════════════════════════════════════════════════════════════════════════════

RegimeType = Literal["STRONG_TREND_UP", "STRONG_TREND_DOWN", "RANGING", "TRANSITION"]


@dataclass
class RegimeResult:
    regime: RegimeType
    adx: float
    atr_ratio: float
    swing_structure: str  # "bullish", "bearish", "neutral"
    is_ath_zone: bool
    ath_price: float
    current_price: float
    session: str  # "asia", "london", "newyork", "overlap_london_ny"
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)

    # Model weight matrix for this regime
    model_weights: Dict[str, float] = field(default_factory=dict)

    # RSI overrides
    rsi_overbought: float = 78.0  # default
    rsi_oversold: float = 22.0    # default
    rsi_trend_boost: bool = False  # if True, RSI>70 = momentum, not sell signal

    # Allowed directions
    allowed_directions: List[str] = field(default_factory=lambda: ["BUY", "SELL", "HOLD"])

    # R/R minimum for this regime
    min_rr: float = 1.2


# ═══════════════════════════════════════════════════════════════════════════════
# REGIME CACHE
# ═══════════════════════════════════════════════════════════════════════════════

_regime_cache: Dict[str, tuple] = {}  # symbol -> (RegimeResult, datetime)
REGIME_CACHE_SECONDS = 900  # 15 minutes (was 30m — reduced for faster regime transitions)


# ═══════════════════════════════════════════════════════════════════════════════
# FAKE SIGNAL PROTECTION CACHE
# ═══════════════════════════════════════════════════════════════════════════════

_timeout_cache: Dict[str, datetime] = {}  # symbol -> timeout_until


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: ADX CALCULATION (proper Wilder smoothing)
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate ADX using Wilder's smoothing method (matches TradingView)."""
    n = len(closes)
    if n < period * 2 + 1:
        return 20.0  # default neutral

    # True Range
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1])
        )
    )

    # +DM / -DM
    plus_dm = np.zeros(n - 1)
    minus_dm = np.zeros(n - 1)
    for i in range(n - 1):
        up = highs[i + 1] - highs[i]
        down = lows[i] - lows[i + 1]
        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down

    # Wilder smoothing (proper: seed = MEAN of first N values, not SUM)
    def wilder_smooth(values, period):
        result = np.zeros(len(values))
        result[period - 1] = np.mean(values[:period])  # SMA seed
        for i in range(period, len(values)):
            result[i] = result[i - 1] - (result[i - 1] / period) + values[i] / period
        return result

    atr_smooth = wilder_smooth(tr, period)
    plus_dm_smooth = wilder_smooth(plus_dm, period)
    minus_dm_smooth = wilder_smooth(minus_dm, period)

    # +DI / -DI
    plus_di = np.where(atr_smooth > 0, 100 * plus_dm_smooth / atr_smooth, 0)
    minus_di = np.where(atr_smooth > 0, 100 * minus_dm_smooth / atr_smooth, 0)

    # DX
    di_sum = plus_di + minus_di
    dx = np.where(di_sum > 0, 100 * np.abs(plus_di - minus_di) / di_sum, 0)

    # ADX (Wilder smooth of DX)
    if len(dx) < period * 2:
        return float(np.mean(dx[-period:])) if len(dx) >= period else 20.0

    adx_values = wilder_smooth(dx[period - 1:], period)
    valid = adx_values[adx_values > 0]
    return float(valid[-1]) if len(valid) > 0 else 20.0


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: SWING STRUCTURE (Higher Highs / Higher Lows)
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_swing_structure(highs: np.ndarray, lows: np.ndarray, lookback: int = 20) -> str:
    """
    Analyze last N candles for HH/HL (bullish) or LH/LL (bearish) structure.
    Uses simple pivot detection with 3-bar left/right.
    """
    n = len(highs)
    if n < lookback:
        return "neutral"

    h = highs[-lookback:]
    l = lows[-lookback:]

    # Find swing highs and lows (3-bar pivot)
    swing_highs = []
    swing_lows = []
    pivot_len = 3

    for i in range(pivot_len, len(h) - pivot_len):
        if h[i] == max(h[i - pivot_len:i + pivot_len + 1]):
            swing_highs.append((i, float(h[i])))
        if l[i] == min(l[i - pivot_len:i + pivot_len + 1]):
            swing_lows.append((i, float(l[i])))

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "neutral"

    # Check last 3 swing highs/lows
    recent_highs = [sh[1] for sh in swing_highs[-3:]]
    recent_lows = [sl[1] for sl in swing_lows[-3:]]

    hh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i - 1])
    hl_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i - 1])
    lh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] < recent_highs[i - 1])
    ll_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i - 1])

    bullish_score = hh_count + hl_count
    bearish_score = lh_count + ll_count

    if bullish_score >= 2:
        return "bullish"
    elif bearish_score >= 2:
        return "bearish"
    return "neutral"


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: ATH (All Time High) DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_ath_zone(highs: np.ndarray, current_price: float, lookback_days: int = 60) -> tuple:
    """
    Check if current price is near All Time High (within 1.5% of highest recorded).
    Returns (is_ath_zone, ath_price).
    """
    if len(highs) == 0:
        return False, current_price

    ath_price = float(np.max(highs[-lookback_days:])) if len(highs) >= lookback_days else float(np.max(highs))
    threshold = 0.015  # 1.5% of ATH
    is_ath = current_price >= ath_price * (1 - threshold)

    return is_ath, ath_price


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: SESSION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_session(symbol: str = "") -> str:
    """
    Detect current trading session based on UTC time.
    For DAX (GDAXI.INDX): uses XETRA hours.
    Asia: 00:00 - 07:00 UTC
    London: 07:00 - 13:00 UTC
    London/NY Overlap: 13:00 - 16:00 UTC (highest volume)
    New York: 16:00 - 21:00 UTC
    After Hours: 21:00 - 00:00 UTC (treated as asia-like)
    
    XETRA (DAX):
    Pre-market: 07:00 UTC (08:00 CET)
    Main session: 08:00 - 15:30 UTC (09:00-16:30 CET)
    Closing auction: 15:30 UTC (16:30 CET)
    US overlap: 13:30 - 15:30 UTC (highest DAX volatility)
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute

    # DAX-specific XETRA session detection
    if symbol == "GDAXI.INDX":
        if 8 <= hour < 13:
            return "xetra"  # XETRA main session (09:00-14:00 CET)
        elif 13 <= hour < 15 or (hour == 15 and minute <= 30):
            return "xetra_us_overlap"  # XETRA + US open (highest volatility)
        elif (hour == 7 and minute >= 0) or (hour == 15 and minute > 30) or (15 < hour < 21):
            return "newyork"  # XETRA closed but US still active
        else:
            return "asia"  # off-hours

    # WTI Crude Oil — NYMEX session detection
    # NYMEX main: 14:30–21:00 UTC (09:30–16:00 EST)
    # EIA release: Wednesday 15:30 UTC (10:30 EST)
    # London oil: 08:00–14:30 UTC (03:00–09:30 EST)
    if symbol == "USOIL.FOREX":
        is_wednesday = now.weekday() == 2
        # EIA window: Wednesday 15:15–15:45 UTC (10:15–10:45 EST)
        if is_wednesday and hour == 15 and 15 <= minute <= 45:
            return "nymex_eia_window"
        if 14 <= hour < 15 or (hour == 14 and minute >= 30):
            return "nymex"  # NYMEX opening (highest volatility)
        elif 15 <= hour < 21:
            return "nymex"  # NYMEX main session
        elif 8 <= hour < 14:
            return "london_oil"  # London/European oil trading
        else:
            return "asia"  # off-hours (low volume)

    # Default session detection for other symbols
    if 0 <= hour < 7:
        return "asia"
    elif 7 <= hour < 13:
        return "london"
    elif 13 <= hour < 16:
        return "overlap_london_ny"
    elif 16 <= hour < 21:
        return "newyork"
    else:
        return "asia"  # after hours = low volume like asia


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER BLOCK DETECTION (ICT simplified)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OrderBlock:
    type: str  # "bullish" or "bearish"
    low: float
    high: float
    volume: float
    index: int
    strength: float  # 0-1 rating


def detect_order_blocks(
    opens: np.ndarray, highs: np.ndarray, lows: np.ndarray,
    closes: np.ndarray, volumes: np.ndarray, lookback: int = 20
) -> List[OrderBlock]:
    """
    Find Order Blocks (ICT concept simplified):
    Bullish OB = last bearish candle before a strong bullish move
    Bearish OB = last bullish candle before a strong bearish move
    """
    n = len(closes)
    if n < lookback + 3:
        return []

    blocks = []
    data_slice = slice(-lookback, None)
    o = opens[data_slice]
    h = highs[data_slice]
    l = lows[data_slice]
    c = closes[data_slice]
    v = volumes[data_slice]

    avg_vol = float(np.mean(v)) if float(np.sum(v)) > 0 else 1.0
    avg_range = float(np.mean(h - l))

    for i in range(1, len(c) - 2):
        candle_range = float(h[i + 1] - l[i + 1])
        is_big_move = candle_range > avg_range * 1.5

        if not is_big_move:
            continue

        # Bullish OB: bearish candle (close < open) followed by strong bullish
        if c[i] < o[i] and c[i + 1] > o[i + 1] and c[i + 1] > h[i]:
            vol_strength = min(1.0, float(v[i + 1]) / avg_vol) if avg_vol > 0 else 0.5
            blocks.append(OrderBlock(
                type="bullish",
                low=float(l[i]),
                high=float(h[i]),
                volume=float(v[i + 1]),
                index=i + (n - lookback),
                strength=round(vol_strength * 0.6 + 0.4, 2)
            ))

        # Bearish OB: bullish candle followed by strong bearish
        if c[i] > o[i] and c[i + 1] < o[i + 1] and c[i + 1] < l[i]:
            vol_strength = min(1.0, float(v[i + 1]) / avg_vol) if avg_vol > 0 else 0.5
            blocks.append(OrderBlock(
                type="bearish",
                low=float(l[i]),
                high=float(h[i]),
                volume=float(v[i + 1]),
                index=i + (n - lookback),
                strength=round(vol_strength * 0.6 + 0.4, 2)
            ))

    # Return only the 3 most recent of each type
    bullish = sorted([b for b in blocks if b.type == "bullish"], key=lambda x: x.index, reverse=True)[:3]
    bearish = sorted([b for b in blocks if b.type == "bearish"], key=lambda x: x.index, reverse=True)[:3]

    return bullish + bearish


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: DETECT REGIME
# ═══════════════════════════════════════════════════════════════════════════════

async def detect_regime(symbol: str, force_refresh: bool = False) -> RegimeResult:
    """
    Main entry point. Detects market regime for a symbol.
    Uses 1H data for structure (more reliable), 1H for ATR ratio, EOD for ATH.
    Cached for 30 minutes.
    """
    # Check cache
    if not force_refresh and symbol in _regime_cache:
        cached_result, cached_time = _regime_cache[symbol]
        age = (datetime.now(timezone.utc) - cached_time).total_seconds()
        if age < REGIME_CACHE_SECONDS:
            return cached_result

    from services.market_data_service import get_ohlcv_data
    from services.data_fetcher import fetch_latest_price, fetch_eod_candles
    from services.data_hub import get_candles

    # Fetch data: 1H for structure + ADX (more reliable than 4H derived), EOD for ATH
    # Use DataHub directly to get 1H candles (fetched directly from API)
    data_1h = await get_ohlcv_data(symbol, "1H", limit=100)
    
    # Fallback: try DataHub direct if market_data_service returns empty
    if not data_1h or len(data_1h) < 30:
        data_1h = get_candles(symbol, "1h", limit=100)
        if data_1h:
            # Convert DataHub format to standard OHLCV format
            data_1h = [{"timestamp": c.get("timestamp"), "open": c["open"], 
                       "high": c["high"], "low": c["low"], "close": c["close"], 
                       "volume": c.get("volume", 0)} for c in data_1h]
    
    eod_data = await fetch_eod_candles(symbol, limit=120)
    live_price = await fetch_latest_price(symbol)

    # Defaults if data is missing
    if not data_1h or len(data_1h) < 30:
        logger.warning(f"Insufficient 1H data for {symbol}, defaulting to TRANSITION")
        return _default_regime(symbol, live_price)

    # Extract arrays from 1H (we use 1H directly instead of 4H for better reliability)
    h1_closes = np.array([c["close"] for c in data_1h], dtype=np.float64)
    h1_highs = np.array([c["high"] for c in data_1h], dtype=np.float64)
    h1_lows = np.array([c["low"] for c in data_1h], dtype=np.float64)

    current_price = float(live_price) if live_price else float(h1_closes[-1])

    # 1. ADX (1H with period 14 - we have more data points)
    adx = _calculate_adx(h1_highs, h1_lows, h1_closes, period=14)

    # 2. ATR ratio (1H) — current ATR vs 20-period average ATR
    atr_ratio = 1.0
    if len(data_1h) >= 25:
        tr = np.maximum(
            h1_highs[1:] - h1_lows[1:],
            np.maximum(np.abs(h1_highs[1:] - h1_closes[:-1]), np.abs(h1_lows[1:] - h1_closes[:-1]))
        )
        if len(tr) >= 20:
            current_atr = float(np.mean(tr[-5:]))
            avg_atr = float(np.mean(tr[-20:]))
            atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

    # 3. Swing structure (1H - more granular, still reliable)
    structure = _detect_swing_structure(h1_highs, h1_lows, lookback=30)

    # 4. ATH detection (EOD)
    is_ath = False
    ath_price = current_price
    if eod_data:
        eod_highs = np.array([c["high"] for c in eod_data], dtype=np.float64)
        is_ath, ath_price = _detect_ath_zone(eod_highs, current_price, lookback_days=60)

    # 5. Session (symbol-aware for XETRA)
    session = _detect_session(symbol)

    # ═══ REGIME DECISION ═══
    # ADX threshold 25'ten 30'a yükseltildi - daha güçlü trendlerde filtre devreye girsin
    regime: RegimeType = "TRANSITION"

    if adx >= 30 and structure == "bullish":
        regime = "STRONG_TREND_UP"
    elif adx >= 30 and structure == "bearish":
        regime = "STRONG_TREND_DOWN"
    elif adx < 20 and atr_ratio < 1.0:
        regime = "RANGING"
    else:
        regime = "TRANSITION"

    # ATH override: if at ATH and structure bullish, force trend up
    # ADX threshold 18'den 22'ye yükseltildi (yeni threshold'un %75'i)
    if is_ath and structure != "bearish" and adx >= 22:
        regime = "STRONG_TREND_UP"

    # Build result with regime-specific parameters
    result = _build_regime_result(
        regime=regime,
        adx=adx,
        atr_ratio=atr_ratio,
        structure=structure,
        is_ath=is_ath,
        ath_price=ath_price,
        current_price=current_price,
        session=session,
        symbol=symbol,
    )

    # Cache
    _regime_cache[symbol] = (result, datetime.now(timezone.utc))
    logger.info(
        f"Regime [{symbol}]: {regime} | ADX={adx:.1f} ATR_ratio={atr_ratio:.2f} "
        f"Struct={structure} ATH={is_ath} Session={session}"
    )

    return result


def _build_regime_result(
    regime: RegimeType, adx: float, atr_ratio: float, structure: str,
    is_ath: bool, ath_price: float, current_price: float, session: str, symbol: str
) -> RegimeResult:
    """Build RegimeResult with model weights, RSI thresholds, allowed directions."""

    # ═══ MODEL WEIGHT MATRIX ═══
    # Keys: ml, pulse1, pulse2, pulse3, emel, smc
    if regime == "STRONG_TREND_UP":
        weights = {"ml": 0.50, "pulse1": 0.15, "pulse2": 0.25, "pulse3": 0.10, "emel": 0.25, "smc": 0.15}
        rsi_ob = 92.0    # RSI >92 = too extreme even in trend
        rsi_os = 35.0     # RSI <35 in uptrend = buy dip opportunity
        rsi_boost = True   # RSI 70-92 = "strong momentum", not sell
        directions = ["BUY", "HOLD"]  # NO SELL in strong uptrend
        min_rr = 1.5       # higher R/R in trend for pullback entries

    elif regime == "STRONG_TREND_DOWN":
        weights = {"ml": 0.50, "pulse1": 0.15, "pulse2": 0.25, "pulse3": 0.10, "emel": 0.25, "smc": 0.15}
        rsi_ob = 65.0
        rsi_os = 8.0      # RSI <8 = too extreme
        rsi_boost = True   # RSI <30 = strong bearish momentum
        directions = ["SELL", "HOLD"]
        min_rr = 1.5

    elif regime == "RANGING":
        weights = {"ml": 0.20, "pulse1": 0.40, "pulse2": 0.20, "pulse3": 0.20, "emel": 0.25, "smc": 0.15}
        rsi_ob = 70.0
        rsi_os = 30.0
        rsi_boost = False
        directions = ["BUY", "SELL", "HOLD"]
        min_rr = 1.2

    else:  # TRANSITION
        weights = {"ml": 0.40, "pulse1": 0.20, "pulse2": 0.20, "pulse3": 0.20, "emel": 0.25, "smc": 0.15}
        rsi_ob = 75.0
        rsi_os = 25.0
        rsi_boost = False
        directions = ["BUY", "SELL", "HOLD"]
        min_rr = 1.3

    # ═══ ATH OVERRIDE ═══
    if is_ath and regime == "STRONG_TREND_UP":
        directions = ["BUY", "HOLD"]  # absolutely no sell at ATH
        rsi_ob = 95.0  # almost never trigger overbought at ATH
        min_rr = 1.2   # lower R/R at ATH (small pullbacks = entries)

    # ═══ SESSION ADJUSTMENTS ═══
    if session == "asia":
        # Low volume in Asia → reduce pulse1 but keep active
        weights["pulse1"] = max(weights["pulse1"], 0.10)
        if regime != "STRONG_TREND_UP" and regime != "STRONG_TREND_DOWN":
            min_rr = max(min_rr, 1.5)  # Higher R/R in Asia (manipulation risk)
    elif session == "overlap_london_ny":
        # Highest volume → all models active at full power
        pass  # keep defaults
    elif session == "newyork":
        if regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            min_rr = 1.3  # NY can have volatile reversals
    
    # ═══ XETRA SESSION ADJUSTMENTS (DAX) ═══
    if session == "xetra":
        # XETRA main session = best liquidity for DAX
        pass  # keep defaults — optimal trading window
    elif session == "xetra_us_overlap":
        # US open creates highest DAX volatility — widen R/R
        min_rr = max(min_rr, 1.5)
        # Pulse1 gets more weight during volatile US overlap
        weights["pulse1"] = max(weights["pulse1"], 0.25)

    # ═══ NYMEX SESSION ADJUSTMENTS (WTI Crude Oil) ═══
    if session == "nymex_eia_window":
        # EIA release window (Wed 10:30 EST) — extreme volatility, reduce confidence
        min_rr = max(min_rr, 2.0)  # Very high R/R during EIA
        weights["pulse1"] = 0.05   # Scalping dangerous during EIA
        weights["pulse3"] = 0.35   # Hybrid model best for EIA volatility
    elif session == "nymex":
        # NYMEX main session = best liquidity for WTI
        weights["pulse1"] = max(weights["pulse1"], 0.20)  # Scalping OK in NYMEX
    elif session == "london_oil":
        # London pre-market for oil — moderate liquidity
        min_rr = max(min_rr, 1.4)

    return RegimeResult(
        regime=regime,
        adx=round(adx, 1),
        atr_ratio=round(atr_ratio, 2),
        swing_structure=structure,
        is_ath_zone=is_ath,
        ath_price=round(ath_price, 2),
        current_price=round(current_price, 2),
        session=session,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_weights=weights,
        rsi_overbought=rsi_ob,
        rsi_oversold=rsi_os,
        rsi_trend_boost=rsi_boost,
        allowed_directions=directions,
        min_rr=min_rr,
        details={
            "adx_raw": round(adx, 2),
            "atr_ratio_raw": round(atr_ratio, 3),
            "structure": structure,
            "is_ath": is_ath,
            "ath_distance_pct": round((current_price - ath_price) / ath_price * 100, 2) if ath_price > 0 else 0,
        }
    )


def _default_regime(symbol: str, live_price) -> RegimeResult:
    """Fallback regime when data is insufficient."""
    price = float(live_price) if live_price else 0.0
    return RegimeResult(
        regime="TRANSITION",
        adx=20.0,
        atr_ratio=1.0,
        swing_structure="neutral",
        is_ath_zone=False,
        ath_price=price,
        current_price=price,
        session=_detect_session(symbol),
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_weights={"ml": 0.35, "pulse1": 0.15, "pulse2": 0.25, "pulse3": 0.25},
        rsi_overbought=75.0,
        rsi_oversold=25.0,
        rsi_trend_boost=False,
        allowed_directions=["BUY", "SELL", "HOLD"],
        min_rr=1.3,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FAKE SIGNAL FILTER
# ═══════════════════════════════════════════════════════════════════════════════

async def check_fake_signal_timeout(symbol: str) -> tuple:
    """
    Check if symbol is in timeout due to consecutive losing signals.
    Returns (is_timed_out: bool, timeout_until: str or None, reason: str)
    """
    if symbol in _timeout_cache:
        until = _timeout_cache[symbol]
        now = datetime.now(timezone.utc)
        if now < until:
            remaining = (until - now).total_seconds() / 60
            return True, until.isoformat(), f"Timeout: {remaining:.0f}dk kaldı (3+ kayıp sinyal)"
        else:
            del _timeout_cache[symbol]

    # Check recent signals from database
    try:
        from database.supabase_client import get_client
        client = get_client()
        result = client.table("prediction_logs") \
            .select("id,final_decision,outcome_pnl,created_at") \
            .eq("symbol", symbol) \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()

        if result and safe_get_data(result):
            signals = result["data"]
            # Count losses in last 24 hours
            now = datetime.now(timezone.utc)
            recent_losses = 0
            for s in signals:
                pnl = s.get("outcome_pnl")
                if pnl is not None and pnl < 0:
                    recent_losses += 1

            if recent_losses >= 3:
                from datetime import timedelta
                timeout_until = now + timedelta(hours=6)
                _timeout_cache[symbol] = timeout_until
                logger.warning(f"FAKE SIGNAL TIMEOUT: {symbol} - {recent_losses} losses, timeout until {timeout_until}")
                return True, timeout_until.isoformat(), f"6 saat timeout: Son 5 sinyalden {recent_losses} kayıp"

    except Exception as e:
        logger.debug(f"Fake signal check failed (non-critical): {e}")

    return False, None, ""


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTION FILTER (enforces regime rules)
# ═══════════════════════════════════════════════════════════════════════════════

def filter_signal_by_regime(signal: str, regime: RegimeResult) -> tuple:
    """
    Filter a signal direction by the current regime rules.
    Returns (filtered_signal, was_modified, reason)
    """
    if signal == "HOLD":
        return "HOLD", False, ""

    if signal not in regime.allowed_directions:
        if regime.regime == "STRONG_TREND_UP" and signal == "SELL":
            return "HOLD", True, f"SELL blocked: Güçlü yükseliş trendi (ADX={regime.adx})"
        elif regime.regime == "STRONG_TREND_DOWN" and signal == "BUY":
            return "HOLD", True, f"BUY blocked: Güçlü düşüş trendi (ADX={regime.adx})"
        return "HOLD", True, f"Signal {signal} not allowed in {regime.regime}"

    return signal, False, ""


# ═══════════════════════════════════════════════════════════════════════════════
# RSI INTERPRETATION (regime-aware)
# ═══════════════════════════════════════════════════════════════════════════════

def interpret_rsi(rsi_value: float, regime: RegimeResult, proposed_direction: str) -> dict:
    """
    Interpret RSI value based on regime context.
    In trend mode: RSI>70 is NOT overbought, it's momentum.
    Returns dict with action, score_adjustment, note.
    """
    result = {
        "action": "neutral",      # "boost", "neutral", "caution", "block"
        "score_adjustment": 0,     # points to add/subtract
        "note": "",
    }

    if regime.rsi_trend_boost:
        # TREND MODE: RSI reinterpreted
        if regime.regime == "STRONG_TREND_UP":
            if rsi_value > regime.rsi_overbought:
                result["action"] = "caution"
                result["score_adjustment"] = -5
                result["note"] = f"RSI aşırı yüksek ({rsi_value:.0f}), trend yorulmuş olabilir"
            elif rsi_value > 70:
                result["action"] = "boost"
                result["score_adjustment"] = 5
                result["note"] = f"Güçlü momentum (RSI={rsi_value:.0f}), trend devam"
            elif rsi_value < regime.rsi_oversold:
                result["action"] = "boost"
                result["score_adjustment"] = 10
                result["note"] = f"Trendde dip fırsatı (RSI={rsi_value:.0f})"
            else:
                result["action"] = "neutral"

        elif regime.regime == "STRONG_TREND_DOWN":
            if rsi_value < regime.rsi_oversold:
                result["action"] = "caution"
                result["score_adjustment"] = -5
                result["note"] = f"RSI aşırı düşük ({rsi_value:.0f}), bounce olabilir"
            elif rsi_value < 30:
                result["action"] = "boost"
                result["score_adjustment"] = 5
                result["note"] = f"Güçlü bearish momentum (RSI={rsi_value:.0f})"
            elif rsi_value > regime.rsi_overbought:
                result["action"] = "boost"
                result["score_adjustment"] = 10
                result["note"] = f"Trendde ralli satış fırsatı (RSI={rsi_value:.0f})"

    else:
        # RANGING / TRANSITION: Classic RSI interpretation
        if rsi_value > regime.rsi_overbought:
            if proposed_direction == "BUY":
                result["action"] = "caution"
                result["score_adjustment"] = -10
                result["note"] = f"Aşırı alım bölgesi (RSI={rsi_value:.0f})"
            elif proposed_direction == "SELL":
                result["action"] = "boost"
                result["score_adjustment"] = 5
                result["note"] = f"Aşırı alım, SELL uygun (RSI={rsi_value:.0f})"
        elif rsi_value < regime.rsi_oversold:
            if proposed_direction == "SELL":
                result["action"] = "caution"
                result["score_adjustment"] = -10
                result["note"] = f"Aşırı satım bölgesi (RSI={rsi_value:.0f})"
            elif proposed_direction == "BUY":
                result["action"] = "boost"
                result["score_adjustment"] = 5
                result["note"] = f"Aşırı satım, BUY uygun (RSI={rsi_value:.0f})"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINT HELPER
# ═══════════════════════════════════════════════════════════════════════════════

async def get_regime_info(symbol: str) -> dict:
    """Return regime info as JSON-serializable dict for API endpoints."""
    regime = await detect_regime(symbol)
    return {
        "regime": regime.regime,
        "adx": regime.adx,
        "atr_ratio": regime.atr_ratio,
        "swing_structure": regime.swing_structure,
        "is_ath_zone": regime.is_ath_zone,
        "ath_price": regime.ath_price,
        "current_price": regime.current_price,
        "session": regime.session,
        "model_weights": regime.model_weights,
        "rsi_overbought": regime.rsi_overbought,
        "rsi_oversold": regime.rsi_oversold,
        "rsi_trend_boost": regime.rsi_trend_boost,
        "allowed_directions": regime.allowed_directions,
        "min_rr": regime.min_rr,
        "details": regime.details,
    }
