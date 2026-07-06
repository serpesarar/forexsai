"""
Signal Lifecycle Manager
─────────────────────────
Tracks active signals every minute, captures wicks (session high/low),
detects target hits and stop losses, performs failure autopsy, and manages
timeframe-aware signal expiration/cleanup.

Tables used:
  - prediction_logs  (read active, update status/targets_hit/exit)
  - signal_failures  (insert failure autopsy on stop)

Note: per-check audit snapshots are NO LONGER written to `signal_checks`
(that table is frozen as of 2026-06-10, commit 4a1bbd6). The periodic
per-active-signal snapshot is now produced by signal_trajectory_service into
`signal_trajectory_snapshots` (richer: adds deterioration scoring + features).
"""
from __future__ import annotations

import asyncio
import logging
import json
import time
import traceback
from datetime import datetime, timedelta, timezone
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.data_fetcher import fetch_intraday_candles, fetch_latest_price
from services.target_config import (
    calculate_target_prices,
    calculate_stoploss_price,
    pips_from_price_change,
)
from services.signal_analytics import (
    canonical_stop_loss_pips,
    classify_signal,
    filter_market_closed_invalid_signals,
    normalize_model_type,
    normalize_timeframe as normalize_analytics_timeframe,
    normalized_targets_hit,
    resolved_exit_price,
    resolved_targets,
)
from utils.json_helpers import parse_json_field, parse_json_fields
from utils.market_hours import is_symbol_market_open

logger = logging.getLogger(__name__)


# Thread-safe SimpleCache for dashboard statistics
class SimpleCache:
    def __init__(self, ttl_seconds: float = 60.0):
        self.ttl = ttl_seconds
        self.store = {}
        self.lock = None

    def _get_lock(self):
        if self.lock is None:
            try:
                self.lock = asyncio.Lock()
            except Exception:
                pass
        return self.lock

    async def get(self, key: Any) -> Optional[Any]:
        lock = self._get_lock()
        if lock:
            async with lock:
                return self._get_cached_value(key)
        return self._get_cached_value(key)

    def _get_cached_value(self, key: Any) -> Optional[Any]:
        if key in self.store:
            expiry, val = self.store[key]
            if time.time() < expiry:
                return val
            else:
                del self.store[key]
        return None

    async def set(self, key: Any, val: Any):
        lock = self._get_lock()
        if lock:
            async with lock:
                self.store[key] = (time.time() + self.ttl, val)
        else:
            self.store[key] = (time.time() + self.ttl, val)

    async def invalidate_all(self):
        lock = self._get_lock()
        if lock:
            async with lock:
                self.store.clear()
        else:
            self.store.clear()


_dashboard_stats_cache = SimpleCache(ttl_seconds=60.0)


def _as_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _parse_candle_time(c: dict) -> datetime:
    ts = c.get("timestamp")
    if ts:
        return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
    date_val = c.get("date") or c.get("candle_time")
    if not date_val:
        return _utc_now()
    if isinstance(date_val, datetime):
        return _as_utc(date_val)
    return _as_utc(datetime.fromisoformat(str(date_val).replace("Z", "+00:00")))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: Optional[datetime] = None) -> str:
    return _as_utc(dt or _utc_now()).isoformat().replace("+00:00", "Z")


# ─── Observability: lightweight metrics ──────────────────────────────────────

class LifecycleMetrics:
    """In-process counters for lifecycle observability. Thread-safe not needed (single asyncio loop)."""

    def __init__(self):
        self.total_checks = 0
        self.total_signals_processed = 0
        self.total_errors = 0
        self.total_completed = 0
        self.total_stopped = 0
        self.total_expired = 0
        self.last_check_duration_ms: float = 0
        self.last_check_time: Optional[str] = None
        self.consecutive_failures = 0

    def record_check(self, duration_ms: float, processed: int, errors: int,
                     completed: int, stopped: int, expired: int):
        self.total_checks += 1
        self.total_signals_processed += processed
        self.total_errors += errors
        self.total_completed += completed
        self.total_stopped += stopped
        self.total_expired += expired
        self.last_check_duration_ms = round(duration_ms, 1)
        self.last_check_time = _utc_iso()
        if errors == 0:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checks": self.total_checks,
            "total_signals_processed": self.total_signals_processed,
            "total_errors": self.total_errors,
            "total_completed": self.total_completed,
            "total_stopped": self.total_stopped,
            "total_expired": self.total_expired,
            "last_check_duration_ms": self.last_check_duration_ms,
            "last_check_time": self.last_check_time,
            "consecutive_failures": self.consecutive_failures,
        }


metrics = LifecycleMetrics()

# ─── Configuration ───────────────────────────────────────────────────────────
LIFECYCLE_CHECK_INTERVAL = 60         # 1 minute — compare signals every minute
SIGNAL_MAX_AGE_MINUTES = 15           # Default evaluation window for legacy/15m
MAX_ACTIVE_SIGNALS = 100              # Cap for performance
ARCHIVE_AFTER_DAYS = 30               # Move to cold storage after 30 days
CLEANUP_INTERVAL_SECONDS = 1800       # Cleanup every 30 minutes

KNOWN_TIMEFRAMES = {"1m", "5m", "15m", "20m", "30m", "1h", "4h", "1d"}
TIMEFRAME_EVALUATION_WINDOWS = {
    "1m": 2,
    "5m": 10,
    "15m": SIGNAL_MAX_AGE_MINUTES,
    "20m": 20,
    "30m": 60,
    "1h": 120,
    "4h": 480,
    "1d": 2880,
}

_last_lifecycle_check: Optional[datetime] = None
_last_cleanup_run: Optional[datetime] = None
_lifecycle_lock = asyncio.Lock()  # Prevents concurrent lifecycle checks in same process


# ─── Circuit breaker for DataHub price fetching ──────────────────────────────
_price_fetch_failures: Dict[str, int] = {}
PRICE_CIRCUIT_BREAKER_THRESHOLD = 5  # Skip after N consecutive failures
PRICE_CIRCUIT_BREAKER_RESET = 60     # Reset after N seconds

# Track last known price per symbol for staleness detection
_price_last_seen: Dict[str, float] = {}  # symbol -> price
_price_last_seen_time: Dict[str, datetime] = {}  # symbol -> timestamp
PRICE_STALENESS_THRESHOLD_MINUTES = 1  # 1 minute - if price unchanged for 1min, consider market closed
MARKET_DATA_FRESHNESS_THRESHOLD_MINUTES = 20

# Average spread in pips per instrument (spread/slippage-aware TP/SL simulation)
SYMBOL_SPREADS = {
    "NDX.INDX": 1.5,
    "XAUUSD": 2.5,
    "GDAXI.INDX": 2.0,
    "USOIL.FOREX": 3.0,
}


def _get_pip_size(sym: str) -> float:
    """Price units per pip for spread/slippage scaling."""
    sym_upper = (sym or "").upper()
    if "XAUUSD" in sym_upper:
        return 0.1
    if "USOIL" in sym_upper or "CL.COMM" in sym_upper:
        return 0.01
    return 1.0


def _is_price_stale(symbol: str, current_price: float) -> bool:
    """
    Check if price is stale (hasn't changed in a long time).
    This detects when market is closed or upstream vendor is returning old data.
    """
    global _price_last_seen, _price_last_seen_time
    
    now = _utc_now()
    last_price = _price_last_seen.get(symbol)
    last_time = _price_last_seen_time.get(symbol)
    
    # Update tracking
    _price_last_seen[symbol] = current_price
    _price_last_seen_time[symbol] = now
    
    # If no previous price, not stale yet
    if last_price is None or last_time is None:
        return False
    
    # If price changed, reset staleness
    if abs(current_price - last_price) > 0.001:  # Small tolerance for floating point
        return False
    
    # Price is same as before - check how long
    minutes_unchanged = (now - last_time).total_seconds() / 60
    return minutes_unchanged >= PRICE_STALENESS_THRESHOLD_MINUTES


def _normalize_timeframe(value: Optional[str]) -> str:
    normalized = (value or "").lower().strip()
    return normalized if normalized in KNOWN_TIMEFRAMES else "15m"


