from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

import os as _os
from datetime import datetime as _dt, timezone as _tz

from config import settings
from services.redis_client import get_redis_url

logger = logging.getLogger(__name__)

# ── MT5 broker → UTC timezone normalization ───────────────────────────────────
# MT5 bridges publish bar/tick epochs in *broker server time* (commonly EET,
# UTC+2/+3) labelled as if UTC, so candles land 2-3h in the future and every
# time-based check (lifecycle freshness, wick guard, market-open) misfires.
# We normalize every incoming epoch to true UTC at ingest. The offset is
# auto-detected from ticks / small-interval (<=15m) bars: their open time is
# within minutes of "now", so rounding (broker_epoch - now_utc) to the nearest
# hour yields the exact integer offset and follows DST automatically. Pin it
# with MT5_BROKER_UTC_OFFSET_HOURS (e.g. "3" or "0") to skip auto-detection.
_TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400, "d1": 86400}
_DETECT_MAX_TRUE_DRIFT = 1800   # only detect from streams whose latest-bar age < 30 min
_mt5_offset_seconds = 0         # detected broker→UTC offset for BAR streams
_mt5_tick_offset_seconds = 0    # detected offset for TICKS (kept separate — see below)
_mt5_offset_fixed: Optional[int] = None  # env override in seconds, or None

# 2026-07-08: tick and bar offsets are tracked SEPARATELY. The bridge stamps
# ticks in UTC but bars in broker time (UTC+2/+3); a single shared offset
# flip-flopped between 0 and +3h depending on which observation came last,
# leaving a mixture of shifted and unshifted bars in the stores.


def _load_mt5_offset_override() -> None:
    global _mt5_offset_fixed
    raw = (_os.getenv("MT5_BROKER_UTC_OFFSET_HOURS", "") or "").strip()
    if raw:
        try:
            _mt5_offset_fixed = int(round(float(raw) * 3600))
            logger.info("[MT5Redis] broker→UTC offset pinned via env: %+.0fh", _mt5_offset_fixed / 3600.0)
        except Exception:
            _mt5_offset_fixed = None


_load_mt5_offset_override()


def _tf_seconds(timeframe) -> int:
    return _TF_SECONDS.get(str(timeframe or "").lower().strip(), 0)


def _effective_offset() -> int:
    return _mt5_offset_fixed if _mt5_offset_fixed is not None else _mt5_offset_seconds


def _candle_epoch_seconds(c: Dict[str, Any]) -> Optional[float]:
    if not isinstance(c, dict):
        return None
    v = c.get("time")
    if v is None and c.get("timestamp") is not None:
        try:
            ts = float(c["timestamp"])
            v = ts / 1000.0 if ts > 1e12 else ts
        except Exception:
            v = None
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _observe_for_offset(epoch_s: Optional[float], max_true_drift: float, kind: str = "bar") -> None:
    """Update the detected broker offset from an epoch whose true age is small.

    kind="bar" updates the bar-stream offset; kind="tick" updates the tick
    offset. They are independent because the bridge stamps them differently.
    """
    global _mt5_offset_seconds, _mt5_tick_offset_seconds
    if _mt5_offset_fixed is not None or epoch_s is None or max_true_drift > _DETECT_MAX_TRUE_DRIFT:
        return
    now = _dt.now(_tz.utc).timestamp()
    off = int(round((epoch_s - now) / 3600.0)) * 3600
    if abs(off) > 14 * 3600:
        return
    current = _mt5_tick_offset_seconds if kind == "tick" else _mt5_offset_seconds
    if off != current:
        logger.warning(
            "[MT5Redis] broker→UTC %s offset detected: %+.0fh (was %+.0fh) — normalizing timestamps",
            kind, off / 3600.0, current / 3600.0,
        )
        if kind == "tick":
            _mt5_tick_offset_seconds = off
        else:
            _mt5_offset_seconds = off


def _normalize_candle_times(c: Dict[str, Any]) -> Dict[str, Any]:
    """Subtract the broker offset from a candle's time/timestamp (in place)."""
    off = _effective_offset()
    if not off or not isinstance(c, dict):
        return c
    if c.get("time") is not None:
        try:
            c["time"] = int(float(c["time"]) - off)
        except Exception:
            pass
    if c.get("timestamp") is not None:
        try:
            ts = float(c["timestamp"])
            c["timestamp"] = int(ts - off * (1000.0 if ts > 1e12 else 1.0))
        except Exception:
            pass
    return c


def _normalize_tick_timestamp(ts):
    off = _mt5_offset_fixed if _mt5_offset_fixed is not None else _mt5_tick_offset_seconds
    if not off or ts is None:
        return ts
    try:
        v = float(ts)
        return int(v - off * (1000.0 if v > 1e12 else 1.0))
    except Exception:
        return ts

