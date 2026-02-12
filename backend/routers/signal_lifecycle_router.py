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
