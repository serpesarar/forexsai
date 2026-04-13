from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

from config import settings
from services.redis_client import get_redis_url

logger = logging.getLogger(__name__)

_listener_running = False
_listener_client: Optional[redis.Redis] = None
_listener_pubsub = None


def _source_mode_enabled() -> bool:
    source = (settings.market_data_source or "eodhd").strip().lower()
    return source in {"mt5_redis", "hybrid"}


def _decode_payload(data: Any) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="ignore")
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            logger.debug("[MT5Redis] Invalid JSON payload: %s", data[:200])
            return None
    return None


def _extract_price(payload: Dict[str, Any]) -> Optional[float]:
    for key in ("price", "last", "close", "mid"):
        value = payload.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass

    bid = payload.get("bid")
    ask = payload.get("ask")
    if bid is not None and ask is not None:
        try:
            return (float(bid) + float(ask)) / 2.0
        except (TypeError, ValueError):
            return None
    return None


def _extract_candle_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    nested = payload.get("candle") or payload.get("bar") or payload.get("data")
    if isinstance(nested, dict):
        candle = dict(nested)
    else:
        candle = dict(payload)

    if payload.get("timestamp") is not None and candle.get("timestamp") is None:
        candle["timestamp"] = payload.get("timestamp")
    if payload.get("time") is not None and candle.get("time") is None:
        candle["time"] = payload.get("time")
    if payload.get("date") is not None and candle.get("date") is None:
        candle["date"] = payload.get("date")
    return candle


async def _handle_tick(payload: Dict[str, Any]) -> None:
    from services.data_hub import ingest_live_price

    symbol = payload.get("symbol") or payload.get("instrument") or payload.get("ticker")
    if not symbol:
        logger.debug("[MT5Redis] Tick payload missing symbol: %s", payload)
        return

    price = _extract_price(payload)
    if price is None:
        logger.debug("[MT5Redis] Tick payload missing price: %s", payload)
        return

    await ingest_live_price(
        symbol=symbol,
        price=price,
        timestamp=payload.get("timestamp") or payload.get("time"),
        bid=payload.get("bid"),
        ask=payload.get("ask"),
        source="mt5_redis",
    )


async def _handle_bar(payload: Dict[str, Any]) -> None:
    from services.data_hub import ingest_candle, ingest_candles

    symbol = payload.get("symbol") or payload.get("instrument") or payload.get("ticker")
    timeframe = payload.get("timeframe") or payload.get("tf") or payload.get("interval")
    if not symbol or not timeframe:
        logger.debug("[MT5Redis] Bar payload missing symbol/timeframe: %s", payload)
        return

    if payload.get("closed") is False or payload.get("is_closed") is False:
        return

    candles = payload.get("candles")
    if isinstance(candles, list):
        await ingest_candles(symbol, timeframe, candles, source="mt5_redis")
        return

    candle = _extract_candle_payload(payload)
    await ingest_candle(symbol, timeframe, candle, source="mt5_redis")


async def _close_connections() -> None:
    global _listener_client, _listener_pubsub

    if _listener_pubsub is not None:
        try:
            await _listener_pubsub.close()
        except Exception:
            pass
        _listener_pubsub = None

    if _listener_client is not None:
        try:
            await _listener_client.close()
        except Exception:
            pass
        _listener_client = None


async def start_mt5_redis_listener() -> None:
    global _listener_running, _listener_client, _listener_pubsub

    if not _source_mode_enabled():
        logger.info("[MT5Redis] Listener disabled for market_data_source=%s", settings.market_data_source)
        return
    if _listener_running:
        logger.warning("[MT5Redis] Listener already running")
        return

    redis_url = get_redis_url()
    if not redis_url:
        logger.warning("[MT5Redis] No Redis URL configured; listener not started")
        return

    tick_channel = settings.mt5_redis_tick_channel
    _listener_running = True

    while _listener_running:
        stream_task = None
        try:
            _listener_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await _listener_client.ping()
            _listener_pubsub = _listener_client.pubsub()
            await _listener_pubsub.subscribe(tick_channel)
            logger.info("[MT5Redis] Listening pubsub tick=%s, streams mt5:bar:*", tick_channel)

            async def _stream_loop():
                # Start reading from current end of streams
                streams = {
                    "mt5:bar:5m": "$",
                    "mt5:bar:1h": "$",
                    "mt5:bar:1d": "$"
                }
                while _listener_running:
                    try:
                        result = await _listener_client.xread(streams, count=50, block=1000)
                        if result:
                            for stream_name, messages in result:
                                for msg_id, msg_data in messages:
                                    payload_str = msg_data.get("payload")
                                    if payload_str:
                                        payload = _decode_payload(payload_str)
                                        if payload:
                                            # Derive timeframe from stream name if not present
                                            tf = stream_name.split(":")[-1]
                                            if not payload.get("timeframe"):
                                                payload["timeframe"] = tf
                                            await _handle_bar(payload)
                                    # Update offset
                                    streams[stream_name] = msg_id
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error("[MT5Redis] Stream read error: %s", e)
                        await asyncio.sleep(2)

            stream_task = asyncio.create_task(_stream_loop())

            while _listener_running:
                if stream_task.done():
                    logger.warning("[MT5Redis] Stream task exited unexpectedly, reconnecting...")
                    break
                
                message = await _listener_pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    await asyncio.sleep(0.05)
                    continue

                payload = _decode_payload(message.get("data"))
                if not payload:
                    continue

                channel = message.get("channel")
                if channel == tick_channel:
                    await _handle_tick(payload)
                    
        except asyncio.CancelledError:
            if stream_task:
                stream_task.cancel()
            raise
        except Exception as exc:
            logger.error("[MT5Redis] Listener error: %s", exc)
            await asyncio.sleep(2)
        finally:
            if stream_task:
                stream_task.cancel()
            await _close_connections()


async def stop_mt5_redis_listener() -> None:
    global _listener_running

    _listener_running = False
    await _close_connections()
