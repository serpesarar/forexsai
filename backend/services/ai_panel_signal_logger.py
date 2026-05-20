from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.ai_panel_analysis_service import NY_TZ, SYMBOL_PROFILES, _get_market_state, get_ai_panel_analysis
from services.prediction_logger import log_prediction
from utils.safe_supabase import safe_get_data

logger = logging.getLogger(__name__)

AI_PANEL_TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
AI_PANEL_LOG_INTERVAL = 3600
AI_PANEL_MODEL_TYPE = "ai_panel"
AI_PANEL_STRATEGY = "AI_PANEL_HOURLY"
AI_PANEL_TIMEFRAME = "1h"

# Symbols where the MT5 auto-trader should consume AI-Panel signals via the
# `meta_signals` table (the bot's source of truth). Override via env var
# AI_PANEL_BRIDGE_SYMBOLS (comma-separated) for a quick A/B test.
import os as _os
_env_bridge = _os.getenv("AI_PANEL_BRIDGE_SYMBOLS", "XAUUSD")
AI_PANEL_BRIDGE_SYMBOLS = {s.strip().upper() for s in _env_bridge.split(",") if s.strip()}

_last_ai_panel_log: Dict[str, datetime] = {}
_last_ai_panel_attempt: Dict[str, datetime] = {}
_last_ai_panel_success: Dict[str, datetime] = {}
_last_ai_panel_error: Dict[str, str] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    dt = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _get_last_persisted_snapshot_time(symbol: str) -> Optional[datetime]:
    if not is_db_available():
        return None

    client = get_supabase_client()
    if client is None:
        return None

    try:
        result = client.table("ai_panel_signal_snapshots").select("created_at").eq("symbol", symbol).order("created_at", desc=True).limit(1).execute()
        rows = safe_get_data(result) or []
        if not rows:
            return None
        return _parse_timestamp(rows[0].get("created_at"))
    except Exception as exc:
        logger.debug("AI panel snapshot lookup failed for %s: %s", symbol, exc)
        return None


def _resolve_last_log_time(symbol: str) -> Optional[datetime]:
    memory_last = _last_ai_panel_log.get(symbol)
    db_last = _get_last_persisted_snapshot_time(symbol)
    if memory_last and memory_last.tzinfo is None:
        memory_last = memory_last.replace(tzinfo=timezone.utc)
    if memory_last and db_last:
        return max(memory_last, db_last)
    return memory_last or db_last


def _refresh_window_bounds(symbol: str) -> tuple[int, int]:
    profile = SYMBOL_PROFILES.get(symbol) or {}
    primary_start = int(profile.get("ny_session_start") or (9 * 60 + 30))
    primary_end = int(profile.get("ny_session_end") or (16 * 60))
    us_cash_start = 9 * 60 + 30
    us_cash_end = 16 * 60
    return min(primary_start, us_cash_start), max(primary_end, us_cash_end)


def _is_extended_hours(symbol: str) -> bool:
    profile = SYMBOL_PROFILES.get(symbol) or {}
    return bool(profile.get("extended_hours_24x5"))


def _align_to_refresh_window(symbol: str, candidate: datetime) -> datetime:
    candidate_utc = candidate.astimezone(timezone.utc) if candidate.tzinfo else candidate.replace(tzinfo=timezone.utc)
    candidate_ny = candidate_utc.astimezone(NY_TZ)
    minutes_now = candidate_ny.hour * 60 + candidate_ny.minute

    # Extended-hours symbols (e.g. XAUUSD) trade nearly 24h on weekdays.
    # Any weekday minute is a valid refresh slot — no NY-session gating.
    if _is_extended_hours(symbol):
        if candidate_ny.weekday() < 5:
            return candidate_utc
        # Saturday/Sunday — push to next weekday 00:00 NY (gold opens Sun 18:00 NY,
        # but we wait until Monday for consistency with our hourly cron cadence).
        days_ahead = 1
        while True:
            next_day = candidate_ny + timedelta(days=days_ahead)
            if next_day.weekday() < 5:
                aligned = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
                return aligned.astimezone(timezone.utc)
            days_ahead += 1

    start_minutes, end_minutes = _refresh_window_bounds(symbol)
    if candidate_ny.weekday() < 5 and start_minutes <= minutes_now <= end_minutes:
        return candidate_utc

    if candidate_ny.weekday() < 5 and minutes_now < start_minutes:
        aligned = candidate_ny.replace(
            hour=start_minutes // 60,
            minute=start_minutes % 60,
            second=0,
            microsecond=0,
        )
        return aligned.astimezone(timezone.utc)

    days_ahead = 1
    while True:
        next_day = candidate_ny + timedelta(days=days_ahead)
        if next_day.weekday() < 5:
            aligned = next_day.replace(
                hour=start_minutes // 60,
                minute=start_minutes % 60,
                second=0,
                microsecond=0,
            )
            return aligned.astimezone(timezone.utc)
        days_ahead += 1


