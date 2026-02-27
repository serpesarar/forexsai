"""
Prediction Logger Service
Logs every ML + Claude prediction to database for future learning.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from database.supabase_client import get_supabase_client, is_db_available
from services.error_analysis_service import save_candle_snapshot

logger = logging.getLogger(__name__)

# ─── Uses target_config.py as single source of truth for TP/SL levels ──────────


def _has_active_signal(client, symbol: str, model_type: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if there's already an active signal for this symbol+model.
    Returns: (has_active, signal_id, current_direction)
    """
    try:
        result = client.table("prediction_logs").select("id, ml_direction").eq(
            "symbol", symbol
        ).eq("model_type", model_type
        ).eq("status", "active"
        ).limit(1).execute()
        
        data = result.get("data") or []
        has_active = len(data) > 0
        
        if has_active:
            signal_id = data[0].get("id")
            current_dir = data[0].get("ml_direction")
            logger.debug(f"Active signal exists: {symbol} {model_type} dir={current_dir}")
            return True, signal_id, current_dir
        
        return False, None, None
    except Exception as e:
        logger.error(f"Active signal check error: {e}")
        return False, None, None


def _close_existing_signal(client, signal_id: str, new_direction: str, reason: str = "direction_change"):
    """
    Close existing signal when direction changes.
    This allows new signals to open when model flips direction.
    """
    try:
        from datetime import datetime
        update_data = {
            "status": "stopped",
            "exit_time": datetime.utcnow().isoformat() + "Z",
            "exit_price": None,  # Will be filled by lifecycle
            "factors": {
                "close_reason": reason,
                "replaced_by_direction": new_direction,
            }
        }
        client.table("prediction_logs").eq("id", signal_id).update(update_data)
        logger.info(f"Closed signal {signal_id[:8]}: {reason} -> {new_direction}")
        return True
    except Exception as e:
        logger.error(f"Failed to close signal {signal_id}: {e}")
        return False