def _evaluation_window_minutes(timeframe: Optional[str]) -> int:
    return TIMEFRAME_EVALUATION_WINDOWS.get(_normalize_timeframe(timeframe), SIGNAL_MAX_AGE_MINUTES)


def _cleanup_grace_minutes(timeframe: Optional[str]) -> int:
    return max(_evaluation_window_minutes(timeframe) * 2, 120)


def _parse_created_at(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return _as_utc(value)
    if isinstance(value, str):
        try:
            return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except Exception:
            return None
    return None


def _coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return parsed


def _is_reasonable_price_level(
    entry_price: float,
    candidate_price: Optional[float],
    fallback_price: float,
    direction: str,
    *,
    is_stop: bool = False,
) -> bool:
    if candidate_price is None or candidate_price <= 0:
        return False

    if direction == "BUY":
        if is_stop and candidate_price >= entry_price:
            return False
        if not is_stop and candidate_price <= entry_price:
            return False
    elif direction == "SELL":
        if is_stop and candidate_price <= entry_price:
            return False
        if not is_stop and candidate_price >= entry_price:
            return False

    fallback_distance = abs(fallback_price - entry_price)
    candidate_distance = abs(candidate_price - entry_price)
    if fallback_distance <= 0:
        return False

    ratio = candidate_distance / fallback_distance
    return 0.85 <= ratio <= 1.15


def _resolve_target_prices(
    signal: dict,
    entry_price: float,
    direction: str,
    symbol: str,
    timeframe: str,
) -> Dict[str, float]:
    stored_targets = signal.get("targets") or {}
    if not isinstance(stored_targets, dict):
        stored_targets = {}

    fallback_targets = calculate_target_prices(entry_price, direction, symbol, timeframe)
    resolved_targets: Dict[str, float] = {}
    for tp_name, fallback_price in fallback_targets.items():
        stored_price = _coerce_float(stored_targets.get(tp_name))
        if _is_reasonable_price_level(entry_price, stored_price, fallback_price, direction):
            resolved_targets[tp_name] = round(stored_price or fallback_price, 4)
        else:
            resolved_targets[tp_name] = round(fallback_price, 4)
    return resolved_targets


def _target_rank(tp_name: str) -> Optional[int]:
    if not tp_name:
        return None
    name = str(tp_name).upper().strip()
    digits = "".join(ch for ch in name if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None


def _resolved_exit_price_from_targets(
    target_prices: Dict[str, float],
    targets_hit: Dict[str, Any],
) -> Optional[float]:
    ranked_hits = []
    for tp_name, tp_price in target_prices.items():
        if not targets_hit.get(tp_name):
            continue
        rank = _target_rank(tp_name)
        if rank is None:
            continue
        ranked_hits.append((rank, tp_price))

    if not ranked_hits:
        return None

    _, exit_price = max(ranked_hits, key=lambda item: item[0])
    return round(float(exit_price), 4)


async def _get_session_high_low(symbol: str, minutes: int = 5) -> Dict[str, Optional[float]]:
    """Get session high/low from the last N minutes of 5m candles (wick capture).
    Has a circuit breaker: after 5 consecutive failures per symbol, returns None
    to avoid cascading timeouts."""
    global _price_fetch_failures

    fail_count = _price_fetch_failures.get(symbol, 0)
    if fail_count >= PRICE_CIRCUIT_BREAKER_THRESHOLD:
        logger.warning(f"lifecycle.price_circuit_open | symbol={symbol} failures={fail_count}")
        # Reset after some cycles so it retries eventually
        _price_fetch_failures[symbol] = fail_count - 1
        return {"high": None, "low": None, "current": None}

    try:
        candles = await fetch_intraday_candles(symbol, interval="5m", limit=2)
        if candles and len(candles) > 0:
            last = candles[-1]
            _price_fetch_failures[symbol] = 0  # Reset on success
            return {
                "high": float(last.get("high", 0)),
                "low": float(last.get("low", 0)),
                "current": float(last.get("close", 0)),
            }
    except Exception as e:
        _price_fetch_failures[symbol] = fail_count + 1
        logger.warning(f"lifecycle.price_candle_error | symbol={symbol} failures={fail_count+1} error={e}")

    # Fallback to spot price from DataHub-backed fetcher
    try:
        price = await fetch_latest_price(symbol)
        if price:
            _price_fetch_failures[symbol] = 0  # Reset on success
            return {"high": float(price), "low": float(price), "current": float(price)}
    except Exception as e:
        _price_fetch_failures[symbol] = fail_count + 1
        logger.warning(f"lifecycle.price_spot_error | symbol={symbol} error={e}")

    return {"high": None, "low": None, "current": None}

def _extract_candle_timestamp_ms(candle: Dict[str, Any]) -> Optional[float]:
    for key in ("timestamp", "time"):
        value = candle.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    for key in ("date", "datetime"):
        value = candle.get(key)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
            except Exception:
                continue
    return None


async def _get_price_window_since_signal(
    symbol: str,
    created_dt: Optional[datetime],
    evaluation_window: int,
    fallback_current: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    current = fallback_current
    latest_candle_at: Optional[datetime] = None
    has_post_entry_candles = created_dt is None
    if current is None:
        try:
            price_val = await fetch_latest_price(symbol)
            if price_val:
                current = float(price_val)
        except Exception as e:
            logger.warning(f"lifecycle.price_error | symbol={symbol} error={e}")

    try:
        age_minutes = evaluation_window
        if created_dt is not None:
            age_minutes = max((_utc_now() - created_dt).total_seconds() / 60, 1)

        candle_limit = max(12, min(72, int(max(age_minutes, evaluation_window) / 5) + 4))
        candles = await fetch_intraday_candles(symbol, interval="5m", limit=candle_limit)

        if candles:
            timestamps = [_extract_candle_timestamp_ms(candle) for candle in candles]
            valid_timestamps = [ts for ts in timestamps if ts is not None]
            if valid_timestamps:
                latest_candle_at = datetime.fromtimestamp(max(valid_timestamps) / 1000.0, tz=timezone.utc)

            relevant_candles = list(candles)

            if created_dt is not None:
                # Use exact signal creation time as cutoff — not minus 5 minutes.
                # A 5m candle starting BEFORE the signal includes pre-signal wicks
                # which cause false TP/SL hits on volatile instruments.
                cutoff_ms = created_dt.timestamp() * 1000
                filtered = []
                for candle in candles:
                    candle_ts = _extract_candle_timestamp_ms(candle)
                    if candle_ts is not None and candle_ts >= cutoff_ms:
                        filtered.append(candle)
                if filtered:
                    relevant_candles = filtered
                    has_post_entry_candles = True
                else:
                    freshness = False
                    if latest_candle_at is not None:
                        freshness = (_utc_now() - latest_candle_at).total_seconds() / 60.0 <= MARKET_DATA_FRESHNESS_THRESHOLD_MINUTES
                    return {
                        "high": current,
                        "low": current,
                        "current": current,
                        "has_post_entry_candles": False,
                        "market_data_fresh": freshness,
                        "latest_candle_at": _utc_iso(latest_candle_at) if latest_candle_at else None,
                    }

            highs = [float(c["high"]) for c in relevant_candles if c.get("high") is not None]
            lows = [float(c["low"]) for c in relevant_candles if c.get("low") is not None]
            closes = [float(c["close"]) for c in relevant_candles if c.get("close") is not None]

            window_current = closes[-1] if closes else current
            if window_current is not None:
                current = window_current

            if highs and lows:
                freshness = False
                if latest_candle_at is not None:
                    freshness = (_utc_now() - latest_candle_at).total_seconds() / 60.0 <= MARKET_DATA_FRESHNESS_THRESHOLD_MINUTES
                return {
                    "high": max(highs + ([current] if current is not None else [])),
                    "low": min(lows + ([current] if current is not None else [])),
                    "current": current,
                    "has_post_entry_candles": has_post_entry_candles,
                    "market_data_fresh": freshness,
                    "latest_candle_at": _utc_iso(latest_candle_at) if latest_candle_at else None,
                }
    except Exception as e:
        logger.warning(f"lifecycle.price_window_error | symbol={symbol} error={e}")

    if current is not None:
        return {
            "high": current,
            "low": current,
            "current": current,
            "has_post_entry_candles": has_post_entry_candles,
            "market_data_fresh": False,
            "latest_candle_at": _utc_iso(latest_candle_at) if latest_candle_at else None,
        }

    return {
        "high": None,
        "low": None,
        "current": None,
        "has_post_entry_candles": has_post_entry_candles,
        "market_data_fresh": False,
        "latest_candle_at": _utc_iso(latest_candle_at) if latest_candle_at else None,
    }


def _is_favorable_vs_entry(entry_price: float, current_price: float, direction: str) -> bool:
    if direction == "BUY":
        return current_price > entry_price
    if direction == "SELL":
        return current_price < entry_price
    return False

# ─── Helper: capture current indicators for failure analysis ─────────────────

async def _capture_indicators(symbol: str) -> Dict[str, Any]:
    """Capture a snapshot of all technical indicators at this moment."""
    try:
        from services.ta_service import compute_ta_snapshot
        ta = await compute_ta_snapshot(symbol)
        if ta:
            return {
                "rsi_14": ta.get("rsi_14"),
                "rsi_7": ta.get("rsi_7"),
                "macd_hist": ta.get("macd_hist"),
                "macd_line": ta.get("macd_line"),
                "macd_signal": ta.get("macd_signal"),
                "ema_20": ta.get("ema_20"),
                "ema_50": ta.get("ema_50"),
                "ema_200": ta.get("ema_200"),
                "adx": ta.get("adx"),
                "stoch_k": ta.get("stoch_k"),
                "boll_zscore": ta.get("boll_zscore"),
                "boll_width": ta.get("boll_width"),
                "atr_14": ta.get("atr_14"),
                "atr_pct": ta.get("atr_pct"),
                "mfi": ta.get("mfi"),
                "williams_r": ta.get("williams_r"),
                "close": ta.get("close"),
            }
    except Exception as e:
        logger.warning(f"_capture_indicators error for {symbol}: {e}")
    return {}


# ─── Helper: determine failure type ─────────────────────────────────────────

def _classify_failure(signal: dict, hit_any_target: bool, post_stop_direction: Optional[str] = None) -> str:
    """Classify why a signal failed."""
    targets_hit = parse_json_field(signal.get("targets_hit"), {})
    any_target_was_hit = any(targets_hit.values()) if targets_hit else hit_any_target

    if any_target_was_hit:
        return "volatile_reversal"  # Hit target then reversed to stop
    if post_stop_direction and post_stop_direction != signal.get("ml_direction"):
        return "whipsaw"  # Stopped out then went in predicted direction
    return "hard_stop"


# ─── Helper: get market context for failure analysis ─────────────────────────

async def _get_market_context() -> Dict[str, Any]:
    """Get macro context (VIX, DXY, session) for correlation."""
    ctx: Dict[str, Any] = {}
    try:
        from services.data_hub import get_macro
        macro = get_macro()
        if macro:
            ctx["vix"] = macro.get("vix", {}).get("price")
            ctx["dxy"] = macro.get("dxy", {}).get("price")
            ctx["usdtry"] = macro.get("usdtry", {}).get("price")
    except Exception:
        pass

    now_utc = _utc_now()
    hour = now_utc.hour
    if 0 <= hour < 8:
        ctx["session"] = "asia"
    elif 8 <= hour < 13:
        ctx["session"] = "europe"
    elif 13 <= hour < 21:
        ctx["session"] = "us"
    else:
        ctx["session"] = "closed"
    ctx["hour_utc"] = hour
    return ctx


def _update_signal_status(client, signal_id: str, status: str, exit_price=None, resolution_reason: Optional[str] = None, exit_time: Optional[str] = None):
    """Helper to update a signal's status in prediction_logs."""
    resolved_exit_time = exit_time or _utc_iso()
    update_data = {"status": status, "exit_time": resolved_exit_time}
    if exit_price is not None:
        update_data["exit_price"] = round(float(exit_price), 4)
    if resolution_reason:
        update_data["resolution_reason"] = resolution_reason
    try:
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data)
        if result and safe_get_data(result):
            logger.info(f"✅ Signal {signal_id[:8]} status updated to {status} (exit_time={resolved_exit_time})")
        return result
    except Exception as e:
        logger.error(f"Failed to update signal status {signal_id[:8]}: {e}")
        return None


# ═════════════════════════════════════════════════════════════════════════════
#  CORE: Process a single active signal
# ═════════════════════════════════════════════════════════════════════════════

async def _process_signal(client, signal: dict) -> Optional[str]:
    """
    Process one active signal:
      1. Get post-entry price window (high/low/current)
      2. Calculate profit/drawdown
      3. Check TP hits
      4. Check SL
      5. Update prediction_logs
      6. If stopped -> create failure autopsy

    (Per-check audit rows are written separately by signal_trajectory_service
    into signal_trajectory_snapshots — the old signal_checks insert was
    removed in commit 4a1bbd6.)

    Rules:
      - TP1 / TP2 / TP3 hit => signal counts as successful
      - If TP1/TP2/TP3 hit and later SL hits => still completed
      - TP4 hit => completed
      - At evaluation-window end, resolve by TP hit or entry-vs-current comparison
      - Avoid blind expired outcomes where possible

    Returns:
      new status if changed, otherwise None
    """
    signal_id = signal["id"]
    symbol = signal["symbol"]
    direction = (signal.get("ml_direction") or "HOLD").upper().strip()
    entry_price = _coerce_float(signal.get("ml_entry_price"))
    timeframe = _normalize_timeframe(signal.get("timeframe"))
    evaluation_window = _evaluation_window_minutes(timeframe)

    parse_json_fields(signal, ["targets", "targets_hit", "factors"])

    # Invalid tradeable signal -> stopped, not expired
    if entry_price is None or direction not in {"BUY", "SELL"}:
        _update_signal_status(client, signal_id, "stopped", entry_price)
        logger.info(
            f"lifecycle.invalid_signal | signal={signal_id[:8]} symbol={symbol} "
            f"direction={direction} entry={entry_price} -> stopped"
        )
        return "stopped"

    created_dt = _parse_created_at(signal.get("created_at"))
    if created_dt is not None and not is_symbol_market_open(symbol, created_dt):
        # Grace buffer: boundary signals (within 30min of a market-open window)
        # are likely timing drift vs retroactive kills. Only flag as market_closed_invalid
        # when the signal is clearly deep inside a market-closed period on both sides.
        buffer = timedelta(minutes=30)
        if not is_symbol_market_open(symbol, created_dt - buffer) and not is_symbol_market_open(symbol, created_dt + buffer):
            _update_signal_status(
                client,
                signal_id,
                "expired",
                None,
                resolution_reason="market_closed_invalid",
            )
            logger.warning(
                f"lifecycle.invalid_market_closed_signal | signal={signal_id[:8]} symbol={symbol} created_at={signal.get('created_at')}"
            )
            return "expired"
        logger.info(
            f"lifecycle.market_boundary_grace | signal={signal_id[:8]} symbol={symbol} "
            f"created_at={signal.get('created_at')} — within 30min of market window, not killing"
        )

    # ------------------------------------------------------------------
    # Chronological Candle Evaluation (Strict Verification Logic)
    # ------------------------------------------------------------------
    target_prices = _resolve_target_prices(signal, entry_price, direction, symbol, timeframe)
    sl_price = calculate_stoploss_price(entry_price, direction, symbol, timeframe)
    resolved_sl_pips = abs(pips_from_price_change(abs(entry_price - sl_price), symbol))

    pip_size = _get_pip_size(symbol)
    spread = SYMBOL_SPREADS.get(symbol, 2.0) * pip_size
    slippage = 1.0 * pip_size

    age_minutes = 0.0
    if created_dt is not None:
        age_minutes = max((_utc_now() - created_dt).total_seconds() / 60.0, 1.0)

    # Fetch 1-minute candles for the evaluation window (plus small buffer)
    candle_limit = max(30, int(age_minutes) + 10)
    candle_interval = "1m"
    candles = await fetch_intraday_candles(symbol, interval="1m", limit=candle_limit)

    # The live MT5->Redis feed only streams 5m/1h/1d bars (no mt5:bar:1m), so the
    # 1m fetch is frequently empty and would freeze resolution indefinitely. Fall
    # back to the live 5m series; the pre-entry wick guard below still protects
    # against false TP/SL hits from the candle that straddles the signal time.
    if not candles:
        candle_interval = "5m"
        candles = await fetch_intraday_candles(
            symbol, interval="5m", limit=max(12, candle_limit // 5 + 4)
        )

    # Filter candles starting from the signal creation time
    relevant_candles = []
    latest_candle_at = None
    if candles and created_dt is not None:
        cutoff_ms = created_dt.timestamp() * 1000
        for c in candles:
            c_ts = _extract_candle_timestamp_ms(c)
            if c_ts is not None:
                if c_ts >= cutoff_ms:
                    relevant_candles.append(c)
                latest_candle_at = datetime.fromtimestamp(c_ts / 1000.0, tz=timezone.utc)

    # Determine data freshness
    market_data_fresh = False
    if latest_candle_at is not None:
        market_data_fresh = (_utc_now() - latest_candle_at).total_seconds() / 60.0 <= MARKET_DATA_FRESHNESS_THRESHOLD_MINUTES

    if created_dt is not None and not relevant_candles:
        logger.info(
            f"lifecycle.defer_no_post_entry_candles | signal={signal_id[:8]} symbol={symbol} interval={candle_interval} latest_candle={_utc_iso(latest_candle_at) if latest_candle_at else None}"
        )
        return None

    # Chronological simulation state
    new_status = None
    exit_price = None
    exit_time = None
    resolution_reason = None
    targets_hit = {}
    targets_hit_times = {}

    # 2026-07-01 (rapor aksiyon #1): Önceki check'lerde DB'ye yazılmış TP
    # vuruşlarını tohumla. 1m/5m fetch penceresi sinyal başlangıcını
    # kapsamadığında TP bilgisi kaybolup sinyal haksız yere 'stopped'
    # oluyordu. Tohumlanan vuruşların zamanı bilinmediği için
    # targets_hit_times'a girilmez (aşağıdaki fallback'ler halleder).
    _stored_hits = signal.get("targets_hit")
    if isinstance(_stored_hits, dict):
        for _tp_name, _tp_val in _stored_hits.items():
            if _tp_val:
                targets_hit[str(_tp_name)] = True

    new_high = 0.0
    new_low = 0.0

    # Simulate candles chronologically
    for c in relevant_candles:
        c_time = _parse_candle_time(c)
        c_date = c.get("date") or _utc_iso(c_time)
        
        # Pre-entry wick guard: skip candle if it closed before or exactly at entry (within 60s)
        is_guard_period = (c_time - created_dt).total_seconds() < 60

        c_high = float(c["high"])
        c_low = float(c["low"])
        c_close = float(c["close"])

        # Calculate profit/drawdown
        if direction == "BUY":
            prof = pips_from_price_change(c_high - entry_price, symbol)
            draw = pips_from_price_change(c_low - entry_price, symbol)
        else:
            prof = pips_from_price_change(entry_price - c_low, symbol)
            draw = pips_from_price_change(entry_price - c_high, symbol)

        new_high = max(new_high, prof)
        new_low = min(new_low, draw)

        # Skip SL/TP checking during the guard period to prevent false positive wicks
        if is_guard_period:
            continue

        # Check TP hits
        for tp_name, tp_val in target_prices.items():
            if targets_hit.get(tp_name):
                continue

            tp_pips_distance = abs(pips_from_price_change(abs(tp_val - entry_price), symbol))

            # Sanity gate: cumulative best profit must be at least 60% of target distance
            tp_drawdown_ok = tp_pips_distance <= 0 or new_high >= tp_pips_distance * 0.6

            if direction == "BUY" and (c_high - spread) >= tp_val and tp_drawdown_ok:
                targets_hit[tp_name] = True
                targets_hit_times[tp_name] = c_date
            elif direction == "SELL" and (c_low + spread) <= tp_val and tp_drawdown_ok:
                targets_hit[tp_name] = True
                targets_hit_times[tp_name] = c_date

        # Check SL hit
        hit_stop = False
        sl_drawdown_ok = resolved_sl_pips <= 0 or abs(new_low) >= resolved_sl_pips * 0.6

        if direction == "BUY" and c_low <= (sl_price + slippage) and sl_drawdown_ok:
            hit_stop = True
        elif direction == "SELL" and c_high >= (sl_price - slippage) and sl_drawdown_ok:
            hit_stop = True

        tp1_3_hit = any(tp in {"TP1", "TP2", "TP3"} for tp in targets_hit)

        if hit_stop:
            # If TP1-3 was hit BEFORE (or in a previous candle), we exit with win!
            if tp1_3_hit:
                new_status = "completed"
                # Find the earliest TP exit time
                if targets_hit_times:
                    earliest_tp = min(targets_hit_times.keys(), key=lambda k: targets_hit_times[k])
                    exit_time = targets_hit_times[earliest_tp]
                else:
                    # TP vuruşu önceki check'ten tohumlandı — zamanı bilinmiyor
                    earliest_tp = next(
                        tp for tp in ("TP1", "TP2", "TP3") if targets_hit.get(tp)
                    )
                    exit_time = c_date
                exit_price = target_prices.get(earliest_tp, entry_price)
                resolution_reason = "tp1_3_hit_then_sl"
                break
            else:
                new_status = "stopped"
                exit_time = c_date
                exit_price = sl_price
                resolution_reason = "sl_hit"
                break

        # If TP4 is hit, it completes immediately
        if targets_hit.get("TP4"):
            new_status = "completed"
            exit_time = targets_hit_times.get("TP4", c_date)
            exit_price = target_prices.get("TP4", entry_price)
            resolution_reason = "tp4_hit"
            break

    # If loop finished without breaking, check evaluation window expiry
    if not new_status and relevant_candles:
        last_c = relevant_candles[-1]
        last_c_time = _parse_candle_time(last_c)
        last_c_date = last_c.get("date") or _utc_iso(last_c_time)
        last_c_close = float(last_c["close"])
        age_at_end = (last_c_time - created_dt).total_seconds() / 60.0

        if age_at_end >= evaluation_window:
            if not market_data_fresh:
                logger.info(
                    f"lifecycle.defer_window_resolution | signal={signal_id[:8]} symbol={symbol} age={age_at_end:.0f}m latest_candle={_utc_iso(latest_candle_at)}"
                )
                return None

            tp1_3_hit = any(tp in {"TP1", "TP2", "TP3"} for tp in targets_hit)
            tp1_distance = 0.0
            if target_prices:
                try:
                    tp1_price = target_prices.get("TP1")
                    if tp1_price and entry_price:
                        tp1_distance = abs(float(tp1_price) - float(entry_price))
                except Exception:
                    pass
            mfe_in_pips = abs(new_high) if new_high else 0.0
            real_tp_reached = tp1_3_hit or (
                tp1_distance > 0 and mfe_in_pips >= tp1_distance * 0.95
            )

            favorable_vs_entry = _is_favorable_vs_entry(entry_price, last_c_close, direction)

            if real_tp_reached:
                new_status = "completed"
                # Get the first TP hit time and price
                if targets_hit_times:
                    earliest_tp = min(targets_hit_times.keys(), key=lambda k: targets_hit_times[k])
                    exit_time = targets_hit_times[earliest_tp]
                    exit_price = target_prices[earliest_tp]
                else:
                    exit_time = last_c_date
                    exit_price = last_c_close
                resolution_reason = "window_resolve_positive"
            elif favorable_vs_entry:
                new_status = "expired"
                exit_time = last_c_date
                exit_price = last_c_close
                resolution_reason = "window_resolve_inconclusive"
            else:
                new_status = "stopped"
                exit_time = last_c_date
                exit_price = last_c_close
                resolution_reason = "window_resolve_negative"

            logger.info(
                f"⏰ Signal {signal_id[:8]} {symbol} resolved after {age_at_end:.0f}m "
                f"-> {new_status} "
                f"(tp1_3={tp1_3_hit}, tp4={targets_hit.get('TP4')}, favorable={favorable_vs_entry})"
            )

    # Use final candle close as current price reference
    current = float(relevant_candles[-1]["close"]) if relevant_candles else entry_price

    # ------------------------------------------------------------------
    # 7. prediction_logs update
    # ------------------------------------------------------------------
    update_data: Dict[str, Any] = {
    "highest_profit_pips": round(new_high, 2),
    "lowest_drawdown_pips": round(new_low, 2),
    "targets_hit": dict(targets_hit),
    "targets": dict(target_prices),
    "stop_loss_pips": round(resolved_sl_pips, 2),
    "resolution_reason": resolution_reason,
    }

    # İstersen ve DB kolonun varsa bunu aç:
    # if resolution_reason:
    #     update_data["resolution_reason"] = resolution_reason

    # ──────────────────────────────────────────────────────────────────
    # Post-Entry Trajectory Learner (PETL) — v1 rule-based deterioration
    # Capture a snapshot every check. If signal still active AND already
    # in drawdown AND trajectory rules say it's deteriorating, force abort.
    # ──────────────────────────────────────────────────────────────────
    trajectory_alert: Optional[Dict[str, Any]] = None
    if not new_status and current is not None:
        try:
            from services.signal_trajectory_service import (
                capture_snapshot as _traj_capture,
                log_abort as _traj_log_abort,
            )
            trajectory_alert = await _traj_capture(
                signal=signal,
                current_price=current,
                current_profit_pips=new_high,
                current_drawdown_pips=new_low,
            )
            # Abort logic — conservative gate to avoid premature exits
            #   - deterioration score ≥ threshold
            #   - already in real drawdown (>30% of SL distance traveled)
            #   - trade is not in profit (don't kill a winning trade on noise)
            if (trajectory_alert
                    and trajectory_alert.get("deteriorating")
                    and new_high < 1.0           # not already winning
                    and not any(targets_hit.values())  # 2026-07-01: TP görmüş sinyal abort edilmez
                    and resolved_sl_pips > 0
                    and abs(new_low) >= resolved_sl_pips * 0.3):
                new_status = "stopped"
                resolution_reason = f"deterioration_abort:{trajectory_alert['score']:.2f}"
                exit_price = current
                # Estimate what we would have lost if we held to SL
                saved_pips = max(0.0, resolved_sl_pips - abs(new_low))
                logger.warning(
                    f"🛑 Signal {signal_id[:8]} {symbol} ABORTED — "
                    f"deterioration={trajectory_alert['score']:.2f} "
                    f"reasons={trajectory_alert['reasons']} "
                    f"pnl@abort={new_low:.1f}p saved≈{saved_pips:.1f}p"
                )
                await _traj_log_abort(
                    signal=signal,
                    reason=resolution_reason + " | " + "; ".join(trajectory_alert["reasons"]),
                    source="rule_v1",
                    pnl_at_abort_pips=float(new_low or 0),
                    saved_pips_estimate=saved_pips,
                    factors={"score": trajectory_alert["score"],
                             "reasons": trajectory_alert["reasons"]},
                )
        except Exception as traj_err:
            logger.debug(f"trajectory check failed for {signal_id[:8]}: {traj_err}")

    if new_status:
        update_data["status"] = new_status
        update_data["exit_price"] = round(exit_price, 4) if exit_price is not None else None
        update_data["exit_time"] = _utc_iso()

    try:
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data)
        if result and safe_get_data(result) and new_status:
            logger.info(
                f"✅ Signal {signal_id[:8]} updated: "
                f"status={new_status}, reason={resolution_reason}, "
                f"high={new_high:.1f}p, low={new_low:.1f}p"
            )
    except Exception as e:
        logger.error(f"Failed to update signal {signal_id[:8]}: {e}")

    # ------------------------------------------------------------------
    # 8. Failure autopsy
    # ------------------------------------------------------------------
    if new_status == "stopped":
        await _create_failure_autopsy(client, signal, targets_hit, current)

    if new_status in {"completed", "stopped"}:
        try:
            model_type = normalize_model_type(signal)
            if model_type == "meta":
                resolved_signal = dict(signal)
                resolved_signal.update(update_data)
                factors = resolved_signal.get("factors") or {}
                if not isinstance(factors, dict):
                    factors = parse_json_field(factors, {})
                combo_key = str(factors.get("source_combo") or "").strip()
                regime = str(factors.get("regime") or "UNKNOWN").strip() or "UNKNOWN"
                if combo_key:
                    _, is_win, scored_pips = classify_signal(resolved_signal, default_symbol=symbol)
                    if is_win is not None and scored_pips is not None:
                        from services.meta_signal_logger import update_combination_stats
                        await update_combination_stats(
                            combo_key=combo_key,
                            symbol=symbol,
                            regime=regime,
                            is_win=bool(is_win),
                            profit_pips=abs(float(scored_pips)),
                        )
        except Exception as combo_err:
            logger.warning(
                f"lifecycle.meta_combo_update_failed | signal={signal_id[:8]} symbol={symbol} error={combo_err}"
            )

    return new_status


# ═════════════════════════════════════════════════════════════════════════════
#  Failure Autopsy
# ═════════════════════════════════════════════════════════════════════════════

async def _create_failure_autopsy(
    client, signal: dict, targets_hit: dict, current_price: float
):
    """Create a detailed failure analysis record."""
    signal_id = signal["id"]
    symbol = signal["symbol"]

    try:
        # Capture indicators at failure moment
        failure_indicators = await _capture_indicators(symbol)

        # Entry indicators from stored factors
        entry_indicators = parse_json_field(signal.get("factors"), {})

        # Get last 5 candles for price action context
        price_action = []
        try:
            candles = await fetch_intraday_candles(symbol, interval="5m", limit=5)
            if candles:
                for c in candles[-5:]:
                    price_action.append({
                        "open": c.get("open"),
                        "high": c.get("high"),
                        "low": c.get("low"),
                        "close": c.get("close"),
                        "volume": c.get("volume"),
                    })
        except Exception:
            pass

        # Market context
        market_ctx = await _get_market_context()

        # Classify failure type
        hit_any = any(targets_hit.values()) if targets_hit else False
        failure_type = _classify_failure(signal, hit_any)

        # Confluence score: how many indicators agreed at entry
        confluence = _calculate_confluence(entry_indicators, signal.get("ml_direction", "HOLD"))

        # Contradiction flags
        contradictions = _find_contradictions(entry_indicators, signal.get("ml_direction", "HOLD"))

        # Market regime
        adx = failure_indicators.get("adx", 20)
        atr_pct = failure_indicators.get("atr_pct", 0)
        if adx and adx >= 25:
            regime = "trending"
        elif atr_pct and atr_pct > 1.5:
            regime = "volatile"
        else:
            regime = "range"

        # Insert failure record
        failure_record = {
            "signal_id": signal_id,
            "failure_type": failure_type,
            "entry_indicators": json.dumps(entry_indicators),
            "failure_indicators": json.dumps(failure_indicators),
            "price_action_context": json.dumps(price_action),
            "market_regime": regime,
            "correlation_context": json.dumps(market_ctx),
            "confluence_score": confluence,
            "contradiction_flags": json.dumps(contradictions),
            "retrain_weight": 0.5,
        }

        client.table("signal_failures").insert(failure_record)
        logger.info(f"📋 Failure autopsy saved for {signal_id[:8]}: type={failure_type}, regime={regime}, confluence={confluence}")

    except Exception as e:
        logger.error(f"Failed to create failure autopsy for {signal_id[:8]}: {e}")


def _calculate_confluence(indicators: dict, direction: str) -> int:
    """Count how many indicators agreed with the signal direction at entry."""
    score = 0
    if not indicators:
        return 0

    rsi = indicators.get("rsi_14")
    macd = indicators.get("macd_histogram") or indicators.get("macd_hist")
    ema20_dist = indicators.get("ema20_distance_pct") or indicators.get("ema_20")
    stoch = indicators.get("stoch_k")
    adx = indicators.get("adx")

    if direction == "BUY":
        if rsi and rsi > 50: score += 1
        if macd and macd > 0: score += 1
        if ema20_dist and ema20_dist > 0: score += 1
        if stoch and stoch > 50: score += 1
        if adx and adx > 25: score += 1
    elif direction == "SELL":
        if rsi and rsi < 50: score += 1
        if macd and macd < 0: score += 1
        if ema20_dist and ema20_dist < 0: score += 1
        if stoch and stoch < 50: score += 1
        if adx and adx > 25: score += 1

    return score


def _find_contradictions(indicators: dict, direction: str) -> Dict[str, str]:
    """Find which indicators contradicted the signal at entry."""
    flags = {}
    if not indicators:
        return flags

    rsi = indicators.get("rsi_14")
    macd = indicators.get("macd_histogram") or indicators.get("macd_hist")
    stoch = indicators.get("stoch_k")
    boll_z = indicators.get("boll_zscore")

    if direction == "BUY":
        if rsi and rsi > 70: flags["rsi_overbought"] = f"RSI={rsi:.0f}"
        if macd and macd < 0: flags["macd_bearish"] = f"MACD_H={macd:.4f}"
        if stoch and stoch > 80: flags["stoch_overbought"] = f"Stoch={stoch:.0f}"
        if boll_z and boll_z > 2: flags["boll_upper"] = f"Z={boll_z:.2f}"
    elif direction == "SELL":
        if rsi and rsi < 30: flags["rsi_oversold"] = f"RSI={rsi:.0f}"
        if macd and macd > 0: flags["macd_bullish"] = f"MACD_H={macd:.4f}"
        if stoch and stoch < 20: flags["stoch_oversold"] = f"Stoch={stoch:.0f}"
        if boll_z and boll_z < -2: flags["boll_lower"] = f"Z={boll_z:.2f}"

    return flags


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN: Run lifecycle check for all active signals
# ═════════════════════════════════════════════════════════════════════════════

async def run_lifecycle_check() -> Dict[str, Any]:
    """
    Main entry point — runs every minute.
    1. Fetch all active signals
    2. Process each one (target/stop check, wick capture)
    3. Return summary with metrics
    """
    # Prevent concurrent lifecycle checks within same process
    if _lifecycle_lock.locked():
        logger.info("lifecycle.skip | reason=already_running")
        return {"skipped": True, "reason": "already_running"}

    async with _lifecycle_lock:
        return await _run_lifecycle_check_inner()


async def _run_lifecycle_check_inner() -> Dict[str, Any]:
    """Inner implementation — always called under _lifecycle_lock."""
    t_start = time.monotonic()

    if not is_db_available():
        return {"error": "DB not available"}

    client = get_supabase_client()
    if not client:
        return {"error": "No DB client"}

    summary = {
        "checked": 0,
        "completed": 0,
        "stopped": 0,
        "expired": 0,
        "still_active": 0,
        "errors": 0,
        "target_hits": [],
        "timestamp": _utc_iso(),
    }

    try:
        # Try RPC-based claim (row-level locking for multi-instance safety)
        signals = None
        try:
            rpc_result = client.rpc("claim_active_signals", {"p_limit": MAX_ACTIVE_SIGNALS})
            if safe_get_data(rpc_result) and isinstance(rpc_result["data"], list):
                signals = rpc_result["data"]
                logger.debug(f"lifecycle.claim_rpc | claimed={len(signals)}")
        except Exception as rpc_err:
            logger.debug(f"lifecycle.claim_rpc_fallback | error={rpc_err}")

        # Fallback to REST query if RPC unavailable
        if signals is None:
            result = client.table("prediction_logs").select("*").eq(
                "status", "active"
            ).order("created_at", desc=True).limit(MAX_ACTIVE_SIGNALS).execute()
            signals = safe_get_data(result)

        if not signals:
            duration_ms = (time.monotonic() - t_start) * 1000
            metrics.record_check(duration_ms, 0, 0, 0, 0, 0)
            summary["duration_ms"] = round(duration_ms, 1)
            return summary

        logger.info(f"lifecycle.check_start | signals={len(signals)}")

        for signal in signals:
            sig_id = signal.get("id", "?")[:8]
            sig_symbol = signal.get("symbol", "?")
            sig_model = signal.get("model_type", "?")
            sig_dir = signal.get("ml_direction", "?")

            try:
                new_status = await _process_signal(client, signal)
                summary["checked"] += 1

                if new_status == "completed":
                    summary["completed"] += 1
                    summary["target_hits"].append({
                        "signal_id": sig_id,
                        "symbol": sig_symbol,
                        "direction": sig_dir,
                    })
                elif new_status == "stopped":
                    summary["stopped"] += 1
                elif new_status == "expired":
                    summary["expired"] += 1
                else:
                    summary["still_active"] += 1

            except Exception as e:
                summary["errors"] += 1
                # Structured error log with full signal context
                logger.error(
                    f"lifecycle.process_error | signal={sig_id} symbol={sig_symbol} "
                    f"model={sig_model} direction={sig_dir} "
                    f"error_type={type(e).__name__} error={e}"
                )
                logger.debug(f"lifecycle.process_traceback | signal={sig_id}\n{traceback.format_exc()}")
                # TODO: Sentry hook — sentry_sdk.capture_exception(e, tags={...})

            # Small delay between signals to avoid overwhelming DataHub
            await asyncio.sleep(0.2)

        duration_ms = (time.monotonic() - t_start) * 1000
        summary["duration_ms"] = round(duration_ms, 1)

        # Record metrics
        metrics.record_check(
            duration_ms,
            processed=summary["checked"],
            errors=summary["errors"],
            completed=summary["completed"],
            stopped=summary["stopped"],
            expired=summary["expired"],
        )

        logger.info(
            f"lifecycle.check_done | checked={summary['checked']} "
            f"completed={summary['completed']} stopped={summary['stopped']} "
            f"expired={summary['expired']} active={summary['still_active']} "
            f"errors={summary['errors']} duration_ms={summary['duration_ms']}"
        )

    except Exception as e:
        logger.error(f"lifecycle.check_fatal | error_type={type(e).__name__} error={e}\n{traceback.format_exc()}")
        summary["error"] = str(e)

    # Invalidate dashboard stats cache and learning router cache
    await _dashboard_stats_cache.invalidate_all()
    try:
        from routers.learning import _learning_stats_cache
        await _learning_stats_cache.invalidate_all()
    except Exception as e:
        logger.warning(f"Failed to invalidate learning stats cache: {e}")

    # Record job state for scheduler resilience
    _record_job_state(client, "lifecycle_check", summary)

    return summary


def _record_job_state(client, job_name: str, summary: Dict[str, Any]):
    """Persist job run metadata to scheduler_state table for observability & catch-up."""
    if not client:
        return
    try:
        client.table("scheduler_state").eq("job_name", job_name).update({
            "last_run_at": _utc_iso(),
            "last_duration_ms": summary.get("duration_ms", 0),
            "last_status": "error" if safe_get_error(summary) else "ok",
            "last_error": safe_get_error(summary),
            "run_count": 1,  # Will use raw SQL increment later if needed
            "updated_at": _utc_iso(),
        }).execute()
    except Exception as e:
        logger.debug(f"_record_job_state({job_name}): {e}")


# ═════════════════════════════════════════════════════════════════════════════
#  Cleanup: archive old signals, cap active count
# ═════════════════════════════════════════════════════════════════════════════

async def cleanup_old_signals():
    """
    1. Resolve active signals that exceed timeframe-aware cleanup grace
    2. Keep signal_checks retention bounded
    """
    if not is_db_available():
        return

    client = get_supabase_client()
    if not client:
        return

    try:
        result = client.table("prediction_logs").select("*").eq(
            "status", "active"
        ).order("created_at", desc=False).limit(200).execute()

        stale = safe_get_data(result) or []
        resolved_count = 0

        for s in stale:
            try:
                created_dt = _parse_created_at(s.get("created_at"))
                if created_dt is None:
                    continue

                age_minutes = (_utc_now() - created_dt).total_seconds() / 60
                if age_minutes < _cleanup_grace_minutes(s.get("timeframe")):
                    continue

                new_status = await _process_signal(client, s)
                if new_status in {"completed", "stopped"}:
                    resolved_count += 1
            except Exception as upd_err:
                logger.warning(f"Failed to resolve signal {s['id'][:8]}: {upd_err}")

        if resolved_count:
            logger.info(f"🧹 Resolved {resolved_count} stale active signals beyond cleanup grace")

        archive_cutoff = _utc_iso(_utc_now() - timedelta(days=ARCHIVE_AFTER_DAYS))
        client.table("signal_checks").select("id").lt(
            "created_at", archive_cutoff
        ).limit(500).execute()
        logger.debug("Cleanup cycle completed")

    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ═════════════════════════════════════════════════════════════════════════════
#  Dashboard Data: aggregated stats per model
# ═════════════════════════════════════════════════════════════════════════════

async def get_dashboard_stats(days: int = 365) -> Dict[str, Any]:
    """
    Build Learning Dashboard v2 data:
      - Per model type: total, win rate, avg profit, avg loss, R/R, target rates
      - Failure patterns breakdown
      - Cumulative pips over time
    """
    if not is_db_available():
        return {"error": "DB not available"}

    client = get_supabase_client()
    if not client:
        return {"error": "No DB client"}

    # Cache check
    cached = await _dashboard_stats_cache.get(days)
    if cached is not None:
        logger.info(f"Dashboard stats cache HIT for days={days}")
        return cached

    try:
        tf_order = ["5m", "15m", "20m", "30m", "1h", "4h", "1d"]

        # Supabase PostgREST caps at 1000 rows per request.
        # Fetch with offset range pagination to minimize round trips.
        signals = []

        # Determine date range
        if days > 0:
            start_date = _utc_now() - timedelta(days=days)
        else:
            oldest_result = client.table("prediction_logs").select(
                "created_at"
            ).order("created_at", desc=False).limit(1).execute()
            oldest_rows = safe_get_data(oldest_result) or []
            oldest_created_at = oldest_rows[0].get("created_at") if oldest_rows else None
            oldest_dt = None
            if oldest_created_at:
                try:
                    oldest_dt = datetime.fromisoformat(str(oldest_created_at).replace("Z", "+00:00"))
                except Exception:
                    oldest_dt = None
            start_date = _as_utc(oldest_dt) if oldest_dt else (_utc_now() - timedelta(days=90))

        end_date = _utc_now()
        start_date_iso = _utc_iso(start_date)
        end_date_iso = _utc_iso(end_date)

        offset = 0
        limit = 1000
        while True:
            result = client.table("prediction_logs").select(
                "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
                "model_type, status, targets_hit, highest_profit_pips, "
                "lowest_drawdown_pips, exit_price, exit_time, stop_loss_pips, "
                "targets, created_at, strategy, resolution_reason"
            ).neq("status", "active").gte(
                "created_at", start_date_iso
            ).lt(
                "created_at", end_date_iso
            ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            batch = safe_get_data(result)
            if not batch:
                break
            signals.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        signals = filter_market_closed_invalid_signals(signals)

        logger.info(f"Dashboard: fetched {len(signals)} total signals via range pagination (offset={offset})")

        # Per-model stats
        models = {}
        for sig in signals:
            mt = normalize_model_type(sig)
            if mt not in models:
                models[mt] = {
                    "total": 0, "completed": 0, "stopped": 0, "expired": 0,
                    "total_profit_pips": 0, "total_loss_pips": 0,
                    "profits": [], "losses": [],
                    "target_hits": {},  # TP1: hit count, TP2: hit count, etc.
                    "symbols": {},
                    "timeframes": {},  # per-timeframe stats
                }

            m = models[mt]
            m["total"] += 1
            sym = sig.get("symbol", "?")
            status, _, scored_pips = classify_signal(sig, default_symbol=sym)
            if status not in {"completed", "stopped", "expired"}:
                continue
            m[status] = m.get(status, 0) + 1

            if sym not in m["symbols"]:
                m["symbols"][sym] = {
                    "total": 0, "completed": 0, "stopped": 0, "expired": 0,
                    "total_profit_pips": 0, "total_loss_pips": 0,
                    "target_hits": {},
                }
            m["symbols"][sym]["total"] += 1
            m["symbols"][sym][status] = m["symbols"][sym].get(status, 0) + 1

            tf = normalize_analytics_timeframe(sig.get("timeframe"))
            if tf:
                if tf not in m["timeframes"]:
                    m["timeframes"][tf] = {
                        "total": 0, "completed": 0, "stopped": 0, "expired": 0,
                        "total_profit_pips": 0, "total_loss_pips": 0,
                    }
                m["timeframes"][tf]["total"] += 1
                m["timeframes"][tf][status] = m["timeframes"][tf].get(status, 0) + 1

            if status == "completed":
                actual_profit = max(scored_pips or 0.0, 0.0)
                m["total_profit_pips"] += actual_profit
                m["profits"].append(actual_profit)
                m["symbols"][sym]["total_profit_pips"] += actual_profit
                if tf and tf in m["timeframes"]:
                    m["timeframes"][tf]["total_profit_pips"] += actual_profit
            elif status == "stopped":
                loss = abs(scored_pips or 0.0)
                m["total_loss_pips"] += loss
                m["losses"].append(loss)
                m["symbols"][sym]["total_loss_pips"] += loss
                if tf and tf in m["timeframes"]:
                    m["timeframes"][tf]["total_loss_pips"] += loss

            th = normalized_targets_hit(sig, default_symbol=sym)
            if status in {"completed", "stopped"} and th:
                for tp_name, hit in th.items():
                    if hit:
                        m["target_hits"][tp_name] = m["target_hits"].get(tp_name, 0) + 1
                        m["symbols"][sym]["target_hits"][tp_name] = (
                            m["symbols"][sym]["target_hits"].get(tp_name, 0) + 1
                        )

        # Ensure all known model types exist in response (even with 0 signals)
        KNOWN_MODELS = ["ml", "meta", "pulse1", "pulse2", "pulse3", "emel", "emel_inverse", "hybrid"]
        for km in KNOWN_MODELS:
            if km not in models:
                models[km] = {
                    "total": 0, "completed": 0, "stopped": 0, "expired": 0,
                    "total_profit_pips": 0, "total_loss_pips": 0,
                    "profits": [], "losses": [],
                    "target_hits": {},
                    "symbols": {},
                    "timeframes": {},
                }

        # Build final stats
        model_stats = {}
        for mt, m in models.items():
            # Exclude expired from win_rate calculation (only completed + stopped count)
            total_with_outcome = m["completed"] + m["stopped"]
            outcome_denominator = total_with_outcome or 1
            
            avg_profit = sum(m["profits"]) / len(m["profits"]) if m["profits"] else 0
            avg_loss = sum(m["losses"]) / len(m["losses"]) if m["losses"] else 0

            target_rates = {}
            for tp_name in ["TP1", "TP2", "TP3", "TP4"]:
                hits = m["target_hits"].get(tp_name, 0)
                target_rates[tp_name] = round(hits / outcome_denominator * 100, 1) if total_with_outcome > 0 else 0

            # Build per-symbol stats with target rates
            symbols_out = {}
            for sym, sd in m["symbols"].items():
                sym_target_rates = {}
                sym_total_with_outcome = sd.get("completed", 0) + sd.get("stopped", 0)
                sym_outcome_denominator = sym_total_with_outcome or 1
                for tp_name in ["TP1", "TP2", "TP3", "TP4"]:
                    hits = sd.get("target_hits", {}).get(tp_name, 0)
                    sym_target_rates[tp_name] = round(hits / sym_outcome_denominator * 100, 1) if sym_total_with_outcome > 0 else 0
                symbols_out[sym] = {
                    "total": sd["total"],
                    "completed": sd.get("completed", 0),
                    "stopped": sd.get("stopped", 0),
                    "expired": sd.get("expired", 0),
                    "win_rate": round(sd.get("completed", 0) / sym_outcome_denominator * 100, 1),
                    "net_pips": round(sd.get("total_profit_pips", 0) - sd.get("total_loss_pips", 0), 1),
                    "target_rates": sym_target_rates,
                }

            # Build per-timeframe stats
            timeframes_out = {}
            for tf_key in tf_order:
                if tf_key in m.get("timeframes", {}):
                    tfd = m["timeframes"][tf_key]
                    tf_outcome = tfd.get("completed", 0) + tfd.get("stopped", 0)
                    timeframes_out[tf_key] = {
                        "total": tfd["total"],
                        "completed": tfd.get("completed", 0),
                        "stopped": tfd.get("stopped", 0),
                        "expired": tfd.get("expired", 0),
                        "win_rate": round(tfd.get("completed", 0) / (tf_outcome or 1) * 100, 1),
                        "net_pips": round(tfd.get("total_profit_pips", 0) - tfd.get("total_loss_pips", 0), 1),
                    }

            model_stats[mt] = {
                "total_signals": m["total"],
                "completed": m["completed"],
                "stopped": m["stopped"],
                "expired": m["expired"],
                "win_rate": round(m["completed"] / outcome_denominator * 100, 1),
                "avg_profit_pips": round(avg_profit, 1),
                "avg_loss_pips": round(avg_loss, 1),
                "risk_reward": round(avg_profit / avg_loss, 2) if avg_loss > 0 else 0,
                "total_profit_pips": round(m["total_profit_pips"], 1),
                "total_loss_pips": round(m["total_loss_pips"], 1),
                "net_pips": round(m["total_profit_pips"] - m["total_loss_pips"], 1),
                "target_rates": target_rates,
                "symbols": symbols_out,
                "timeframe_stats": timeframes_out,
            }

        # Failure patterns
        fail_query = client.table("signal_failures").select(
            "failure_type, market_regime, confluence_score, signal_id"
        )
        if days > 0:
            fail_cutoff = _utc_iso(_utc_now() - timedelta(days=days))
            fail_query = fail_query.gte("created_at", fail_cutoff)
        fail_result = fail_query.limit(500).execute()

        failures = safe_get_data(fail_result)
        failure_breakdown = {}
        for f in failures:
            ft = f.get("failure_type", "unknown")
            failure_breakdown[ft] = failure_breakdown.get(ft, 0) + 1

        # Active signals count
        active_result = client.table("prediction_logs").select(
            "id"
        ).eq("status", "active").execute()
        active_count = len(safe_get_data(active_result))

        res = {
            "period_days": days,
            "model_stats": model_stats,
            "failure_breakdown": failure_breakdown,
            "total_failures": len(failures),
            "active_signals": active_count,
            "generated_at": _utc_iso(),
        }
        await _dashboard_stats_cache.set(days, res)
        return res

    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return {"error": str(e)}


async def get_signal_detail(signal_id: str) -> Dict[str, Any]:
    """Get full signal detail with all 5-min checks for the detail modal."""
    if not is_db_available():
        return {"error": "DB not available"}

    client = get_supabase_client()
    if not client:
        return {"error": "No DB client"}

    try:
        # Get the signal
        sig_result = client.table("prediction_logs").select("*").eq(
            "id", signal_id
        ).execute()
        sig_data = safe_get_data(sig_result)
        if not sig_data:
            return {"error": "Signal not found"}
        signal = sig_data[0]

        # Get all checks
        checks_result = client.table("signal_checks").select("*").eq(
            "signal_id", signal_id
        ).order("check_time", desc=False).execute()
        checks = safe_get_data(checks_result)

        # Get failure autopsy if exists
        fail_result = client.table("signal_failures").select("*").eq(
            "signal_id", signal_id
        ).execute()
        failure = (safe_get_data(fail_result) or [None])[0]

        # Parse JSON fields
        parse_json_fields(signal, ["targets", "targets_hit", "factors"])

        for check in checks:
            parse_json_fields(check, ["target_status"])

        if failure:
            parse_json_fields(failure, [
                "entry_indicators", "failure_indicators", "price_action_context",
                "correlation_context", "contradiction_flags",
            ])

        classified_status, _, classified_pnl = classify_signal(
            signal,
            default_symbol=signal.get("symbol"),
        )
        corrected_targets = resolved_targets(
            signal,
            default_symbol=signal.get("symbol"),
        )
        corrected_targets_hit = normalized_targets_hit(
            signal,
            default_symbol=signal.get("symbol"),
        )
        corrected_exit_price = resolved_exit_price(
            signal,
            default_symbol=signal.get("symbol"),
        )
        corrected_stop_loss_pips = canonical_stop_loss_pips(
            signal,
            default_symbol=signal.get("symbol"),
        )
        signal["normalized_status"] = classified_status or signal.get("status")
        signal["calculated_pnl_pips"] = round(classified_pnl, 2) if classified_pnl is not None else None
        signal["targets"] = {key: round(float(value), 4) for key, value in corrected_targets.items()}
        signal["targets_hit"] = {key: bool(corrected_targets_hit.get(key)) for key in corrected_targets.keys()}
        signal["stop_loss_pips"] = round(corrected_stop_loss_pips, 2) if corrected_stop_loss_pips is not None else signal.get("stop_loss_pips")
        signal["raw_exit_price"] = signal.get("exit_price")
        signal["exit_price"] = corrected_exit_price

        return {
            "signal": signal,
            "checks": checks,
            "failure": failure,
        }

    except Exception as e:
        logger.error(f"Signal detail error: {e}")
        return {"error": str(e)}


async def export_failures(days: int = 30) -> List[Dict[str, Any]]:
    """Export failure records for ML retraining dataset."""
    if not is_db_available():
        return []

    client = get_supabase_client()
    if not client:
        return []

    cutoff = _utc_iso(_utc_now() - timedelta(days=days))

    try:
        result = client.table("signal_failures").select("*").gte(
            "created_at", cutoff
        ).order("created_at", desc=True).limit(500).execute()

        failures = safe_get_data(result)

        # Parse JSON fields
        for f in failures:
            parse_json_fields(f, [
                "entry_indicators", "failure_indicators", "price_action_context",
                "correlation_context", "contradiction_flags",
            ])

        return failures

    except Exception as e:
        logger.error(f"Export failures error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════════════════
#  Scheduler integration
# ═════════════════════════════════════════════════════════════════════════════

async def _check_daily_bias_invalidation() -> None:
    """Invalidate today's NASDAQ macro bias if intraday price broke its structure.

    Cheap: one price read + (only on breach) one UPDATE. No-op when the macro
    bias layer is off, no bias exists today, or it's already invalidated.
    """
    from services.daily_bias_service import (
        DEFAULT_BIAS_SYMBOL, get_current_bias, check_and_maybe_invalidate,
    )
    bias = get_current_bias(DEFAULT_BIAS_SYMBOL)
    if not bias or bias.get("is_invalidated"):
        return
    price = await fetch_latest_price(DEFAULT_BIAS_SYMBOL)
    if not price or price <= 0:
        return
    reason = check_and_maybe_invalidate(DEFAULT_BIAS_SYMBOL, float(price), bias=bias)
    if reason:
        logger.info(f"[daily-bias] NDX.INDX bias invalidated intraday: {reason}")


async def check_lifecycle_if_needed():
    """Called from background_scheduler every 60s; runs lifecycle every minute."""
    global _last_lifecycle_check, _last_cleanup_run

    now = _utc_now()
    if _last_lifecycle_check and (now - _last_lifecycle_check).total_seconds() < LIFECYCLE_CHECK_INTERVAL:
        return

    _last_lifecycle_check = now

    try:
        summary = await run_lifecycle_check()
        logger.info(f"Lifecycle summary: {summary.get('checked', 0)} checked")

        # Broadcast to WebSocket clients
        try:
            from services.ws_manager import manager
            await manager.broadcast_all({
                "lifecycle": {
                    "type": "lifecycle_update",
                    "summary": summary,
                }
            })
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Lifecycle check error: {e}")

    # Stage 3.2 — NASDAQ günlük bias'ının invalid_if koşulunu izle. Fiyat
    # main_support/main_resistance yapısını kırdıysa bias'ı geçersiz kıl; bu
    # andan sonra veto engine makro etkiyi nötr sayar. Fail-open, NASDAQ-only.
    try:
        await _check_daily_bias_invalidation()
    except Exception as e:
        logger.debug(f"Daily bias invalidation check skipped: {e}")

    if _last_cleanup_run is None or (now - _last_cleanup_run).total_seconds() >= CLEANUP_INTERVAL_SECONDS:
        try:
            await cleanup_old_signals()
            _last_cleanup_run = _utc_now()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
