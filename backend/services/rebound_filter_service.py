from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from order_block_detector import OrderBlockConfig
from services.data_fetcher import fetch_latest_price, fetch_ohlc_data
from services.market_regime_service import detect_regime
from services.order_block_service import service as order_block_service
from services.technical_indicators import (
    calculate_obv,
    calculate_rsi_series,
    obv_trend_confirmation,
    weighted_linear_regression,
)
from services.trend_analyzer import detect_pivot_rsi_divergence

logger = logging.getLogger(__name__)

_CACHE: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}
_CACHE_LOCK = Lock()
_CACHE_TTL = timedelta(seconds=60)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _pip_value(symbol: str) -> float:
    symbol_upper = (symbol or "").upper()
    if "XAU" in symbol_upper:
        return 1.0
    if "OIL" in symbol_upper or "USOIL" in symbol_upper or "CL" in symbol_upper:
        return 0.01
    return 1.0


def _normalize_timeframe(timeframe: str) -> str:
    tf = (timeframe or "5m").lower().strip()
    mapping = {
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "h1": "1h",
        "h4": "4h",
        "d1": "1d",
    }
    return mapping.get(tf, "5m")


def _compute_ta(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> Dict[str, float]:
    def ema(values: np.ndarray, period: int) -> float:
        if len(values) == 0:
            return 0.0
        if len(values) < period:
            return float(np.mean(values))
        alpha = 2.0 / (period + 1.0)
        result = float(np.mean(values[:period]))
        for value in values[period:]:
            result = alpha * float(value) + (1.0 - alpha) * result
        return float(result)

    def atr_series(high_arr: np.ndarray, low_arr: np.ndarray, close_arr: np.ndarray, period: int = 14) -> np.ndarray:
        if len(close_arr) < 2:
            return np.zeros(len(close_arr), dtype=np.float64)
        tr = np.zeros(len(close_arr), dtype=np.float64)
        tr[0] = high_arr[0] - low_arr[0]
        for i in range(1, len(close_arr)):
            tr[i] = max(
                high_arr[i] - low_arr[i],
                abs(high_arr[i] - close_arr[i - 1]),
                abs(low_arr[i] - close_arr[i - 1]),
            )
        out = np.zeros(len(close_arr), dtype=np.float64)
        seed = min(period, len(tr))
        out[:seed] = float(np.mean(tr[:seed])) if seed else 0.0
        if len(tr) <= period:
            return out
        current = float(np.mean(tr[:period]))
        out[period - 1] = current
        for i in range(period, len(tr)):
            current = ((current * (period - 1)) + tr[i]) / period
            out[i] = current
        out[: period - 1] = out[period - 1]
        return out

    def adx_with_di(high_arr: np.ndarray, low_arr: np.ndarray, close_arr: np.ndarray, period: int = 14) -> Tuple[float, float, float]:
        n = len(close_arr)
        if n < period * 2 + 1:
            return 20.0, 20.0, 20.0
        tr = np.maximum(
            high_arr[1:] - low_arr[1:],
            np.maximum(np.abs(high_arr[1:] - close_arr[:-1]), np.abs(low_arr[1:] - close_arr[:-1])),
        )
        up_move = high_arr[1:] - high_arr[:-1]
        down_move = low_arr[:-1] - low_arr[1:]
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        alpha = 1.0 / period
        atr_smooth = float(np.mean(tr[:period]))
        plus_dm_smooth = float(np.mean(plus_dm[:period]))
        minus_dm_smooth = float(np.mean(minus_dm[:period]))
        dx_values: List[float] = []
        plus_di_val = 20.0
        minus_di_val = 20.0
        for i in range(period, len(tr)):
            atr_smooth = atr_smooth * (1 - alpha) + float(tr[i]) * alpha
            plus_dm_smooth = plus_dm_smooth * (1 - alpha) + float(plus_dm[i]) * alpha
            minus_dm_smooth = minus_dm_smooth * (1 - alpha) + float(minus_dm[i]) * alpha
            if atr_smooth > 0:
                plus_di_val = 100.0 * plus_dm_smooth / atr_smooth
                minus_di_val = 100.0 * minus_dm_smooth / atr_smooth
                di_sum = plus_di_val + minus_di_val
                if di_sum > 0:
                    dx_values.append(100.0 * abs(plus_di_val - minus_di_val) / di_sum)
        if len(dx_values) < period:
            return 25.0, float(plus_di_val), float(minus_di_val)
        adx_val = float(np.mean(dx_values[:period]))
        for dx in dx_values[period:]:
            adx_val = adx_val * (1 - alpha) + dx * alpha
        return float(np.clip(adx_val, 0, 100)), float(plus_di_val), float(minus_di_val)

    current = float(closes[-1]) if len(closes) else 0.0
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi_series = calculate_rsi_series(closes, 14)
    rsi14 = float(rsi_series[-1]) if len(rsi_series) else 50.0
    atr_vals = atr_series(highs, lows, closes, 14)
    atr14 = float(atr_vals[-1]) if len(atr_vals) else 0.0
    atr_avg20 = float(np.mean(atr_vals[-20:])) if len(atr_vals) >= 20 else atr14 or 1.0
    atr_ratio = atr14 / atr_avg20 if atr_avg20 > 0 else 1.0
    adx_val, plus_di, minus_di = adx_with_di(highs, lows, closes, 14)
    ema_stack_bull = float(sum([current > ema20, ema20 > ema50, ema50 > ema200])) / 3.0 * 100.0
    ema_stack_bear = float(sum([current < ema20, ema20 < ema50, ema50 < ema200])) / 3.0 * 100.0
    return {
        "close": current,
        "ema_20": ema20,
        "ema_50": ema50,
        "ema_200": ema200,
        "rsi_14": rsi14,
        "rsi_series_last": rsi_series,
        "atr_14": atr14,
        "atr_ratio": atr_ratio,
        "adx": adx_val,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "ema_stack_bull": ema_stack_bull,
        "ema_stack_bear": ema_stack_bear,
    }


def _closeness_score(distance: float, atr_value: float, hard_cap: float = 2.0) -> float:
    denom = max(atr_value, 1e-9)
    normalized = distance / denom
    if normalized >= hard_cap:
        return 0.0
    return max(0.0, 1.0 - (normalized / hard_cap))


def _detect_candlestick_signal(ohlcv: List[Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
    try:
        from services.candlestick_pattern_service import PATTERN_INFO, detect_patterns_manual

        opens = np.array([c["open"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        patterns = detect_patterns_manual(opens, highs, lows, closes, timeframe)
        top = patterns[0] if patterns else None
        if not top:
            return {"bullish": False, "bearish": False, "name": None, "confidence": 0.0}
        info = PATTERN_INFO.get(top.pattern_id, {})
        signal = str(info.get("signal") or top.signal or "neutral").lower()
        return {
            "bullish": signal == "bullish",
            "bearish": signal == "bearish",
            "name": info.get("name") or top.name,
            "name_tr": info.get("name_tr") or top.name_tr,
            "confidence": float(getattr(top, "confidence", 0.0) or 0.0),
        }
    except Exception as exc:
        logger.debug("rebound candlestick detection failed: %s", exc)
        return {"bullish": False, "bearish": False, "name": None, "confidence": 0.0}


def _count_zone_touches(ohlcv: List[Dict[str, Any]], low: float, high: float, limit: int = 80) -> int:
    touches = 0
    for candle in ohlcv[-limit:]:
        candle_low = float(candle.get("low", 0.0) or 0.0)
        candle_high = float(candle.get("high", 0.0) or 0.0)
        if candle_high >= low and candle_low <= high:
            touches += 1
    return touches


def _select_order_block(order_blocks: List[Dict[str, Any]], direction: str, current_price: float, ohlcv: List[Dict[str, Any]], atr_value: float) -> Optional[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for block in order_blocks or []:
        if str(block.get("type") or "").lower() != direction:
            continue
        low = float(block.get("zone_low", block.get("low", 0.0)) or 0.0)
        high = float(block.get("zone_high", block.get("high", 0.0)) or 0.0)
        if low <= 0 or high <= 0 or high < low:
            continue
        distance = min(abs(current_price - low), abs(current_price - high), abs(current_price - ((low + high) / 2.0)))
        touch_count = _count_zone_touches(ohlcv, low, high)
        score = float(block.get("score", 0.0) or 0.0)
        candidates.append(
            {
                **block,
                "zone_low": low,
                "zone_high": high,
                "distance": distance,
                "touch_count": touch_count,
                "proximity_score": _closeness_score(distance, atr_value or max(current_price * 0.002, 1e-6)),
                "is_fresh": not bool(block.get("tested")) and not bool(block.get("mitigated")),
                "score_numeric": score,
            }
        )
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            -float(item["proximity_score"]),
            -float(item["score_numeric"]),
            -int(item["touch_count"]),
        )
    )
    return candidates[0]


def _select_fvg(fvg_list: List[Dict[str, Any]], direction: str, current_price: float, atr_value: float) -> Optional[Dict[str, Any]]:
    candidates = []
    for fvg in fvg_list or []:
        if str(fvg.get("direction") or "").lower() != direction:
            continue
        low = float(fvg.get("low", 0.0) or 0.0)
        high = float(fvg.get("high", 0.0) or 0.0)
        if low <= 0 or high <= 0 or high < low:
            continue
        distance = 0.0 if low <= current_price <= high else min(abs(current_price - low), abs(current_price - high))
        candidates.append({
            **fvg,
            "distance": distance,
            "proximity_score": _closeness_score(distance, atr_value or max(current_price * 0.002, 1e-6)),
        })
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-float(item["proximity_score"]), float(item["distance"])))
    return candidates[0]


def _liquidity_sweep(ohlcv: List[Dict[str, Any]], side: str) -> bool:
    if len(ohlcv) < 25:
        return False
    recent = ohlcv[-25:]
    latest = recent[-1]
    prior = recent[:-1]
    latest_low = float(latest.get("low", 0.0) or 0.0)
    latest_high = float(latest.get("high", 0.0) or 0.0)
    latest_close = float(latest.get("close", 0.0) or 0.0)
    prior_lows = [float(c.get("low", 0.0) or 0.0) for c in prior]
    prior_highs = [float(c.get("high", 0.0) or 0.0) for c in prior]
    if side == "sell":
        reference = min(prior_lows) if prior_lows else latest_low
        return latest_low < reference and latest_close > reference
    reference = max(prior_highs) if prior_highs else latest_high
    return latest_high > reference and latest_close < reference


def _obv_metrics(closes: np.ndarray, volumes: np.ndarray) -> Dict[str, Any]:
    confirmed, trend = obv_trend_confirmation(closes, volumes, period=min(20, len(closes)))
    obv = calculate_obv(closes, volumes)
    spike = False
    divergence = False
    if len(obv) >= 6 and len(closes) >= 6:
        recent_change = abs(float(obv[-1] - obv[-2]))
        baseline = np.mean(np.abs(np.diff(obv[-6:]))) if len(obv) >= 6 else 0.0
        spike = recent_change > baseline * 1.8 if baseline > 0 else False
        price_up = closes[-1] > closes[-5]
        obv_up = obv[-1] > obv[-5]
        divergence = price_up and not obv_up
    return {
        "confirmed": confirmed,
        "trend": trend,
        "spike": spike,
        "divergence": divergence,
    }


def _derive_targets(current_price: float, support: Optional[Dict[str, Any]], resistance: Optional[Dict[str, Any]], atr_value: float, direction: str) -> Dict[str, float]:
    atr_buffer = atr_value or max(current_price * 0.003, 1e-6)
    if direction == "BUY":
        bounce_target = float((resistance or {}).get("price") or (current_price + atr_buffer * 2.2))
        invalidation = float((support or {}).get("price") or current_price) - atr_buffer * 0.6
        secondary_turn = bounce_target + atr_buffer * 0.4
    else:
        bounce_target = float((support or {}).get("price") or (current_price - atr_buffer * 2.2))
        invalidation = float((resistance or {}).get("price") or current_price) + atr_buffer * 0.6
        secondary_turn = bounce_target - atr_buffer * 0.4
    return {
        "bounce_target": round(bounce_target, 2),
        "invalidation": round(invalidation, 2),
        "secondary_turn": round(secondary_turn, 2),
    }


def _rr_progress(current_price: float, target: float, invalidation: float, price_reference: float, direction: str) -> float:
    total_move = abs(target - price_reference)
    if total_move <= 1e-9:
        return 0.0
    current_move = abs(current_price - price_reference)
    if direction == "SELL" and current_price > price_reference:
        current_move = 0.0
    if direction == "BUY" and current_price < price_reference:
        current_move = 0.0
    return max(0.0, min(1.5, current_move / total_move))


async def analyze_rebound(symbol: str, timeframe: str = "5m", use_cache: bool = True) -> Dict[str, Any]:
    normalized_tf = _normalize_timeframe(timeframe)
    cache_key = f"{symbol}:{normalized_tf}"
    if use_cache:
        with _CACHE_LOCK:
            cached = _CACHE.get(cache_key)
            if cached and _utc_now() - cached[0] < _CACHE_TTL:
                return cached[1]

    response_timestamp = _utc_now().isoformat().replace("+00:00", "Z")
    base_limit = 240 if normalized_tf in {"5m", "15m"} else 180
    base_ohlcv = await fetch_ohlc_data(symbol, normalized_tf, limit=base_limit)
    if not base_ohlcv or len(base_ohlcv) < 60:
        return {
            "symbol": symbol,
            "timeframe": normalized_tf,
            "timestamp": response_timestamp,
            "error": "Insufficient data for rebound analysis",
        }

    h1_ohlcv = await fetch_ohlc_data(symbol, "1h", limit=240)
    h4_ohlcv = await fetch_ohlc_data(symbol, "4h", limit=180)
    live_price = await fetch_latest_price(symbol)

    current_price = float(live_price) if live_price else float(base_ohlcv[-1]["close"])

    closes = np.array([c["close"] for c in base_ohlcv], dtype=np.float64)
    highs = np.array([c["high"] for c in base_ohlcv], dtype=np.float64)
    lows = np.array([c["low"] for c in base_ohlcv], dtype=np.float64)
    volumes = np.array([c.get("volume", 0.0) for c in base_ohlcv], dtype=np.float64)
    base_ta = _compute_ta(closes, highs, lows, volumes)

    h1_ta = None
    h4_ta = None
    if h1_ohlcv and len(h1_ohlcv) >= 60:
        h1_ta = _compute_ta(
            np.array([c["close"] for c in h1_ohlcv], dtype=np.float64),
            np.array([c["high"] for c in h1_ohlcv], dtype=np.float64),
            np.array([c["low"] for c in h1_ohlcv], dtype=np.float64),
            np.array([c.get("volume", 0.0) for c in h1_ohlcv], dtype=np.float64),
        )
    if h4_ohlcv and len(h4_ohlcv) >= 40:
        h4_ta = _compute_ta(
            np.array([c["close"] for c in h4_ohlcv], dtype=np.float64),
            np.array([c["high"] for c in h4_ohlcv], dtype=np.float64),
            np.array([c["low"] for c in h4_ohlcv], dtype=np.float64),
            np.array([c.get("volume", 0.0) for c in h4_ohlcv], dtype=np.float64),
        )

    regime = await detect_regime(symbol)
    smc = await order_block_service.detect(symbol, normalized_tf, 300, OrderBlockConfig(), use_cache=use_cache, log_signals=False)

    support_resistance = (smc or {}).get("support_resistance") or {}
    nearest_support = support_resistance.get("nearest_support")
    nearest_resistance = support_resistance.get("nearest_resistance")
    bullish_ob = _select_order_block((smc or {}).get("order_blocks") or [], "bullish", current_price, base_ohlcv, base_ta["atr_14"])
    bearish_ob = _select_order_block((smc or {}).get("order_blocks") or [], "bearish", current_price, base_ohlcv, base_ta["atr_14"])
    bullish_fvg = _select_fvg((smc or {}).get("fvg_list") or [], "bullish", current_price, base_ta["atr_14"])
    bearish_fvg = _select_fvg((smc or {}).get("fvg_list") or [], "bearish", current_price, base_ta["atr_14"])
    choch_list = (smc or {}).get("choch_list") or []
    bos_list = (smc or {}).get("bos_list") or []

    candle_signal = _detect_candlestick_signal(base_ohlcv, normalized_tf)
    rsi_divergence = detect_pivot_rsi_divergence(highs, lows, closes, base_ta["rsi_series_last"], lookback=min(50, len(closes)))
    regression_slope, _, regression_r2 = weighted_linear_regression(closes[-30:])
    obv_data = _obv_metrics(closes, volumes)

    mtf_bull_count = 0
    mtf_bear_count = 0
    mtf_stack_scores: List[float] = []
    for tf_ta in [h1_ta, h4_ta]:
        if not tf_ta:
            continue
        mtf_stack_scores.append(float(tf_ta["ema_stack_bull"]))
        if tf_ta["ema_stack_bull"] >= 70:
            mtf_bull_count += 1
        if tf_ta["ema_stack_bear"] >= 70:
            mtf_bear_count += 1
    mtf_bull_score = round(float(np.mean(mtf_stack_scores)) if mtf_stack_scores else 0.0, 1)
    mtf_bear_score = round(float(np.mean([tf_ta["ema_stack_bear"] for tf_ta in [h1_ta, h4_ta] if tf_ta])) if any([h1_ta, h4_ta]) else 0.0, 1)

    long_mandatory_hits = 0
    long_reasons: List[str] = []
    long_bonus_reasons: List[str] = []
    long_score = 0.0

    bullish_ob_hit = bool(
        bullish_ob
        and bullish_ob["proximity_score"] >= 0.35
        and (bullish_ob["is_fresh"] or bullish_ob["score_numeric"] >= 60)
        and bullish_ob["touch_count"] >= 1
    )
    if bullish_ob_hit:
        long_mandatory_hits += 1
        long_score += 22
        long_reasons.append("Bullish order block zone active")

    bullish_divergence = rsi_divergence.type == "BULLISH_DIV"
    oversold = base_ta["rsi_14"] < 40
    if oversold or bullish_divergence:
        long_mandatory_hits += 1
        long_score += 16
        long_reasons.append("RSI oversold/divergence support")

    if candle_signal["bullish"]:
        long_mandatory_hits += 1
        long_score += 16
        long_reasons.append(f"Bullish reversal candle: {candle_signal.get('name_tr') or candle_signal.get('name')}")

    if mtf_bull_count >= 1 and mtf_bull_score >= 60:
        long_mandatory_hits += 1
        long_score += 18
        long_reasons.append("1H + 4H bullish EMA stack alignment")

    if _liquidity_sweep(base_ohlcv, "sell"):
        long_score += 15
        long_bonus_reasons.append("Sell-side liquidity sweep detected")
    if bullish_fvg and bullish_fvg["proximity_score"] >= 0.4:
        long_score += 12
        long_bonus_reasons.append("Bullish FVG nearby")
    if base_ta["adx"] > 25 and base_ta["plus_di"] > base_ta["minus_di"]:
        long_score += 10
        long_bonus_reasons.append("ADX and +DI support bullish rebound")
    if obv_data["trend"] == "BULLISH" or obv_data["spike"]:
        long_score += 8
        long_bonus_reasons.append("OBV rising / spike confirmation")
    if regression_slope > 0 and regression_r2 > 0.75:
        long_score += 8
        long_bonus_reasons.append("Positive weighted regression slope")
    if base_ta["atr_ratio"] < 1.5:
        long_score += 6
        long_bonus_reasons.append("Volatility compression supports cleaner bounce")
    if regime.session in {"london", "newyork", "overlap_london_ny", "xetra_us_overlap", "nymex"}:
        long_score += 5
        long_bonus_reasons.append(f"Active session: {regime.session}")
    if not regime.is_ath_zone:
        long_score += 10
        long_bonus_reasons.append("Not near ATH, better room for dip rebound")

    long_targets = _derive_targets(current_price, nearest_support, nearest_resistance, base_ta["atr_14"], "BUY")
    long_score = round(min(100.0, long_score), 1)
    long_label = "HIGH_PROBABILITY" if long_mandatory_hits >= 3 and long_score >= 75 else "WATCH" if long_mandatory_hits >= 2 and long_score >= 60 else "NO_SIGNAL"

    exit_mandatory_hits = 0
    exit_reasons: List[str] = []
    exit_bonus_reasons: List[str] = []
    exit_score = 0.0

    bearish_ob_hit = bool(
        bearish_ob
        and bearish_ob["proximity_score"] >= 0.35
        and (bearish_ob["is_fresh"] or bearish_ob["score_numeric"] >= 55)
    )
    if bearish_ob_hit:
        exit_mandatory_hits += 1
        exit_score += 20
        exit_reasons.append("Bearish order block / breaker zone active")

    bearish_divergence = rsi_divergence.type == "BEARISH_DIV"
    overbought = base_ta["rsi_14"] > 65
    if overbought or bearish_divergence:
        exit_mandatory_hits += 1
        exit_score += 16
        exit_reasons.append("RSI overbought/divergence warning")

    if candle_signal["bearish"]:
        exit_mandatory_hits += 1
        exit_score += 14
        exit_reasons.append(f"Bearish reversal candle: {candle_signal.get('name_tr') or candle_signal.get('name')}")

    bearish_choch = any(str(item.get("type") or "").lower() == "bearish" for item in choch_list[-2:])
    bearish_bos = any(str(item.get("type") or "").lower() == "bearish" for item in bos_list[-2:])
    if bearish_choch:
        exit_score += 20
        exit_bonus_reasons.append("Bearish CHoCH detected")
    if bearish_bos:
        exit_score += 15
        exit_bonus_reasons.append("Bearish BOS detected")
    if mtf_bear_count >= 1 or mtf_bear_score >= 60:
        exit_score += 12
        exit_bonus_reasons.append("Higher timeframe bearish alignment emerging")
    if _liquidity_sweep(base_ohlcv, "buy"):
        exit_score += 10
        exit_bonus_reasons.append("Buy-side liquidity sweep / high sweep detected")
    if obv_data["divergence"] or obv_data["trend"] == "BEARISH":
        exit_score += 8
        exit_bonus_reasons.append("OBV divergence / weakening participation")

    lookback = min(22, len(closes))
    chandelier_period_high = float(np.max(highs[-lookback:])) if lookback else current_price
    chandelier_exit_long = chandelier_period_high - (base_ta["atr_14"] * 3.0)
    if current_price < chandelier_exit_long:
        exit_score += 10
        exit_bonus_reasons.append("Price slipped below chandelier long exit")

    exit_targets = _derive_targets(current_price, nearest_support, nearest_resistance, base_ta["atr_14"], "SELL")
    rr_progress = _rr_progress(current_price, long_targets["bounce_target"], long_targets["invalidation"], float((nearest_support or {}).get("price") or current_price), "BUY")
    if 0.7 <= rr_progress <= 1.05 and bearish_divergence:
        exit_score += 8
        exit_bonus_reasons.append("Bounce reached 70-80% objective with divergence")

    if bearish_ob_hit and (overbought or bearish_divergence) and candle_signal["bearish"]:
        exit_mandatory_hits = max(exit_mandatory_hits, 3)

    exit_score = round(min(100.0, exit_score), 1)
    exit_label = "EXIT_OR_SHORT" if exit_mandatory_hits >= 2 and exit_score >= 60 else "WATCH_EXIT" if exit_mandatory_hits >= 1 and exit_score >= 45 else "HOLD_REBOUND"

    payload = {
        "symbol": symbol,
        "timeframe": normalized_tf,
        "timestamp": response_timestamp,
        "price": round(current_price, 2),
        "rebound_long": {
            "label": long_label,
            "is_high_probability": long_label == "HIGH_PROBABILITY",
            "score": long_score,
            "threshold": 85,
            "mandatory_hits": long_mandatory_hits,
            "mandatory_required": 3,
            "zone": {
                "type": "bullish_order_block" if bullish_ob_hit else ("support" if nearest_support else "none"),
                "low": round(float((bullish_ob or {}).get("zone_low", 0.0) or float((nearest_support or {}).get("price", 0.0) or 0.0)), 2) if (bullish_ob or nearest_support) else None,
                "high": round(float((bullish_ob or {}).get("zone_high", 0.0) or float((nearest_support or {}).get("price", 0.0) or 0.0)), 2) if (bullish_ob or nearest_support) else None,
                "touch_count": int((bullish_ob or {}).get("touch_count", 0) or 0),
                "fresh": bool((bullish_ob or {}).get("is_fresh", False)),
                "score": float((bullish_ob or {}).get("score_numeric", 0.0) or 0.0),
            },
            "expected_bounce_to": long_targets["bounce_target"],
            "secondary_turn_zone": long_targets["secondary_turn"],
            "invalidation": long_targets["invalidation"],
            "reasons": long_reasons,
            "bonus_confirmations": long_bonus_reasons,
        },
        "rebound_exit": {
            "label": exit_label,
            "is_exit_trigger": exit_label == "EXIT_OR_SHORT",
            "score": exit_score,
            "threshold": 70,
            "mandatory_hits": exit_mandatory_hits,
            "mandatory_required": 2,
            "reversal_zone": {
                "type": "bearish_order_block" if bearish_ob_hit else ("resistance" if nearest_resistance else "none"),
                "low": round(float((bearish_ob or {}).get("zone_low", 0.0) or float((nearest_resistance or {}).get("price", 0.0) or 0.0)), 2) if (bearish_ob or nearest_resistance) else None,
                "high": round(float((bearish_ob or {}).get("zone_high", 0.0) or float((nearest_resistance or {}).get("price", 0.0) or 0.0)), 2) if (bearish_ob or nearest_resistance) else None,
            },
            "take_profit_zone": exit_targets["bounce_target"],
            "short_invalidation": exit_targets["invalidation"],
            "reasons": exit_reasons,
            "bonus_confirmations": exit_bonus_reasons,
        },
        "context": {
            "regime": regime.regime,
            "session": regime.session,
            "is_ath": regime.is_ath_zone,
            "mtf_bull_count": mtf_bull_count,
            "mtf_bear_count": mtf_bear_count,
            "mtf_bull_score": mtf_bull_score,
            "mtf_bear_score": mtf_bear_score,
            "rsi": round(base_ta["rsi_14"], 2),
            "adx": round(base_ta["adx"], 2),
            "plus_di": round(base_ta["plus_di"], 2),
            "minus_di": round(base_ta["minus_di"], 2),
            "atr_ratio": round(base_ta["atr_ratio"], 3),
            "regression_slope": round(regression_slope, 5),
            "regression_r2": round(regression_r2, 3),
            "obv_trend": obv_data["trend"],
            "divergence": rsi_divergence.type,
            "smc_trend": (smc or {}).get("trend"),
        },
        "levels": {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "bullish_fvg": bullish_fvg,
            "bearish_fvg": bearish_fvg,
        },
    }

    with _CACHE_LOCK:
        _CACHE[cache_key] = (_utc_now(), payload)

    return payload
