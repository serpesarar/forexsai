"""Fiyat alarmları API — /api/alerts (services/price_alert_service.py).

Tüm uçlar yönetici oturumu ister: alarm Telegram'a mesaj attırır, anonim erişim kötüye kullanılabilir.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services import price_alert_service as pas
from services.admin_auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(require_admin)])


class AlertIn(BaseModel):
    symbol: str
    kind: str = Field(..., pattern="^(above|below|pct_move|time|stop|target)$")
    price: Optional[float] = None
    pct: Optional[float] = None
    ref_price: Optional[float] = None
    at_utc: Optional[str] = None
    label: Optional[str] = None
    one_shot: bool = True
    notify_telegram: bool = True


class PlanIn(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    entry: float
    stop: float
    target: float
    horizon_min: Optional[int] = Field(None, ge=5, le=1440)


class StatusIn(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


def _db_call(fn, *args) -> Any:
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))


@router.get("")
async def list_alerts(status: Optional[str] = Query(None, pattern="^(active|triggered|disabled)$")) -> Dict[str, Any]:
    return {"alerts": _db_call(pas.list_alerts, status), "service": pas.status()}


@router.post("")
async def create_alert(body: AlertIn) -> Dict[str, Any]:
    payload = body.model_dump()
    row = _db_call(pas.validate, payload, pas.current_price(body.symbol))
    return {"created": _db_call(pas.create_alerts, [row])}


@router.post("/from-plan")
async def create_from_plan(body: PlanIn) -> Dict[str, Any]:
    rows = _db_call(pas.plan_alerts, body.symbol, body.side, body.entry, body.stop, body.target, body.horizon_min)
    return {"created": _db_call(pas.create_alerts, rows)}


@router.patch("/{alert_id}")
async def update_status(alert_id: int, body: StatusIn) -> Dict[str, Any]:
    row = _db_call(pas.set_status, alert_id, body.status)
    if row is None:
        raise HTTPException(404, "alarm bulunamadı")
    return {"alert": row}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int) -> Dict[str, Any]:
    if not _db_call(pas.delete_alert, alert_id):
        raise HTTPException(404, "alarm bulunamadı")
    return {"deleted": alert_id}


@router.post("/run-once")
async def run_once() -> Dict[str, Any]:
    return await pas.run_once()
