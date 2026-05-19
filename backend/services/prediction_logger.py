"""
Prediction Logger Service
Logs every ML + Claude prediction to database for future learning.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from database.supabase_client import get_supabase_client, is_db_available
from services.error_analysis_service import save_candle_snapshot
from services.ml_scope_policy import normalize_ml_scope
from utils.market_hours import get_symbol_market_hours_label, is_symbol_market_open

logger = logging.getLogger(__name__)
SMC_MODEL_TYPE = "smc"
SMC_STRATEGY = "SMART_MONEY_ZONES"

def _utc_iso(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _normalize_timeframe(value: Optional[str]) -> str:
    normalized = (value or "").lower().strip()
    return normalized if normalized else "15m"


def _extract_candle_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, dict):
        timestamp_ms = value.get("timestamp") or value.get("time")
        if isinstance(timestamp_ms, (int, float)):
            return datetime.fromtimestamp(float(timestamp_ms) / 1000.0, tz=timezone.utc)
        date_text = value.get("date") or value.get("datetime")
        if isinstance(date_text, str) and date_text.strip():
            try:
                return datetime.fromisoformat(date_text.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                return None
    return None


def _has_fresh_intraday_market_data(symbol: str, *, now: Optional[datetime] = None, max_age_minutes: int = 20) -> Tuple[bool, Optional[float]]:
    try:
        from services.data_hub import get_candles

        candles = get_candles(symbol, "5m", limit=1)
        if not candles:
            return False, None

        latest_dt = _extract_candle_timestamp(candles[-1])
        if latest_dt is None:
            return False, None

        reference = now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)
        age_minutes = max((reference - latest_dt).total_seconds() / 60.0, 0.0)
        return age_minutes <= max_age_minutes, age_minutes
    except Exception:
        return False, None


def _resolve_logging_identity(
    model_type: Optional[str],
    strategy: Optional[str],
) -> Tuple[str, Optional[str]]:
    normalized_model_type = (model_type or "").lower().strip()
    normalized_strategy = normalize_ml_scope(strategy)
    scoped_from_model = normalize_ml_scope(normalized_model_type)

    if normalized_model_type.startswith("ml:") and scoped_from_model:
        return f"ml:{scoped_from_model}", normalized_strategy or scoped_from_model

    if normalized_model_type in {"", "ml"}:
        if normalized_strategy:
            return f"ml:{normalized_strategy}" if normalized_strategy != "main" else "ml:main", normalized_strategy
        return "ml", strategy

    if scoped_from_model:
        return f"ml:{scoped_from_model}" if scoped_from_model != "main" else "ml:main", normalized_strategy or scoped_from_model

    return normalized_model_type or (strategy.lower() if strategy else "ml"), strategy


_TIMEFRAME_COOLDOWN_MINUTES = {
    "5m": 5,
    "15m": 10,
    "30m": 20,
    "1h": 30,
    "4h": 120,
    "1d": 480,
}


def _is_within_cooldown(
    client,
    symbol: str,
    model_type: str,
    timeframe: Optional[str],
) -> bool:
    """
    Check if the most recent signal (any status) for this model/symbol/timeframe
    was created within the cooldown period.  Prevents signal spam from models
    whose signals get resolved very quickly.
    """
    try:
        tf = _normalize_timeframe(timeframe)
        cooldown_min = _TIMEFRAME_COOLDOWN_MINUTES.get(tf, 15)
        cutoff = _utc_iso(datetime.now(timezone.utc) - timedelta(minutes=cooldown_min))

        query = (
            client.table("prediction_logs")
            .select("id, created_at")
            .eq("symbol", symbol)
            .eq("model_type", model_type)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(1)
        )
        data = safe_get_data(query.execute()) or []
        if data:
            logger.debug(
                "Cooldown active for %s %s %s (last signal %s)",
                symbol, model_type, tf, data[0].get("created_at"),
            )
            return True
        return False
    except Exception as e:
        logger.error("Cooldown check error: %s", e)
        return False


def _has_active_signal(
    client,
    symbol: str,
    model_type: str,
    timeframe: Optional[str],
    direction: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if there's already an active signal for this symbol+model+timeframe+direction.
    Opposite-direction signals and different timeframes are allowed to stay active
    independently.
    """
    try:
        query = client.table("prediction_logs").select("id, ml_direction").eq(
            "symbol", symbol
        ).eq("model_type", model_type
        ).eq("status", "active")
        if model_type == "smc":
            query = query.eq("timeframe", _normalize_timeframe(timeframe))
        result = query.order("created_at", desc=True).limit(1).execute()
        
        data = safe_get_data(result) or []
        if data:
            row = data[0]
            row_direction = (row.get("ml_direction") or "").upper().strip()
            signal_id = row.get("id")
            logger.debug(
                "Active signal exists: %s %s dir=%s",
                symbol,
                model_type,
                row_direction,
            )
            return True, signal_id, row_direction
        
        return False, None, None
    except Exception as e:
        logger.error(f"Active signal check error: {e}")
        return False, None, None


