"""MiroShark bias-accuracy MEASUREMENT endpoints (isolated test harness).

Thin HTTP layer over ``services.bias_test_service`` (shared with the scheduled
auto-runner). Writes to bias_test_log only — never the live daily_bias table or
the veto engine.

  GET  /api/bias-test/lab              double-click control-panel UI
  POST /api/bias-test/log              record a bias run + session context
  POST /api/bias-test/run-debate       run the native debate engine NOW + log
  POST /api/bias-test/fill-outcomes    after close, grade predictions vs actual
  GET  /api/bias-test/accuracy-report  accuracy by run_label / confidence / session
  GET  /api/bias-test/routing-status   which LLM providers are configured
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import HTMLResponse

from services import bias_test_service as bts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bias-test", tags=["Bias Test Harness"])

_LAB_HTML_PATH = os.path.join(os.path.dirname(__file__), "bias_lab.html")


@router.get("/lab", response_class=HTMLResponse)
async def bias_lab():
    """Self-contained control-panel UI (served same-origin → no CORS)."""
    try:
        with open(_LAB_HTML_PATH, encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="bias_lab.html missing")


@router.post("/log")
async def log_bias_run(body: dict = Body(...)):
    """Record a MiroShark bias run. Body: CIO JSON (flat or under ``payload``)
    plus optional ``run_label`` and ``run_timestamp_utc`` (ISO, for backfill)."""
    from datetime import datetime, timezone
    run_label = body.get("run_label") or "manual"
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else body

    run_ts = None
    if body.get("run_timestamp_utc"):
        try:
            run_ts = datetime.fromisoformat(
                str(body["run_timestamp_utc"]).replace("Z", "+00:00"))
            if run_ts.tzinfo is None:
                run_ts = run_ts.replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad run_timestamp_utc")

    try:
        return await bts.record_run(payload, run_label, run_ts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid bias payload: {e}")
    except bts.BiasTestError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/run-debate")
async def run_debate_now(run_label: str = Query(default="manual_debate")):
    """Run the native debate engine right now and log the verdict."""
    from services.bias_debate_engine import run_debate
    from services.llm_router import LLMUnavailable
    try:
        verdict = await run_debate()
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"debate failed: {e}")
    try:
        result = await bts.record_run(verdict, run_label)
    except bts.BiasTestError as e:
        raise HTTPException(status_code=503, detail=str(e))
    debate = verdict.get("_debate", {}) or {}
    return {
        **result,
        "verdict": {k: v for k, v in verdict.items() if k != "_debate"},
        "debate": {
            "context_notes": debate.get("context_notes", {}),
            "bull_case": debate.get("bull_case"),
            "bear_case": debate.get("bear_case"),
            "cio_provider": debate.get("cio_provider"),
        },
    }


@router.post("/fill-outcomes")
async def fill_outcomes(ny_date: Optional[str] = Query(default=None)):
    """Grade all rows for a NY date against the actual NDX cash move."""
    try:
        return await bts.fill_outcomes(ny_date)
    except bts.BiasTestError as e:
        # missing candle/session data → 404, db down → 503
        code = 404 if ("no NDX daily candle" in str(e)
                       or "no session/horizon data" in str(e)) else 503
        raise HTTPException(status_code=code, detail=str(e))


@router.get("/accuracy-report")
async def accuracy_report(days: int = Query(default=30, ge=1, le=365)):
    """Accuracy broken down by run_label, confidence bucket, and session flags."""
    try:
        return bts.accuracy_report()
    except bts.BiasTestError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/cortex-signals")
async def cortex_signals(days: int = Query(default=30, ge=1, le=365)):
    """Recent CORTEX confluence SHADOW signals + running hit-rate (log-only)."""
    from services.cortex_confluence_signal import _client
    client = _client()
    if client is None:
        raise HTTPException(status_code=503, detail="db unavailable")
    rows = (client.table("cortex_confluence_signals").select("*")
            .order("decision_ts_utc", desc=True).limit(500).execute()).get("data") or []
    fired = [r for r in rows if r.get("fired")]
    graded = [r for r in fired if r.get("was_correct") is not None]
    correct = sum(1 for r in graded if r["was_correct"])
    return {"total_evaluations": len(rows), "fired": len(fired),
            "graded": len(graded), "correct": correct,
            "live_hit_rate": round(correct / len(graded) * 100, 1) if graded else None,
            "recent": rows[:20]}


@router.post("/cortex-signals/run")
async def cortex_signals_run():
    """Manually evaluate the confluence rules right now (test/trigger)."""
    from services.cortex_confluence_signal import evaluate_and_record
    return {"signals": evaluate_and_record()}


@router.get("/routing-status")
async def routing_status():
    """Which LLM providers back each importance tier (config diagnostic)."""
    from services.llm_router import routing_status as rs
    from config import settings
    return {**rs(),
            "auto_run_enabled": settings.bias_auto_run_enabled,
            "run_windows": settings.bias_run_windows_et,
            "fill_time_et": settings.bias_fill_time_et}
