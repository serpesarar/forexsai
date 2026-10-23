from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import suppress
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
_listener_task: Optional[asyncio.Task] = None

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
    "connected": False,
    "stream_reader_active": False,
    "last_error": None,
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
    _diag["last_tick_time"] = time.time()
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
    _diag["last_bar_time"] = time.time()
    _diag["last_bar_symbol"] = f"{symbol}/{timeframe}"


async def _close_connections() -> None:
    global _listener_client, _listener_pubsub
    # Detach globals before awaiting, so a later generation cannot be closed here.
    client, pubsub = _listener_client, _listener_pubsub
    _listener_client = _listener_pubsub = None
    if pubsub is not None:
        with suppress(Exception):
            await pubsub.aclose()
    if client is not None:
        with suppress(Exception):
            await client.aclose(close_connection_pool=True)


async def _read_bar_streams(client: redis.Redis) -> None:
    """One reader per connection generation; never reference the global client."""
    streams = {"mt5:bar:5m": "$", "mt5:bar:1h": "$", "mt5:bar:1d": "$", "mt5:bar:1m": "$"}
    while _listener_running:
        try:
            result = await client.xread(streams, count=50, block=1000)
        except redis.ResponseError as exc:
            # Missing streams are valid for XREAD. Only an actual wrong-type
            # optional key warrants dropping it; connection failures reconnect.
            if "WRONGTYPE" in str(exc).upper() and "mt5:bar:1m" in streams:
                del streams["mt5:bar:1m"]
                logger.warning("[MT5Redis] Ignoring wrong-type optional 1m stream")
                continue
            raise
        for stream_name, messages in result or []:
            for msg_id, msg_data in messages:
                try:
                    payload = _decode_payload(msg_data.get("payload"))
                    if payload:
                        payload.setdefault("timeframe", stream_name.split(":")[-1])
                        await _handle_bar(payload)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.warning("[MT5Redis] Bar ingestion failed (%s)", type(exc).__name__)
                finally:
                    streams[stream_name] = msg_id


async def start_mt5_redis_listener() -> None:
    global _listener_running, _listener_client, _listener_pubsub, _listener_task
    if not _source_mode_enabled() or _listener_running:
        return
    redis_url = get_redis_url()
    if not redis_url:
        logger.warning("[MT5Redis] No Redis URL configured")
        return
    _listener_running = True
    _listener_task = asyncio.current_task()
    _diag["listener_started_at"] = time.time()
    backoff = 2
    try:
        while _listener_running:
            stream_task = None
            try:
                # Pub/sub + blocking stream read + heartbeat; leave one spare.
                client = redis.from_url(
                    redis_url, decode_responses=True, max_connections=4,
                    socket_connect_timeout=5, socket_timeout=5,
                    client_name="forexsai-mt5-feed",
                )
                _listener_client = client
                await client.ping()
                pubsub = client.pubsub()
                _listener_pubsub = pubsub
                await pubsub.subscribe(settings.mt5_redis_tick_channel)
                _diag.update(connected=True, last_error=None, stream_reader_active=True,
                             last_heartbeat=time.time())
                stream_task = asyncio.create_task(_read_bar_streams(client), name="mt5-bar-reader")
                last_heartbeat = last_tick_seen = time.monotonic()
                while _listener_running:
                    if stream_task.done():
                        await stream_task  # Propagate failures to the reconnect boundary.
                        raise RuntimeError("stream_reader_stopped")
                    now = time.monotonic()
                    if now - last_heartbeat > _HEARTBEAT_INTERVAL:
                        await client.ping()
                        last_heartbeat = now
                        _diag["last_heartbeat"] = time.time()
                    if now - last_tick_seen > _NO_TICK_RECONNECT_THRESHOLD:
                        raise TimeoutError("tick_watchdog")
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if not message:
                        await asyncio.sleep(0.05)
                        continue
                    payload = _decode_payload(message.get("data"))
                    if payload and message.get("channel") == settings.mt5_redis_tick_channel:
                        await _handle_tick(payload)
                        last_tick_seen = time.monotonic()
                        backoff = 2
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # Error messages may contain connection strings; expose types only.
                _diag["last_error"] = type(exc).__name__
                logger.warning("[MT5Redis] Reconnecting after %s", type(exc).__name__)
            finally:
                _diag.update(connected=False, stream_reader_active=False)
                if stream_task is not None:
                    stream_task.cancel()
                    # Join BEFORE creating another client. Otherwise orphan readers
                    # can fill the replacement client's pool on every reconnect.
                    with suppress(asyncio.CancelledError, Exception):
                        await stream_task
                await _close_connections()
            if _listener_running:
                _diag["reconnect_count"] += 1
                _diag["last_reconnect"] = time.time()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
    finally:
        _listener_running = False
        _listener_task = None
        _diag.update(connected=False, stream_reader_active=False)


async def get_mt5_redis_diagnostics() -> Dict[str, Any]:
    """Bounded, credential-free diagnostics; timestamps are UTC epoch seconds."""
    redis_url = get_redis_url()
    now = time.time()
    tick_age = now - _diag["last_tick_time"] if _diag["last_tick_time"] is not None else None
    bar_age = now - _diag["last_bar_time"] if _diag["last_bar_time"] is not None else None
    result: Dict[str, Any] = {
        "source_mode_enabled": _source_mode_enabled(),
        "market_data_source": settings.market_data_source,
        "listener_running": _listener_running,
        "listener_connected": _diag["connected"],
        "stream_reader_active": _diag["stream_reader_active"],
        "feed_healthy": bool(_diag["connected"] and _diag["stream_reader_active"]
                             and tick_age is not None and tick_age < _NO_TICK_RECONNECT_THRESHOLD),
        "last_tick_age_seconds": round(tick_age, 1) if tick_age is not None else None,
        "last_bar_age_seconds": round(bar_age, 1) if bar_age is not None else None,
        "redis_url_configured": bool(redis_url),
        "tick_channel": settings.mt5_redis_tick_channel,
        "bar_streams": ["mt5:bar:5m", "mt5:bar:1h", "mt5:bar:1d"],
        "counters": {k: v for k, v in _diag.items() if k not in {"last_tick_payload", "errors"}},
    }
    probe = None
    if redis_url:
        try:
            probe = redis.from_url(redis_url, decode_responses=True, max_connections=1,
                                   socket_connect_timeout=3, socket_timeout=3,
                                   client_name="forexsai-mt5-diagnostics")
            await probe.ping()
            result["redis_ping"] = "ok"
            for stream in [*result["bar_streams"], "mt5:bar:1m"]:
                try:
                    info = await probe.xinfo_stream(stream)
                    result[f"stream_{stream}"] = {
                        "length": info.get("length", 0),
                        "last_generated_id": info.get("last-generated-id"),
                    }
                except redis.ResponseError:
                    result[f"stream_{stream}"] = "not_found"
            numsub = await probe.pubsub_numsub(settings.mt5_redis_tick_channel)
            result["tick_channel_subscribers"] = dict(numsub).get(settings.mt5_redis_tick_channel, 0)
        except Exception as exc:
            result["redis_probe_error"] = type(exc).__name__
        finally:
            if probe is not None:
                with suppress(Exception):
                    await probe.aclose(close_connection_pool=True)
    return result


async def stop_mt5_redis_listener() -> None:
    global _listener_running
    _listener_running = False
    task = _listener_task
    if task is not None and task is not asyncio.current_task():
        if not task.cancelling():
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task
