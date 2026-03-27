from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Query

from services.data_fetcher import fetch_eod_candles, fetch_latest_price, fetch_ohlc_data
from services.ta_service import compute_ta_snapshot


router = APIRouter(prefix="/api/data", tags=["data"])


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class OHLCVDataPoint(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class SupportResistanceLevel(BaseModel):
    type: str
    price: float
    label: str

class OHLCVResponse(BaseModel):
    symbol: str
    timeframe: str
    data: List[OHLCVDataPoint]
    support_resistance: List[SupportResistanceLevel]

class CachedData(BaseModel):
    symbol: str
    updated_at: Optional[str] = None
    ta_snapshot: Dict[str, Any]
    current_price: float

class CachedDataResponse(BaseModel):
    success: bool
    cached: bool
    data: CachedData

class CachedErrorResponse(BaseModel):
    success: bool = False
    error: str

class SchedulerStatusResponse(BaseModel):
    running: bool
    tracked_symbols: List[str]
    error: Optional[str] = None


def _date_to_ms(date_str: str) -> int:
    # Expect YYYY-MM-DD or YYYY-MM-DD HH:MM:SS; interpret as UTC
    try:
        if " " in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


@router.get("/ohlcv", response_model=OHLCVResponse)
async def ohlcv(
    symbol: str = Query(default="NDX.INDX"),
    timeframe: str = Query(default="1d"),
    limit: int = Query(default=500, ge=50, le=1500),
) -> Dict[str, Any]:
    """
    Chart data endpoint used by frontend `useChartData`.
    Returns proper intraday data for 5m/15m/1h/4h timeframes via DataHub.
    Falls back to EOD for daily timeframe.
    """
    tf_lower = timeframe.lower()
    
    # Use fetch_ohlc_data which reads from DataHub first (0 API calls)
    rows = await fetch_ohlc_data(symbol, timeframe=tf_lower, limit=limit)
    
    data: List[Dict[str, Any]] = []
    for r in rows:
        # Handle both intraday (datetime) and EOD (date) formats
        ts = r.get("timestamp", 0)
        if not ts:
            ds = r.get("date") or r.get("datetime") or ""
            if ds:
                ts = _date_to_ms(ds)
        data.append(
            {
                "timestamp": ts,
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": float(r.get("volume", 0)),
            }
        )

    # support/resistance: reuse TA snapshot levels, map to expected shape
    ta = await compute_ta_snapshot(symbol=symbol, limit=min(260, max(120, limit)))
    sr = []
    for idx, lvl in enumerate(ta.get("supports", [])[:3], start=1):
        sr.append({"type": "support", "price": float(lvl["price"]), "label": f"S{idx}"})
    for idx, lvl in enumerate(ta.get("resistances", [])[:3], start=1):
        sr.append({"type": "resistance", "price": float(lvl["price"]), "label": f"R{idx}"})

    # if we have live price, append it as an unlabeled level (optional)
    live = await fetch_latest_price(symbol)
    if live is not None and live != 0:
        sr.append({"type": "resistance" if float(live) > float(ta.get("ema", {}).get("ema20", live)) else "support", "price": float(live), "label": "LIVE"})

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": data,
        "support_resistance": sr,
    }


@router.get("/cached/{symbol}", response_model=CachedDataResponse)
async def get_cached_data_endpoint(symbol: str) -> Dict[str, Any]:
    """
    Get cached live data — reads from DataHub (in-memory, updated every 30s).
    Falls back to Supabase live_data_cache if DataHub has no data.
    """
    try:
        # PRIMARY: Read from DataHub (always fresh, updated every 30s)
        from services.data_hub import get_price, get_hub_status
        live_price = get_price(symbol)
        
        if live_price is not None:
            ta = await compute_ta_snapshot(symbol)
            return {
                "success": True,
                "cached": False,
                "data": {
                    "symbol": symbol,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "ta_snapshot": ta,
                    "current_price": float(live_price),
                }
            }
        
        # FALLBACK: Supabase cache (may be stale)
        from services.background_scheduler import get_cached_data
        cached = await get_cached_data(symbol)
        
        if cached:
            return {
                "success": True,
                "cached": True,
                "data": cached,
            }
        
        # LAST RESORT: compute fresh
        ta = await compute_ta_snapshot(symbol)
        live = await fetch_latest_price(symbol)
        return {
            "success": True,
            "cached": False,
            "data": {
                "symbol": symbol,
                "ta_snapshot": ta,
                "current_price": float(live) if live else None,
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def scheduler_status() -> Dict[str, Any]:
    """Check if background scheduler is running."""
    try:
        from services.background_scheduler import _scheduler_running, TRACKED_SYMBOLS
        return {
            "running": _scheduler_running,
            "tracked_symbols": TRACKED_SYMBOLS,
        }
    except Exception as e:
        return {
            "running": False,
            "error": str(e),
        }
