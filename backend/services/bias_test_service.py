"""Core logic for the bias-accuracy measurement harness (shared).

Both the HTTP router (``routers.bias_test_router``) and the scheduled
auto-runner (``services.bias_auto_runner``) call these functions, so the
recording / grading / reporting rules live in exactly one place.

Writes to bias_test_log only — isolated from the live daily_bias / veto engine.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from services import daily_bias_service as bias_svc
from services import session_context_service as sc

logger = logging.getLogger(__name__)

NDX = "NDX.INDX"
_FLAT_PCT = 0.15


class BiasTestError(RuntimeError):
    """Recoverable harness error (bad payload, missing candle, db down)."""


def _client():
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return None
    return get_supabase_client()


def direction_from_pct(pct: Optional[float]) -> Optional[str]:
    if pct is None:
        return None
    if pct > _FLAT_PCT:
        return "positive"
    if pct < -_FLAT_PCT:
        return "negative"
    return "flat"


def predicted_matches_actual(predicted: str, actual: Optional[str]) -> Optional[bool]:
    if actual is None:
        return None
    predicted = (predicted or "").lower()
    if predicted == "bullish":
        return actual == "positive"
    if predicted == "bearish":
        return actual == "negative"
    if predicted in ("neutral", "choppy"):
        return actual == "flat"
    return None


async def record_run(payload: dict, run_label: str = "manual",
                     run_ts: Optional[datetime] = None) -> dict:
    """Normalise a bias payload, attach session context, insert a log row.

    Raises :class:`ValueError` on an unparseable payload, :class:`BiasTestError`
    if the DB is unavailable or the insert fails.
    """
    parsed = bias_svc.normalize_cio_payload(payload)   # may raise ValueError
    run_ts = run_ts or datetime.now(timezone.utc)
    if run_ts.tzinfo is None:
        run_ts = run_ts.replace(tzinfo=timezone.utc)

    ctx = await sc.enrich_price_context(run_ts)
    row = {
        "run_timestamp_utc": run_ts.isoformat(),
        "ny_time": ctx["ny_time"],
        "ny_date": ctx["ny_time"][:10],
        "run_label": run_label,
        "current_session": ctx["current_session"],
        "london_direction": ctx.get("london_session_direction"),
        "asia_overnight_change": ctx.get("asia_overnight_change"),
        "us_premarket_change": ctx.get("us_premarket_change"),
        "minutes_to_us_open": ctx["minutes_to_us_open"],
        "is_half_day": ctx["is_half_day"],
        "is_holiday": ctx["is_holiday"],
        "session_overlap": ctx["session_overlap"],
        "predicted_bias": parsed["nasdaq_daily_bias"],
        "confidence": parsed["confidence"],
        "trade_mode": parsed.get("trade_mode"),
        "main_support": parsed.get("main_support"),
        "main_resistance": parsed.get("main_resistance"),
        "invalid_if": parsed.get("invalid_if"),
        "reason_summary": parsed.get("reason_summary"),
        "raw_payload": parsed.get("raw_payload"),
    }
    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    res = client.table("bias_test_log").insert(row)
    if res.get("error"):
        raise BiasTestError(str(res["error"]))

    # CORTEX episodic memory (fail-open — never breaks bias logging).
    try:
        from config import settings
        if settings.cortex_enabled:
            from services import cortex_memory as cortex
            situation = payload.get("_cortex_situation") if isinstance(payload, dict) else None
            if situation is None:
                situation = await cortex.build_situation(run_ts)
            cortex.record_episode(
                situation, predicted_bias=parsed["nasdaq_daily_bias"],
                confidence=parsed["confidence"], run_label=run_label,
                source="bias_run", now_utc=run_ts)
    except Exception as e:
        logger.debug("[bias-test] CORTEX episode skipped: %s", e)

    return {"ok": True, "run_label": run_label,
            "current_session": ctx["current_session"],
            "ny_date": row["ny_date"],
            "predicted_bias": parsed["nasdaq_daily_bias"]}


def already_logged(ny_date: str, run_label: str) -> bool:
    """Has a row already been recorded for this (date, label)? (idempotency)."""
    client = _client()
    if client is None:
        return False
    rows = (client.table("bias_test_log").select("id")
            .eq("ny_date", ny_date).eq("run_label", run_label)
            .limit(1).execute()).get("data") or []
    return bool(rows)


async def _ndx_day_stats(ny_date: str) -> Optional[dict]:
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(NDX, "1d", limit=60)
    except Exception:
        return None
    for c in candles or []:
        ts = str(c.get("timestamp") or c.get("time") or c.get("date") or "")
        if ts.startswith(ny_date):
            o = c.get("open") or c.get("o")
            cl = c.get("close") or c.get("c")
            if o and cl:
                return {"open": float(o), "close": float(cl),
                        "high": float(c.get("high") or c.get("h") or cl),
                        "low": float(c.get("low") or c.get("l") or cl)}
    return None


async def fill_outcomes(ny_date: Optional[str] = None) -> dict:
    if not ny_date:
        ny_date = datetime.now(sc.NY).date().isoformat()
    stats = await _ndx_day_stats(ny_date)
    if not stats:
        raise BiasTestError(f"no NDX daily candle for {ny_date}")

    change_pct = round((stats["close"] - stats["open"]) / stats["open"] * 100.0, 3)
    actual_dir = direction_from_pct(change_pct)

    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log").select("*")
            .eq("ny_date", ny_date).execute()).get("data") or []

    updated = 0
    for r in rows:
        predicted = r.get("predicted_bias")
        correct = predicted_matches_actual(predicted, actual_dir)
        triggered = None
        sup, resist = r.get("main_support"), r.get("main_resistance")
        if predicted == "bullish" and sup:
            triggered = stats["low"] < float(sup)
        elif predicted == "bearish" and resist:
            triggered = stats["high"] > float(resist)
        (client.table("bias_test_log").eq("id", r["id"]).update({
            "actual_close_direction": actual_dir,
            "actual_change_pct": change_pct,
            "was_correct": correct,
            "invalid_if_triggered": triggered,
            "outcome_filled_at": datetime.now(timezone.utc).isoformat(),
        }))
        updated += 1

    # CORTEX — grade the same day's episodes (fail-open).
    cortex_filled = 0
    try:
        from config import settings
        if settings.cortex_enabled:
            from services import cortex_memory as cortex
            cortex_filled = cortex.fill_outcomes(ny_date, actual_dir, change_pct)
    except Exception as e:
        logger.debug("[bias-test] CORTEX fill skipped: %s", e)

    return {"ok": True, "ny_date": ny_date, "actual_change_pct": change_pct,
            "actual_close_direction": actual_dir, "rows_updated": updated,
            "cortex_episodes_filled": cortex_filled}


def _conf_bucket(c: float) -> str:
    if c < 60:
        return "low(<60)"
    if c < 75:
        return "med(60-75)"
    return "high(>75)"


def _rate(rows: list[dict]) -> dict[str, Any]:
    graded = [r for r in rows if r.get("was_correct") is not None]
    correct = sum(1 for r in graded if r["was_correct"])
    n = len(graded)
    return {"n": n, "correct": correct,
            "accuracy_pct": round(correct / n * 100.0, 1) if n else None}


def accuracy_report() -> dict:
    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log").select("*")
            .order("ny_time", desc=True).limit(2000).execute()).get("data") or []
    graded = [r for r in rows if r.get("was_correct") is not None]

    def group(key_fn):
        out: dict[str, list] = {}
        for r in graded:
            out.setdefault(str(key_fn(r)), []).append(r)
        return {k: _rate(v) for k, v in sorted(out.items())}

    return {
        "total_graded": len(graded),
        "overall": _rate(graded),
        "by_run_label": group(lambda r: r.get("run_label")),
        "by_confidence_bucket": group(lambda r: _conf_bucket(float(r.get("confidence") or 0))),
        "by_session_overlap": group(lambda r: r.get("session_overlap")),
        "by_half_day": group(lambda r: r.get("is_half_day")),
        "by_holiday": group(lambda r: r.get("is_holiday")),
        "by_current_session": group(lambda r: r.get("current_session")),
        "go_live_hint": (
            "≥65% good, ≥55% minimum to consider wiring live; below → refine prompts"
        ),
    }
