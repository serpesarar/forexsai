"""
SMC (Smart Money Concepts) Calculator Service
==============================================
Legacy-shaped SMC facade over the canonical v2 engine.

2026-07-08 consolidation: OB / FVG / trend / bias now derive from
``order_block_detector_v2.MarketStructureAnalyzer`` (the single canonical SMC
engine). This module only adapts the v2 output to the legacy response shape
consumed by routers/deepseek_analysis.py and services/meta_analysis_engine.py.
Liquidity pools, breaker blocks and the daily-gap analysis are independent of
the old buggy OB/FVG detectors and are kept as-is.
NO DeepSeek/AI - Pure geometric calculation for instant results.
"""

import logging
import numpy as np
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from order_block_detector_v2 import (
    Candle as V2Candle,
    MarketStructure as V2MarketStructure,
    MarketStructureAnalyzer,
)

logger = logging.getLogger(__name__)


@dataclass
class OrderBlock:
    type: Literal["bullish", "bearish"]
    price_high: float
    price_low: float
    strength: int  # 1-10
    status: Literal["fresh", "tested", "mitigated"]
    timeframe: str
    created_at: str


@dataclass
class FairValueGap:
    direction: Literal["bullish", "bearish"]
    high: float
    low: float
    fill_pct: float
    status: Literal["open", "partial", "filled"]


@dataclass
class LiquidityPool:
    type: Literal["buy_side", "sell_side"]
    price: float
    strength: Literal["weak", "moderate", "strong"]
    swept: bool


@dataclass
class BreakerBlock:
    type: Literal["bullish", "bearish"]
    price_high: float
    price_low: float
    status: Literal["active", "tested"]


@dataclass
class GapInfo:
    date: str
    prev_close: float
    today_open: float
    size: float
    size_pct: float
    atr_multiple: float
    classification: str  # EXTREME_GAP, NORMAL_GAP, MINIMAL
    direction: str  # BULLISH, BEARISH
    fill_probability: float
    is_fvg: bool
    strength: str  # HIGH, MEDIUM, LOW


@dataclass
class SMCAnalysis:
    market_structure: Dict
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    liquidity_pools: List[LiquidityPool]
    breaker_blocks: List[BreakerBlock]
    bias: Dict
    gaps: List[GapInfo]  # NEW: Gap analysis


def find_swing_points(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 5) -> tuple:
    """Find swing highs and lows using fractal method."""
    swing_highs = []
    swing_lows = []
    
    for i in range(period, len(closes) - period):
        # Swing High: Current high is highest in period
        if highs[i] == max(highs[i-period:i+period+1]):
            swing_highs.append({"index": i, "price": float(highs[i])})
        
        # Swing Low: Current low is lowest in period  
        if lows[i] == min(lows[i-period:i+period+1]):
            swing_lows.append({"index": i, "price": float(lows[i])})
    
    return swing_highs, swing_lows


def _to_v2_candles(candles: list) -> List[V2Candle]:
    """Convert legacy candle dicts to v2 ``Candle`` dataclasses.

    Handles ``timestamp`` in seconds or milliseconds, ``time`` aliases and
    missing timestamps (falls back to the candle index to preserve order).
    """
    v2_candles: List[V2Candle] = []
    for i, c in enumerate(candles):
        ts = c.get("timestamp", c.get("time", c.get("t")))
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except ValueError:
                ts = None
        if isinstance(ts, (int, float)):
            ts = float(ts)
            if ts > 1e12:  # milliseconds → seconds
                ts = ts / 1000.0
        else:
            ts = float(i)
        v2_candles.append(V2Candle(
            timestamp=ts,
            open=float(c["open"]),
            high=float(c["high"]),
            low=float(c["low"]),
            close=float(c["close"]),
            volume=float(c.get("volume", 0) or 0),
        ))
    return v2_candles


def _map_v2_order_blocks(structure: V2MarketStructure, timeframe: str) -> List[OrderBlock]:
    """Map v2 OrderBlocks (score 0-100, tested/mitigated) to legacy shape."""
    mapped: List[OrderBlock] = []
    for ob in structure.ob_list[:5]:
        strength = max(1, min(10, round(ob.score / 10)))
        status = "tested" if (ob.tested or ob.mitigated) else "fresh"
        mapped.append(OrderBlock(
            type=ob.type,
            price_high=float(ob.zone_high),
            price_low=float(ob.zone_low),
            strength=int(strength),
            status=status,
            timeframe=timeframe,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        ))
    return mapped


