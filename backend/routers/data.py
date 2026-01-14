from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Query

from backend.services.data_fetcher import fetch_eod_candles, fetch_latest_price
from backend.services.ta_service import compute_ta_snapshot


router = APIRouter(prefix="/api/data", tags=["data"])


def _date_to_ms(date_str: str) -> int:
    # Expect YYYY-MM-DD; interpret as UTC midnight
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


@router.get("/ohlcv")
async def ohlcv(
    symbol: str = Query(default="NDX.INDX"),
    timeframe: str = Query(default="1d"),
    limit: int = Query(default=500, ge=50, le=500),
) -> Dict[str, Any]:
    """
    Chart data endpoint used by frontend `useChartData`.
    Note: Some EODHD plans don't allow intraday; we serve daily candles for all timeframes.
    """
    # Daily candles
    rows = await fetch_eod_candles(symbol, limit=limit)
    data: List[Dict[str, Any]] = []
    for r in rows:
        ds = r.get("date") or ""
        if not ds:
            continue
        data.append(
            {
                "timestamp": _date_to_ms(ds),
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r.get("volume") or 0.0,
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