def _next_eligible_run_at(symbol: str, *, now: Optional[datetime] = None) -> datetime:
    current = now or _utc_now()
    last_log = _resolve_last_log_time(symbol)
    candidate = last_log + timedelta(seconds=AI_PANEL_LOG_INTERVAL) if last_log else current
    return _align_to_refresh_window(symbol, candidate)


def get_ai_panel_scheduler_status() -> Dict[str, Any]:
    now = _utc_now()
    symbols: list[Dict[str, Any]] = []

    for symbol in AI_PANEL_TRACKED_SYMBOLS:
        market_state = _get_market_state(symbol)
        last_log = _resolve_last_log_time(symbol)
        next_eligible = _next_eligible_run_at(symbol, now=now)
        window_open = bool(market_state.get("is_primary_session_open") or market_state.get("is_us_cash_open"))
        eligible_now = window_open and (last_log is None or (now - last_log).total_seconds() >= AI_PANEL_LOG_INTERVAL)

        symbols.append({
            "symbol": symbol,
            "window_open": window_open,
            "market_state": market_state,
            "last_attempt_at": _utc_iso(_last_ai_panel_attempt.get(symbol)),
            "last_success_at": _utc_iso(_last_ai_panel_success.get(symbol)),
            "last_persisted_snapshot_at": _utc_iso(_get_last_persisted_snapshot_time(symbol)),
            "last_resolved_run_at": _utc_iso(last_log),
            "last_error": _last_ai_panel_error.get(symbol),
            "next_eligible_at": _utc_iso(next_eligible),
            "eligible_now": eligible_now,
            "interval_seconds": AI_PANEL_LOG_INTERVAL,
        })

    return {
        "current_time": _utc_iso(now),
        "interval_seconds": AI_PANEL_LOG_INTERVAL,
        "tracked_symbols": symbols,
    }


def _coerce_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed



def _coerce_direction(value: Any) -> str:
    direction = str(value or "HOLD").upper().strip()
    if direction in {"BUY", "SELL", "HOLD", "NO_TRADE"}:
        return direction
    return "HOLD"



def _extract_signal_prices(claude_analysis: Dict[str, Any]) -> Dict[str, Optional[float]]:
    return {
        "entry": _coerce_float(claude_analysis.get("recommended_entry")),
        "stop": _coerce_float(claude_analysis.get("recommended_sl")),
        "target": _coerce_float(claude_analysis.get("recommended_tp")),
    }



def _build_prediction_context(symbol: str, result: Dict[str, Any]) -> Dict[str, Any]:
    claude_analysis = result.get("claude_analysis") or {}
    panel_signal = claude_analysis.get("panel_signal") or {}
    market_context = claude_analysis.get("market_context") or {}
    ta_snapshot = result.get("ta_snapshot") or {}
    prices = _extract_signal_prices(claude_analysis)

    return {
        "symbol": symbol,
        "source": "ai_panel_hourly",
        "ml_prediction": {
            "direction": _coerce_direction(claude_analysis.get("claude_direction")),
            "confidence": _coerce_float(claude_analysis.get("claude_confidence")) or 0.0,
            "entry_price": prices["entry"],
            "target_price": prices["target"],
            "stop_price": prices["stop"],
        },
        "ta": {
            "rsi_14": ta_snapshot.get("rsi_14") or ta_snapshot.get("rsi"),
            "macd_histogram": ta_snapshot.get("macd_histogram") or ta_snapshot.get("macd_hist"),
            "boll_zscore": ta_snapshot.get("boll_zscore"),
            "atr_pct": ta_snapshot.get("atr_pct"),
            "adx": ta_snapshot.get("adx"),
            "mfi": ta_snapshot.get("mfi"),
            "stoch_k": ta_snapshot.get("stoch_k"),
            "stoch_d": ta_snapshot.get("stoch_d"),
            "close": ta_snapshot.get("close"),
        },
        "distances": {},
        "volume": {},
        "trend_channel": {},
        "macro": {},
        "news": {
            "high_impact_count": len((panel_signal.get("event_risk") or {}).get("events") or []),
            "sentiment_score": 0,
        },
        "levels": {},
        "market_context": market_context,
        "ai_panel_signal": panel_signal,
    }



