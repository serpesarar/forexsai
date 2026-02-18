"""
Prediction Logger Service
Logs every ML + Claude prediction to database for future learning.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from database.supabase_client import get_supabase_client, is_db_available
from services.error_analysis_service import save_candle_snapshot

logger = logging.getLogger(__name__)

# ─── Cooldown tracking: prevent rapid signal churn ──────────────────────────
# After a signal completes/stops/expires, block new signals for same symbol+model
# for SIGNAL_COOLDOWN_SECONDS. This prevents the churn cycle:
#   create → complete/stop in 2min → create → repeat
SIGNAL_COOLDOWN_SECONDS = 900  # 15 minutes (30'dan düşürüldü)
_signal_cooldowns: Dict[str, datetime] = {}  # key = "symbol:model_type"


def calculate_targets(symbol: str, entry_price: float, direction: str):
    """Sembol bazlı TP/SL hesaplama"""
    if not entry_price or entry_price <= 0:
        return None
        
    multipliers = 1 if direction == "BUY" else -1
    
    if symbol in ["NDX.INDX", "GDAXI.INDX"]:
        # NASDAQ/DAX: 1 pip = 0.01
        pip_size = 0.01
        targets = {
            "TP1": round(entry_price + (15 * pip_size * multipliers), 2),
            "TP2": round(entry_price + (25 * pip_size * multipliers), 2),
            "TP3": round(entry_price + (35 * pip_size * multipliers), 2),
            "TP4": round(entry_price + (50 * pip_size * multipliers), 2),
            "SL": round(entry_price - (50 * pip_size * multipliers), 2)
        }
    elif symbol == "XAUUSD":
        # XAUUSD: 1 pip = 0.01 ($0.01)
        pip_size = 0.01
        targets = {
            "TP1": round(entry_price + (7 * pip_size * multipliers), 2),
            "TP2": round(entry_price + (12 * pip_size * multipliers), 2),
            "TP3": round(entry_price + (20 * pip_size * multipliers), 2),
            "TP4": round(entry_price + (30 * pip_size * multipliers), 2),
            "SL": round(entry_price - (10 * pip_size * multipliers), 2)
        }
    elif symbol == "CL.COMM":
        # US OIL: Yüzde bazlı
        targets = {
            "TP1": round(entry_price * (1 + 0.0002 * multipliers), 3),
            "TP2": round(entry_price * (1 + 0.0004 * multipliers), 3),
            "TP3": round(entry_price * (1 + 0.0006 * multipliers), 3),
            "TP4": round(entry_price * (1 + 0.0010 * multipliers), 3),
            "SL": round(entry_price * (1 - 0.0005 * multipliers), 3)
        }
    else:
        return None
    
    return targets


def _is_on_cooldown(symbol: str, model_type: str) -> bool:
    """DB-based cooldown check: Son sinyalden bu yana 15 dk geçti mi?"""
    try:
        client = get_supabase_client()
        if client is None:
            return False
            
        result = client.table("prediction_logs").select("created_at").eq(
            "symbol", symbol
        ).eq("model_type", model_type
        ).order("created_at", desc=True
        ).limit(1).execute()
        
        if result.get("data") and len(result["data"]) > 0:
            last_time_str = result["data"][0]["created_at"]
            # ISO format parsing (with or without Z)
            if last_time_str.endswith("Z"):
                last_time_str = last_time_str[:-1] + "+00:00"
            last_time = datetime.fromisoformat(last_time_str)
            
            # Ensure last_time has timezone info
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            
            elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
            
            if elapsed < SIGNAL_COOLDOWN_SECONDS:
                remaining = int(SIGNAL_COOLDOWN_SECONDS - elapsed)
                logger.info(f"⏱️ COOLDOWN: {symbol} {model_type} için {int(elapsed)}sn geçti, {remaining}sn kaldı")
                return True
    except Exception as e:
        logger.error(f"Cooldown check hatası: {e}")
    
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


async def log_prediction(
    symbol: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    timeframe: str = "1d",
    strategy: Optional[str] = None,
    model_type: Optional[str] = None,
) -> Optional[str]:
    """
    Log a prediction to the database.
    
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
        
        # ── Skip HOLD signals entirely — they create expired spam in DB ──
        if direction not in ("BUY", "SELL"):
            logger.debug(f"Skipping HOLD signal for {symbol} (model={model_type or strategy})")
            return None
        
        effective_model_type = model_type or (strategy.lower() if strategy else "ml")
        
        # ── Cooldown check: prevent rapid signal churn ──
        if _is_on_cooldown(symbol, effective_model_type):
            logger.info(f"🚫 COOLDOWN ENGELLENDİ: {symbol} {effective_model_type}")
            return None
        
        # ── Deduplication: Son 30dk içinde aynı symbol+model sinyali var mı? ──
        try:
            cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
            
            # Hem model_type hem strategy kontrolü yap
            existing = client.table("prediction_logs").select("id, created_at").eq(
                "symbol", symbol
            ).or_("model_type.eq.{},strategy.eq.{}".format(
                effective_model_type, 
                strategy or effective_model_type
            )).gt("created_at", cutoff_time
            ).limit(1).execute()
            
            if existing.get("data") and len(existing["data"]) > 0:
                logger.info(f"🚫 DUPLICATE BLOCKED: {symbol} {effective_model_type} son 30dk içinde mevcut")
                return existing["data"][0]["id"]
        except Exception as dedup_err:
            logger.warning(f"Dedup check failed (proceeding): {dedup_err}")
        
        # ── Calculate targets ──
        ml_entry_price = ml.get("entry_price")
        targets_data = calculate_targets(symbol, ml_entry_price, direction)
        if targets_data:
            # Update targets dict with calculated prices
            targets_dict = {
                "TP1": {"price": targets_data["TP1"], "hit": False},
                "TP2": {"price": targets_data["TP2"], "hit": False},
                "TP3": {"price": targets_data["TP3"], "hit": False},
                "TP4": {"price": targets_data["TP4"], "hit": False},
                "SL": {"price": targets_data["SL"], "hit": False}
            }
            # Add to record as JSON string
            import json as _json
            targets_json = _json.dumps(targets_data)
        else:
            targets_dict = {tl.name: {"price": None, "hit": False} for tl in cfg.targets}
            import json as _json
            targets_json = _json.dumps({tl.name: None for tl in cfg.targets})

        factors = _extract_factors(context, analysis)
        
        # Store strategy in both the column and factors JSONB
        if strategy:
            factors["strategy"] = strategy
            factors["source"] = context.get("source", strategy)
        
        # Compute lifecycle targets from target_config
        import json as _json
        from services.target_config import get_symbol_config
        cfg = get_symbol_config(symbol)
        targets_dict = {tl.name: tl.pips for tl in cfg.targets}

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
            "targets": targets_json,
            "stop_loss_pips": cfg.stoploss_pips,
            "targets_hit": _json.dumps({tp: False for tp in targets_dict}),
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
