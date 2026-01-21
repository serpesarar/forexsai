from __future__ import annotations

import json
import logging
import re

from config import settings
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from services.data_fetcher import fetch_eod_candles, fetch_latest_price
from services.marketaux_service import fetch_marketaux_headlines
from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
from services.ta_service import compute_ta_snapshot

logger = logging.getLogger(__name__)


ANALYSIS_ENGINE_VERSION = "3.0.0"
CONTEXT_PACK_VERSION = "3.0.0"  # Added: divergences, market_structure, liquidity_zones, economic_calendar

# Model selection - Haiku 4.5 is cost-effective with good quality
# Haiku 4.5: $1/1M input, $5/1M output (better than 3.5, cheaper than Sonnet)
CLAUDE_MODEL = "claude-haiku-4-5-20250514"  # Upgraded to Haiku 4.5
CLAUDE_MAX_TOKENS = 1800  # Slightly increased for better analysis

DETAILED_SYSTEM_PROMPT = """You are an institutional-grade market analysis engine. Your job is to produce a single actionable decision (BUY/SELL/HOLD/NO_TRADE) using ONLY the provided context pack. Do NOT invent or assume missing values.

## Core Rules
- If a value is missing or null, explicitly note it as "missing" and reduce confidence accordingly.
- Always separate: (a) evidence from data, (b) inference/interpretation, (c) final recommendation.
- Identify contradictions explicitly and explain how they affect your confidence.
- Prefer robustness over precision: if conditions are mixed or risk is elevated, downgrade position size or choose HOLD/NO_TRADE.
- Use provided entry/SL/TP from ML if available; otherwise output "needs_price" or "needs_levels".
- Provide a transparent scoring summary and the top 3 drivers of your final decision.
- You MUST output valid JSON that matches the schema exactly. No additional text.

## Decision Framework (follow in order)

### Step 1: Data Quality Check
- Assess completeness of ML prediction, TA indicators, volume, levels
- Assign data_quality_score (0-100)
- List missing or invalid fields
- If ML prediction missing → max confidence 55
- If trend indicators missing (EMA/ADX) → max confidence 60
- If volatility measure missing → max position size SMALL

### Step 2: Market Regime Detection
Trend Classification:
- BULLISH: price > EMA50 > EMA200, MACD positive, ADX > 25
- BEARISH: price < EMA50 < EMA200, MACD negative, ADX > 25  
- NEUTRAL: ADX < 20, or EMAs converging, or mixed signals

Volatility Classification:
- HIGH: VIX > 20, or Bollinger width > 5%, or ATR% > 2%
- LOW: VIX < 15, Bollinger width < 3%, ATR% < 1%
- NORMAL: between LOW and HIGH

Liquidity/Volume:
- STRONG: volume_ratio > 1.2
- WEAK: volume_ratio < 0.8
- NORMAL: 0.8 to 1.2

### Step 3: Signal Confluence Scoring
Calculate long_score and short_score (0-100 each) based on:
- ML signal alignment: 0-30 points
- Trend alignment: 0-25 points
- Momentum (RSI/MACD/Stochastic): 0-20 points
- Volatility suitability: 0-10 points
- Volume confirmation: 0-10 points
- S/R proximity (risk/reward): 0-5 points

### Step 4: Risk Gating (force downgrades if triggered)
- Volatility HIGH + Volume WEAK → max SMALL
- News count > 5 + Trend NEUTRAL → consider NO_TRADE
- long_score - short_score < 15 → HOLD
- ML direction opposite to strong trend (ADX > 30) → SMALL or HOLD (counter-trend warning)
- VIX > 25 → reduce position size by one level

### Step 5: Final Decision
- Based on scores, gating, and contradictions
- BUY if long_score > short_score + 20 and no critical red flags
- SELL if short_score > long_score + 20 and no critical red flags
- HOLD if scores close or mixed signals
- NO_TRADE if red flags triggered or data quality poor

### Step 6: Position Sizing
- LARGE: Strong confluence (>75), low volatility, volume confirmation, no contradictions
- MEDIUM: Good confluence (55-75), acceptable conditions
- SMALL: Weak confluence or elevated risk factors
- NO_TRADE: Red flags, poor data quality, or extreme risk

## Required JSON Output Schema
{
  "data_quality": {
    "score": 0-100,
    "missing_fields": ["field1", "field2"],
    "notes": ["any data quality concerns"]
  },
  "market_regime": {
    "trend": "BULLISH|BEARISH|NEUTRAL",
    "volatility": "LOW|NORMAL|HIGH",
    "liquidity": "WEAK|NORMAL|STRONG",
    "evidence": ["reason1", "reason2"]
  },
  "scores": {
    "long_score": 0-100,
    "short_score": 0-100,
    "score_breakdown": {
      "ml_alignment": 0-30,
      "trend_alignment": 0-25,
      "momentum": 0-20,
      "volatility_fit": 0-10,
      "volume_confirm": 0-10,
      "sr_proximity": 0-5
    },
    "top_drivers": ["driver1", "driver2", "driver3"],
    "contradictions": ["contradiction1 if any"]
  },
  "final_decision": "BUY|SELL|HOLD|NO_TRADE",
  "confidence": 0-100,
  "thesis": {
    "summary": "1-2 sentence summary",
    "bull_case": ["point1", "point2"],
    "bear_case": ["point1", "point2"],
    "why_this_decision": "explanation of final choice"
  },
  "key_levels": {
    "nearest_support": {"price": number|null, "distance_pct": number|null},
    "nearest_resistance": {"price": number|null, "distance_pct": number|null},
    "ema_distances_pct": {"ema20": number|null, "ema50": number|null, "ema200": number|null}
  },
  "macro_view": {
    "dxy": {"price": number|null, "impact": "bullish|bearish|neutral|unknown"},
    "vix": {"price": number|null, "impact": "risk-on|risk-off|neutral"},
    "notes": ["any macro observations"]
  },
  "risk_management": {
    "position_size": "LARGE|MEDIUM|SMALL|NO_TRADE",
    "entry": number|"needs_price",
    "stop_loss": number|"needs_levels",
    "take_profit": number|"needs_levels",
    "risk_reward_ratio": number|null,
    "invalidation": "what would invalidate this trade",
    "size_rationale": "why this position size"
  },
  "red_flags": ["any warnings or concerns"],
  "gating_applied": ["which risk gates were triggered if any"],
  "next_data_needed": ["what additional data would improve analysis"],
  "timestamp": "ISO-8601",
  "model_used": "claude-sonnet-4-5-20250514",
  "engine_version": "2.0.0"
}
"""