def _map_v2_fvgs(structure: V2MarketStructure) -> List[FairValueGap]:
    """Map v2 FVGs (fill_percentage/filled) to legacy shape, active only."""
    mapped: List[FairValueGap] = []
    for fvg in structure.fvg_list:
        if fvg.filled:
            status = "filled"
        elif fvg.fill_percentage <= 0:
            status = "open"
        else:
            status = "partial"
        mapped.append(FairValueGap(
            direction=fvg.direction,
            high=float(fvg.high),
            low=float(fvg.low),
            fill_pct=round(float(fvg.fill_percentage), 1),
            status=status,
        ))
    # Legacy contract: only open/partial FVGs, last 3 by recency
    active = [f for f in mapped if f.status in ("open", "partial")]
    return active[-3:]


def _map_v2_market_structure(structure: V2MarketStructure, current_price: float) -> Dict:
    """Build the legacy market_structure dict from the v2 analysis."""
    swing_highs = [s for s in structure.swing_list if s.type == "high"]
    swing_lows = [s for s in structure.swing_list if s.type == "low"]

    bos = None
    if structure.bos_list:
        last = structure.bos_list[-1]
        bos = {
            "direction": "up" if last.type == "bullish" else "down",
            "price": round(float(last.price), 2),
            "confirmed": bool(last.confirmation),
        }

    choch = None
    if structure.choch_list:
        last = structure.choch_list[-1]
        choch = {
            "direction": "up" if last.type == "bullish" else "down",
            "price": round(float(last.price), 2),
            "confirmed": True,
        }

    return {
        "current_trend": structure.trend,
        "last_bos": bos,
        "last_choch": choch,
        "swing_high": round(float(swing_highs[-1].price), 2) if swing_highs else round(current_price * 1.01, 2),
        "swing_low": round(float(swing_lows[-1].price), 2) if swing_lows else round(current_price * 0.99, 2),
    }


def detect_liquidity_pools(
    highs: np.ndarray,
    lows: np.ndarray,
    swing_highs: List[Dict],
    swing_lows: List[Dict],
    current_price: float
) -> List[LiquidityPool]:
    """
    Detect liquidity pools around equal highs/lows.
    """
    pools = []
    
    # Group swing highs by price proximity
    tolerance = current_price * 0.001  # 0.1%
    
    # Find equal highs (sell-side liquidity)
    high_clusters = []
    for i, sh in enumerate(swing_highs):
        clustered = False
        for cluster in high_clusters:
            if abs(sh["price"] - cluster["price"]) < tolerance:
                cluster["count"] += 1
                cluster["prices"].append(sh["price"])
                clustered = True
                break
        if not clustered:
            high_clusters.append({"price": sh["price"], "count": 1, "prices": [sh["price"]]})
    
    # Find equal lows (buy-side liquidity)
    low_clusters = []
    for i, sl in enumerate(swing_lows):
        clustered = False
        for cluster in low_clusters:
            if abs(sl["price"] - cluster["price"]) < tolerance:
                cluster["count"] += 1
                cluster["prices"].append(sl["price"])
                clustered = True
                break
        if not clustered:
            low_clusters.append({"price": sl["price"], "count": 1, "prices": [sl["price"]]})
    
    # Create liquidity pools from clusters with 2+ touches
    for cluster in high_clusters:
        if cluster["count"] >= 2:
            avg_price = np.mean(cluster["prices"])
            strength = "strong" if cluster["count"] >= 3 else "moderate"
            swept = current_price > avg_price * 1.002
            
            pools.append(LiquidityPool(
                type="sell_side",
                price=round(avg_price, 2),
                strength=strength,
                swept=swept
            ))
    
    for cluster in low_clusters:
        if cluster["count"] >= 2:
            avg_price = np.mean(cluster["prices"])
            strength = "strong" if cluster["count"] >= 3 else "moderate"
            swept = current_price < avg_price * 0.998
            
            pools.append(LiquidityPool(
                type="buy_side",
                price=round(avg_price, 2),
                strength=strength,
                swept=swept
            ))
    
    # Sort by proximity to current price
    pools.sort(key=lambda x: abs(x.price - current_price))
    return pools[:4]