def _build_prediction_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    claude_analysis = result.get("claude_analysis") or {}
    market_context = claude_analysis.get("market_context") or {}
    regime = market_context.get("regime") or {}
    panel_signal = claude_analysis.get("panel_signal") or {}

    return {
        "final_decision": _coerce_direction(claude_analysis.get("claude_direction")),
        "confidence": _coerce_float(claude_analysis.get("claude_confidence")) or 0.0,
        "model_used": claude_analysis.get("model_used") or ((claude_analysis.get("analysis_meta") or {}).get("model")),
        "market_regime": {
            "trend": regime.get("trend_direction") or regime.get("regime"),
            "volatility": market_context.get("volatility_level"),
            "volume_confirmation": None,
        },
        "news_impact": {
            "tone": (panel_signal.get("event_risk") or {}).get("level"),
        },
    }



def _is_actionable_signal(result: Dict[str, Any]) -> bool:
    claude_analysis = result.get("claude_analysis") or {}
    direction = _coerce_direction(claude_analysis.get("claude_direction"))
    prices = _extract_signal_prices(claude_analysis)
    return direction in {"BUY", "SELL"} and all((prices["entry"], prices["stop"], prices["target"]))



def _snapshot_row(symbol: str, result: Dict[str, Any], prediction_log_id: Optional[str]) -> Dict[str, Any]:
    claude_analysis = result.get("claude_analysis") or {}
    panel_signal = claude_analysis.get("panel_signal") or {}
    analysis_meta = claude_analysis.get("analysis_meta") or {}
    direction = _coerce_direction(claude_analysis.get("claude_direction"))
    actionability = "actionable" if _is_actionable_signal(result) else "standby"

    return {
        "symbol": symbol,
        "timeframe": AI_PANEL_TIMEFRAME,
        "source": "hourly_scheduler",
        "direction": direction,
        "confidence": _coerce_float(claude_analysis.get("claude_confidence")) or 0.0,
        "market_session": analysis_meta.get("market_session"),
        "market_open": bool(analysis_meta.get("market_open")),
        "event_risk_level": ((panel_signal.get("event_risk") or {}).get("level") or "LOW"),
        "analysis_model": analysis_meta.get("model") or claude_analysis.get("model_used"),
        "prompt_version": analysis_meta.get("prompt_version"),
        "analysis_generated_at": analysis_meta.get("generated_at"),
        "actionability": actionability,
        "prediction_log_id": prediction_log_id,
        "signal_payload": panel_signal,
        "response_payload": result,
    }