def _close_existing_signal(
    client,
    signal_id: str,
    new_direction: str,
    exit_price: Optional[float],
    reason: str = "direction_flip",
):
    """
    Close existing signal when direction changes.
    This allows new signals to open when model flips direction.
    """
    try:
        existing_factors: Dict[str, Any] = {}
        existing_result = client.table("prediction_logs").select("factors").eq("id", signal_id).limit(1).execute()
        existing_rows = safe_get_data(existing_result) or []
        if existing_rows and isinstance(existing_rows[0].get("factors"), dict):
            existing_factors = dict(existing_rows[0]["factors"])

        existing_factors["close_reason"] = reason
        existing_factors["replaced_by_direction"] = new_direction

        update_data = {
            "status": "stopped",
            "resolution_reason": reason,
            "reentry_unlocked": True,
            "exit_time": _utc_iso(),
            "exit_price": exit_price,
            "factors": existing_factors,
        }
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data).execute()
        if result and safe_get_data(result):
            logger.info(f"✅ Closed signal {signal_id[:8]}: {reason} -> {new_direction}")
            return True
        return False
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
    Check if signal should be filtered based on session.
    Returns: (should_filter, reason)
    """
    now = datetime.now(timezone.utc)

    if not is_symbol_market_open(symbol, now):
        return True, f"Filtered: {symbol} market closed ({get_symbol_market_hours_label(symbol)})"

    has_fresh_data, age_minutes = _has_fresh_intraday_market_data(symbol, now=now)
    if not has_fresh_data:
        if age_minutes is None:
            return True, f"Filtered: stale intraday data for {symbol} (no recent 5m candle)"
        return True, f"Filtered: stale intraday data for {symbol} ({age_minutes:.1f}m old)"

    return False, ""


def _check_correlation_filter(
    symbol: str, 
    direction: str, 
    context: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Check correlation context and TAG signals — never block them.
    Returns: (should_filter=False always, reason_tag)
    
    NOTE: Correlation filter no longer blocks signals. Instead, it returns
    a reason string that gets stored in factors for analysis. Confidence
    is reduced in the caller when correlation disagrees.
    """
    macro = context.get("macro", {}) or {}
    
    # XAU/USD - DXY negative correlation (tag, don't block)
    if symbol == "XAUUSD":
        dxy = macro.get("dxy", {})
        dxy_change = dxy.get("change_24h", 0) or dxy.get("change_pct", 0)
        
        if dxy_change is not None:
            if direction == "BUY" and dxy_change > 0.3:
                return False, f"XAU BUY correlation_warning: DXY strengthening (+{dxy_change:.2f}%)"
            if direction == "SELL" and dxy_change < -0.3:
                return False, f"XAU SELL correlation_warning: DXY weakening ({dxy_change:.2f}%)"
    
    # NASDAQ - VIX context (tag, don't block)
    if symbol == "NDX.INDX":
        vix = macro.get("vix", {})
        vix_price = vix.get("price", 0)
        
        if vix_price and vix_price > 25:
            return False, f"NDX correlation_warning: High VIX ({vix_price})"
    
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


