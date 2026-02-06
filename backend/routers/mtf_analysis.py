"""
Multi-Timeframe Analysis API Router
====================================
Endpoints for MTF technical analysis with ATR, Bollinger, Volume, and Confluence scoring.

Uses NumpySafeJSONResponse to bypass FastAPI's jsonable_encoder which
can't handle numpy types (np.bool_, np.int64, np.float64).
"""

from __future__ import annotations

import logging
import traceback
from typing import Optional, Literal
from fastapi import APIRouter, Query, HTTPException

from services.mtf_analysis_service import get_mtf_analysis, Timeframe
from utils.json_response import NumpySafeJSONResponse

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/mtf", tags=["mtf-analysis"])


@router.get("/analysis")
async def mtf_analysis(
    symbol: str = Query(default="XAUUSD", description="Trading symbol"),
    timeframe: Optional[str] = Query(default=None, description="Specific timeframe (M1, M5, M15, M30, H1, H4, D1) or None for all")
):
    """
    Get Multi-Timeframe Technical Analysis.
    
    - If timeframe is specified: Returns detailed analysis for that timeframe
    - If timeframe is None: Returns analysis for all timeframes + MTF confluence score
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
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)
    
    if not result.get("success"):
        return NumpySafeJSONResponse(content={"success": False, "error": result.get("error", "Analysis failed")}, status_code=500)
    
    return NumpySafeJSONResponse(content=result)


@router.get("/confluence/{symbol}")
async def mtf_confluence(symbol: str):
    """Get MTF Confluence score for a symbol."""
    try:
        result = await get_mtf_analysis(symbol, None)
    except Exception as e:
        logger.error(f"MTF confluence error {symbol}: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)
    
    if not result.get("success"):
        return NumpySafeJSONResponse(content={"success": False, "error": result.get("error", "Analysis failed")}, status_code=500)
    
    return NumpySafeJSONResponse(content={
        "success": True,
        "symbol": symbol,
        "timestamp": result.get("timestamp"),
        "current_price": result.get("current_price"),
        "confluence": result.get("confluence")
    })


@router.get("/timeframe/{symbol}/{timeframe}")
async def single_timeframe(symbol: str, timeframe: str):
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
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)})
    
    if not result.get("success"):
        return NumpySafeJSONResponse(content={"success": False, "error": result.get("error", "Analysis failed")})
    
    return NumpySafeJSONResponse(content=result)
