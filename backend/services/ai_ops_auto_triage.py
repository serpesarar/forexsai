"""
AI-Ops Auto-Triage — silently process pending proposals.

User has 200+ pending proposals. Most are noise (overfit clusters, low
selectivity, etc.). Manual review is impractical. This service objectively
classifies every pending proposal into one of three buckets using the
already-computed simulation + walk-forward + selectivity data:

  AUTO_APPLY    — meets all strict gates → ready for auto-implementation
  HUMAN_REVIEW  — ambiguous, needs human judgment
  AUTO_REJECT   — objectively fails gates → close

Strict gate criteria for AUTO_APPLY (all must hold):
  1. simulated_metric.status == 'ok'
  2. deltas.verdict == 'unanimously_better'
  3. deltas.robustness.status in ('robust', 'marginally_overfit')
  4. deltas.selectivity_label in ('clean', 'acceptable')
  5. simulated.n_signals >= 30  (sample size)
  6. deltas.win_rate_pp >= 2.0   (meaningful improvement)
  7. The fix is a filter_rule with a valid filter_spec (not feature_addition etc)

Auto-reject criteria (any one is enough):
  1. deltas.verdict == 'unanimously_worse'
  2. deltas.verdict == 'noisy_filter'
  3. deltas.robustness.status == 'highly_overfit'
  4. deltas.robustness.status == 'broken'
  5. simulated.n_signals < 10 (too few samples)
  6. No filter_rule with valid spec AND no other auto-simulatable fix

Everything else → HUMAN_REVIEW.

The triage runs simulation if missing, then applies the gates. It does NOT
auto-merge code — that's a separate auto-implement step.

Cron: runs once per 6 hours on every pending proposal that hasn't been triaged.
Manual trigger via POST /api/ai-ops/auto-triage/run.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Gating thresholds — change here to tune aggressiveness
MIN_SAMPLE_FOR_AUTO_APPLY = 30
MIN_SAMPLE_FOR_DECISION = 10      # below this → human review (don't auto-reject)
MIN_WINRATE_DELTA_PP = 2.0        # below this → not material enough
ROBUST_RATIOS = {"robust", "marginally_overfit"}
CLEAN_SELECTIVITIES = {"clean", "acceptable"}
HARD_REJECT_VERDICTS = {"unanimously_worse", "noisy_filter"}
HARD_REJECT_ROBUSTNESS = {"highly_overfit", "broken"}
AUTO_SIMULATABLE_FIX_TYPES = {"filter_rule", "threshold_tweak"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Decision logic — pure function, no side effects
# ---------------------------------------------------------------------------

def classify_proposal(prop: dict) -> tuple[str, str]:
    """Return (decision, reason). Decision ∈ {auto_apply, human_review, auto_reject}.

    Pure function — given a proposal dict, decide. No DB calls. Easy to test."""
    sim = prop.get("simulated_metric")
    fixes = prop.get("proposed_fixes") or []
    if isinstance(fixes, str):
        try:
            fixes = json.loads(fixes)
        except Exception:
            fixes = []

    # First: is there at least one auto-simulatable fix? If not, requires
    # human implementation regardless of simulation outcome.
    has_simulatable_fix = any(
        isinstance(f, dict) and f.get("type") in AUTO_SIMULATABLE_FIX_TYPES
        and (f.get("filter_spec") or f.get("threshold_spec"))
        for f in fixes
    )

    if isinstance(sim, str):
        try:
            sim = json.loads(sim)
        except Exception:
            sim = None

    if not sim or sim.get("status") != "ok":
        # No simulation run yet OR sim failed — human must review
        if not has_simulatable_fix:
            return ("auto_reject",
                    "no auto-simulatable fix (feature_addition/retrain type) and no simulation data — needs human dev work anyway")
        return ("human_review", "simulation not yet computed or returned non-ok status")

    deltas = sim.get("deltas") or {}
    simulated = sim.get("simulated") or {}

    n_signals = (simulated.get("n_signals") or sim.get("simulated", {}).get("n_signals") or 0)
    verdict = deltas.get("verdict")
    selectivity = deltas.get("selectivity_label")
    win_rate_delta = deltas.get("win_rate_pp")
    robustness = (deltas.get("robustness") or {}).get("status")

    # ── HARD REJECT GATES ────────────────────────────────────────────────
    if verdict in HARD_REJECT_VERDICTS:
        return ("auto_reject", f"verdict={verdict} — change does not improve metrics")
    if robustness in HARD_REJECT_ROBUSTNESS:
        return ("auto_reject",
                f"walk-forward robustness={robustness} — rule fits noise in recent cluster window")
    if n_signals < MIN_SAMPLE_FOR_DECISION:
        return ("auto_reject", f"sample size {n_signals} < {MIN_SAMPLE_FOR_DECISION} — not enough data to be confident")
    if not has_simulatable_fix:
        return ("auto_reject", "no filter_rule or threshold_tweak with valid spec — manual code work needed")

    # ── AUTO_APPLY GATES (all must hold) ─────────────────────────────────
    gates_passed: list[str] = []
    gates_failed: list[str] = []
    def check(condition: bool, ok_msg: str, fail_msg: str):
        if condition:
            gates_passed.append(ok_msg)
        else:
            gates_failed.append(fail_msg)

    check(verdict == "unanimously_better", "verdict_unanimous", f"verdict={verdict}")
    check(robustness in ROBUST_RATIOS, f"robustness_{robustness}", f"robustness={robustness}")
    check(selectivity in CLEAN_SELECTIVITIES,
          f"selectivity_{selectivity}", f"selectivity={selectivity}")
    check(n_signals >= MIN_SAMPLE_FOR_AUTO_APPLY,
          f"sample_n={n_signals}", f"sample {n_signals} < {MIN_SAMPLE_FOR_AUTO_APPLY}")
    check(win_rate_delta is not None and win_rate_delta >= MIN_WINRATE_DELTA_PP,
          f"win_rate_delta={win_rate_delta}",
          f"win_rate_delta={win_rate_delta} < {MIN_WINRATE_DELTA_PP}")

    if not gates_failed:
        return ("auto_apply",
                f"All gates passed: {', '.join(gates_passed)}")
    return ("human_review",
            f"Mixed signals — passed: {len(gates_passed)}, failed: [{'; '.join(gates_failed)}]")


# ---------------------------------------------------------------------------
# Triage runner
# ---------------------------------------------------------------------------

async def _fetch_pending_proposals(client, limit: int = 500) -> list[dict]:
    """All status='pending' proposals that haven't been triaged yet."""
    try:
        q = client.table("improvement_proposals").select(
            "id,symbol,model_type,severity,proposed_fixes,simulated_metric,"
            "pre_change_metric,status,auto_decision,created_at"
        ).eq("status", "pending").order("created_at", desc=True).limit(limit)
        res = q.execute() if hasattr(q, "execute") else q
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        # Skip already-triaged
        return [p for p in (data or []) if not p.get("auto_decision")]
    except Exception as e:
        logger.exception("[auto-triage] fetch failed: %s", e)
        return []