def detect_breaker_blocks(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    swing_highs: List[Dict],
    swing_lows: List[Dict]
) -> List[BreakerBlock]:
    """
    Detect Breaker Blocks (failed Order Blocks that become support/resistance).
    """
    breakers = []
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return breakers
    
    # Bearish Breaker: Previous swing low broken, then retested as resistance
    for sl in swing_lows[-3:]:
        idx = sl["index"]
        if idx < len(closes) - 3:
            # Check if price broke below, then came back up
            broke_below = any(lows[i] < sl["price"] for i in range(idx+1, min(idx+10, len(closes))))
            retested = any(highs[i] > sl["price"] * 0.998 and closes[i] < sl["price"] 
                          for i in range(idx+1, len(closes)))
            
            if broke_below and retested:
                breakers.append(BreakerBlock(
                    type="bearish",
                    price_high=float(highs[idx]),
                    price_low=float(lows[idx]),
                    status="active"
                ))
    
    # Bullish Breaker: Previous swing high broken, then retested as support
    for sh in swing_highs[-3:]:
        idx = sh["index"]
        if idx < len(closes) - 3:
            broke_above = any(highs[i] > sh["price"] for i in range(idx+1, min(idx+10, len(closes))))
            retested = any(lows[i] < sh["price"] * 1.002 and closes[i] > sh["price"]
                          for i in range(idx+1, len(closes)))
            
            if broke_above and retested:
                breakers.append(BreakerBlock(
                    type="bullish",
                    price_high=float(highs[idx]),
                    price_low=float(lows[idx]),
                    status="active"
                ))
    
    return breakers[:3]


def determine_market_structure(
    swing_highs: List[Dict],
    swing_lows: List[Dict],
    current_price: float
) -> Dict:
    """
    Determine market structure (trend, BOS, CHoCH).
    """
    if not swing_highs or not swing_lows:
        return {
            "current_trend": "ranging",
            "last_bos": None,
            "last_choch": None,
            "swing_high": current_price * 1.01,
            "swing_low": current_price * 0.99
        }
    
    last_sh = swing_highs[-1]["price"]
    last_sl = swing_lows[-1]["price"]
    prev_sh = swing_highs[-2]["price"] if len(swing_highs) > 1 else last_sh
    prev_sl = swing_lows[-2]["price"] if len(swing_lows) > 1 else last_sl
    prior_sh = swing_highs[-3]["price"] if len(swing_highs) > 2 else prev_sh
    prior_sl = swing_lows[-3]["price"] if len(swing_lows) > 2 else prev_sl

    prior_trend = "ranging"
    if prev_sh > prior_sh and prev_sl > prior_sl:
        prior_trend = "bullish"
    elif prev_sh < prior_sh and prev_sl < prior_sl:
        prior_trend = "bearish"

    # Trend determination
    if last_sh > prev_sh and last_sl > prev_sl:
        trend = "bullish"
    elif last_sh < prev_sh and last_sl < prev_sl:
        trend = "bearish"
    else:
        trend = "ranging"
    
    # BOS detection
    bos = None
    if last_sh > prev_sh:
        bos = {"direction": "up", "price": last_sh, "confirmed": True}
    elif last_sl < prev_sl:
        bos = {"direction": "down", "price": last_sl, "confirmed": True}

    # CHoCH detection based on prior structure transition
    choch = None
    if prior_trend == "bullish" and last_sl < prev_sl:
        choch = {"direction": "down", "price": round(last_sl, 2), "confirmed": True}
    elif prior_trend == "bearish" and last_sh > prev_sh:
        choch = {"direction": "up", "price": round(last_sh, 2), "confirmed": True}

    return {
        "current_trend": trend,
        "last_bos": bos,
        "last_choch": choch,
        "swing_high": round(last_sh, 2),
        "swing_low": round(last_sl, 2)
    }


_PROJECTION_CONFIDENCE = {"high": 75, "medium": 60, "low": 45}


