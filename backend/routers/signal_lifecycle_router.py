"""
Signal Lifecycle API Router
─────────────────────────────
Endpoints for the Learning Dashboard v2:
  - GET  /api/signals/active        → list active signals
  - POST /api/signals/check-now     → manual lifecycle check
  - GET  /api/signals/dashboard     → aggregated model stats
  - GET  /api/signals/detail/{id}   → single signal + checks + failure
  - GET  /api/admin/export-failures → CSV-ready failure dataset
"""
from __future__ import annotations

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["signals"])


# ─── Active Signals ──────────────────────────────────────────────────────────

@router.get("/api/signals/active")
async def get_active_signals():
    """Return all currently active signals."""
    from database.supabase_client import get_supabase_client, is_db_available

    if not is_db_available():
        return {"signals": [], "error": "DB not available"}

    client = get_supabase_client()
    if not client:
        return {"signals": [], "error": "No DB client"}

    try:
        result = client.table("prediction_logs").select(
            "id, symbol, ml_direction, ml_confidence, ml_entry_price, "
            "model_type, strategy, status, targets, targets_hit, "
            "highest_profit_pips, lowest_drawdown_pips, stop_loss_pips, "
            "created_at"
        ).eq("status", "active").order("created_at", desc=True).limit(50).execute()

        signals = result.get("data") or []

        # Parse JSON fields
        import json
        for s in signals:
            for field in ("targets", "targets_hit"):
                val = s.get(field)
                if isinstance(val, str):
                    try:
                        s[field] = json.loads(val)
                    except Exception:
                        pass

        return {"signals": signals, "count": len(signals)}

    except Exception as e:
        logger.error(f"get_active_signals error: {e}")
        return {"signals": [], "error": str(e)}


# ─── Manual Lifecycle Check ──────────────────────────────────────────────────

@router.post("/api/signals/check-now")
async def manual_lifecycle_check():
    """Manually trigger a lifecycle check (same as the 5-min auto check)."""
    from services.signal_lifecycle import run_lifecycle_check

    try:
        summary = await run_lifecycle_check()

        # Broadcast update via WebSocket
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

        return {"success": True, "summary": summary}

    except Exception as e:
        logger.error(f"manual_lifecycle_check error: {e}")
        return {"success": False, "error": str(e)}


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

@router.get("/api/signals/dashboard")
async def get_dashboard(days: int = 30):
    """Return aggregated performance stats per model type for Learning Dashboard v2."""
    from services.signal_lifecycle import get_dashboard_stats

    try:
        stats = await get_dashboard_stats(days=days)
        return stats
    except Exception as e:
        logger.error(f"get_dashboard error: {e}")
        return {"error": str(e)}


# ─── Signal Detail ────────────────────────────────────────────────────────────

@router.get("/api/signals/detail/{signal_id}")
async def get_signal_detail_endpoint(signal_id: str):
    """Return full signal detail: signal info + all 5-min checks + failure autopsy."""
    from services.signal_lifecycle import get_signal_detail

    try:
        detail = await get_signal_detail(signal_id)
        return detail
    except Exception as e:
        logger.error(f"get_signal_detail error: {e}")
        return {"error": str(e)}


# ─── Export Failures (for ML retraining) ──────────────────────────────────────

@router.post("/api/signals/backfill")
async def backfill_existing_records():
    """One-time backfill: set model_type from strategy, expire old active signals."""
    from database.supabase_client import get_supabase_client, is_db_available
    import json

    if not is_db_available():
        return {"error": "DB not available"}

    client = get_supabase_client()
    if not client:
        return {"error": "No DB client"}

    stats = {"model_type_updated": 0, "expired": 0}

    try:
        # Fetch all records missing model_type
        result = client.table("prediction_logs").select(
            "id, strategy, status, created_at, ml_direction, targets, model_type"
        ).limit(500).execute()

        records = result.get("data") or []

        for rec in records:
            updates = {}
            # Backfill model_type
            if not rec.get("model_type") or rec.get("model_type") == "ml":
                strat = (rec.get("strategy") or "").upper()
                if "EMEL" in strat:
                    updates["model_type"] = "emel"
                elif "PULSE" in strat:
                    updates["model_type"] = "pulse"
                else:
                    updates["model_type"] = "ml"

            # Backfill targets if empty
            if not rec.get("targets") or rec.get("targets") in ("{}", "null"):
                from services.target_config import get_symbol_config
                # Need symbol — fetch it
                full = client.table("prediction_logs").select("symbol").eq("id", rec["id"]).execute()
                sym = (full.get("data") or [{}])[0].get("symbol", "NDX.INDX")
                cfg = get_symbol_config(sym)
                targets_dict = {tl.name: tl.pips for tl in cfg.targets}
                updates["targets"] = json.dumps(targets_dict)
                updates["stop_loss_pips"] = cfg.stoploss_pips
                updates["targets_hit"] = json.dumps({tp: False for tp in targets_dict})

            # Expire old active signals (older than 2 hours)
            if rec.get("status") == "active":
                from datetime import datetime, timedelta
                try:
                    created = rec.get("created_at", "")
                    if created:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if (datetime.now(created_dt.tzinfo) - created_dt).total_seconds() > 7200:
                            updates["status"] = "expired"
                            stats["expired"] += 1
                except Exception:
                    updates["status"] = "expired"
                    stats["expired"] += 1

            if updates:
                client.table("prediction_logs").eq("id", rec["id"]).update(updates)
                if "model_type" in updates:
                    stats["model_type_updated"] += 1

        return {"success": True, "total_records": len(records), **stats}

    except Exception as e:
        logger.error(f"backfill error: {e}")
        return {"error": str(e)}


