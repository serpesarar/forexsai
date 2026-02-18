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


@router.get("/api/signals/test-pulse-log")
async def test_pulse_log(symbol: str = "GDAXI.INDX", model_type: str = "pulse2"):
    """Diagnostic: manually attempt to create a pulse signal and return detailed result."""
    import traceback
    steps = []
    try:
        from routers.emel_pulse import get_pulse_v3_analysis, get_pulse_ml_analysis, get_pulse_analysis, get_emel_analysis

        # Step 1: Get analysis
        if model_type == "pulse3":
            result = await get_pulse_v3_analysis(symbol)
            sig_key = "direction"
        elif model_type == "pulse2":
            result = await get_pulse_ml_analysis(symbol)
            sig_key = "signal"
        elif model_type == "pulse1":
            result = await get_pulse_analysis(symbol)
            sig_key = "signal"
        elif model_type == "emel":
            result = await get_emel_analysis(symbol)
            sig_key = "signal"
        else:
            return {"error": f"Unknown model_type: {model_type}"}

        steps.append({"step": "analysis", "result_keys": list(result.keys()) if isinstance(result, dict) else str(type(result))})

        if not isinstance(result, dict):
            return {"error": "Result not dict", "steps": steps, "result_type": str(type(result))}

        sig = result.get(sig_key, "HOLD")
        steps.append({"step": "signal", "sig_key": sig_key, "sig": sig})

        if sig not in ("BUY", "SELL"):
            return {"skipped": f"Signal is {sig}, not BUY/SELL", "steps": steps}

        # Step 2: Extract price
        entry = result.get("entry_price")
        price_field = result.get("price")
        if not entry:
            if isinstance(price_field, dict):
                entry = price_field.get("current", 0)
            else:
                entry = price_field
        steps.append({"step": "price", "entry": entry, "price_field_type": str(type(price_field)), "entry_type": str(type(entry))})

        if not entry or not isinstance(entry, (int, float)) or entry <= 0:
            return {"error": "No valid entry price", "steps": steps}

        conf = result.get("confidence", 50) or 50
        steps.append({"step": "confidence", "conf": conf})

        # Step 3: Try log_prediction directly (inline for debugging)
        from database.supabase_client import get_supabase_client, is_db_available
        from services.prediction_logger import _has_active_signal
        import json as _json

        client = get_supabase_client()
        if not client:
            steps.append({"step": "error", "error": "No DB client"})
            return {"error": "No DB client", "steps": steps}

        has_active = _has_active_signal(client, symbol, model_type)
        steps.append({"step": "active_check", "has_active": has_active, "model_type": model_type})
        if has_active:
            return {"blocked": "Active signal exists", "steps": steps}

        from services.target_config import get_symbol_config, calculate_target_prices, calculate_stoploss_price
        cfg = get_symbol_config(symbol)
        target_prices = calculate_target_prices(entry, sig, symbol)
        sl_price = calculate_stoploss_price(entry, sig, symbol)
        targets_dict = target_prices
        targets_dict["SL"] = round(sl_price, 4)
        steps.append({"step": "targets", "targets": targets_dict, "sl_pips": cfg.stoploss_pips})

        record = {
            "symbol": symbol,
            "timeframe": "5m",
            "ml_direction": sig,
            "ml_confidence": float(conf),
            "ml_entry_price": entry,
            "status": "active",
            "targets": _json.dumps(targets_dict),
            "stop_loss_pips": cfg.stoploss_pips,
            "targets_hit": _json.dumps({tp: False for tp in targets_dict if tp != "SL"}),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "model_type": model_type,
            "strategy": f"TEST_{model_type.upper()}",
            "factors": {},
        }
        steps.append({"step": "record_built", "record_keys": list(record.keys())})

        try:
            # Direct HTTP to capture full Supabase error
            url = f"{client.url}/rest/v1/prediction_logs"
            headers = {"Prefer": "return=representation"}
            resp = client.http.post(url, json=record, headers=headers)
            steps.append({
                "step": "raw_response",
                "status_code": resp.status_code,
                "body": resp.text[:500],
            })
            if resp.status_code in (200, 201):
                data = resp.json()
                new_id = data[0].get("id", "") if isinstance(data, list) and data else ""
                return {"success": True, "pred_id": new_id, "steps": steps}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}", "steps": steps}
        except Exception as insert_err:
            steps.append({"step": "insert_error", "error": str(insert_err), "traceback": traceback.format_exc()})
            return {"error": str(insert_err), "steps": steps}

    except Exception as e:
        steps.append({"step": "error", "error": str(e), "traceback": traceback.format_exc()})
        return {"error": str(e), "steps": steps}


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
