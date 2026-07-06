"""MiroShark → ForexSAI daily-bias bridge.

Receives the once-a-day NASDAQ macro bias produced by MiroShark's CIO agent and
persists it to the ``daily_bias`` table. Three endpoints:

  POST /api/miroshark/webhook        HMAC-SHA256 verified push (production path)
  POST /api/miroshark/manual-bias    unverified fallback (paste JSON from the UI)
  GET  /api/miroshark/current-bias   read today's bias (frontend + veto engine)

All persistence goes through ``services.daily_bias_service`` so the webhook and
the manual fallback share one UPSERT path. NASDAQ-only by design.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from config import settings
from services import daily_bias_service as bias_svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/miroshark", tags=["MiroShark Bias"])

_SIGNATURE_HEADER = "X-MiroShark-Signature"


def verify_signature(raw_body: bytes, signature: str | None, secret: str) -> bool:
    """Constant-time HMAC-SHA256 check. Expected header: ``sha256=<hexdigest>``."""
    if not signature or not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _persist(payload: dict, source: str) -> dict:
    """Shared UPSERT + response shaping for webhook and manual paths."""
    try:
        result = bias_svc.upsert_bias(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid bias payload: {e}")

    if not result.get("ok"):
        # DB down / write failed — 503 so the sender can retry (webhooks retry).
        raise HTTPException(status_code=503,
                            detail=f"bias not stored: {result.get('error')}")

    row = result.get("row") or {}
    logger.info("[miroshark] bias stored via %s: %s conf=%s",
                source, row.get("nasdaq_daily_bias"), row.get("confidence"))
    return {
        "ok": True,
        "source": source,
        "bias_date": row.get("bias_date"),
        "symbol": row.get("symbol"),
        "nasdaq_daily_bias": row.get("nasdaq_daily_bias"),
        "confidence": row.get("confidence"),
    }


@router.post("/webhook")
async def miroshark_webhook(request: Request):
    """Verified MiroShark push. 401 on bad signature, 400 on unparseable JSON."""
    raw = await request.body()
    secret = settings.miroshark_webhook_secret
    if not secret:
        # Misconfiguration should be loud, not a silent accept.
        raise HTTPException(status_code=503, detail="WEBHOOK_SECRET not configured")

    signature = request.headers.get(_SIGNATURE_HEADER)
    if not verify_signature(raw, signature, secret):
        logger.warning("[miroshark] webhook rejected — bad signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {e}")

    return _persist(payload, source="webhook")


@router.post("/manual-bias")
async def miroshark_manual_bias(payload: dict):
    """Fallback: paste the MiroShark CIO JSON when the webhook isn't wired.

    No signature (operator-triggered). Same UPSERT + validation as the webhook.
    """
    return _persist(payload, source="manual")


@router.get("/current-bias")
async def miroshark_current_bias(
    symbol: str = Query(default=bias_svc.DEFAULT_BIAS_SYMBOL),
):
    """Today's bias for *symbol*, or a null bias with ``no_bias_today``."""
    bias = bias_svc.get_current_bias(symbol)
    if bias is None:
        return {"symbol": symbol, "bias": None, "status": "no_bias_today"}
    return {"symbol": symbol, "bias": bias, "status": "ok"}
