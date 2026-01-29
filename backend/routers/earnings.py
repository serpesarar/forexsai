"""
NASDAQ Earnings Calendar API Endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.earnings_service import earnings_service, scenario_engine, NASDAQ_WEIGHTS

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


@router.get("/calendar")
async def get_earnings_calendar(days_ahead: int = Query(default=7, ge=1, le=30)):
    """
    Önümüzdeki X gün için NASDAQ-100 earnings takvimi
    Senaryo analizleri dahil
    """
    try:
        events = await earnings_service.get_earnings_with_scenarios(days_ahead)
        return {
            "success": True,
            "count": len(events),
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenario/{symbol}")
async def get_earnings_scenario(
    symbol: str,
    actual_eps: float = Query(..., description="Gerçekleşen EPS"),
    expected_eps: float = Query(..., description="Beklenen EPS"),
    actual_revenue: float = Query(..., description="Gerçekleşen Revenue (milyar)"),
    expected_revenue: float = Query(..., description="Beklenen Revenue (milyar)"),
    guidance: Optional[str] = Query(None, description="up/down/maintain")
):
    """
    Kazanç sonucuna göre NASDAQ senaryo analizi
    """
    symbol = symbol.upper()
    
    if symbol not in NASDAQ_WEIGHTS:
        raise HTTPException(status_code=404, detail=f"{symbol} NASDAQ-100'de bulunamadı")
    
    try:
        result = scenario_engine.analyze_scenario(
            symbol=symbol,
            actual_eps=actual_eps,
            expected_eps=expected_eps,
            actual_revenue=actual_revenue,
            expected_revenue=expected_revenue,
            guidance=guidance
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "nasdaq_weight": f"{NASDAQ_WEIGHTS[symbol]:.2f}%",
            "scenario": {
                "type": result.scenario_type.value,
                "confidence": result.confidence,
                "nasdaq_direction": result.nasdaq_direction,
                "color": result.color,
                "expected_move": f"{'+' if result.expected_move_pips > 0 else ''}{result.expected_move_pips} pips",
                "timeframe": result.timeframe,
                "risk_level": result.risk_level,
                "reasoning": result.reasoning
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pre-scenarios/{symbol}")
async def get_pre_earnings_scenarios(
    symbol: str,
    expected_eps: float = Query(..., description="Beklenen EPS"),
    expected_revenue: float = Query(..., description="Beklenen Revenue (milyar)")
):
    """
    Earnings öncesi 3 olası senaryo (Beat/Inline/Miss)
    """
    symbol = symbol.upper()
    
    if symbol not in NASDAQ_WEIGHTS:
        raise HTTPException(status_code=404, detail=f"{symbol} NASDAQ-100'de bulunamadı")
    
    try:
        scenarios = scenario_engine.generate_pre_earnings_scenarios(
            symbol=symbol,
            expected_eps=expected_eps,
            expected_revenue=expected_revenue
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "nasdaq_weight": f"{NASDAQ_WEIGHTS[symbol]:.2f}%",
            "scenarios": scenarios
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/constituents")
async def get_nasdaq_constituents():
    """
    NASDAQ-100 top 20 şirket listesi
    """
    constituents = [
        {"symbol": symbol, "weight": weight, "importance": "CRITICAL" if weight >= 5 else "HIGH" if weight >= 2 else "MEDIUM"}
        for symbol, weight in sorted(NASDAQ_WEIGHTS.items(), key=lambda x: -x[1])
    ]
    
    return {
        "success": True,
        "count": len(constituents),
        "constituents": constituents
    }
