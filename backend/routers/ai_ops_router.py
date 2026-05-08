"""
AI-Ops dashboard endpoints — review/approve/reject DeepSeek proposals.

Workflow:
  1. orchestrator daily runs → writes pending proposals
  2. user opens dashboard → GET /api/ai-ops/proposals
  3. user approves → PATCH /api/ai-ops/proposals/{id}/approve
     → optionally creates a GitHub issue (Step 3 handoff)
  4. user/Claude Code implements → PR opened → review & merge
  5. Post-merge: status moves to 'implemented'; orchestrator tracks 7-day delta
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from database.supabase_client import get_supabase_client, is_db_available

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-ops", tags=["AI-Ops"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ApproveRequest(BaseModel):
    reviewer: Optional[str] = None
    create_github_issue: bool = True   # Step 3 handoff
    note: Optional[str] = None


class RejectRequest(BaseModel):
    reviewer: Optional[str] = None
    reason: Optional[str] = None


class ManualRunRequest(BaseModel):
    window_days: int = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_data(result_or_query: Any) -> list[dict]:
    """Universal extractor — works for both auto-executing wrappers and
    lazy query builders. If the object has .execute(), call it; otherwise
    treat it as already-executed result."""
    obj = result_or_query
    if hasattr(obj, "execute") and callable(getattr(obj, "execute", None)):
        try:
            obj = obj.execute()
        except Exception as e:
            logger.warning("[ai_ops] query execute failed: %s", e)
            return []
    if isinstance(obj, dict):
        return obj.get("data") or []
    return getattr(obj, "data", None) or []


def _exec(query_or_result: Any) -> Any:
    """Execute a lazy query if needed; pass through executed results."""
    obj = query_or_result
    if hasattr(obj, "execute") and callable(getattr(obj, "execute", None)):
        try:
            return obj.execute()
        except Exception as e:
            logger.warning("[ai_ops] mutation execute failed: %s", e)
            return None
    return obj


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_stats():
    """High-level counts for the dashboard header."""
    if not is_db_available():
        return {"available": False}
    client = get_supabase_client()
    out: dict[str, Any] = {"available": True, "by_status": {}, "by_severity": {}}
    try:
        # Explicit .execute() — the project's supabase wrapper sometimes auto-executes
        # and sometimes returns a lazy query, depending on the method chain. Always
        # be explicit on read paths.
        q1 = client.table("improvement_proposals").select("status,severity").limit(2000)
        res1 = q1.execute() if hasattr(q1, "execute") else q1
        rows = (res1.get("data") if isinstance(res1, dict)
                else getattr(res1, "data", None)) or []
        for r in rows:
            s = r.get("status") or "unknown"
            sev = r.get("severity") or "unknown"
            out["by_status"][s] = out["by_status"].get(s, 0) + 1
            out["by_severity"][sev] = out["by_severity"].get(sev, 0) + 1
        out["total"] = len(rows)

        q2 = client.table("failure_clusters").select("id").limit(2000)
        res2 = q2.execute() if hasattr(q2, "execute") else q2
        cluster_rows = (res2.get("data") if isinstance(res2, dict)
                        else getattr(res2, "data", None)) or []
        out["clusters_total"] = len(cluster_rows)
    except Exception as e:
        logger.exception("ai_ops stats failed: %s", e)
        out["error"] = str(e)
    return out


@router.get("/proposals")
async def list_proposals(
    status: Optional[str] = Query(None, description="pending|approved|rejected|implemented|rolled_back"),
    severity: Optional[str] = Query(None, description="critical|high|medium|low"),
    symbol: Optional[str] = None,
    model_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """List improvement proposals with optional filters, newest first."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        q = client.table("improvement_proposals").select(
            "id,cluster_id,symbol,model_type,severity,status,llm_model,"
            "root_cause,proposed_fixes,alternative_explanations,requires_data,"
            "pre_change_metric,post_change_metric,simulated_metric,simulated_at,"
            "reviewed_by,reviewed_at,"
            "pr_url,created_at,updated_at"
        ).order("created_at", desc=True).limit(limit)
        if status:
            q = q.eq("status", status)
        if severity:
            q = q.eq("severity", severity)
        if symbol:
            q = q.eq("symbol", symbol)
        if model_type:
            q = q.eq("model_type", model_type)
        # Force explicit execution
        result = q.execute() if hasattr(q, "execute") else q
        rows = (result.get("data") if isinstance(result, dict)
                else getattr(result, "data", None)) or []
        return {"proposals": rows, "count": len(rows)}
    except Exception as e:
        logger.exception("list_proposals failed: %s", e)
        raise HTTPException(500, str(e))


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """Single proposal + its cluster + sample failures for inspection."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        rows = _row_data(client.table("improvement_proposals")
                         .select("*").eq("id", proposal_id).limit(1))
        if not rows:
            raise HTTPException(404, "proposal not found")
        prop = rows[0]
        cluster = None
        if prop.get("cluster_id"):
            crows = _row_data(client.table("failure_clusters")
                              .select("*").eq("id", prop["cluster_id"]).limit(1))
            cluster = crows[0] if crows else None
        # Sample failures
        sample_failures: list[dict] = []
        if cluster and cluster.get("representative_prediction_ids"):
            ids = cluster["representative_prediction_ids"][:10]
            if ids:
                sample = _row_data(client.table("prediction_logs").select(
                    "id,symbol,model_type,ml_direction,ml_confidence,ml_entry_price,"
                    "ml_target_price,ml_stop_price,status,resolution_reason,factors,created_at"
                ).in_("id", ids))
                sample_failures = sample
        return {"proposal": prop, "cluster": cluster, "sample_failures": sample_failures}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_proposal failed: %s", e)
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Step 3 — GitHub issue handoff
# ---------------------------------------------------------------------------

GITHUB_REPO = os.getenv("GITHUB_REPO", "serpesarar/forexsai")  # owner/repo
GITHUB_TOKEN_ENV = "GITHUB_TOKEN"


def _format_issue_body(prop: dict, cluster: Optional[dict]) -> tuple[str, list[str]]:
    """Build issue body markdown + label list."""
    sev = (prop.get("severity") or "medium").lower()
    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
    fixes = prop.get("proposed_fixes") or []
    body = []
    body.append(f"## {severity_emoji} AI-Ops Proposal — {prop['symbol']} / {prop['model_type']}")
    body.append("")
    body.append(f"**Severity:** `{sev}`  ·  **LLM:** `{prop.get('llm_model', 'deepseek-reasoner')}`  ·  "
                f"**Proposal ID:** `{prop['id']}`")
    body.append("")
    body.append("### Root Cause")
    body.append(prop.get("root_cause") or "_(not provided)_")
    body.append("")
    if cluster:
        body.append("### Cluster Stats")
        body.append(f"- Sample size: **{cluster.get('sample_size')}** failures")
        body.append(f"- Win rate (this signature): **{cluster.get('win_rate')}%**")
        body.append(f"- Total P/L: **{cluster.get('total_pnl_pips')} pips**")
        body.append(f"- Window: `{cluster.get('window_start')}` → `{cluster.get('window_end')}`")
        body.append(f"- Common tags: `{cluster.get('common_tags')}`")
        body.append(f"- Signature: `{cluster.get('cluster_signature')}`")
        body.append("")
    body.append("### Proposed Fixes")
    for i, fix in enumerate(fixes, 1):
        if not isinstance(fix, dict):
            continue
        body.append(f"#### {i}. {fix.get('description', '(no description)')} — `{fix.get('type', '?')}` "
                    f"(risk: {fix.get('risk', '?')})")
        if fix.get("implementation_hint"):
            body.append("```")
            body.append(fix["implementation_hint"])
            body.append("```")
        if fix.get("estimated_impact"):
            body.append(f"_Estimated impact: {fix['estimated_impact']}_")
        body.append("")
    if prop.get("alternative_explanations"):
        body.append("### Alternative Explanations")
        for alt in prop["alternative_explanations"]:
            body.append(f"- {alt}")
        body.append("")
    if prop.get("requires_data"):
        body.append("### Additional Data Needed")
        body.append(prop["requires_data"])
        body.append("")
    body.append("---")
    body.append("**Workflow:** Implement the chosen fix in a branch → open a PR referencing this issue. "
                "After merge, the orchestrator will track post-change metrics for 7 days and auto-rollback "
                "if win-rate degrades > 5%.")
    body.append("")
    body.append(f"_Generated by AI-Ops orchestrator on {prop.get('created_at')}_")
    labels = ["ai-ops", f"severity:{sev}", f"symbol:{prop['symbol']}", f"model:{prop['model_type']}"]
    return "\n".join(body), labels


async def _create_github_issue(prop: dict, cluster: Optional[dict]) -> Optional[str]:
    """Create a GitHub issue describing the proposal. Returns the issue HTML URL or None."""
    token = os.environ.get(GITHUB_TOKEN_ENV)
    if not token:
        logger.warning("[ai-ops] GITHUB_TOKEN missing — skipping issue creation")
        return None
    title = (f"[AI-Ops] {(prop.get('severity') or 'medium').upper()} · "
             f"{prop['symbol']}/{prop['model_type']} — "
             f"{(prop.get('root_cause') or '')[:80]}")
    body, labels = _format_issue_body(prop, cluster)
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={"title": title, "body": body, "labels": labels},
            )
        if r.status_code in (200, 201):
            return r.json().get("html_url")
        logger.warning("[ai-ops] github issue create failed: %s %s", r.status_code, r.text[:300])
    except Exception as e:
        logger.exception("[ai-ops] github call failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Approve / Reject
# ---------------------------------------------------------------------------

@router.patch("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, payload: ApproveRequest):
    """Approve a proposal. Optionally creates a GitHub issue for implementation handoff."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        # Fetch current state
        rows = _row_data(client.table("improvement_proposals")
                         .select("*").eq("id", proposal_id).limit(1))
        if not rows:
            raise HTTPException(404, "proposal not found")
        prop = rows[0]
        if prop.get("status") not in ("pending", "reviewed"):
            raise HTTPException(409, f"cannot approve from status={prop.get('status')}")

        # Optional issue creation
        issue_url = None
        if payload.create_github_issue:
            cluster = None
            if prop.get("cluster_id"):
                crows = _row_data(client.table("failure_clusters")
                                  .select("*").eq("id", prop["cluster_id"]).limit(1))
                cluster = crows[0] if crows else None
            issue_url = await _create_github_issue(prop, cluster)

        update = {
            "status": "approved",
            "reviewed_by": payload.reviewer or "anonymous",
            "reviewed_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        if issue_url:
            update["pr_url"] = issue_url   # column is pr_url but stores issue URL too
        _exec(client.table("improvement_proposals").update(update).eq("id", proposal_id))

        return {"ok": True, "status": "approved", "issue_url": issue_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("approve_proposal failed: %s", e)
        raise HTTPException(500, str(e))


@router.patch("/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, payload: RejectRequest):
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        rows = _row_data(client.table("improvement_proposals")
                         .select("status").eq("id", proposal_id).limit(1))
        if not rows:
            raise HTTPException(404, "proposal not found")
        if rows[0].get("status") not in ("pending", "reviewed", "approved"):
            raise HTTPException(409, f"cannot reject from status={rows[0].get('status')}")
        update = {
            "status": "rejected",
            "reviewed_by": payload.reviewer or "anonymous",
            "reviewed_at": _now_iso(),
            "rollback_reason": payload.reason,
            "updated_at": _now_iso(),
        }
        _exec(client.table("improvement_proposals").update(update).eq("id", proposal_id))
        return {"ok": True, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("reject_proposal failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/run")
async def manual_run(payload: ManualRunRequest, bg: BackgroundTasks):
    """Manually trigger one orchestration cycle. Runs in background (returns immediately)."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    try:
        from services.ai_ops_orchestrator import orchestrate_ai_ops
    except ImportError as e:
        raise HTTPException(500, f"orchestrator unavailable: {e}")

    async def _run():
        try:
            summary = await orchestrate_ai_ops(window_days=payload.window_days)
            logger.info("[ai_ops] manual run complete: %s", summary)
        except Exception as e:
            logger.exception("[ai_ops] manual run failed: %s", e)

    bg.add_task(_run)
    return {"ok": True, "status": "scheduled", "window_days": payload.window_days}


@router.get("/pattern-alerts/{symbol}")
async def pattern_alerts(symbol: str, model_type: str = "meta",
                          direction: Optional[str] = None,
                          confidence: Optional[float] = None):
    """Live pattern alerts — winning/toxic mined-rule matches for the current snapshot.
    Used by frontend to render flashing 'trusted setup' / 'caution' indicators."""
    try:
        from services.signal_feature_snapshot import build_signal_feature_snapshot
        from services.pattern_matcher import match_patterns, get_rules_meta
    except ImportError as e:
        raise HTTPException(500, f"matcher unavailable: {e}")
    try:
        snap = await build_signal_feature_snapshot(symbol)
        if not snap:
            return {"available": False, "reason": "snapshot_unavailable", "symbol": symbol}
        # If no direction provided, try both — return alerts that fire either way
        directions = [direction] if direction in ("BUY", "SELL") else ["BUY", "SELL"]
        results: dict = {"symbol": symbol, "model_type": model_type, "by_direction": {}}
        for d in directions:
            results["by_direction"][d] = match_patterns(
                symbol=symbol, model_type=model_type,
                ml_direction=d, ml_confidence=confidence,
                snapshot=snap,
            )
        results["meta"] = get_rules_meta()
        results["available"] = True
        return results
    except Exception as e:
        logger.exception("pattern_alerts failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/pattern-alerts/reload")
async def reload_pattern_rules():
    """Force reload pattern_rules.json (call after running pattern_miner.py again)."""
    try:
        from services.pattern_matcher import reload_rules
        n = reload_rules()
        return {"ok": True, "rules_loaded": n}
    except Exception as e:
        logger.exception("reload_pattern_rules failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/pattern-mining/run")
async def trigger_pattern_mining(bg: BackgroundTasks, days: int = 60):
    """Manually trigger a fresh pattern mining cycle (otherwise weekly cron handles it)."""
    try:
        from services.pattern_mining_service import run_mining_now
    except ImportError as e:
        raise HTTPException(500, f"mining service unavailable: {e}")

    async def _run():
        try:
            summary = await run_mining_now(days=days, triggered_by="manual")
            logger.info("[ai_ops] manual mining run complete: rules=%s",
                        summary.get("rules_count"))
        except Exception as e:
            logger.exception("[ai_ops] manual mining run failed: %s", e)

    bg.add_task(_run)
    return {"ok": True, "status": "scheduled", "days": days,
            "note": "Running in background. ~1-3 minutes to complete; check /pattern-mining/status."}


@router.get("/pattern-mining/status")
async def pattern_mining_status():
    """Frontend status badge — last run, rule count, recent history."""
    try:
        from services.pattern_mining_service import get_status
        return await get_status()
    except Exception as e:
        logger.exception("pattern_mining_status failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/proposals/{proposal_id}/simulate")
async def simulate_proposal_endpoint(proposal_id: str, window_days: int = 60):
    """Re-run counterfactual simulation for a single proposal."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    try:
        from services.proposal_simulator import simulate_and_persist
        result = await simulate_and_persist(proposal_id, window_days=window_days)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.exception("simulate_proposal_endpoint failed: %s", e)
        raise HTTPException(500, str(e))


@router.get("/diagnostic")
async def diagnostic():
    """Self-check — what's wrong with the AI-Ops loop on this deploy?
    Hit this when the dashboard shows 0 proposals after multiple days."""
    from pathlib import Path
    out: dict = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": [],
    }

    # 1) Are the rule files deployed?
    backend_root = Path(__file__).resolve().parent.parent
    pr_path = backend_root / "data" / "pattern_rules.json"
    cr_path = backend_root / "data" / "chart_pattern_rules.json"
    out["checks"].append({
        "name": "pattern_rules_file",
        "ok": pr_path.exists(),
        "path": str(pr_path),
        "size_bytes": pr_path.stat().st_size if pr_path.exists() else 0,
    })
    out["checks"].append({
        "name": "chart_pattern_rules_file",
        "ok": cr_path.exists(),
        "path": str(cr_path),
        "size_bytes": cr_path.stat().st_size if cr_path.exists() else 0,
    })

    # 2) Pattern matcher loads rules?
    try:
        from services.pattern_matcher import _load_rules, get_rules_meta
        rules = _load_rules()
        meta = get_rules_meta()
        out["checks"].append({
            "name": "pattern_matcher_load",
            "ok": len(rules) > 0,
            "rules_loaded": len(rules),
            "meta": meta,
        })
    except Exception as e:
        out["checks"].append({"name": "pattern_matcher_load", "ok": False, "error": str(e)[:200]})

    # 3) Are required Supabase tables/columns present?
    if is_db_available():
        client = get_supabase_client()
        for table, sample_col in [
            ("failure_clusters", "id"),
            ("improvement_proposals", "id"),
            ("pattern_mining_runs", "id"),
            ("failure_analyses", "id"),
            ("prediction_logs", "id"),
        ]:
            try:
                r = client.table(table).select(sample_col).limit(1)
                res = r.execute() if hasattr(r, "execute") else r
                data = res.get("data") if isinstance(res, dict) else getattr(res, "data", None)
                out["checks"].append({
                    "name": f"table:{table}",
                    "ok": True,
                    "has_rows": bool(data),
                })
            except Exception as e:
                out["checks"].append({
                    "name": f"table:{table}",
                    "ok": False,
                    "error": str(e)[:200],
                    "hint": ("Migration not applied. Run "
                             "supabase/migrations/20260430_ai_ops_proposals.sql "
                             "and 20260504_pattern_mining_runs.sql in Supabase SQL Editor.")
                            if "does not exist" in str(e) or "PGRST205" in str(e) else None,
                })
        # Check for simulated_metric column on improvement_proposals
        try:
            r = client.table("improvement_proposals").select("simulated_metric").limit(1)
            res = r.execute() if hasattr(r, "execute") else r
            out["checks"].append({"name": "column:improvement_proposals.simulated_metric", "ok": True})
        except Exception as e:
            out["checks"].append({
                "name": "column:improvement_proposals.simulated_metric",
                "ok": False, "error": str(e)[:200],
                "hint": "Run 20260430_proposal_simulation.sql migration"
                        if "does not exist" in str(e) else None,
            })
        # Check for live_tracking columns
        try:
            r = client.table("improvement_proposals").select("live_tracking_started_at").limit(1)
            res = r.execute() if hasattr(r, "execute") else r
            out["checks"].append({"name": "column:improvement_proposals.live_tracking_*", "ok": True})
        except Exception as e:
            out["checks"].append({
                "name": "column:improvement_proposals.live_tracking_*",
                "ok": False, "error": str(e)[:200],
                "hint": "Run 20260505_proposal_monitoring.sql migration"
                        if "does not exist" in str(e) else None,
            })

    # 4) Recent prediction_logs activity (proves system is producing signals)
    # Counting via fetch+len works on the older safe client wrapper that doesn't
    # accept count="exact" — fetch a bounded sample instead.
    if is_db_available():
        client = get_supabase_client()
        try:
            from datetime import timedelta
            since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            r = client.table("prediction_logs").select("id").gte(
                "created_at", since).limit(5000)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            n = len(data or [])
            out["checks"].append({
                "name": "recent_prediction_logs_7d",
                "ok": n > 0,
                "count_sampled": n,
                "note": "sample bounded at 5000 — actual could be higher" if n == 5000 else None,
                "hint": "If 0, the trading system itself isn't producing signals." if n == 0 else None,
            })
        except Exception as e:
            out["checks"].append({"name": "recent_prediction_logs_7d", "ok": False, "error": str(e)[:200]})

    # 5) Failure tagger — has it ever populated failure_analyses?
    if is_db_available():
        client = get_supabase_client()
        try:
            r = client.table("failure_analyses").select("id").limit(1000)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            n = len(data or [])
            out["checks"].append({
                "name": "failure_analyses_total_rows",
                "ok": n > 0,
                "count_sampled": n,
                "hint": ("Orchestrator hasn't tagged any failures. Likely cause: "
                         "failure_analyses_prediction_id_unique constraint missing — "
                         "UPSERT silently fails. Try clusters and proposals are still "
                         "produced via in-memory clustering, so this is non-blocking, "
                         "but historical tag retrieval will be empty."
                         if n == 0 else None),
            })
        except Exception as e:
            out["checks"].append({"name": "failure_analyses_total_rows", "ok": False, "error": str(e)[:200]})

    # 6) Last orchestrator run? Use most recent failure_clusters.created_at as proxy
    if is_db_available():
        client = get_supabase_client()
        try:
            r = client.table("failure_clusters").select("created_at").order(
                "created_at", desc=True).limit(1)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", None)
            last = data[0]["created_at"] if data else None
            out["checks"].append({
                "name": "orchestrator_last_run",
                "ok": last is not None,
                "last_cluster_created_at": last,
                "hint": "Orchestrator may have never produced a cluster (need 5+ similar fails)." if not last else None,
            })
        except Exception as e:
            out["checks"].append({"name": "orchestrator_last_run", "ok": False, "error": str(e)[:200]})

    # Aggregate verdict
    failed = [c for c in out["checks"] if not c.get("ok")]
    out["overall_status"] = "healthy" if not failed else "issues_detected"
    out["failed_checks"] = len(failed)
    return out


@router.post("/proposals/{proposal_id}/check-live")
async def check_proposal_live_endpoint(proposal_id: str):
    """Manually trigger one live-tracking pass for a single proposal.
    Otherwise the daily cron handles it automatically."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    try:
        from services.post_deploy_monitor import check_proposal
        client = get_supabase_client()
        rows = _row_data(client.table("improvement_proposals").select("*")
                         .eq("id", proposal_id).limit(1))
        if not rows:
            raise HTTPException(404, "proposal not found")
        result = await check_proposal(rows[0])
        return {"ok": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("check_proposal_live failed: %s", e)
        raise HTTPException(500, str(e))


@router.get("/proposals/tracked")
async def list_tracked_proposals():
    """List all proposals currently in live tracking (status=implemented + within 7d)."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        q = client.table("improvement_proposals").select(
            "id,symbol,model_type,severity,root_cause,simulated_metric,"
            "live_tracking_metric,live_tracking_started_at,live_tracking_last_check,"
            "rollback_recommended,rollback_recommendation_reason,reviewed_at"
        ).eq("status", "implemented").gte("live_tracking_started_at", cutoff
        ).order("live_tracking_started_at", desc=True).limit(100)
        return {"tracked": _row_data(q)}
    except Exception as e:
        logger.exception("list_tracked_proposals failed: %s", e)
        raise HTTPException(500, str(e))


@router.get("/tp-sl/recommendations")
async def list_tp_sl_recommendations(
    symbol: Optional[str] = None,
    status: Optional[str] = "pending",
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """Latest TP/SL recommendations from the optimizer."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        q = client.table("tp_sl_recommendations").select("*").order(
            "created_at", desc=True).limit(limit)
        if symbol:
            q = q.eq("symbol", symbol)
        if status:
            q = q.eq("status", status)
        if severity:
            q = q.eq("severity", severity)
        return {"recommendations": _row_data(q)}
    except Exception as e:
        logger.exception("list_tp_sl failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/tp-sl/run")
async def trigger_tp_sl_analysis(bg: BackgroundTasks, days: int = 60,
                                   symbol: Optional[str] = None):
    """Manual trigger — analyze TP/SL for one symbol or all."""
    try:
        from services.tp_sl_optimizer import analyze_tp_sl, analyze_all_combinations
    except ImportError as e:
        raise HTTPException(500, f"tp_sl_optimizer unavailable: {e}")

    async def _run():
        try:
            if symbol:
                for direction in ("BUY", "SELL"):
                    await analyze_tp_sl(symbol, direction=direction, days=days)
            else:
                await analyze_all_combinations(days=days)
        except Exception as e:
            logger.exception("[tp_sl] manual run failed: %s", e)

    bg.add_task(_run)
    return {"ok": True, "status": "scheduled", "days": days, "symbol": symbol or "all"}


@router.patch("/tp-sl/recommendations/{rec_id}/apply")
async def mark_tp_sl_applied(rec_id: str, body: dict):
    """Mark a recommendation as applied. After updating target_config.py manually
    or via PR, hit this endpoint so it stops appearing in pending."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        _exec(client.table("tp_sl_recommendations").update({
            "status": "applied",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": body.get("reviewer") or "user",
            "notes": body.get("notes"),
        }).eq("id", rec_id))
        return {"ok": True}
    except Exception as e:
        logger.exception("mark_tp_sl_applied failed: %s", e)
        raise HTTPException(500, str(e))


@router.patch("/tp-sl/recommendations/{rec_id}/reject")
async def reject_tp_sl(rec_id: str, body: dict):
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        _exec(client.table("tp_sl_recommendations").update({
            "status": "rejected",
            "reviewed_by": body.get("reviewer") or "user",
            "notes": body.get("reason"),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", rec_id))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/clusters")
async def list_clusters(
    symbol: Optional[str] = None,
    model_type: Optional[str] = None,
    sent_to_llm: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Browse raw clusters (without LLM analysis) — useful for debugging."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        q = client.table("failure_clusters").select("*").order(
            "created_at", desc=True).order("sample_size", desc=True).limit(limit)
        if symbol:
            q = q.eq("symbol", symbol)
        if model_type:
            q = q.eq("model_type", model_type)
        if sent_to_llm is not None:
            q = q.eq("sent_to_llm", sent_to_llm)
        return {"clusters": _row_data(q), "count": limit}
    except Exception as e:
        logger.exception("list_clusters failed: %s", e)
        raise HTTPException(500, str(e))
