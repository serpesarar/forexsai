"""Daily macro bias (MiroShark → ForexSAI) — shared core.

One place for everything the MiroShark bridge and the Precision Veto Engine both
need, so the rules live in exactly one testable spot:

  * normalise a MiroShark CIO payload into a ``daily_bias`` row
  * UPSERT today's bias (webhook + manual fallback share this)
  * read today's bias (short in-memory cache — it changes at most once/day)
  * flip ``is_invalidated`` when intraday price breaches the bias structure
  * ``compute_alignment`` — the pure bonus/penalty/soft-veto rules

Scope guard: NASDAQ only (NDX.INDX). Every public helper returns a neutral,
no-effect result for any other symbol so DAX / XAUUSD / USOIL are never touched.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Optional

logger = logging.getLogger(__name__)

# NASDAQ is a NY-based instrument, so the "bias day" must be the NY trading date.
_NY = ZoneInfo("America/New_York")

# ── Scope ─────────────────────────────────────────────────────────────────────
# Only these symbols receive a macro-bias nudge. Kept as a set so aliases can be
# added later without touching call sites.
NASDAQ_BIAS_SYMBOLS: set[str] = {"NDX.INDX"}
DEFAULT_BIAS_SYMBOL = "NDX.INDX"

_VALID_BIASES = {"bullish", "bearish", "neutral", "choppy"}

# Read cache — the bias is a once-a-day snapshot, so a 60s TTL removes a Supabase
# round-trip from every single signal without ever masking a same-day update by
# more than a minute. Writes (upsert / invalidate) clear it immediately.
_CACHE_TTL_SECONDS = 60.0
_bias_cache: dict[str, tuple[float, Optional[dict]]] = {}


def is_nasdaq_symbol(symbol: str | None) -> bool:
    return (symbol or "") in NASDAQ_BIAS_SYMBOLS


def _today_ny() -> str:
    """Bias day key = the NY trading date. Using UTC here would misfile an
    evening-ET bias (20:00-24:00 ET already rolls to the next UTC day), so the
    veto engine could then fail to find that day's bias."""
    return datetime.now(_NY).date().isoformat()


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _clear_cache(symbol: str | None = None) -> None:
    if symbol is None:
        _bias_cache.clear()
    else:
        _bias_cache.pop(symbol, None)


# ── Payload normalisation ─────────────────────────────────────────────────────
def _first(payload: dict, *keys: str, default: Any = None) -> Any:
    """Return the first present, non-None value among *keys* (flat lookup)."""
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return default


