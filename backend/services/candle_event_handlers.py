"""
Candle Close Event Handlers
============================
Event-driven model refresh: instead of blind polling every 10s,
models are recalculated only when their relevant candle timeframe closes.

Registration happens at import time so main.py just needs to import this module.

Event mapping:
  5m close  → Pulse 1, Pulse 3 refresh + WS broadcast
  15m close → Pulse 2 refresh + WS broadcast  
  30m close → ML Prediction refresh + WS broadcast
  1h close  → EMEL refresh + WS broadcast
  4h close  → Regime cache invalidation
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Throttle: don't re-run if last run was < N seconds ago
_last_run: Dict[str, float] = {}


def _should_run(key: str, min_interval: float = 10.0) -> bool:
    """Simple throttle to prevent duplicate fires within min_interval seconds."""
    now = time.time()
    if now - _last_run.get(key, 0) < min_interval:
        return False
    _last_run[key] = now
    return True


async def _refresh_and_broadcast_panel(symbol: str, panel_name: str, refresh_func, broadcast_key: str):
    """Run a panel refresh and broadcast the result via WS."""
    try:
        result = await refresh_func(symbol)
        if result:
            from services.redis_client import cache_set
            # Write to broadcast-format key
            payload = result.dict() if hasattr(result, "dict") else (result.model_dump() if hasattr(result, "model_dump") else result)
            cache_set(f"panel:{broadcast_key}:{symbol.upper()}", payload, ttl=120)

            # Trigger WS broadcast for this symbol
            from services.ws_manager import manager
            from services.background_scheduler import _get_cached_panel_data
            panel_data = _get_cached_panel_data(symbol)
            if panel_data:
                await manager.broadcast(symbol, {
                    "type": "panel_update",
                    "symbol": symbol,
                    "panels": panel_data,
                })
            logger.info(f"[CandleEvent] {panel_name} refreshed for {symbol}")
    except Exception as e:
        logger.error(f"[CandleEvent] {panel_name} refresh failed for {symbol}: {e}")


async def on_5m_candle_close(symbol: str, timeframe: str):
    """5m candle closed → refresh Pulse 1 and Pulse 3."""
    if not _should_run(f"pulse1:{symbol}", 30):
        return
    
    from routers.emel_pulse import get_pulse_analysis, get_pulse_v3_analysis

    # Run Pulse 1 and Pulse 3 in parallel
    tasks = [
        _refresh_and_broadcast_panel(symbol, "Pulse1", lambda s: get_pulse_analysis(s, timeframe="5m", refresh=True), "pulse1"),
        _refresh_and_broadcast_panel(symbol, "Pulse3", lambda s: get_pulse_v3_analysis(s, refresh=True), "pulse_v3"),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


async def on_15m_candle_close(symbol: str, timeframe: str):
    """15m candle closed → refresh Pulse 2."""
    if not _should_run(f"pulse2:{symbol}", 60):
        return
    
    from routers.emel_pulse import get_pulse_ml_analysis
    await _refresh_and_broadcast_panel(symbol, "Pulse2", lambda s: get_pulse_ml_analysis(s, timeframe="15m", refresh=True), "pulse2")


async def on_30m_candle_close(symbol: str, timeframe: str):
    """30m candle closed → refresh ML Prediction."""
    if not _should_run(f"ml:{symbol}", 120):
        return
    
    try:
        from services.ml_prediction_service import get_ml_prediction
        result = await get_ml_prediction(symbol)
        if result:
            direction = result.get("direction", "N/A") if isinstance(result, dict) else getattr(result, "direction", "N/A")
            logger.info(f"[CandleEvent] ML Prediction refreshed for {symbol}: {direction}")
    except Exception as e:
        logger.error(f"[CandleEvent] ML Prediction refresh failed for {symbol}: {e}")


async def on_1h_candle_close(symbol: str, timeframe: str):
    """1h candle closed → refresh EMEL analysis."""
    if not _should_run(f"emel:{symbol}", 120):
        return
    
    from routers.emel_pulse import get_emel_analysis
    await _refresh_and_broadcast_panel(symbol, "EMEL", lambda s: get_emel_analysis(s, timeframe="1H"), "emel")


async def on_4h_candle_close(symbol: str, timeframe: str):
    """4h candle closed → invalidate regime cache so next access recalculates."""
    try:
        from services.market_regime_service import _regime_cache
        key = symbol.upper()
        if key in _regime_cache:
            del _regime_cache[key]
            logger.info(f"[CandleEvent] Regime cache invalidated for {symbol}")
    except Exception as e:
        logger.error(f"[CandleEvent] Regime cache invalidation failed for {symbol}: {e}")


def register_all_candle_event_handlers():
    """Register all candle close event handlers with DataHub."""
    from services.data_hub import register_candle_close_callback

    register_candle_close_callback("5m", on_5m_candle_close)
    register_candle_close_callback("15m", on_15m_candle_close)
    register_candle_close_callback("30m", on_30m_candle_close)
    register_candle_close_callback("1h", on_1h_candle_close)
    register_candle_close_callback("4h", on_4h_candle_close)
    
    logger.info("[CandleEvent] All candle close event handlers registered")
