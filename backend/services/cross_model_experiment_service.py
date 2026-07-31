"""
Cross-Model Experiment — NASDAQ ML model applied to XAUUSD data
================================================================

Hypothesis (user-driven, 2026-05-20): the bespoke XAUUSD v2 model has been
losing on live execution. Maybe the NASDAQ 150-feature LightGBM picks up
different patterns that translate better. This experiment runs the NASDAQ
model file against XAUUSD candle data and logs predictions through the
same lifecycle so we can measure win-rate / net-pips on the same footing
as every other model.

Isolation guarantees (CRITICAL — must not pollute production):
  - Distinct model_type:  "ml_cross_xau_nasdaq"
  - Distinct strategy:    "EXPERIMENT_NASDAQ_ON_XAU"
  - Does NOT mirror to meta_signals (MT5 bot won't trade these)
  - AI-Ops orchestrator's AUDITED_MODELS set does NOT include this key,
    so failure clustering & DeepSeek proposals don't trigger on it
  - Kill switch:  CROSS_MODEL_EXPERIMENT_ENABLED env (default "0" — KAPALI;
    2026-07-01'de kanıt sonrası varsayılan kapatıldı. is_enabled() her tick'te
    yeniden okunur, yani env'i 0 yapmak süreç yeniden başlatmadan da durdurur.)

Cache TTL:  60 seconds for the live preview endpoint (no Redis needed,
in-memory dict). Cron writes don't read this cache.

Public API:
  predict_xau_via_nasdaq_model()  → PredictionResult-like dict
  run_experiment_tick()           → fired by background_scheduler each 15m
  experiment_stats(days)           → roll-up for the dashboard panel
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

EXPERIMENT_MODEL_TYPE = "ml_cross_xau_nasdaq"
EXPERIMENT_STRATEGY = "EXPERIMENT_NASDAQ_ON_XAU"
EXPERIMENT_SYMBOL = "XAUUSD"
EXPERIMENT_TIMEFRAME = "15m"
EXPERIMENT_CRON_INTERVAL_SECONDS = 900  # 15 minutes
EXPERIMENT_CONFIDENCE_FLOOR = 55.0      # below this we skip logging (noise)
PREVIEW_CACHE_TTL_S = 60

_preview_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_last_tick_at: Optional[datetime] = None
_last_tick_status: str = "never_run"
_last_logged_prediction_id: Optional[str] = None


def is_enabled() -> bool:
    """Master kill switch. Set CROSS_MODEL_EXPERIMENT_ENABLED=1 to re-enable.

    2026-07-01 (rapor aksiyon #7): Default KAPALI. 60 günlük canlı sonuç:
    ml_cross_xau_nasdaq SELL 12W/162L (%6.9 WR), toplam %48.3 WR —
    NASDAQ modelinin XAU mumlarına transferi kanıtlanmış şekilde başarısız.
    """
    return os.getenv("CROSS_MODEL_EXPERIMENT_ENABLED", "0") == "1"


async def predict_xau_via_nasdaq_model() -> Dict[str, Any]:
    """Run the legacy NASDAQ ML pipeline against XAUUSD candles.

    We bypass the XAUUSD v2 short-circuit in get_ml_prediction by
    importing the underlying helpers directly. This way:
      - XAUUSD candle data is fetched (correct chart)
      - NASDAQ 150-feature engineering runs on it
      - NASDAQ joblib model produces probability_up / probability_down
      - Direction/confidence/TP/SL are decided by the NASDAQ pipeline's
        logic, not the bespoke XAU v2 ensemble

    Returns a dict roughly compatible with PredictionResult.to_dict().
    On any failure returns {"direction": "HOLD", "error": ..., ...}.
    """
    try:
        # Lazy imports — keeps experiment fully separable from prod pipeline.
        from services import ml_prediction_service as mlp
        from services.data_fetcher import fetch_30m_candles, fetch_latest_price

        # ── Load the NASDAQ model (cached internally by ml_prediction_service) ──
        nasdaq_model = mlp._load_model("NDX.INDX")
        if nasdaq_model is None:
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": "nasdaq_model_unavailable",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        # ── Fetch XAUUSD candles (the actual chart we want analysed) ──
        candles_30m = await fetch_30m_candles(EXPERIMENT_SYMBOL, limit=300)
        if not candles_30m or len(candles_30m) < 60:
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": "insufficient_xau_candles",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        current_price_val = await fetch_latest_price(EXPERIMENT_SYMBOL) or 0.0
        try:
            current_price = float(current_price_val)
        except (TypeError, ValueError):
            current_price = 0.0
        if current_price <= 0:
            try:
                current_price = float(candles_30m[-1].get("close") or 0)
            except (TypeError, ValueError):
                current_price = 0.0
        if current_price <= 0:
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": "no_current_price",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        # ── Build feature vector using the NASDAQ pipeline's helpers ──
        ta_30m: Dict[str, Any] = {}
        try:
            import numpy as np
            closes_30m = np.array([float(c.get("close") or 0) for c in candles_30m], dtype=float)
            highs_30m = np.array([float(c.get("high") or 0) for c in candles_30m], dtype=float)
            lows_30m = np.array([float(c.get("low") or 0) for c in candles_30m], dtype=float)
            volumes_30m = np.array([float(c.get("volume") or 0) for c in candles_30m], dtype=float)

            ta_30m = mlp._compute_technical_indicators(closes_30m, highs_30m, lows_30m, volumes_30m)
            ta_30m["close"] = current_price
        except Exception as feat_err:
            logger.exception("[cross-model] feature compute failed: %s", feat_err)
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": f"feature_compute_failed:{str(feat_err)[:80]}",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        # ── Build the feature_df matching NASDAQ model's expected schema ──
        # _build_feature_vector signature: (symbol, ta, candles, ta_1h=None, ta_4h=None)
        # We pass ta_30m as fallback for H1/H4 — same TF degeneracy the prod
        # pipeline tolerates when MTF data is unavailable.
        try:
            feature_df = mlp._build_feature_vector(
                "NDX.INDX",        # MATCH the NASDAQ model's training schema
                ta_30m,
                candles_30m,
                ta_1h=ta_30m,
                ta_4h=ta_30m,
            )
        except Exception as build_err:
            logger.exception("[cross-model] feature_df build failed: %s", build_err)
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": f"feature_df_failed:{str(build_err)[:80]}",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        if feature_df is None or len(feature_df) == 0:
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": "empty_feature_df",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        # ── Probability prediction ──
        try:
            proba = nasdaq_model.predict_proba(feature_df)[0]
            # LightGBM binary: [prob_class_0, prob_class_1] — class 1 = up
            prob_up = float(proba[1]) if len(proba) >= 2 else 0.5
            prob_down = float(proba[0]) if len(proba) >= 2 else 0.5
        except Exception as predict_err:
            logger.exception("[cross-model] predict_proba failed: %s", predict_err)
            return {"direction": "HOLD", "confidence": 0.0,
                    "error": f"predict_failed:{str(predict_err)[:80]}",
                    "symbol": EXPERIMENT_SYMBOL,
                    "timestamp": _utc_iso()}

        # ── Decide direction (mirror NASDAQ pipeline thresholds) ──
        if prob_up >= 0.55:
            direction = "BUY"
            confidence = round(prob_up * 100, 1)
        elif prob_down >= 0.55:
            direction = "SELL"
            confidence = round(prob_down * 100, 1)
        else:
            direction = "HOLD"
            confidence = round(max(prob_up, prob_down) * 100, 1)

        # ── TP/SL using XAUUSD's own target_config (so MT5-style outcomes match) ──
        try:
            from services.target_config import (
                calculate_target_prices, calculate_stoploss_price,
            )
            tp_map = calculate_target_prices(current_price, direction, EXPERIMENT_SYMBOL, EXPERIMENT_TIMEFRAME)
            sl_price = calculate_stoploss_price(current_price, direction, EXPERIMENT_SYMBOL, EXPERIMENT_TIMEFRAME)
            target_price = float(tp_map.get("TP1") or current_price)
        except Exception:
            target_price = current_price
            sl_price = current_price

        return {
            "symbol": EXPERIMENT_SYMBOL,
            "direction": direction,
            "confidence": confidence,
            "probability_up": round(prob_up, 4),
            "probability_down": round(prob_down, 4),
            "entry_price": round(current_price, 4),
            "target_price": round(target_price, 4),
            "stop_price": round(sl_price, 4),
            "model_used": "model_lgbm_nasdaq.joblib (cross-applied to XAUUSD)",
            "experiment": EXPERIMENT_MODEL_TYPE,
            "timestamp": _utc_iso(),
            "error": None,
        }
    except Exception as e:
        logger.exception("[cross-model] predict_xau_via_nasdaq_model failed: %s", e)
        return {"direction": "HOLD", "confidence": 0.0,
                "error": str(e)[:120], "symbol": EXPERIMENT_SYMBOL,
                "timestamp": _utc_iso()}


async def get_cached_preview() -> Dict[str, Any]:
    """Live preview for the experiment dashboard panel (60s in-memory cache)."""
    now_ts = time.time()
    cached = _preview_cache.get("preview")
    if cached and (now_ts - cached[0]) < PREVIEW_CACHE_TTL_S:
        out = dict(cached[1])
        out["cached"] = True
        return out
    payload = await predict_xau_via_nasdaq_model()
    payload["cached"] = False
    _preview_cache["preview"] = (now_ts, payload)
    return payload


async def run_experiment_tick() -> Dict[str, Any]:
    """Cron-driven tick: produce a prediction and log it if actionable.

    Returns a summary dict so the scheduler can record what happened.
    Errors are swallowed (returned as status='error', never raises).
    """
    global _last_tick_at, _last_tick_status, _last_logged_prediction_id
    _last_tick_at = datetime.now(timezone.utc)

    if not is_enabled():
        _last_tick_status = "disabled"
        return {"status": "disabled"}

    pred = await predict_xau_via_nasdaq_model()
    direction = pred.get("direction")
    confidence = float(pred.get("confidence") or 0)

    if pred.get("error"):
        _last_tick_status = f"error:{pred.get('error')}"
        return {"status": "error", "reason": pred.get("error")}

    if direction not in ("BUY", "SELL"):
        _last_tick_status = "hold"
        return {"status": "hold", "confidence": confidence}

    if confidence < EXPERIMENT_CONFIDENCE_FLOOR:
        _last_tick_status = "low_confidence"
        return {"status": "low_confidence", "direction": direction, "confidence": confidence}

    # ── Log to prediction_logs via the standard logger so the lifecycle
    # tracks TP/SL outcomes identically to all other models. We pass the
    # experiment-specific model_type and strategy, and DO NOT mirror to
    # meta_signals — the bot stays out of these trades.
    try:
        from services.prediction_logger import log_prediction
        context = {
            "ml_prediction": {
                "direction": direction,
                "confidence": confidence,
                "probability_up": pred.get("probability_up"),
                "probability_down": pred.get("probability_down"),
                "entry_price": pred.get("entry_price"),
                "target_price": pred.get("target_price"),
                "stop_price": pred.get("stop_price"),
            },
            "ta": {},
            "distances": {},
            "volume": {},
            "trend_channel": {},
            "macro": {},
            "news": {},
            "levels": {},
            "market_context": {"source": EXPERIMENT_STRATEGY},
            "source": EXPERIMENT_STRATEGY,
        }
        analysis = {
            "final_decision": direction,
            "confidence": confidence,
            "model_used": pred.get("model_used"),
            "market_regime": {"trend": "unknown"},
            "news_impact": {"tone": "neutral"},
        }
        pid = await log_prediction(
            symbol=EXPERIMENT_SYMBOL,
            context=context,
            analysis=analysis,
            timeframe=EXPERIMENT_TIMEFRAME,
            strategy=EXPERIMENT_STRATEGY,
            model_type=EXPERIMENT_MODEL_TYPE,
            allow_parallel_active=True,  # this experiment is independent of other ml signals
        )
        if pid:
            _last_logged_prediction_id = pid
            _last_tick_status = f"logged:{direction}@{confidence:.1f}"
            logger.info(
                "[cross-model] logged experiment signal %s %s conf=%.1f → %s",
                EXPERIMENT_SYMBOL, direction, confidence, pid[:8],
            )
            return {"status": "logged", "prediction_id": pid,
                    "direction": direction, "confidence": confidence}
        _last_tick_status = "log_skipped"
        return {"status": "log_skipped", "direction": direction, "confidence": confidence}
    except Exception as log_err:
        logger.exception("[cross-model] log_prediction failed: %s", log_err)
        _last_tick_status = f"log_error:{str(log_err)[:60]}"
        return {"status": "log_error", "error": str(log_err)[:120]}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def experiment_stats(days: int = 14) -> Dict[str, Any]:
    """Roll-up stats over the experiment cohort for the dashboard panel."""
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return {"enabled": is_enabled(), "available": False,
                    "reason": "db_unavailable"}
        client = get_supabase_client()
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        rows_q = client.table("prediction_logs").select(
            "id, ml_direction, ml_confidence, status, resolution_reason, "
            "highest_profit_pips, lowest_drawdown_pips, exit_price, "
            "created_at, exit_time"
        ).eq("symbol", EXPERIMENT_SYMBOL).eq("model_type", EXPERIMENT_MODEL_TYPE).gte(
            "created_at", since
        ).limit(2000)
        res = rows_q.execute() if hasattr(rows_q, "execute") else rows_q
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []

        total = len(data)
        active = sum(1 for r in data if r.get("status") == "active")
        resolved = [r for r in data if r.get("status") in ("completed", "stopped")]
        real_wins = [r for r in resolved
                      if (r.get("resolution_reason") or "") in (
                          "tp4_hit", "tp1_3_hit_then_sl", "all_targets_hit"
                      )]
        sl_hits = [r for r in resolved if (r.get("resolution_reason") or "") == "sl_hit"]
        window_wins = [r for r in resolved
                        if (r.get("resolution_reason") or "") == "window_resolve_positive"]
        net_pips = 0.0
        for r in resolved:
            mfe = abs(float(r.get("highest_profit_pips") or 0))
            mae = abs(float(r.get("lowest_drawdown_pips") or 0))
            if r.get("status") == "completed":
                net_pips += mfe
            elif r.get("status") == "stopped":
                net_pips -= mae

        recent_signals = []
        for r in sorted(data, key=lambda x: x.get("created_at") or "", reverse=True)[:10]:
            recent_signals.append({
                "id": r.get("id"),
                "direction": r.get("ml_direction"),
                "confidence": r.get("ml_confidence"),
                "status": r.get("status"),
                "resolution": r.get("resolution_reason"),
                "created_at": r.get("created_at"),
                "exit_time": r.get("exit_time"),
            })

        return {
            "enabled": is_enabled(),
            "available": True,
            "window_days": days,
            "model_type": EXPERIMENT_MODEL_TYPE,
            "total_signals": total,
            "active": active,
            "resolved": len(resolved),
            "real_wins": len(real_wins),
            "sl_hits": len(sl_hits),
            "window_wins": len(window_wins),
            "real_win_rate_pct": (
                round(len(real_wins) / (len(real_wins) + len(sl_hits)) * 100, 1)
                if (len(real_wins) + len(sl_hits)) > 0 else None
            ),
            "net_pips": round(net_pips, 1),
            "last_tick_at": _last_tick_at.isoformat() if _last_tick_at else None,
            "last_tick_status": _last_tick_status,
            "recent_signals": recent_signals,
        }
    except Exception as e:
        logger.exception("[cross-model] experiment_stats failed: %s", e)
        return {"enabled": is_enabled(), "available": False,
                "error": str(e)[:120]}


async def daily_loop() -> None:
    """Lifespan task — kicks every EXPERIMENT_CRON_INTERVAL_SECONDS once enabled.
    Sleeps 30s initially so app startup completes first."""
    import asyncio
    await asyncio.sleep(30)
    while True:
        try:
            if is_enabled():
                await run_experiment_tick()
            else:
                logger.debug("[cross-model] disabled by env, skipping tick")
        except Exception as e:
            logger.exception("[cross-model] tick failed: %s", e)
        await asyncio.sleep(EXPERIMENT_CRON_INTERVAL_SECONDS)