async def log_smc_prediction(
    symbol: str,
    timeframe: str,
    direction: str,
    confidence: Any,
    entry_price: Any,
    *,
    reasoning: Optional[list[Any]] = None,
) -> Optional[str]:
    if direction not in {"BUY", "SELL"}:
        return None

    should_filter, reason = _check_session_filter(symbol)
    if should_filter:
        logger.info(reason)
        return None

    normalized_timeframe = _normalize_timeframe(timeframe)

    try:
        parsed_entry_price = float(entry_price)
    except (TypeError, ValueError):
        return None
    if parsed_entry_price <= 0:
        return None

    try:
        raw_confidence = float(confidence)
    except (TypeError, ValueError):
        raw_confidence = 0.0
    if raw_confidence <= 1.0:
        raw_confidence *= 100.0
    raw_confidence = round(raw_confidence, 1)

    if not is_db_available():
        logger.debug("Database not available, skipping SMC prediction log.")
        return None

    client = get_supabase_client()
    if client is None:
        return None

    try:
        has_active, active_signal_id, active_direction = _has_active_signal(
            client,
            symbol,
            SMC_MODEL_TYPE,
            normalized_timeframe,
            direction,
        )

        if has_active:
            if active_direction == direction:
                logger.debug(
                    "Active %s SMC signal already exists for %s %s",
                    direction,
                    symbol,
                    normalized_timeframe,
                )
                return None

            if not active_signal_id:
                logger.warning(
                    "Active SMC signal lookup for %s %s returned no id; skipping insert",
                    symbol,
                    normalized_timeframe,
                )
                return None

            closed = _close_existing_signal(
                client,
                active_signal_id,
                direction,
                parsed_entry_price,
                reason="direction_flip",
            )
            if not closed:
                logger.warning(
                    "Failed to close active SMC signal %s for %s %s; skipping insert",
                    active_signal_id[:8],
                    symbol,
                    normalized_timeframe,
                )
                return None

        from services.target_config import calculate_stoploss_price, calculate_target_prices, pips_from_price_change

        target_prices = calculate_target_prices(parsed_entry_price, direction, symbol, normalized_timeframe)
        sl_price = calculate_stoploss_price(parsed_entry_price, direction, symbol, normalized_timeframe)
        targets_dict = dict(target_prices)
        targets_dict["SL"] = round(sl_price, 4)
        stop_loss_pips = abs(pips_from_price_change(abs(parsed_entry_price - sl_price), symbol))

        factors: Dict[str, Any] = {
            "session": _get_current_session(),
            "target_type": "static_pips",
            "strategy": SMC_STRATEGY,
            "source": SMC_STRATEGY,
        }
        if reasoning:
            factors["signal_reasoning"] = [str(item) for item in reasoning]

        # SMC enrich with feature snapshot (failsafe — same shared snapshot as ML logs)
        try:
            from services.signal_feature_snapshot import build_signal_feature_snapshot
            snap = await build_signal_feature_snapshot(symbol)
            if snap:
                for k, v in snap.items():
                    factors.setdefault(k, v)
        except Exception as snap_err:
            logger.debug("signal_feature_snapshot enrich (smc) failed: %s", snap_err)

        record = {
            "symbol": symbol,
            "timeframe": normalized_timeframe,
            "ml_direction": direction,
            "ml_confidence": raw_confidence,
            "ml_entry_price": parsed_entry_price,
            "claude_direction": direction,
            "claude_confidence": raw_confidence,
            "claude_model": SMC_STRATEGY,
            "factors": factors,
            "outcome_checked": False,
            "strategy": SMC_STRATEGY,
            "status": "active",
            "targets": targets_dict,
            "stop_loss_pips": stop_loss_pips,
            "targets_hit": {tp: False for tp in targets_dict if tp != "SL"},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "model_type": SMC_MODEL_TYPE,
        }

        result = client.table("prediction_logs").insert_ignore(record)

        if safe_get_error(result):
            logger.error(
                "prediction_logger.smc_insert_error | symbol=%s timeframe=%s dir=%s error=%s",
                symbol,
                normalized_timeframe,
                direction,
                result["error"],
            )
            return None

        if result.get("duplicate"):
            logger.debug(
                "DB dedup blocked active SMC %s %s %s signal",
                symbol,
                normalized_timeframe,
                direction,
            )
            return None

        if safe_get_data(result) and len(result["data"]) > 0:
            prediction_id = result["data"][0].get("id")
            logger.info(
                "prediction_logger.smc_logged | id=%s symbol=%s timeframe=%s dir=%s",
                prediction_id[:8] if prediction_id else "?",
                symbol,
                normalized_timeframe,
                direction,
            )
            return prediction_id

        return None

    except Exception as e:
        logger.error(
            "Failed to log SMC prediction for %s %s: %s",
            symbol,
            normalized_timeframe,
            e,
        )
        return None