def calculate_bias(
    structure: V2MarketStructure,
    order_blocks: List[OrderBlock],
    current_price: float,
) -> Dict:
    """
    Calculate overall bias from the v2 engine's trend + TP/SL projection.

    Direction comes from v2 trend / projection agreement; confidence is scaled
    from the projection confidence (high=75, medium=60, low=45). Output field
    names/types match the legacy bias contract exactly.
    """
    trend = structure.trend
    projection = structure.projection
    factors: List[str] = []

    if trend == "bullish":
        factors.append("Bullish structure")
    elif trend == "bearish":
        factors.append("Bearish structure")

    if trend in ("bullish", "bearish"):
        direction = trend
        if projection and projection.direction == trend:
            confidence = _PROJECTION_CONFIDENCE.get(projection.confidence, 45)
            factors.append(f"Projection agrees ({projection.confidence} confidence)")
        elif projection:
            confidence = 45
            factors.append(f"Projection diverges ({projection.direction})")
        else:
            confidence = 50
    elif projection:
        # Ranging structure but a projection exists — weak directional lean
        direction = "neutral"
        confidence = 40
        factors.append(f"Ranging structure, {projection.direction} projection")
    else:
        direction = "neutral"
        confidence = 40

    # Signed score consistent with legacy semantics (positive=bullish)
    if direction == "bullish":
        score = confidence - 40
    elif direction == "bearish":
        score = -(confidence - 40)
    else:
        score = 0

    # Key level: nearest fresh OB in the bias direction, else projection entry zone
    fresh_bullish = [ob for ob in order_blocks if ob.type == "bullish" and ob.status == "fresh"]
    fresh_bearish = [ob for ob in order_blocks if ob.type == "bearish" and ob.status == "fresh"]

    if direction == "bullish":
        if fresh_bullish:
            key_level = min(ob.price_low for ob in fresh_bullish)
            factors.append(f"Bullish OB at {round(key_level, 2)}")
        elif projection and projection.direction == "bullish":
            key_level = projection.entry_zone_low
        else:
            key_level = current_price * 0.99
        invalidation = projection.stop_loss if (projection and projection.direction == "bullish") else current_price * 0.97
    elif direction == "bearish":
        if fresh_bearish:
            key_level = max(ob.price_high for ob in fresh_bearish)
            factors.append(f"Bearish OB at {round(key_level, 2)}")
        elif projection and projection.direction == "bearish":
            key_level = projection.entry_zone_high
        else:
            key_level = current_price * 1.01
        invalidation = projection.stop_loss if (projection and projection.direction == "bearish") else current_price * 1.03
    else:
        key_level = current_price
        invalidation = current_price * 0.95 if score > 0 else current_price * 1.05

    return {
        "direction": direction,
        "confidence": int(confidence),
        "key_level_to_watch": round(float(key_level), 2),
        "invalidation": round(float(invalidation), 2),
        "narrative": " | ".join(factors) if factors else "No clear SMC setup",
        "score": int(score),
    }


async def calculate_smc(symbol: str, candles: list, timeframe: str = "H1") -> dict:
    """
    Main entry point - Calculate SMC analysis from candle data.

    OB/FVG/trend/bias derive from the canonical v2 engine
    (order_block_detector_v2.MarketStructureAnalyzer); liquidity pools and
    breaker blocks keep their independent legacy detectors.

    Args:
        symbol: Trading symbol
        candles: List of candle dicts with open, high, low, close, volume

    Returns:
        SMCAnalysis as dict (JSON serializable, legacy shape)
    """
    if not candles or len(candles) < 20:
        return {
            "error": "Insufficient candle data",
            "market_structure": {"current_trend": "unknown"},
            "order_blocks": [],
            "fair_value_gaps": [],
            "liquidity_pools": [],
            "breaker_blocks": [],
            "bias": {"direction": "neutral", "confidence": 0}
        }

    # Convert to numpy arrays (liquidity/breaker detectors still need them)
    highs = np.array([c["high"] for c in candles])
    lows = np.array([c["low"] for c in candles])
    closes = np.array([c["close"] for c in candles])

    current_price = float(closes[-1])

    # Canonical v2 engine: swings, CHoCH/BOS, OB, FVG, trend, projection
    v2_candles = _to_v2_candles(candles)
    structure = MarketStructureAnalyzer.analyze(
        v2_candles,
        swing_period=3,
        symbol=symbol,
        min_displacement_atr=1.2,
        min_ob_score=0.0,
        volume_bonus=True,
    )

    order_blocks = _map_v2_order_blocks(structure, timeframe)
    fvgs = _map_v2_fvgs(structure)
    market_structure = _map_v2_market_structure(structure, current_price)
    bias = calculate_bias(structure, order_blocks, current_price)

    # Independent legacy detectors (not part of the buggy OB/FVG code)
    swing_highs, swing_lows = find_swing_points(highs, lows, closes)
    liquidity_pools = detect_liquidity_pools(highs, lows, swing_highs, swing_lows, current_price)
    breaker_blocks = detect_breaker_blocks(highs, lows, closes, swing_highs, swing_lows)
    
    # Convert to dict format
    return {
        "symbol": symbol,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "market_structure": market_structure,
        "order_blocks": [
            {
                "type": ob.type,
                "price_high": ob.price_high,
                "price_low": ob.price_low,
                "strength": ob.strength,
                "status": ob.status,
                "timeframe": ob.timeframe
            }
            for ob in order_blocks
        ],
        "fair_value_gaps": [
            {
                "direction": fvg.direction,
                "high": fvg.high,
                "low": fvg.low,
                "fill_pct": fvg.fill_pct,
                "status": fvg.status
            }
            for fvg in fvgs
        ],
        "liquidity_pools": [
            {
                "type": lp.type,
                "price": lp.price,
                "strength": lp.strength,
                "swept": lp.swept
            }
            for lp in liquidity_pools
        ],
        "breaker_blocks": [
            {
                "type": bb.type,
                "price_high": bb.price_high,
                "price_low": bb.price_low,
                "status": bb.status
            }
            for bb in breaker_blocks
        ],
        "bias": bias,
        "calculation_method": "rule_based",
        "candles_analyzed": len(candles),
        "gaps": []  # Will be populated by gap analysis
    }


