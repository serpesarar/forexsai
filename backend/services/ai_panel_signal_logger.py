from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.ai_panel_analysis_service import get_ai_panel_analysis
from services.prediction_logger import log_prediction
from utils.safe_supabase import safe_get_data

logger = logging.getLogger(__name__)

AI_PANEL_TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
AI_PANEL_LOG_INTERVAL = 3600
AI_PANEL_MODEL_TYPE = "ai_panel"
AI_PANEL_STRATEGY = "AI_PANEL_HOURLY"
AI_PANEL_TIMEFRAME = "1h"

_last_ai_panel_log: Dict[str, datetime] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
        last_log = _resolve_last_log_time(symbol)
        if last_log and (now - last_log).total_seconds() < AI_PANEL_LOG_INTERVAL:
            continue

        try:
            prediction_log_id = await log_ai_panel_signal(symbol)
            _last_ai_panel_log[symbol] = now
            logger.info(
                "AI panel hourly snapshot logged for %s (prediction=%s)",
                symbol,
                prediction_log_id[:8] if prediction_log_id else "none",
            )
        except Exception as exc:
            logger.error("AI panel hourly logger failed for %s: %s", symbol, exc)
