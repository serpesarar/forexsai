"""CORTEX Phase 1 — episodic memory + analog retrieval (the hippocampus).

Captures a NASDAQ "situation" at decision time, stores it with the decision, and
(after close) the outcome. Before a debate, retrieves the K most-similar graded
past days and computes a real, shrinkage-adjusted base rate to feed the CIO —
"in the days most like today, NDX closed up 6/8 times". Zero LLM cost (SQL/kNN).

Design notes:
  * Every situation field is optional; distance only weighs fields present on
    BOTH the query and the candidate. History is partial by nature.
  * vix_regime is the heaviest weight — it is the project's one *validated*
    macro→NDX edge (2026-06-27: VIX regime predicts NDX direction +25pp,
    placebo p=0, OOS +17). See [[macro-ndx-vix-direction]].
  * Small samples are shrunk toward a prior so the brain doesn't over-learn
    early. Sample size is always surfaced.

NASDAQ-only; isolated from live signals.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

NDX = "NDX.INDX"

# ── Feature weights (vix_regime dominant — validated edge) ─────────────────────
_WEIGHTS: dict[str, float] = {
    "vix_regime": 3.0,
    "market_regime": 2.0,
    "high_impact_event": 1.5,
    "qqq_premarket_change": 1.5,
    "london_direction": 1.2,
    "current_session": 1.0,
    "prior_day_dir": 1.0,
    "vix_chg": 1.0,
    "us10y_chg": 1.0,
    "asia_overnight_change": 0.8,
    "dxy_chg": 0.8,
    "range_position": 0.8,
    "prior_day_change_pct": 0.8,
    "day_of_week": 0.5,
    "session_overlap": 0.5,
    "is_half_day": 0.5,
    "minutes_to_us_open": 0.3,
}
# Normalising scales for numeric fields (|diff|/scale, clipped to 1).
_SCALES: dict[str, float] = {
    "qqq_premarket_change": 0.8, "vix_chg": 8.0, "us10y_chg": 3.0, "dxy_chg": 0.5,
    "range_position": 0.5, "prior_day_change_pct": 1.5,
    "minutes_to_us_open": 240.0, "asia_overnight_change": 1.0,
}
_CATEGORICAL = {"vix_regime", "market_regime", "current_session", "london_direction",
                "prior_day_dir", "high_impact_event", "session_overlap",
                "is_half_day", "day_of_week"}

# Shrinkage: blend the observed up-rate toward the NASDAQ upward drift prior.
# 0.55 = MEASURED directional up-rate over 2015-2024 (1115 up / 2020 directional
# days in the backfill). The earlier 0.40 guess actively fought the drift.
_PRIOR_UP = 0.55
_SHRINK_ALPHA = 6.0
_LOW_SAMPLE_N = 20
# Calibration gain: the 2015-2024 walk-forward showed raw analog p_up is
# over-confident (predicted Q1-Q4 spread ~27pp vs realized ~5pp). The reported
# probability is therefore compressed toward the prior by this factor so the
# CIO reads an honest tilt, not a fake oracle. See research/cortex_backfill.
_CALIBRATION_GAIN = 0.20


def _vix_regime(price: Optional[float]) -> Optional[str]:
    """Same thresholds as strategy_optimizer_service (single source of truth)."""
    if price is None:
        return None
    if price < 14:
        return "LOW"
    if price < 20:
        return "NORMAL"
    if price < 28:
        return "ELEVATED"
    if price < 38:
        return "HIGH"
    return "EXTREME"


def _to_float(v: Any) -> Optional[float]:
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None


# ── Situation building ────────────────────────────────────────────────────────
async def build_situation(now_utc: datetime, market: Optional[dict] = None) -> dict:
    """Assemble the situation vector best-effort. Reuses *market* (from the debate
    engine's context gather) when given to avoid refetching. All fields nullable.
    """
    from services import session_context_service as sc

    if market:
        sess = market.get("session") or {}
        macro = market.get("macro") or {}
        qqq = market.get("qqq") or {}
        prior = market.get("prior_day") or {}
        rng = market.get("recent_range") or {}
        price = _to_float(market.get("price"))
    else:
        sess = await sc.enrich_price_context(now_utc)
        from services.bias_debate_engine import _macro_gauges, _qqq_premarket
        macro = _macro_gauges()
        qqq = await _qqq_premarket()
        prior, rng, price = {}, {}, None
        try:
            from services.data_fetcher import fetch_latest_price, fetch_ohlc_data
            price = _to_float(await fetch_latest_price(NDX))
            daily = await fetch_ohlc_data(NDX, "1d", limit=10)
            if daily and len(daily) >= 2:
                p = daily[-2]
                prior = {"open": _to_float(p.get("open") or p.get("o")),
                         "close": _to_float(p.get("close") or p.get("c"))}
                highs = [_to_float(d.get("high") or d.get("h")) for d in daily[-5:]]
                lows = [_to_float(d.get("low") or d.get("l")) for d in daily[-5:]]
                highs = [h for h in highs if h]; lows = [l for l in lows if l]
                if highs and lows:
                    rng = {"5d_high": max(highs), "5d_low": min(lows)}
        except Exception as e:
            logger.debug("[cortex] daily fetch degraded: %s", e)

    ny_iso = sess.get("ny_time") or now_utc.astimezone(sc.NY).isoformat()
    ny_dt = datetime.fromisoformat(ny_iso)

    vix = macro.get("vix") or {}
    dxy = macro.get("dxy") or {}
    us10y = macro.get("us10y") or {}
    vix_price = _to_float(vix.get("price"))

    # prior-day direction/magnitude
    prior_dir, prior_pct = None, None
    if prior.get("open") and prior.get("close"):
        prior_pct = round((prior["close"] - prior["open"]) / prior["open"] * 100, 3)
        prior_dir = "up" if prior_pct > 0 else "down"

    # range position of current price within the 5-day band
    range_pos = None
    if price and rng.get("5d_high") and rng.get("5d_low") and rng["5d_high"] > rng["5d_low"]:
        range_pos = round((price - rng["5d_low"]) / (rng["5d_high"] - rng["5d_low"]), 3)

    # market regime + calendar (async, best-effort)
    market_regime = None
    try:
        from services.market_regime_service import get_regime_info
        market_regime = (await get_regime_info(NDX)).get("regime")
    except Exception as e:
        logger.debug("[cortex] regime unavailable: %s", e)
    high_impact = None
    try:
        from services.economic_calendar_service import get_calendar_service
        events = await get_calendar_service().fetch_today_events()
        high_impact = any(str(getattr(e, "impact", "")).lower() == "high" for e in events)
    except Exception as e:
        logger.debug("[cortex] calendar unavailable: %s", e)

    sit = {
        "current_session": sess.get("current_session"),
        "session_overlap": sess.get("session_overlap"),
        "is_half_day": sess.get("is_half_day"),
        "minutes_to_us_open": sess.get("minutes_to_us_open"),
        "london_direction": sess.get("london_session_direction"),
        "asia_overnight_change": _to_float(sess.get("asia_overnight_change")),
        "qqq_premarket_change": _to_float(qqq.get("premarket_change_pct")),
        "vix_regime": _vix_regime(vix_price),
        "vix_price": vix_price,
        "vix_chg": _to_float(vix.get("chg_1h")),
        "dxy_chg": _to_float(dxy.get("chg_1h")),
        "us10y_chg": _to_float(us10y.get("chg_1h")),
        "market_regime": market_regime,
        "prior_day_dir": prior_dir,
        "prior_day_change_pct": prior_pct,
        "range_position": range_pos,
        "day_of_week": ny_dt.weekday(),
        "high_impact_event": high_impact,
        "_ny_time": ny_iso,
    }
    return sit


# ── Persistence ───────────────────────────────────────────────────────────────
def _client():
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        return get_supabase_client() if is_db_available() else None
    except Exception:
        return None


_SIT_COLS = [
    "current_session", "session_overlap", "is_half_day", "minutes_to_us_open",
    "london_direction", "asia_overnight_change", "qqq_premarket_change",
    "vix_regime", "vix_price", "vix_chg", "dxy_chg", "us10y_chg", "market_regime",
    "prior_day_dir", "prior_day_change_pct", "range_position", "day_of_week",
    "high_impact_event",
]


def record_episode(situation: dict, predicted_bias: Optional[str] = None,
                   confidence: Optional[float] = None, run_label: Optional[str] = None,
                   source: str = "bias_run", now_utc: Optional[datetime] = None) -> Optional[int]:
    """Insert an episode (situation + decision; outcome filled later). Returns id
    or None (fail-open — never breaks the caller)."""
    client = _client()
    if client is None:
        return None
    now_utc = now_utc or datetime.now(timezone.utc)
    ny_iso = situation.get("_ny_time") or now_utc.isoformat()
    row = {k: situation.get(k) for k in _SIT_COLS}
    row.update({
        "episode_ts_utc": now_utc.isoformat(),
        "ny_date": ny_iso[:10],
        "symbol": NDX,
        "run_label": run_label,
        "source": source,
        "predicted_bias": predicted_bias,
        "confidence": confidence,
        "situation_json": {k: v for k, v in situation.items() if not k.startswith("_")},
    })
    try:
        res = client.table("cortex_episodes").insert(row)
        if res.get("error"):
            logger.warning("[cortex] record error: %s", res["error"])
            return None
        data = res.get("data")
        return (data[0].get("id") if isinstance(data, list) and data else None)
    except Exception as e:
        logger.warning("[cortex] record exception: %s", e)
        return None


def fill_outcomes(ny_date: str, actual_dir: str, actual_pct: float) -> int:
    """Grade every episode for *ny_date* against the realised NDX move."""
    client = _client()
    if client is None:
        return 0
    try:
        rows = (client.table("cortex_episodes").select("*")
                .eq("symbol", NDX).eq("ny_date", ny_date).execute()).get("data") or []
    except Exception as e:
        logger.warning("[cortex] fill read error: %s", e)
        return 0
    n = 0
    for r in rows:
        pb = (r.get("predicted_bias") or "").lower()
        correct = None
        if pb in ("bullish", "bearish", "neutral", "choppy"):
            correct = ((pb == "bullish" and actual_dir == "positive")
                       or (pb == "bearish" and actual_dir == "negative")
                       or (pb in ("neutral", "choppy") and actual_dir == "flat"))
        try:
            (client.table("cortex_episodes").eq("id", r["id"]).update({
                "actual_close_direction": actual_dir,
                "actual_change_pct": actual_pct,
                "was_correct": correct,
                "outcome_filled_at": datetime.now(timezone.utc).isoformat(),
            }))
            n += 1
        except Exception as e:
            logger.debug("[cortex] fill row %s error: %s", r.get("id"), e)
    return n


# ── Analog retrieval (kNN) ────────────────────────────────────────────────────
def _distance(q: dict, c: dict) -> Optional[float]:
    """Weighted distance over fields present on BOTH sides; None if no overlap."""
    num, den = 0.0, 0.0
    for field, w in _WEIGHTS.items():
        a, b = q.get(field), c.get(field)
        if a is None or b is None:
            continue
        if field in _CATEGORICAL:
            d = 0.0 if a == b else 1.0
        else:
            scale = _SCALES.get(field, 1.0)
            try:
                d = min(1.0, abs(float(a) - float(b)) / scale)
            except (TypeError, ValueError):
                continue
        num += w * d
        den += w
    return (num / den) if den > 0 else None


def find_analogs(situation: dict, k: int = 8, symbol: str = NDX) -> dict:
    """Return the K most-similar graded past days + a shrunk base rate."""
    empty = {"analogs": [], "sample_n": 0, "up": 0, "down": 0, "flat": 0,
             "p_up_shrunk": None, "avg_change_pct": None, "low_sample": True}
    client = _client()
    if client is None:
        return empty
    try:
        # Fetch this symbol's episodes; graded-only filtering happens in Python
        # (PostgREST NOT-NULL filtering is finicky, and the pool is small).
        rows = (client.table("cortex_episodes").select("*")
                .eq("symbol", symbol)
                .limit(2000).execute()).get("data") or []
    except Exception as e:
        logger.warning("[cortex] analog read error: %s", e)
        return empty

    scored = []
    for r in rows:
        if not r.get("actual_close_direction"):
            continue
        d = _distance(situation, r)
        if d is not None:
            scored.append((d, r))
    scored.sort(key=lambda x: x[0])
    top = [r for _, r in scored[:k]]
    n = len(top)
    if n == 0:
        return empty

    up = sum(1 for r in top if r.get("actual_close_direction") == "positive")
    down = sum(1 for r in top if r.get("actual_close_direction") == "negative")
    flat = n - up - down
    changes = [_to_float(r.get("actual_change_pct")) for r in top]
    changes = [c for c in changes if c is not None]
    p_up = (up + _SHRINK_ALPHA * _PRIOR_UP) / (n + _SHRINK_ALPHA)
    # Calibrated tilt — what we actually surface to the CIO (validated gain).
    p_cal = _PRIOR_UP + _CALIBRATION_GAIN * (p_up - _PRIOR_UP)
    return {
        "analogs": [{"ny_date": r.get("ny_date"), "dir": r.get("actual_close_direction"),
                     "chg": r.get("actual_change_pct"), "vix_regime": r.get("vix_regime"),
                     "market_regime": r.get("market_regime")} for r in top],
        "sample_n": n, "up": up, "down": down, "flat": flat,
        "p_up_shrunk": round(p_up, 3),
        "p_up_calibrated": round(p_cal, 3),
        "avg_change_pct": round(sum(changes) / len(changes), 3) if changes else None,
        "low_sample": n < _LOW_SAMPLE_N,
    }


def analogs_prompt_block(res: dict) -> str:
    """Compact English base-rate block for the CIO prompt."""
    n = res.get("sample_n", 0)
    if not n:
        return ("HISTORICAL ANALOGS (CORTEX memory): none comparable yet — memory "
                "is still accumulating; rely on live analysis this run.")
    warn = " (LOW sample)" if res.get("low_sample") else ""
    avg = res.get("avg_change_pct")
    return (
        f"HISTORICAL CONTEXT (CORTEX memory — {n} structurally-similar past days{warn}):\n"
        f"- how they resolved: {res['up']} up / {res['down']} down / {res['flat']} flat, "
        f"avg move {avg}%\n"
        "IMPORTANT: backtest found NO reliable directional edge in this analog set "
        "— treat it as loose context on how comparable setups have resolved, NOT a "
        "prediction. Your live analysis of price/structure/macro governs the call."
    )
