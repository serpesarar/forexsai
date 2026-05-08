"""
Post-Deploy Monitor — observe implemented proposals for 7 days.

After a proposal merges (status='implemented' + reviewed_at set), this service
tracks LIVE performance daily for the next 7 days and compares it to the
simulated_metric we computed pre-merge. If reality diverges materially from
the simulation, recommend a rollback.

Workflow per implemented proposal:
  Day 0  → mark live_tracking_started_at = NOW
  Day 1-7 → daily: pull signals matching the proposal's symbol+model_type
                   that fired AFTER live_tracking_started_at, compute live
                   metrics, append to live_tracking_metric.daily_snapshots
  Day 7  → final verdict:
              divergence_factor = live_winrate_delta / simulated_winrate_delta
              if divergence_factor < 0.5 → mark rollback_recommended=TRUE
              else → mark live_tracking_metric.status='confirmed'

Critical safety net — without this, a proposal that looks great in simulation
but fails in production silently degrades the system.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Tracking window
MAX_TRACKING_DAYS = 7
DAILY_CHECK_INTERVAL_SECONDS = 24 * 3600

# Decision thresholds
DIVERGENCE_ROLLBACK_THRESHOLD = 0.5    # live_delta < sim_delta × 0.5 → rollback
MIN_LIVE_SAMPLES_FOR_VERDICT = 10      # need ≥10 affected signals before verdict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Confidence interval (Wilson) — for honest small-sample estimates
# ---------------------------------------------------------------------------

def wilson_interval(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% CI for a binomial win rate, robust at small n."""
    if total == 0:
        return (0.0, 0.0)
    p = wins / total
    z2 = z * z
    denom = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)) / denom
    return (max(0.0, center - margin) * 100, min(1.0, center + margin) * 100)


# ---------------------------------------------------------------------------
# Live signal pull + metrics
# ---------------------------------------------------------------------------

async def _fetch_live_signals(client, symbol: str, model_type: str,
                                since_iso: str, max_rows: int = 5000) -> list[dict]:
    """All resolved signals for this proposal's scope since tracking started."""
    try:
        q = client.table("prediction_logs").select(
            "id,ml_direction,ml_confidence,status,resolution_reason,factors,created_at"
        ).eq("symbol", symbol).eq("model_type", model_type).gte(
            "created_at", since_iso
        ).in_("status", ["completed", "stopped"]).limit(max_rows)
        res = q.execute() if hasattr(q, "execute") else q
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", [])
        return data or []
    except Exception as e:
        logger.exception("[monitor] fetch failed: %s", e)
        return []


async def _fetch_outcomes(client, prediction_ids: list[str]) -> dict[str, dict]:
    if not prediction_ids:
        return {}
    out: dict[str, dict] = {}
    for i in range(0, len(prediction_ids), 200):
        chunk = prediction_ids[i:i + 200]
        try:
            r = client.table("outcome_results").select(
                "prediction_id,highest_profit_pips,lowest_drawdown_pips,exit_price"
            ).in_("prediction_id", chunk)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            for o in data:
                out[o["prediction_id"]] = o
        except Exception as e:
            logger.warning("[monitor] outcome fetch failed: %s", e)
    return out


def _compute_live_metric(signals: list[dict], outcomes: dict[str, dict]) -> dict:
    """Pure-function metric computation (mirrors proposal_simulator)."""
    if not signals:
        return {"n_signals": 0, "win_rate": None, "total_pnl_pips": 0.0,
                "max_drawdown_pips": 0.0, "ci_low_pct": None, "ci_high_pct": None}
    wins = sum(1 for s in signals if s.get("status") == "completed")
    n = len(signals)
    pnls: list[float] = []
    for s in signals:
        o = outcomes.get(s["id"], {})
        if s.get("status") == "completed":
            pnls.append(float(o.get("highest_profit_pips") or 0))
        elif s.get("status") == "stopped":
            pnls.append(-float(o.get("lowest_drawdown_pips") or 0))
        else:
            pnls.append(0.0)
    cum = []
    running = 0.0
    for v in pnls:
        running += v
        cum.append(running)
    # Max drawdown of cumulative P/L
    peak = cum[0] if cum else 0.0
    max_dd = 0.0
    for v in cum:
        if v > peak:
            peak = v
        dd = peak - v
        if dd > max_dd:
            max_dd = dd
    ci_low, ci_high = wilson_interval(wins, n)
    return {
        "n_signals": n,
        "n_wins": wins,
        "win_rate": round(wins / n * 100, 2) if n else None,
        "total_pnl_pips": round(sum(pnls), 2),
        "max_drawdown_pips": round(max_dd, 2),
        "ci_low_pct": round(ci_low, 2),
        "ci_high_pct": round(ci_high, 2),
    }