async def log_prediction(
    symbol: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    timeframe: str = "1d",
    strategy: Optional[str] = None,
    model_type: Optional[str] = None,
    allow_parallel_active: bool = False,
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

        # ── ML INVERSION (ASYMMETRIC) for XAUUSD + USOIL ───────────────────
        # Live-data analysis 2026-05-18 (36h sample):
        #   Raw ML BUY  → inverted SELL → 72W/44L, +213 pip net (XAU)
        #                                 270 trades, +179 pip net (USOIL)
        #   Raw ML SELL → inverted BUY  →  0W/5L,  -140 pip net (XAU)
        #
        # Conclusion: ML model is MIS-CALIBRATED on the BUY side (current
        # market is mean-reverting after rallies; trend-trained model fires
        # BUY on EMA-cross conditions just before the reversal). SELL signals
        # are rare and accurate — flipping them destroyed value.
        #
        # Root cause: same as PULSE1's AGAINST_MTF_TREND_BUY / SAR_AGAINST_BUY
        # clusters — XAUUSD's recent regime is hostile to BUYs.
        # Rule #001/002 patched PULSE1; ML output was never guarded.
        # Inversion is the band-aid; root fix is model retraining or
        # ML-side BUY guards. Tracked as ml_direction_original in factors.
        ML_INVERSION_SYMBOLS = {"XAUUSD", "XAUUSD.FOREX", "USOIL.FOREX", "USOIL"}
        ml_invert_active = False
        original_direction = direction
        if (symbol.upper() in ML_INVERSION_SYMBOLS
                and (model_type or "").lower().startswith("ml")
                and direction == "BUY"):
            # Only invert BUY — SELL signals proven accurate, leave alone.
            direction = "SELL"
            ml_invert_active = True
            # Mirror ML's pre-computed TP/SL around entry so they point the
            # right way for the inverted direction.
            entry_p = ml.get("entry_price")
            if entry_p is not None:
                try:
                    e = float(entry_p)
                    for k in ("target_price", "stop_price"):
                        v = ml.get(k)
                        if v is not None:
                            ml[k] = round(2 * e - float(v), 6)
                except Exception:
                    pass
            logger.info(
                f"[ML-INVERT] {symbol} {model_type}: BUY → SELL (asymmetric, BUY-only)"
            )

        effective_model_type, resolved_strategy = _resolve_logging_identity(model_type, strategy)
        raw_confidence = float(ml.get("confidence", 0.0))
        
        # ═══════════════════════════════════════════════════════════════════════
        # FILTERS: Session, Correlation, News
        # ═══════════════════════════════════════════════════════════════════════
        
        # 1. Session Filter
        should_filter, reason = _check_session_filter(symbol)
        if should_filter:
            logger.info(f"FILTERED: {reason}")
            return None
        
        # 2. Correlation Context (DXY for XAU, VIX for NDX) — tag only, never block
        _correlation_tag = ""
        _, correlation_reason = _check_correlation_filter(symbol, direction, context)
        if correlation_reason:
            logger.info(f"CORRELATION TAG: {correlation_reason}")
            _correlation_tag = correlation_reason
            # Reduce confidence but DON'T block — let the signal be recorded for evaluation
            confidence *= 0.7
        
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
        normalized_timeframe = _normalize_timeframe(timeframe)
        new_signal_entry_price = ml.get("entry_price")
        entry_price = new_signal_entry_price or 0
        if not allow_parallel_active:
            has_active, active_signal_id, active_direction = _has_active_signal(
                client,
                symbol,
                effective_model_type,
                normalized_timeframe,
                direction,
            )
            
            if has_active:
                if active_direction == direction:
                    logger.debug(
                        "Active %s signal already exists for %s %s",
                        direction,
                        symbol,
                        effective_model_type,
                    )
                    return None

                if not active_signal_id:
                    logger.warning(
                        "Active signal lookup for %s %s returned no id; skipping insert",
                        symbol,
                        effective_model_type,
                    )
                    return None

                closed = _close_existing_signal(
                    client,
                    active_signal_id,
                    direction,
                    new_signal_entry_price,
                    reason="direction_flip",
                )
                if not closed:
                    logger.warning(
                        "Failed to close active signal %s for %s %s; skipping insert",
                        active_signal_id[:8],
                        symbol,
                        effective_model_type,
                    )
                    return None

        # ═══════════════════════════════════════════════════════════════════════
        # COOLDOWN: Prevent signal spam when previous signals resolve instantly
        # ═══════════════════════════════════════════════════════════════════════
        if _is_within_cooldown(client, symbol, effective_model_type, normalized_timeframe):
            logger.debug(
                "Cooldown active — skipping %s %s %s %s",
                symbol, effective_model_type, normalized_timeframe, direction,
            )
            return None

        # ═══════════════════════════════════════════════════════════════════════
        # STATIC TARGETS: Fixed pip-based TP/SL (Reverted from ATR)
        # ATR system removed - using fixed pip values from target_config
        # ═══════════════════════════════════════════════════════════════════════
        from services.target_config import (
            get_symbol_config,
            calculate_target_prices,
            calculate_stoploss_price,
            pips_from_price_change,
        )
        
        cfg = get_symbol_config(symbol)
        
        # Calculate actual price targets for DB storage using fixed pip values
        if entry_price and entry_price > 0:
            # XAUUSD v2 model emits a single-target risk profile (TP=$10, SL=$15);
            # honor it instead of the legacy TP1/2/3/4 ladder so lifecycle does not
            # trigger an early "completed" on a $4 TP1 the model never targeted.
            is_xauusd_v2 = (symbol == "XAUUSD"
                            and (effective_model_type or "").lower().startswith("ml")
                            and ml.get("target_price") and ml.get("stop_price"))
            if is_xauusd_v2:
                tp_price = float(ml["target_price"])
                sl_price = float(ml["stop_price"])
                targets_dict = {"TP1": round(tp_price, 4)}
                targets_dict["SL"] = round(sl_price, 4)
                stop_loss_pips = abs(pips_from_price_change(abs(entry_price - sl_price), symbol))
            else:
                target_prices = calculate_target_prices(entry_price, direction, symbol, normalized_timeframe)
                sl_price = calculate_stoploss_price(entry_price, direction, symbol, normalized_timeframe)
                targets_dict = dict(target_prices)
                targets_dict["SL"] = round(sl_price, 4)
                stop_loss_pips = abs(pips_from_price_change(abs(entry_price - sl_price), symbol))
        else:
            targets_dict = {tl.name: tl.pips for tl in cfg.targets}
            targets_dict["SL"] = cfg.stoploss_pips
            stop_loss_pips = cfg.stoploss_pips
        
        factors = _extract_factors(context, analysis)
        factors["session"] = _get_current_session()
        factors["target_type"] = "static_pips"
        if _correlation_tag:
            factors["correlation_warning"] = _correlation_tag

        # Store strategy in both the column and factors JSONB
        stored_strategy = resolved_strategy or strategy
        if stored_strategy:
            factors["strategy"] = stored_strategy
            factors["source"] = context.get("source", stored_strategy)
        if allow_parallel_active:
            factors["parallel_active_allowed"] = True

        # ── Enrich with comprehensive feature snapshot (failsafe) ──
        # Adds ~60 fields covering momentum, trend, S/R, exhaustion, macro, session
        # so that the AI-ops loop can later cluster and analyze failures.
        try:
            from services.signal_feature_snapshot import build_signal_feature_snapshot
            snap = await build_signal_feature_snapshot(symbol)
            if snap:
                # Caller-provided values take precedence; snapshot fills the gaps.
                for k, v in snap.items():
                    factors.setdefault(k, v)
        except Exception as snap_err:
            logger.debug("signal_feature_snapshot enrich failed: %s", snap_err)

        # Tag inversion in factors so analytics can compare inverted vs raw
        if ml_invert_active:
            factors["ml_direction_original"] = original_direction
            factors["ml_inverted"] = True

        record = {
            "symbol": symbol,
            "timeframe": normalized_timeframe,
            "ml_direction": direction,
            "ml_confidence": raw_confidence,
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
            "targets": targets_dict,
            "stop_loss_pips": stop_loss_pips,
            "targets_hit": {tp: False for tp in targets_dict if tp != "SL"},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "model_type": effective_model_type,
        }
        
        if stored_strategy:
            record["strategy"] = stored_strategy
        
        result = client.table("prediction_logs").insert_ignore(record)

        if safe_get_error(result):
            logger.error(
                "prediction_logger.insert_error | symbol=%s model=%s strategy=%s dir=%s error=%s",
                symbol,
                effective_model_type,
                stored_strategy,
                direction,
                result["error"],
            )
            return None
        
        # If a remote environment still has a stricter unique constraint, insert_ignore
        # may still reject overlaps. Local schema does not require that behavior.
        if result.get("duplicate"):
            logger.debug(
                "DB dedup blocked active %s %s %s %s signal",
                symbol,
                effective_model_type,
                normalized_timeframe,
                direction,
            )
            return None

        if safe_get_data(result) and len(result["data"]) > 0:
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
        return safe_get_data(result)
        
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
        if safe_get_error(result):
            logger.error(f"Failed to mark prediction {prediction_id} checked: {result['error']}")
            return False
        data = safe_get_data(result)
        if not data or len(data) == 0:
            logger.warning(f"mark_prediction_checked: update returned empty data for {prediction_id[:8]}, result={result}")
            return False
        logger.info(f"Marked prediction {prediction_id[:8]} as checked, rows affected: {len(data)}")
        return True
    except Exception as e:
        logger.error(f"Failed to mark prediction checked: {e}")
        return False
