import asyncio
from fastapi import APIRouter, Query
import logging

from services.consensus_report_service import get_symbol_consensus_view
from services.permutation_analysis_service import (
    analyze_model_permutations,
    analyze_technical_permutations
)
from services.permutation_batch_service import (
    get_latest_model_batch_results,
    get_latest_technical_batch_results,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/permutation-analysis",
    tags=["Permutation Analysis"],
    responses={404: {"description": "Not found"}},
)


@router.get("/consensus/{symbol}")
async def get_consensus_analysis(
    symbol: str,
    top: int = Query(6, ge=1, le=20),
    prefix: str = Query("consensus_model_analysis_all_tf_10m"),
    report_path: str | None = Query(None),
):
    try:
        data = await asyncio.to_thread(
            get_symbol_consensus_view,
            symbol,
            top=top,
            prefix=prefix,
            report_path=report_path,
        )
        return {
            "success": True,
            "data": data,
        }
    except Exception as e:
        logger.error(f"[PermutationRouter] Consensus error for {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@router.get("/{symbol}")
async def get_permutation_analysis(
    symbol: str,
    analysis_type: str = Query("both", description="models | indicators | both"),
    source: str = Query("auto", description="auto | batch | live"),
    direction: str = Query("BUY", description="BUY | SELL"),
    lookback_days: int = Query(30, ge=1, le=365, description="Gün sayısı (Sadece model analizi için kullanılır)"),
    min_occurrences: int = Query(10, ge=1, description="Kombinasyon minimum yaşanma sayısı"),
    cluster_window_minutes: int = Query(10, ge=5, le=15, description="Model analizi için aynı-an tolerans penceresi (dakika)"),
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
        source = (source or "auto").lower().strip()
        if source not in {"auto", "batch", "live"}:
            return {"success": False, "error": f"Unsupported source: {source}"}

        response_data = {
            "symbol": symbol,
            "direction": direction,
            "source": source,
            "models_analysis": None,
            "indicators_analysis": None
        }

        # 1. Model Permutations
        if analysis_type in ["both", "models"]:
            models_result = None
            batch_error = None

            if source in {"auto", "batch"}:
                batch_candidate = await asyncio.to_thread(get_latest_model_batch_results, symbol, direction)
                if batch_candidate.get("error"):
                    batch_error = batch_candidate.get("error")
                    if source == "batch":
                        models_result = batch_candidate
                else:
                    models_result = batch_candidate

            if models_result is None and source in {"auto", "live"}:
                models_result = await analyze_model_permutations(
                    symbol=symbol,
                    direction=direction,
                    min_occurrences=min_occurrences,
                    lookback_days=lookback_days,
                    cluster_window_minutes=cluster_window_minutes,
                )
                if isinstance(models_result, dict) and not models_result.get("error"):
                    models_result["source"] = "live"
                    if batch_error:
                        models_result["fallback_reason"] = batch_error

            response_data["models_analysis"] = models_result

        # 2. Technical Indicator Permutations
        if analysis_type in ["both", "indicators"]:
            tech_result = None
            batch_error = None

            if source in {"auto", "batch"}:
                batch_candidate = await asyncio.to_thread(get_latest_technical_batch_results, symbol, direction)
                if batch_candidate.get("error"):
                    batch_error = batch_candidate.get("error")
                    if source == "batch":
                        tech_result = batch_candidate
                else:
                    tech_result = batch_candidate

            if tech_result is None and source in {"auto", "live"}:
                tech_result = await analyze_technical_permutations(
                    symbol=symbol,
                    direction=direction,
                    min_occurrences=max(1, min_occurrences // 2),
                    lookforward_candles=lookforward_candles,
                    take_profit_pct=target_move_pct
                )
                if isinstance(tech_result, dict) and not tech_result.get("error"):
                    tech_result["source"] = "live"
                    if batch_error:
                        tech_result["fallback_reason"] = batch_error

            response_data["indicators_analysis"] = tech_result

        return {
            "success": True,
            "data": response_data
        }

    except Exception as e:
        logger.error(f"[PermutationRouter] Error analyzing {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
