"""
Signal Lifecycle Manager
─────────────────────────
Tracks active signals every minute, captures wicks (session high/low),
detects target hits and stop losses, performs failure autopsy, and manages
timeframe-aware signal expiration/cleanup.

Tables used:
  - prediction_logs  (read active, update status/targets_hit/exit)
  - signal_checks    (insert per-check snapshots)
  - signal_failures  (insert failure autopsy on stop)
"""
from __future__ import annotations

import asyncio
import logging
import json
import time
import traceback
from datetime import datetime, timedelta
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
    classify_signal,
    normalize_model_type,
    normalize_timeframe as normalize_analytics_timeframe,
    parse_targets_hit,
)
from utils.json_helpers import parse_json_field, parse_json_fields

logger = logging.getLogger(__name__)


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
        self.last_check_time = datetime.utcnow().isoformat() + "Z"
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

KNOWN_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
TIMEFRAME_EVALUATION_WINDOWS = {
    "1m": 2,
    "5m": 10,
    "15m": SIGNAL_MAX_AGE_MINUTES,
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


def _is_price_stale(symbol: str, current_price: float) -> bool:
    """
    Check if price is stale (hasn't changed in a long time).
    This detects when market is closed or EODHD is returning old data.
    """
    global _price_last_seen, _price_last_seen_time
    
    now = datetime.utcnow()
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
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


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
    return 0.2 <= ratio <= 5.0


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

    now_utc = datetime.utcnow()
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


def _update_signal_status(client, signal_id: str, status: str, exit_price=None):
    """Helper to update a signal's status in prediction_logs."""
    update_data = {"status": status, "exit_time": datetime.utcnow().isoformat() + "Z"}
    if exit_price is not None:
        update_data["exit_price"] = round(float(exit_price), 4)
    try:
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data).execute()
        if result and safe_get_data(result):
            logger.info(f"✅ Signal {signal_id[:8]} status updated to {status}")
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
      1. Get session high/low (wick capture)
      2. Calculate profit pips
      3. Check target hits
      4. Check stop loss
      5. Insert signal_check record
      6. Update prediction_logs
      7. If stopped → create failure autopsy

    Returns: new status if changed, None otherwise
    """
    signal_id = signal["id"]
    symbol = signal["symbol"]
    direction = (signal.get("ml_direction") or "HOLD").upper().strip()
    entry_price = _coerce_float(signal.get("ml_entry_price"))
    timeframe = _normalize_timeframe(signal.get("timeframe"))
    evaluation_window = _evaluation_window_minutes(timeframe)

    # Parse JSON string fields from DB (safe normalization)
    parse_json_fields(signal, ["targets", "targets_hit", "factors"])

    if entry_price is None or direction not in {"BUY", "SELL"}:
        # Can't track HOLD signals; mark expired
        _update_signal_status(client, signal_id, "expired", entry_price)
        return "expired"

    created_dt = _parse_created_at(signal.get("created_at"))

    # ── 1. Get current spot price (DataHub-backed canonical source) ──
    current = None
    try:
        price_val = await fetch_latest_price(symbol)
        if price_val:
            current = float(price_val)
    except Exception as e:
        logger.warning(f"lifecycle.price_error | symbol={symbol} error={e}")

    if current is None or current <= 0:
        try:
            if created_dt is not None:
                age_minutes = (datetime.now(created_dt.tzinfo) - created_dt).total_seconds() / 60
                if age_minutes >= evaluation_window:
                    _update_signal_status(client, signal_id, "expired", entry_price)
                    logger.info(
                        f"⏰ Signal {signal_id[:8]} {symbol} expired without price update "
                        f"(age={age_minutes:.0f}m)"
                    )
                    return "expired"
        except Exception:
            pass

        logger.warning(f"No price for {symbol}, skipping signal {signal_id[:8]}")
        return None

    # ── 1b. Check if price is stale (market closed or EODHD returning old data)
    is_stale = _is_price_stale(symbol, current)
    if is_stale:
        # Price hasn't changed in >1 minute - market likely closed
        # PAUSE signal lifetime - set very long timeout (24 hours)
        effective_max_age = 1440  # 24 hours - effectively paused until market opens
        logger.info(
            f"lifecycle.price_stale | signal={signal_id[:8]} symbol={symbol} "
            f"price={current:.2f} unchanged for 1min+ - PAUSING lifetime (24h max)"
        )
    else:
        effective_max_age = evaluation_window

    # ── 2. Calculate profit/loss in pips using spot price ──
    if direction == "BUY":
        profit_pips = pips_from_price_change(current - entry_price, symbol)
    else:  # SELL
        profit_pips = pips_from_price_change(entry_price - current, symbol)
    best_pips = max(profit_pips, 0)
    worst_pips = min(profit_pips, 0)

    # Use last 5m candle high/low for wick capture (better than spot-only check)
    # This catches targets hit intra-candle that spot price misses at 3-min intervals
    session_high = current
    session_low = current
    try:
        from services.data_hub import get_candles
        recent_candles = get_candles(symbol, "5m", limit=2)  # last 2 candles
        if recent_candles:
            # Filter out candles that occurred before the signal was created
            created_at_str = signal.get("created_at")
            if created_at_str:
                created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                # Allow a 5-minute buffer so we don't accidentally ignore the entry candle completely
                cutoff_ts = (created_dt - timedelta(minutes=5)).timestamp() * 1000
                valid_candles = []
                for c in recent_candles:
                    c_ts = c.get("timestamp")
                    if not c_ts and "date" in c:
                        try:
                            c_dt = datetime.fromisoformat(str(c["date"]).replace("Z", "+00:00"))
                            c_ts = c_dt.timestamp() * 1000
                        except Exception:
                            pass
                    
                    if c_ts and c_ts >= cutoff_ts:
                        valid_candles.append(c)
                
                if valid_candles:
                    session_high = max(c.get("high", current) for c in valid_candles)
                    session_low = min(c.get("low", current) for c in valid_candles)
            else:
                session_high = max(c.get("high", current) for c in recent_candles)
                session_low = min(c.get("low", current) for c in recent_candles)
    except Exception as e:
        logger.warning(f"Failed to use candle wicks for {symbol}, falling back to spot: {e}")
        pass  # Fallback to spot price if candle data unavailable


    # ── 3. Update cumulative high/low ──
    prev_high = _coerce_float(signal.get("highest_profit_pips"), 0.0) or 0.0
    prev_low = _coerce_float(signal.get("lowest_drawdown_pips"), 0.0) or 0.0
    new_high = max(prev_high, best_pips)
    new_low = min(prev_low, worst_pips)

    # ── 4. Check targets ──
    target_prices = _resolve_target_prices(signal, entry_price, direction, symbol, timeframe)
    targets_hit = signal.get("targets_hit") or {}
    if not isinstance(targets_hit, dict):
        targets_hit = {}

    for tp_name, tp_price in target_prices.items():
        if targets_hit.get(tp_name):
            continue  # Already hit
        if direction == "BUY" and session_high and session_high >= tp_price:
            targets_hit[tp_name] = True
            logger.info(f"✅ Signal {signal_id[:8]} {symbol} {direction}: {tp_name} HIT @ high={session_high:.2f} (target={tp_price:.2f})")
        elif direction == "SELL" and session_low and session_low <= tp_price:
            targets_hit[tp_name] = True
            logger.info(f"✅ Signal {signal_id[:8]} {symbol} {direction}: {tp_name} HIT @ low={session_low:.2f} (target={tp_price:.2f})")

    # ── 5. Check stop loss ──
    sl_price = calculate_stoploss_price(entry_price, direction, symbol, timeframe)
    resolved_sl_pips = abs(pips_from_price_change(abs(entry_price - sl_price), symbol))
    hit_stop = False

    if direction == "BUY" and session_low and session_low <= sl_price:
        hit_stop = True
    elif direction == "SELL" and session_high and session_high >= sl_price:
        hit_stop = True

    # ── 6. Build target_status for this check ──
    target_status = {}
    for tp_name in target_prices:
        target_status[tp_name] = bool(targets_hit.get(tp_name))

    # ── 7. Insert signal_check record ──
    check_record = {
        "signal_id": signal_id,
        "check_time": datetime.utcnow().isoformat() + "Z",
        "current_price": round(current, 4),
        "session_high": round(session_high, 4) if session_high else None,
        "session_low": round(session_low, 4) if session_low else None,
        "profit_pips": round(profit_pips, 2),
        "cumulative_high_pips": round(new_high, 2),
        "cumulative_low_pips": round(new_low, 2),
        "target_status": json.dumps(target_status),
    }
    try:
        client.table("signal_checks").insert(check_record).execute()
    except Exception as e:
        logger.error(f"Failed to insert signal_check for {signal_id[:8]}: {e}")
        # Continue to status determination even if check record insert fails

    # ── 8. Determine new status ──
    new_status = None
    exit_price = None
    any_target_hit = any(targets_hit.values()) if targets_hit else False

    if all(target_status.get(tp) for tp in target_prices):
        # All targets hit → completed
        new_status = "completed"
        exit_price = current
        logger.info(f"🎯 Signal {signal_id[:8]} {symbol} {direction} ALL TARGETS HIT!")
    elif hit_stop and any_target_hit:
        # CRITICAL: If ANY target was hit before stop → signal is SUCCESSFUL
        new_status = "completed"
        exit_price = current
        logger.info(f"✅ Signal {signal_id[:8]} {symbol} {direction} TP hit then SL → completed (TP takes priority)")
    elif hit_stop:
        # Pure stop loss, no target ever hit → stopped
        new_status = "stopped"
        exit_price = sl_price
        logger.info(f"🛑 Signal {signal_id[:8]} {symbol} {direction} STOPPED @ {sl_price:.2f}")
    else:
        # Check age for expiration (respect effective_max_age for stale prices)
        if created_dt is not None:
            try:
                age_minutes = (datetime.now(created_dt.tzinfo) - created_dt).total_seconds() / 60
                
                max_age_for_symbol = effective_max_age
                
                if age_minutes >= max_age_for_symbol:
                    new_status = "completed" if any_target_hit else "expired"
                    exit_price = current
                    logger.info(f"⏰ Signal {signal_id[:8]} {symbol} aged out ({age_minutes:.0f}m, max={max_age_for_symbol}m) → {new_status} (any_tp={any_target_hit}, stale={is_stale})")
            except Exception as exp_err:
                logger.warning(f"Failed to check signal age for {signal_id[:8]}: {exp_err}")

    # ── 9. Update prediction_logs ──
    update_data: Dict[str, Any] = {
        "highest_profit_pips": round(new_high, 2),
        "lowest_drawdown_pips": round(new_low, 2),
        "targets_hit": json.dumps(targets_hit),
        "targets": json.dumps(target_prices),
        "stop_loss_pips": round(resolved_sl_pips, 2),
    }
    if new_status:
        update_data["status"] = new_status
        update_data["exit_price"] = round(exit_price, 4) if exit_price else None
        update_data["exit_time"] = datetime.utcnow().isoformat() + "Z"

    try:
        result = client.table("prediction_logs").eq("id", signal_id).update(update_data).execute()
        if result and safe_get_data(result) and new_status:
            logger.info(f"✅ Signal {signal_id[:8]} updated: status={new_status}, high={new_high:.1f}p, low={new_low:.1f}p")
    except Exception as e:
        logger.error(f"Failed to update signal {signal_id[:8]}: {e}")

    # ── 10. Failure autopsy on stop ──
    if new_status == "stopped":
        await _create_failure_autopsy(client, signal, targets_hit, current)

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

        client.table("signal_failures").insert(failure_record).execute()
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
        "timestamp": datetime.utcnow().isoformat() + "Z",
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

    # Record job state for scheduler resilience
    _record_job_state(client, "lifecycle_check", summary)

    return summary


def _record_job_state(client, job_name: str, summary: Dict[str, Any]):
    """Persist job run metadata to scheduler_state table for observability & catch-up."""
    if not client:
        return
    try:
        client.table("scheduler_state").eq("job_name", job_name).update({
            "last_run_at": datetime.utcnow().isoformat() + "Z",
            "last_duration_ms": summary.get("duration_ms", 0),
            "last_status": "error" if safe_get_error(summary) else "ok",
            "last_error": safe_get_error(summary),
            "run_count": 1,  # Will use raw SQL increment later if needed
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as e:
        logger.debug(f"_record_job_state({job_name}): {e}")


# ═════════════════════════════════════════════════════════════════════════════
#  Cleanup: archive old signals, cap active count
# ═════════════════════════════════════════════════════════════════════════════

async def cleanup_old_signals():
    """
    1. Force-expire active signals that exceed timeframe-aware cleanup grace
    2. Keep signal_checks retention bounded
    """
    if not is_db_available():
        return

    client = get_supabase_client()
    if not client:
        return

    try:
        result = client.table("prediction_logs").select("id, created_at, symbol, timeframe").eq(
            "status", "active"
        ).order("created_at", desc=False).limit(200).execute()

        stale = safe_get_data(result) or []
        expired_count = 0
        for s in stale:
            try:
                created_dt = _parse_created_at(s.get("created_at"))
                if created_dt is None:
                    continue
                age_minutes = (datetime.now(created_dt.tzinfo) - created_dt).total_seconds() / 60
                if age_minutes < _cleanup_grace_minutes(s.get("timeframe")):
                    continue
                upd_result = client.table("prediction_logs").eq("id", s["id"]).update({
                    "status": "expired",
                    "exit_time": datetime.utcnow().isoformat() + "Z",
                    "exit_price": None,
                }).execute()
                if upd_result and safe_get_data(upd_result):
                    expired_count += 1
            except Exception as upd_err:
                logger.warning(f"Failed to expire signal {s['id'][:8]}: {upd_err}")

        if expired_count:
            logger.info(f"🧹 Force-expired {expired_count} stale signals beyond cleanup grace")

        # Delete signal_checks older than 30 days
        archive_cutoff = (datetime.utcnow() - timedelta(days=ARCHIVE_AFTER_DAYS)).isoformat() + "Z"
        client.table("signal_checks").select("id").lt(
            "created_at", archive_cutoff
        ).limit(500).execute()
        # Note: actual deletion would need a delete call; for now just log
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

    try:
        tf_order = ["5m", "15m", "30m", "1h", "4h", "1d"]

        # Supabase PostgREST caps at 1000 rows per request.
        # Fetch day-by-day to stay under 1000 rows per request.
        signals = []

        # Determine date range
        if days > 0:
            start_date = datetime.utcnow() - timedelta(days=days)
        else:
            # All time: start from 90 days ago (covers all historical data)
            start_date = datetime.utcnow() - timedelta(days=90)

        end_date = datetime.utcnow()
        current = start_date

        while current < end_date:
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = (day_start + timedelta(days=1))
            
            day_start_iso = day_start.isoformat() + "Z"
            day_end_iso = day_end.isoformat() + "Z"

            result = client.table("prediction_logs").select(
                "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
                "model_type, status, targets_hit, highest_profit_pips, "
                "lowest_drawdown_pips, exit_price, exit_time, stop_loss_pips, "
                "targets, created_at, strategy"
            ).neq("status", "active").gte(
                "created_at", day_start_iso
            ).lt(
                "created_at", day_end_iso
            ).limit(1000).execute()

            batch = safe_get_data(result)
            if batch:
                signals.extend(batch)
            
            current = day_end

        # Also fetch today's partial data
        today_start = end_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        result = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
            "model_type, status, targets_hit, highest_profit_pips, "
            "lowest_drawdown_pips, exit_price, exit_time, stop_loss_pips, "
            "targets, created_at, strategy"
        ).neq("status", "active").gte("created_at", today_start).limit(1000).execute()
        today_batch = safe_get_data(result)
        if today_batch:
            # Deduplicate with existing signals by id
            existing_ids = {s.get("id") for s in signals}
            for s in today_batch:
                if s.get("id") not in existing_ids:
                    signals.append(s)

        logger.info(f"Dashboard: fetched {len(signals)} total signals via day-by-day pagination")

        # Per-model stats
        models = {}
        for sig in signals:
            mt = normalize_model_type(sig)
            if mt not in models:
                models[mt] = {
                    "total": 0, "completed": 0, "stopped": 0, "expired": 0,
                    "total_profit_pips": 0, "total_loss_pips": 0,
                    "profits": [], "losses": [],
                    "target_hits": {},  # TP1: count, TP2: count, etc.
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

            th = parse_targets_hit(sig.get("targets_hit"))
            if th:
                for tp_name, hit in th.items():
                    # Global
                    if tp_name not in m["target_hits"]:
                        m["target_hits"][tp_name] = {"total": 0, "hit": 0}
                    m["target_hits"][tp_name]["total"] += 1
                    if hit:
                        m["target_hits"][tp_name]["hit"] += 1
                    # Per-symbol
                    if tp_name not in m["symbols"][sym]["target_hits"]:
                        m["symbols"][sym]["target_hits"][tp_name] = {"total": 0, "hit": 0}
                    m["symbols"][sym]["target_hits"][tp_name]["total"] += 1
                    if hit:
                        m["symbols"][sym]["target_hits"][tp_name]["hit"] += 1

        # Ensure all known model types exist in response (even with 0 signals)
        KNOWN_MODELS = ["ml", "pulse1", "pulse2", "pulse3", "emel", "emel_inverse", "hybrid"]
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
            total = m["total"] or 1
            # Exclude expired from win_rate calculation (only completed + stopped count)
            total_with_outcome = m["completed"] + m["stopped"]
            if total_with_outcome == 0:
                total_with_outcome = 1  # Prevent div by zero
            
            avg_profit = sum(m["profits"]) / len(m["profits"]) if m["profits"] else 0
            avg_loss = sum(m["losses"]) / len(m["losses"]) if m["losses"] else 0

            target_rates = {}
            for tp_name, counts in m["target_hits"].items():
                t = counts["total"] or 1
                target_rates[tp_name] = round(counts["hit"] / t * 100, 1)

            # Build per-symbol stats with target rates
            symbols_out = {}
            for sym, sd in m["symbols"].items():
                sym_target_rates = {}
                for tp_name, counts in sd.get("target_hits", {}).items():
                    t = counts["total"] or 1
                    sym_target_rates[tp_name] = round(counts["hit"] / t * 100, 1)
                sym_total_with_outcome = sd.get("completed", 0) + sd.get("stopped", 0)
                if sym_total_with_outcome == 0:
                    sym_total_with_outcome = 1
                symbols_out[sym] = {
                    "total": sd["total"],
                    "completed": sd.get("completed", 0),
                    "stopped": sd.get("stopped", 0),
                    "expired": sd.get("expired", 0),
                    "win_rate": round(sd.get("completed", 0) / sym_total_with_outcome * 100, 1),
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
                "win_rate": round(m["completed"] / total_with_outcome * 100, 1),
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
            fail_cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
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

        return {
            "period_days": days,
            "model_stats": model_stats,
            "failure_breakdown": failure_breakdown,
            "total_failures": len(failures),
            "active_signals": active_count,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

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

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

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

async def check_lifecycle_if_needed():
    """Called from background_scheduler every 60s; runs lifecycle every minute."""
    global _last_lifecycle_check, _last_cleanup_run

    now = datetime.utcnow()
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

    if _last_cleanup_run is None or (now - _last_cleanup_run).total_seconds() >= CLEANUP_INTERVAL_SECONDS:
        try:
            await cleanup_old_signals()
            _last_cleanup_run = datetime.utcnow()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