async def _ensure_simulation(prop: dict) -> bool:
    """If no simulation data, kick one off. Returns True if sim available after."""
    if prop.get("simulated_metric"):
        return True
    try:
        from services.proposal_simulator import simulate_and_persist
        await simulate_and_persist(prop["id"], window_days=60)
        # Refresh — fetch updated row
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client is None:
            return False
        q = client.table("improvement_proposals").select("simulated_metric").eq(
            "id", prop["id"]).limit(1)
        res = q.execute() if hasattr(q, "execute") else q
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        if data and data[0].get("simulated_metric"):
            prop["simulated_metric"] = data[0]["simulated_metric"]
            return True
    except Exception as e:
        logger.warning("[auto-triage] simulation kick-off failed for %s: %s",
                       prop.get("id"), e)
    return False


async def triage_proposal(prop: dict, *, run_simulation_if_missing: bool = True) -> dict:
    """Classify one proposal, persist the decision back to DB."""
    if run_simulation_if_missing and not prop.get("simulated_metric"):
        await _ensure_simulation(prop)
    decision, reason = classify_proposal(prop)
    # Persist
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client is not None:
            update = {
                "auto_decision": decision,
                "auto_decision_reason": reason,
                "auto_decided_at": _iso(_now()),
            }
            if decision == "auto_reject":
                # Auto-rejected proposals get status='rejected' so they leave the queue
                update["status"] = "rejected"
                update["rollback_reason"] = f"auto-triage: {reason}"
                update["reviewed_by"] = "auto-triage"
                update["reviewed_at"] = _iso(_now())
            # Custom wrapper order: .eq() before .update()
            client.table("improvement_proposals").eq("id", prop["id"]).update(update)
    except Exception as e:
        logger.warning("[auto-triage] persist failed for %s: %s", prop.get("id"), e)
    return {"id": prop["id"], "decision": decision, "reason": reason}


async def run_full_triage(limit: int = 500) -> dict:
    """Process every untriaged pending proposal. Run from cron or manual trigger."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "skipped", "reason": "db_unavailable"}
    client = get_supabase_client()
    if client is None:
        return {"status": "skipped"}

    pending = await _fetch_pending_proposals(client, limit=limit)
    logger.info("[auto-triage] processing %d untriaged pending proposals", len(pending))

    counts = {"auto_apply": 0, "human_review": 0, "auto_reject": 0, "errors": 0}
    decisions: list[dict] = []
    for prop in pending:
        try:
            result = await triage_proposal(prop, run_simulation_if_missing=True)
            counts[result["decision"]] = counts.get(result["decision"], 0) + 1
            decisions.append(result)
        except Exception as e:
            logger.warning("[auto-triage] failed for %s: %s", prop.get("id"), e)
            counts["errors"] += 1

    summary = {
        "status": "ok",
        "processed": len(pending),
        "counts": counts,
        "completed_at": _iso(_now()),
    }
    logger.info("[auto-triage] complete: %s", summary)
    return summary


# ---------------------------------------------------------------------------
# Cron loop
# ---------------------------------------------------------------------------

CRON_INTERVAL_SECONDS = 6 * 3600   # every 6h
INITIAL_DELAY_SECONDS = 5 * 60     # 5min after startup


async def cron_loop() -> None:
    await asyncio.sleep(INITIAL_DELAY_SECONDS)
    while True:
        try:
            summary = await run_full_triage(limit=500)
            logger.info("[auto-triage] cron cycle: %s", summary)
        except Exception as e:
            logger.exception("[auto-triage] cron cycle failed: %s", e)
        await asyncio.sleep(CRON_INTERVAL_SECONDS)
