"""
MT5 reconciliation endpoints.
Upload MT5 deal exports (JSON/CSV/HTML), reconcile against prediction_logs,
and view the divergence report.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from services.mt5_reconciliation_service import (
    ingest_deals, parse_upload, reconcile_window, reconciliation_report,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mt5", tags=["MT5 Reconciliation"])

# MT5 broker symbol → ForexSAI canonical symbol. Mirrors the mapping in
# services/mt5_reconciliation_service.py so the replay operation lines up
# with the prediction_logs naming.
SYMBOL_NORMALIZATION = {
    "XAUUSD": "XAUUSD",
    "USTEC": "NDX.INDX",
    "DE40": "GDAXI.INDX",
    "XTIUSD": "USOIL.FOREX",
}


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


@router.post("/upload-1m-bars")
async def upload_1m_bars(
    file: UploadFile = File(...),
    broker_utc_offset_hours: float = Query(
        None,
        description=(
            "Hours to subtract from each bar's `t` so candle_cache stores TRUE UTC. "
            "MT5 returns time as unix-seconds-treated-as-broker-local, so the bar "
            "labeled t=22:01 on a UTC+3 broker is actually 19:01 UTC. "
            "If omitted, falls back to env MT5_BROKER_UTC_OFFSET_HOURS (default 3)."
        ),
    ),
):
    """Bulk-ingest 1m MT5 bars into candle_cache for the recovery operation.

    Payload format — output of backend/scripts/mt5_export_1m_bars.py:
        {
          "timeframe": "1m",
          "symbols": {
            "XAUUSD": {"count": N, "bars": [{"t":sec,"o":..,"h":..,"l":..,"c":..,"v":..}, ...]},
            "USTEC":  {...}, "DE40": {...}, "XTIUSD": {...}
          }
        }

    Each MT5 symbol is normalized to ForexSAI canonical before upsert so
    the replay engine joins cleanly against prediction_logs.symbol values.
    """
    try:
        raw = await file.read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            raise HTTPException(400, "Body is not valid JSON")

        # Accept BOTH payload shapes:
        #   1) Combined export: {"symbols": {"XAUUSD": {"bars":[...]}, ...}}
        #   2) Per-symbol export: {"symbol": "XAUUSD", "bars": [...]}
        symbols_block = data.get("symbols")
        if not symbols_block:
            single_sym = data.get("symbol")
            single_bars = data.get("bars")
            if single_sym and isinstance(single_bars, list):
                symbols_block = {single_sym: {"bars": single_bars,
                                                "count": len(single_bars)}}
        if not symbols_block:
            raise HTTPException(400, "No 'symbols' block or top-level 'symbol/bars' in payload")

        # Broker timezone shift — convert MT5's "broker-local-as-unix" to true UTC.
        if broker_utc_offset_hours is None:
            try:
                broker_utc_offset_hours = float(os.getenv("MT5_BROKER_UTC_OFFSET_HOURS", "3"))
            except ValueError:
                broker_utc_offset_hours = 3.0
        offset_seconds = int(broker_utc_offset_hours * 3600)

        from services.candle_cache_store import persist_candles

        per_symbol_report = {}
        total_persisted = 0
        for mt5_sym, blob in symbols_block.items():
            canonical = SYMBOL_NORMALIZATION.get(mt5_sym, mt5_sym)
            bars = blob.get("bars") or []
            if not bars:
                per_symbol_report[mt5_sym] = {"canonical": canonical, "persisted": 0,
                                                "note": "empty"}
                continue

            # Convert exporter format → candle_cache_store input format.
            # Subtract broker offset so we store TRUE UTC, aligning with the
            # prediction_logs.created_at (which is always real UTC).
            candles_in = []
            for b in bars:
                t_sec = int(b.get("t") or 0)
                if t_sec <= 0:
                    continue
                utc_sec = t_sec - offset_seconds
                candles_in.append({
                    "timestamp": utc_sec * 1000,    # ms (true UTC)
                    "open": float(b.get("o") or 0),
                    "high": float(b.get("h") or 0),
                    "low": float(b.get("l") or 0),
                    "close": float(b.get("c") or 0),
                    "volume": float(b.get("v") or 0),
                })

            n = persist_candles(canonical, "1m", candles_in)
            total_persisted += n
            per_symbol_report[mt5_sym] = {
                "canonical": canonical,
                "received": len(bars),
                "persisted": n,
            }

        return {
            "ok": True,
            "exported_at": data.get("exported_at"),
            "since": data.get("since"),
            "until": data.get("until"),
            "broker_utc_offset_hours_applied": broker_utc_offset_hours,
            "total_persisted": total_persisted,
            "per_symbol": per_symbol_report,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("1m upload failed: %s", e)
        raise HTTPException(500, f"Upload failed: {str(e)[:200]}")
