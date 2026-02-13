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


@router.get("/api/signals/debug-lifecycle")
async def debug_lifecycle():
    """Debug endpoint: manually replicate what run_lifecycle_check does to find the issue."""
    from database.supabase_client import get_supabase_client, is_db_available

    debug = {"db_available": is_db_available()}
    client = get_supabase_client()
    debug["client_ok"] = client is not None

    if not client:
        return debug

    try:
        result = client.table("prediction_logs").select("*").eq(
            "status", "active"
        ).order("created_at", desc=True).limit(100).execute()

        debug["raw_result_type"] = str(type(result))
        debug["raw_result_keys"] = list(result.keys()) if isinstance(result, dict) else "not_dict"
        debug["data_type"] = str(type(result.get("data"))) if isinstance(result, dict) else None
        data = result.get("data") or []
        debug["signal_count"] = len(data) if isinstance(data, list) else "not_list"
        if data and isinstance(data, list) and len(data) > 0:
            debug["first_signal_keys"] = list(data[0].keys()) if isinstance(data[0], dict) else str(type(data[0]))
            debug["first_signal_id"] = data[0].get("id", "?") if isinstance(data[0], dict) else None
            debug["first_signal_status"] = data[0].get("status", "?") if isinstance(data[0], dict) else None
        debug["error"] = result.get("error")
    except Exception as e:
        debug["exception"] = str(e)
        import traceback
        debug["traceback"] = traceback.format_exc()

    return debug


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