_listener_running = False
_listener_client: Optional[redis.Redis] = None
_listener_pubsub = None

# ── Heartbeat / reconnect settings ────────────────────────────────────────────
_HEARTBEAT_INTERVAL = 30        # seconds between keepalive pings
_NO_TICK_RECONNECT_THRESHOLD = 120  # seconds — force reconnect if no ticks received

# ── Diagnostic counters ──────────────────────────────────────────────────────
_diag = {
    "ticks_received": 0,
    "ticks_ingested": 0,
    "ticks_rejected": 0,
    "bars_received": 0,
    "last_tick_time": None,
    "last_bar_time": None,
    "last_tick_symbol": None,
    "last_bar_symbol": None,
    "last_tick_payload": None,
    "last_tick_price": None,
    "errors": [],
    "reconnect_count": 0,
    "last_heartbeat": None,
    "listener_started_at": None,
    "last_reconnect": None,
}


def _source_mode_enabled() -> bool:
    source = (settings.market_data_source or "mt5_redis").strip().lower()
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

    # Ticks are ~"now", so they are the most accurate source for offset detection.
    raw_ts = payload.get("timestamp") or payload.get("time")
    if raw_ts is not None:
        try:
            _v = float(raw_ts)
            _observe_for_offset(_v / 1000.0 if _v > 1e12 else _v, 30, kind="tick")
        except Exception:
            pass

    ingested = await ingest_live_price(
        symbol=symbol,
        price=price,
        timestamp=_normalize_tick_timestamp(raw_ts),
        bid=payload.get("bid"),
        ask=payload.get("ask"),
        source="mt5_redis",
    )
    _diag["ticks_received"] += 1
    _diag["last_tick_time"] = asyncio.get_event_loop().time()
    _diag["last_tick_symbol"] = symbol
    _diag["last_tick_price"] = price
    _diag["last_tick_payload"] = {k: v for k, v in payload.items() if k != "candles"}  # sample
    if ingested:
        _diag["ticks_ingested"] += 1
    else:
        _diag["ticks_rejected"] += 1


