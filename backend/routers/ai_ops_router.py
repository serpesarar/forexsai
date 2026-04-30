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

def _row_data(result: Any) -> list[dict]:
    if isinstance(result, dict):
        return result.get("data") or []
    return getattr(result, "data", None) or []


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
        rows = _row_data(client.table("improvement_proposals")
                         .select("status,severity").limit(2000))
        for r in rows:
            s = r.get("status") or "unknown"
            sev = r.get("severity") or "unknown"
            out["by_status"][s] = out["by_status"].get(s, 0) + 1
            out["by_severity"][sev] = out["by_severity"].get(sev, 0) + 1
        out["total"] = len(rows)
        clusters_total = _row_data(client.table("failure_clusters").select("id").limit(1))
        out["clusters_total"] = len(_row_data(client.table("failure_clusters")
                                              .select("id").limit(2000)))
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
            "pre_change_metric,post_change_metric,reviewed_by,reviewed_at,"
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
        rows = _row_data(q)
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
        client.table("improvement_proposals").update(update).eq("id", proposal_id)

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
        client.table("improvement_proposals").update(update).eq("id", proposal_id)
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
