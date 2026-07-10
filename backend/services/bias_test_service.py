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

# Multi-symbol (2026-07-08): rows are attributed to a symbol via the payload's
# `symbol` field (set by the debate engine) or the run_label prefix. The DB
# table has no symbol column — run_label carries it, raw_payload records it.
LABEL_SYMBOLS = {"xau": "XAUUSD", "dax": "GDAXI.INDX", "usoil": "USOIL.FOREX",
                 "ndx": NDX}

# Per-symbol grading windows (DST-safe): (tz, start_min, end_min).
# start=None → whole day up to the cutoff. Grading = session open→close for
# NDX (unchanged legacy behaviour); decision-price→session close for others.
_SESSION_WINDOWS = {
    NDX: ("America/New_York", 9 * 60 + 30, 16 * 60),
    "GDAXI.INDX": ("Europe/Berlin", 9 * 60, 17 * 60 + 30),
    "XAUUSD": ("America/New_York", None, 17 * 60),
    "USOIL.FOREX": ("America/New_York", None, 14 * 60 + 30),   # NYMEX settle
}


def symbol_for_row(row: dict) -> str:
    """Resolve which instrument a bias_test_log row belongs to."""
    raw = row.get("raw_payload") or {}
    if isinstance(raw, dict) and raw.get("symbol") in _SESSION_WINDOWS:
        return raw["symbol"]
    label = (row.get("run_label") or "").lower()
    for prefix, sym in LABEL_SYMBOLS.items():
        if label.startswith(prefix):
            return sym
    return NDX   # legacy default — all pre-multi-symbol rows are NASDAQ


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
    # NASDAQ-only by design: other symbols' runs skip the episodic store.
    _sym = (payload.get("symbol") if isinstance(payload, dict) else None) or NDX
    try:
        from config import settings
        if settings.cortex_enabled and _sym == NDX:
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


def recent_track_record(limit: int = 25) -> str:
    """ÖZ-KALİBRASYON bloğu: sistemin SON tahminlerinin gerçekleşme karnesi (bias_test_log).
    Debate/CIO promptuna enjekte edilir — model kendi sistematik önyargısını GÖRÜR
    (2026-07-09 otopsisi: %30.8 doğruluk; boğa piyasasında art arda bearish çağrılar —
    model kendi karnesini görmediği için aynı hatayı tekrarlıyordu). Fail-open: DB yoksa ''."""
    try:
        client = _client()
        if client is None:
            return ""
        rows = (client.table("bias_test_log")
                .select("predicted_bias,was_correct,ny_date,run_label")
                .not_.is_("was_correct", "null")
                .order("ny_date", desc=True).limit(limit).execute()).get("data") or []
        if len(rows) < 5:
            return ""
        by: dict = {}
        for r in rows:
            b = (r.get("predicted_bias") or "?").lower()
            w, n = by.get(b, (0, 0))
            by[b] = (w + (1 if r.get("was_correct") else 0), n + 1)
        tot_w = sum(w for w, _ in by.values())
        tot_n = sum(n for _, n in by.values())
        parts = [f"{b}: {w}/{n}" for b, (w, n) in sorted(by.items(), key=lambda x: -x[1][1])]
        worst = min(by.items(), key=lambda x: (x[1][0] / max(x[1][1], 1), -x[1][1]))
        warn = ""
        if worst[1][1] >= 3 and worst[1][0] / worst[1][1] < 0.4:
            warn = (f" ⚠ '{worst[0]}' calls hit only {worst[1][0]}/{worst[1][1]} — you have a "
                    f"systematic bias in that direction; before calling '{worst[0]}' again, "
                    f"show that your evidence DIFFERS from those failed calls.")
        return (f"SELF-CALIBRATION (outcome record of your LAST {tot_n} predictions): "
                f"{tot_w}/{tot_n} correct overall; breakdown → " + " | ".join(parts) + "." + warn)
    except Exception as e:
        logger.debug("[bias-test] track record skipped: %s", e)
        return ""


def already_logged(ny_date: str, run_label: str) -> bool:
    """Has a row already been recorded for this (date, label)? (idempotency)."""
    client = _client()
    if client is None:
        return False
    rows = (client.table("bias_test_log").select("id")
            .eq("ny_date", ny_date).eq("run_label", run_label)
            .limit(1).execute()).get("data") or []
    return bool(rows)


def _synth_session_stats(symbol: str, ny_date: str) -> Optional[dict]:
    """Synthesize the instrument's session-day OHLC from 1h candle_cache rows.

    The MT5 bridge never streams 1d bars (candle_cache has zero 1d rows), which
    left outcome-filling permanently dead. This rebuilds each instrument's own
    session window (DST-correct via zoneinfo) from the 1h bars that DO exist:
    NDX 09:30-16:00 NY · DAX 09:00-17:30 Berlin · XAU day→17:00 NY ·
    USOIL day→14:30 NY settle."""
    from zoneinfo import ZoneInfo
    win = _SESSION_WINDOWS.get(symbol)
    client = _client()
    if win is None or client is None:
        return None
    tz_name, start_min, end_min = win
    client_tz = ZoneInfo(tz_name)
    try:
        rows = (client.table("candle_cache").select("candle_time,open,high,low,close")
                .eq("symbol", symbol).eq("timeframe", "1h")
                .gte("candle_time", f"{ny_date}T00:00:00+00:00")
                .lte("candle_time", f"{ny_date}T23:59:59+00:00")
                .order("candle_time").limit(60).execute()).get("data") or []
    except Exception as e:
        logger.warning("[bias-test] 1h synth read error (%s): %s", symbol, e)
        return None
    keep = []
    for r in rows:
        try:
            t = datetime.fromisoformat(str(r["candle_time"]).replace("Z", "+00:00"))
            local = t.astimezone(client_tz)
            minutes = local.hour * 60 + local.minute
            if (start_min is None or minutes >= start_min) and minutes < end_min:
                keep.append(r)
        except (ValueError, KeyError):
            continue
    if len(keep) < 3:
        return None
    try:
        return {"open": float(keep[0]["open"]), "close": float(keep[-1]["close"]),
                "high": max(float(r["high"]) for r in keep),
                "low": min(float(r["low"]) for r in keep)}
    except (TypeError, ValueError):
        return None