def _to_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalize_cio_payload(payload: dict) -> dict:
    """Map a MiroShark CIO output onto ``daily_bias`` columns.

    Accepts either a flat dict or one nested under ``cio_final`` / ``result`` /
    ``data``. Unknown shapes still store the raw payload so nothing is lost and
    it can be re-parsed later. ``bias_date`` and ``symbol`` are added by the
    caller (upsert), not here.

    Raises ValueError if the mandatory bias direction is missing/invalid so the
    webhook can answer 400 instead of writing a junk row.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    # Unwrap a common envelope if present, but keep the ORIGINAL for raw_payload.
    core = payload
    for envelope in ("cio_final", "result", "data", "bias"):
        inner = payload.get(envelope)
        if isinstance(inner, dict):
            core = inner
            break

    bias = _first(core, "nasdaq_daily_bias", "daily_bias", "bias", "direction")
    bias = (str(bias).strip().lower() if bias is not None else "")
    if bias not in _VALID_BIASES:
        raise ValueError(
            f"invalid/missing daily bias (got {bias!r}); "
            f"expected one of {sorted(_VALID_BIASES)}"
        )

    confidence = _to_float(_first(core, "confidence", "conviction", "score"))
    if confidence is None:
        confidence = 0.0
    confidence = max(0.0, min(100.0, confidence))

    risk_flags = _first(core, "risk_flags", "risks")
    if isinstance(risk_flags, (str, int, float)):
        risk_flags = [risk_flags]

    return {
        "nasdaq_daily_bias": bias,
        "confidence": confidence,
        "expected_close": _first(core, "expected_close", "close_expectation"),
        "trade_mode": _first(core, "trade_mode", "mode"),
        "risk_level": _first(core, "risk_level", "risk"),
        "main_support": _to_float(_first(core, "main_support", "support")),
        "main_resistance": _to_float(_first(core, "main_resistance", "resistance")),
        "invalid_if": _first(core, "invalid_if", "invalidation", "invalidate_if"),
        "reason_summary": _first(core, "reason_summary", "reason", "summary", "rationale"),
        "agent_agreement": _first(core, "agent_agreement", "agreement"),
        "risk_flags": risk_flags,
        "debate_winner": _first(core, "debate_winner", "winner"),
        "raw_payload": payload,
    }


# ── Persistence ───────────────────────────────────────────────────────────────
def _client():
    """Return a Supabase client or None (DB optional — everything fails open)."""
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return None
        return get_supabase_client()
    except Exception as e:  # pragma: no cover - import/config guard
        logger.warning("[daily-bias] supabase unavailable: %s", e)
        return None


def upsert_bias(
    payload: dict,
    symbol: str = DEFAULT_BIAS_SYMBOL,
    bias_date: str | None = None,
) -> dict:
    """Normalise + UPSERT today's bias on (bias_date, symbol).

    Returns ``{"ok": bool, "row": dict|None, "error": str|None}``. Raises
    ValueError only for an unparseable payload (caller → HTTP 400).
    """
    row = normalize_cio_payload(payload)          # may raise ValueError
    row["symbol"] = symbol
    row["bias_date"] = bias_date or _today_ny()
    # A freshly (re)posted bias is valid again for the day.
    row["is_invalidated"] = False
    row["invalidated_at"] = None

    client = _client()
    if client is None:
        return {"ok": False, "row": row, "error": "db_unavailable"}

    res = client.table("daily_bias").upsert(row, on_conflict="bias_date,symbol")
    _clear_cache(symbol)
    if res.get("error"):
        logger.warning("[daily-bias] upsert error: %s", res["error"])
        return {"ok": False, "row": row, "error": str(res["error"])}
    data = res.get("data")
    return {"ok": True, "row": (data[0] if isinstance(data, list) and data else row),
            "error": None}


def get_current_bias(
    symbol: str = DEFAULT_BIAS_SYMBOL,
    use_cache: bool = True,
) -> Optional[dict]:
    """Today's bias row for *symbol*, or None if none exists / DB down."""
    if use_cache:
        cached = _bias_cache.get(symbol)
        if cached and (_now_ts() - cached[0]) < _CACHE_TTL_SECONDS:
            return cached[1]

    client = _client()
    if client is None:
        return None
    try:
        res = (client.table("daily_bias")
               .select("*")
               .eq("symbol", symbol)
               .eq("bias_date", _today_ny())
               .order("created_at", desc=True)
               .limit(1)
               .execute())
    except Exception as e:  # pragma: no cover - transient DB error
        logger.warning("[daily-bias] read error %s: %s", symbol, e)
        return None

    data = res.get("data") if isinstance(res, dict) else None
    bias = data[0] if isinstance(data, list) and data else None
    _bias_cache[symbol] = (_now_ts(), bias)
    return bias


def invalidate_bias(symbol: str, reason: str | None = None) -> bool:
    """Mark today's bias invalidated (intraday structure broke). Idempotent."""
    client = _client()
    if client is None:
        return False
    try:
        res = (client.table("daily_bias")
               .eq("symbol", symbol)
               .eq("bias_date", _today_ny())
               .update({"is_invalidated": True,
                        "invalidated_at": datetime.now(timezone.utc).isoformat()}))
        _clear_cache(symbol)
        if res.get("error"):
            logger.warning("[daily-bias] invalidate error: %s", res["error"])
            return False
        logger.info("[daily-bias] %s bias invalidated (%s)", symbol, reason or "n/a")
        return True
    except Exception as e:  # pragma: no cover
        logger.warning("[daily-bias] invalidate exception %s: %s", symbol, e)
        return False


# Invalidation needs a *decisive* breach, not a one-tick wick that instantly
# recovers. Require price to clear the level by this fraction before killing the
# bias. (A candle-close rule would be even stricter; the buffer is the cheap,
# robust first cut — the lifecycle feeds the latest price here, and a real
# breakdown will hold beyond the buffer where a stop-hunt wick won't.)
_INVALIDATION_BUFFER = 0.0015   # 0.15%


