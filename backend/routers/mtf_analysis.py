"""
Multi-Timeframe Analysis API Router
====================================
Endpoints for MTF technical analysis with ATR, Bollinger, Volume, and Confluence scoring.
"""

from __future__ import annotations

import logging
import traceback
from typing import Optional, Literal
from fastapi import APIRouter, Query, HTTPException

from services.mtf_analysis_service import get_mtf_analysis, Timeframe

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/mtf", tags=["mtf-analysis"])


@router.get("/analysis")
async def mtf_analysis(
    symbol: str = Query(default="XAUUSD", description="Trading symbol"),
    timeframe: Optional[str] = Query(default=None, description="Specific timeframe (M1, M5, M15, M30, H1, H4, D1) or None for all")
) -> dict:
    """
    Get Multi-Timeframe Technical Analysis.
    
    - If timeframe is specified: Returns detailed analysis for that timeframe
    - If timeframe is None: Returns analysis for all timeframes + MTF confluence score
    
    Response includes:
    - EMA (20, 50, 200) with distances
    - Bollinger Bands with %B and squeeze detection
    - ATR with dynamic SL/TP suggestions
    - Volume analysis with confirmation
    - RSI and MACD signals
    - Support/Resistance levels
    - Overall signal and confidence
    - MTF Confluence score (when all timeframes requested)
    """
    
    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    
    if timeframe and timeframe.upper() not in valid_timeframes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    tf = timeframe.upper() if timeframe else None
    try:
        result = await get_mtf_analysis(symbol, tf)
    except Exception as e:
        logger.error(f"MTF analysis error for {symbol} {tf}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    return result


@router.get("/confluence/{symbol}")
async def mtf_confluence(symbol: str) -> dict:
    """
    Get MTF Confluence score for a symbol.
    
    Quick endpoint that returns just the confluence data without full timeframe details.
    """
    result = await get_mtf_analysis(symbol, None)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    return {
        "success": True,
        "symbol": symbol,
        "timestamp": result.get("timestamp"),
        "current_price": result.get("current_price"),
        "confluence": result.get("confluence")
    }


@router.get("/timeframe/{symbol}/{timeframe}")
async def single_timeframe(symbol: str, timeframe: str) -> dict:
    """
    Get analysis for a specific timeframe.
    
    Path parameters:
    - symbol: Trading symbol (e.g., XAUUSD, NDX.INDX)
    - timeframe: M1, M5, M15, M30, H1, H4, or D1
    """
    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    tf = timeframe.upper()
    
    if tf not in valid_timeframes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    try:
        result = await get_mtf_analysis(symbol, tf)
    except Exception as e:
        logger.error(f"MTF timeframe error {symbol} {tf}: {e}\n{traceback.format_exc()}")
        return {"success": False, "error": f"Analysis error: {str(e)}", "traceback": traceback.format_exc()}
    
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Analysis failed")}
    
    return result
