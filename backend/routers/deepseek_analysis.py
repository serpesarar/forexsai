"""
DeepSeek-R1 Analysis Router
=============================
Endpoints for DeepSeek-R1 powered market analysis:
- Master Analysis (full institutional analysis)
- Smart Money Concepts (SMC)
- Risk/Reward Optimization
- Seasonality & Anomaly Detection
"""

import logging
import traceback
from fastapi import APIRouter, Query
from utils.json_response import NumpySafeJSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deepseek", tags=["deepseek-analysis"])


@router.get("/master/{symbol}")
async def deepseek_master_analysis(symbol: str):
    """Full institutional analysis using DeepSeek-R1."""
    try:
        from services.deepseek_analysis_service import analyze_with_deepseek
        result = await analyze_with_deepseek(symbol, "master")
        return NumpySafeJSONResponse(content={"success": True, "data": result})
    except Exception as e:
        logger.error(f"DeepSeek master error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@router.get("/smc/{symbol}")
async def deepseek_smc_analysis(symbol: str):
    """Smart Money Concepts analysis using DeepSeek-R1."""
    try:
        from services.deepseek_analysis_service import analyze_with_deepseek
        result = await analyze_with_deepseek(symbol, "smc")
        return NumpySafeJSONResponse(content={"success": True, "data": result})
    except Exception as e:
        logger.error(f"DeepSeek SMC error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@router.get("/risk/{symbol}")
async def deepseek_risk_analysis(symbol: str):
    """Risk/Reward optimization using DeepSeek-R1."""
    try:
        from services.deepseek_analysis_service import analyze_with_deepseek
        result = await analyze_with_deepseek(symbol, "risk")
        return NumpySafeJSONResponse(content={"success": True, "data": result})
    except Exception as e:
        logger.error(f"DeepSeek risk error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@router.get("/seasonality/{symbol}")
async def deepseek_seasonality_analysis(symbol: str):
    """Seasonality & anomaly detection using DeepSeek-R1."""
    try:
        from services.deepseek_analysis_service import analyze_with_deepseek
        result = await analyze_with_deepseek(symbol, "seasonality")
        return NumpySafeJSONResponse(content={"success": True, "data": result})
    except Exception as e:
        logger.error(f"DeepSeek seasonality error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@router.get("/full/{symbol}")
async def deepseek_full_analysis(symbol: str):
    """Run all analysis types and return combined result."""
    try:
        from services.deepseek_analysis_service import analyze_with_deepseek
        import asyncio

        master, smc, risk, seasonality = await asyncio.gather(
            analyze_with_deepseek(symbol, "master"),
            analyze_with_deepseek(symbol, "smc"),
            analyze_with_deepseek(symbol, "risk"),
            analyze_with_deepseek(symbol, "seasonality"),
        )

        return NumpySafeJSONResponse(content={
            "success": True,
            "data": {
                "master": master,
                "smc": smc,
                "risk": risk,
                "seasonality": seasonality,
                "symbol": symbol,
            }
        })
    except Exception as e:
        logger.error(f"DeepSeek full error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)