# ---------------------------------------------------------------------------
# Single-proposal tracker
# ---------------------------------------------------------------------------

async def check_proposal(proposal: dict) -> dict:
    """Pull live signals since tracking started, append daily snapshot, decide verdict."""
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if client is None:
        return {"status": "skipped", "reason": "no_db"}

    pid = proposal["id"]
    started_iso = proposal.get("live_tracking_started_at")
    if not started_iso:
        return {"status": "skipped", "reason": "no_start_time"}
    started = datetime.fromisoformat(started_iso.replace("Z", "+00:00"))
    age_days = (_now() - started).total_seconds() / (24 * 3600)

    # Pull live signals in scope
    signals = await _fetch_live_signals(client, proposal["symbol"],
                                          proposal["model_type"], started_iso)
    outcomes = await _fetch_outcomes(client, [s["id"] for s in signals])
    live = _compute_live_metric(signals, outcomes)

    # Compare with simulation
    sim = proposal.get("simulated_metric") or {}
    sim_simulated = sim.get("simulated") or {}
    sim_original = sim.get("original") or {}

    sim_winrate_delta = (
        sim_simulated.get("win_rate", 0) - sim_original.get("win_rate", 0)
        if sim_simulated.get("win_rate") is not None and sim_original.get("win_rate") is not None
        else None
    )
    # For LIVE delta we don't have a counterfactual baseline, but we can compare
    # current win-rate to the historic baseline (pre-change_metric)
    pre_change = proposal.get("pre_change_metric") or {}
    pre_winrate = pre_change.get("win_rate")
    live_winrate_delta = (live["win_rate"] - pre_winrate) if (
        live.get("win_rate") is not None and pre_winrate is not None) else None

    divergence_factor = None
    if (sim_winrate_delta is not None and live_winrate_delta is not None
            and sim_winrate_delta != 0):
        divergence_factor = live_winrate_delta / sim_winrate_delta

    # Verdict
    verdict_status = "tracking"
    rollback_recommended = False
    rollback_reason: Optional[str] = None
    if age_days >= MAX_TRACKING_DAYS:
        if live["n_signals"] < MIN_LIVE_SAMPLES_FOR_VERDICT:
            verdict_status = "insufficient_data"
        elif divergence_factor is not None and divergence_factor < DIVERGENCE_ROLLBACK_THRESHOLD:
            verdict_status = "degraded"
            rollback_recommended = True
            rollback_reason = (
                f"Live delta ({live_winrate_delta:+.2f}pp) is only "
                f"{divergence_factor:.0%} of simulated ({sim_winrate_delta:+.2f}pp) "
                f"after {int(age_days)} days, {live['n_signals']} signals."
            )
        elif live.get("max_drawdown_pips", 0) > sim_simulated.get("total_pnl_pips", 0) * 0.8:
            # Drawdown ate most of expected gain — material risk regardless of win-rate
            verdict_status = "degraded_drawdown"
            rollback_recommended = True
            rollback_reason = (
                f"Live max drawdown ({live['max_drawdown_pips']:.0f} pips) is "
                f"≥80% of simulated total P/L target. Risk profile worse than expected."
            )
        else:
            verdict_status = "confirmed"

    # Append daily snapshot
    existing = proposal.get("live_tracking_metric") or {}
    if isinstance(existing, str):
        try: existing = json.loads(existing)
        except Exception: existing = {}
    daily = list(existing.get("daily_snapshots") or [])
    daily.append({
        "checked_at": _iso(_now()),
        "age_days": round(age_days, 2),
        **live,
    })
    new_metric = {
        "started_at": started_iso,
        "checked_days": int(age_days),
        "daily_snapshots": daily[-30:],   # cap to last 30 entries
        "overall": live,
        "vs_simulation": {
            "sim_winrate_delta": sim_winrate_delta,
            "live_winrate_delta": live_winrate_delta,
            "divergence_factor": divergence_factor,
        },
        "status": verdict_status,
    }

    # Persist back
    update = {
        "live_tracking_metric": new_metric,
        "live_tracking_last_check": _iso(_now()),
    }
    if rollback_recommended:
        update["rollback_recommended"] = True
        update["rollback_recommendation_reason"] = rollback_reason
    try:
        # Custom supabase wrapper expects .eq() BEFORE .update() — see ai_ops_router.
        client.table("improvement_proposals").eq("id", pid).update(update)
    except Exception as e:
        logger.exception("[monitor] update failed: %s", e)

    logger.info(f"[monitor] proposal {pid[:8]}: status={verdict_status} "
                f"live_winrate={live.get('win_rate')} sim_div={divergence_factor} "
                f"signals={live['n_signals']}")
    return {"proposal_id": pid, "verdict": verdict_status,
            "rollback_recommended": rollback_recommended,
            "live": live, "divergence_factor": divergence_factor}


