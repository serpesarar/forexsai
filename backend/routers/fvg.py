"""
FVG (Fair Value Gap) API Router
Endpoints for detecting and analyzing Fair Value Gaps.
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from fvg_detector import FVGDetector, FVGConfig, Candle, FairValueGap
from services.data_fetcher import fetch_eod_candles, fetch_intraday_candles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fvg", tags=["fvg"])


class FVGRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    limit: int = 100
    min_gap_percent: float = 0.05
    min_body_percent: float = 0.3


class FVGResponse(BaseModel):
    symbol: str
    timeframe: str
    total_fvgs: int
    bullish_fvgs: int
    bearish_fvgs: int
    unfilled_count: int
    fvgs: List[dict]
    nearest_bullish: Optional[dict] = None
    nearest_bearish: Optional[dict] = None


@router.post("/detect", response_model=FVGResponse)
async def detect_fvgs(request: FVGRequest):
    """
    Detect Fair Value Gaps in price data.
    
    A Fair Value Gap is an imbalance in price action where:
    - Bullish FVG: Candle 1's high < Candle 3's low (price gapped up)
    - Bearish FVG: Candle 1's low > Candle 3's high (price gapped down)
    
    These gaps often act as magnets for price to return and fill.
    
    Supported timeframes: 1m, 5m, 1h, 1d
    """
    try:
        # Fetch candle data based on timeframe
        if request.timeframe in ("1m", "5m", "15m", "1h"):
            raw_candles = await fetch_intraday_candles(request.symbol, interval=request.timeframe, limit=request.limit)
        else:
            raw_candles = await fetch_eod_candles(request.symbol, limit=request.limit)
        
        if not raw_candles:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")
        
        # Convert to Candle objects
        candles = [
            Candle(
                timestamp=c.get("timestamp", 0),
                open=c.get("open", 0),
                high=c.get("high", 0),
                low=c.get("low", 0),
                close=c.get("close", 0),
                volume=c.get("volume", 0),
            )
            for c in raw_candles
        ]
        
        # Configure and run detector
        config = FVGConfig(
            min_gap_percent=request.min_gap_percent,
            min_body_percent=request.min_body_percent,
            lookback_candles=request.limit,
        )
        detector = FVGDetector(config)
        
        # Detect FVGs
        fvgs = detector.detect(candles)
        
        # Get statistics
        bullish_fvgs = [f for f in fvgs if f.type == "bullish"]
        bearish_fvgs = [f for f in fvgs if f.type == "bearish"]
        unfilled = [f for f in fvgs if f.is_valid and not f.is_filled]
        
        # Get nearest FVGs to current price
        current_price = candles[-1].close if candles else 0
        nearest_bullish = detector.get_nearest_fvg(candles, current_price, "bullish")
        nearest_bearish = detector.get_nearest_fvg(candles, current_price, "bearish")
        
        return FVGResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            total_fvgs=len(fvgs),
            bullish_fvgs=len(bullish_fvgs),
            bearish_fvgs=len(bearish_fvgs),
            unfilled_count=len(unfilled),
            fvgs=[f.to_dict() for f in fvgs],
            nearest_bullish=nearest_bullish.to_dict() if nearest_bullish else None,
            nearest_bearish=nearest_bearish.to_dict() if nearest_bearish else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FVG detection failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unfilled/{symbol}")
async def get_unfilled_fvgs(
    symbol: str,
    limit: int = Query(100, ge=10, le=500),
):
    """
    Get only unfilled (valid) FVGs for a symbol.
    These are the zones where price is likely to return.
    """
    try:
        raw_candles = await fetch_eod_candles(symbol, limit=limit)
        
        if not raw_candles:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        candles = [
            Candle(
                timestamp=c.get("timestamp", 0),
                open=c.get("open", 0),
                high=c.get("high", 0),
                low=c.get("low", 0),
                close=c.get("close", 0),
                volume=c.get("volume", 0),
            )
            for c in raw_candles
        ]
        
        detector = FVGDetector()
        unfilled = detector.get_unfilled_fvgs(candles)
        
        current_price = candles[-1].close if candles else 0
        
        # Add distance to current price
        result = []
        for fvg in unfilled:
            fvg_dict = fvg.to_dict()
            mid = (fvg.gap_high + fvg.gap_low) / 2
            fvg_dict["distance_to_price"] = round(current_price - mid, 4)
            fvg_dict["distance_percent"] = round(((current_price - mid) / current_price) * 100, 4)
            result.append(fvg_dict)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "unfilled_fvgs": result,
            "count": len(result),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get unfilled FVGs for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearest/{symbol}")
async def get_nearest_fvg(
    symbol: str,
    fvg_type: Optional[str] = Query(None, description="bullish or bearish"),
    limit: int = Query(100, ge=10, le=500),
):
    """
    Get the nearest unfilled FVG to current price.
    Useful for finding potential reversal zones.
    """
    try:
        raw_candles = await fetch_eod_candles(symbol, limit=limit)
        
        if not raw_candles:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        candles = [
            Candle(
                timestamp=c.get("timestamp", 0),
                open=c.get("open", 0),
                high=c.get("high", 0),
                low=c.get("low", 0),
                close=c.get("close", 0),
                volume=c.get("volume", 0),
            )
            for c in raw_candles
        ]
        
        current_price = candles[-1].close if candles else 0
        
        detector = FVGDetector()
        nearest = detector.get_nearest_fvg(candles, current_price, fvg_type)
        
        if not nearest:
            return {
                "symbol": symbol,
                "current_price": current_price,
                "nearest_fvg": None,
                "message": "No unfilled FVG found",
            }
        
        fvg_dict = nearest.to_dict()
        mid = (nearest.gap_high + nearest.gap_low) / 2
        fvg_dict["distance_to_price"] = round(current_price - mid, 4)
        fvg_dict["distance_percent"] = round(((current_price - mid) / current_price) * 100, 4)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "nearest_fvg": fvg_dict,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get nearest FVG for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
