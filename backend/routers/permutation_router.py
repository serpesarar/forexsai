from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.permutation_analysis_service import (
    analyze_model_permutations,
    analyze_technical_permutations
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/permutation-analysis",
    tags=["Permutation Analysis"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{symbol}")
async def get_permutation_analysis(
    symbol: str,
    analysis_type: str = Query("both", description="models | indicators | both"),
    direction: str = Query("BUY", description="BUY | SELL"),
    lookback_days: int = Query(30, ge=1, le=365, description="Gün sayısı (Sadece model analizi için kullanılır)"),
    min_occurrences: int = Query(10, ge=1, description="Kombinasyon minimum yaşanma sayısı"),
    lookforward_candles: int = Query(5, ge=1, le=50, description="Sadece indicator analizi: Kaç mum sonrasına bakılacak?"),
    target_move_pct: float = Query(0.3, ge=0.01, description="Sadece indicator analizi: Hedef yüzde kaç (TP) ?")
):
    """
    Get rigorous historical permutation combinations for a specific symbol.
    Provides decoupled insights:
    - Which Models work best together?
    - Which Technical Indicator conditions yield the highest probability of moving in the desired direction?
    """
    try:
        response_data = {
            "symbol": symbol,
            "direction": direction,
            "models_analysis": None,
            "indicators_analysis": None
        }

        # 1. Model Permutations
        if analysis_type in ["both", "models"]:
            models_result = await analyze_model_permutations(
                symbol=symbol,
                direction=direction,
                min_occurrences=min_occurrences,
                lookback_days=lookback_days
            )
            response_data["models_analysis"] = models_result

        # 2. Technical Indicator Permutations
        if analysis_type in ["both", "indicators"]:
            tech_result = await analyze_technical_permutations(
                symbol=symbol,
                direction=direction,
                min_occurrences=max(1, min_occurrences // 2),  # indicators trigger less easily with strict overlap
                lookforward_candles=lookforward_candles,
                take_profit_pct=target_move_pct
            )
            response_data["indicators_analysis"] = tech_result

        return {
            "success": True,
            "data": response_data
        }

    except Exception as e:
        logger.error(f"[PermutationRouter] Error analyzing {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
