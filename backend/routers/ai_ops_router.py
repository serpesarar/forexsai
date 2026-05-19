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
    auto_decision: Optional[str] = Query(None, description="auto_apply|human_review|auto_reject"),
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
            "auto_decision,auto_decision_reason,auto_decided_at,auto_implemented_pr_url,"
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
        if auto_decision:
            q = q.eq("auto_decision", auto_decision)
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
# Multiple common env var names — Railway / .env / shell may use any of these
GITHUB_TOKEN_ENV_NAMES = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_API_TOKEN")


def _resolve_github_token() -> tuple[Optional[str], str]:
    """Walk through accepted env var names, return (token, source_name)."""
    for name in GITHUB_TOKEN_ENV_NAMES:
        v = os.environ.get(name)
        if v and v.strip():
            return v.strip(), name
    return None, ""


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


async def _create_github_issue(prop: dict, cluster: Optional[dict]) -> dict:
    """Create a GitHub issue describing the proposal. Returns:
        {ok: True, url: str}                       on success
        {ok: False, reason: str, detail: str}      on failure (so caller can surface to UI)
    """
    token, token_source = _resolve_github_token()
    if not token:
        return {"ok": False, "reason": "no_token",
                "detail": f"None of the env vars {list(GITHUB_TOKEN_ENV_NAMES)} are set on the backend. "
                          f"Add GITHUB_TOKEN to Railway service env vars (not just .env) and redeploy."}
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
            url = r.json().get("html_url")
            return {"ok": True, "url": url, "token_source": token_source}
        logger.warning("[ai-ops] github issue create failed: %s %s", r.status_code, r.text[:300])
        # Decode common GitHub errors
        api_err = ""
        try:
            api_err = r.json().get("message", "")
        except Exception:
            api_err = r.text[:200]
        reason = "github_api_error"
        if r.status_code == 401:
            reason = "token_invalid_or_expired"
        elif r.status_code == 403:
            reason = "token_lacks_issues_write_permission"
        elif r.status_code == 404:
            reason = "repo_not_found_or_token_no_access"
        elif r.status_code == 422:
            reason = "github_validation_error"
        return {"ok": False, "reason": reason, "detail": f"{r.status_code}: {api_err}",
                "repo": GITHUB_REPO, "token_source": token_source}
    except Exception as e:
        logger.exception("[ai-ops] github call failed: %s", e)
        return {"ok": False, "reason": "network_error", "detail": str(e)[:200]}


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
        issue_url: Optional[str] = None
        github_error: Optional[dict] = None
        if payload.create_github_issue:
            cluster = None
            if prop.get("cluster_id"):
                crows = _row_data(client.table("failure_clusters")
                                  .select("*").eq("id", prop["cluster_id"]).limit(1))
                cluster = crows[0] if crows else None
            gh_result = await _create_github_issue(prop, cluster)
            if gh_result.get("ok"):
                issue_url = gh_result.get("url")
            else:
                github_error = gh_result

        update = {
            "status": "approved",
            "reviewed_by": payload.reviewer or "anonymous",
            "reviewed_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        if issue_url:
            update["pr_url"] = issue_url   # column is pr_url but stores issue URL too
        # The project's supabase wrapper requires .eq() BEFORE .update() (custom
        # API differs from supabase-py upstream). Order is critical.
        _exec(client.table("improvement_proposals").eq("id", proposal_id).update(update))

        return {
            "ok": True, "status": "approved",
            "issue_url": issue_url,
            "github_error": github_error,   # surfaces to UI when issue creation fails
        }
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
        _exec(client.table("improvement_proposals").eq("id", proposal_id).update(update))
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


@router.post("/proposals/{proposal_id}/discriminator-analysis")
async def discriminator_analysis_endpoint(proposal_id: str, window_days: int = 60):
    """Deep-dive: for a filter proposal that blocks both fails AND wins, find
    the features that distinguish them. Returns ranked discriminators + a
    refined filter recommendation that rescues winning signals."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    try:
        from services.filter_discriminator import analyze_discriminators
        result = await analyze_discriminators(proposal_id, days=window_days)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.exception("discriminator_analysis failed: %s", e)
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


@router.post("/auto-triage/run")
async def trigger_auto_triage(bg: BackgroundTasks, limit: int = 500):
    """Manually run auto-triage on all untriaged pending proposals.
    Otherwise the 6h cron handles it."""
    try:
        from services.ai_ops_auto_triage import run_full_triage
    except ImportError as e:
        raise HTTPException(500, f"auto-triage unavailable: {e}")

    async def _run():
        try:
            summary = await run_full_triage(limit=limit)
            logger.info("[ai-ops] manual auto-triage complete: %s", summary)
        except Exception as e:
            logger.exception("[ai-ops] manual auto-triage failed: %s", e)

    bg.add_task(_run)
    return {"ok": True, "status": "scheduled",
            "note": "Triage runs in background — 1-3 min depending on queue size. "
                    "Pending proposals will get auto_decision values populated. "
                    "Auto-rejected proposals also flip status to 'rejected'."}


@router.get("/auto-triage/stats")
async def auto_triage_stats():
    """Counts by auto_decision so the dashboard can show triage outcome."""
    if not is_db_available():
        return {"available": False}
    client = get_supabase_client()
    out: dict = {"available": True, "counts": {}}
    try:
        q = client.table("improvement_proposals").select(
            "auto_decision,status").limit(5000)
        res = q.execute() if hasattr(q, "execute") else q
        rows = (res.get("data") if isinstance(res, dict)
                else getattr(res, "data", None)) or []
        for r in rows:
            d = r.get("auto_decision") or "untriaged"
            out["counts"][d] = out["counts"].get(d, 0) + 1
        out["total"] = len(rows)
    except Exception as e:
        logger.exception("auto_triage_stats failed: %s", e)
        out["error"] = str(e)
    return out


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

    # 7) GitHub token presence (proposal approval needs this)
    token, token_source = _resolve_github_token()
    out["checks"].append({
        "name": "github_token",
        "ok": bool(token),
        "found_in_env": token_source if token else None,
        "scanned_env_names": list(GITHUB_TOKEN_ENV_NAMES),
        "repo_target": GITHUB_REPO,
        "hint": ("None of the scanned env vars are populated on this Railway service. "
                 "Even if you set GITHUB_TOKEN in your local .env file, Railway needs "
                 "it set as a SERVICE ENV VAR (Railway dashboard → Variables tab). "
                 "After setting it, hit 'Redeploy' so the new env var is in process scope."
                 if not token else None),
    })

    # 8) DeepSeek key presence (proposal generation needs this)
    deep_key = os.environ.get("DEEP_SEEKR1") or os.environ.get("DEEPSEEK_API_KEY")
    out["checks"].append({
        "name": "deepseek_api_key",
        "ok": bool(deep_key),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        "scanned_env_names": ["DEEP_SEEKR1", "DEEPSEEK_API_KEY"],
        "hint": "Set DEEP_SEEKR1 (or DEEPSEEK_API_KEY) on Railway." if not deep_key else None,
    })

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
        # Custom wrapper requires .eq() BEFORE .update() — .update() auto-executes
        client.table("tp_sl_recommendations").eq("id", rec_id).update({
            "status": "applied",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": body.get("reviewer") or "user",
            "notes": body.get("notes"),
        })
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
        client.table("tp_sl_recommendations").eq("id", rec_id).update({
            "status": "rejected",
            "reviewed_by": body.get("reviewer") or "user",
            "notes": body.get("reason"),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/coverage-stats")
async def coverage_stats(days: int = 7):
    """Why does symbol X have few/no proposals? This breaks down the raw
    funnel so the user can see WHERE coverage drops:
        signals → resolved → failures → factor-rich → clusters → proposals
    For each symbol in the last `days` window."""
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    from datetime import timedelta
    since_iso = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    out: dict[str, Any] = {"window_days": days, "since": since_iso, "symbols": {}}

    SYMBOLS = ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
    try:
        for sym in SYMBOLS:
            # Bounded sampling — we just need counts, not full content
            q = client.table("prediction_logs").select(
                "id,status,model_type,factors"
            ).eq("symbol", sym).gte("created_at", since_iso).limit(10000)
            res = q.execute() if hasattr(q, "execute") else q
            rows = (res.get("data") if isinstance(res, dict)
                    else getattr(res, "data", None)) or []
            total = len(rows)
            resolved = sum(1 for r in rows if r.get("status") in ("completed", "stopped"))
            failures = sum(1 for r in rows if r.get("status") == "stopped")
            # How many failures have rich snapshot factors? (key indicator)
            factor_rich = 0
            for r in rows:
                if r.get("status") != "stopped":
                    continue
                f = r.get("factors")
                if isinstance(f, str):
                    try:
                        import json as _json
                        f = _json.loads(f)
                    except Exception:
                        f = {}
                if isinstance(f, dict) and (
                    f.get("regime_label") or f.get("M30_rsi_14") is not None
                    or f.get("sar_bearish") is not None
                ):
                    factor_rich += 1
            # Model breakdown
            from collections import Counter
            by_model = Counter(r.get("model_type") for r in rows)

            # Clusters for this symbol
            cq = client.table("failure_clusters").select("id,sample_size,model_type").eq(
                "symbol", sym).limit(500)
            cres = cq.execute() if hasattr(cq, "execute") else cq
            crows = (cres.get("data") if isinstance(cres, dict)
                     else getattr(cres, "data", None)) or []
            clusters_total = len(crows)
            clusters_meeting_threshold = sum(1 for c in crows if (c.get("sample_size") or 0) >= 5)

            # Proposals for this symbol
            pq = client.table("improvement_proposals").select("id,status").eq(
                "symbol", sym).limit(500)
            pres = pq.execute() if hasattr(pq, "execute") else pq
            prows = (pres.get("data") if isinstance(pres, dict)
                     else getattr(pres, "data", None)) or []
            proposals_total = len(prows)
            proposals_pending = sum(1 for p in prows if p.get("status") == "pending")

            out["symbols"][sym] = {
                "signals_total": total,
                "resolved": resolved,
                "failures": failures,
                "win_rate_pct": (round((resolved - failures) / resolved * 100, 1)
                                  if resolved > 0 else None),
                "factor_rich_failures": factor_rich,
                "factor_coverage_pct": (round(factor_rich / failures * 100, 1)
                                         if failures > 0 else None),
                "by_model_signals": dict(by_model.most_common(10)),
                "clusters_total": clusters_total,
                "clusters_meeting_5plus": clusters_meeting_threshold,
                "proposals_total": proposals_total,
                "proposals_pending": proposals_pending,
                # Diagnostic interpretation
                "bottleneck": _diagnose_bottleneck(
                    total, failures, factor_rich, clusters_meeting_threshold, proposals_total
                ),
            }
    except Exception as e:
        logger.exception("coverage_stats failed: %s", e)
        out["error"] = str(e)
    return out


def _diagnose_bottleneck(signals: int, fails: int, factor_rich: int,
                          clusters: int, proposals: int) -> str:
    """Identify WHERE the funnel breaks for a symbol."""
    if signals == 0:
        return "no_signals — symbol not generating any predictions in this window"
    if fails == 0:
        return "no_failures — model is winning everything (rare; verify outcome_results)"
    if factor_rich == 0:
        return "no_factor_coverage — snapshot enrichment not producing readable factors for this symbol"
    if factor_rich < 5:
        return f"only {factor_rich} factor-rich failures — below cluster threshold (need ≥5)"
    if clusters == 0:
        return "failures don't cluster — each failure has a unique signature (no repeated patterns)"
    if proposals == 0:
        return "clusters exist but no proposals — DeepSeek call may be failing"
    return "healthy — funnel producing proposals"


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


@router.get("/outcome-audit/{symbol}")
async def outcome_audit(symbol: str, days: int = Query(30, ge=1, le=365)):
    """
    Diagnostic: inspect raw outcome_results for a symbol to surface P/L
    recording bugs (e.g. USOIL 98% win-rate with 0 total pips).

    Joins prediction_logs (status=completed|stopped) with outcome_results and
    reports MFE/MAE distribution, zero-counts, and a health verdict.
    """
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Symbol normalization — prediction_logs may use bare form (USOIL)
        # while proposals/config use suffixed form (USOIL.FOREX).
        variants = {symbol}
        if "." in symbol:
            variants.add(symbol.split(".")[0])
        else:
            variants.add(f"{symbol}.FOREX")
            variants.add(f"{symbol}.INDX")

        preds: list[dict] = []
        matched_symbol = None
        for variant in variants:
            rows = _row_data(
                client.table("prediction_logs")
                .select(
                    "id, symbol, model_type, ml_direction, status, "
                    "ml_entry_price, exit_price, highest_profit_pips, "
                    "lowest_drawdown_pips, targets_hit, created_at"
                )
                .eq("symbol", variant)
                .gte("created_at", since)
                .limit(5000)
            )
            rows = [r for r in rows if r.get("status") in ("completed", "stopped")]
            if rows:
                preds = rows
                matched_symbol = variant
                break

        if not preds:
            # Debug: list statuses for this symbol (no status filter)
            all_rows = _row_data(
                client.table("prediction_logs")
                .select("symbol, status, model_type")
                .eq("symbol", symbol)
                .gte("created_at", since)
                .limit(5000)
            )
            status_counts: dict[str, int] = {}
            model_counts: dict[str, int] = {}
            for r in all_rows:
                s = r.get("status") or "null"
                m = r.get("model_type") or "null"
                status_counts[s] = status_counts.get(s, 0) + 1
                model_counts[m] = model_counts.get(m, 0) + 1
            sample_symbols = _row_data(
                client.table("prediction_logs")
                .select("symbol")
                .gte("created_at", since)
                .limit(500)
            )
            distinct = sorted({r.get("symbol") for r in sample_symbols if r.get("symbol")})
            return {
                "symbol": symbol,
                "tried_variants": sorted(variants),
                "days": days,
                "n_signals": 0,
                "health": "no_resolved_signals",
                "distinct_symbols_in_window": distinct,
                "status_breakdown_for_symbol": status_counts,
                "model_breakdown_for_symbol": model_counts,
                "total_rows_for_symbol_any_status": len(all_rows),
            }

        # P/L lives ON prediction_logs (not in legacy outcome_results table).
        # signal_lifecycle.py writes highest_profit_pips/lowest_drawdown_pips
        # directly to the row when it transitions status to completed/stopped.
        outcomes: dict[str, dict] = {
            p["id"]: {
                "signal_id": p["id"],
                "outcome": p.get("status"),
                "highest_profit_pips": p.get("highest_profit_pips"),
                "lowest_drawdown_pips": p.get("lowest_drawdown_pips"),
                "exit_price": p.get("exit_price"),
            }
            for p in preds
        }
        outcome_total_in_window = len(outcomes)

        n = len(preds)
        matched = sum(1 for p in preds if p["id"] in outcomes)
        unmatched = n - matched
        mfe_zero = 0
        mae_zero = 0
        mfe_values: list[float] = []
        mae_values: list[float] = []
        wins = 0
        losses = 0
        total_mfe = 0.0
        total_mae = 0.0
        samples: list[dict] = []
        for p in preds:
            o = outcomes.get(p["id"])
            if not o:
                continue
            mfe = float(o.get("highest_profit_pips") or 0)
            mae = float(o.get("lowest_drawdown_pips") or 0)
            mfe_values.append(mfe)
            mae_values.append(mae)
            if mfe == 0:
                mfe_zero += 1
            if mae == 0:
                mae_zero += 1
            total_mfe += mfe
            total_mae += mae
            if p["status"] == "completed":
                wins += 1
            elif p["status"] == "stopped":
                losses += 1
            if len(samples) < 10:
                samples.append({
                    "signal_id": p["id"],
                    "model_type": p["model_type"],
                    "direction": p.get("ml_direction"),
                    "status": p["status"],
                    "entry_price": p.get("ml_entry_price"),
                    "exit_price": o.get("exit_price"),
                    "outcome": o.get("outcome"),
                    "mfe_pips": mfe,
                    "mae_pips": mae,
                })

        wr = (wins / matched * 100.0) if matched else None
        avg_mfe = (total_mfe / matched) if matched else None
        avg_mae = (total_mae / matched) if matched else None
        net = total_mfe + total_mae  # mae is negative-ish

        # Health verdict — surfaces the USOIL bug
        if matched == 0:
            health = "no_outcome_rows"
        elif mfe_zero == matched and mae_zero == matched:
            health = "BUG_all_zero"
        elif wr is not None and wr >= 70 and abs(net) < 1.0:
            health = "BUG_high_winrate_zero_pnl"
        elif unmatched > matched:
            health = "WARN_mostly_unmatched"
        else:
            health = "ok"

        return {
            "symbol": symbol,
            "matched_symbol": matched_symbol,
            "days": days,
            "outcome_rows_in_window_all_symbols": outcome_total_in_window,
            "n_signals": n,
            "matched_outcomes": matched,
            "unmatched": unmatched,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": wr,
            "mfe_zero_count": mfe_zero,
            "mae_zero_count": mae_zero,
            "avg_mfe_pips": avg_mfe,
            "avg_mae_pips": avg_mae,
            "total_mfe_pips": total_mfe,
            "total_mae_pips": total_mae,
            "net_pips": net,
            "health": health,
            "samples": samples,
        }
    except Exception as e:
        logger.exception("outcome_audit failed: %s", e)
        raise HTTPException(500, str(e))


@router.get("/trajectory/stats")
async def trajectory_stats(days: int = Query(7, ge=1, le=90)):
    """
    Diagnostic: how is the Post-Entry Trajectory Learner (PETL) doing?
    Counts trajectory snapshots, deterioration alerts, aborts triggered,
    and estimated pips saved by aborts. Per-symbol breakdown.
    """
    if not is_db_available():
        raise HTTPException(503, "supabase unavailable")
    client = get_supabase_client()
    try:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        snaps = _row_data(
            client.table("signal_trajectory_snapshots")
            .select("symbol, deteriorating, deterioration_score, captured_at")
            .gte("captured_at", since).limit(20000)
        )
        aborts = _row_data(
            client.table("signal_aborts")
            .select("symbol, abort_source, pnl_at_abort_pips, saved_pips_estimate, created_at")
            .gte("created_at", since).limit(5000)
        )

        by_symbol: dict[str, dict] = {}
        for s in snaps:
            sym = s.get("symbol") or "unknown"
            entry = by_symbol.setdefault(sym, {
                "snapshots": 0, "deteriorating": 0, "aborts": 0,
                "saved_pips": 0.0, "abort_pnl_pips": 0.0,
            })
            entry["snapshots"] += 1
            if s.get("deteriorating"):
                entry["deteriorating"] += 1
        for a in aborts:
            sym = a.get("symbol") or "unknown"
            entry = by_symbol.setdefault(sym, {
                "snapshots": 0, "deteriorating": 0, "aborts": 0,
                "saved_pips": 0.0, "abort_pnl_pips": 0.0,
            })
            entry["aborts"] += 1
            entry["saved_pips"] += float(a.get("saved_pips_estimate") or 0)
            entry["abort_pnl_pips"] += float(a.get("pnl_at_abort_pips") or 0)

        # Round and sort
        for sym, e in by_symbol.items():
            e["saved_pips"] = round(e["saved_pips"], 1)
            e["abort_pnl_pips"] = round(e["abort_pnl_pips"], 1)
            e["deterioration_rate_pct"] = (
                round(e["deteriorating"] / e["snapshots"] * 100, 2)
                if e["snapshots"] else 0
            )

        return {
            "window_days": days,
            "total_snapshots": len(snaps),
            "total_aborts": len(aborts),
            "by_symbol": by_symbol,
        }
    except Exception as e:
        logger.exception("trajectory_stats failed: %s", e)
        raise HTTPException(500, str(e))