def check_and_maybe_invalidate(symbol: str, price: float,
                               bias: Optional[dict] = None) -> Optional[str]:
    """Stage 3.2 — flip the bias if intraday price *decisively* breaks its
    structure. A bullish bias dies when price is a buffer below ``main_support``;
    a bearish bias when a buffer above ``main_resistance``. Returns the reason if
    it fired, else None. NASDAQ-only and a no-op once already invalidated.
    """
    if not is_nasdaq_symbol(symbol) or not price or price <= 0:
        return None
    bias = bias if bias is not None else get_current_bias(symbol)
    if not bias or bias.get("is_invalidated"):
        return None

    direction = str(bias.get("nasdaq_daily_bias") or "").lower()
    support = _to_float(bias.get("main_support"))
    resistance = _to_float(bias.get("main_resistance"))

    reason: Optional[str] = None
    if direction == "bullish" and support and price < support * (1 - _INVALIDATION_BUFFER):
        reason = f"price {price} decisively < main_support {support}"
    elif direction == "bearish" and resistance and price > resistance * (1 + _INVALIDATION_BUFFER):
        reason = f"price {price} decisively > main_resistance {resistance}"

    if reason and invalidate_bias(symbol, reason):
        return reason
    return None


# ── Alignment rules (pure — no DB, unit-testable) ─────────────────────────────
# Tunables kept as module constants (no magic numbers in the branches).
_BONUS_CAP = 15.0
_BONUS_COEF = 0.20
_PENALTY_CAP = 20.0
_PENALTY_COEF = 0.25
_SOFT_VETO_CONF = 75.0
_CHOPPY_PENALTY = 10.0
_CHOPPY_WAIT_PENALTY = 20.0


def _neutral(state: str, reason: str = "") -> dict:
    return {"adjustment": 0.0, "state": state, "soft_veto": False,
            "reason": reason, "aligned": None, "confidence": 0.0,
            "trade_mode": None}


def compute_alignment(direction: str, bias: Optional[dict]) -> dict:
    """Pure macro-bias → confidence effect. No I/O.

    Returns a dict:
      adjustment  signed float — positive = confidence bonus, negative = penalty
      state       bullish|bearish|neutral|choppy|no_bias|invalidated
      soft_veto   True when a high-conviction opposing bias should force HOLD
      aligned     True/False/None — does the signal agree with the bias
    """
    if bias is None:
        return _neutral("no_bias")
    if bias.get("is_invalidated"):
        return _neutral("invalidated")

    state = str(bias.get("nasdaq_daily_bias") or "").lower()
    conf = _to_float(bias.get("confidence")) or 0.0
    trade_mode = bias.get("trade_mode")
    d = (direction or "").upper()

    if state == "neutral":
        return {**_neutral("neutral"), "confidence": conf, "trade_mode": trade_mode}

    if state == "choppy":
        pen = (_CHOPPY_WAIT_PENALTY if str(trade_mode) == "wait_and_see"
               else _CHOPPY_PENALTY)
        return {"adjustment": -pen, "state": "choppy", "soft_veto": False,
                "reason": "choppy_day", "aligned": None,
                "confidence": conf, "trade_mode": trade_mode}

    if state not in ("bullish", "bearish"):
        return _neutral("no_bias", f"unknown_bias:{state}")

    favored = "BUY" if state == "bullish" else "SELL"
    if d not in ("BUY", "SELL"):
        return {**_neutral(state), "confidence": conf, "trade_mode": trade_mode}

    if d == favored:
        bonus = min(_BONUS_CAP, conf * _BONUS_COEF)
        return {"adjustment": round(bonus, 2), "state": state, "soft_veto": False,
                "reason": f"aligned_with_{state}", "aligned": True,
                "confidence": conf, "trade_mode": trade_mode}

    # Opposing the bias
    penalty = min(_PENALTY_CAP, conf * _PENALTY_COEF)
    soft = conf > _SOFT_VETO_CONF
    return {"adjustment": -round(penalty, 2), "state": state, "soft_veto": soft,
            "reason": "macro_bias_opposition", "aligned": False,
            "confidence": conf, "trade_mode": trade_mode}


def check_macro_bias_alignment(signal_direction: str, symbol: str) -> dict:
    """Entry point used by the Precision Veto Engine.

    NASDAQ-only; every other symbol returns a neutral no-op. Fetches today's
    bias (cached) and applies :func:`compute_alignment`.
    """
    if not is_nasdaq_symbol(symbol):
        return _neutral("not_nasdaq")
    bias = get_current_bias(symbol)
    return compute_alignment(signal_direction, bias)