def _ai_panel_to_meta_signals_row(
    symbol: str, result: Dict[str, Any], prediction_log_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Build a meta_signals row from an AI-Panel actionable signal.

    The MT5 auto-trader reads from `meta_signals`. By mirroring AI-Panel
    signals into that table (for symbols in AI_PANEL_BRIDGE_SYMBOLS), we
    can let the bot consume the higher-WR AI-Panel feed without changing
    the bot code. Returns None if signal isn't actionable / pieces missing.
    """
    if not _is_actionable_signal(result):
        return None
    claude_analysis = result.get("claude_analysis") or {}
    panel_signal = claude_analysis.get("panel_signal") or {}
    prices = _extract_signal_prices(claude_analysis)
    direction = _coerce_direction(claude_analysis.get("claude_direction"))
    confidence = _coerce_float(claude_analysis.get("claude_confidence")) or 0.0
    if direction not in ("BUY", "SELL") or not prices["entry"]:
        return None

    # Match meta engine's strength thresholds so the bot filter behaves
    # the same way: ≥75 STRONG, ≥55 MODERATE, else WEAK.
    if confidence >= 75:
        strength = "STRONG"
    elif confidence >= 55:
        strength = "MODERATE"
    else:
        strength = "WEAK"

    market_context = (claude_analysis.get("market_context") or {})
    regime_info = market_context.get("regime") or {}
    regime = regime_info.get("regime") or regime_info.get("trend_direction") or "UNKNOWN"

    entry = float(prices["entry"])
    stop = float(prices["stop"]) if prices["stop"] is not None else None
    target = float(prices["target"]) if prices["target"] is not None else None
    risk_reward = None
    if stop is not None and target is not None and entry != stop:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        risk_reward = round(reward / risk, 2) if risk > 0 else None

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": round(confidence, 1),
        "strength": strength,
        "source_combo": "ai_panel_hourly",
        "regime": regime,
        "agreement_ratio": 1.0,           # single-source signal, agreement is implicit
        "technical_score": 1.0,
        "passed_conditions": ["ai_panel:actionable"],
        "entry_price": round(entry, 4),
        "stop_loss": round(stop, 4) if stop is not None else None,
        "take_profit_1": round(target, 4) if target is not None else None,
        "take_profit_2": round(target, 4) if target is not None else None,
        "risk_reward": risk_reward,
        "model_breakdown": {
            "ai_panel": {
                "direction": direction,
                "confidence": confidence,
                "is_available": True,
                "agrees": True,
            }
        },
        "status": "active",
        # Bridge marker so downstream lifecycle / dashboard can distinguish
        # AI-Panel-sourced meta_signals from true 6-model meta signals.
        # Stored in model_breakdown to avoid migration; queries can filter
        # on this when needed.
    }


async def _mirror_ai_panel_to_meta_signals(
    symbol: str, result: Dict[str, Any], prediction_log_id: Optional[str]
) -> None:
    """Write the AI-Panel signal into meta_signals so the MT5 bot picks it up."""
    if symbol.upper() not in AI_PANEL_BRIDGE_SYMBOLS:
        return
    if not is_db_available():
        return
    client = get_supabase_client()
    if client is None:
        return
    row = _ai_panel_to_meta_signals_row(symbol, result, prediction_log_id)
    if row is None:
        logger.debug("AI-Panel bridge skipped (not actionable) for %s", symbol)
        return
    try:
        # Close any existing active row for this symbol+direction first so
        # the bot doesn't see overlapping AI-Panel signals.
        try:
            client.table("meta_signals").eq("symbol", symbol).eq(
                "status", "active"
            ).eq("source_combo", "ai_panel_hourly").update({"status": "closed"})
        except Exception as close_err:
            logger.debug("AI-Panel bridge prior-close failed (non-fatal): %s", close_err)
        client.table("meta_signals").insert(row)
        logger.info(
            "[AI-Panel→MT5] mirrored %s %s conf=%.0f strength=%s entry=%.4f",
            symbol, row["direction"], row["confidence"], row["strength"], row["entry_price"]
        )
    except Exception as e:
        logger.warning("AI-Panel meta_signals mirror failed for %s: %s", symbol, e)


async def log_ai_panel_signal(symbol: str) -> Optional[str]:
    result = await get_ai_panel_analysis(symbol, force_refresh=True)
    prediction_log_id: Optional[str] = None

    if _is_actionable_signal(result):
        context = _build_prediction_context(symbol, result)
        analysis = _build_prediction_analysis(result)
        prediction_log_id = await log_prediction(
            symbol=symbol,
            context=context,
            analysis=analysis,
            timeframe=AI_PANEL_TIMEFRAME,
            strategy=AI_PANEL_STRATEGY,
            model_type=AI_PANEL_MODEL_TYPE,
            allow_parallel_active=True,
        )
        # ── MT5 bridge: mirror AI-Panel signal into meta_signals so the
        # bot consumes the higher-WR AI-Panel feed (commit 2026-05-19,
        # XAUUSD only by default; AI_PANEL_BRIDGE_SYMBOLS env to extend).
        await _mirror_ai_panel_to_meta_signals(symbol, result, prediction_log_id)

    if is_db_available():
        client = get_supabase_client()
        if client is not None:
            snapshot = _snapshot_row(symbol, result, prediction_log_id)
            response = client.table("ai_panel_signal_snapshots").insert(snapshot)
            if response.get("error"):
                raise RuntimeError(f"AI panel snapshot persist failed for {symbol}: {response['error']}")
            logger.info(
                "AI panel snapshot persisted for %s (actionability=%s, prediction=%s)",
                symbol,
                snapshot.get("actionability"),
                prediction_log_id[:8] if prediction_log_id else "none",
            )

    return prediction_log_id



async def log_ai_panel_signals_if_needed() -> None:
    now = _utc_now()

    for symbol in AI_PANEL_TRACKED_SYMBOLS:
        market_state = _get_market_state(symbol)
        if not (market_state.get("is_primary_session_open") or market_state.get("is_us_cash_open")):
            continue

        last_log = _resolve_last_log_time(symbol)
        if last_log and (now - last_log).total_seconds() < AI_PANEL_LOG_INTERVAL:
            continue

        try:
            _last_ai_panel_attempt[symbol] = now
            prediction_log_id = await log_ai_panel_signal(symbol)
            _last_ai_panel_log[symbol] = now
            _last_ai_panel_success[symbol] = now
            _last_ai_panel_error.pop(symbol, None)
            logger.info(
                "AI panel hourly snapshot logged for %s (prediction=%s)",
                symbol,
                prediction_log_id[:8] if prediction_log_id else "none",
            )
        except Exception as exc:
            _last_ai_panel_error[symbol] = str(exc)
            logger.error("AI panel hourly logger failed for %s: %s", symbol, exc)
