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

    2026-07-01 (rapor aksiyon #1 — TP1 breakeven semantiği):
    Sinyal daha önce TP1/TP2/TP3/TP4 vurmuşsa flip-close artık 'stopped' değil
    'completed' yazar (resolution_reason: {reason}_after_tp). Önceki davranış
    14 günde 1026 TP-görmüş sinyali kayıp saymıştı (XAUUSD+GDAXI).
    SIGNAL_BREAKEVEN_AFTER_TP1=0 ile eski davranışa dönülür.
    """
    try:
        existing_factors: Dict[str, Any] = {}
        tp_already_hit = False
        existing_result = (
            client.table("prediction_logs")
            .select("factors, targets_hit")
            .eq("id", signal_id)
            .limit(1)
            .execute()
        )
        existing_rows = safe_get_data(existing_result) or []
        if existing_rows:
            if isinstance(existing_rows[0].get("factors"), dict):
                existing_factors = dict(existing_rows[0]["factors"])
            raw_targets_hit = existing_rows[0].get("targets_hit")
            if isinstance(raw_targets_hit, str):
                try:
                    import json as _json
                    raw_targets_hit = _json.loads(raw_targets_hit)
                except Exception:
                    raw_targets_hit = {}
            if isinstance(raw_targets_hit, dict):
                tp_already_hit = any(bool(v) for v in raw_targets_hit.values())

        import os as _os
        breakeven_enabled = _os.getenv("SIGNAL_BREAKEVEN_AFTER_TP1", "1") != "0"

        existing_factors["close_reason"] = reason
        existing_factors["replaced_by_direction"] = new_direction

        if breakeven_enabled and tp_already_hit:
            final_status = "completed"
            final_reason = f"{reason}_after_tp"
            existing_factors["tp_hit_before_flip"] = True
        else:
            final_status = "stopped"
            final_reason = reason

        update_data = {
            "status": final_status,
            "resolution_reason": final_reason,
            "reentry_unlocked": True,
            "exit_time": _utc_iso(),
            "exit_price": exit_price,
            "factors": existing_factors,
        }
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data)
        if result and safe_get_data(result):
            logger.info(
                f"✅ Closed signal {signal_id[:8]}: {final_reason} -> {new_direction} "
                f"(status={final_status})"
            )
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


async def _apply_entry_optimizer(record: dict) -> dict:
    """Entry Optimizer geçişi — precision_veto SONRASI, insert ÖNCESİ.

    ENTRY_OPTIMIZER_MODE env'ine göre davranır:
      off (default) → record değişmez, optimizer hiç çağrılmaz
      shadow        → optimizer çağrılır + Supabase'e loglanır, record DEĞİŞMEZ
      enforce       → çağrılır + log + record entry/sl/tp DEĞİŞTİRİLİR

    Hata atmaz — exception olursa record olduğu gibi döner (sinyal kaybolmaz).
    """
    try:
        from services.shadow_executor import apply_entry_optimizer
        sig = {
            "symbol": record.get("symbol"),
            "direction": record.get("ml_direction"),
            "confidence": float(record.get("ml_confidence") or 0),
            "model_type": record.get("model_type"),
            "timeframe": record.get("timeframe"),
            "price": record.get("ml_entry_price"),
        }
        out = await apply_entry_optimizer(sig)
        # enforce mode'da out.entry_price/sl_price/tp_price gelir → record'a yansıt
        if out.get("entry_price") and out.get("entry_price") != sig.get("price"):
            record["ml_entry_price"] = float(out["entry_price"])
        if out.get("sl_price"):
            # record'ta stop_loss_pips var — entry'den pip cinsinden mesafe
            # Optimizer fiyat veriyor; conversion: ml_stop_price ekle
            record["ml_stop_price"] = float(out["sl_price"])
        if out.get("tp_price"):
            record["ml_target_price"] = float(out["tp_price"])
        if out.get("entry_optimizer_action"):
            if isinstance(record.get("factors"), dict):
                record["factors"]["entry_optimizer"] = {
                    "action": out["entry_optimizer_action"],
                    "priority": out.get("entry_optimizer_priority"),
                    "structure": out.get("structure_type"),
                    "max_wait_candles": out.get("max_wait_candles"),
                }
        return record
    except Exception as e:
        logger.warning("[entry-optimizer] hook hata — sinyal değişmedi: %s", e)
        return record


async def _apply_precision_veto(record: dict) -> bool:
    """Precision Veto Engine geçişi — sinyal prediction_logs'a yazılMADAN önce.

    Dönüş: True → sinyal yayınlanabilir; False → hard veto, bloklandı.
    Hard-veto / shadow / penalty durumları signal_vetoes'a loglanır.
    Penalty varsa record['ml_confidence'] düşürülür."""
    try:
        from services.precision_veto_service import check_signal, log_veto
        sig = {
            "symbol": record.get("symbol"),
            "direction": record.get("ml_direction"),
            "confidence": float(record.get("ml_confidence") or 0),
            "model_type": record.get("model_type"),
            "timeframe": record.get("timeframe"),
            "price": record.get("ml_entry_price"),
        }
        vr = await check_signal(sig)
        if vr.would_veto or vr.total_penalty > 0:
            await log_veto(vr, sig)
        if vr.vetoed:
            logger.info("[precision-veto] BLOKLANDI %s %s — stage%d/%s",
                        sig["symbol"], sig["direction"], vr.stage, vr.reason)
            return False
        if vr.adjusted_confidence and abs(vr.adjusted_confidence - sig["confidence"]) > 0.01:
            record["ml_confidence"] = round(vr.adjusted_confidence, 2)
            if isinstance(record.get("factors"), dict):
                record["factors"]["precision_veto_penalty"] = round(vr.total_penalty, 1)
        # Macro daily-bias context → persist onto the signal itself (prediction_logs
        # factors) so it lands next to the realized outcome. This is what makes the
        # "does aligning with the bias help?" question TRAINABLE — signal_vetoes only
        # keeps penalised/vetoed rows, but bonus (aligned) signals need capturing too.
        f = vr.features or {}
        if f.get("macro_bias_state") and isinstance(record.get("factors"), dict):
            record["factors"]["macro_bias"] = {
                "state": f.get("macro_bias_state"),
                "adjustment": f.get("macro_bias_adjustment"),
                "daily_bias_confidence": f.get("daily_bias_confidence"),
                "signal_aligns_with_bias": f.get("signal_aligns_with_bias"),
                "bias_is_invalidated": f.get("bias_is_invalidated"),
            }
        return True
    except Exception as e:
        logger.warning("[precision-veto] kontrol hatası — sinyal geçti: %s", e)
        return True


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
        snap = None
        try:
            from services.signal_feature_snapshot import build_signal_feature_snapshot
            snap = await build_signal_feature_snapshot(symbol)
            if snap:
                for k, v in snap.items():
                    factors.setdefault(k, v)
        except Exception as snap_err:
            logger.debug("signal_feature_snapshot enrich (smc) failed: %s", snap_err)

        # ── ATR merdiveni (2026-07-28 genelleme): SMC bu fonksiyona kendi
        # stop'unu geçirmiyor; mesafe, zaten çekilen snapshot'ın TF'e uygun
        # ATR'sinden türetilir (1.0×ATR). Snapshot/ATR yoksa legacy statik
        # merdiven kalır (fail-open).
        try:
            _atr_dist = _snapshot_atr_distance(snap, normalized_timeframe)
            if _atr_dist:
                _sl_guess = (parsed_entry_price - _atr_dist if direction == "BUY"
                             else parsed_entry_price + _atr_dist)
                _ladder = _atr_ladder_targets(
                    symbol, SMC_MODEL_TYPE, direction, parsed_entry_price, _sl_guess)
                if _ladder:
                    targets_dict = dict(_ladder["targets"])
                    stop_loss_pips = _ladder["stop_loss_pips"]
                    factors["target_type"] = "atr_ladder_v1"
                    factors["atr_ladder_sl_dist"] = _ladder["stop_loss_pips"]
        except Exception as _ladder_err:
            logger.debug("smc atr ladder skipped (%s): %s", symbol, _ladder_err)

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

        if not await _apply_precision_veto(record):
            return None
        # Entry Optimizer — shadow/enforce moduna göre çağrılır
        record = await _apply_entry_optimizer(record)
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

            # Shadow inversion for SMC (separate logger path) — mirror via the
            # generic log_prediction so the inverted "smc_inv" row gets standard
            # mirrored TP/SL + lifecycle resolution. Filters bypassed (shadow).
            if (entry_price and direction in ("BUY", "SELL")
                    and _shadow_inversion_enabled(symbol, SMC_MODEL_TYPE)):
                try:
                    inv_dir = "SELL" if direction == "BUY" else "BUY"
                    # ATR merdivenli SMC satırında aynayı aynı geometride tut —
                    # stop None kalırsa smc_inv legacy 30/50'ye düşer, kıyas bozulur.
                    inv_stop = None
                    if factors.get("target_type") == "atr_ladder_v1":
                        _sl_level = targets_dict.get("SL")
                        if _sl_level:
                            inv_stop = round(2 * parsed_entry_price - float(_sl_level), 4)
                    inv_ctx = {
                        "symbol": symbol,
                        "source": SMC_STRATEGY,
                        "ml_prediction": {
                            "direction": inv_dir,
                            "confidence": float(confidence or 0),
                            "entry_price": entry_price,
                            "target_price": None,
                            "stop_price": inv_stop,
                        },
                        "_shadow_inverted": True,
                    }
                    await log_prediction(
                        symbol, inv_ctx, {"final_decision": inv_dir}, normalized_timeframe,
                        SMC_STRATEGY, f"{SMC_MODEL_TYPE}_inv",
                        allow_parallel_active=True, bypass_quality_filters=True,
                    )
                except Exception as _inv_err:
                    logger.debug("smc shadow inversion failed (%s): %s", symbol, _inv_err)

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


def _ff_bool(factors: dict, key: str) -> Optional[bool]:
    v = factors.get(key)
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def _ff_float(factors: dict, key: str) -> Optional[float]:
    v = factors.get(key)
    try:
        return float(v) if v is not None and str(v) != "" else None
    except (TypeError, ValueError):
        return None


def _apply_ai_ops_filters(symbol: str, model_type: str, direction: str, factors: dict) -> Optional[str]:
    """Robust, OOS-validated AI-Ops filter rules (counterfactual simulator
    'robust'/OOS-positive verdicts only). Returns a block reason if the signal
    matches a known systematic-failure pattern, else None. Toggle with
    AI_OPS_FILTERS_ENABLED=0. Field names verified against live `factors`.
    """
    import os as _os
    if _os.getenv("AI_OPS_FILTERS_ENABLED", "1") != "1":
        return None
    s = (symbol or "").upper()
    m = (model_type or "").lower()
    d = (direction or "").upper()
    regime = (factors.get("regime_label") or "").lower()

    # 1) USOIL pulse2: BUY into a clear H4 downtrend  (+25.7pp, robust)
    if s == "USOIL.FOREX" and m == "pulse2" and d == "BUY" and factors.get("H4_ema_stack") == "down":
        return "USOIL pulse2 BUY vs H4 downtrend (ema_stack=down)"

    # 2) XAUUSD pulse1: SELL right on top of swing-low support  (+3.8pp OOS+)
    if s == "XAUUSD" and m == "pulse1" and d == "SELL" and _ff_bool(factors, "near_support"):
        swlow = _ff_float(factors, "M30_dist_swing_low_30_atr")
        if swlow is not None and swlow < 0.3 and regime != "strong_trend_down":
            return "XAUUSD pulse1 SELL into swing-low support (<0.3 ATR)"

    # 3) XAUUSD ml_cross: SELL into support with low RSI in transition/ranging  (+4.8pp, robust)
    if s == "XAUUSD" and m == "ml_cross_xau_nasdaq" and d == "SELL" and _ff_bool(factors, "near_support"):
        rsi = _ff_float(factors, "M30_rsi_14")
        if rsi is not None and rsi < 45 and regime in ("transition", "ranging"):
            return "XAUUSD ml_cross SELL into support + low RSI (bounce zone)"

    # 4) XAUUSD pulse3: SELL in transition while SAR is not bearish  (robust, big loss-avoid)
    if s == "XAUUSD" and m == "pulse3" and d == "SELL" and regime == "transition":
        if _ff_bool(factors, "sar_bearish") is False:
            return "XAUUSD pulse3 SELL in transition vs non-bearish SAR"

    return None


def _shadow_inversion_enabled(symbol: str, model_type: str) -> bool:
    """Whether to log a parallel inverted '<model>_inv' shadow signal for this
    (symbol, model). Lets us measure the real reverse win-rate honestly — the
    inverted row is resolved by the lifecycle with the same candles/spread.
    Disable with SHADOW_INVERSION_ENABLED=0.
    """
    import os as _os
    if _os.getenv("SHADOW_INVERSION_ENABLED", "1") != "1":
        return False
    syms = {s.strip().upper() for s in _os.getenv(
        "SHADOW_INVERSION_SYMBOLS", "NDX.INDX,GDAXI.INDX,XAUUSD").split(",") if s.strip()}
    if symbol.upper() not in syms:
        return False
    # "emel" listede DEĞİL: EMEL'in kendi adanmış ters modeli var (emel_inverse,
    # emel_pulse.py) — genel gölge de açıkken her EMEL sinyali 3 kez loglanıyordu
    # (emel + emel_inv + emel_inverse).
    models = {m.strip().lower() for m in _os.getenv(
        "SHADOW_INVERSION_MODELS",
        "pulse1,pulse2,pulse3,smc,meta,ml:main,ml_cross_xau_nasdaq").split(",") if m.strip()}
    return (model_type or "").lower() in models


# ─── ATR merdiveni (2026-07-28 NDX denetimi; aynı gün ml/emel/meta/smc'ye genellendi) ─
# Kanıt: backend/data/evolution/analyst_reports/pulse_ndx_denetimi_2026-07-28.md
# Statik TP30/SL50 merdiveni (RR 0.6) başabaş için %62.5 WR ister; 60 günde
# NDX'te HİÇBİR akış ulaşamadı (pulse BUY %32-41; ml:main %54.5, meta %55.1,
# emel %58, smc %33). Bu yardımcı sinyalin kendi SL mesafesinden RR≥1 merdiven
# kurar: SL=1.0×d, TP1..4 = 1.0/1.5/2.0/2.5×d (d = |entry − stop|).
# Lifecycle merdiveni factors.target_type == "atr_ladder_v1" etiketiyle tanır
# (statik ±%15 doğrulama bandına takılmadan). PULSE_ATR_LADDER=0 ile kapanır;
# model kapsamı PULSE_ATR_LADDER_MODELS (env adları tarihsel, pulse'ta doğdu).

_ATR_LADDER_DEFAULT_MODELS = "pulse1,pulse2,pulse3,ml,emel,emel_inverse,meta,smc"

#: SMC gibi kendi stop'unu geçmeyen modeller için snapshot ATR'sinden mesafe.
#: TF → tercih sırasıyla snapshot ATR anahtarı öneki (NDX snapshot: M15/H1/H4).
_SNAPSHOT_ATR_PREFS = {
    "1m": ("M15", "M30", "H1"), "5m": ("M15", "M30", "H1"),
    "15m": ("M15", "M30", "H1"), "20m": ("M15", "M30", "H1"),
    "30m": ("M30", "M15", "H1"),
    "1h": ("H1", "M30", "H4"), "4h": ("H4", "H1"), "1d": ("H4", "H1"),
}


def _snapshot_atr_distance(snap: Any, timeframe: str) -> Optional[float]:
    """Feature snapshot'tan sinyal TF'ine uygun ATR mesafesi (yoksa None)."""
    if not isinstance(snap, dict):
        return None
    prefs = _SNAPSHOT_ATR_PREFS.get((timeframe or "").lower(), ("M30", "M15", "H1"))
    for suffix in prefs:
        try:
            val = float(snap.get(f"{suffix}_atr_14"))
        except (TypeError, ValueError):
            continue
        if val > 0:
            return val
    return None


def _atr_ladder_targets(
    symbol: str,
    model_type: Optional[str],
    direction: str,
    entry_price: Optional[float],
    stop_price: Any,
) -> Optional[Dict[str, Any]]:
    """ATR tabanlı TP/SL merdiveni kur; koşullar sağlanmazsa None (legacy akış)."""
    import os as _os
    if _os.getenv("PULSE_ATR_LADDER", "1") == "0":
        return None
    syms = {s.strip().upper() for s in _os.getenv(
        "PULSE_ATR_LADDER_SYMBOLS", "NDX.INDX").split(",") if s.strip()}
    if (symbol or "").upper() not in syms:
        return None
    allowed = {m.strip().lower() for m in _os.getenv(
        "PULSE_ATR_LADDER_MODELS", _ATR_LADDER_DEFAULT_MODELS).split(",") if m.strip()}
    base = (model_type or "").lower().strip().split(":")[0]
    if base.endswith("_inv"):
        base = base[:-4]
    if base not in allowed:
        return None
    if direction not in ("BUY", "SELL") or not entry_price or entry_price <= 0:
        return None
    try:
        stop = float(stop_price) if stop_price is not None else None
    except (TypeError, ValueError):
        return None
    if stop is None or stop <= 0:
        return None
    # Mesafe yön-bağımsızdır (|entry−stop| = 1.0×ATR): pulse1 suggestion
    # geometrisi trend yönüne göre kurulduğundan stop bazen sinyalin ters
    # tarafında gelir — SL'i doğru tarafa burada kendimiz koyarız.
    dist = abs(entry_price - stop)
    # Sanite bandı: SL mesafesi girişin %0.04-%2'si arasında olmalı (NDX ~28000
    # için 11-560 puan) — bunun dışı bozuk panel verisidir, legacy'ye düş.
    if not (entry_price * 0.0004 <= dist <= entry_price * 0.02):
        return None
    sl_signed = entry_price - dist if direction == "BUY" else entry_price + dist
    mults_raw = _os.getenv("PULSE_ATR_LADDER_MULTS", "1.0,1.5,2.0,2.5")
    try:
        mults = [float(m) for m in mults_raw.split(",")]
    except ValueError:
        mults = [1.0, 1.5, 2.0, 2.5]
    if len(mults) != 4 or any(m <= 0 for m in mults) or mults != sorted(mults):
        mults = [1.0, 1.5, 2.0, 2.5]
    sgn = 1.0 if direction == "BUY" else -1.0
    targets = {
        f"TP{i + 1}": round(entry_price + sgn * dist * mult, 4)
        for i, mult in enumerate(mults)
    }
    targets["SL"] = round(sl_signed, 4)
    return {"targets": targets, "stop_loss_pips": round(dist, 2)}


async def log_prediction(
    symbol: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    timeframe: str = "1d",
    strategy: Optional[str] = None,
    model_type: Optional[str] = None,
    allow_parallel_active: bool = False,
    bypass_quality_filters: bool = False,  # shadow experiments: skip entry-quality + precision veto
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

        # ── ML INVERSION (ASYMMETRIC, env-gated) ────────────────────────────
        # Originally enabled 2026-05-18 as an experiment for XAUUSD + USOIL.
        # Disabled by default 2026-05-20 because the AI-Panel→MT5 bridge
        # is now the primary source for XAUUSD bot trades, and inverted
        # ML signals on prediction_logs were conflicting with the AI-Panel
        # direction (bot opens SELL while AI says BUY).
        #
        # To re-enable: env ML_INVERSION_ENABLED=1
        # History: see commit b151a1d for the experiment data.
        import os as _os
        _ml_invert_enabled = _os.getenv("ML_INVERSION_ENABLED", "0") == "1"
        ML_INVERSION_SYMBOLS = {"XAUUSD", "XAUUSD.FOREX", "USOIL.FOREX", "USOIL"}
        ml_invert_active = False
        original_direction = direction
        if (_ml_invert_enabled
                and symbol.upper() in ML_INVERSION_SYMBOLS
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

        # NOTE: Pulse inversion is NOT applied in-place here — the original
        # pulse signal is logged untouched. The inverted variant is emitted as
        # a SEPARATE shadow signal (model_type pulse1_inv/pulse2_inv, indices
        # only) by background_scheduler._maybe_log_pulse_inversion_shadow so we
        # can measure real inverted WR without altering the main system.

        effective_model_type, resolved_strategy = _resolve_logging_identity(model_type, strategy)
        # Güvenlik ağı: üretici clamp'lemeyi kaçırsa bile DB'ye asla [0,100]
        # dışı confidence yazma (canlı: pulse1/pulse3 101-105 kayıtları).
        raw_confidence = max(0.0, min(float(ml.get("confidence", 0.0)), 100.0))

        # ═══════════════════════════════════════════════════════════════════════
        # 0. MERKEZİ SİNYAL KAPILARI (signal_gates) — güvenlik ağı
        # Panel endpoint'leri kapıları kendi içinde uygular; burası panel dışı
        # üreticileri (background_scheduler SMC vb.) de kapsayan son savunma
        # hattıdır. Shadow deneyleri (bypass_quality_filters) kapsam dışıdır.
        # Rapor aksiyonları #2 (XAU SELL), #3 (GDAXI pulse1), #5 (seans), #9 (takvim).
        # ═══════════════════════════════════════════════════════════════════════
        if not bypass_quality_filters:
            try:
                from services.signal_gates import apply_signal_gates
                gated_direction, gate_notes = await apply_signal_gates(
                    symbol, direction, effective_model_type
                )
                if gated_direction != direction:
                    logger.info(
                        f"GATED: {symbol} {effective_model_type} {direction} -> HOLD | "
                        + "; ".join(gate_notes)
                    )
                    return None
            except Exception as gate_err:  # fail-open
                logger.warning(f"signal_gates safety net skipped (fail-open): {gate_err}")

        # ═══════════════════════════════════════════════════════════════════════
        # FILTERS: Session, Correlation, News
        # ═══════════════════════════════════════════════════════════════════════
        
        # 1. Session Filter
        should_filter, reason = _check_session_filter(symbol)
        if should_filter and not bypass_quality_filters:
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
        if should_filter and not bypass_quality_filters:
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
        if not allow_parallel_active and not bypass_quality_filters:
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
        pulse_ladder = None
        if entry_price and entry_price > 0:
            # XAUUSD v2 model emits a single-target risk profile (TP=$10, SL=$15);
            # honor it instead of the legacy TP1/2/3/4 ladder so lifecycle does not
            # trigger an early "completed" on a $4 TP1 the model never targeted.
            is_xauusd_v2 = (symbol == "XAUUSD"
                            and (effective_model_type or "").lower().startswith("ml")
                            and ml.get("target_price") and ml.get("stop_price"))
            pulse_ladder = _atr_ladder_targets(
                symbol, effective_model_type, direction, entry_price, ml.get("stop_price"))
            if is_xauusd_v2:
                tp_price = float(ml["target_price"])
                sl_price = float(ml["stop_price"])
                targets_dict = {"TP1": round(tp_price, 4)}
                targets_dict["SL"] = round(sl_price, 4)
                stop_loss_pips = abs(pips_from_price_change(abs(entry_price - sl_price), symbol))
            elif pulse_ladder:
                targets_dict = dict(pulse_ladder["targets"])
                stop_loss_pips = pulse_ladder["stop_loss_pips"]
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
        # Geometri epoch etiketi: lifecycle ATR merdivenini bu etiketten tanır;
        # analizler de eski (static_pips) / yeni (atr_ladder_v1) dönemi ayırır.
        factors["target_type"] = "atr_ladder_v1" if pulse_ladder else "static_pips"
        if pulse_ladder:
            factors["atr_ladder_sl_dist"] = pulse_ladder["stop_loss_pips"]
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

        # ── Entry-Quality Filter (Katman 1) ─────────────────────────────────
        # If a trained P(SL) classifier is available for this symbol, score
        # the entry features now and block if confidence-of-failure ≥
        # threshold. Tag the result either way so we can audit later.
        try:
            from services.entry_quality_service import score_entry
            eq = score_entry(
                symbol=symbol,
                direction=direction,
                ml_confidence=raw_confidence,
                factors=factors,
            )
            if eq.get("model_available"):
                factors["entry_quality_p_sl"] = eq.get("p_sl")
                factors["entry_quality_threshold"] = eq.get("threshold")
                if eq.get("should_block") and not bypass_quality_filters:
                    logger.info(
                        f"[EntryQuality] BLOCKED {symbol} {direction} — {eq.get('reason')}"
                    )
                    return None
        except Exception as eq_err:
            logger.debug(f"entry_quality scoring failed: {eq_err}")

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

        if not bypass_quality_filters:
            # AI-Ops learned filters (robust, OOS-validated) — block known
            # systematic-failure patterns. Shadow-inversion signals skip this.
            _ai_block = _apply_ai_ops_filters(symbol, effective_model_type, direction, factors)
            if _ai_block:
                logger.info("[ai-ops-filter] BLOCKED %s %s %s — %s",
                            symbol, effective_model_type, direction, _ai_block)
                return None
            if not await _apply_precision_veto(record):
                return None
            # Entry Optimizer — shadow/enforce moduna göre çağrılır
            record = await _apply_entry_optimizer(record)
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

            # ── Shadow inversion ────────────────────────────────────────────
            # Log the inverted signal as a parallel "<model>_inv" row so the
            # real reverse win-rate is measured honestly (lifecycle resolves it
            # with the same candles/spread/slippage as the original). Re-enters
            # log_prediction with the flipped direction + filters bypassed; the
            # "_inv" suffix guards against infinite recursion. Covers every model
            # that flows through here (pulse/emel/ml/meta/ml_cross); SMC has its
            # own hook in its logger.
            if (not (effective_model_type or "").endswith("_inv")
                    and not (model_type or "").endswith("_inv")
                    and direction in ("BUY", "SELL")
                    and _shadow_inversion_enabled(symbol, effective_model_type)):
                try:
                    inv_ml = dict(ml)
                    inv_ml["direction"] = "SELL" if direction == "BUY" else "BUY"
                    if pulse_ladder and entry_price:
                        # ATR merdivenli pulse satırında ayna geometriyi koru:
                        # None bırakmak _inv'i legacy 30/50 merdivene düşürür ve
                        # düz/ters kıyası farklı geometrilerde ölçülürdü.
                        _orig_tp, _orig_sp = ml.get("target_price"), ml.get("stop_price")
                        inv_ml["target_price"] = (
                            round(2 * entry_price - float(_orig_tp), 4) if _orig_tp else None)
                        inv_ml["stop_price"] = (
                            round(2 * entry_price - float(_orig_sp), 4) if _orig_sp else None)
                    else:
                        inv_ml["target_price"] = None
                        inv_ml["stop_price"] = None
                    inv_ml["probability_up"], inv_ml["probability_down"] = (
                        inv_ml.get("probability_down"), inv_ml.get("probability_up"))
                    inv_ctx = {**context, "ml_prediction": inv_ml, "_shadow_inverted": True}
                    inv_analysis = {**analysis, "final_decision": inv_ml["direction"]}
                    await log_prediction(
                        symbol, inv_ctx, inv_analysis, timeframe, stored_strategy,
                        f"{effective_model_type}_inv",
                        allow_parallel_active=True, bypass_quality_filters=True,
                    )
                except Exception as _inv_err:
                    logger.debug("shadow inversion log failed (%s %s): %s",
                                 symbol, effective_model_type, _inv_err)

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
