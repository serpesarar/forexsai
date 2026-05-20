"""
MT5 reconciliation endpoints.
Upload MT5 deal exports (JSON/CSV/HTML), reconcile against prediction_logs,
and view the divergence report.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from services.mt5_reconciliation_service import (
    ingest_deals, parse_upload, reconcile_window, reconciliation_report,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mt5", tags=["MT5 Reconciliation"])


@router.post("/upload-deals")
async def upload_deals(file: UploadFile = File(...)):
    """Upload an MT5 export. Accepts:
      - JSON (output of backend/scripts/mt5_export_deals.py)
      - CSV/TSV (MT5 "Save as Report — CSV")
      - HTML (MT5 "Save as Report — Detailed Report")
    Ingests into mt5_trades (dedupes via UNIQUE ticket+entry_type)."""
    try:
        content = await file.read()
        meta, rows = parse_upload(content, filename=file.filename or "")
        if not rows:
            raise HTTPException(400, "No deals parsed — check file format")
        ingest = await ingest_deals(rows)
        return {
            "ok": True,
            "meta": meta,
            "rows_parsed": len(rows),
            "ingest": ingest,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("mt5 upload failed: %s", e)
        raise HTTPException(500, f"Upload failed: {str(e)[:200]}")


@router.post("/reconcile")
async def reconcile(days: int = Query(14, ge=1, le=90),
                     tolerance_seconds: int = Query(90, ge=10, le=600)):
    """Match unmatched MT5 deals to prediction_logs by symbol+direction+time.
    Idempotent — only updates deals where matched_prediction_id IS NULL."""
    return await reconcile_window(days=days, time_tolerance_seconds=tolerance_seconds)


@router.get("/reconciliation/report")
async def report(days: int = Query(7, ge=1, le=90)):
    """Per-symbol divergence: MT5 actual profit vs match rate vs our claimed pips."""
    return await reconciliation_report(days)
