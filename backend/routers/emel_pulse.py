"""
EMEL + PULSE Panel API Endpoints
- EMEL: 9 kontrol noktalı stratejik analiz
- PULSE: Hızlı scalp analizi
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timezone, timedelta
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/panel", tags=["Panel Analysis"])


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class PriceLevel(BaseModel):
    price: Optional[float] = None
    distance: Optional[float] = None
    alert: Optional[bool] = None

class Levels(BaseModel):
    r2: Optional[float] = None
    r1: Optional[float] = None
    pivot: Optional[float] = None
    s1: Optional[PriceLevel] = None
    s2: Optional[float] = None
    nearest: Optional[str] = None
    nearest_distance: Optional[float] = None

class MomentumIndicator(BaseModel):
    value: Optional[float] = None
    trend: Optional[str] = None

class Momentum(BaseModel):
    rsi: Optional[MomentumIndicator] = None
    macd: Optional[MomentumIndicator] = None
    stochastic: Optional[MomentumIndicator] = None

class Volume(BaseModel):
    status: Optional[str] = None
    label: Optional[str] = None
    ratio: Optional[float] = None
    available: Optional[bool] = None

class Trend(BaseModel):
    direction: Optional[str] = None
    strength: Optional[float] = None
    label: Optional[str] = None
    strength_pct: Optional[int] = None
    last_5_candles: Optional[List[str]] = None

class Regime(BaseModel):
    type: Optional[str] = None
    adx: Optional[float] = None
    session: Optional[str] = None
    is_ath: Optional[bool] = None
    rsi_mode: Optional[str] = None
    allowed_directions: Optional[List[str]] = None
    min_rr: Optional[float] = None

class Suggestion(BaseModel):
    text: Optional[str] = None
    target: Optional[float] = None
    stop: Optional[float] = None
    target_distance: Optional[float] = None
    stop_distance: Optional[float] = None
    rr_ratio: Optional[float] = None
    timeframe_estimate: Optional[str] = None

class PulseResponse(BaseModel):
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    timestamp: Optional[str] = None
    signal_timestamp: Optional[str] = None
    signal: Optional[str] = None
    signal_type: Optional[str] = None
    pulse_score: Optional[float] = None
    trend: Optional[Trend] = None
    price: Optional[Dict[str, float]] = None
    levels: Optional[Levels] = None
    momentum: Optional[Momentum] = None
    volume: Optional[Volume] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    decision_notes: Optional[List[str]] = None
    regime: Optional[Regime] = None
    suggestion: Optional[Suggestion] = None
    error: Optional[str] = None

class EMELCheck(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[str] = None
    direction: Optional[str] = None
    color: Optional[str] = None
    label: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None

class EMELRecommendation(BaseModel):
    action: Optional[str] = None
    entry: Optional[float] = None
    target: Optional[float] = None
    stop: Optional[float] = None
    confidence: Optional[int] = None
    timeframe: Optional[str] = None

class EMELResponse(BaseModel):
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    timestamp: Optional[str] = None
    signal_timestamp: Optional[str] = None
    signal: Optional[str] = None
    confidence: Optional[float] = None
    price: Optional[float] = None
    checks: Optional[List[EMELCheck]] = None
    confluence: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    final_score: Optional[int] = None
    signal_type: Optional[str] = None
    regime: Optional[Regime] = None
    technical_summary: Optional[Dict[str, Any]] = None
    ml_context: Optional[Dict[str, Any]] = None
    recommendation: Optional[EMELRecommendation] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    rebound: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ScoreBreakdownML(BaseModel):
    pts: int
    confidence: float
    direction: str

class ScoreBreakdownEMA(BaseModel):
    pts: int
    status: str
    ema20: float
    ema50: float

class ScoreBreakdownMACD(BaseModel):
    pts: int
    hist: float

class ScoreBreakdownRSI(BaseModel):
    pts: int
    value: float

class ScoreBreakdownVolume(BaseModel):
    pts: int

class ScoreBreakdownMLModel(BaseModel):
    ml: ScoreBreakdownML
    ema: ScoreBreakdownEMA
    macd: ScoreBreakdownMACD
    rsi: ScoreBreakdownRSI
    volume: ScoreBreakdownVolume

class DetailsML(BaseModel):
    ml_direction: str
    ema_20: float
    ema_50: float
    rsi_14: float
    macd_hist: float
    notes: List[str]

class PulseMLResponse(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    signal_timestamp: Optional[str] = None
    signal: str
    signal_type: str
    pulse_score: float
    confidence: float
    model_type: str
    price: float
    target: float
    stop: float
    rr_ratio: float
    score_breakdown: ScoreBreakdownMLModel
    details: DetailsML
    suggestion: str
    regime: Optional[Regime] = None

class TimeframeScore(BaseModel):
    raw_score: int
    max: int
    trend: str
    details: Any

class LevelsV3(BaseModel):
    r2: float
    r1: float
    pivot: float
    s1: float
    s2: float
    target: float
    stop: float

class EntryZone(BaseModel):
    price: float
    share: float
    label: str

class OrderBlock(BaseModel):
    type: str
    low: float
    high: float
    strength: float
    is_nearby: bool

class PulseV3Response(BaseModel):
    symbol: str
    timestamp: str
    signal_timestamp: Optional[str] = None
    # float: payload round(total_score, 1) küsuratlı olabilir; int tanımı
    # Pydantic ResponseValidationError ile endpoint'i 500'e düşürüyordu.
    pulse_score: float
    max_score: int
    signal_type: str
    direction: str
    confidence: float
    price: float
    timeframes: Dict[str, TimeframeScore]
    levels: LevelsV3
    rr_ratio: float
    suggestion: str
    entry_zones: List[EntryZone]
    notes: List[str]
    valid_for_seconds: int
    regime: Optional[Regime] = None
    order_blocks: Optional[List[OrderBlock]] = None
    rebound: Optional[Dict[str, Any]] = None

class RegimeResponse(BaseModel):
    symbol: Optional[str] = None
    timestamp: Optional[str] = None
    regime: Optional[Regime] = None
    error: Optional[str] = None

class PerformanceStatsResponse(BaseModel):
    symbol: str
    signals_generated: int
    avg_score: float
    win_rate: float
    profit_factor: float
    timestamp: str

class ErrorResponse(BaseModel):
    error: str

class DataHubDebugResponse(BaseModel):
    symbol: str
    hub_status: Dict[str, Any]
    last_update: Optional[str] = None
    cached: bool

class EMADebugResponse(BaseModel):
    symbol: str
    timeframe: str
    ema_5: float
    ema_10: float
    ema_20: float
    ema_50: float
    closes_sample: List[float]
    timestamp: str

class CompareResponse(BaseModel):
    symbol: str
    emel_score: int
    pulse_score: int
    pulse_ml_score: int
    pulse_v3_score: int
    consensus: str
    timestamp: str


# ═══════════════════════════════════════════════════════════════════════════════
# SCALPING TP/SL DISTANCE TABLE (instrument-specific)
# These are fixed pip/point distances appropriate for scalping timeframes
# ═══════════════════════════════════════════════════════════════════════════════
SCALP_DISTANCES = {
    "NDX.INDX":     {"tp": 20, "sl": 12},   # points
    "XAUUSD":       {"tp": 7,  "sl": 4},    # dollars
    "GDAXI.INDX":   {"tp": 20, "sl": 12},   # points
    "USOIL.FOREX":  {"tp": 0.50, "sl": 0.30}, # dollars
}

PULSE_PANEL_CACHE_TTL = 60


def _panel_analysis_cache_key(panel_name: str, symbol: str, timeframe: str) -> str:
    return f"panel_analysis:{panel_name}:{symbol.upper()}:{timeframe.lower()}"


def _get_cached_panel_analysis(panel_name: str, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
    from services.redis_client import cache_get

    cached = cache_get(_panel_analysis_cache_key(panel_name, symbol, timeframe))
    if isinstance(cached, dict) and not cached.get("error"):
        return cached
    return None


def _set_cached_panel_analysis(panel_name: str, symbol: str, timeframe: str, payload: Dict[str, Any]) -> None:
    from services.redis_client import cache_set

    cache_set(_panel_analysis_cache_key(panel_name, symbol, timeframe), payload, ttl=PULSE_PANEL_CACHE_TTL)
    # Also write to the broadcast-format key so WS broadcasts include this panel data
    broadcast_key = f"panel:{panel_name}:{symbol.upper()}"
    cache_set(broadcast_key, payload, ttl=PULSE_PANEL_CACHE_TTL)


def _get_latest_market_timestamp(symbol: str) -> Optional[str]:
    from services.redis_client import cache_get

    cached_broadcast = cache_get(f"broadcast:{symbol.upper()}")
    if isinstance(cached_broadcast, dict):
        timestamp = cached_broadcast.get("timestamp")
        if isinstance(timestamp, str) and timestamp:
            return timestamp
    return None


def _resolve_signal_timestamp(symbol: str, fallback: str) -> str:
    return _get_latest_market_timestamp(symbol) or fallback


def _emel_macro_notes(symbol: str, decision: str) -> List[str]:
    """Return up to 3 macro-context commentary lines for EMEL's summary block.
    Maps EMEL's BUY_SETUP / SELL_SETUP / HOLD into BUY / SELL / HOLD before
    delegating to the macro_context_service. Never raises."""
    try:
        from services.macro_context_service import commentary_lines
        direction = "BUY" if decision == "BUY_SETUP" else "SELL" if decision == "SELL_SETUP" else "HOLD"
        return list(commentary_lines(symbol, direction, max_lines=3))
    except Exception as e:
        logger.debug(f"EMEL macro notes skipped: {e}")
        return []


def _pattern_signal_value(pattern: Dict[str, Any]) -> str:
    raw = str(pattern.get("signal") or pattern.get("direction") or "neutral").strip().upper()
    if raw in {"BULLISH", "BUY", "UP"}:
        return "bullish"
    if raw in {"BEARISH", "SELL", "DOWN"}:
        return "bearish"
    return "neutral"


def _extract_shared_patterns(patterns: Any) -> List[Dict[str, Any]]:
    items = [pattern for pattern in (patterns or []) if isinstance(pattern, dict)]
    shared = [
        pattern
        for pattern in items
        if str(pattern.get("pattern_source") or pattern.get("source") or "").lower() == "harmonic_visualizer_4h"
        or str(pattern.get("timeframe") or "").lower() == "4h"
    ]
    return shared or items


def _summarize_panel_patterns(patterns: Any, preferred_direction: Optional[str] = None) -> Dict[str, Any]:
    selected = _extract_shared_patterns(patterns)
    if not selected:
        return {
            "count": 0,
            "selected": [],
            "top_pattern": None,
            "bullish_count": 0,
            "bearish_count": 0,
            "bias": "NEUTRAL",
            "preferred_direction": (preferred_direction or "").upper(),
            "aligned_count": 0,
            "opposing_count": 0,
        }

    selected = sorted(
        selected,
        key=lambda pattern: (
            0 if str(pattern.get("category") or "").lower() == "harmonic" else 1,
            -float(pattern.get("confidence") or 0),
        ),
    )
    bullish_count = sum(1 for pattern in selected if _pattern_signal_value(pattern) == "bullish")
    bearish_count = sum(1 for pattern in selected if _pattern_signal_value(pattern) == "bearish")
    bias = "NEUTRAL"
    if bullish_count > bearish_count:
        bias = "BUY"
    elif bearish_count > bullish_count:
        bias = "SELL"

    preferred = (preferred_direction or "").upper()
    aligned_count = 0
    opposing_count = 0
    if preferred == "BUY":
        aligned_count = bullish_count
        opposing_count = bearish_count
    elif preferred == "SELL":
        aligned_count = bearish_count
        opposing_count = bullish_count

    return {
        "count": len(selected),
        "selected": selected,
        "top_pattern": selected[0],
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "bias": bias,
        "preferred_direction": preferred,
        "aligned_count": aligned_count,
        "opposing_count": opposing_count,
    }

def _calc_ema(values, period):
    """Calculate true Exponential Moving Average (matching TradingView)."""
    if len(values) < period:
        return float(values[-1]) if len(values) > 0 else 0.0
    alpha = 2.0 / (period + 1.0)
    ema = float(np.mean(values[:period]))
    for v in values[period:]:
        ema = alpha * float(v) + (1 - alpha) * ema
    return ema


#: Endekslerde sabit mesafeler taban, ATR tavan belirler (rapor aksiyon #3).
#: GDAXI 60g kanıtı: sabit TP20/SL12 point 5m gürültüsünün içinde kaldı —
#: stopped sinyallerde ort. MFE 6-7 pip vs SL 65-68 pip, her iki yön de kaybetti.
_ATR_GEOMETRY_SYMBOLS = {"GDAXI.INDX", "NDX.INDX"}
_ATR_TP_MULT = 1.5
_ATR_SL_MULT = 1.0


def _scalp_tp_sl(symbol: str, current_price: float, direction: str, atr_val: float):
    """Calculate scalping-appropriate TP/SL.

    Endeksler (GDAXI/NDX): ATR-bazlı dinamik mesafe — TP ≥ max(fixed, ATR×1.5),
    SL ≥ max(fixed, ATR×1.0). Volatilite arttığında mesafeler genişler, sabit
    mesafeler taban görevi görür. PULSE_ATR_GEOMETRY=0 ile eski davranışa dönülür.

    Emtialar (XAUUSD/USOIL): eski davranış — sabit mesafe tavan, düşük ATR'de
    daralma (BUY tarafı %69-80 WR ile bu geometride çalışıyor, rapor 3.1/2.3).
    """
    import os as _os
    dist = SCALP_DISTANCES.get(symbol, {"tp": 15, "sl": 10})
    tp_dist = dist["tp"]
    sl_dist = dist["sl"]

    atr_geometry_on = _os.getenv("PULSE_ATR_GEOMETRY", "1") != "0"
    if atr_geometry_on and symbol in _ATR_GEOMETRY_SYMBOLS and atr_val and atr_val > 0:
        # ATR taban geometrisi: gürültü bandının dışına çık
        tp_dist = max(tp_dist, atr_val * _ATR_TP_MULT)
        sl_dist = max(sl_dist, atr_val * _ATR_SL_MULT)
    else:
        # Clamp: if ATR is very low, reduce distances
        atr_tp = atr_val * 1.0
        atr_sl = atr_val * 0.6
        tp_dist = min(tp_dist, max(atr_tp, tp_dist * 0.3))  # Don't go below 30% of fixed
        sl_dist = min(sl_dist, max(atr_sl, sl_dist * 0.3))
    
    if direction == "BUY":
        target = current_price + tp_dist
        stop = current_price - sl_dist
    elif direction == "SELL":
        target = current_price - tp_dist
        stop = current_price + sl_dist
    else:
        target = current_price + tp_dist
        stop = current_price - sl_dist
    
    return target, stop, tp_dist, sl_dist


# ═══════════════════════════════════════════════════════════════════════════════
# EMEL PANEL - 9 KONTROL NOKTASI
# ═══════════════════════════════════════════════════════════════════════════════

# EMEL check-8 (Learning) gerçek veri kaynağı: sembolün son 30 günlük EMEL
# WR'ı. Eskiden prediction.get("learning_insights") okunuyordu ama o alan
# PredictionResult'ta hiç yoktu → kontrol her zaman "VERİ YOK" idi (ölü).
# 10 dakikalık modül-içi cache ile sorgu maliyeti panel trafiğinden ayrışır.
_emel_wr_cache: Dict[str, tuple] = {}  # symbol -> (expires_epoch, win_rate, samples)
_EMEL_WR_TTL = 600.0


async def _emel_recent_winrate(symbol: str) -> tuple:
    """(win_rate_pct, sample_count) — son 30g EMEL completed/stopped sayımı."""
    import time as _time
    cached = _emel_wr_cache.get(symbol)
    if cached and cached[0] > _time.time():
        return cached[1], cached[2]
    win_rate, samples = 50.0, 0
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if is_db_available():
            client = get_supabase_client()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            res = (client.table("prediction_logs")
                   .select("status")
                   .eq("symbol", symbol).eq("model_type", "emel")
                   .gte("created_at", cutoff)
                   .in_("status", ["completed", "stopped"])
                   .limit(2000).execute())
            # SupabaseRestClient dict döner; resmi client obje — ikisini de kapsa.
            rows = (res.get("data") if isinstance(res, dict) else getattr(res, "data", None)) or []
            comp = sum(1 for r in rows if r.get("status") == "completed")
            samples = len(rows)
            if samples > 0:
                win_rate = comp / samples * 100.0
    except Exception as _wr_err:
        logger.debug(f"[EMEL Learning] {symbol}: WR sorgusu atlandı ({_wr_err})")
    _emel_wr_cache[symbol] = (_time.time() + _EMEL_WR_TTL, win_rate, samples)
    return win_rate, samples


@router.get("/emel/{symbol}", response_model=EMELResponse)
async def get_emel_analysis(symbol: str, timeframe: str = "1H"):
    """
    EMEL Panel - 9 Kontrol Noktası ile Detaylı Analiz
    """
    try:
        from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
        from services.market_data_service import get_ohlcv_data
        from services.rebound_filter_service import analyze_rebound
        
        # Get market data — track effective timeframe so panel can expose fallback to user.
        effective_tf = timeframe
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=250)
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=250)
            if ohlcv and len(ohlcv) >= 50:
                effective_tf = "30M"
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=250)
            if ohlcv and len(ohlcv) >= 50:
                effective_tf = "5M"
        if not ohlcv or len(ohlcv) < 20:
            logger.warning(f"EMEL: Insufficient candle data for {symbol} (tried 1H/30m/5m)")
            return {"error": "Insufficient data"}

        
        # Convert to numpy arrays - CRITICAL for correct EMA calculation
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        
        # DEBUG: Log volumes array details to diagnose timeframe mixing issues
        logger.info(f"[EMEL Volume Debug] {symbol} {timeframe}: volumes.shape={volumes.shape}, "
                   f"first_5={volumes[:5].tolist()}, last_5={volumes[-5:].tolist()}, "
                   f"min={float(volumes.min()):.0f}, max={float(volumes.max()):.0f}, mean={float(volumes.mean()):.0f}")
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        # Calculate TA with numpy arrays
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # Get ML prediction for context
        from dataclasses import asdict
        prediction_raw = await get_ml_prediction(symbol, "balanced")
        prediction = asdict(prediction_raw) if hasattr(prediction_raw, '__dataclass_fields__') else (prediction_raw if isinstance(prediction_raw, dict) else {})
        
        # Build 9 checkpoints
        checks = []
        green_count = 0
        yellow_count = 0
        red_count = 0
        
        # ─────────────────────────────────────────────────────────────────────
        # 1️⃣ TREND ANALİZİ (EMA 20/50/200)
        # ─────────────────────────────────────────────────────────────────────
        ema_20 = ta.get("ema_20", current_price)
        ema_50 = ta.get("ema_50", current_price)
        ema_200 = ta.get("ema_200", current_price)

        # EMA20 slope over last 5 bars (normalized by price)
        ema20_series = ta.get("ema_20_series") or ta.get("ema20_series")
        if isinstance(ema20_series, (list, tuple)) and len(ema20_series) >= 6:
            ema20_slope_pct = (float(ema20_series[-1]) - float(ema20_series[-6])) / max(current_price, 1e-9) * 100.0
        else:
            # Fallback: approximate slope from closes (last 5 bars EMA ≈ mean of last 5 closes for signal)
            ema20_slope_pct = (float(closes[-1]) - float(closes[-6])) / max(current_price, 1e-9) * 100.0 if len(closes) >= 6 else 0.0

        price_above_ema20 = current_price > ema_20
        ema20_above_ema50 = ema_20 > ema_50
        ema50_above_ema200 = ema_50 > ema_200

        # Bull/bear structure: stacking + slope must agree
        bull_stack = price_above_ema20 and ema20_above_ema50 and ema50_above_ema200
        bear_stack = (not price_above_ema20) and (not ema20_above_ema50) and (not ema50_above_ema200)
        slope_threshold = 0.05  # %0.05 over 5 bars = meaningful slope

        if bull_stack and ema20_slope_pct > slope_threshold:
            trend_status = "pass"; trend_direction = "up"; trend_color = "green"
            trend_label = "YUKARI YÖN"
            trend_comment = f"EMA dizilimi bullish + slope +{ema20_slope_pct:.2f}%. Trend takip uygun."
            green_count += 1
        elif bear_stack and ema20_slope_pct < -slope_threshold:
            trend_status = "fail"; trend_direction = "down"; trend_color = "red"
            trend_label = "AŞAĞI YÖN"
            trend_comment = f"EMA dizilimi bearish + slope {ema20_slope_pct:.2f}%. Trend aşağı."
            red_count += 1
        elif bull_stack or bear_stack:
            # Stacking var ama slope zayıf → düşük güven
            trend_status = "warning"
            trend_direction = "up" if bull_stack else "down"
            trend_color = "yellow"
            trend_label = "ZAYIF TREND"
            trend_comment = f"EMA dizilimi {'bullish' if bull_stack else 'bearish'} ama momentum zayıf (slope {ema20_slope_pct:+.2f}%)."
            yellow_count += 1
        else:
            trend_status = "warning"; trend_direction = "neutral"; trend_color = "yellow"
            trend_label = "KARIŞIK"
            trend_comment = "EMA'lar karışık sinyal veriyor. Net bir yön yok."
            yellow_count += 1
        
        checks.append({
            "id": 1,
            "name": "Trend Analizi",
            "subtitle": "EMA 20/50/200",
            "status": trend_status,
            "direction": trend_direction,
            "color": trend_color,
            "label": trend_label,
            "details": {
                "ema20": round(ema_20, 2),
                "ema50": round(ema_50, 2),
                "ema200": round(ema_200, 2),
                "price_vs_ema20": "üzerinde" if price_above_ema20 else "altında"
            },
            "comment": trend_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 2️⃣ REJİM TESPİTİ (ADX + Yapı)
        # ─────────────────────────────────────────────────────────────────────
        adx_val = ta.get("adx", 20)
        
        if adx_val >= 25:
            regime_status = "pass"
            regime_color = "green"
            regime_label = "GÜÇLÜ TREND"
            regime_comment = "ADX güçlü trend gösteriyor. Trend takip stratejileri uygun."
            green_count += 1
        elif adx_val >= 18:
            regime_status = "warning"
            regime_color = "yellow"
            regime_label = "ZAYIF TREND"
            regime_comment = "Trend gücü zayıf. Büyük pozisyonlar için beklemek daha güvenli."
            yellow_count += 1
        else:
            regime_status = "fail"
            regime_color = "red"
            regime_label = "YATAY PİYASA"
            regime_comment = "Piyasa yatay seyrediyor. Range stratejileri düşün."
            red_count += 1
        
        checks.append({
            "id": 2,
            "name": "Rejim Tespiti",
            "subtitle": "ADX + Yapı",
            "status": regime_status,
            "direction": "neutral",
            "color": regime_color,
            "label": regime_label,
            "details": {
                "adx": round(adx_val, 1),
                "strength": "Güçlü" if adx_val >= 25 else "Zayıf" if adx_val >= 18 else "Yok"
            },
            "comment": regime_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 3️⃣ MULTI-TIMEFRAME UYUMU
        # ─────────────────────────────────────────────────────────────────────
        mtf_data = prediction.get("mtf_data", {})
        mtf_checks = []

        # Ana yönü trend_direction'dan belirle (bullish/bearish bias yok)
        # NEUTRAL ise dominant çoğunluğa bak
        dirs: Dict[str, int] = {"up": 0, "down": 0, "neutral": 0}
        for tf in ["1D", "4H", "1H", "15m"]:
            tf_trend = str(mtf_data.get(tf, {}).get("trend", "NEUTRAL")).upper()
            if tf_trend == "UP":
                mtf_checks.append({"tf": tf, "dir": "up", "icon": "🟢"}); dirs["up"] += 1
            elif tf_trend == "DOWN":
                mtf_checks.append({"tf": tf, "dir": "down", "icon": "🔴"}); dirs["down"] += 1
            else:
                mtf_checks.append({"tf": tf, "dir": "neutral", "icon": "🟡"}); dirs["neutral"] += 1

        if trend_direction in ("up", "down"):
            main_dir = trend_direction
        else:
            main_dir = "up" if dirs["up"] > dirs["down"] else ("down" if dirs["down"] > dirs["up"] else "neutral")

        # 4H ve 1H ana yöne karşı mı?
        opposing_core = 0
        neutral_core = 0
        if main_dir != "neutral":
            opp = "down" if main_dir == "up" else "up"
            for item in mtf_checks:
                if item["tf"] in ("4H", "1H"):
                    if item["dir"] == opp:
                        opposing_core += 1
                    elif item["dir"] == "neutral":
                        neutral_core += 1

        if main_dir == "neutral":
            mtf_status = "warning"; mtf_color = "yellow"
            mtf_label = "NET YÖN YOK"
            mtf_comment = "Ana trend belirsiz, MTF verisi yön taraması için yetersiz."
            yellow_count += 1
        elif opposing_core == 0 and neutral_core == 0:
            mtf_status = "pass"; mtf_color = "green"
            mtf_label = "UYUMLU"
            mtf_comment = f"Tüm zaman dilimleri {main_dir.upper()} yönünde hizalı."
            green_count += 1
        elif opposing_core == 0:
            mtf_status = "warning"; mtf_color = "yellow"
            mtf_label = "KISMI UYUM"
            mtf_comment = "Bazı core TF'ler nötr — hizalanma bekleyin."
            yellow_count += 1
        else:
            mtf_status = "fail"; mtf_color = "red"
            mtf_label = "ÇELİŞKİLİ"
            mtf_comment = f"Core TF ({opposing_core}) ana trende karşı ({main_dir.upper()}). BEKLE."
            red_count += 1
        
        checks.append({
            "id": 3,
            "name": "Multi-Timeframe Uyumu",
            "subtitle": "1D/4H/1H/15m",
            "status": mtf_status,
            "direction": "neutral",
            "color": mtf_color,
            "label": mtf_label,
            "details": {"timeframes": mtf_checks},
            "comment": mtf_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 4️⃣ FORMASYON ANALİZİ (Gerçek Formasyon Bulucu)
        # ─────────────────────────────────────────────────────────────────────
        try:
            from services.harmonic_pattern_service import get_pattern_adjustment

            active_patterns = _extract_shared_patterns(prediction.get("active_patterns", []))
            if not active_patterns:
                pattern_result = await get_pattern_adjustment(symbol, timeframe="4h")
                active_patterns = pattern_result.get("patterns", [])

            pattern_context = _summarize_panel_patterns(active_patterns, prediction.get("direction"))
            top_pattern = pattern_context.get("top_pattern") or {}
            pattern_name_tr = top_pattern.get("name_tr") or top_pattern.get("name") or "Formasyon"
            pattern_signal = _pattern_signal_value(top_pattern)
            pattern_confidence = float(top_pattern.get("confidence") or 0)
            pattern_strength = 3 if str(top_pattern.get("category") or "").lower() == "harmonic" else 2
            patterns_found = pattern_context.get("count", 0)

            if patterns_found > 0:
                pattern_label = pattern_name_tr.upper()
                signal_label = "boğa" if pattern_signal == "bullish" else "ayı" if pattern_signal == "bearish" else "nötr"
                if pattern_context.get("preferred_direction") in {"BUY", "SELL"} and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
                    pattern_status = "fail"
                    pattern_color = "red"
                    pattern_comment = f"4H {signal_label} formasyon ML yönüyle çelişiyor. {pattern_name_tr} dikkat gerektiriyor."
                    red_count += 1
                elif pattern_confidence >= 75:
                    pattern_status = "pass"
                    pattern_color = "green"
                    pattern_comment = f"4H {signal_label} formasyonu tespit edildi: {pattern_name_tr}. Analize dahil edildi."
                    green_count += 1
                else:
                    pattern_status = "warning"
                    pattern_color = "yellow"
                    pattern_comment = f"4H {signal_label} formasyonu izleniyor: {pattern_name_tr}. Güven artarsa onaylanır."
                    yellow_count += 1
                pattern_completion = pattern_confidence
            else:
                pattern_status = "warning"
                pattern_color = "yellow"
                pattern_label = "FORMASYON YOK"
                pattern_comment = "Harmonic 4H pattern feed üzerinde aktif formasyon yok."
                yellow_count += 1
                pattern_completion = 0
                pattern_strength = 0
                
        except Exception as pattern_err:
            logger.warning(f"Pattern detection error: {pattern_err}")
            pattern_status = "warning"
            pattern_signal = "neutral"
            pattern_strength = 0
            pattern_color = "yellow"
            pattern_label = "FORMASYON YOK"
            pattern_comment = "Formasyon analizi yapılamadı."
            yellow_count += 1
            pattern_completion = 0
            patterns_found = 0
        
        checks.append({
            "id": 4,
            "name": "Formasyon Analizi",
            "subtitle": "Pattern Recognition",
            "status": pattern_status,
            "direction": pattern_signal if pattern_status != "warning" else "neutral",
            "color": pattern_color,
            "label": pattern_label,
            "details": {
                "completion": round(pattern_completion, 1),
                "patterns_found": patterns_found,
                "strength": pattern_strength if pattern_status != "warning" else 0
            },
            "comment": pattern_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 5️⃣ DESTEK/DİRENÇ SEVİYELERİ
        # ─────────────────────────────────────────────────────────────────────
        boll_upper = ta.get("boll_upper", current_price * 1.02)
        boll_lower = ta.get("boll_lower", current_price * 0.98)
        boll_middle = ta.get("boll_middle", current_price)
        
        # Calculate pivot points
        high_20 = max(highs[-20:])
        low_20 = min(lows[-20:])
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        s1 = 2 * pivot - high_20
        
        dist_to_support = current_price - s1
        dist_to_resistance = r1 - current_price
        
        near_support = dist_to_support < dist_to_resistance * 0.5
        near_resistance = dist_to_resistance < dist_to_support * 0.5

        # Yön-farkında skorlama:
        # UP trend + destek yakın = bounce setup (pass)
        # UP trend + direnç yakın = breakout riski (warning)
        # DOWN trend + destek yakın = breakdown riski (warning)
        # DOWN trend + direnç yakın = rejection setup (pass, SELL yönü için)
        if near_support:
            if trend_direction == "up":
                sr_status = "pass"; sr_color = "green"; sr_label = "DESTEK YAKINI"
                sr_comment = f"UP trend + destek yakın ({dist_to_support:.0f} pts). Bounce entry fırsatı."
                green_count += 1
            elif trend_direction == "down":
                sr_status = "warning"; sr_color = "yellow"; sr_label = "BREAKDOWN RİSKİ"
                sr_comment = f"DOWN trend + destek yakın. Kırılım → SL tetiklenme riski."
                yellow_count += 1
            else:
                sr_status = "warning"; sr_color = "yellow"; sr_label = "DESTEK YAKINI"
                sr_comment = f"Yönsüz piyasada destek yakın ({dist_to_support:.0f} pts)."
                yellow_count += 1
        elif near_resistance:
            if trend_direction == "down":
                sr_status = "pass"; sr_color = "green"; sr_label = "DİRENÇ REDDİ"
                sr_comment = f"DOWN trend + direnç yakın ({dist_to_resistance:.0f} pts). SELL setup için uygun."
                green_count += 1
            elif trend_direction == "up":
                sr_status = "warning"; sr_color = "yellow"; sr_label = "BREAKOUT BÖLGESİ"
                sr_comment = f"UP trend + direnç yakın. Kırılım veya rejection — teyit bekle."
                yellow_count += 1
            else:
                sr_status = "fail"; sr_color = "red"; sr_label = "DİRENÇ YAKINI"
                sr_comment = f"Yönsüz piyasada direnç yakın ({dist_to_resistance:.0f} pts). Satış baskısı gelebilir."
                red_count += 1
        else:
            sr_status = "warning"; sr_color = "yellow"; sr_label = "ORTADA"
            sr_comment = "Fiyat destek ve direnç arasında — net S/R sinyali yok."
            yellow_count += 1
        
        checks.append({
            "id": 5,
            "name": "Destek/Direnç Seviyeleri",
            "subtitle": "S/R + Pivot",
            "status": sr_status,
            "direction": "neutral",
            "color": sr_color,
            "label": sr_label,
            "details": {
                "price": round(current_price, 2),
                "s1": round(s1, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "dist_support": round(dist_to_support, 1),
                "dist_resistance": round(dist_to_resistance, 1)
            },
            "comment": sr_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 6️⃣ MOMENTUM GÖSTERGELERİ
        # ─────────────────────────────────────────────────────────────────────
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        stoch_k = ta.get("stoch_k", 50)
        
        bullish_momentum = rsi_14 > 50 and macd_hist > 0 and stoch_k > 50
        bearish_momentum = rsi_14 < 50 and macd_hist < 0 and stoch_k < 50
        
        if bullish_momentum:
            mom_status = "pass"
            mom_color = "green"
            mom_label = "YUKARI MOMENTUM"
            mom_comment = "Tüm momentum göstergeleri yukarı yönlü."
            green_count += 1
        elif bearish_momentum:
            mom_status = "fail"
            mom_color = "red"
            mom_label = "AŞAĞI MOMENTUM"
            mom_comment = "Tüm momentum göstergeleri aşağı yönlü."
            red_count += 1
        else:
            mom_status = "warning"
            mom_color = "yellow"
            mom_label = "KARARSIZ"
            mom_comment = "Momentum göstergeleri kararsız. Net bir yön yok."
            yellow_count += 1
        
        checks.append({
            "id": 6,
            "name": "Momentum Göstergeleri",
            "subtitle": "RSI/MACD/Stoch",
            "status": mom_status,
            "direction": "up" if bullish_momentum else "down" if bearish_momentum else "neutral",
            "color": mom_color,
            "label": mom_label,
            "details": {
                "rsi": round(rsi_14, 1),
                "macd_hist": round(macd_hist, 4),
                "stoch_k": round(stoch_k, 1)
            },
            "comment": mom_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 7️⃣ HACİM ANALİZİ — z-score tabanlı (20 mum baseline)
        # ─────────────────────────────────────────────────────────────────────
        # Endeksler (NDX, GDAXI) MT5'ten TICK VOLUME alır, gerçek hacim değil.
        # Futures-based sembollerde (XAUUSD, USOIL) de MT5 exchange volume'ı kısmen yansıtır.
        is_tick_volume = symbol in ("NDX.INDX", "GDAXI.INDX")
        vol_source_label = "tick" if is_tick_volume else "volume"

        # Son 20 mumun hacim baseline'ı (son mum hariç — henüz kapanmadı)
        baseline_window = [float(v) for v in volumes[-21:-1] if v > 0] if len(volumes) >= 21 else [float(v) for v in volumes[:-1] if v > 0]
        # Son tam mum (sondan 2.)
        current_volume = float(volumes[-2]) if len(volumes) >= 2 and volumes[-2] > 0 else 0.0

        volume_ratio = 1.0
        volume_z = 0.0
        if len(baseline_window) >= 5 and current_volume > 0:
            baseline_mean = float(np.mean(baseline_window))
            baseline_std = float(np.std(baseline_window)) or 1.0
            volume_ratio = current_volume / max(baseline_mean, 1e-9)
            volume_z = (current_volume - baseline_mean) / baseline_std

            logger.info(f"[EMEL Volume] {symbol} {timeframe} src={vol_source_label}: "
                        f"current={current_volume:.0f} baseline_mean={baseline_mean:.0f} "
                        f"ratio={volume_ratio:.2f} z={volume_z:.2f}")

            if volume_z >= 1.0:  # 1σ üzeri spike
                vol_status = "pass"; vol_color = "green"; vol_label = "HACİM SPİKE"
                vol_comment = f"{vol_source_label.capitalize()} z={volume_z:.1f}σ (spike). Hareket güçlü."
                green_count += 1
            elif volume_z <= -1.0:
                vol_status = "fail"; vol_color = "red"; vol_label = "DÜŞÜK HACİM"
                vol_comment = f"{vol_source_label.capitalize()} z={volume_z:.1f}σ. Hareket güvenilmez."
                red_count += 1
            else:
                vol_status = "warning"; vol_color = "yellow"; vol_label = "NORMAL HACİM"
                vol_comment = f"{vol_source_label.capitalize()} z={volume_z:+.1f}σ — ortalama band içinde."
                yellow_count += 1
        else:
            vol_status = "warning"; vol_color = "yellow"; vol_label = "VERİ YOK"
            vol_comment = f"Hacim baseline'ı oluşmuyor ({len(baseline_window)} mum)."
            yellow_count += 1
            logger.warning(f"[EMEL Volume] {symbol}: baseline yetersiz ({len(baseline_window)})")
        
        checks.append({
            "id": 7,
            "name": "Hacim Analizi",
            "subtitle": "Volume",
            "status": vol_status,
            "direction": "neutral",
            "color": vol_color,
            "label": vol_label,
            "details": {
                "z_score": round(volume_z, 2),
                "ratio": round(volume_ratio * 100, 0),
                "source": vol_source_label,
                "baseline_n": len(baseline_window),
                "trend": "Artıyor" if volume_z > 0 else "Azalıyor",
            },
            "comment": vol_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 8️⃣ LEARNING / GEÇMİŞ PERFORMANS
        # ─────────────────────────────────────────────────────────────────────
        # 2026-07-15 fix: "learning_insights" alanı PredictionResult'ta yoktu →
        # kontrol her zaman "VERİ YOK" veriyordu (ölü). Artık gerçek 30g EMEL WR.
        win_rate, sample_count = await _emel_recent_winrate(symbol)

        # İstatistiksel güven için min 10 örnek şart
        if sample_count < 10:
            learn_status = "warning"
            learn_color = "yellow"
            learn_label = "VERİ YOK"
            learn_comment = f"Benzer setup için yeterli geçmiş yok ({sample_count} örnek, min 10 gerekli)."
            yellow_count += 1
        elif win_rate >= 60:
            learn_status = "pass"; learn_color = "green"; learn_label = "İYİ GEÇMİŞ"
            learn_comment = f"Benzer setup'larda %{win_rate:.0f} başarı ({sample_count} örnek)."
            green_count += 1
        elif win_rate >= 45:
            learn_status = "warning"; learn_color = "yellow"; learn_label = "ORTA RİSK"
            learn_comment = f"Geçmiş performans ortalama (%{win_rate:.0f}, n={sample_count})."
            yellow_count += 1
        else:
            learn_status = "fail"; learn_color = "red"; learn_label = "DÜŞÜK BAŞARI"
            learn_comment = f"Benzer setup'larda düşük başarı (%{win_rate:.0f}, n={sample_count}). Dikkatli ol."
            red_count += 1
        
        checks.append({
            "id": 8,
            "name": "Learning / Geçmiş Performans",
            "subtitle": "Historical Analysis",
            "status": learn_status,
            "direction": "neutral",
            "color": learn_color,
            "label": learn_label,
            "details": {
                "win_rate": round(win_rate, 1),
                "samples": sample_count
            },
            "comment": learn_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 9️⃣ PORTFÖY RİSK YÖNETİMİ
        # ─────────────────────────────────────────────────────────────────────
        # 2026-07-15 fix: prediction dict'inde "portfolio_risk" alanı hiç yoktu
        # (PredictionResult'ta tanımsız) → kontrol her zaman current_risk=0 ile
        # PASS veriyordu (ölü kontrol, sabit +yeşil). Gerçek portföy riski artık
        # trading_engine.check_portfolio_risk'ten okunuyor (fail-open).
        current_risk = 0.0
        daily_limit = 3.0
        try:
            from services.trading_engine import check_portfolio_risk as _check_port_risk
            _pr = _check_port_risk(symbol, prediction.get("direction") or "BUY")
            _risk_level = str(_pr.get("risk_level") or "").lower()
            if not _pr.get("can_trade", True):
                port_status = "fail"; port_color = "red"; port_label = "LİMİT AŞILDI"
                port_comment = f"Portföy riski: {_pr.get('reason') or 'yeni pozisyon engellendi.'}"
                red_count += 1
            elif _risk_level in ("high", "elevated", "critical") or _pr.get("warnings"):
                port_status = "warning"; port_color = "yellow"; port_label = "DİKKAT"
                _warn = (_pr.get("warnings") or [f"risk seviyesi {_risk_level}"])[0]
                port_comment = f"Portföy riski yükseldi: {_warn}"
                yellow_count += 1
            else:
                port_status = "pass"; port_color = "green"; port_label = "UYGUN"
                port_comment = "Portföy risk limitleri uygun. Yeni pozisyona izin veriliyor."
                green_count += 1
        except Exception as _port_err:
            logger.debug(f"[EMEL Portfolio] {symbol}: risk servisi yok ({_port_err}) — nötr")
            port_status = "warning"; port_color = "yellow"; port_label = "VERİ YOK"
            port_comment = "Portföy risk servisi erişilemedi — nötr sayıldı."
            yellow_count += 1
        
        checks.append({
            "id": 9,
            "name": "Portföy Risk Yönetimi",
            "subtitle": "Risk Management",
            "status": port_status,
            "direction": "neutral",
            "color": port_color,
            "label": port_label,
            "details": {
                "current_risk": round(current_risk, 1),
                "daily_limit": daily_limit
            },
            "comment": port_comment
        })

        # ─── 10. MAKRO UYUM (DXY / US10Y / VIX) — 2026-07-01, rapor aksiyon #10 ──
        # yfinance makro verisi (macro_data_service, saatlik) EMEL'e 10. kontrol
        # olarak bağlandı. XAUUSD/USOIL: DXY + US10Y günlük değişimi → emtia
        # rüzgar yönü. NDX/GDAXI: VIX günlük değişimi → risk iştahı. Fail-open:
        # makro veri yoksa nötr (warning) kalır, skoru etkilemez.
        macro_status = "warning"
        macro_dir = "neutral"
        macro_comment = "Makro veri henüz hazır değil (nötr katkı)"
        macro_details: Dict[str, Any] = {}
        try:
            from services.macro_data_service import get_snapshot as _macro_get_snapshot
            _msnap = _macro_get_snapshot()
            _dxy = _msnap.get("DXY")
            _us10y = _msnap.get("US10Y")
            _vix = _msnap.get("VIX")
            if symbol in ("XAUUSD", "USOIL.FOREX"):
                _macro_score = 0.0
                if _dxy is not None and _dxy.change_1d_pct is not None:
                    _macro_score -= _dxy.change_1d_pct  # DXY zayıflarsa emtia lehine
                    macro_details["dxy_1d_pct"] = round(_dxy.change_1d_pct, 2)
                if _us10y is not None and _us10y.change_1d_pct is not None:
                    _macro_score -= 0.5 * _us10y.change_1d_pct
                    macro_details["us10y_1d_pct"] = round(_us10y.change_1d_pct, 2)
                macro_details["composite"] = round(_macro_score, 2)
                if _macro_score > 0.15:
                    macro_dir, macro_status = "up", "pass"
                    macro_comment = "DXY/US10Y zayıflıyor → emtia için BUY rüzgarı"
                elif _macro_score < -0.15:
                    macro_dir, macro_status = "down", "pass"
                    macro_comment = "DXY/US10Y güçleniyor → emtia için SELL rüzgarı"
                else:
                    macro_comment = "Makro nötr (DXY/US10Y belirgin hareket yok)"
            else:
                if _vix is not None and _vix.change_1d_pct is not None:
                    macro_details["vix_1d_pct"] = round(_vix.change_1d_pct, 2)
                    if _vix.change_1d_pct < -2.0:
                        macro_dir, macro_status = "up", "pass"
                        macro_comment = "VIX düşüyor → risk iştahı, endeks BUY rüzgarı"
                    elif _vix.change_1d_pct > 4.0:
                        macro_dir, macro_status = "down", "pass"
                        macro_comment = "VIX sıçraması → risk-off, endeks SELL rüzgarı"
                    else:
                        macro_comment = "Makro nötr (VIX belirgin hareket yok)"
        except Exception as _macro_check_err:
            logger.debug(f"EMEL macro check fail-open: {_macro_check_err}")

        checks.append({
            "id": 10,
            "name": "Makro Uyum",
            "subtitle": "DXY / US10Y / VIX",
            "status": macro_status,
            "direction": macro_dir,
            "color": "green" if macro_status == "pass" else "yellow",
            "label": ("BUY RÜZGARI" if macro_dir == "up" else "SELL RÜZGARI") if macro_status == "pass" else "NÖTR",
            "details": macro_details,
            "comment": macro_comment
        })

        # ─────────────────────────────────────────────────────────────────────
        # KONFLUANS TABANLI AĞIRLIKLI SİNYAL KATMANI (YENİ)
        # ─────────────────────────────────────────────────────────────────────
        
        # 1. ENSTRÜMAN-SPESİFİK AĞIRLIKLAR
        # 2026-07-01 (rapor 4.4 + aksiyon #10): "macro" faktörü eklendi
        # (emtialarda ağır, endekslerde hafif). GDAXI: sentetik tick-volume
        # ağırlığı 15→8 düşürüldü, trend 20→25 yükseltildi, SR 15→12
        # (pivot DAX'ta zayıf referans — rapor 4.4).
        SYMBOL_WEIGHTS = {
            "NDX.INDX": {
                "trend": 25, "mtf": 20, "regime": 15, "momentum": 20,
                "volume": 15, "sr": 10, "pattern": 15, "portfolio": 20,
                "macro": 5
            },
            "GDAXI.INDX": {
                "trend": 25, "mtf": 25, "regime": 15, "momentum": 20,
                "volume": 8, "sr": 12, "pattern": 10, "portfolio": 20,
                "macro": 5
            },
            "XAUUSD": {
                "trend": 15, "mtf": 20, "regime": 15, "momentum": 25,
                "volume": 10, "sr": 20, "pattern": 15, "portfolio": 20,
                "macro": 15
            },
            "USOIL.FOREX": {
                "trend": 20, "mtf": 15, "regime": 20, "momentum": 20,
                "volume": 20, "sr": 15, "pattern": 10, "portfolio": 20,
                "macro": 10
            }
        }
        
        weights = SYMBOL_WEIGHTS.get(symbol, SYMBOL_WEIGHTS["NDX.INDX"])
        
        # 2. FAKTÖR DURUMLARINI HARİTALA
        factor_status = {
            "trend": trend_status,      # pass/warning/fail
            "mtf": mtf_status,
            "regime": regime_status,
            "momentum": mom_status,
            "volume": vol_status,
            "sr": sr_status,
            "pattern": pattern_status,
            "portfolio": port_status,
            "macro": macro_status       # 2026-07-01: 10. kontrol
        }
        
        # 3. YÖNLÜ ağırlıklı skor: yönlü faktörler (trend, mtf, momentum, sr, pattern)
        #    pass olduğunda faktörün kendi yönüne göre +/- skor ekler.
        #    Salt kalite faktörleri (regime, volume, portfolio, learning) skoru azaltır/artırır
        #    ama yön kararı vermez.
        directional_factors = {"trend", "mtf", "momentum", "sr", "pattern", "macro"}

        # Momentum yönü (label yerine flag kullan)
        mom_direction = "up" if bullish_momentum else "down" if bearish_momentum else "neutral"
        # SR yönü (trend'e paralel setup'ta aynı yönde katkı)
        sr_direction = trend_direction if sr_status == "pass" else "neutral"
        # Pattern yönü
        pattern_direction = "up" if pattern_signal == "bullish" else "down" if pattern_signal == "bearish" else "neutral"

        factor_dirs = {
            "trend": trend_direction,
            "mtf": main_dir if mtf_status == "pass" else "neutral",
            "momentum": mom_direction,
            "sr": sr_direction,
            "pattern": pattern_direction,
            "macro": macro_dir if macro_status == "pass" else "neutral",
        }

        # 2026-07-15 fix: kalite faktörleri (regime/volume/portfolio) eskiden
        # yönlü skora HER ZAMAN +işaretli katkı ekliyordu → her kalite onayı
        # skoru BUY yönüne itiyor, SELL kurulumlarını zayıflatıyordu (sistematik
        # long yanlılığı; ör. NDX'te sabit +10 portfolio + +7.5 regime). Artık
        # iki fazlı: önce yönlü faktörler işareti belirler, sonra kalite
        # faktörleri işaret-farkındalıklı olarak yalnızca BÜYÜKLÜĞÜ ayarlar.
        score = 0.0
        factor_contributions: Dict[str, Dict[str, Any]] = {}
        for factor, status in factor_status.items():
            if factor not in directional_factors:
                continue
            weight = weights.get(factor, 15)
            contribution = 0.0
            fdir = factor_dirs.get(factor, "neutral")
            if status == "pass" and fdir == "up":
                contribution = +weight
            elif status == "pass" and fdir == "down":
                contribution = -weight
            elif status == "fail":
                # fail = yön bilgisi var (trend down stack gibi) → karşı yön skoruna eksi
                if fdir == "up":
                    contribution = -weight
                elif fdir == "down":
                    contribution = +weight

            score += contribution
            factor_contributions[factor] = {
                "weight": weight, "status": status, "contribution": round(contribution, 1),
                "direction": factor_dirs.get(factor)
            }

        _dir_sign = 1.0 if score > 0 else (-1.0 if score < 0 else 0.0)
        for factor, status in factor_status.items():
            if factor in directional_factors:
                continue
            weight = weights.get(factor, 15)
            contribution = 0.0
            if status == "pass":
                contribution = _dir_sign * weight * 0.5   # magnitude'u güçlendirir
            elif status == "fail":
                contribution = -_dir_sign * weight        # magnitude'u HOLD'a çeker

            score += contribution
            factor_contributions[factor] = {
                "weight": weight, "status": status, "contribution": round(contribution, 1),
                "direction": factor_dirs.get(factor)
            }

        # 4. KONFLUANS BONUS/CEZALARI
        bonuses: List[Dict[str, Any]] = []

        # Holy Trinity — pure direction check (no label string match)
        if (mtf_status == "pass" and trend_status == "pass" and mom_status == "pass"
                and trend_direction == mom_direction and trend_direction == main_dir
                and trend_direction in ("up", "down")):
            delta = 15 if trend_direction == "up" else -15
            score += delta
            bonuses.append({"name": f"Holy Trinity ({'Bullish' if trend_direction == 'up' else 'Bearish'})", "value": delta})

        # Yatay + düşük hacim cezası (yönsüz)
        if regime_status != "pass" and vol_status == "fail":
            penalty = 15
            score -= penalty if score >= 0 else 0  # pozitif skoru düşür
            score += penalty if score < 0 else 0   # negatif skoru toparla (daha az negatif)
            # Simpler: magnitude azalt
            bonuses.append({"name": "Low Volume + Ranging", "value": -penalty, "applied_to": "magnitude"})

        # Portföy riski aşımı = kesin red (hard gate)
        if port_status == "fail":
            score = 0  # yön kararını öldür, HOLD'a düşer
            bonuses.append({"name": "Risk Limit Exceeded", "value": 0, "hard_gate": True})
        
        # 5. SİNYAL SEVİYESİ BELİRLE
        # DÜZELTME: Sinyal yönü kendi 9-check skorundan türetilir, ML'den DEĞİL
        # ML prediction yalnızca minor boost olarak skora eklenir
        ml_confidence = prediction.get("confidence", 50)

        # ML sinyali ile skoru birleştir (küçük boost, yön değiştirmez)
        ml_boost = 0
        ml_dir = prediction.get("direction", "HOLD")
        if ml_dir == "BUY":
            ml_boost = (ml_confidence - 50) / 5  # +0 to +10
        elif ml_dir == "SELL":
            ml_boost = -(ml_confidence - 50) / 5  # -0 to -10

        final_score = score + ml_boost

        # ─── ATH / Session hard gates ───
        gate_notes: List[str] = []
        regime_info: Dict[str, Any] = {}
        try:
            from services.market_regime_service import get_regime_info as _get_regime
            regime_info = await _get_regime(symbol) or {}
        except Exception as reg_err:
            logger.warning(f"EMEL regime gate failed: {reg_err}")

        # ATH zone: SELL bloklanır (CLAUDE.md ATH protocol)
        if regime_info.get("is_ath_zone") and final_score < 0:
            gate_notes.append("ATH zone — SELL bloklandı, HOLD'a zorlandı")
            final_score = max(final_score, 0)
            bonuses.append({"name": "ATH Zone Block (SELL)", "value": 0, "hard_gate": True})

        # Market session gate: piyasa kapalıysa yeni sinyal üretme (HOLD)
        try:
            from utils.market_hours import is_symbol_market_open
            if not is_symbol_market_open(symbol):
                gate_notes.append("Piyasa kapalı — sinyal HOLD'a indirildi")
                # skor gösterilsin ama kararı HOLD'a düşür
                market_closed = True
            else:
                market_closed = False
        except Exception:
            market_closed = False
        
        # 6. KARAR VER — Yön 9-check skorundan gelir
        if final_score >= 70:
            decision = "STRONG_BUY"
            signal = "BUY"
            decision_reason = f"Güçlü konfluans skoru: {final_score:.1f}"
        elif final_score >= 55:
            decision = "BUY"
            signal = "BUY"
            decision_reason = f"Konfluans skoru: {final_score:.1f}"
        elif final_score >= 40:
            decision = "BUY_SETUP"
            signal = "HOLD"
            decision_reason = f"Bekleyen alış fırsatı: {final_score:.1f} - Koşullar oluşunca giriş"
        elif final_score <= -70:
            decision = "STRONG_SELL"
            signal = "SELL"
            decision_reason = f"Güçlü satış konfluansı: {final_score:.1f}"
        elif final_score <= -55:
            decision = "SELL"
            signal = "SELL"
            decision_reason = f"Satış konfluansı: {final_score:.1f}"
        elif final_score <= -40:
            decision = "SELL_SETUP"
            signal = "HOLD"
            decision_reason = f"Bekleyen satış fırsatı: {final_score:.1f} - Koşullar oluşunca giriş"
        else:
            decision = "HOLD"
            signal = "HOLD"
            decision_reason = f"Yetersiz konfluans: {final_score:.1f} (40-55 arası sinyal gerekli)"

        # Market closed: hard-override to HOLD (gösterimde kalır, loglanmaz)
        if market_closed and signal in ("BUY", "SELL"):
            decision = "HOLD"
            signal = "HOLD"
            decision_reason = "Piyasa kapalı — yeni sinyal üretilmedi"

        # Confidence = reliability × |final_score|
        # reliability = clamp(0-1, resolved_samples / 8) — low-sample penalizasyonu
        reliability = max(0.0, min(1.0, sample_count / 8.0)) if sample_count > 0 else 0.4
        confidence = min(abs(final_score) * (0.5 + 0.5 * reliability), 100)
        
        # Build rejection reasons
        rejections = []
        for check in checks:
            if check["status"] == "fail":
                rejections.append(f"✗ {check['name']}: {check['label']}")
        
        # Build conditions for entry
        conditions = []
        if mtf_status != "pass":
            conditions.append("MTF uyumu sağlanmalı")
        if mom_status != "pass":
            conditions.append("Momentum onayı gerekli")
        if vol_status == "fail":
            conditions.append("Hacim artmalı")
        
        # ─────────────────────────────────────────────────────────────────────
        # LEARNING ENTEGRASYONU - Sinyali kaydet
        # ─────────────────────────────────────────────────────────────────────
        if decision in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                
                context = {
                    "ta": ta,
                    "source": "EMEL",
                    "checks_summary": {
                        "green": green_count,
                        "yellow": yellow_count,
                        "red": red_count
                    },
                    "ml_prediction": {
                        "direction": signal,
                        "confidence": confidence,
                        "entry_price": current_price,
                        "target_price": prediction.get("target_price"),
                        "stop_price": prediction.get("stop_price")
                    }
                }
                
                analysis = {
                    "final_decision": decision,
                    "confidence": confidence,
                    "model_used": "EMEL-9-Check"
                }
                
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe=timeframe,
                    strategy="EMEL",
                    model_type="emel",
                )
                logger.info(f"EMEL signal logged: {symbol} {decision} @ {current_price}")
                
                # ─── TERSİNE NASDAQ: NDX.INDX sinyallerini tersine çevirerek logla ──
                if symbol == "NDX.INDX":
                    inverse_signal = "SELL" if signal == "BUY" else "BUY"
                    inverse_context = {
                        "ta": ta,
                        "source": "EMEL_INVERSE",
                        "checks_summary": {
                            "green": green_count,
                            "yellow": yellow_count,
                            "red": red_count
                        },
                        "ml_prediction": {
                            "direction": inverse_signal,
                            "confidence": confidence,
                            "entry_price": current_price,
                            "target_price": prediction.get("stop_price"),  # TP↔SL swap
                            "stop_price": prediction.get("target_price")
                        }
                    }
                    inverse_analysis = {
                        "final_decision": inverse_signal,
                        "confidence": confidence,
                        "model_used": "EMEL-9-Inverse"
                    }
                    await log_prediction(
                        symbol=symbol,
                        context=inverse_context,
                        analysis=inverse_analysis,
                        timeframe=timeframe,
                        strategy="EMEL_INVERSE",
                        model_type="emel_inverse",
                    )
                    logger.info(f"EMEL INVERSE signal logged: {symbol} {inverse_signal} @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log EMEL prediction: {log_err}")
        
        rebound_summary = None
        try:
            from services.rebound_filter_service import analyze_rebound
            rebound_summary = await analyze_rebound(symbol, timeframe=timeframe)
        except Exception as rebound_err:
            logger.warning(f"EMEL rebound integration failed: {rebound_err}")
        
        _now_iso = datetime.now().isoformat()
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "effective_timeframe": effective_tf,
            "timestamp": _now_iso,
            "signal_timestamp": _resolve_signal_timestamp(symbol, _now_iso),
            "signal": decision,
            "confidence": confidence,
            "price": current_price,
            "reliability": round(reliability, 2),
            "gates": {
                "is_ath_zone": bool(regime_info.get("is_ath_zone")),
                "market_open": not market_closed,
                "notes": gate_notes,
            },
            "checks": checks,
            "confluence": {
                "score": round(final_score, 1),
                "raw_score": round(score, 1),
                "ml_boost": round(ml_boost, 1),
                "max_score": 100,
                "min_signal_threshold": 40,
                "strong_threshold": 70,
                "weights_applied": weights,
                "factor_contributions": factor_contributions,
                "bonuses": bonuses,
                "calculation_method": "weighted_confluence_v2"
            },
            "summary": {
                "green_count": green_count,
                "yellow_count": yellow_count,
                "red_count": red_count,
                "total": 9,
                "decision": decision,
                "decision_reason": decision_reason,
                "rejections": rejections,
                "entry_conditions": conditions if decision in ["BUY_SETUP", "SELL_SETUP"] else [],
                "macro_notes": _emel_macro_notes(symbol, decision),
            },
            "rebound": rebound_summary
        }
        
    except Exception as e:
        logger.error(f"EMEL analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE 1 (ALGORİTMİK) - GELİŞTİRİLMİŞ KURAL TABANLI SCALP
# Sorun düzeltmeleri: 
#   - Son 5 mum yetersiz → 10 mum + EMA stack + hacim eklendi
@router.get("/pulse/{symbol}", response_model=PulseResponse)
async def get_pulse_analysis(symbol: str, timeframe: str = "5m", refresh: bool = False):
    """
    PULSE 1 - Geliştirilmiş Algoritmik Scalp Analizi
    İki kademeli sinyal: SCOUT (izle) + CONFIRM (işlem yap)
    
    REGIME-AWARE: Güçlü trend modlarında (STRONG_TREND_UP/DOWN) devre dışı kalır.
    Sadece RANGING ve TRANSITION rejimlerinde aktif çalışır.
    """
    try:
        cached_response = None if refresh else _get_cached_panel_analysis("pulse1", symbol, timeframe)
        if cached_response:
            return cached_response

        response_timestamp = datetime.now(timezone.utc).isoformat()
        signal_timestamp = _resolve_signal_timestamp(symbol, response_timestamp)

        from services.ml_prediction_service import _compute_technical_indicators
        from services.harmonic_pattern_service import get_pattern_adjustment
        from services.market_data_service import get_ohlcv_data
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout
        
        # ─── REGIME CHECK: Pulse 1 disabled in strong trends ────────────
        regime = await detect_regime(symbol)

        # 2026-07-01 (rapor aksiyon #3): GDAXI'de pulse1 askıda — 60g: 446W/1339L
        # (%25 WR), inverse dahi %38. GDAXI_PULSE1_ENABLED=1 ile tekrar açılır.
        from services.signal_gates import pulse1_symbol_enabled
        _pulse1_suspended = not pulse1_symbol_enabled(symbol)

        if regime.model_weights.get("pulse1", 0) == 0 or _pulse1_suspended:
            _disable_reason = (
                "Pulse 1 GDAXI'de askıda: 60 günlük WR %25, sinyaller DAX 5m gürültüsünde bilgi taşımıyor (gösterge denetimi 2026-07-01)"
                if _pulse1_suspended
                else f"Pulse 1 devre dışı: {regime.regime} rejiminde scalp sinyalleri güvenilir değil"
            )
            payload = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": response_timestamp,
                "signal_timestamp": signal_timestamp,
                "signal": "HOLD",
                "signal_type": "SYMBOL_SUSPENDED" if _pulse1_suspended else "REGIME_DISABLED",
                "pulse_score": 0,
                "regime": {
                    "type": regime.regime,
                    "reason": _disable_reason,
                    "adx": regime.adx,
                    "session": regime.session,
                    "allowed_models": [k for k, v in regime.model_weights.items() if v > 0],
                },
                "trend": {"direction": "neutral", "strength": 0, "label": "REGIME DISABLED", "strength_pct": 0, "last_5_candles": []},
                "price": {"current": regime.current_price or 0, "change_5": 0},
                "levels": {"r2": 0, "r1": 0, "pivot": 0, "s1": {"price": 0, "distance": 0, "alert": False}, "s2": 0, "nearest": "none", "nearest_distance": 0},
                "momentum": {"rsi": {"value": 50, "trend": "neutral"}, "macd": {"value": 0, "trend": "neutral"}, "stochastic": {"value": 50, "trend": "neutral"}},
                "volume": {"status": "unknown", "label": "N/A", "ratio": 0, "available": False},
                "score_breakdown": {},
                "decision_notes": [_disable_reason if _pulse1_suspended else f"Pulse 1 kapalı: {regime.regime} rejimi"],
                "suggestion": {"text": ("⛔ Pulse 1 GDAXI'de askıda (gösterge denetimi). ML ve Pulse 2 kullanın." if _pulse1_suspended else f"⛔ Pulse 1 {regime.regime} rejiminde devre dışı. ML ve Pulse 2/3 kullanın."), "target": regime.current_price or 0, "stop": regime.current_price or 0, "target_distance": 0, "stop_distance": 0, "rr_ratio": 0, "timeframe_estimate": "N/A"}
            }
            _set_cached_panel_analysis("pulse1", symbol, timeframe, payload)
            return payload
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        if is_timed_out:
            payload = {
                "symbol": symbol, "timeframe": timeframe, "timestamp": response_timestamp,
                "signal_timestamp": signal_timestamp,
                "signal": "HOLD", "signal_type": "TIMEOUT",
                "pulse_score": 0,
                "regime": {"type": regime.regime, "reason": timeout_reason},
                "decision_notes": [timeout_reason],
                "suggestion": {"text": f"⏸️ {timeout_reason}", "target": 0, "stop": 0, "target_distance": 0, "stop_distance": 0, "rr_ratio": 0, "timeframe_estimate": "N/A"},
                "trend": {"direction": "neutral", "strength": 0, "label": "TIMEOUT", "strength_pct": 0, "last_5_candles": []},
                "price": {"current": regime.current_price or 0, "change_5": 0},
                "levels": {"r2": 0, "r1": 0, "pivot": 0, "s1": {"price": 0, "distance": 0, "alert": False}, "s2": 0, "nearest": "none", "nearest_distance": 0},
                "momentum": {"rsi": {"value": 50, "trend": "neutral"}, "macd": {"value": 0, "trend": "neutral"}, "stochastic": {"value": 50, "trend": "neutral"}},
                "volume": {"status": "unknown", "label": "N/A", "ratio": 0, "available": False},
                "score_breakdown": {},
            }
            _set_cached_panel_analysis("pulse1", symbol, timeframe, payload)
            return payload
        
        # Get market data - 100 bar (EMA20 için yeterli)
        # XAUUSD: 1H derives from 30m in DataHub — fallback to 5m if insufficient
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 20:
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=100)
        if not ohlcv or len(ohlcv) < 20:
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=100)
        if not ohlcv or len(ohlcv) < 20:
            return {"error": "Insufficient data"}
        
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # ─── PUANLAMA SİSTEMİ (0-100) ─────────────────────────────────────
        score = 0.0
        score_details = {}
        decision_notes = []
        
        # 1. Son 10 mum yönü (20 puan) - Eskiden 5 mumdu, artık 10
        last_10 = []
        for i in range(-10, 0):
            if closes[i] > closes[i-1]:
                last_10.append("up")
            elif closes[i] < closes[i-1]:
                last_10.append("down")
            else:
                last_10.append("neutral")
        
        up_count = last_10.count("up")
        down_count = last_10.count("down")
        
        if up_count >= 7:
            score += 20
            candle_bias = "up"
        elif up_count >= 5:
            score += 10
            candle_bias = "up"
        elif down_count >= 7:
            score += 20
            candle_bias = "down"
        elif down_count >= 5:
            score += 10
            candle_bias = "down"
        else:
            candle_bias = "neutral"
        
        score_details["candle_10"] = {"up": up_count, "down": down_count, "bias": candle_bias, "pts": round(score)}
        
        # 2. EMA Stack (25 puan) - TRUE EMA5 > EMA10 > EMA20
        ema_5 = _calc_ema(closes, 5)
        ema_10 = _calc_ema(closes, 10)
        ema_20 = ta.get("ema_20", current_price)
        
        ema_pts = 0
        if ema_5 > ema_10 > ema_20:
            ema_pts = 25
            ema_stack = "bullish"
        elif ema_5 > ema_10:
            ema_pts = 12
            ema_stack = "weak_bullish"
        elif ema_5 < ema_10 < ema_20:
            ema_pts = 25
            ema_stack = "bearish"
        elif ema_5 < ema_10:
            ema_pts = 12
            ema_stack = "weak_bearish"
        else:
            ema_stack = "neutral"
        score += ema_pts
        score_details["ema_stack"] = {"ema5": round(ema_5, 2), "ema10": round(ema_10, 2), "ema20": round(ema_20, 2), "stack": ema_stack, "pts": ema_pts}
        
        # 3. RSI Momentum (20 puan)
        # 2026-07-01 (rapor 3.1): Aşırı bölge cezası trend-aware yapıldı.
        # Altın ATH trendinde RSI haftalarca 70+ kalabiliyor; yönle uyumlu aşırı
        # RSI = momentum devamıdır, ceza XAU SELL felaketinin (%19 WR) kaynağıydı.
        rsi_14 = ta.get("rsi_14", 50)
        rsi_pts = 0
        _rsi_extreme_aligned = (rsi_14 > 75 and candle_bias == "up") or (rsi_14 < 25 and candle_bias == "down")
        if 40 <= rsi_14 <= 60:
            rsi_pts = 10  # Neutral = trend devam ediyor
        elif _rsi_extreme_aligned and (regime.regime in ("TRANSITION", "STRONG_TREND_UP", "STRONG_TREND_DOWN") or regime.is_ath_zone):
            rsi_pts = 10  # Trend ortamında yönle uyumlu aşırı RSI = momentum, ceza yok
            decision_notes.append(f"RSI {rsi_14:.0f} aşırı ama trend yönünde (momentum devam)")
        elif (rsi_14 > 60 and candle_bias == "up") or (rsi_14 < 40 and candle_bias == "down"):
            rsi_pts = 20  # RSI yönle uyumlu
        elif rsi_14 > 75 or rsi_14 < 25:
            rsi_pts = 0  # Aşırı bölge + yön uyumsuz = risk
        else:
            rsi_pts = 5
        score += rsi_pts
        score_details["rsi"] = {"value": round(rsi_14, 1), "pts": rsi_pts}
        
        # 4. MACD Histogram (15 puan)
        macd_hist = ta.get("macd_hist", 0)
        macd_pts = 0
        if macd_hist > 0 and candle_bias == "up":
            macd_pts = 15
        elif macd_hist < 0 and candle_bias == "down":
            macd_pts = 15
        elif abs(macd_hist) < 0.01:
            macd_pts = 5
        else:
            if regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
                macd_pts = 3
                decision_notes.append("MACD gecikmeli, trend güçlü devam ediyor")
            else:
                decision_notes.append("MACD yönü desteklemiyor")
        score += macd_pts
        score_details["macd"] = {"hist": round(macd_hist, 4), "pts": macd_pts}
        
        # 5. Hacim (10 puan)
        # NOT: Son mum tam kapanmamış olabilir (hacim=0), bu yüzden son 4 TAM mumu kullan
        vol_pts = 0
        volume_status = "unknown"
        volume_ratio = 1.0
        
        # Son 5 mumdan 0 olmayanları al (son mum hariç)
        recent_volumes = [v for v in volumes[-5:-1] if v > 0] if len(volumes) >= 5 else [v for v in volumes if v > 0]
        
        if len(recent_volumes) >= 2:
            avg_volume = float(np.mean(recent_volumes))
            current_volume = float(recent_volumes[-1])  # Son tam mum
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio >= 1.3:
                vol_pts = 10
                volume_status = "high"
            elif volume_ratio >= 1.1:
                vol_pts = 5
                volume_status = "normal"
            else:
                volume_status = "low"
        score += vol_pts
        score_details["volume"] = {"ratio": round(volume_ratio, 2), "status": volume_status, "pts": vol_pts}
        
        # 6. H4 Trend Uyumu (10 puan) — Stochastic'in yerini aldı (2026-07-01)
        # Stoch 5m'de RSI-14 ile ~%90 korele idi: aynı mean-reversion bilgisini
        # iki kez sayıp counter-trend sinyali güçlendiriyordu (rapor 3.1).
        # Stoch artık yalnızca görüntü amaçlı (pts=0), puan H4 uyumuna taşındı.
        stoch_k = ta.get("stoch_k", 50)
        score_details["stochastic"] = {"k": round(stoch_k, 1), "pts": 0, "display_only": True}

        h4_trend = "neutral"
        h4_pts = 3  # 4h verisi yoksa nötr katkı (fail-soft)
        try:
            _h4_candles = await get_ohlcv_data(symbol, timeframe="4h", limit=60)
            if _h4_candles and len(_h4_candles) >= 25:
                _h4_closes = [float(c["close"]) for c in _h4_candles]
                _h4_ema20 = _calc_ema(_h4_closes, 20)
                h4_trend = "up" if _h4_closes[-1] > _h4_ema20 else "down"
                if (h4_trend == "up" and candle_bias == "up") or (h4_trend == "down" and candle_bias == "down"):
                    h4_pts = 10
                elif candle_bias == "neutral":
                    h4_pts = 3
                else:
                    h4_pts = 0
                    decision_notes.append(f"H4 trend ({h4_trend}) 5m bias ile çelişiyor")
        except Exception as _h4_err:
            logger.debug(f"PULSE1 H4 alignment skipped: {_h4_err}")
        score += h4_pts
        score_details["h4_alignment"] = {"trend": h4_trend, "pts": h4_pts}

        preferred_pattern_direction = "BUY" if candle_bias == "up" else "SELL" if candle_bias == "down" else None
        pattern_result = await get_pattern_adjustment(symbol, timeframe="4h")
        pattern_context = _summarize_panel_patterns(pattern_result.get("patterns", []), preferred_pattern_direction)
        pattern_pts = 0
        if pattern_context.get("count", 0) > 0:
            top_pattern = pattern_context.get("top_pattern") or {}
            top_name = top_pattern.get("name_tr") or top_pattern.get("name") or "Pattern"
            if pattern_context.get("aligned_count", 0) > 0 and pattern_context.get("opposing_count", 0) == 0:
                # Formasyon teyit bonusu yön kapısı (2026-07-26): shadow tracker
                # ölçümünde formasyon SELL sinyalleri %22.6 (n=115, p≈3e-9) —
                # ayı formasyonunu "teyit" sayıp skoru artırmak ölçülen zarar.
                from services.signal_gates import pattern_bonus_allowed
                if pattern_bonus_allowed(symbol, preferred_pattern_direction):
                    pattern_pts = 10 if str(top_pattern.get("category") or "").lower() == "harmonic" else 6
                    score += pattern_pts
                    decision_notes.append(f"4H pattern onayı: {top_name}")
                else:
                    decision_notes.append(
                        f"4H pattern onayı sayılmadı ({top_name}): bu yönde dedektör "
                        f"canlı ölçümde kaybediyor")
            elif preferred_pattern_direction and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
                decision_notes.append(f"4H pattern çelişkisi: {top_name}")
            else:
                decision_notes.append(f"4H pattern tespit edildi: {top_name}")
        score_details["pattern"] = {"count": pattern_context.get("count", 0), "bias": pattern_context.get("bias", "NEUTRAL"), "pts": pattern_pts}
        
        # ─── TOPLAM SKOR → SİNYAL TİPİ ───────────────────────────────────
        # Yönü belirle (dominant yön)
        bullish_score = 0
        bearish_score = 0
        if candle_bias == "up": bullish_score += 30
        elif candle_bias == "down": bearish_score += 30
        if ema_stack in ["bullish", "weak_bullish"]: bullish_score += 25
        elif ema_stack in ["bearish", "weak_bearish"]: bearish_score += 25
        if rsi_14 > 50: bullish_score += 15
        else: bearish_score += 15
        if macd_hist > 0: bullish_score += 15
        else: bearish_score += 15
        # 2026-07-01: Stoch oyu H4 trend oyuyla değiştirildi (mükerrer bilgiydi)
        if h4_trend == "up": bullish_score += 15
        elif h4_trend == "down": bearish_score += 15
        
        if bullish_score > bearish_score:
            trend_direction = "up"
        elif bearish_score > bullish_score:
            trend_direction = "down"
        else:
            trend_direction = "neutral"
        
        trend_strength = score / 100.0
        
        # İki kademeli sinyal sistemi
        signal_type = "HOLD"  # HOLD / SCOUT / CONFIRM
        pulse_signal = "HOLD"
        
        if score >= 56:  # 56'ya düşürüldü (threshold: 56)
            signal_type = "CONFIRM"
            pulse_signal = "BUY" if trend_direction == "up" else "SELL" if trend_direction == "down" else "HOLD"
        elif score >= 35:  # Scout threshold da düşürüldü (40'tan)
            signal_type = "SCOUT"
            pulse_signal = "BUY" if trend_direction == "up" else "SELL" if trend_direction == "down" else "HOLD"
        else:
            signal_type = "HOLD"
            pulse_signal = "HOLD"

        if pattern_context.get("count", 0) > 0 and preferred_pattern_direction and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"
            elif signal_type == "SCOUT":
                signal_type = "HOLD"
                pulse_signal = "HOLD"
        score = min(score, 100)
        
        # ─── SEVİYELER ────────────────────────────────────────────────────
        high_20 = float(np.max(highs[-20:]))
        low_20 = float(np.min(lows[-20:]))
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        r2 = pivot + (high_20 - low_20)
        s1 = 2 * pivot - high_20
        s2 = pivot - (high_20 - low_20)
        
        dist_s1 = current_price - s1
        dist_r1 = r1 - current_price
        nearest_level = "s1" if dist_s1 < dist_r1 else "r1"
        nearest_distance = min(dist_s1, dist_r1)
        
        # Hedef ve Stop — SCALPING distances (instrument-specific)
        atr_14 = ta.get("atr_14", abs(high_20 - low_20) / 20)
        scalp_dir = "BUY" if trend_direction == "up" else "SELL" if trend_direction == "down" else "HOLD"
        target, stop, potential_profit, potential_loss = _scalp_tp_sl(symbol, current_price, scalp_dir, atr_14)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # ─── FİLTRELER (REGIME-AWARE) ────────────────────────────────────
        # R/R minimum from regime (dynamic instead of static 1.2)
        min_rr = regime.min_rr
        if pulse_signal in ["BUY", "SELL"] and rr_ratio < min_rr:
            decision_notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr})")
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"  # CONFIRM → SCOUT downgrade
            else:
                pulse_signal = "HOLD"
                signal_type = "HOLD"
        
        # RSI filtresi - REGIME-AWARE (trend modunda RSI>70 = momentum, sat değil)
        rsi_interpretation = interpret_rsi(rsi_14, regime, pulse_signal)
        if rsi_interpretation["action"] == "caution":
            decision_notes.append(rsi_interpretation["note"])
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"
        elif rsi_interpretation["action"] == "block":
            decision_notes.append(rsi_interpretation["note"])
            pulse_signal = "HOLD"
            signal_type = "HOLD"
        elif rsi_interpretation["action"] == "boost":
            decision_notes.append(rsi_interpretation["note"])
            score += rsi_interpretation["score_adjustment"]
        # RSI boost min(score,100) clamp'inden SONRA eklendiği için skor 101-105'e
        # taşabiliyordu (canlı: pulse1 XAU conf=101/105) — burada tekrar sabitle.
        score = max(0.0, min(score, 100.0))

        # Direction filter - enforce regime allowed directions
        pulse_signal, was_filtered, filter_reason = filter_signal_by_regime(pulse_signal, regime)
        if was_filtered:
            signal_type = "HOLD"
            decision_notes.append(filter_reason)

        # ─── MERKEZİ KAPILAR (signal_gates — rapor aksiyon #2/#5/#9) ─────────
        # XAU trend-yönü SELL kapısı + seans kapısı + takvim kapısı.
        if pulse_signal in ("BUY", "SELL"):
            try:
                from services.signal_gates import apply_signal_gates
                _gated_signal, _gate_notes = await apply_signal_gates(
                    symbol, pulse_signal, "pulse1", regime=regime
                )
                if _gate_notes:
                    decision_notes.extend(_gate_notes)
                if _gated_signal != pulse_signal:
                    pulse_signal = _gated_signal
                    signal_type = "HOLD"
            except Exception as _gate_err:
                logger.warning(f"PULSE1 signal_gates skipped (fail-open): {_gate_err}")

        # ─── AI-Ops Guards (XAU/PULSE1) ───────────────────────────────────────
        # Multiple independent failure clusters surfaced by AI-Ops on
        # XAUUSD/PULSE1. Each guard is additive — checked in series with one
        # shared snapshot fetch (30s cached). Sources: GitHub issues #6, #7, #8.
        if pulse_signal == "BUY" and symbol.upper() in ("XAUUSD", "XAUUSD.FOREX"):
            try:
                from services.signal_feature_snapshot import build_signal_feature_snapshot
                snap = await build_signal_feature_snapshot(symbol)

                # Rule #XAU-PULSE1-001: SAR-against-transition guard (refined)
                # Issue #12 + clusters: 33 historical fails / 0 wins under
                # (sar_bearish + regime=transition). Earlier 2-predicate
                # version also blocked ~43 winners (precision 71%, net -1980 pip).
                # Discriminator analysis (proposal 76c75023) found two extra
                # predicates that lift precision to ~86% by leaving in the
                # volatility-breakout setups (high ATR, MACD not yet negative):
                #   - M30_macd_hist < 0   (momentum confirmation)
                #   - M30_atr_pct ≤ 0.362 (calm-tape filter; high-ATR setups
                #     are volatility breakouts that often pay)
                m30_macd_hist = snap.get("M30_macd_hist")
                m30_atr_pct = snap.get("M30_atr_pct")
                if (snap.get("sar_bearish") is True
                        and snap.get("regime_label") == "transition"
                        and m30_macd_hist is not None and m30_macd_hist < 0
                        and m30_atr_pct is not None and m30_atr_pct <= 0.362):
                    pulse_signal = "HOLD"
                    signal_type = "HOLD"
                    decision_notes.append(
                        "PULSE1 BUY blocked: SAR bearish + MACD<0 + low-ATR "
                        "during transition regime "
                        "(AI-Ops rule #XAU-PULSE1-001 — refined; "
                        "precision 86%, rescues 31/39 winners vs v1)"
                    )
                    logger.info(
                        f"[AI-Ops] PULSE1 BUY blocked on {symbol}: "
                        f"sar_bearish=True, regime=transition, "
                        f"macd_hist={m30_macd_hist}, atr_pct={m30_atr_pct}"
                    )

                # Rule #XAU-PULSE1-002: DXY-strength in transition regime guard
                # Cluster: 6 fails (#7), 0 wins. DXY strengthening (>0.2% 1d
                # change) is a structural bearish headwind for gold. Combined
                # with a 'transition' regime (no clear direction), these BUYs
                # repeatedly fail. Only block in the transition regime — in a
                # confirmed uptrend, transient DXY strength can still be bought.
                dxy_chg = snap.get("macro_dxy_chg1d_pct")
                if (pulse_signal == "BUY"   # may have just been blocked by rule 001
                        and snap.get("regime_label") == "transition"
                        and dxy_chg is not None and dxy_chg > 0.2):
                    pulse_signal = "HOLD"
                    signal_type = "HOLD"
                    decision_notes.append(
                        f"PULSE1 BUY blocked: DXY +{dxy_chg:.2f}% in transition regime "
                        f"(AI-Ops rule #XAU-PULSE1-002 — 6 historical fails, 0 wins)"
                    )
                    logger.info(
                        f"[AI-Ops] PULSE1 BUY blocked on {symbol}: "
                        f"dxy_chg1d={dxy_chg}%, regime=transition"
                    )

                # Rule #XAU-PULSE1-003: SAR-against-downtrend guard
                # Issue #14 (proposal 50c15215). The transition variant of
                # this pattern is covered by Rule #001; this rule extends
                # the block to confirmed downtrend regime, where a bearish
                # SAR + counter-trend BUY is even less defensible.
                # Re-simulation (after P/L fix) over 60d: 189 blocked
                # (136L / 53W), verdict=unanimously_better, robust
                # walk-forward (in/oos both positive), +1693 pip P/L delta.
                if (pulse_signal == "BUY"
                        and snap.get("sar_bearish") is True
                        and snap.get("regime_label") == "downtrend"):
                    pulse_signal = "HOLD"
                    signal_type = "HOLD"
                    decision_notes.append(
                        "PULSE1 BUY blocked: SAR bearish during downtrend regime "
                        "(AI-Ops rule #XAU-PULSE1-003 — verdict unanimously_better, "
                        "robust; +1693 pip / +1.93pp WR on 60d backtest)"
                    )
                    logger.info(
                        f"[AI-Ops] PULSE1 BUY blocked on {symbol}: "
                        f"sar_bearish=True, regime=downtrend (rule 003)"
                    )
            except Exception as guard_err:
                logger.warning(f"PULSE1 AI-Ops guard check failed: {guard_err}")

        # Hacim notu (iptal değil, bilgi)
        if pulse_signal in ["BUY", "SELL"] and volume_status == "low":
            decision_notes.append("Low volume - be cautious")
        
        # ─── SUGGESTION ───────────────────────────────────────────────────
        rsi_trend = "up" if rsi_14 > 50 else "down" if rsi_14 < 50 else "neutral"
        macd_trend = "up" if macd_hist > 0 else "down"
        stoch_trend = "up" if stoch_k > 50 else "down"
        
        if signal_type == "CONFIRM":
            if pulse_signal == "BUY":
                suggestion_text = f"🟢 Strong BUY signal (score: {score:.0f}). Target: {r1:.0f}, Stop: {s1:.0f}"
            else:
                suggestion_text = f"🔴 Strong SELL signal (score: {score:.0f}). Target: {s1:.0f}, Stop: {r1:.0f}"
        elif signal_type == "SCOUT":
            if pulse_signal == "BUY":
                suggestion_text = f"👀 Bullish momentum building (score: {score:.0f}). Hold above {s1:.0f}, consider if strengthens."
            elif pulse_signal == "SELL":
                suggestion_text = f"👀 Bearish momentum building (score: {score:.0f}). Hold below {r1:.0f}, consider if strengthens."
            else:
                suggestion_text = f"👀 Watch mode (score: {score:.0f}). Direction unclear."
        else:
            suggestion_text = f"⏱️ Hold mode (score: {score:.0f}). No strong trend formation."
        
        if decision_notes:
            suggestion_text += f" | Notes: {', '.join(decision_notes)}"
        
        # ─── LEARNING ENTEGRASYONU ────────────────────────────────────────
        # Log ALL BUY/SELL signals regardless of signal_type (CONFIRM/SCOUT/HOLD)
        # so Signal Performance panel tracks every directional signal from Pulse 1
        if pulse_signal in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                context = {
                    "ta": ta,
                    "source": "PULSE",
                    "score": score,
                    "signal_type": signal_type,
                    "score_details": score_details,
                    "decision_notes": decision_notes,
                    "ml_prediction": {
                        "direction": pulse_signal,
                        "confidence": round(score),
                        "entry_price": current_price,
                        "target_price": target,
                        "stop_price": stop
                    }
                }
                analysis = {
                    "final_decision": pulse_signal,
                    "confidence": round(score),
                    "model_used": "PULSE-V1-Improved"
                }
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe=timeframe,
                    strategy="PULSE",
                    model_type="pulse1",
                )
                logger.info(f"PULSE signal logged: {symbol} {pulse_signal} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE prediction: {log_err}")

        rebound_summary = None
        try:
            from services.rebound_filter_service import analyze_rebound
            rebound_summary = await analyze_rebound(symbol, timeframe=timeframe)
        except Exception as rebound_err:
            logger.warning(f"PULSE rebound integration failed: {rebound_err}")

        # ─── MACRO CONTEXT — informational decision notes ──────────────────
        # Append macro overlay commentary (DXY/VIX/Yield/Risk-On/PSI) to the
        # decision_notes for transparency. Does not change the score.
        try:
            from services.macro_context_service import commentary_lines as _macro_lines
            for _m in _macro_lines(symbol, pulse_signal, max_lines=2):
                if _m not in decision_notes:
                    decision_notes.append(f"🌍 {_m}")
        except Exception as _macro_err:
            logger.debug(f"PULSE1 macro notes skipped: {_macro_err}")

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": response_timestamp,
            "signal_timestamp": signal_timestamp,
            "signal": pulse_signal,
            "signal_type": signal_type,
            "pulse_score": round(score, 1),
            "trend": {
                "direction": trend_direction,
                "strength": round(trend_strength, 2),
                "label": f"{'UPTREND' if trend_direction == 'up' else 'DOWNTREND' if trend_direction == 'down' else 'NEUTRAL'}",
                "strength_pct": round(trend_strength * 100),
                "last_5_candles": last_10[-5:]
            },
            "price": {
                "current": round(current_price, 2),
                "change_5": round((current_price - closes[-6]) / closes[-6] * 100, 2) if len(closes) >= 6 else 0
            },
            "levels": {
                "r2": round(r2, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "s1": {"price": round(s1, 2), "distance": round(dist_s1, 1), "alert": nearest_level == "s1"},
                "s2": round(s2, 2),
                "nearest": nearest_level,
                "nearest_distance": round(nearest_distance, 1)
            },
            "momentum": {
                "rsi": {"value": round(rsi_14, 1), "trend": rsi_trend},
                "macd": {"value": round(macd_hist, 4), "trend": macd_trend},
                "stochastic": {"value": round(stoch_k, 1), "trend": stoch_trend}
            },
            "volume": {
                "status": volume_status,
                "label": "High ▲" if volume_status == "high" else "Low ▼" if volume_status == "low" else "Normal" if volume_status == "normal" else "N/A",
                "ratio": round(volume_ratio, 2),
                "available": volume_status != "unknown"
            },
            "score_breakdown": score_details,
            "decision_notes": decision_notes,
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
            },
            "suggestion": {
                "text": suggestion_text,
                "target": round(target, 2),
                "stop": round(stop, 2),
                "target_distance": round(potential_profit, 1),
                "stop_distance": round(potential_loss, 1),
                "rr_ratio": round(rr_ratio, 2),
                "timeframe_estimate": "15-30 min"
            },
            "rebound": rebound_summary
        }

        _set_cached_panel_analysis("pulse1", symbol, timeframe, payload)
        return payload
        
    except Exception as e:
        logger.error(f"PULSE analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE 2 (ML TABANLI) - GELİŞTİRİLMİŞ ML + TA HİBRİT
# Sorun düzeltmeleri:
#   - ML güveni %60 çok yüksek → %45 SCOUT / %60 CONFIRM
#   - EMA50 tek başına yetersiz → EMA20 + EMA50 + MACD üçlü onay
#   - R/R 1.0 çok düşük → 1.2 optimal
#   - İki kademeli sinyal eklendi (SCOUT/CONFIRM)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pulse-ml/{symbol}", response_model=PulseMLResponse)
async def get_pulse_ml_analysis(symbol: str, timeframe: str = "15m", refresh: bool = False):
    """
    PULSE 2 - Geliştirilmiş ML + TA Hibrit Scalp (REGIME-AWARE)
    ML modelini kullanır, EMA20+EMA50+MACD ile trend onayı yapar.
    İki kademeli: SCOUT (izle) + CONFIRM (işlem)
    
    REGIME-AWARE:
    - Trend modunda RSI>70 = momentum sinyali (sat değil)
    - ATH'de SELL bloklanır, ML confidence threshold düşer
    - Session bazlı R/R ayarı
    - Fake signal timeout koruması
    """
    try:
        cached_response = None if refresh else _get_cached_panel_analysis("pulse2", symbol, timeframe)
        if cached_response:
            return cached_response

        response_timestamp = datetime.now(timezone.utc).isoformat()
        signal_timestamp = _resolve_signal_timestamp(symbol, response_timestamp)

        from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
        from services.harmonic_pattern_service import get_pattern_adjustment
        from services.market_data_service import get_ohlcv_data
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout
        
        # ─── REGIME DETECTION ───────────────────────────────────────────
        regime = await detect_regime(symbol)
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        
        # 1. Market Data — XAUUSD fallback to 5m/30m if 1h not seeded yet
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=200)
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=200)
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=200)
        if not ohlcv or len(ohlcv) < 20:
            return {"error": "Insufficient data"}
            
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        # 2. ML Tahmini Al
        from dataclasses import asdict
        prediction_raw = await get_ml_prediction(symbol, "aggressive")
        prediction = asdict(prediction_raw) if hasattr(prediction_raw, '__dataclass_fields__') else (prediction_raw if isinstance(prediction_raw, dict) else {})
        ml_direction = prediction.get("direction", "HOLD")
        ml_confidence = prediction.get("confidence", 0)
        
        # 3. Teknik İndikatörler
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        ema_20 = ta.get("ema_20", current_price)
        ema_50 = ta.get("ema_50", current_price)
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        stoch_k = ta.get("stoch_k", 50)
        atr_val = ta.get("atr_14", current_price * 0.002)
        
        # 4. PUANLAMA SİSTEMİ (ML + TA hybrid skor) - REGIME-AWARE
        score = 0.0
        notes = []
        signal_type = "HOLD"
        signal = "HOLD"
        
        # ─── TA-ONLY DIRECTION (fallback when ML is HOLD/low conf) ─────
        # Derive direction from technical indicators alone
        ta_direction = "HOLD"
        ta_votes = 0
        if current_price > ema_20 > ema_50:
            ta_direction = "BUY"
            ta_votes += 2
        elif current_price < ema_20 < ema_50:
            ta_direction = "SELL"
            ta_votes += 2
        elif current_price > ema_20:
            ta_direction = "BUY"
            ta_votes += 1
        elif current_price < ema_20:
            ta_direction = "SELL"
            ta_votes += 1
        
        if macd_hist > 0:
            if ta_direction == "BUY": ta_votes += 1
            elif ta_direction == "HOLD": ta_direction = "BUY"; ta_votes += 1
        elif macd_hist < 0:
            if ta_direction == "SELL": ta_votes += 1
            elif ta_direction == "HOLD": ta_direction = "SELL"; ta_votes += 1
        
        if rsi_14 < 35: 
            if ta_direction != "SELL": ta_votes += 1
        elif rsi_14 > 65:
            if ta_direction != "BUY": ta_votes += 1
        
        # Use ML direction if available, else fallback to TA direction
        active_direction = ml_direction if ml_direction in ("BUY", "SELL") else ta_direction
        is_ta_fallback = ml_direction == "HOLD" and ta_direction in ("BUY", "SELL")
        if is_ta_fallback:
            notes.append(f"ML HOLD → TA analiz yönü: {ta_direction} ({ta_votes} onay)")

        shared_patterns = _extract_shared_patterns(prediction.get("active_patterns", []))
        if not shared_patterns:
            shared_patterns = (await get_pattern_adjustment(symbol, timeframe="4h")).get("patterns", [])
        pattern_context = _summarize_panel_patterns(shared_patterns, active_direction if active_direction in ("BUY", "SELL") else None)
        pattern_pts = 0
        if pattern_context.get("count", 0) > 0:
            top_pattern = pattern_context.get("top_pattern") or {}
            top_name = top_pattern.get("name_tr") or top_pattern.get("name") or "Pattern"
            if pattern_context.get("aligned_count", 0) > 0 and pattern_context.get("opposing_count", 0) == 0:
                # Yön kapısı — bkz. signal_gates.pattern_bonus_allowed
                # (formasyon SELL canlı ölçümde %22.6, n=115, p≈3e-9).
                from services.signal_gates import pattern_bonus_allowed
                if pattern_bonus_allowed(symbol, active_direction):
                    pattern_pts = 10 if str(top_pattern.get("category") or "").lower() == "harmonic" else 6
                    notes.append(f"4H pattern confirms bias: {top_name}")
                else:
                    notes.append(f"4H pattern confirmation withheld ({top_name}): "
                                 f"detector loses in this direction (live measurement)")
            elif pattern_context.get("preferred_direction") in {"BUY", "SELL"} and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
                notes.append(f"4H pattern opposes bias: {top_name}")
            else:
                notes.append(f"4H pattern detected: {top_name}")
        
        # ─── ML Güven Puanı (40 puan max) ────────────────────────────────
        ml_pts = 0
        ml_confirm_floor = 50.0  # 55'ten 50'ye düşürüldü
        ml_scout_floor = 45.0    # 52'den 45'e düşürüldü
        
        if regime.regime == "STRONG_TREND_UP" and regime.is_ath_zone:
            ml_confirm_floor = 42.0  # 48'den düşürüldü
            ml_scout_floor = 38.0    # 42'den düşürüldü
            notes.append("ATH modu: ML threshold düşürüldü")
        elif regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            ml_confirm_floor = 45.0  # 50'den düşürüldü
            ml_scout_floor = 40.0    # 45'ten düşürüldü
        
        if ml_direction in ("BUY", "SELL"):
            if ml_confidence >= 70:
                ml_pts = 40
            elif ml_confidence >= 60:
                ml_pts = 30
            elif ml_confidence >= ml_scout_floor:
                ml_pts = 20
            else:
                ml_pts = 10  # ML has a direction but low confidence
                notes.append(f"ML yön var ({ml_direction}) ama güven düşük ({ml_confidence:.1f}%)")
        else:
            # ML gave HOLD — give partial credit if TA fallback aligns with regime
            if is_ta_fallback and ta_votes >= 2:
                ml_pts = 15  # TA consensus replaces ML
                notes.append("TA konsensüs ML yerine geçti")
            elif is_ta_fallback:
                ml_pts = 8
            else:
                ml_pts = 0
                notes.append(f"ML HOLD, TA belirsiz")
        score += ml_pts
        
        # ─── EMA Trend Onayı (25 puan max) ──────────────────────────────
        ema_pts = 0
        ema_status = "neutral"
        
        if active_direction == "BUY":
            if current_price > ema_20 > ema_50:
                ema_pts = 25
                ema_status = "strong_confirm"
            elif current_price > ema_20:
                ema_pts = 15
                ema_status = "confirm"
            elif current_price > ema_50:
                ema_pts = 8
                ema_status = "weak"
                if regime.regime == "STRONG_TREND_UP":
                    ema_pts = 15
                    ema_status = "pullback_opportunity"
                    notes.append("Trend pullback: EMA20 retest, dip alım fırsatı")
                else:
                    notes.append("Fiyat EMA20 altında, temkinli ol")
            else:
                ema_pts = 0
                ema_status = "against"
                if regime.regime == "STRONG_TREND_UP":
                    ema_pts = 5
                    ema_status = "deep_pullback"
                    notes.append("Derin pullback: EMA50 altında ama trend yukarı")
                else:
                    notes.append("Trend (EMA) yönü desteklemiyor")
        elif active_direction == "SELL":
            if current_price < ema_20 < ema_50:
                ema_pts = 25
                ema_status = "strong_confirm"
            elif current_price < ema_20:
                ema_pts = 15
                ema_status = "confirm"
            elif current_price < ema_50:
                ema_pts = 8
                ema_status = "weak"
                if regime.regime == "STRONG_TREND_DOWN":
                    ema_pts = 15
                    ema_status = "pullback_opportunity"
                    notes.append("Trend pullback: EMA20 retest, ralli satış fırsatı")
                else:
                    notes.append("Fiyat EMA20 üstünde, temkinli ol")
            else:
                ema_pts = 0
                ema_status = "against"
                if regime.regime == "STRONG_TREND_DOWN":
                    ema_pts = 5
                    ema_status = "deep_pullback"
                    notes.append("Derin pullback: EMA50 üstünde ama trend aşağı")
                else:
                    notes.append("Trend (EMA) yönü desteklemiyor")
        score += ema_pts
        
        # ─── MACD Momentum Onayı (15 puan max) ──────────────────────────
        macd_pts = 0
        if active_direction == "BUY" and macd_hist > 0:
            macd_pts = 15
        elif active_direction == "SELL" and macd_hist < 0:
            macd_pts = 15
        elif abs(macd_hist) < 0.01:
            macd_pts = 5
        else:
            if regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
                macd_pts = 3
                notes.append("MACD gecikmeli, trend güçlü devam ediyor")
            else:
                notes.append("MACD yönü desteklemiyor")
        score += macd_pts
        
        # ─── RSI Filtresi (10 puan max) - REGIME-AWARE ──────────────────
        rsi_pts = 0
        rsi_interpretation = interpret_rsi(rsi_14, regime, active_direction)
        
        if rsi_interpretation["action"] == "boost":
            rsi_pts = 10 + rsi_interpretation["score_adjustment"]
            notes.append(rsi_interpretation["note"])
        elif rsi_interpretation["action"] == "caution":
            rsi_pts = 0
            notes.append(rsi_interpretation["note"])
        elif rsi_interpretation["action"] == "neutral":
            if active_direction in ("BUY", "SELL"):
                if regime.rsi_oversold < rsi_14 < regime.rsi_overbought:
                    rsi_pts = 10
                else:
                    rsi_pts = 3
        score += max(0, rsi_pts)
        
        # ─── Hacim Onayı (10 puan max) ───────────────────────────────────
        # NOT: Son mum tam kapanmamış olabilir (hacim=0), bu yüzden son 4 TAM mumu kullan
        vol_pts = 0
        # Son 5 mumdan 0 olmayanları al (son mum hariç)
        recent_volumes = [v for v in volumes[-5:-1] if v > 0] if len(volumes) >= 5 else [v for v in volumes if v > 0]
        
        if len(recent_volumes) >= 2:
            vol_avg = float(np.mean(recent_volumes))
            vol_current = float(recent_volumes[-1])  # Son tam mum
            vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
            if vol_ratio >= 1.2:
                vol_pts = 10
            elif vol_ratio >= 0.9:
                vol_pts = 5
            else:
                notes.append("Düşük hacim")
        score += vol_pts
        score += pattern_pts
        
        # ─── SİNYAL BELİRLEME (İki kademe) - REGIME-AWARE ──────────────
        # For TA fallback mode, use lower thresholds (TA has already proven direction)
        confirm_threshold = 56 if is_ta_fallback else 56  # 56'ya düşürüldü
        scout_threshold = 35 if is_ta_fallback else 35    # 40'tan 35'e düşürüldü
        conf_floor = ml_scout_floor if is_ta_fallback else ml_confirm_floor
        scout_conf_floor = 0 if is_ta_fallback else ml_scout_floor  # No ML floor needed for TA fallback
        
        if score >= confirm_threshold and (ml_confidence >= conf_floor or is_ta_fallback):
            signal_type = "CONFIRM"
            signal = active_direction
        elif score >= scout_threshold and (ml_confidence >= scout_conf_floor or is_ta_fallback):
            signal_type = "SCOUT"
            signal = active_direction
        else:
            signal_type = "HOLD"
            signal = "HOLD"

        if pattern_context.get("count", 0) > 0 and pattern_context.get("preferred_direction") in {"BUY", "SELL"} and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"
            elif signal_type == "SCOUT":
                signal_type = "HOLD"
                signal = "HOLD"
        score = min(score, 100)
        
        # ─── DIRECTION FILTER (enforce regime rules) ────────────────────
        signal, was_filtered, filter_reason = filter_signal_by_regime(signal, regime)
        if was_filtered:
            signal_type = "HOLD"
            notes.append(filter_reason)

        # ─── MERKEZİ KAPILAR (signal_gates — rapor aksiyon #2/#5/#9) ────
        if signal in ("BUY", "SELL"):
            try:
                from services.signal_gates import apply_signal_gates
                _gated_signal, _gate_notes = await apply_signal_gates(
                    symbol, signal, "pulse2", regime=regime
                )
                if _gate_notes:
                    notes.extend(_gate_notes)
                if _gated_signal != signal:
                    signal = _gated_signal
                    signal_type = "HOLD"
            except Exception as _gate_err:
                logger.warning(f"PULSE2 signal_gates skipped (fail-open): {_gate_err}")

        # ─── Hedef / Stop (SCALPING distances — instrument-specific) ────
        atr_val = ta.get("atr_14", current_price * 0.002)
        target, stop, _, _ = _scalp_tp_sl(symbol, current_price, signal, atr_val)
        
        # ─── R/R Kontrolü (regime-dynamic minimum) ──────────────────────
        min_rr = regime.min_rr
        rr_ratio = 0
        if signal != "HOLD" and target and stop:
            profit = abs(target - current_price)
            risk = abs(current_price - stop)
            rr_ratio = profit / risk if risk > 0 else 0
            
            if rr_ratio < min_rr:
                if signal_type == "CONFIRM":
                    signal_type = "SCOUT"
                    notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr}), downgraded to SCOUT")
                else:
                    signal = "HOLD"
                    signal_type = "HOLD"
                    notes.append(f"R/R too low ({rr_ratio:.2f} < {min_rr})")
        
        # ─── FAKE SIGNAL TIMEOUT (reduce to SCOUT if in timeout) ────────
        if is_timed_out and signal_type == "CONFIRM" and ml_confidence < 75:
            signal_type = "SCOUT"
            notes.append(f"Timeout aktif: CONFIRM→SCOUT (ML<75%)")
            
        # ─── SUGGESTION ──────────────────────────────────────────────────
        regime_tag = f" [{regime.regime}]" if regime.regime != "TRANSITION" else ""
        if signal_type == "CONFIRM":
            suggestion = f"🟢 ML confirmed {'BUY' if signal == 'BUY' else 'SELL'} signal{regime_tag} (score: {score:.0f}, ML: {ml_confidence:.0f}%)"
        elif signal_type == "SCOUT":
            suggestion = f"👀 ML watch mode{regime_tag} (score: {score:.0f}). Consider if strengthens."
        else:
            suggestion = f"⏱️ Hold{regime_tag}. ML score: {score:.0f}/100"
        
        if notes:
            suggestion += f" | Notes: {', '.join(notes)}"
        
        # ─── LEARNING ENTEGRASYONU ────────────────────────────────────────
        # Log ALL BUY/SELL signals (not just CONFIRM/SCOUT/HOLD)
        # so Signal Performance panel tracks every directional signal from Pulse 1
        if signal in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                # Pulse2'nin kanaati hibrit `score`tur; eskiden ham ml_confidence
                # loglanıyordu → ML HOLD + TA-fallback sinyallerinde conf=0 satırlar
                # (14g XAU'da 336 adet) WR istatistiklerini kirletiyordu.
                pulse2_conf = round(max(0.0, min(float(score), 100.0)), 1)
                await log_prediction(
                    symbol=symbol,
                    context={
                        "source": "PULSE_ML",
                        "ta": ta,
                        "score": score,
                        "signal_type": signal_type,
                        "ml_raw_confidence": round(float(ml_confidence), 1),
                        "ml_prediction": {
                            "direction": signal,
                            "confidence": pulse2_conf,
                            "entry_price": current_price,
                            "target_price": target,
                            "stop_price": stop,
                        }
                    },
                    analysis={"final_decision": signal, "confidence": pulse2_conf, "model_used": "PULSE-ML-V2"},
                    timeframe=timeframe,
                    strategy="PULSE_ML",
                    model_type="pulse2",
                )
                logger.info(f"PULSE-ML signal logged: {symbol} {signal} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE-ML prediction: {log_err}")

        # ─── MACRO CONTEXT — informational notes ──────────────────────────
        try:
            from services.macro_context_service import commentary_lines as _macro_lines
            for _m in _macro_lines(symbol, signal, max_lines=2):
                if _m not in notes:
                    notes.append(f"🌍 {_m}")
        except Exception as _macro_err:
            logger.debug(f"PULSE2 macro notes skipped: {_macro_err}")

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": response_timestamp,
            "signal_timestamp": signal_timestamp,
            "signal": signal,
            "signal_type": signal_type,
            "pulse_score": round(score, 1),
            # Panelin (ve meta motorunun) okuduğu kanaat = hibrit skor.
            # Ham ML güveni score_breakdown.ml.confidence içinde duruyor.
            "confidence": round(max(0.0, min(float(score), 100.0)), 1),
            "model_type": "PULSE_ML_V2",
            "price": current_price,
            "target": round(target, 2) if target else 0,
            "stop": round(stop, 2) if stop else 0,
            "rr_ratio": round(rr_ratio, 2),
            "score_breakdown": {
                "ml": {"pts": ml_pts, "confidence": round(ml_confidence, 1), "direction": ml_direction},
                "ema": {"pts": ema_pts, "status": ema_status, "ema20": round(ema_20, 2), "ema50": round(ema_50, 2)},
                "macd": {"pts": macd_pts, "hist": round(macd_hist, 4)},
                "rsi": {"pts": rsi_pts, "value": round(rsi_14, 1)},
                "volume": {"pts": vol_pts}
            },
            "details": {
                "ml_direction": ml_direction,
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "rsi_14": round(rsi_14, 1),
                "macd_hist": round(macd_hist, 4),
                "notes": notes
            },
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
                "ml_confirm_floor": ml_confirm_floor,
                "ml_scout_floor": ml_scout_floor,
            },
            "suggestion": suggestion,
        }
        _set_cached_panel_analysis("pulse2", symbol, timeframe, payload)
        return payload
            
    except Exception as e:
        logger.error(f"PULSE-ML analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE 3 (HYBRID SCALP) - 3 ZAMANLI, 3 FİLTRELİ, HIZLI KARAR
# Konsept: Hem hızlı olsun, hem güvenilir, hem sık sinyal versin
#   - 5m: Anlık momentum (%50 ağırlık)
#   - 1H: Kısa trend (%30 ağırlık)
#   - 4H: Ana trend yönü (%20 ağırlık)
#   - İki kademe: SCOUT (zayıf-sık) + CONFIRM (güçlü-az)
#   - R/R minimum 1.2
#   - Cache sistemi ile hız optimizasyonu
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory cache for PULSE 3 speed
_pulse3_cache: Dict[str, Any] = {}

def _cache_get(key: str, max_age_seconds: int) -> Any:
    """Get from cache if not expired"""
    if key in _pulse3_cache:
        data, ts = _pulse3_cache[key]
        if (datetime.now(timezone.utc) - ts).total_seconds() < max_age_seconds:
            return data
    return None

def _cache_set(key: str, data: Any):
    """Store in cache with timestamp"""
    _pulse3_cache[key] = (data, datetime.now(timezone.utc))


async def _fetch_tf_data(symbol: str, tf: str, limit: int, cache_seconds: int):
    """Fetch OHLCV data with caching. Falls back to EOD daily for symbols without intraday (e.g. XAUUSD)."""
    cache_key = f"p3_{symbol}_{tf}"
    cached = _cache_get(cache_key, cache_seconds)
    if cached is not None:
        return cached
    
    from services.market_data_service import get_ohlcv_data
    ohlcv = await get_ohlcv_data(symbol, tf, limit=limit)
    if ohlcv:
        _cache_set(cache_key, ohlcv)
        return ohlcv
    
    # Fallback: use EOD daily data for symbols without intraday support (e.g. XAUUSD)
    logger.warning(f"No intraday {tf} data for {symbol}, falling back to EOD daily")
    ohlcv = await get_ohlcv_data(symbol, "1d", limit=limit)
    if ohlcv:
        _cache_set(cache_key, ohlcv)
    return ohlcv


def _analyze_5m(closes, highs, lows, volumes, ta) -> Dict:
    """5 dakikalık analiz - 50 puan üzerinden"""
    score = 0.0
    details = {}
    
    if len(closes) < 10:
        return {"score": 25.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    # 1. Son 5 mum yönü (15 puan)
    last_5_dirs = []
    for i in range(-5, 0):
        if closes[i] > closes[i-1]:
            last_5_dirs.append("up")
        elif closes[i] < closes[i-1]:
            last_5_dirs.append("down")
        else:
            last_5_dirs.append("neutral")
    
    bullish = last_5_dirs.count("up")
    bearish = last_5_dirs.count("down")
    
    candle_pts = 0
    if bullish >= 4:
        candle_pts = 15
    elif bullish == 3:
        candle_pts = 5
    elif bearish >= 4:
        candle_pts = 15
    elif bearish == 3:
        candle_pts = 5
    score += candle_pts
    details["candles"] = {"up": bullish, "down": bearish, "bias": "up" if bullish > bearish else "down" if bearish > bullish else "neutral", "pts": candle_pts}
    
    # 2. EMA Stack: SMA5 > SMA10 > EMA20 (20 puan)
    sma5 = float(np.mean(closes[-5:])) if len(closes) >= 5 else float(closes[-1])
    sma10 = float(np.mean(closes[-10:])) if len(closes) >= 10 else float(closes[-1])
    ema20 = ta.get("ema_20", float(closes[-1]))
    
    ema_pts = 0
    if sma5 > sma10 > ema20:
        ema_pts = 20
        ema_dir = "bullish"
    elif sma5 > sma10:
        ema_pts = 10
        ema_dir = "weak_bullish"
    elif sma5 < sma10 < ema20:
        ema_pts = 20
        ema_dir = "bearish"
    elif sma5 < sma10:
        ema_pts = 10
        ema_dir = "weak_bearish"
    else:
        ema_dir = "neutral"
    score += ema_pts
    details["ema_stack"] = {"sma5": round(sma5, 2), "sma10": round(sma10, 2), "ema20": round(ema20, 2), "dir": ema_dir, "pts": ema_pts}
    
    # 3. Hacim artışı (10 puan)
    # NOT: Son mum tam kapanmamış olabilir (hacim=0), bu yüzden son 4 TAM mumu kullan
    vol_pts = 0
    # Son 5 mumdan 0 olmayanları al (son mum hariç)
    recent_volumes = [v for v in volumes[-5:-1] if v > 0] if len(volumes) >= 5 else [v for v in volumes if v > 0]
    
    if len(recent_volumes) >= 2:
        vol_avg = float(np.mean(recent_volumes))
        vol_last = float(recent_volumes[-1])  # Son tam mum
        vol_ratio = vol_last / vol_avg if vol_avg > 0 else 1
        if vol_ratio >= 1.3:
            vol_pts = 10
        elif vol_ratio >= 1.1:
            vol_pts = 5
    score += vol_pts
    details["volume"] = {"pts": vol_pts}
    
    # 4. RSI hızlı (5 puan) - 40-60 neutral = trend gücü
    rsi = ta.get("rsi_7", ta.get("rsi_14", 50))
    rsi_pts = 0
    if 40 <= rsi <= 60:
        rsi_pts = 5
    elif rsi > 70 or rsi < 30:
        rsi_pts = -5  # Aşırı bölge riski
    score += rsi_pts
    details["rsi"] = {"value": round(rsi, 1), "pts": rsi_pts}
    
    # Normalize to 0-50
    score = max(0, min(50, score))
    
    # Trend yönü
    if bullish > bearish and ema_dir in ["bullish", "weak_bullish"]:
        trend = "up"
    elif bearish > bullish and ema_dir in ["bearish", "weak_bearish"]:
        trend = "down"
    else:
        trend = "neutral"
    
    return {"score": round(score, 1), "trend": trend, "details": details}


def _analyze_1h(closes, ta) -> Dict:
    """1 saatlik analiz - 30 puan üzerinden"""
    if len(closes) < 20:
        return {"score": 15.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    score = 0.0
    details = {}
    current = float(closes[-1])
    
    # 1. EMA50 pozisyonu (15 puan)
    ema50 = ta.get("ema_50", current)
    ema_pts = 0
    if current > ema50 * 1.005:  # %0.5 üzerinde
        ema_pts = 15
        ema_dir = "above"
    elif current > ema50:
        ema_pts = 10
        ema_dir = "slightly_above"
    elif current < ema50 * 0.995:
        ema_pts = 15
        ema_dir = "below"
    elif current < ema50:
        ema_pts = 10
        ema_dir = "slightly_below"
    else:
        ema_dir = "at"
    score += ema_pts
    details["ema50"] = {"value": round(ema50, 2), "dir": ema_dir, "pts": ema_pts}
    
    # 2. MACD Histogram yönü (10 puan)
    macd_hist = ta.get("macd_hist", 0)
    macd_pts = 0
    if macd_hist > 0:
        macd_pts = 10
        macd_dir = "bullish"
    elif macd_hist < 0:
        macd_pts = 10
        macd_dir = "bearish"
    else:
        macd_dir = "neutral"
    score += macd_pts
    details["macd"] = {"hist": round(macd_hist, 4), "dir": macd_dir, "pts": macd_pts}
    
    # 3. Son 20 mum performans (5 puan)
    # 2026-07-01 (rapor aksiyon #4): sabit %1 eşiği ATR-normalize edildi —
    # düşük volatilitede %1 ulaşılmaz, yüksek volatilitede önemsizdir.
    perf_pts = 0
    if len(closes) >= 20:
        change = (closes[-1] - closes[-20]) / closes[-20]
        _atr_pct = ta.get("atr_pct")
        if _atr_pct:
            _th_perf = max(1.5 * float(_atr_pct) / 100.0, 0.005)
        else:
            _th_perf = 0.01  # fallback: eski sabit eşik
        if abs(change) > _th_perf:
            perf_pts = 5
    score += perf_pts
    details["performance"] = {"pts": perf_pts}
    
    score = max(0, min(30, score))
    
    if current > ema50 and macd_dir == "bullish":
        trend = "up"
    elif current < ema50 and macd_dir == "bearish":
        trend = "down"
    else:
        trend = "neutral"
    
    return {"score": round(score, 1), "trend": trend, "details": details}


def _analyze_4h(closes, ta) -> Dict:
    """4 saatlik analiz - 20 puan üzerinden"""
    if len(closes) < 10:
        return {"score": 10.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    score = 0.0
    details = {}
    current = float(closes[-1])
    
    # Son 10 mumun genel yönü
    first = float(closes[-10])
    change = (current - first) / first

    # 2026-07-01 (rapor aksiyon #4): sabit %2/%1/%0.3 eşikleri ATR-normalize
    # edildi. 10 barlık hareket 4H ATR%'sine oranla ölçeklenir; ATR verisi
    # yoksa eski sabitlere düşülür. Böylece altın gibi yüksek volatilite
    # enstrümanlarında eşikler otomatik genişler, sakin dönemde daralır.
    _atr_pct = ta.get("atr_pct")
    if _atr_pct:
        _atr_frac = float(_atr_pct) / 100.0
        _th_strong = max(3.0 * _atr_frac, 0.008)
        _th_mid = max(1.5 * _atr_frac, 0.004)
        _th_weak = max(0.5 * _atr_frac, 0.0015)
    else:
        _th_strong, _th_mid, _th_weak = 0.02, 0.01, 0.003

    change_pts = 0
    if change > _th_strong:
        change_pts = 15
        trend = "up"
    elif change > _th_mid:
        change_pts = 10
        trend = "up"
    elif change > _th_weak:
        change_pts = 5
        trend = "up"
    elif change < -_th_strong:
        change_pts = 15
        trend = "down"
    elif change < -_th_mid:
        change_pts = 10
        trend = "down"
    elif change < -_th_weak:
        change_pts = 5
        trend = "down"
    else:
        trend = "neutral"
    score += change_pts
    details["change"] = {"pct": round(change * 100, 2), "pts": change_pts, "atr_normalized": bool(_atr_pct)}
    
    # EMA20 ek kontrol (5 puan)
    ema20 = ta.get("ema_20", current)
    ema_pts = 0
    if current > ema20 and trend in ["up", "neutral"]:
        ema_pts = 5
    elif current < ema20 and trend in ["down", "neutral"]:
        ema_pts = 5
    score += ema_pts
    details["ema20"] = {"value": round(ema20, 2), "pts": ema_pts}
    
    score = max(0, min(20, score))
    
    return {"score": round(score, 1), "trend": trend, "details": details}


@router.get("/pulse-v3/{symbol}", response_model=PulseV3Response)
async def get_pulse_v3_analysis(symbol: str, refresh: bool = False):
    """
    PULSE 3 - Hybrid Scalp: 3 Zamanlı, 3 Filtreli, Hızlı Karar (REGIME-AWARE)
    
    Zaman Dilimleri: 5m(%50) + 1H(%30) + 4H(%20) (Base timeframe is dynamic)
    Sinyal Tipleri: SCOUT (40-65) / CONFIRM (65+) / HOLD (<40)
    """
    try:
        cached_response = None if refresh else _get_cached_panel_analysis("pulse3", symbol, "5m")
        if cached_response:
            return cached_response

        response_timestamp = datetime.now(timezone.utc).isoformat()
        signal_timestamp = _resolve_signal_timestamp(symbol, response_timestamp)

        from services.ml_prediction_service import _compute_technical_indicators
        from services.harmonic_pattern_service import detect_chart_patterns_from_candles
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout, detect_order_blocks
        from services.rebound_filter_service import analyze_rebound
        import asyncio
        
        # ─── REGIME DETECTION ───────────────────────────────────────────
        regime = await detect_regime(symbol)
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        
        # ─── PARALEL VERİ ÇEKME (Cache'li) ───────────────────────────────
        data_base, data_1h, data_4h = await asyncio.gather(
            _fetch_tf_data(symbol, "5m", limit=50, cache_seconds=30),
            _fetch_tf_data(symbol, "1H", limit=60, cache_seconds=300),
            _fetch_tf_data(symbol, "4H", limit=30, cache_seconds=600)
        )
        
        if not data_base or len(data_base) < 15:
            return {"error": f"Insufficient 5m data for this symbol.", "error_key": "pulse.insufficientData"}
        
        # Convert base data
        c5 = np.array([c["close"] for c in data_base], dtype=np.float64)
        h5 = np.array([c["high"] for c in data_base], dtype=np.float64)
        l5 = np.array([c["low"] for c in data_base], dtype=np.float64)
        v5 = np.array([c.get("volume", 0) for c in data_base], dtype=np.float64)
        # Use live price from DataHub (updated every 30s)
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(c5[-1])
        ta_5m = _compute_technical_indicators(c5, h5, l5, v5)
        
        # Convert 1H data
        ta_1h = {}
        if data_1h and len(data_1h) >= 20:
            c1h = np.array([c["close"] for c in data_1h], dtype=np.float64)
            h1h = np.array([c["high"] for c in data_1h], dtype=np.float64)
            l1h = np.array([c["low"] for c in data_1h], dtype=np.float64)
            v1h = np.array([c.get("volume", 0) for c in data_1h], dtype=np.float64)
            ta_1h = _compute_technical_indicators(c1h, h1h, l1h, v1h)
        else:
            c1h = c5  # Fallback
        
        # Convert 4H data
        ta_4h = {}
        if data_4h and len(data_4h) >= 10:
            c4h = np.array([c["close"] for c in data_4h], dtype=np.float64)
            h4h = np.array([c["high"] for c in data_4h], dtype=np.float64)
            l4h = np.array([c["low"] for c in data_4h], dtype=np.float64)
            v4h = np.array([c.get("volume", 0) for c in data_4h], dtype=np.float64)
            ta_4h = _compute_technical_indicators(c4h, h4h, l4h, v4h)
        else:
            c4h = c5  # Fallback
        
        # ─── 3 ZAMANLI ANALİZ ────────────────────────────────────────────
        result_5m = _analyze_5m(c5, h5, l5, v5, ta_5m)
        result_1h = _analyze_1h(c1h, ta_1h)
        result_4h = _analyze_4h(c4h, ta_4h)

        # Ağırlıklı toplam skor — REGIME-AWARE (2026-07-01, rapor aksiyon #4)
        # Eski sabit dağılım (5m %50 / 1H %30 / 4H %20) trend ortamında 5m
        # gürültüsünün 4H trendini ezmesine yol açıyordu (XAU SELL WR %19.7).
        # Trend/ATH: 4H %40 / 1H %35 / 5m %25; TRANSITION: 35/35/30;
        # RANGING: eski dağılım korunur. PULSE3_REGIME_WEIGHTS=0 → eski davranış.
        import os as _os
        if _os.getenv("PULSE3_REGIME_WEIGHTS", "1") != "0" and (
            regime.regime in ("STRONG_TREND_UP", "STRONG_TREND_DOWN") or regime.is_ath_zone
        ):
            _w5, _w1h, _w4h = 25.0, 35.0, 40.0
        elif _os.getenv("PULSE3_REGIME_WEIGHTS", "1") != "0" and regime.regime == "TRANSITION":
            _w5, _w1h, _w4h = 30.0, 35.0, 35.0
        else:
            _w5, _w1h, _w4h = 50.0, 30.0, 20.0
        total_score = (
            (result_5m["score"] / 50.0) * _w5
            + (result_1h["score"] / 30.0) * _w1h
            + (result_4h["score"] / 20.0) * _w4h
        )
        # Max: 100 (normalize edilmiş alt skorların ağırlıklı toplamı)
        
        # ─── YÖN BELİRLEME (regime-biased) ──────────────────────────────
        up_votes = sum(1 for r in [result_5m, result_1h, result_4h] if r["trend"] == "up")
        down_votes = sum(1 for r in [result_5m, result_1h, result_4h] if r["trend"] == "down")
        
        # Regime bias: in strong trend, bias toward trend direction
        if regime.regime == "STRONG_TREND_UP" and up_votes >= 1:
            direction = "BUY"  # 1 vote enough in strong uptrend
        elif regime.regime == "STRONG_TREND_DOWN" and down_votes >= 1:
            direction = "SELL"
        elif up_votes >= 2:
            direction = "BUY"
        elif down_votes >= 2:
            direction = "SELL"
        elif result_5m["trend"] != "neutral":
            direction = "BUY" if result_5m["trend"] == "up" else "SELL"
        else:
            direction = "NEUTRAL"

        pattern_context = _summarize_panel_patterns(
            detect_chart_patterns_from_candles(data_4h or [], timeframe="4h").get("patterns", []),
            direction if direction in ("BUY", "SELL") else None,
        )
        if pattern_context.get("count", 0) > 0:
            top_pattern = pattern_context.get("top_pattern") or {}
            top_name = top_pattern.get("name_tr") or top_pattern.get("name") or "Pattern"
            if pattern_context.get("aligned_count", 0) > 0 and pattern_context.get("opposing_count", 0) == 0:
                # Yön kapısı (2026-07-26) — shadow tracker: formasyon SELL %22.6
                # (n=115), NDX BUY %9.1 (n=22). Kaybeden yönde bonus verilmez.
                from services.signal_gates import pattern_bonus_allowed
                if pattern_bonus_allowed(symbol, direction):
                    total_score += 10 if str(top_pattern.get("category") or "").lower() == "harmonic" else 6
                    notes = [f"4H pattern confirms bias: {top_name}"]
                else:
                    notes = [f"4H pattern onayı sayılmadı ({top_name}): dedektör bu "
                             f"yönde canlı ölçümde kaybediyor"]
            elif pattern_context.get("preferred_direction") in {"BUY", "SELL"} and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
                notes = [f"4H pattern opposes bias: {top_name}"]
            else:
                notes = [f"4H pattern detected: {top_name}"]
        else:
            notes = []
        
        # ─── SİNYAL TİPİ ────────────────────────────────────────────────
        if total_score >= 56:  # 56'ya düşürüldü
            signal_type = "CONFIRM"
        elif total_score >= 35:  # 40'tan 35'e
            signal_type = "SCOUT"
        else:
            signal_type = "HOLD"
            direction = "NEUTRAL"
        
        # ─── DIRECTION FILTER (enforce regime rules) ────────────────────
        direction, was_filtered, filter_reason = filter_signal_by_regime(direction, regime)
        if was_filtered:
            signal_type = "HOLD"
            notes.append(filter_reason)

        # ─── MERKEZİ KAPILAR (signal_gates — rapor aksiyon #2/#5/#9) ────
        if direction in ("BUY", "SELL"):
            try:
                from services.signal_gates import apply_signal_gates
                _gated_dir, _gate_notes = await apply_signal_gates(
                    symbol, direction, "pulse3", regime=regime
                )
                if _gate_notes:
                    notes.extend(_gate_notes)
                if _gated_dir != direction:
                    direction = "NEUTRAL"
                    signal_type = "HOLD"
            except Exception as _gate_err:
                logger.warning(f"PULSE3 signal_gates skipped (fail-open): {_gate_err}")

        if pattern_context.get("count", 0) > 0 and pattern_context.get("preferred_direction") in {"BUY", "SELL"} and pattern_context.get("opposing_count", 0) > pattern_context.get("aligned_count", 0):
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"
            elif signal_type == "SCOUT":
                signal_type = "HOLD"
                direction = "NEUTRAL"
        total_score = min(total_score, 100)
        
        # ─── ORDER BLOCK DETECTION (4H) ─────────────────────────────────
        order_blocks_data = []
        ob_entry_zone = None
        if data_4h and len(data_4h) >= 20:
            o4h = np.array([c["open"] for c in data_4h], dtype=np.float64)
            h4h_arr = np.array([c["high"] for c in data_4h], dtype=np.float64)
            l4h_arr = np.array([c["low"] for c in data_4h], dtype=np.float64)
            c4h_arr = np.array([c["close"] for c in data_4h], dtype=np.float64)
            v4h_arr = np.array([c.get("volume", 0) for c in data_4h], dtype=np.float64)
            
            obs = detect_order_blocks(o4h, h4h_arr, l4h_arr, c4h_arr, v4h_arr, lookback=20)
            
            for ob in obs:
                ob_dict = {
                    "type": ob.type, "low": round(ob.low, 2), "high": round(ob.high, 2),
                    "strength": ob.strength,
                    "is_nearby": abs(current_price - (ob.low + ob.high) / 2) / current_price < 0.02
                }
                order_blocks_data.append(ob_dict)
                
                # In trend mode, if price is at a bullish OB = strong buy zone
                if regime.regime == "STRONG_TREND_UP" and ob.type == "bullish" and ob_dict["is_nearby"]:
                    if current_price >= ob.low and current_price <= ob.high * 1.005:
                        ob_entry_zone = ob
                        if signal_type == "SCOUT":
                            signal_type = "CONFIRM"
                            notes.append(f"Order Block onayı: Fiyat bullish OB'de ({ob.low:.0f}-{ob.high:.0f})")
                elif regime.regime == "STRONG_TREND_DOWN" and ob.type == "bearish" and ob_dict["is_nearby"]:
                    if current_price <= ob.high and current_price >= ob.low * 0.995:
                        ob_entry_zone = ob
                        if signal_type == "SCOUT":
                            signal_type = "CONFIRM"
                            notes.append(f"Order Block onayı: Fiyat bearish OB'de ({ob.low:.0f}-{ob.high:.0f})")
        
        # ─── SEVİYELER (5m verilerinden) ─────────────────────────────────
        high_20 = float(np.max(h5[-20:])) if len(h5) >= 20 else float(np.max(h5))
        low_20 = float(np.min(l5[-20:])) if len(l5) >= 20 else float(np.min(l5))
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        r2 = pivot + (high_20 - low_20)
        s1 = 2 * pivot - high_20
        s2 = pivot - (high_20 - low_20)
        
        # Hedef/Stop — SCALPING distances (instrument-specific)
        atr_val = ta_5m.get("atr_14", abs(high_20 - low_20) / 20)
        target, stop, potential_profit, potential_loss = _scalp_tp_sl(symbol, current_price, direction, atr_val)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # ─── R/R FİLTRE (regime-dynamic) ─────────────────────────────────
        min_rr = regime.min_rr
        if signal_type == "CONFIRM" and rr_ratio < min_rr:
            signal_type = "SCOUT"
            notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr}), downgraded to SCOUT")
        elif signal_type == "SCOUT" and rr_ratio < 1.0:
            signal_type = "HOLD"
            direction = "NEUTRAL"
            notes.append(f"R/R too low ({rr_ratio:.2f})")
        
        # Timeframe conflict note
        if up_votes == 1 and down_votes == 1:
            notes.append("Timeframes conflicting")
        
        # ─── FAKE SIGNAL TIMEOUT ────────────────────────────────────────
        if is_timed_out and signal_type == "CONFIRM":
            signal_type = "SCOUT"
            notes.append(f"Timeout aktif: CONFIRM→SCOUT")
        
        # ─── RSI REGIME CHECK ───────────────────────────────────────────
        rsi_5m = ta_5m.get("rsi_14", 50)
        rsi_check = interpret_rsi(rsi_5m, regime, direction)
        if rsi_check["action"] == "boost":
            total_score += rsi_check["score_adjustment"]
            notes.append(rsi_check["note"])
        elif rsi_check["action"] == "caution" and signal_type == "CONFIRM":
            signal_type = "SCOUT"
            notes.append(rsi_check["note"])
        # RSI boost sonrası skor 100'ü aşabiliyordu (canlı: pulse3 NDX conf=105,
        # loglanan confidence clamp'siz round(total_score) idi) — sabitle.
        total_score = max(0.0, min(total_score, 100.0))
        
        # ─── SUGGESTION ──────────────────────────────────────────────────
        regime_tag = f" [{regime.regime}]" if regime.regime != "TRANSITION" else ""
        if signal_type == "CONFIRM":
            suggestion = f"🚀 Strong BUY{regime_tag} (score: {total_score:.0f}). 3 TF aligned. Target: {target:.0f}, Stop: {stop:.0f}"
        elif signal_type == "SCOUT":
            suggestion = f"👀 Bullish momentum{regime_tag} (score: {total_score:.0f}). Hold above {s1:.0f}, consider if strengthens."
        else:
            suggestion = f"⏱️ Hold{regime_tag}. No strong trend formation."
        
        if notes:
            suggestion += f" | Notes: {', '.join(notes)}"
        
        # ─── LEARNING ENTEGRASYONU ────────────────────────────────────────
        # Log ALL BUY/SELL signals (not just CONFIRM/SCOUT)
        if direction in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                await log_prediction(
                    symbol=symbol,
                    context={
                        "source": "PULSE_V3",
                        "total_score": total_score,
                        "signal_type": signal_type,
                        "regime": regime.regime,
                        "tf_scores": {"5m": result_5m["score"], "1h": result_1h["score"], "4h": result_4h["score"]},
                        "ml_prediction": {
                            "direction": direction,
                            "confidence": round(total_score),
                            "entry_price": current_price,
                            "target_price": target,
                            "stop_price": stop
                        }
                    },
                    analysis={
                        "final_decision": direction,
                        "confidence": round(total_score),
                        "model_used": "PULSE-V3-Hybrid-Regime"
                    },
                    timeframe="5m",
                    strategy="PULSE_V3",
                    model_type="pulse3",
                )
                logger.info(f"PULSE-V3 signal logged: {symbol} {direction} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE-V3 prediction: {log_err}")

        rebound_summary = None
        try:
            rebound_summary = await analyze_rebound(symbol, timeframe="5m", use_cache=not refresh)
        except Exception as rebound_err:
            logger.warning(f"PULSE-V3 rebound integration failed: {rebound_err}")

        payload = {
            "symbol": symbol,
            "timeframe": "5m",
            "timestamp": response_timestamp,
            "signal_timestamp": signal_timestamp,
            "pulse_score": round(total_score, 1),
            "max_score": 100,
            "signal_type": signal_type,
            "direction": direction,
            "confidence": min(95, int(total_score)),
            "price": round(current_price, 2),
            "timeframes": {
                "5m": {"raw_score": result_5m["score"], "max": 50, "trend": result_5m["trend"], "details": result_5m["details"]},
                "1h": {"raw_score": result_1h["score"], "max": 30, "trend": result_1h["trend"], "details": result_1h["details"]},
                "4h": {"raw_score": result_4h["score"], "max": 20, "trend": result_4h["trend"], "details": result_4h["details"]}
            },
            "levels": {
                "r2": round(r2, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "s1": round(s1, 2),
                "s2": round(s2, 2),
                "target": round(target, 2),
                "stop": round(stop, 2)
            },
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
            },
            "order_blocks": order_blocks_data[:4],
            "rr_ratio": round(rr_ratio, 2),
            "suggestion": suggestion,
            "entry_zones": [
                {"price": round(current_price, 2), "share": 40, "label": "Instant"},
                {"price": round(current_price - atr_val * 0.5, 2), "share": 30, "label": "On Dip"},
                {"price": round(current_price - atr_val, 2), "share": 30, "label": "Support"},
            ],
            "notes": notes,
            "valid_for_seconds": 300,
            "rebound": rebound_summary,
        }

        # ─── MACRO CONTEXT — informational notes ──────────────────────────
        try:
            from services.macro_context_service import commentary_lines as _macro_lines
            for _m in _macro_lines(symbol, direction, max_lines=2):
                if f"🌍 {_m}" not in payload["notes"]:
                    payload["notes"].append(f"🌍 {_m}")
        except Exception as _macro_err:
            logger.debug(f"PULSE3 macro notes skipped: {_macro_err}")

        _set_cached_panel_analysis("pulse3", symbol, "5m", payload)
        return payload
        
    except Exception as e:
        logger.error(f"PULSE V3 analysis error: {e}")
        import traceback
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "traceback": traceback.format_exc()}
        )


@router.get("/rebound/{symbol}", response_model=Dict[str, Any])
async def get_rebound_analysis(symbol: str, timeframe: str = Query("5m"), refresh: bool = False):
    try:
        from services.rebound_filter_service import analyze_rebound

        return await analyze_rebound(symbol, timeframe=timeframe, use_cache=not refresh)
    except Exception as e:
        logger.error(f"Rebound analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME ENDPOINT - Piyasa Rejimi Algılama
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/regime/{symbol}")  # raw dict: market_regime_service returns regime as a string + flat fields,
# which does not match the RegimeResponse(regime: Regime-object) schema and caused a 500 on serialization.
async def get_market_regime(symbol: str, force_refresh: bool = False):
    """
    Market Regime Detection - Piyasa Rejimi
    
    Regimes:
    - STRONG_TREND_UP: ADX>25, bullish structure → only LONG
    - STRONG_TREND_DOWN: ADX>25, bearish structure → only SHORT
    - RANGING: ADX<20, low volatility → mean reversion
    - TRANSITION: everything else → low risk
    
    Returns regime info, model weights, RSI thresholds, ATH status, session.
    Cached for 30 minutes (use force_refresh=true to override).
    """
    try:
        from services.market_regime_service import get_regime_info, check_fake_signal_timeout
        
        regime_info = await get_regime_info(symbol)
        
        # Add fake signal timeout status
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        regime_info["fake_signal_timeout"] = {
            "active": is_timed_out,
            "until": timeout_until,
            "reason": timeout_reason,
        }
        
        return regime_info
        
    except Exception as e:
        logger.error(f"Regime detection error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# EMA DEBUG ENDPOINT - TradingView Karşılaştırması
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/debug/ema/{symbol}", response_model=EMADebugResponse)
async def debug_ema_calculation(symbol: str, timeframe: str = "1H"):
    """
    EMA Debug - TradingView değerleriyle karşılaştırma için
    """
    try:
        from services.market_data_service import get_ohlcv_data
        
        # Get market data - need 250+ candles for EMA200
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=300)
        if not ohlcv:
            return {"error": "Veri alınamadı"}
        
        # Convert to numpy arrays
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        
        # Manual EMA calculation for verification
        def calculate_ema_manual(values, period):
            """Standard EMA formula matching TradingView"""
            if len(values) < period:
                return None
            alpha = 2.0 / (period + 1.0)
            # Start with SMA for first value
            ema = float(np.mean(values[:period]))
            # Then apply EMA formula
            for v in values[period:]:
                ema = alpha * float(v) + (1 - alpha) * ema
            return ema
        
        current_price = float(closes[-1])
        
        # Calculate EMAs
        ema20 = calculate_ema_manual(closes, 20)
        ema50 = calculate_ema_manual(closes, 50)
        ema200 = calculate_ema_manual(closes, 200)
        
        # Also calculate using our existing function for comparison
        from services.ml_prediction_service import _compute_technical_indicators
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data_points": len(closes),
            "current_price": round(current_price, 2),
            "manual_ema": {
                "ema20": round(ema20, 2) if ema20 else None,
                "ema50": round(ema50, 2) if ema50 else None,
                "ema200": round(ema200, 2) if ema200 else None,
            },
            "service_ema": {
                "ema20": round(ta.get("ema_20", 0), 2),
                "ema50": round(ta.get("ema_50", 0), 2),
                "ema200": round(ta.get("ema_200", 0), 2),
            },
            "distances": {
                "price_to_ema20": round(current_price - (ema20 or current_price), 2),
                "price_to_ema50": round(current_price - (ema50 or current_price), 2),
                "price_to_ema200": round(current_price - (ema200 or current_price), 2),
            },
            "distances_pct": {
                "price_to_ema20_pct": round(((current_price - (ema20 or current_price)) / current_price) * 100, 3) if ema20 else None,
                "price_to_ema50_pct": round(((current_price - (ema50 or current_price)) / current_price) * 100, 3) if ema50 else None,
                "price_to_ema200_pct": round(((current_price - (ema200 or current_price)) / current_price) * 100, 3) if ema200 else None,
            },
            "first_5_closes": [round(c, 2) for c in closes[:5]],
            "last_5_closes": [round(c, 2) for c in closes[-5:]],
            "note": "TradingView'deki EMA değerleriyle karşılaştırın. ±5 pips içinde olmalı."
        }
        
    except Exception as e:
        logger.error(f"EMA debug error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL KARŞILAŞTIRMA
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/compare/{symbol}", response_model=CompareResponse)
async def compare_models(symbol: str, timeframe: str = "M15"):
    """
    Run both EMEL and PULSE models and compare their signals.
    Logs predictions to database for performance tracking.
    """
    try:
        from services.model_comparison_service import run_model_comparison
        
        result = await run_model_comparison(symbol, timeframe)
        return result
        
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        return {"error": str(e)}


@router.get("/performance-stats", response_model=PerformanceStatsResponse)
async def get_performance_stats(days: int = 7):
    """
    Get performance statistics for EMEL vs PULSE models.
    """
    try:
        from services.model_comparison_service import get_model_performance_stats
        
        stats = await get_model_performance_stats(days)
        return stats
        
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# DATAHUB DEBUG - Hacim Verisi Kontrolü
# ═══════════════════════════════════════════════════════════════════════════════

# response_model kaldırıldı (2026-07-08): handler serbest-şekilli debug dict'i
# dönüyor; DataHubDebugResponse şeması (hub_status/cached) ile uyuşmayıp
# 500 validation hatası veriyordu.
@router.get("/debug/datahub/{symbol}", response_model=Dict[str, Any])
async def debug_datahub_volumes(symbol: str):
    """
    DataHub'daki hacim verilerini kontrol et.
    Hacim analizinin neden 0.0 gösterdiğini debug etmek için.
    """
    try:
        from services.data_hub import get_candles, get_hub_status
        from services.market_data_service import get_ohlcv_data
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_hub_status": get_hub_status(),
            "candle_data": {}
        }
        
        # Her timeframe için hacim verisini kontrol et
        for tf in ["5m", "15m", "30m", "1h", "4h", "eod"]:
            candles = get_candles(symbol, tf, limit=20)
            if candles:
                volumes = [c.get("volume", 0) for c in candles]
                result["candle_data"][tf] = {
                    "count": len(candles),
                    "volumes_sample": volumes[-5:],  # Son 5 hacim
                    "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
                    "max_volume": max(volumes) if volumes else 0,
                    "min_volume": min(volumes) if volumes else 0,
                    "total_volume": sum(volumes),
                }
            else:
                result["candle_data"][tf] = {"count": 0, "error": "No data in cache"}
        
        # EMEL'in kullandığı get_ohlcv_data ile karşılaştır
        ohlcv_1h = await get_ohlcv_data(symbol, "1h", limit=20)
        if ohlcv_1h:
            volumes = [c.get("volume", 0) for c in ohlcv_1h]
            result["ohlcv_1h_via_market_data_service"] = {
                "count": len(ohlcv_1h),
                "volumes_sample": volumes[-5:],
                "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
            }
        else:
            result["ohlcv_1h_via_market_data_service"] = {"error": "No data"}
        
        return result

    except Exception as e:
        logger.error(f"DataHub debug error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# ═══════════════════════════════════════════════════════════════════════════════
# SMC PANEL ENDPOINT - Smart Money Concepts / ICT Order Blocks
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/smc/{symbol}", response_model=Dict[str, Any])
async def get_smc_panel(
    symbol: str,
    timeframe: str = Query(default="5m", description="Timeframe: 5m, 15m, 1h, 4h"),
    limit: int = Query(default=100, ge=50, le=300, description="Candle count"),
    refresh: bool = Query(default=False, description="Force cache bypass"),
):
    """
    SMC Panel — Smart Money Concepts / ICT Order Block analizi.

    Returns OB/FVG/CHoCH/BOS detection + combined directional signal.
    Logs BUY/SELL signals to prediction_logs (model_type='smc').
    Cached for 300s (use refresh=true to bypass).
    """
    try:
        from services.order_block_service import service as smc_service
        from order_block_detector import OrderBlockConfig

        config = OrderBlockConfig()
        result = await smc_service.detect(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            config=config,
            use_cache=not refresh,
            log_signals=True,
        )

        # Normalise combined_signal action → direction for frontend consistency
        combined = result.get("combined_signal") or {}
        action = (combined.get("action") or "HOLD").upper()
        if action == "NEUTRAL":
            action = "HOLD"

        result["direction"] = action
        result["model"] = "smc"
        result["panel"] = "smc"
        return result

    except Exception as e:
        logger.error(f"SMC panel error for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "model": "smc", "direction": "HOLD"}

