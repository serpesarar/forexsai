"""
DeepSeek-R1 Analysis Router
=============================
Endpoints for market analysis:
- Master Analysis (DeepSeek-R1 AI powered)
- Smart Money Concepts (Rule-based geometric calculation)
- Risk/Reward Optimization (Pure mathematical calculation)
- Seasonality & Anomaly Detection (Historical statistics)

COST OPTIMIZATION:
- SMC, Risk, Seasonality use rule-based calculations (FREE, instant)
- Only Master analysis uses DeepSeek-R1 (paid, cached)
"""

import logging
import traceback
from fastapi import APIRouter, Query
from utils.json_response import NumpySafeJSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deepseek", tags=["deepseek-analysis"])


# ============================================================================
# MASTER ANALYSIS (DeepSeek-R1 AI - Premium)
# ============================================================================

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


# ============================================================================
# SMC ANALYSIS (Rule-based - FREE, Instant)
# ============================================================================

@router.get("/smc/{symbol}")
async def smc_analysis(symbol: str):
    """
    Smart Money Concepts analysis using rule-based geometric calculation.
    NO DeepSeek/AI - Pure technical calculation for instant results.
    """
    try:
        from services.smc_calculator_service import calculate_smc_with_gaps
        from services import data_hub
        
        # Get EOD candle data (daily) for gap analysis
        candles = data_hub.get_candles(symbol, "1d", limit=50)
        
        if not candles or len(candles) < 20:
            return NumpySafeJSONResponse(
                content={"success": False, "error": "Insufficient candle data"},
                status_code=400
            )
        
        result = await calculate_smc_with_gaps(symbol, candles)
        return NumpySafeJSONResponse(content={"success": True, "data": result})
        
    except Exception as e:
        logger.error(f"SMC calculation error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ============================================================================
# RISK ANALYSIS (Pure Math - FREE, Instant)
# ============================================================================

@router.get("/risk/{symbol}")
async def risk_analysis(
    symbol: str,
    direction: str = Query("long", enum=["long", "short"]),
    account_size: float = Query(10000, ge=100),
    risk_per_trade: float = Query(1.0, ge=0.1, le=10)
):
    """
    Risk/Reward analysis using pure mathematical calculation.
    NO DeepSeek/AI - Kelly Criterion, ATR, position sizing formulas.
    """
    try:
        from services.risk_calculator_service import calculate_risk_analysis
        from services import data_hub
        
        # Get candle data and current price
        candles = data_hub.get_candles(symbol, "1h", limit=50)
        current_price = data_hub.get_price(symbol)

        if not candles or len(candles) < 14:
            logger.warning("Risk analysis DataHub cache unavailable for %s 1h candles", symbol)

        if not current_price:
            logger.warning("Risk analysis DataHub cache unavailable for %s price", symbol)
        
        if not candles or len(candles) < 14:
            return NumpySafeJSONResponse(
                content={"success": False, "error": "Insufficient candle data"},
                status_code=400
            )
        
        if not current_price:
            return NumpySafeJSONResponse(
                content={"success": False, "error": "Price data unavailable"},
                status_code=400
            )
        
        result = await calculate_risk_analysis(
            symbol=symbol,
            current_price=current_price,
            direction=direction,
            candles=candles,
            account_size=account_size,
            risk_per_trade_pct=risk_per_trade
        )
        
        return NumpySafeJSONResponse(content={"success": True, "data": result})
        
    except Exception as e:
        logger.error(f"Risk calculation error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ============================================================================
# SEASONALITY ANALYSIS (Historical Stats - FREE, Instant)
# ============================================================================

@router.get("/seasonality/{symbol}")
async def seasonality_analysis(symbol: str):
    """
    Seasonality analysis using historical statistics.
    NO DeepSeek/AI - Database aggregation of 15+ years of data.
    """
    try:
        from services.seasonality_calculator_service import calculate_seasonality
        from services import data_hub
        
        # Get recent candles for anomaly detection
        candles = data_hub.get_candles(symbol, "1d", limit=30)
        
        result = await calculate_seasonality(symbol, candles)
        return NumpySafeJSONResponse(content={"success": True, "data": result})
        
    except Exception as e:
        logger.error(f"Seasonality calculation error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ============================================================================
# COMBINED ANALYSIS (Smart Setup Generator)
# ============================================================================

@router.get("/smart-setup/{symbol}")
async def smart_setup_analysis(
    symbol: str,
    direction: str = Query("long", enum=["long", "short"]),
    account_size: float = Query(10000, ge=100),
    risk_per_trade: float = Query(1.0, ge=0.1, le=10)
):
    """
    Smart Setup Generator - Combines SMC, Risk, and Seasonality into one view.
    All calculations are rule-based (FREE, instant).
    DeepSeek master analysis is optional and cached separately.
    """
    try:
        import asyncio
        from services.smc_calculator_service import calculate_smc
        from services.risk_calculator_service import calculate_risk_analysis
        from services.seasonality_calculator_service import calculate_seasonality
        from services import data_hub
        
        # Get data
        candles_1h = data_hub.get_candles(symbol, "1h", limit=100)
        candles_1d = data_hub.get_candles(symbol, "1d", limit=30)
        current_price = data_hub.get_price(symbol)

        if not candles_1h or len(candles_1h) < 20:
            logger.warning("Smart setup DataHub cache unavailable for %s 1h candles", symbol)
        if not candles_1d or len(candles_1d) < 20:
            logger.warning("Smart setup DataHub cache unavailable for %s daily candles", symbol)
        if not current_price:
            logger.warning("Smart setup DataHub cache unavailable for %s price", symbol)
        
        if not candles_1h or len(candles_1h) < 20:
            return NumpySafeJSONResponse(
                content={"success": False, "error": "Insufficient candle data"},
                status_code=400
            )
        
        # Run all calculations in parallel
        smc_task = calculate_smc(symbol, candles_1h)
        risk_task = calculate_risk_analysis(
            symbol, current_price or candles_1h[-1]["close"],
            direction, candles_1h, account_size, risk_per_trade
        )
        seasonality_task = calculate_seasonality(symbol, candles_1d)
        
        smc, risk, seasonality = await asyncio.gather(smc_task, risk_task, seasonality_task)
        
        # Generate combined setup recommendation
        setup = generate_setup_recommendation(smc, risk, seasonality, direction)
        
        return NumpySafeJSONResponse(content={
            "success": True,
            "data": {
                "symbol": symbol,
                "direction": direction,
                "current_price": current_price or candles_1h[-1]["close"],
                "timestamp": smc.get("timestamp"),
                "setup": setup,
                "smc": smc,
                "risk": risk,
                "seasonality": seasonality,
                "calculation_method": "rule_based_combined",
                "cost": "FREE"
            }
        })
        
    except Exception as e:
        logger.error(f"Smart setup error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)


def generate_setup_recommendation(smc: dict, risk: dict, seasonality: dict, direction: str) -> dict:
    """Generate a combined setup recommendation from all analyses."""
    
    score = 0
    factors = []
    warnings = []
    
    # SMC contribution
    smc_bias = smc.get("bias", {})
    if smc_bias.get("direction") == direction:
        score += 30
        factors.append(f"SMC aligns with {direction}")
    elif smc_bias.get("direction") == "neutral":
        score += 10
        factors.append("SMC neutral")
    else:
        score -= 20
        warnings.append("SMC contradicts trade direction")
    
    # Risk contribution
    kelly = risk.get("kelly_criterion", {})
    if kelly.get("recommendation") in ["moderate", "aggressive"]:
        score += 20
        factors.append("Kelly Criterion positive")
    elif kelly.get("recommendation") == "avoid":
        score -= 30
        warnings.append("Kelly suggests avoiding this setup")
    
    # Check R:R ratio
    take_profits = risk.get("take_profits", [])
    if take_profits and take_profits[0].get("r_r_ratio", 0) >= 2.0:
        score += 15
        factors.append("Good R:R ratio (2:1+)")
    
    # Seasonality contribution
    seasonal_bias = seasonality.get("bias", {})
    if seasonal_bias.get("direction") == direction:
        score += 20
        factors.append("Seasonality favorable")
    elif seasonal_bias.get("direction") == "neutral":
        score += 5
    else:
        score -= 10
        warnings.append("Seasonality unfavorable")
    
    # Monthly check
    monthly = seasonality.get("monthly", {})
    if monthly.get("win_rate", 50) > 55:
        score += 10
        factors.append("Strong monthly win rate")
    elif monthly.get("win_rate", 50) < 45:
        score -= 10
        warnings.append("Weak historical month")
    
    # Determine grade
    if score >= 60:
        grade = "A"
        verdict = "High Probability Setup"
    elif score >= 40:
        grade = "B"
        verdict = "Favorable Setup"
    elif score >= 20:
        grade = "C"
        verdict = "Marginal Setup"
    elif score >= 0:
        grade = "D"
        verdict = "Weak Setup"
    else:
        grade = "F"
        verdict = "Avoid Setup"
    
    return {
        "grade": grade,
        "score": score,
        "verdict": verdict,
        "alignment_factors": factors,
        "warnings": warnings,
        "recommendation": "proceed" if score >= 40 else "caution" if score >= 0 else "avoid",
        "confidence": min(90, max(20, 50 + score))
    }


# ============================================================================
# LEGACY ENDPOINTS (Backward Compatibility)
# ============================================================================

@router.get("/full/{symbol}")
async def deepseek_full_analysis(symbol: str):
    """
    DEPRECATED: Use /smart-setup instead for cost-effective analysis.
    This endpoint runs all DeepSeek analyses (expensive).
    """
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
                "cost_notice": "This endpoint uses 4x DeepSeek API calls. Consider /smart-setup for FREE rule-based analysis."
            }
        })
    except Exception as e:
        logger.error(f"DeepSeek full error: {e}\n{traceback.format_exc()}")
        return NumpySafeJSONResponse(content={"success": False, "error": str(e)}, status_code=500)
