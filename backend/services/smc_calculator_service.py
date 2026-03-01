"""
SMC (Smart Money Concepts) Calculator Service
==============================================
Rule-based technical calculation for Order Blocks, FVG, Liquidity Pools.
NO DeepSeek/AI - Pure geometric calculation for instant results.
"""

import numpy as np
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
from datetime import datetime


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
class SMCAnalysis:
    market_structure: Dict
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    liquidity_pools: List[LiquidityPool]
    breaker_blocks: List[BreakerBlock]
    bias: Dict


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
                    created_at=datetime.utcnow().isoformat()
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
                    created_at=datetime.utcnow().isoformat()
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
    
    # CHoCH detection (simplified)
    choch = None
    if trend == "bullish" and last_sl < prev_sl:
        choch = {"direction": "down", "price": last_sl, "confirmed": False}
    elif trend == "bearish" and last_sh > prev_sh:
        choch = {"direction": "up", "price": last_sh, "confirmed": False}
    
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
        "timestamp": datetime.utcnow().isoformat(),
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
        "candles_analyzed": len(candles)
    }