# ---------------------------------------------------------------------------
# Cron loop
# ---------------------------------------------------------------------------

async def check_all_implemented_proposals() -> dict:
    """Daily — check every implemented proposal that's still in tracking window."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "skipped", "reason": "db_unavailable"}
    client = get_supabase_client()
    if client is None:
        return {"status": "skipped"}

    # Bootstrap: any 'implemented' proposals without a tracking start time → start now
    try:
        bootstrap = client.table("improvement_proposals").select("id").eq(
            "status", "implemented"
        ).is_("live_tracking_started_at", "null").limit(50)
        res = bootstrap.execute() if hasattr(bootstrap, "execute") else bootstrap
        bootstrap_data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        if bootstrap_data:
            for row in bootstrap_data:
                client.table("improvement_proposals").update(
                    {"live_tracking_started_at": _iso(_now())}
                ).eq("id", row["id"])
            logger.info(f"[monitor] bootstrapped {len(bootstrap_data)} proposals into tracking")
    except Exception as e:
        logger.warning("[monitor] bootstrap failed: %s", e)

    # Pull all proposals currently being tracked
    cutoff = _now() - timedelta(days=MAX_TRACKING_DAYS + 2)  # small buffer past final check
    try:
        q = client.table("improvement_proposals").select(
            "id,symbol,model_type,status,simulated_metric,pre_change_metric,"
            "live_tracking_started_at,live_tracking_metric,rollback_recommended"
        ).eq("status", "implemented").gte(
            "live_tracking_started_at", _iso(cutoff)
        ).limit(200)
        res = q.execute() if hasattr(q, "execute") else q
        proposals = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
    except Exception as e:
        logger.exception("[monitor] fetch tracking list failed: %s", e)
        return {"status": "error", "error": str(e)}

    if not proposals:
        return {"status": "ok", "proposals_checked": 0}

    results: list[dict] = []
    for p in proposals:
        try:
            results.append(await check_proposal(p))
        except Exception as e:
            logger.warning("[monitor] check_proposal failed for %s: %s", p.get("id"), e)
    rollback_count = sum(1 for r in results if r.get("rollback_recommended"))
    return {
        "status": "ok",
        "proposals_checked": len(results),
        "rollback_recommendations": rollback_count,
        "results": results,
    }


async def daily_loop():
    """Lifespan task — runs every 24h after 1-hour startup delay."""
    await asyncio.sleep(3600)   # 1h initial delay
    while True:
        try:
            summary = await check_all_implemented_proposals()
            logger.info(f"[monitor] daily cycle: {summary.get('proposals_checked', 0)} checked, "
                        f"{summary.get('rollback_recommendations', 0)} rollback alerts")
        except Exception as e:
            logger.exception("[monitor] daily cycle failed: %s", e)
        await asyncio.sleep(DAILY_CHECK_INTERVAL_SECONDS)