@router.get("/api/signals/metrics")
async def get_lifecycle_metrics():
    """Return lifecycle processing metrics and scheduler state for observability."""
    from services.signal_lifecycle import metrics as lifecycle_metrics
    from database.supabase_client import get_supabase_client, is_db_available

    result = {
        "lifecycle_metrics": lifecycle_metrics.to_dict(),
        "db_available": is_db_available(),
    }

    # Fetch scheduler_state from DB
    client = get_supabase_client()
    if client:
        try:
            state_result = client.table("scheduler_state").select("*").execute()
            jobs = state_result.get("data") or []
            result["scheduler_jobs"] = {j["job_name"]: j for j in jobs}
        except Exception as e:
            result["scheduler_jobs_error"] = str(e)

        # DB connection pool stats
        try:
            result["db_pool"] = client.get_stats()
        except Exception:
            pass

    return result


@router.get("/api/admin/export-failures")
async def export_failures_endpoint(days: int = 30):
    """Export failure records as JSON for ML retraining dataset."""
    from services.signal_lifecycle import export_failures

    try:
        failures = await export_failures(days=days)
        return {
            "count": len(failures),
            "failures": failures,
        }
    except Exception as e:
        logger.error(f"export_failures error: {e}")
        return {"error": str(e)}


@router.post("/api/signals/reset-dashboard")
async def reset_dashboard(confirm: bool = False):
    """
    Reset Signal Performance Dashboard - deletes all non-active (expired/stopped/completed)
    prediction_logs and related records via Supabase REST API.
    Active signals are preserved. Requires confirm=true.
    """
    if not confirm:
        return {
            "error": "Pass confirm=true to actually reset dashboard",
            "warning": "This will delete ALL non-active signal history!",
            "reset": False
        }

    import httpx, os
    from config import settings

    url = settings.supabase_url
    key = settings.supabase_key

    if not url or not key:
        return {"error": "Supabase credentials not configured", "reset": False}

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    base = url.rstrip("/") + "/rest/v1"
    deleted = {}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Get non-active prediction_log IDs
            r = await client.get(
                f"{base}/prediction_logs",
                headers=headers,
                params={"status": "neq.active", "select": "id"}
            )
            ids = [row["id"] for row in (r.json() if isinstance(r.json(), list) else [])]
            deleted["prediction_logs_found"] = len(ids)

            # 2. For each ID delete related records then the log itself
            predictions_deleted = 0
            for pid in ids:
                # Delete signal_checks for this prediction
                await client.delete(
                    f"{base}/signal_checks",
                    headers=headers,
                    params={"prediction_id": f"eq.{pid}"}
                )
                # Delete signal_failures for this prediction
                await client.delete(
                    f"{base}/signal_failures",
                    headers=headers,
                    params={"signal_id": f"eq.{pid}"}
                )
                # Delete the prediction log itself
                dr = await client.delete(
                    f"{base}/prediction_logs",
                    headers=headers,
                    params={"id": f"eq.{pid}"}
                )
                if dr.status_code in (200, 204):
                    predictions_deleted += 1

            # 3. Delete orphaned outcome_results
            or_resp = await client.delete(
                f"{base}/outcome_results",
                headers=headers,
                params={"id": "neq.00000000-0000-0000-0000-000000000000"}
            )
            outcomes_deleted = len(or_resp.json()) if isinstance(or_resp.json(), list) else 0

            # 4. Count remaining active
            ar = await client.get(
                f"{base}/prediction_logs",
                headers=headers,
                params={"status": "eq.active", "select": "id"}
            )
            active_remaining = len(ar.json() if isinstance(ar.json(), list) else [])

        return {
            "reset": True,
            "predictions_deleted": predictions_deleted,
            "outcomes_deleted": outcomes_deleted,
            "active_signals_preserved": active_remaining,
            "message": f"Dashboard reset: {predictions_deleted} signals deleted, {active_remaining} active preserved."
        }

    except Exception as e:
        logger.error(f"Dashboard reset error: {e}")
        return {"error": str(e), "reset": False}