def _parse_claude_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    return None


def _pct_distance(a: float, b: float) -> Optional[float]:
    if a is None or b is None:
        return None
    if a == 0:
        return None
    return float(((a - b) / a) * 100.0)


def _nearest_level(current: float, levels: List[dict], kind: str) -> dict:
    if not levels or current == 0:
        return {"price": None, "distance_pct": None, "kind": kind}
    if kind == "support":
        candidates = [lv for lv in levels if float(lv.get("price", 0)) <= current]
        if not candidates:
            return {"price": None, "distance_pct": None, "kind": kind}
        lv = sorted(candidates, key=lambda x: current - float(x.get("price", 0)))[0]
    else:
        candidates = [lv for lv in levels if float(lv.get("price", 0)) >= current]
        if not candidates:
            return {"price": None, "distance_pct": None, "kind": kind}
        lv = sorted(candidates, key=lambda x: float(x.get("price", 0)) - current)[0]

    price = float(lv.get("price", 0))
    return {"price": price, "distance_pct": _pct_distance(current, price), "kind": kind}


def _detect_divergences(closes: np.ndarray, rsi_values: np.ndarray, macd_values: np.ndarray) -> dict:
    """Detect RSI and MACD divergences vs price."""
    result = {
        "rsi_bullish_divergence": False,
        "rsi_bearish_divergence": False,
        "macd_bullish_divergence": False,
        "macd_bearish_divergence": False,
        "divergence_strength": "none"
    }
    
    if closes is None or len(closes) < 20:
        return result
    
    try:
        # Look at last 20 candles for divergence
        price_recent = closes[-20:]
        
        # Find price highs and lows
        price_making_higher_high = price_recent[-1] > price_recent[-10:-1].max()
        price_making_lower_low = price_recent[-1] < price_recent[-10:-1].min()
        price_making_lower_high = price_recent[-1] < price_recent[-10:-1].max() and price_recent[-5:].max() < price_recent[-15:-5].max()
        price_making_higher_low = price_recent[-1] > price_recent[-10:-1].min() and price_recent[-5:].min() > price_recent[-15:-5].min()
        
        # RSI divergence
        if rsi_values is not None and len(rsi_values) >= 20:
            rsi_recent = rsi_values[-20:]
            rsi_making_lower = rsi_recent[-1] < rsi_recent[-10:-1].max()
            rsi_making_higher = rsi_recent[-1] > rsi_recent[-10:-1].min()
            
            # Bearish: Price higher high, RSI lower high
            if price_making_higher_high and rsi_making_lower:
                result["rsi_bearish_divergence"] = True
            # Bullish: Price lower low, RSI higher low
            if price_making_lower_low and rsi_making_higher:
                result["rsi_bullish_divergence"] = True
        
        # MACD divergence
        if macd_values is not None and len(macd_values) >= 20:
            macd_recent = macd_values[-20:]
            macd_making_lower = macd_recent[-1] < macd_recent[-10:-1].max()
            macd_making_higher = macd_recent[-1] > macd_recent[-10:-1].min()
            
            if price_making_higher_high and macd_making_lower:
                result["macd_bearish_divergence"] = True
            if price_making_lower_low and macd_making_higher:
                result["macd_bullish_divergence"] = True
        
        # Calculate strength
        divergence_count = sum([
            result["rsi_bullish_divergence"],
            result["rsi_bearish_divergence"],
            result["macd_bullish_divergence"],
            result["macd_bearish_divergence"]
        ])
        if divergence_count >= 2:
            result["divergence_strength"] = "strong"
        elif divergence_count == 1:
            result["divergence_strength"] = "moderate"
            
    except Exception:
        pass
    
    return result