def _extract_factors(context: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant factors from context and analysis for storage.
    These factors will be used later for learning/correlation analysis.
    """
    factors = {}
    
    ta = context.get("ta", {}) or {}
    factors["rsi_14"] = ta.get("rsi_14")
    factors["rsi_7"] = ta.get("rsi_7")
    factors["macd_histogram"] = ta.get("macd_histogram")
    factors["boll_zscore"] = ta.get("boll_zscore")
    factors["atr_pct"] = ta.get("atr_pct")
    factors["adx"] = ta.get("adx")
    factors["mfi"] = ta.get("mfi")
    factors["willr"] = ta.get("willr")
    factors["momentum"] = ta.get("momentum")
    factors["stoch_k"] = ta.get("stoch_k")
    factors["stoch_d"] = ta.get("stoch_d")
    
    distances = context.get("distances", {}) or {}
    factors["ema20_distance_pct"] = distances.get("ema20_pct")
    factors["ema50_distance_pct"] = distances.get("ema50_pct")
    factors["ema200_distance_pct"] = distances.get("ema200_pct")
    
    volume = context.get("volume", {}) or {}
    factors["volume_ratio"] = volume.get("ratio")
    factors["volume_last"] = volume.get("last")
    factors["volume_avg20"] = volume.get("avg20")
    
    channel = context.get("trend_channel", {}) or {}
    factors["channel_slope"] = channel.get("slope")
    factors["channel_position"] = channel.get("position")
    
    macro = context.get("macro", {}) or {}
    factors["vix"] = (macro.get("vix") or {}).get("price")
    factors["dxy"] = (macro.get("dxy") or {}).get("price")
    factors["usdtry"] = (macro.get("usdtry") or {}).get("price")
    
    news = context.get("news", {}) or {}
    factors["news_count"] = news.get("count", 0)
    
    market_regime = analysis.get("market_regime", {}) or {}
    factors["trend"] = market_regime.get("trend")
    factors["volatility"] = market_regime.get("volatility")
    factors["volume_confirmation"] = market_regime.get("volume_confirmation")
    
    news_impact = analysis.get("news_impact", {}) or {}
    factors["news_tone"] = news_impact.get("tone")
    
    factors = {k: v for k, v in factors.items() if v is not None}
    
    return factors


def _get_current_session() -> str:
    """Get current trading session for filtering"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    # London: 08:00-17:00 UTC
    # NY: 13:00-22:00 UTC  
    # Overlap: 13:00-17:00 UTC (highest volatility)
    
    if 13 <= hour < 17:
        return "overlap"      # London-NY overlap
    elif 8 <= hour < 13:
        return "europe"       # London only
    elif 13 <= hour < 22:
        return "us"           # NY only
    elif 0 <= hour < 8:
        return "asia"         # Asia session
    else:
        return "closed"       # After hours


def _check_session_filter(symbol: str) -> Tuple[bool, str]:
    """
    Check if signal should be filtered based on session
    Returns: (should_filter, reason)
    """
    session = _get_current_session()
    
    # XAU/USD: Avoid Asia session (low volatility, false signals)
    if symbol == "XAUUSD" and session == "asia":
        return True, f"XAU/USD filtered: Asia session (low liquidity)"
    
    # All symbols: Avoid closed/after hours
    if session == "closed":
        return True, f"{symbol} filtered: Market closed/after hours"
    
    return False, ""


def _check_correlation_filter(
    symbol: str, 
    direction: str, 
    context: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Check if signal should be filtered based on correlations
    Returns: (should_filter, reason)
    """
    macro = context.get("macro", {}) or {}
    
    # XAU/USD - DXY negative correlation
    if symbol == "XAUUSD":
        dxy = macro.get("dxy", {})
        dxy_change = dxy.get("change_24h", 0) or dxy.get("change_pct", 0)
        
        if dxy_change is not None:
            # If DXY is strongly up, avoid XAU BUY
            if direction == "BUY" and dxy_change > 0.3:
                return True, f"XAU BUY filtered: DXY strengthening (+{dxy_change:.2f}%)"
            # If DXY is strongly down, avoid XAU SELL
            if direction == "SELL" and dxy_change < -0.3:
                return True, f"XAU SELL filtered: DXY weakening ({dxy_change:.2f}%)"
    
    # NASDAQ - VIX filter (high VIX = avoid new positions)
    if symbol == "NDX.INDX":
        vix = macro.get("vix", {})
        vix_price = vix.get("price", 0)
        
        if vix_price and vix_price > 25:
            return True, f"NDX filtered: High VIX ({vix_price}) - market fear"
    
    return False, ""


def _check_news_filter(context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if signal should be filtered due to high-impact news
    Returns: (should_filter, reason)
    """
    news = context.get("news", {}) or {}
    high_impact_count = news.get("high_impact_count", 0)
    sentiment_score = news.get("sentiment_score", 0)
    
    # Filter if too many high-impact news in last hour
    if high_impact_count >= 3:
        return True, f"Filtered: {high_impact_count} high-impact news events"
    
    # Filter if extreme sentiment (market panic/euphoria)
    if sentiment_score and abs(sentiment_score) > 0.8:
        return True, f"Filtered: Extreme sentiment ({sentiment_score:.2f})"
    
    return False, ""


async def log_prediction(
    symbol: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    timeframe: str = "1d",
    strategy: Optional[str] = None,
    model_type: Optional[str] = None,
) -> Optional[str]:
    """
    Log a prediction to the database with session, correlation and news filters.
    Uses adaptive TP/SL based on ATR and market conditions.
    
    Args:
        symbol: Trading symbol (e.g., "NDX.INDX", "XAUUSD")
        context: Full context pack from detailed analysis
        analysis: Claude's analysis response
        timeframe: Timeframe of analysis
    
    Returns:
        prediction_id (UUID string) if successful, None otherwise
    """
    if not is_db_available():
        logger.debug("Database not available, skipping prediction log.")
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    try:
        ml = context.get("ml_prediction", {}) or {}
        direction = ml.get("direction", "HOLD")
        confidence = float(ml.get("confidence", 0.5))
        
        # ── Skip HOLD signals entirely — they create expired spam in DB ──
        if direction not in ("BUY", "SELL"):
            logger.debug(f"Skipping HOLD signal for {symbol} (model={model_type or strategy})")
            return None
        
        effective_model_type = model_type or (strategy.lower() if strategy else "ml")
        
        # ═══════════════════════════════════════════════════════════════════════
        # FILTERS: Session, Correlation, News
        # ═══════════════════════════════════════════════════════════════════════
        
        # 1. Session Filter
        should_filter, reason = _check_session_filter(symbol)
        if should_filter:
            logger.info(f"FILTERED: {reason}")
            return None
        
        # 2. Correlation Filter (DXY for XAU, VIX for NDX)
        should_filter, reason = _check_correlation_filter(symbol, direction, context)
        if should_filter:
            logger.info(f"FILTERED: {reason}")
            return None
        
        # 3. News Filter
        should_filter, reason = _check_news_filter(context)
        if should_filter:
            logger.info(f"FILTERED: {reason}")
            return None
        
        # ═══════════════════════════════════════════════════════════════════════
        # 4. Multi-Timeframe Confirmation
        # ═══════════════════════════════════════════════════════════════════════
        from services.mtf_confirmation import confirm_signal_mtf
        
        # Get MTF signals from context (if available)
        mtf_signals = context.get("mtf_signals", {}) or {}
        if not mtf_signals:
            # Try to extract from analysis
            mtf_signals = analysis.get("timeframe_signals", {})
        
        if mtf_signals:
            should_take, mtf_reason, mtf_details = await confirm_signal_mtf(
                symbol, direction, mtf_signals
            )
            
            # Store MTF details in factors for reference
            context["mtf_confirmation"] = {
                "passed": should_take,
                "reason": mtf_reason,
                "details": mtf_details,
            }
            
            if not should_take:
                logger.info(f"FILTERED (MTF): {mtf_reason}")
                # Don't return None - just log the disagreement but allow signal
                # This is configurable based on strictness preference
                # For now, we allow but mark as low confidence
                confidence *= 0.7  # Reduce confidence due to MTF disagreement
        
        # ═══════════════════════════════════════════════════════════════════════
        # ACTIVE SIGNAL HANDLING: Direction Change Logic
        # ═══════════════════════════════════════════════════════════════════════
        has_active, active_signal_id, active_direction = _has_active_signal(client, symbol, effective_model_type)
        
        if has_active:
            if active_direction == direction:
                # Same direction - skip duplicate
                logger.debug(f"Active {direction} signal already exists for {symbol} {effective_model_type}")
                return None
            else:
                # Direction changed! Close old signal and allow new one
                logger.info(f"Direction change detected: {active_direction} -> {direction} for {symbol} {effective_model_type}")
                _close_existing_signal(client, active_signal_id, direction, "direction_flip")

        # ═══════════════════════════════════════════════════════════════════════
        # STATIC TARGETS: Fixed pip-based TP/SL (Reverted from ATR)
        # ATR system removed - using fixed pip values from target_config
        # ═══════════════════════════════════════════════════════════════════════
        import json as _json
        from services.target_config import get_symbol_config, calculate_target_prices, calculate_stoploss_price
        
        cfg = get_symbol_config(symbol)
        entry_price = ml.get("entry_price") or 0
        
        # Calculate actual price targets for DB storage using fixed pip values
        if entry_price and entry_price > 0:
            target_prices = calculate_target_prices(entry_price, direction, symbol)
            sl_price = calculate_stoploss_price(entry_price, direction, symbol)
            # Store as {TP1: price, TP2: price, ...}
            targets_dict = target_prices
            targets_dict["SL"] = round(sl_price, 4)
            stop_loss_pips = cfg.stoploss_pips
        else:
            targets_dict = {tl.name: tl.pips for tl in cfg.targets}
            targets_dict["SL"] = cfg.stoploss_pips
            stop_loss_pips = cfg.stoploss_pips
        
        factors = _extract_factors(context, analysis)
        factors["session"] = _get_current_session()
        factors["target_type"] = "static_pips"
        
        # Store strategy in both the column and factors JSONB
        if strategy:
            factors["strategy"] = strategy
            factors["source"] = context.get("source", strategy)

        record = {
            "symbol": symbol,
            "timeframe": timeframe,
            "ml_direction": direction,
            "ml_confidence": float(ml.get("confidence", 0.0)),
            "ml_probability_up": ml.get("probability_up"),
            "ml_probability_down": ml.get("probability_down"),
            "ml_target_price": ml.get("target_price"),
            "ml_stop_price": ml.get("stop_price"),
            "ml_entry_price": ml.get("entry_price"),
            "claude_direction": analysis.get("final_decision"),
            "claude_confidence": analysis.get("confidence"),
            "claude_model": analysis.get("model_used"),
            "factors": factors,
            "outcome_checked": False,
            # Signal Lifecycle columns
            "status": "active" if direction in ("BUY", "SELL") else "expired",
            "targets": _json.dumps(targets_dict),
            "stop_loss_pips": stop_loss_pips,
            "targets_hit": _json.dumps({tp: False for tp in targets_dict if tp != "SL"}),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "model_type": model_type or (strategy.lower() if strategy else "ml"),
        }
        
        # Add strategy column if provided (user has this column in Supabase)
        if strategy:
            record["strategy"] = strategy
        
        result = client.table("prediction_logs").insert_ignore(record)
        
        # DB-level dedup: unique index on (symbol, model_type, ml_direction) WHERE status='active'
        if result.get("duplicate"):
            logger.debug(f"DB dedup: active {effective_model_type} {direction} signal already exists for {symbol}")
            return None

        if result.get("data") and len(result["data"]) > 0:
            prediction_id = result["data"][0].get("id")
            logger.info(f"prediction_logger.logged | id={prediction_id[:8] if prediction_id else '?'} symbol={symbol} model={effective_model_type} dir={direction}")
            
            # Save candle snapshot for later error analysis (self-learning)
            try:
                indicators = {
                    "rsi_14": factors.get("rsi_14"),
                    "macd_histogram": factors.get("macd_histogram"),
                    "boll_zscore": factors.get("boll_zscore"),
                    "atr_pct": factors.get("atr_pct"),
                    "adx": factors.get("adx"),
                }
                levels = {
                    "support": context.get("levels", {}).get("support", []),
                    "resistance": context.get("levels", {}).get("resistance", []),
                }
                await save_candle_snapshot(
                    prediction_id=prediction_id,
                    symbol=symbol,
                    snapshot_type="at_prediction",
                    indicators=indicators,
                    levels=levels
                )
            except Exception as snap_err:
                logger.warning(f"Could not save candle snapshot: {snap_err}")
            
            return prediction_id
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to log prediction: {e}")
        return None


async def get_recent_predictions(
    symbol: Optional[str] = None,
    limit: int = 50,
    unchecked_only: bool = False
) -> list:
    """
    Get recent predictions from database.
    
    Args:
        symbol: Filter by symbol (optional)
        limit: Max number of records
        unchecked_only: Only return predictions without outcome check
    
    Returns:
        List of prediction records
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    try:
        query = client.table("prediction_logs").select("*")
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        if unchecked_only:
            query = query.eq("outcome_checked", False)
        
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.get("data") or []
        
    except Exception as e:
        logger.error(f"Failed to get predictions: {e}")
        return []


async def mark_prediction_checked(prediction_id: str) -> bool:
    """Mark a prediction as having its outcome checked."""
    if not is_db_available():
        return False
    
    client = get_supabase_client()
    if client is None:
        return False
    
    try:
        result = client.table("prediction_logs").eq("id", prediction_id).update(
            {"outcome_checked": True}
        )
        if result.get("error"):
            logger.error(f"Failed to mark prediction {prediction_id} checked: {result['error']}")
            return False
        data = result.get("data")
        if not data or len(data) == 0:
            logger.warning(f"mark_prediction_checked: update returned empty data for {prediction_id[:8]}, result={result}")
            return False
        logger.info(f"Marked prediction {prediction_id[:8]} as checked, rows affected: {len(data)}")
        return True
    except Exception as e:
        logger.error(f"Failed to mark prediction checked: {e}")
        return False