def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> float:
    """Calculate Average True Range for gap classification."""
    if len(closes) < period + 1:
        return np.mean(highs - lows) if len(highs) > 0 else 1.0
    
    tr1 = highs[1:] - lows[1:]
    tr2 = np.abs(highs[1:] - closes[:-1])
    tr3 = np.abs(lows[1:] - closes[:-1])
    
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    return float(np.mean(tr[-period:]))


def calculate_gap_fill_probability(gap_size_pct: float, direction: str, symbol: str) -> float:
    """
    Calculate historical gap fill probability based on size.
    EOD data: ~70% of gaps fill within 3 days if < 1 ATR
    """
    # Smaller gaps fill more often
    if abs(gap_size_pct) < 0.5:
        return 0.85  # 85% fill rate for small gaps
    elif abs(gap_size_pct) < 1.0:
        return 0.70  # 70% fill rate for normal gaps
    elif abs(gap_size_pct) < 2.0:
        return 0.45  # 45% fill rate for large gaps
    else:
        return 0.20  # 20% fill rate for extreme gaps (trend continuation)


def analyze_gaps(
    candles: list,
    atr: float
) -> List[GapInfo]:
    """
    Analyze inter-day gaps in EOD data.
    Gap = Previous Close to Current Open (overnight session)
    
    CRITICAL: Never interpolate/adjust prices. Gaps are valuable information!
    """
    gaps = []
    
    if len(candles) < 3:
        return gaps
    
    for i in range(1, len(candles)):
        prev_candle = candles[i-1]
        current_candle = candles[i]
        
        prev_close = prev_candle["close"]
        today_open = current_candle["open"]
        
        # Calculate gap
        gap_size = today_open - prev_close
        gap_pct = (gap_size / prev_close) * 100
        
        # Skip minimal gaps (< 0.1%)
        if abs(gap_pct) < 0.1:
            continue
        
        # ATR multiple
        atr_multiple = abs(gap_size) / atr if atr > 0 else 0
        
        # Classification
        if atr_multiple > 2.0:
            classification = "EXTREME_GAP"
            strength = "HIGH"
        elif atr_multiple > 0.5:
            classification = "NORMAL_GAP"
            strength = "MEDIUM" if atr_multiple > 1.0 else "LOW"
        else:
            classification = "MINIMAL"
            strength = "LOW"
        
        direction = "BULLISH" if gap_size > 0 else "BEARISH"
        
        # Fill probability
        fill_prob = calculate_gap_fill_probability(gap_pct, direction, "")
        
        # Check if gap is filled (current price returned to prev_close area)
        current_low = current_candle["low"]
        current_high = current_candle["high"]
        
        is_filled = False
        if direction == "BULLISH" and current_low <= prev_close * 1.001:
            is_filled = True
        elif direction == "BEARISH" and current_high >= prev_close * 0.999:
            is_filled = True
        
        # Gap as FVG: If gap > 0.5 ATR, it's a "Strong FVG"
        is_fvg = atr_multiple > 0.5
        
        gaps.append(GapInfo(
            date=current_candle.get("date", f"Day {i}"),
            prev_close=round(prev_close, 2),
            today_open=round(today_open, 2),
            size=round(gap_size, 2),
            size_pct=round(gap_pct, 2),
            atr_multiple=round(atr_multiple, 2),
            classification=classification,
            direction=direction,
            fill_probability=round(fill_prob, 2),
            is_fvg=is_fvg,
            strength=strength
        ))
    
    # Return last 5 gaps
    return gaps[-5:]


