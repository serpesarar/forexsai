"""
Meta-Engine Router
API endpoints for the Meta-Intelligence Engine.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Query, UploadFile, File
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta", tags=["Meta-Engine"])


@router.get("/analyze/{symbol}")
async def meta_analyze(
    symbol: str,
    risk_profile: str = Query("balanced", pattern="^(conservative|balanced|aggressive)$"),
    min_confidence: float = Query(45, ge=0, le=100),
):
    """
    Get the meta-analysis signal for a symbol.
    Combines all 6 models into a single high-confidence signal.
    """
    try:
        from services.meta_analysis_engine import get_meta_signal

        signal = await get_meta_signal(
            symbol=symbol,
            risk_profile=risk_profile,
            min_confidence=min_confidence,
        )

        if signal is None:
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "direction": "HOLD",
                    "confidence": 0,
                    "strength": "WEAK",
                    "source_combo": "",
                    "regime": "UNKNOWN",
                    "agreement_ratio": 0,
                    "technical_score": 0,
                    "passed_conditions": [],
                    "model_breakdown": {},
                    "message": "Insufficient model signals available",
                },
            }

        return {
            "success": True,
            "data": asdict(signal),
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Analyze error for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/combinations/{symbol}")
async def meta_combinations(
    symbol: str,
    regime: str = Query("UNKNOWN"),
):
    """
    Get combination performance stats for a symbol.
    Shows which model combinations historically perform best.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"success": False, "error": "No database connection"}

        query = client.table("meta_combination_stats") \
            .select("*") \
            .eq("symbol", symbol) \
            .gte("total_signals", 3) \
            .order("win_rate", desc=True) \
            .limit(20)

        if regime != "UNKNOWN":
            query = query.eq("regime", regime)

        result = query.execute()
        rows = result.get("data", []) if isinstance(result, dict) else (result.data if hasattr(result, "data") else [])

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "regime": regime,
                "combinations": rows or [],
                "total_combos": len(rows or []),
            },
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Combinations error for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/dashboard")
async def meta_dashboard():
    """
    Get meta-analysis summary for all 4 symbols.
    Returns a compact overview for the dashboard panel.
    """
    try:
        from services.meta_analysis_engine import get_meta_dashboard
        data = await get_meta_dashboard()
        return {
            "success": True,
            "data": data,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Dashboard error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/backfill")
async def meta_backfill():
    """
    Run historical backfill to populate combination stats
    from existing prediction_logs data.
    Should be called once to initialize the learning system.
    """
    try:
        from services.meta_signal_logger import backfill_combination_stats
        result = await backfill_combination_stats()
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Backfill error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/history")
async def meta_history(
    symbol: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get recent meta-signal history.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"success": False, "error": "No database connection"}

        query = client.table("meta_signals") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit)

        if symbol:
            query = query.eq("symbol", symbol)

        result = query.execute()
        rows = result.get("data", []) if isinstance(result, dict) else (result.data if hasattr(result, "data") else [])

        return {
            "success": True,
            "data": rows or [],
            "count": len(rows or []),
        }
    except Exception as e:
        logger.error(f"[MetaRouter] History error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/audit")
async def meta_audit():
    """
    Trigger the Combinatorial Auditor cycle to scan logs
    and update the meta combinations stats.
    """
    try:
        from services.combinatorial_auditor import run_audit_cycle
        result = await run_audit_cycle()
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Audit trigger error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/import-mt5")
async def import_mt5_history(
    file: UploadFile = File(...),
    tolerance: int = Query(90, ge=10, le=600),
):
    """
    Upload and match an MT5 HTML/CSV report.
    Matches trades with database prediction logs and updates ground truth data.
    """
    try:
        content_bytes = await file.read()
        
        # Robust multi-encoding byte decoder (safeguard for UTF-16LE generated by MT5 on Windows)
        content = None
        
        # 1. Try detecting UTF-16 BOM
        if content_bytes.startswith(b'\xff\xfe') or content_bytes.startswith(b'\xfe\xff'):
            try:
                content = content_bytes.decode("utf-16")
                logger.info("Successfully decoded MT5 report using UTF-16 BOM.")
            except Exception:
                pass
                
        # 2. Try common encodings in sequence
        if not content:
            for enc in ["utf-16", "utf-8", "windows-1254", "iso-8859-9", "windows-1252", "latin-1"]:
                try:
                    decoded = content_bytes.decode(enc)
                    # Heuristic: if utf-16 is tried on ascii file, it will have massive null bytes, skip
                    if enc == "utf-16" and decoded.count("\x00") > len(decoded) * 0.3:
                        continue
                    content = decoded
                    logger.info(f"Successfully decoded MT5 report using encoding: {enc}")
                    break
                except Exception:
                    continue
                    
        # 3. Last resort fallback
        if not content:
            content = content_bytes.decode("utf-8", errors="ignore")
            logger.warning("All MT5 report decoders failed. Using fallback UTF-8 with ignore flag.")
            
        from services.mt5_report_matcher import MT5ReportMatcher
        matcher = MT5ReportMatcher()
        
        trades = []
        filename = file.filename.lower()
        if filename.endswith(".csv"):
            trades = matcher.parse_csv_report(content)
        elif filename.endswith(".html") or filename.endswith(".htm"):
            trades = matcher.parse_html_report(content)
        else:
            return {"success": False, "error": "Invalid file format. Please upload .html or .csv report."}

        if not trades:
            return {"success": False, "error": "No trades parsed from the uploaded report. Verify format."}

        result = await matcher.match_and_sync_trades(trades, tolerance_seconds=tolerance)
        return result
    except Exception as e:
        logger.error(f"[MetaRouter] MT5 history import failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/run-backtest")
async def meta_run_backtest(
    days: int = Query(45, ge=1, le=180),
):
    """
    Trigger the offline combinatorial backtest over the selected days.
    """
    try:
        from services.combinatorial_auditor import run_audit_cycle
        result = await run_audit_cycle()
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Backtest trigger error: {e}")
        return {"success": False, "error": str(e)}