async def _handle_bar(payload: Dict[str, Any]) -> None:
    from services.data_hub import ingest_candle, ingest_candles

    symbol = payload.get("symbol") or payload.get("instrument") or payload.get("ticker")
    timeframe = payload.get("timeframe") or payload.get("tf") or payload.get("interval")
    if not symbol or not timeframe:
        logger.debug("[MT5Redis] Bar payload missing symbol/timeframe: %s", payload)
        return

    if payload.get("closed") is False or payload.get("is_closed") is False:
        return

    interval = _tf_seconds(timeframe)
    candles = payload.get("candles")
    if isinstance(candles, list):
        # Detect offset from the newest candle of small-interval streams, then
        # normalize every candle in the batch to true UTC.
        if interval and interval <= 900:
            epochs = [e for e in (_candle_epoch_seconds(c) for c in candles) if e is not None]
            if epochs:
                _observe_for_offset(max(epochs), interval)
        for c in candles:
            _normalize_candle_times(c)
        await ingest_candles(symbol, timeframe, candles, source="mt5_redis")
        return

    candle = _extract_candle_payload(payload)
    if interval and interval <= 900:
        _observe_for_offset(_candle_epoch_seconds(candle), interval)
    _normalize_candle_times(candle)
    await ingest_candle(symbol, timeframe, candle, source="mt5_redis")
    _diag["bars_received"] += 1
    _diag["last_bar_time"] = asyncio.get_event_loop().time()
    _diag["last_bar_symbol"] = f"{symbol}/{timeframe}"


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
    import time as _time
    _diag["listener_started_at"] = _time.time()

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
                # Start reading from current end of streams.
                # mt5:bar:1m is optional — it may not exist in all MT5 bridge configs.
                # We probe for it; if Redis rejects it we silently drop it and continue.
                core_streams = {
                    "mt5:bar:5m": "$",
                    "mt5:bar:1h": "$",
                    "mt5:bar:1d": "$",
                }
                optional_streams = {"mt5:bar:1m": "$"}
                streams: Dict[str, str] = {**core_streams, **optional_streams}
                optional_probed = False  # have we verified optional streams exist?

                while _listener_running:
                    try:
                        result = await _listener_client.xread(streams, count=50, block=1000)
                        optional_probed = True  # xread succeeded → all current streams are valid
                        if result:
                            for stream_name, messages in result:
                                for msg_id, msg_data in messages:
                                    try:
                                        payload_str = msg_data.get("payload")
                                        if payload_str:
                                            payload = _decode_payload(payload_str)
                                            if payload:
                                                # Derive timeframe from stream name if not present
                                                tf = stream_name.split(":")[-1]
                                                if not payload.get("timeframe"):
                                                    payload["timeframe"] = tf
                                                await _handle_bar(payload)
                                    except Exception as msg_err:
                                        logger.warning(
                                            "[MT5Redis] Error handling message from %s: %s",
                                            stream_name, msg_err,
                                        )
                                    finally:
                                        # Always advance offset so we don't reprocess this message
                                        streams[stream_name] = msg_id
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        err_str = str(e)
                        logger.error("[MT5Redis] Stream read error: %s", err_str)
                        # If optional streams are causing the failure, drop them and retry
                        if not optional_probed:
                            dropped = [k for k in optional_streams if k in streams]
                            if dropped:
                                for k in dropped:
                                    del streams[k]
                                logger.warning(
                                    "[MT5Redis] Dropped optional streams %s (may not exist yet)", dropped
                                )
                                continue  # retry immediately without sleep
                        await asyncio.sleep(2)

            stream_task = asyncio.create_task(_stream_loop())

            import time as _time
            _last_heartbeat = _time.time()
            _last_tick_seen = _time.time()

            while _listener_running:
                if stream_task.done():
                    logger.warning("[MT5Redis] Stream task exited unexpectedly, reconnecting...")
                    break

                # ── Periodic keepalive PING ──────────────────────────────────
                now = _time.time()
                if now - _last_heartbeat > _HEARTBEAT_INTERVAL:
                    try:
                        await _listener_client.ping()
                        _last_heartbeat = now
                        _diag["last_heartbeat"] = now
                    except Exception as ping_err:
                        logger.warning("[MT5Redis] Heartbeat PING failed: %s — forcing reconnect", ping_err)
                        break  # → outer while will reconnect

                # ── No-tick watchdog ─────────────────────────────────────────
                if now - _last_tick_seen > _NO_TICK_RECONNECT_THRESHOLD:
                    logger.warning(
                        "[MT5Redis] No ticks for %ds — forcing reconnect (threshold=%ds)",
                        int(now - _last_tick_seen), _NO_TICK_RECONNECT_THRESHOLD,
                    )
                    _diag["reconnect_count"] = _diag.get("reconnect_count", 0) + 1
                    _diag["last_reconnect"] = now
                    break  # → outer while will reconnect

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
                    _last_tick_seen = _time.time()  # reset watchdog
                    
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


async def get_mt5_redis_diagnostics() -> Dict[str, Any]:
    """Return diagnostic info about the MT5 Redis listener."""
    import time as _time

    redis_url = get_redis_url()
    result: Dict[str, Any] = {
        "source_mode_enabled": _source_mode_enabled(),
        "market_data_source": (settings.market_data_source or "mt5_redis").strip().lower(),
        "listener_running": _listener_running,
        "redis_url_configured": bool(redis_url),
        "redis_url_prefix": (redis_url or "")[:30] + "..." if redis_url else None,
        "tick_channel": settings.mt5_redis_tick_channel,
        "bar_streams": ["mt5:bar:5m", "mt5:bar:1h", "mt5:bar:1d"],
        "counters": dict(_diag),
    }

    # Probe Redis keys and streams
    if redis_url:
        try:
            probe = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=3)
            await probe.ping()
            result["redis_ping"] = "ok"

            # Check if streams exist
            for stream in ["mt5:bar:5m", "mt5:bar:1h", "mt5:bar:1d", "mt5:bar:1m"]:
                try:
                    info = await probe.xinfo_stream(stream)
                    result[f"stream_{stream}"] = {
                        "length": info.get("length", 0),
                        "first_entry": str(info.get("first-entry")) if info.get("first-entry") else None,
                        "last_entry": str(info.get("last-entry")) if info.get("last-entry") else None,
                    }
                except Exception:
                    result[f"stream_{stream}"] = "not_found"

            # Check pubsub channels
            channels = await probe.pubsub_channels()
            result["active_pubsub_channels"] = [c if isinstance(c, str) else c.decode() for c in channels]

            # Check pubsub subscribers for tick channel
            numsub = await probe.pubsub_numsub(settings.mt5_redis_tick_channel)
            result["tick_channel_subscribers"] = numsub.get(settings.mt5_redis_tick_channel, 0) if isinstance(numsub, dict) else str(numsub)

            await probe.close()
        except Exception as e:
            result["redis_probe_error"] = str(e)

    return result


async def stop_mt5_redis_listener() -> None:
    global _listener_running

    _listener_running = False
    await _close_connections()