def detect_gap_fvgs(
    candles: list,
    atr: float
) -> List[FairValueGap]:
    """
    Detect FVGs specifically from gaps (inter-day).
    In EOD data, gaps ARE the most significant FVGs.
    """
    gap_fvgs = []
    
    if len(candles) < 2:
        return gap_fvgs
    
    for i in range(1, len(candles)):
        prev_close = candles[i-1]["close"]
        today_open = candles[i]["open"]
        today_low = candles[i]["low"]
        today_high = candles[i]["high"]
        
        gap_size = abs(today_open - prev_close)
        gap_pct = (gap_size / prev_close) * 100
        
        # Only significant gaps (> 0.5 ATR) become FVGs
        if gap_pct < 0.5 or gap_size < atr * 0.5:
            continue
        
        direction = "bullish" if today_open > prev_close else "bearish"
        
        # Check fill status
        if direction == "bullish":
            if today_low <= prev_close:
                fill_pct = 100.0
                status = "filled"
            else:
                # Partial fill calculation
                fill_pct = ((today_open - today_low) / gap_size) * 100 if gap_size > 0 else 0
                status = "partial" if fill_pct > 10 else "open"
            
            gap_fvgs.append(FairValueGap(
                direction="bullish_gap",
                high=round(today_open, 2),
                low=round(prev_close, 2),
                fill_pct=round(fill_pct, 1),
                status=status
            ))
        else:
            if today_high >= prev_close:
                fill_pct = 100.0
                status = "filled"
            else:
                fill_pct = ((today_high - today_open) / gap_size) * 100 if gap_size > 0 else 0
                status = "partial" if fill_pct > 10 else "open"
            
            gap_fvgs.append(FairValueGap(
                direction="bearish_gap",
                high=round(prev_close, 2),
                low=round(today_open, 2),
                fill_pct=round(fill_pct, 1),
                status=status
            ))
    
    return gap_fvgs


async def calculate_smc_with_gaps(symbol: str, candles: list, timeframe: str = "D1") -> dict:
    """
    Enhanced SMC analysis with Gap-Aware optimizations for EOD data.
    """
    result = await calculate_smc(symbol, candles, timeframe=timeframe)
    
    if "error" in result:
        return result
    
    # Calculate ATR for gap classification
    highs = np.array([c["high"] for c in candles])
    lows = np.array([c["low"] for c in candles])
    closes = np.array([c["close"] for c in candles])
    atr = calculate_atr(highs, lows, closes)
    
    # Analyze gaps
    gaps = analyze_gaps(candles, atr)
    result["gaps"] = [
        {
            "date": g.date,
            "prev_close": g.prev_close,
            "today_open": g.today_open,
            "size": g.size,
            "size_pct": g.size_pct,
            "atr_multiple": g.atr_multiple,
            "classification": g.classification,
            "direction": g.direction,
            "fill_probability": g.fill_probability,
            "is_fvg": g.is_fvg,
            "strength": g.strength
        }
        for g in gaps
    ]
    
    # Add gap FVGs to existing FVGs
    gap_fvgs = detect_gap_fvgs(candles, atr)
    existing_fvgs = result.get("fair_value_gaps", [])
    
    # Mark gap FVGs as "strong"
    for gf in gap_fvgs:
        existing_fvgs.append({
            "direction": gf.direction,
            "high": gf.high,
            "low": gf.low,
            "fill_pct": gf.fill_pct,
            "status": gf.status,
            "type": "gap_fvg",
            "strength": "high"
        })
    
    result["fair_value_gaps"] = existing_fvgs[-6:]  # Keep last 6 (3 normal + 3 gap)
    result["atr_20"] = round(atr, 2)
    result["gap_analysis_enabled"] = True
    
    return result
