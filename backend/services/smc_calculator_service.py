"""
SMC (Smart Money Concepts) Calculator Service
==============================================
Rule-based technical calculation for Order Blocks, FVG, Liquidity Pools.
NO DeepSeek/AI - Pure geometric calculation for instant results.
"""

import numpy as np
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


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


def detect_order_blocks(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    swing_highs: List[Dict],
    swing_lows: List[Dict]
) -> List[OrderBlock]:
    """
    Detect Order Blocks based on price action:
    - Bullish OB: Bearish candle followed by strong bullish move
    - Bearish OB: Bullish candle followed by strong bearish move
    """
    order_blocks = []
    
    if len(closes) < 10:
        return order_blocks
    
    # Look for OBs in last 50 candles
    lookback = min(50, len(closes) - 1)
    
    for i in range(len(closes) - lookback, len(closes) - 2):
        if i < 1:
            continue
            
        current_candle_bullish = closes[i] > opens[i]
        prev_candle_bearish = closes[i-1] < opens[i-1]
        next_candle_bullish = closes[i+1] > opens[i+1]
        
        # Bullish Order Block: Bearish candle before strong bullish move
        if prev_candle_bearish and current_candle_bullish and next_candle_bullish:
            body_size = abs(closes[i] - opens[i])
            avg_body = np.mean(np.abs(closes[max(0,i-10):i] - opens[max(0,i-10):i]))
            
            if body_size > avg_body * 0.5:  # Significant body
                strength = min(10, max(1, int((body_size / avg_body) * 5)))
                
                # Check if tested
                status = "fresh"
                for j in range(i+1, len(closes)):
                    if lows[j] < lows[i]:
                        status = "tested"
                        break
                
                order_blocks.append(OrderBlock(
                    type="bullish",
                    price_high=float(highs[i]),
                    price_low=float(lows[i]),
                    strength=strength,
                    status=status,
                    timeframe="H1",
                    created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                ))
        
        # Bearish Order Block: Bullish candle before strong bearish move
        prev_candle_bullish = closes[i-1] > opens[i-1]
        current_candle_bearish = closes[i] < opens[i]
        next_candle_bearish = closes[i+1] < opens[i+1]
        
        if prev_candle_bullish and current_candle_bearish and next_candle_bearish:
            body_size = abs(opens[i] - closes[i])
            avg_body = np.mean(np.abs(closes[max(0,i-10):i] - opens[max(0,i-10):i]))
            
            if body_size > avg_body * 0.5:
                strength = min(10, max(1, int((body_size / avg_body) * 5)))
                
                status = "fresh"
                for j in range(i+1, len(closes)):
                    if highs[j] > highs[i]:
                        status = "tested"
                        break
                
                order_blocks.append(OrderBlock(
                    type="bearish",
                    price_high=float(highs[i]),
                    price_low=float(lows[i]),
                    strength=strength,
                    status=status,
                    timeframe="H1",
                    created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                ))
    
    # Sort by strength and recency
    order_blocks.sort(key=lambda x: (x.strength, x.status == "fresh"), reverse=True)
    return order_blocks[:5]  # Return top 5


def detect_fair_value_gaps(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray
) -> List[FairValueGap]:
    """
    Detect Fair Value Gaps (3-candle pattern):
    - Bullish FVG: Low[i] > High[i-2] (gap up)
    - Bearish FVG: High[i] < Low[i-2] (gap down)
    """
    fvgs = []
    
    if len(closes) < 5:
        return fvgs
    
    for i in range(2, len(closes)):
        # Bullish FVG
        if lows[i] > highs[i-2]:
            gap_size = lows[i] - highs[i-2]
            
            # Calculate fill percentage
            current_price = closes[-1]
            if current_price <= highs[i-2]:
                fill_pct = 100.0
                status = "filled"
            elif current_price >= lows[i]:
                fill_pct = 0.0
                status = "open"
            else:
                fill_pct = ((highs[i-2] - current_price) / gap_size) * 100
                status = "partial"
            
            fvgs.append(FairValueGap(
                direction="bullish",
                high=float(lows[i]),
                low=float(highs[i-2]),
                fill_pct=round(fill_pct, 1),
                status=status
            ))
        
        # Bearish FVG
        elif highs[i] < lows[i-2]:
            gap_size = lows[i-2] - highs[i]
            
            current_price = closes[-1]
            if current_price >= lows[i-2]:
                fill_pct = 100.0
                status = "filled"
            elif current_price <= highs[i]:
                fill_pct = 0.0
                status = "open"
            else:
                fill_pct = ((current_price - highs[i]) / gap_size) * 100
                status = "partial"
            
            fvgs.append(FairValueGap(
                direction="bearish",
                high=float(lows[i-2]),
                low=float(highs[i]),
                fill_pct=round(fill_pct, 1),
                status=status
            ))
    
    # Return only open/partial FVGs, sorted by recency
    active_fvgs = [f for f in fvgs if f.status in ["open", "partial"]]
    return active_fvgs[-3:]  # Last 3 active FVGs


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


