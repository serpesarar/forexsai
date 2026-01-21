"""
Error Analysis Service
Analyzes failed predictions with AI to understand what went wrong and learn from mistakes.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from config import settings
from database.supabase_client import get_supabase_client, is_db_available
from services.data_fetcher import fetch_intraday_candles, fetch_latest_price
from services.target_config import (
    get_symbol_config,
    calculate_target_prices,
    calculate_stoploss_price,
    pips_from_price_change,
)

logger = logging.getLogger(__name__)

# Claude Haiku 4.5 for error analysis
ERROR_ANALYSIS_MODEL = "claude-haiku-4-5"
ERROR_ANALYSIS_MAX_TOKENS = 1000

# Analysis check intervals
QUICK_CHECK_HOURS = 1
DEEP_ANALYSIS_HOURS = 4


async def save_candle_snapshot(
    prediction_id: str,
    symbol: str,
    snapshot_type: str = "at_prediction",
    indicators: Optional[Dict] = None,
    levels: Optional[Dict] = None
) -> Optional[str]:
    """
    Save candle data snapshot for a prediction.
    
    Args:
        prediction_id: UUID of the prediction
        symbol: Trading symbol
        snapshot_type: 'at_prediction', 'after_1h', 'after_4h', 'after_24h'
        indicators: Technical indicators at this moment
        levels: Support/resistance levels
    
    Returns:
        Snapshot ID if successful
    """
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    try:
        # Fetch current candles
        candles = await fetch_intraday_candles(symbol, interval="5m", limit=100)
        
        if not candles:
            logger.warning(f"No candles available for snapshot: {symbol}")
            return None
        
        # Prepare candle data (compact format)
        candle_data = []
        for c in candles:
            candle_data.append({
                "t": c.get("date", ""),
                "o": round(c.get("open", 0), 2),
                "h": round(c.get("high", 0), 2),
                "l": round(c.get("low", 0), 2),
                "c": round(c.get("close", 0), 2),
                "v": int(c.get("volume", 0))
            })
        
        snapshot = {
            "prediction_id": prediction_id,
            "symbol": symbol,
            "timeframe": "5m",
            "snapshot_type": snapshot_type,
            "candles": candle_data,
            "indicators": indicators or {},
            "levels": levels or {},
            "candle_count": len(candle_data)
        }
        
        result = client.table("candle_snapshots").insert(snapshot).execute()
        
        if result.get("data"):
            logger.info(f"Saved candle snapshot for prediction {prediction_id}: {snapshot_type}")
            return result["data"][0].get("id")
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to save candle snapshot: {e}")
        return None


async def detect_fake_move(
    candles: List[Dict],
    entry_price: float,
    direction: str,
    high_price: float,
    low_price: float
) -> Dict[str, Any]:
    """
    Detect if the price movement was a fake pump/dump or stop hunt.
    
    Returns:
        Dict with is_fake, type, and confidence
    """
    if not candles or len(candles) < 10:
        return {"is_fake": False, "type": None, "confidence": 0}
    
    # Get price movement stats
    config = get_symbol_config("NDX.INDX")  # Default
    
    if direction == "BUY":
        # For BUY: check if price went up then reversed sharply
        max_favorable = high_price - entry_price
        max_adverse = entry_price - low_price
        
        # Fake pump detection: price pumped then dumped
        if max_favorable > 20 and max_adverse > max_favorable * 1.5:
            return {
                "is_fake": True,
                "type": "fake_pump",
                "confidence": min(0.9, max_adverse / (max_favorable + 1) * 0.5),
                "details": f"Pumped {max_favorable:.1f} pips then dumped {max_adverse:.1f} pips"
            }
        
        # Stop hunt detection: price dipped below entry to hit stops then recovered
        if max_adverse > 30 and max_favorable < 10:
            return {
                "is_fake": True,
                "type": "stop_hunt",
                "confidence": 0.7,
                "details": f"Dipped {max_adverse:.1f} pips (possible stop hunt)"
            }
    
    elif direction == "SELL":
        # For SELL: check if price went down then reversed sharply
        max_favorable = entry_price - low_price
        max_adverse = high_price - entry_price
        
        # Fake dump detection
        if max_favorable > 20 and max_adverse > max_favorable * 1.5:
            return {
                "is_fake": True,
                "type": "fake_dump",
                "confidence": min(0.9, max_adverse / (max_favorable + 1) * 0.5),
                "details": f"Dumped {max_favorable:.1f} pips then pumped {max_adverse:.1f} pips"
            }
        
        # Liquidity grab detection
        if max_adverse > 30 and max_favorable < 10:
            return {
                "is_fake": True,
                "type": "liquidity_grab",
                "confidence": 0.7,
                "details": f"Spiked {max_adverse:.1f} pips up (possible liquidity grab)"
            }
    
    return {"is_fake": False, "type": None, "confidence": 0}


async def analyze_error_with_claude(
    prediction: Dict[str, Any],
    outcome: Dict[str, Any],
    candles_at_prediction: List[Dict],
    candles_after: List[Dict],
    fake_move_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Claude to analyze why a prediction failed.
    
    Returns:
        AI analysis result with root cause, lessons, and suggestions
    """
    if not settings.anthropic_api_key:
        return {"error": "Anthropic API key not configured"}
    
    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        # Prepare context
        entry_price = prediction.get("ml_entry_price", 0)
        direction = prediction.get("ml_direction", "HOLD")
        confidence = prediction.get("ml_confidence", 0)
        target = prediction.get("ml_target_price", 0)
        stop = prediction.get("ml_stop_price", 0)
        factors = prediction.get("factors", {})
        
        exit_price = outcome.get("exit_price", 0)
        high_price = outcome.get("high_price", exit_price)
        low_price = outcome.get("low_price", exit_price)
        hit_stop = outcome.get("hit_stop", False)
        hit_target = outcome.get("hit_target", False)
        
        # Format candle data for Claude (last 20 candles)
        candles_text = ""
        if candles_at_prediction:
            candles_text = "Tahmin anındaki son 20 mum:\n"
            for c in candles_at_prediction[-20:]:
                candles_text += f"  {c.get('t', '')}: O={c.get('o')}, H={c.get('h')}, L={c.get('l')}, C={c.get('c')}\n"
        
        after_candles_text = ""
        if candles_after:
            after_candles_text = "\nTahmin sonrası mumlar:\n"
            for c in candles_after[:20]:
                after_candles_text += f"  {c.get('t', '')}: O={c.get('o')}, H={c.get('h')}, L={c.get('l')}, C={c.get('c')}\n"
        
        system_prompt = """Sen bir trading hata analiz uzmanısın. Yanlış giden bir tahmin verildiğinde:
1. Hatanın kök nedenini tespit et
2. Gözden kaçırılan sinyalleri belirle
3. Fake pump/dump veya stop hunt olup olmadığını değerlendir
4. Gelecekte bu hatadan kaçınmak için somut öneriler sun

JSON formatında yanıt ver:
{
    "summary": "Kısa özet (1-2 cümle)",
    "root_cause": "divergence_ignored|overbought_buy|oversold_sell|against_trend|low_volume|fake_move|bad_timing|support_resistance_ignored|other",
    "missed_signals": ["signal1", "signal2"],
    "market_context": "O andaki piyasa durumu açıklaması",
    "is_fake_move": true/false,
    "fake_move_type": "fake_pump|fake_dump|stop_hunt|liquidity_grab|null",
    "lesson_learned": "Bu deneyimden öğrenilen ders",
    "confidence_should_have_been": 0-100 arası,
    "suggested_action": "BUY|SELL|HOLD",
    "improvement_suggestions": ["öneri1", "öneri2"],
    "pattern_to_avoid": "Kaçınılması gereken pattern açıklaması"
}"""

        user_prompt = f"""Yanlış giden tahmin analizi:

## Tahmin Detayları
- Sembol: {prediction.get('symbol')}
- Yön: {direction}
- Güven: %{confidence}
- Giriş: {entry_price}
- Hedef: {target}
- Stop: {stop}

## Faktörler
{json.dumps(factors, indent=2, ensure_ascii=False) if factors else "Faktör bilgisi yok"}

## Sonuç
- Çıkış fiyatı: {exit_price}
- En yüksek: {high_price}
- En düşük: {low_price}
- Stop tetiklendi: {'Evet' if hit_stop else 'Hayır'}
- Hedef ulaşıldı: {'Evet' if hit_target else 'Hayır'}

## Fake Move Tespiti
{json.dumps(fake_move_info, indent=2, ensure_ascii=False)}

## Mum Verileri
{candles_text}
{after_candles_text}

Bu tahminin neden yanlış gittiğini analiz et ve öğrenme noktalarını belirle."""

        response = client.messages.create(
            model=ERROR_ANALYSIS_MODEL,
            max_tokens=ERROR_ANALYSIS_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            analysis = json.loads(json_str)
            analysis["raw_response"] = response_text
            return analysis
            
        except json.JSONDecodeError:
            logger.warning("Could not parse Claude response as JSON")
            return {
                "summary": response_text[:500],
                "root_cause": "unknown",
                "raw_response": response_text,
                "parse_error": True
            }
        
    except Exception as e:
        logger.error(f"Claude error analysis failed: {e}")
        return {"error": str(e)}


async def create_error_analysis(
    prediction_id: str,
    outcome_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a full error analysis for a failed prediction.
    
    Args:
        prediction_id: UUID of the prediction
        outcome_id: UUID of the outcome result (optional)
    
    Returns:
        Error analysis record
    """
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    try:
        # Fetch prediction
        pred_result = client.table("prediction_logs").select("*").eq("id", prediction_id).execute()
        prediction = pred_result.get("data", [{}])[0] if pred_result.get("data") else None
        
        if not prediction:
            logger.warning(f"Prediction not found: {prediction_id}")
            return None
        
        # Fetch outcome
        outcome = None
        if outcome_id:
            out_result = client.table("outcome_results").select("*").eq("id", outcome_id).execute()
            outcome = out_result.get("data", [{}])[0] if out_result.get("data") else None
        else:
            # Get latest outcome for this prediction
            out_result = client.table("outcome_results").select("*").eq(
                "prediction_id", prediction_id
            ).order("created_at", desc=True).limit(1).execute()
            outcome = out_result.get("data", [{}])[0] if out_result.get("data") else None
        
        if not outcome:
            logger.warning(f"No outcome found for prediction: {prediction_id}")
            return None
        
        # Determine error type
        hit_stop = outcome.get("hit_stop", False)
        hit_target = outcome.get("hit_target", False)
        ml_correct = outcome.get("ml_correct", False)
        
        if ml_correct and not hit_stop:
            logger.info(f"Prediction {prediction_id} was correct, skipping error analysis")
            return None
        
        if hit_stop:
            error_type = "stoploss_hit"
        elif not ml_correct:
            error_type = "wrong_direction"
        else:
            error_type = "missed_target"
        
        # Get candle snapshots
        snap_result = client.table("candle_snapshots").select("*").eq(
            "prediction_id", prediction_id
        ).eq("snapshot_type", "at_prediction").execute()
        
        candles_at_prediction = []
        if snap_result.get("data"):
            candles_at_prediction = snap_result["data"][0].get("candles", [])
        
        # Fetch current candles for "after" comparison
        symbol = prediction.get("symbol", "NDX.INDX")
        candles_after = await fetch_intraday_candles(symbol, interval="5m", limit=50)
        candles_after_compact = []
        for c in (candles_after or []):
            candles_after_compact.append({
                "t": c.get("date", ""),
                "o": round(c.get("open", 0), 2),
                "h": round(c.get("high", 0), 2),
                "l": round(c.get("low", 0), 2),
                "c": round(c.get("close", 0), 2)
            })
        
        # Detect fake move
        entry_price = prediction.get("ml_entry_price", 0)
        direction = prediction.get("ml_direction", "HOLD")
        high_price = outcome.get("high_price") or outcome.get("exit_price", entry_price)
        low_price = outcome.get("low_price") or outcome.get("exit_price", entry_price)
        
        fake_move_info = await detect_fake_move(
            candles_after_compact,
            entry_price,
            direction,
            high_price,
            low_price
        )
        
        # Calculate pips
        config = get_symbol_config(symbol)
        if direction == "BUY":
            pips_favor = pips_from_price_change(high_price - entry_price, symbol)
            pips_against = pips_from_price_change(entry_price - low_price, symbol)
        else:
            pips_favor = pips_from_price_change(entry_price - low_price, symbol)
            pips_against = pips_from_price_change(high_price - entry_price, symbol)
        
        # AI Analysis
        ai_analysis = await analyze_error_with_claude(
            prediction,
            outcome,
            candles_at_prediction,
            candles_after_compact,
            fake_move_info
        )
        
        # Create error analysis record
        error_record = {
            "prediction_id": prediction_id,
            "outcome_id": outcome_id,
            "error_type": error_type,
            "prediction_direction": direction,
            "confidence_pct": prediction.get("ml_confidence"),
            "entry_price": entry_price,
            "target_price": prediction.get("ml_target_price"),
            "stop_price": prediction.get("ml_stop_price"),
            "actual_high": high_price,
            "actual_low": low_price,
            "exit_price": outcome.get("exit_price"),
            "pips_against": round(pips_against, 1),
            "pips_favor": round(pips_favor, 1),
            "is_fake_move": fake_move_info.get("is_fake", False),
            "fake_move_type": fake_move_info.get("type"),
            "analysis_status": "completed" if "error" not in ai_analysis else "failed",
            "ai_analysis": ai_analysis,
            "lesson_learned": ai_analysis.get("lesson_learned"),
            "improvement_suggestion": ai_analysis.get("pattern_to_avoid")
        }
        
        result = client.table("error_analysis").insert(error_record).execute()
        
        if result.get("data"):
            logger.info(f"Created error analysis for prediction {prediction_id}: {error_type}")
            
            # Create learning feedback if we have a clear lesson
            if ai_analysis.get("root_cause") and ai_analysis.get("lesson_learned"):
                await create_learning_feedback_from_analysis(
                    symbol,
                    ai_analysis,
                    result["data"][0].get("id")
                )
            
            return result["data"][0]
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to create error analysis: {e}")
        return None


async def create_learning_feedback_from_analysis(
    symbol: str,
    analysis: Dict[str, Any],
    error_id: str
) -> Optional[str]:
    """
    Create a learning feedback entry from error analysis.
    """
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    try:
        root_cause = analysis.get("root_cause", "unknown")
        confidence_should_be = analysis.get("confidence_should_have_been", 50)
        suggested_action = analysis.get("suggested_action", "HOLD")
        
        # Build condition based on root cause
        condition = {}
        action = {}
        
        if root_cause == "overbought_buy":
            condition = {"rsi_above": 70, "direction_attempted": "BUY"}
            action = {"reduce_confidence": 30, "add_warning": "RSI overbought - BUY risky"}
        elif root_cause == "oversold_sell":
            condition = {"rsi_below": 30, "direction_attempted": "SELL"}
            action = {"reduce_confidence": 30, "add_warning": "RSI oversold - SELL risky"}
        elif root_cause == "against_trend":
            condition = {"against_trend": True}
            action = {"reduce_confidence": 25, "add_warning": "Against main trend"}
        elif root_cause == "divergence_ignored":
            condition = {"divergence_present": True}
            action = {"reduce_confidence": 20, "add_warning": "Divergence detected"}
        elif root_cause == "fake_move":
            condition = {"high_volatility": True, "low_volume": True}
            action = {"reduce_confidence": 35, "add_warning": "Possible fake move conditions"}
        elif root_cause == "low_volume":
            condition = {"volume_ratio_below": 0.5}
            action = {"reduce_confidence": 15, "add_warning": "Low volume confirmation"}
        else:
            # Generic feedback
            condition = {"generic": True, "root_cause": root_cause}
            action = {"reduce_confidence": 10, "note": analysis.get("lesson_learned", "")}
        
        feedback = {
            "symbol": symbol,
            "feedback_type": "avoid_condition",
            "condition": condition,
            "action": action,
            "source_error_ids": [error_id],
            "strength": 0.5,
            "sample_count": 1,
            "is_active": True
        }
        
        result = client.table("learning_feedback").insert(feedback).execute()
        
        if result.get("data"):
            logger.info(f"Created learning feedback from error {error_id}")
            return result["data"][0].get("id")
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to create learning feedback: {e}")
        return None


async def check_and_analyze_failed_predictions(
    hours_ago: int = 4,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Check for failed predictions that need analysis.
    Run this periodically (e.g., every hour).
    
    Args:
        hours_ago: How old predictions should be before analysis
        limit: Maximum predictions to analyze per run
    
    Returns:
        List of created error analyses
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    try:
        # Find predictions that:
        # 1. Are at least X hours old
        # 2. Have an outcome marked as incorrect
        # 3. Don't have an error analysis yet
        cutoff = datetime.utcnow() - timedelta(hours=hours_ago)
        cutoff_iso = cutoff.isoformat() + "Z"
        
        # Get outcomes that are failures
        query = client.table("outcome_results").select(
            "id, prediction_id, ml_correct, hit_stop, hit_target"
        ).eq("ml_correct", False).lt("created_at", cutoff_iso).limit(limit * 2)
        
        result = query.execute()
        outcomes = result.get("data") or []
        
        if not outcomes:
            logger.debug("No failed predictions to analyze")
            return []
        
        # Check which ones don't have error analysis yet
        analyses_created = []
        
        for outcome in outcomes[:limit]:
            prediction_id = outcome.get("prediction_id")
            outcome_id = outcome.get("id")
            
            # Check if analysis exists
            existing = client.table("error_analysis").select("id").eq(
                "prediction_id", prediction_id
            ).execute()
            
            if existing.get("data"):
                continue  # Already analyzed
            
            # Create analysis
            analysis = await create_error_analysis(prediction_id, outcome_id)
            if analysis:
                analyses_created.append(analysis)
        
        logger.info(f"Created {len(analyses_created)} error analyses")
        return analyses_created
        
    except Exception as e:
        logger.error(f"Failed to check failed predictions: {e}")
        return []


async def get_active_learning_feedback(symbol: str) -> List[Dict[str, Any]]:
    """
    Get active learning feedback for a symbol to apply to predictions.
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    try:
        result = client.table("learning_feedback").select("*").eq(
            "is_active", True
        ).execute()
        
        feedbacks = result.get("data") or []
        
        # Filter by symbol (include both symbol-specific and general feedback)
        relevant = [
            f for f in feedbacks 
            if f.get("symbol") is None or f.get("symbol") == symbol
        ]
        
        return relevant
        
    except Exception as e:
        logger.error(f"Failed to get learning feedback: {e}")
        return []


async def apply_learning_feedback(
    symbol: str,
    direction: str,
    confidence: float,
    factors: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply learning feedback to adjust prediction confidence.
    
    Args:
        symbol: Trading symbol
        direction: Predicted direction
        confidence: Original confidence
        factors: Prediction factors
    
    Returns:
        Dict with adjusted confidence and warnings
    """
    feedbacks = await get_active_learning_feedback(symbol)
    
    if not feedbacks:
        return {
            "original_confidence": confidence,
            "adjusted_confidence": confidence,
            "adjustments": [],
            "warnings": []
        }
    
    adjusted = confidence
    adjustments = []
    warnings = []
    
    for fb in feedbacks:
        condition = fb.get("condition", {})
        action = fb.get("action", {})
        strength = fb.get("strength", 0.5)
        
        # Check if condition matches
        matches = True
        
        if "rsi_above" in condition:
            rsi = factors.get("rsi_14", 50)
            if rsi < condition["rsi_above"]:
                matches = False
        
        if "rsi_below" in condition:
            rsi = factors.get("rsi_14", 50)
            if rsi > condition["rsi_below"]:
                matches = False
        
        if "direction_attempted" in condition:
            if direction != condition["direction_attempted"]:
                matches = False
        
        if "volume_ratio_below" in condition:
            vol_ratio = factors.get("volume_ratio", 1.0)
            if vol_ratio > condition["volume_ratio_below"]:
                matches = False
        
        if matches:
            # Apply action
            if "reduce_confidence" in action:
                reduction = action["reduce_confidence"] * strength
                adjusted -= reduction
                adjustments.append({
                    "feedback_id": fb.get("id"),
                    "reason": fb.get("feedback_type"),
                    "reduction": reduction
                })
            
            if "add_warning" in action:
                warnings.append(action["add_warning"])
    
    return {
        "original_confidence": confidence,
        "adjusted_confidence": max(0, min(100, adjusted)),
        "adjustments": adjustments,
        "warnings": warnings
    }