async def _day_stats(symbol: str, ny_date: str) -> Optional[dict]:
    """Session-day OHLC for `symbol` on `ny_date` (1d feed → 1h synthesis)."""
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, "1d", limit=60)
    except Exception:
        candles = []
    for c in candles or []:
        ts = str(c.get("timestamp") or c.get("time") or c.get("date") or "")
        if ts.startswith(ny_date):
            o = c.get("open") or c.get("o")
            cl = c.get("close") or c.get("c")
            if o and cl:
                return {"open": float(o), "close": float(cl),
                        "high": float(c.get("high") or c.get("h") or cl),
                        "low": float(c.get("low") or c.get("l") or cl)}
    # 1d feed dead → synthesize from 1h (the fix that unblocks learning)
    return _synth_session_stats(symbol, ny_date)


async def _ndx_day_stats(ny_date: str) -> Optional[dict]:
    return await _day_stats(NDX, ny_date)


def pending_dates(max_days: int = 10) -> list[str]:
    """NY dates (before today) that still have ungraded rows — catch-up queue."""
    client = _client()
    if client is None:
        return []
    today = datetime.now(sc.NY).date().isoformat()
    try:
        rows = (client.table("bias_test_log").select("ny_date,was_correct")
                .limit(500).execute()).get("data") or []
    except Exception:
        return []
    dates = sorted({str(r["ny_date"]) for r in rows
                    if r.get("ny_date") and r.get("was_correct") is None
                    and str(r["ny_date"]) < today})
    return dates[-max_days:]


async def fill_pending(max_days: int = 10) -> dict:
    """Grade every past day left ungraded (backend down at 16:15 ET, or the 1d
    feed was broken). Idempotent."""
    results = {}
    for d in pending_dates(max_days):
        try:
            r = await fill_outcomes(d)
            results[d] = f"{r['rows_updated']} rows → {r['actual_close_direction']}"
        except BiasTestError as e:
            results[d] = f"skipped: {e}"
    return results


async def fill_outcomes(ny_date: Optional[str] = None) -> dict:
    """Grade every row for `ny_date` against its OWN instrument's session.

    NDX rows keep the legacy metric (session open→close, so the whole
    measurement series stays comparable). Other symbols are graded
    decision-price→session-close — the honest question for a bias issued at
    the decision hour. Rows whose session data isn't available yet are left
    ungraded (picked up later by the catch-up filler)."""
    if not ny_date:
        ny_date = datetime.now(sc.NY).date().isoformat()

    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log").select("*")
            .eq("ny_date", ny_date).execute()).get("data") or []

    stats_cache: dict[str, Optional[dict]] = {}
    updated, skipped, ndx_change, ndx_dir = 0, 0, None, None
    for r in rows:
        sym = symbol_for_row(r)
        if sym not in stats_cache:
            stats_cache[sym] = await _day_stats(sym, ny_date)
        stats = stats_cache[sym]
        if not stats:
            skipped += 1
            continue

        # Grading anchor: NDX = session open (legacy); others = decision price.
        raw = r.get("raw_payload") or {}
        p0 = None
        if sym != NDX and isinstance(raw, dict):
            try:
                p0 = float(raw.get("price_at_decision")) if raw.get("price_at_decision") else None
            except (TypeError, ValueError):
                p0 = None
        anchor = p0 or stats["open"]
        change_pct = round((stats["close"] - anchor) / anchor * 100.0, 3)
        actual_dir = direction_from_pct(change_pct)
        if sym == NDX:
            ndx_change, ndx_dir = change_pct, actual_dir

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

    if updated == 0 and rows:
        raise BiasTestError(f"no NDX daily candle for {ny_date}")

    # CORTEX — grade the same day's NDX episodes (fail-open, NASDAQ-only).
    cortex_filled = 0
    try:
        from config import settings
        if settings.cortex_enabled and ndx_dir is not None:
            from services import cortex_memory as cortex
            cortex_filled = cortex.fill_outcomes(ny_date, ndx_dir, ndx_change)
    except Exception as e:
        logger.debug("[bias-test] CORTEX fill skipped: %s", e)

    return {"ok": True, "ny_date": ny_date, "actual_change_pct": ndx_change,
            "actual_close_direction": ndx_dir, "rows_updated": updated,
            "rows_skipped_no_data": skipped,
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
        "by_symbol": group(symbol_for_row),
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
