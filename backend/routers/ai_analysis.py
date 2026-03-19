"""
API Router for AI-powered Signal Analysis
Combines ML predictions with Claude AI review
"""
import asyncio
from fastapi import APIRouter
from typing import Any, Dict, List

router = APIRouter(prefix="/api/ai-analysis", tags=["ai-analysis"])


@router.get("/{symbol}")
async def get_ai_analysis(symbol: str, force_refresh: bool = False):
    """
    Get full AI analysis for a symbol.
    
    Combines:
    1. ML model prediction (LightGBM trained on historical patterns)
    2. Claude AI review (independent assessment of signals + TA data)
    3. Technical analysis snapshot
    """
    from services.claude_signal_analyzer import get_full_analysis

    return await get_full_analysis(symbol, force_refresh=force_refresh)


@router.get("/")
async def get_all_ai_analysis():
    """Get AI analysis for both NASDAQ and XAUUSD."""
    from services.ai_panel_analysis_service import get_supported_ai_symbols
    from services.claude_signal_analyzer import get_full_analysis

    symbols = get_supported_ai_symbols()
    return await asyncio.gather(*(get_full_analysis(symbol) for symbol in symbols))


@router.get("/detailed/{symbol}")
async def get_detailed_ai_analysis(symbol: str):
    try:
        from services.detailed_ai_analysis_service import get_detailed_analysis
        result = await get_detailed_analysis(symbol)
        return {
            "symbol": result.get("symbol", symbol),
            "context": result.get("context", {}),
            "analysis": result.get("analysis", {}),
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "symbol": symbol,
        }