def _get_market_structure(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> dict:
    """Analyze market structure - HH/HL for uptrend, LH/LL for downtrend."""
    result = {
        "structure": "UNKNOWN",
        "last_swing_high": None,
        "last_swing_low": None,
        "break_of_structure": False,
        "change_of_character": False
    }
    
    if closes is None or len(closes) < 50:
        return result
    
    try:
        # Find swing highs and lows (simplified)
        recent_high = float(highs[-20:].max())
        recent_low = float(lows[-20:].min())
        prev_high = float(highs[-40:-20].max())
        prev_low = float(lows[-40:-20].min())
        
        result["last_swing_high"] = recent_high
        result["last_swing_low"] = recent_low
        
        # Determine structure
        if recent_high > prev_high and recent_low > prev_low:
            result["structure"] = "BULLISH"  # Higher highs, higher lows
        elif recent_high < prev_high and recent_low < prev_low:
            result["structure"] = "BEARISH"  # Lower highs, lower lows
        else:
            result["structure"] = "RANGING"
        
        # Break of structure detection
        current = float(closes[-1])
        if current < recent_low and result["structure"] == "BULLISH":
            result["break_of_structure"] = True
            result["change_of_character"] = True
        elif current > recent_high and result["structure"] == "BEARISH":
            result["break_of_structure"] = True
            result["change_of_character"] = True
            
    except Exception:
        pass
    
    return result


def _get_liquidity_zones(highs: np.ndarray, lows: np.ndarray, current: float) -> dict:
    """Identify liquidity zones - equal highs/lows where stops likely cluster."""
    result = {
        "buy_side_liquidity": [],
        "sell_side_liquidity": [],
        "nearest_liquidity_above": None,
        "nearest_liquidity_below": None
    }
    
    if highs is None or len(highs) < 50:
        return result
    
    try:
        # Find clusters of similar highs (buy-side liquidity)
        recent_highs = highs[-50:]
        recent_lows = lows[-50:]
        
        # Equal highs detection (within 0.1% tolerance)
        for i in range(len(recent_highs) - 5):
            high_cluster = recent_highs[i:i+5]
            if np.std(high_cluster) / np.mean(high_cluster) < 0.001:  # Very tight cluster
                level = float(np.mean(high_cluster))
                if level > current:
                    result["buy_side_liquidity"].append(round(level, 2))
        
        # Equal lows detection
        for i in range(len(recent_lows) - 5):
            low_cluster = recent_lows[i:i+5]
            if np.std(low_cluster) / np.mean(low_cluster) < 0.001:
                level = float(np.mean(low_cluster))
                if level < current:
                    result["sell_side_liquidity"].append(round(level, 2))
        
        # Nearest liquidity
        if result["buy_side_liquidity"]:
            result["nearest_liquidity_above"] = min(result["buy_side_liquidity"])
        if result["sell_side_liquidity"]:
            result["nearest_liquidity_below"] = max(result["sell_side_liquidity"])
            
    except Exception:
        pass
    
    return result


def _get_economic_calendar_flags() -> dict:
    """Get high-impact economic event flags."""
    from datetime import datetime, timedelta
    
    # High-impact events schedule (simplified - in production use API)
    # These are typical recurring events
    now = datetime.utcnow()
    weekday = now.weekday()
    hour = now.hour
    
    result = {
        "high_impact_window": False,
        "upcoming_events": [],
        "market_moving_risk": "LOW",
        "avoid_trading_window": False
    }
    
    # FOMC typically 2pm ET (19:00 UTC) on Wednesdays
    if weekday == 2 and 18 <= hour <= 21:
        result["high_impact_window"] = True
        result["upcoming_events"].append("FOMC_RATE_DECISION")
        result["market_moving_risk"] = "EXTREME"
        result["avoid_trading_window"] = True
    
    # NFP first Friday of month at 8:30am ET (13:30 UTC)
    if weekday == 4 and now.day <= 7 and 12 <= hour <= 15:
        result["high_impact_window"] = True
        result["upcoming_events"].append("NFP_EMPLOYMENT")
        result["market_moving_risk"] = "HIGH"
    
    # CPI typically mid-month
    if 10 <= now.day <= 15 and 12 <= hour <= 15:
        result["upcoming_events"].append("POSSIBLE_CPI_RELEASE")
        result["market_moving_risk"] = "MEDIUM"
    
    # US market open volatility (9:30-10:30 ET = 14:30-15:30 UTC)
    if 14 <= hour <= 15:
        result["upcoming_events"].append("US_MARKET_OPEN_VOLATILITY")
        if result["market_moving_risk"] == "LOW":
            result["market_moving_risk"] = "MEDIUM"
    
    return result


def _trend_channel_features(closes: np.ndarray, current: float) -> dict:
    if closes is None or len(closes) < 40 or current == 0:
        return {"slope": None, "position": None, "width_pct": None}

    y = closes[-120:] if len(closes) >= 120 else closes
    x = np.arange(len(y), dtype=float)
    try:
        slope, intercept = np.polyfit(x, y.astype(float), 1)
        fitted = slope * x + intercept
        residual = y - fitted
        resid_std = float(np.std(residual)) if len(residual) else 0.0
        center = float(fitted[-1])
        width = max(1e-9, 2.0 * resid_std)
        pos = float((current - center) / width)
        return {
            "slope": float(slope),
            "position": pos,
            "width_pct": float((width / current) * 100.0) if current else None,
        }
    except Exception:
        return {"slope": None, "position": None, "width_pct": None}


async def build_context_pack(symbol: str) -> Dict[str, Any]:
    normalized_symbol = "NDX.INDX" if (symbol or "").upper() in ["NASDAQ", "NDX.INDX", "NDX"] else (symbol or "").upper()

    ml_prediction = await get_ml_prediction(normalized_symbol)

    candles = await fetch_eod_candles(normalized_symbol, limit=260)
    live_price = await fetch_latest_price(normalized_symbol)

    closes = np.array([c["close"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    highs = np.array([c["high"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    lows = np.array([c["low"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    volumes = np.array([c.get("volume", 0) for c in candles], dtype=float) if candles else np.array([], dtype=float)

    current_price = float(live_price) if live_price is not None else (float(closes[-1]) if len(closes) else 0.0)

    ta = _compute_technical_indicators(closes, highs, lows, volumes) if len(closes) else {"close": 0.0}
    ta["close"] = current_price

    ta_snapshot = await compute_ta_snapshot(normalized_symbol)

    ema20 = float(ta.get("ema_20", 0.0))
    ema50 = float(ta.get("ema_50", 0.0))
    ema200 = float(ta.get("ema_200", 0.0))

    distances = {
        "ema20_pct": _pct_distance(current_price, ema20),
        "ema50_pct": _pct_distance(current_price, ema50),
        "ema200_pct": _pct_distance(current_price, ema200),
        "boll_zscore": float(ta.get("boll_zscore", 0.0)),
        "atr_pct": float(ta.get("atr_pct", 0.0)),
    }

    supports = ta_snapshot.get("supports", []) or []
    resistances = ta_snapshot.get("resistances", []) or []
    nearest_support = _nearest_level(current_price, supports, "support")
    nearest_resistance = _nearest_level(current_price, resistances, "resistance")

    vol_last = float(volumes[-1]) if len(volumes) else 0.0
    vol_avg20 = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else (float(np.mean(volumes)) if len(volumes) else 0.0)
    vol_ratio = float(vol_last / vol_avg20) if vol_avg20 > 0 else None

    channel = _trend_channel_features(closes, current_price)
    
    # PROFESSIONAL FEATURES - Divergence, Market Structure, Liquidity, Economic Calendar
    # Calculate RSI and MACD arrays for divergence detection
    rsi_array = None
    macd_array = None
    if len(closes) >= 20:
        try:
            # Simple RSI calculation for array
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.convolve(gains, np.ones(14)/14, mode='valid')
            avg_loss = np.convolve(losses, np.ones(14)/14, mode='valid')
            rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
            rsi_array = 100 - (100 / (1 + rs))
            
            # MACD histogram array
            ema12 = np.convolve(closes, np.ones(12)/12, mode='valid')
            ema26 = np.convolve(closes, np.ones(26)/26, mode='valid')
            min_len = min(len(ema12), len(ema26))
            macd_array = ema12[-min_len:] - ema26[-min_len:]
        except Exception:
            pass
    
    divergences = _detect_divergences(closes, rsi_array, macd_array)
    market_structure = _get_market_structure(closes, highs, lows)
    liquidity_zones = _get_liquidity_zones(highs, lows, current_price)
    economic_calendar = _get_economic_calendar_flags()

    macro_symbols = {
        "dxy": "DXY.INDX",
        "vix": "VIX.INDX",
        "usdtry": "USDTRY",
    }
    macro = {}
    for k, sym in macro_symbols.items():
        price = await fetch_latest_price(sym)
        macro[k] = {"symbol": sym, "price": float(price) if price is not None else None}

    news_symbols = ["XAUUSD", "GOLD", "DXY", "USD"] if "XAU" in normalized_symbol else ["NDX", "NASDAQ", "VIX", "DXY"]
    headlines = await fetch_marketaux_headlines(news_symbols)

    prediction_dict = {
        "symbol": ml_prediction.symbol,
        "direction": ml_prediction.direction,
        "confidence": ml_prediction.confidence,
        "probability_up": ml_prediction.probability_up,
        "probability_down": ml_prediction.probability_down,
        "target_pips": ml_prediction.target_pips,
        "stop_pips": ml_prediction.stop_pips,
        "risk_reward": ml_prediction.risk_reward,
        "entry_price": ml_prediction.entry_price,
        "target_price": ml_prediction.target_price,
        "stop_price": ml_prediction.stop_price,
        "technical_score": ml_prediction.technical_score,
        "momentum_score": ml_prediction.momentum_score,
        "trend_score": ml_prediction.trend_score,
        "volatility_regime": ml_prediction.volatility_regime,
        "reasoning": ml_prediction.reasoning,
        "key_levels": ml_prediction.key_levels,
    }

    # Session context (market hours)
    now_utc = datetime.utcnow()
    hour_utc = now_utc.hour
    session = "closed"
    if 13 <= hour_utc < 21:  # US market hours (9:30-16:00 EST = 14:30-21:00 UTC)
        session = "us_open"
    elif 8 <= hour_utc < 16:  # European hours
        session = "europe_open"
    elif 0 <= hour_utc < 8:  # Asian hours
        session = "asia_open"
    
    # Additional TA metrics for Claude
    atr_value = float(ta.get("atr_14", 0.0))
    atr_pct = float(ta.get("atr_pct", 0.0))
    boll_width = float(ta.get("boll_width", 0.0))
    adx = float(ta.get("adx", 0.0))
    rsi = float(ta.get("rsi_14", 50.0))
    macd_hist = float(ta.get("macd_hist", 0.0))
    stoch_k = float(ta.get("stoch_k", 50.0))
    
    # Volatility assessment
    vix_price = macro.get("vix", {}).get("price")
    volatility_level = "NORMAL"
    if vix_price and vix_price > 20:
        volatility_level = "HIGH"
    elif vix_price and vix_price < 15:
        volatility_level = "LOW"
    elif boll_width > 5 or atr_pct > 2:
        volatility_level = "HIGH"
    elif boll_width < 3 and atr_pct < 1:
        volatility_level = "LOW"
    
    # Volume assessment
    volume_status = "NORMAL"
    if vol_ratio and vol_ratio > 1.2:
        volume_status = "STRONG"
    elif vol_ratio and vol_ratio < 0.8:
        volume_status = "WEAK"

    return {
        "symbol": normalized_symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "context_pack_version": CONTEXT_PACK_VERSION,
        "ml_prediction": prediction_dict,
        "ta": ta,
        "ta_snapshot": ta_snapshot,
        "ta_summary": {
            "atr": atr_value,
            "atr_pct": atr_pct,
            "bollinger_width": boll_width,
            "adx": adx,
            "rsi": rsi,
            "macd_hist": macd_hist,
            "stoch_k": stoch_k,
        },
        "distances": distances,
        "levels": {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
        },
        "volume": {
            "last": vol_last,
            "avg20": vol_avg20,
            "ratio": vol_ratio,
            "status": volume_status,
        },
        "volatility": {
            "level": volatility_level,
            "vix": vix_price,
            "bollinger_width": boll_width,
            "atr_pct": atr_pct,
        },
        "trend_channel": channel,
        "session": {
            "current": session,
            "hour_utc": hour_utc,
        },
        "macro": macro,
        "news": {"headlines": headlines, "count": len(headlines)},
        # PROFESSIONAL FEATURES
        "divergences": divergences,
        "market_structure": market_structure,
        "liquidity_zones": liquidity_zones,
        "economic_calendar": economic_calendar,
    }


def _fallback_detailed_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback analysis when Claude API is unavailable - uses new v2.0 schema."""
    ml = context.get("ml_prediction", {}) or {}
    levels = context.get("levels", {}) or {}
    distances = context.get("distances", {}) or {}
    volume = context.get("volume", {}) or {}
    volatility = context.get("volatility", {}) or {}
    ta_summary = context.get("ta_summary", {}) or {}

    direction = ml.get("direction", "HOLD")
    confidence = float(ml.get("confidence", 50.0))
    
    # Calculate basic scores based on ML
    long_score = 0
    short_score = 0
    if direction == "BUY":
        long_score = min(30, int(confidence * 0.3))
    elif direction == "SELL":
        short_score = min(30, int(confidence * 0.3))
    
    # Add trend score
    trend = (context.get("ta_snapshot") or {}).get("trend", "NEUTRAL")
    if trend == "BULLISH":
        long_score += 20
    elif trend == "BEARISH":
        short_score += 20
    
    # Volume status
    vol_status = volume.get("status", "NORMAL")
    vol_confirm = 5 if vol_status == "STRONG" else 0
    
    # Position sizing based on conditions
    position_size = "SMALL"
    if direction == "HOLD":
        position_size = "NO_TRADE"
    elif volatility.get("level") == "HIGH" and vol_status == "WEAK":
        position_size = "NO_TRADE"
    
    return {
        "data_quality": {
            "score": 60,
            "missing_fields": ["claude_analysis"],
            "notes": ["Fallback mode - Claude API unavailable"]
        },
        "market_regime": {
            "trend": trend.upper() if trend else "NEUTRAL",
            "volatility": volatility.get("level", "NORMAL"),
            "liquidity": vol_status,
            "evidence": [f"Based on ta_snapshot trend: {trend}"]
        },
        "scores": {
            "long_score": long_score + vol_confirm,
            "short_score": short_score,
            "score_breakdown": {
                "ml_alignment": min(30, int(confidence * 0.3)) if direction == "BUY" else 0,
                "trend_alignment": 20 if (direction == "BUY" and trend == "BULLISH") or (direction == "SELL" and trend == "BEARISH") else 0,
                "momentum": 0,
                "volatility_fit": 5 if volatility.get("level") != "HIGH" else 0,
                "volume_confirm": vol_confirm,
                "sr_proximity": 0
            },
            "top_drivers": [f"ML prediction: {direction} ({confidence:.0f}%)", f"Trend: {trend}", f"Volume: {vol_status}"],
            "contradictions": []
        },
        "final_decision": direction,
        "confidence": float(np.clip(confidence * 0.85, 0.0, 100.0)),
        "thesis": {
            "summary": f"Fallback analysis: ML suggests {direction} with {confidence:.0f}% confidence.",
            "bull_case": [f"ML confidence: {confidence:.0f}%"] if direction == "BUY" else [],
            "bear_case": [f"ML confidence: {confidence:.0f}%"] if direction == "SELL" else [],
            "why_this_decision": "Claude API unavailable - using ML prediction with reduced confidence"
        },
        "key_levels": {
            "nearest_support": {
                "price": (levels.get("nearest_support") or {}).get("price"),
                "distance_pct": (levels.get("nearest_support") or {}).get("distance_pct"),
            },
            "nearest_resistance": {
                "price": (levels.get("nearest_resistance") or {}).get("price"),
                "distance_pct": (levels.get("nearest_resistance") or {}).get("distance_pct"),
            },
            "ema_distances_pct": {
                "ema20": distances.get("ema20_pct"),
                "ema50": distances.get("ema50_pct"),
                "ema200": distances.get("ema200_pct"),
            },
        },
        "macro_view": {
            "dxy": {"price": ((context.get("macro") or {}).get("dxy") or {}).get("price"), "impact": "unknown"},
            "vix": {"price": ((context.get("macro") or {}).get("vix") or {}).get("price"), "impact": "unknown"},
            "notes": []
        },
        "risk_management": {
            "position_size": position_size,
            "entry": ml.get("entry_price") or "needs_price",
            "stop_loss": ml.get("stop_price") or "needs_levels",
            "take_profit": ml.get("target_price") or "needs_levels",
            "risk_reward_ratio": ml.get("risk_reward"),
            "invalidation": "Price breaking key EMA levels or support/resistance",
            "size_rationale": "Reduced size due to fallback mode - no Claude confirmation"
        },
        "red_flags": ["Claude API unavailable - analysis quality reduced"],
        "gating_applied": ["fallback_mode"],
        "next_data_needed": ["Claude API connection for full analysis"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_used": "fallback",
        "engine_version": ANALYSIS_ENGINE_VERSION
    }


async def analyze_detailed_with_claude(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        return _fallback_detailed_analysis(context)

    api_key = settings.anthropic_api_key
    if not api_key:
        return _fallback_detailed_analysis(context)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""Analyze the following context pack and return ONLY valid JSON matching the schema in your instructions.

Context Pack (version {context.get('context_pack_version', '2.0.0')}):
{json.dumps(context, ensure_ascii=False, indent=2)}

Remember:
1. Follow the 6-step decision framework exactly
2. Calculate long_score and short_score transparently
3. Apply risk gating rules
4. Output ONLY the JSON response, no additional text"""

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=DETAILED_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        response_text = message.content[0].text if getattr(message, "content", None) else ""

        parsed = _parse_claude_json(response_text)
        if parsed is not None:
            parsed["timestamp"] = parsed.get("timestamp") or (datetime.utcnow().isoformat() + "Z")
            parsed["model_used"] = parsed.get("model_used") or CLAUDE_MODEL
            parsed["engine_version"] = ANALYSIS_ENGINE_VERSION
            return parsed

        # JSON parse failed - return partial response
        return {
            "data_quality": {"score": 40, "missing_fields": ["valid_json"], "notes": ["Claude response was not valid JSON"]},
            "final_decision": context.get("ml_prediction", {}).get("direction", "HOLD"),
            "confidence": float(context.get("ml_prediction", {}).get("confidence", 50.0)) * 0.7,
            "thesis": {"summary": response_text[:1000], "bull_case": [], "bear_case": [], "why_this_decision": "JSON parse failed"},
            "scores": {"long_score": 0, "short_score": 0, "top_drivers": [], "contradictions": ["JSON parse error"]},
            "market_regime": {"trend": "UNKNOWN", "volatility": "UNKNOWN", "liquidity": "UNKNOWN", "evidence": []},
            "key_levels": {},
            "macro_view": {"dxy": {}, "vix": {}, "notes": []},
            "risk_management": {"position_size": "NO_TRADE", "entry": "needs_price", "stop_loss": "needs_levels", "take_profit": "needs_levels", "invalidation": "JSON parse failed", "size_rationale": "Cannot trade without valid analysis"},
            "red_flags": ["Claude response was not valid JSON - raw response logged"],
            "gating_applied": ["json_parse_failure"],
            "next_data_needed": ["Valid JSON response from Claude"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_used": CLAUDE_MODEL,
            "engine_version": ANALYSIS_ENGINE_VERSION,
            "raw_response_preview": response_text[:500]
        }
    except Exception as e:
        logger.error(f"Claude detailed analysis error: {e}")
        # Return fallback with actual error message for debugging
        fallback = _fallback_detailed_analysis(context)
        fallback["red_flags"] = [f"Claude API error: {str(e)}"]
        return fallback


async def get_detailed_analysis(symbol: str, log_to_db: bool = True) -> Dict[str, Any]:
    context = await build_context_pack(symbol)
    analysis = await analyze_detailed_with_claude(context)
    
    if log_to_db:
        try:
            from services.prediction_logger import log_prediction
            await log_prediction(
                symbol=context.get("symbol", symbol),
                context=context,
                analysis=analysis,
                timeframe="1d"
            )
        except Exception as e:
            logger.warning(f"Failed to log prediction to database: {e}")
    
    return {"symbol": context.get("symbol", symbol), "context": context, "analysis": analysis}