def calculate_bias(
    order_blocks: List[OrderBlock],
    fvgs: List[FairValueGap],
    liquidity_pools: List[LiquidityPool],
    market_structure: Dict,
    current_price: float
) -> Dict:
    """
    Calculate overall bias based on SMC elements.
    """
    score = 0
    factors = []
    
    # Trend contribution
    if market_structure["current_trend"] == "bullish":
        score += 20
        factors.append("Bullish structure")
    elif market_structure["current_trend"] == "bearish":
        score -= 20
        factors.append("Bearish structure")
    
    # Order Blocks
    fresh_bullish_obs = [ob for ob in order_blocks if ob.type == "bullish" and ob.status == "fresh"]
    fresh_bearish_obs = [ob for ob in order_blocks if ob.type == "bearish" and ob.status == "fresh"]
    
    if fresh_bullish_obs and current_price > fresh_bullish_obs[0].price_low:
        score += 25
        factors.append(f"Bullish OB at {fresh_bullish_obs[0].price_low}")
    
    if fresh_bearish_obs and current_price < fresh_bearish_obs[0].price_high:
        score -= 25
        factors.append(f"Bearish OB at {fresh_bearish_obs[0].price_high}")
    
    # FVGs
    open_bullish_fvgs = [f for f in fvgs if f.direction == "bullish" and f.status == "open"]
    open_bearish_fvgs = [f for f in fvgs if f.direction == "bearish" and f.status == "open"]
    
    if open_bullish_fvgs:
        score += 15
        factors.append("Open bullish FVG")
    
    if open_bearish_fvgs:
        score -= 15
        factors.append("Open bearish FVG")
    
    # Liquidity
    unswept_buy = [p for p in liquidity_pools if p.type == "buy_side" and not p.swept]
    unswept_sell = [p for p in liquidity_pools if p.type == "sell_side" and not p.swept]
    
    if unswept_buy:
        score += 10
        factors.append("Buy-side liquidity below")
    
    if unswept_sell:
        score -= 10
        factors.append("Sell-side liquidity above")
    
    # Determine direction
    if score > 30:
        direction = "bullish"
        confidence = min(90, 50 + score)
        key_level = min([ob.price_low for ob in fresh_bullish_obs], default=current_price * 0.99)
        invalidation = min([p.price for p in unswept_buy], default=current_price * 0.97)
    elif score < -30:
        direction = "bearish"
        confidence = min(90, 50 - score)
        key_level = max([ob.price_high for ob in fresh_bearish_obs], default=current_price * 1.01)
        invalidation = max([p.price for p in unswept_sell], default=current_price * 1.03)
    else:
        direction = "neutral"
        confidence = 40
        key_level = current_price
        invalidation = current_price * 0.95 if score > 0 else current_price * 1.05
    
    return {
        "direction": direction,
        "confidence": confidence,
        "key_level_to_watch": round(key_level, 2),
        "invalidation": round(invalidation, 2),
        "narrative": " | ".join(factors) if factors else "No clear SMC setup",
        "score": score
    }


async def calculate_smc(symbol: str, candles: list) -> dict:
    """
    Main entry point - Calculate SMC analysis from candle data.
    
    Args:
        symbol: Trading symbol
        candles: List of candle dicts with open, high, low, close, volume
    
    Returns:
        SMCAnalysis as dict (JSON serializable)
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
    
    # Convert to numpy arrays
    opens = np.array([c["open"] for c in candles])
    highs = np.array([c["high"] for c in candles])
    lows = np.array([c["low"] for c in candles])
    closes = np.array([c["close"] for c in candles])
    volumes = np.array([c.get("volume", 0) for c in candles])
    
    current_price = float(closes[-1])
    
    # Find swing points
    swing_highs, swing_lows = find_swing_points(highs, lows, closes)
    
    # Detect SMC elements
    order_blocks = detect_order_blocks(opens, highs, lows, closes, volumes, swing_highs, swing_lows)
    fvgs = detect_fair_value_gaps(highs, lows, closes)
    liquidity_pools = detect_liquidity_pools(highs, lows, swing_highs, swing_lows, current_price)
    breaker_blocks = detect_breaker_blocks(highs, lows, closes, swing_highs, swing_lows)
    
    # Determine structure and bias
    market_structure = determine_market_structure(swing_highs, swing_lows, current_price)
    bias = calculate_bias(order_blocks, fvgs, liquidity_pools, market_structure, current_price)
    
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


async def calculate_smc_with_gaps(symbol: str, candles: list) -> dict:
    """
    Enhanced SMC analysis with Gap-Aware optimizations for EOD data.
    """
    result = await calculate_smc(symbol, candles)
    
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
