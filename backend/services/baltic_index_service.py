from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Any, Dict, Optional

import httpx
import pandas as pd

from config import settings
from database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

INDEX_URLS = {
    "BDTI": "https://en.stockq.org/index/BDTI.php",
    "BCTI": "https://en.stockq.org/index/BCTI.php",
}

_CACHE: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_CACHE_TTL = timedelta(minutes=45)
_SYNC_TASK: Optional[asyncio.Task] = None
_SYNC_RUNNING = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    return frame


def _table_value(frame: pd.DataFrame) -> Optional[Dict[str, Any]]:
    normalized = _clean_columns(frame.copy())
    if normalized.empty:
        return None

    value_candidates = [
        "close",
        "value",
        "last",
        "index",
        "price",
        "latest",
    ]
    date_candidates = ["date", "time", "day"]
    change_candidates = ["change", "chg"]
    pct_candidates = ["change%", "change %", "% change", "pct", "%"]

    value_col = next((column for column in normalized.columns if column in value_candidates), None)
    if value_col is None:
        value_col = next((column for column in normalized.columns if any(token in column for token in value_candidates)), None)
    if value_col is None:
        numeric_columns = [column for column in normalized.columns if normalized[column].map(_parse_float).notna().sum() >= 1]
        if numeric_columns:
            value_col = numeric_columns[-1]
    if value_col is None:
        return None

    row_index = 0
    value = _parse_float(normalized.iloc[row_index][value_col])
    if value is None:
        return None

    date_col = next((column for column in normalized.columns if column in date_candidates), None)
    date_value = normalized.iloc[row_index][date_col] if date_col else None
    parsed_date = None
    if date_value is not None:
        try:
            parsed_date = pd.to_datetime(date_value, utc=True).date()
        except Exception:
            parsed_date = None

    change_col = next((column for column in normalized.columns if column in change_candidates or any(token in column for token in change_candidates)), None)
    change_pct_col = next((column for column in normalized.columns if column in pct_candidates or any(token in column for token in pct_candidates)), None)

    change_day = _parse_float(normalized.iloc[row_index][change_col]) if change_col else None
    change_percent = _parse_float(normalized.iloc[row_index][change_pct_col]) if change_pct_col else None

    if change_day is None and len(normalized) > 1:
        previous = _parse_float(normalized.iloc[1][value_col])
        if previous is not None:
            change_day = value - previous
            if previous != 0 and change_percent is None:
                change_percent = (change_day / previous) * 100.0

    return {
        "value": round(value, 2),
        "change_day": round(change_day, 2) if change_day is not None else None,
        "change_percent": round(change_percent, 2) if change_percent is not None else None,
        "as_of_date": parsed_date.isoformat() if parsed_date else None,
    }


async def _fetch_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "Mozilla/5.0 ForexSAI Baltic Collector"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_from_stockq(index_type: str) -> Optional[Dict[str, Any]]:
    url = INDEX_URLS.get(index_type)
    if not url:
        return None
    try:
        html = await _fetch_html(url)
        tables = pd.read_html(StringIO(html))
        for table in tables:
            parsed = _table_value(table)
            if parsed and parsed.get("value") is not None:
                return {
                    "index_type": index_type,
                    "source": "stockq",
                    **parsed,
                    "fetched_at": _now().isoformat(),
                    "status": "live",
                    "note": "Parsed from StockQ public tanker index page.",
                    "raw_payload": {"url": url},
                }
    except Exception as exc:
        logger.warning("StockQ fetch failed for %s: %s", index_type, exc)
    return None


async def _fetch_from_manual_url(index_type: str, url: str) -> Optional[Dict[str, Any]]:
    try:
        html = await _fetch_html(url)
        try:
            payload = httpx.Response(200, text=html).json()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            value = _parse_float(payload.get("value"))
            if value is not None:
                previous = _parse_float(payload.get("previous"))
                change_day = _parse_float(payload.get("change_day"))
                change_percent = _parse_float(payload.get("change_percent"))
                if change_day is None and previous is not None:
                    change_day = value - previous
                if change_percent is None and previous not in (None, 0):
                    change_percent = ((value - previous) / previous) * 100.0
                return {
                    "index_type": index_type,
                    "source": url,
                    "value": round(value, 2),
                    "change_day": round(change_day, 2) if change_day is not None else None,
                    "change_percent": round(change_percent, 2) if change_percent is not None else None,
                    "as_of_date": payload.get("as_of_date"),
                    "fetched_at": _now().isoformat(),
                    "status": "live",
                    "note": "Fetched from configured manual Baltic source.",
                    "raw_payload": payload,
                }
        tables = pd.read_html(StringIO(html))
        for table in tables:
            parsed = _table_value(table)
            if parsed and parsed.get("value") is not None:
                return {
                    "index_type": index_type,
                    "source": url,
                    **parsed,
                    "fetched_at": _now().isoformat(),
                    "status": "live",
                    "note": "Parsed from configured manual Baltic page.",
                    "raw_payload": {"url": url},
                }
    except Exception as exc:
        logger.warning("Manual Baltic source failed for %s: %s", index_type, exc)
    return None


def _cache_put(index_type: str, payload: Dict[str, Any]) -> None:
    _CACHE[index_type] = (_now(), payload)


def _cache_get(index_type: str) -> Optional[Dict[str, Any]]:
    cached = _CACHE.get(index_type)
    if not cached:
        return None
    created_at, payload = cached
    if _now() - created_at > _CACHE_TTL:
        return None
    return payload


def _upsert_cache_row(row: Dict[str, Any]) -> None:
    client = get_supabase_client()
    if client is None:
        return
    client.table("baltic_index_cache").upsert(row, on_conflict="index_type")


def _read_cached_row(index_type: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None
    result = client.table("baltic_index_cache").select("*").eq("index_type", index_type).limit(1).execute()
    rows = result.get("data") if isinstance(result, dict) else None
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def fetch_baltic_index(index_type: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    if not force_refresh:
        cached = _cache_get(index_type)
        if cached:
            return cached

    manual_url = None
    if index_type == "BDTI":
        manual_url = getattr(settings, "baltic_bdti_url", None)
    elif index_type == "BCTI":
        manual_url = getattr(settings, "baltic_bcti_url", None)
    elif index_type == "TD3C":
        manual_url = getattr(settings, "baltic_td3c_url", None)

    payload = None
    if manual_url:
        payload = await _fetch_from_manual_url(index_type, manual_url)

    if payload is None and index_type in INDEX_URLS and getattr(settings, "baltic_stockq_enabled", True):
        payload = await _fetch_from_stockq(index_type)

    if payload is not None:
        _upsert_cache_row(payload)
        _cache_put(index_type, payload)
        return payload

    db_row = _read_cached_row(index_type)
    if db_row:
        db_row["status"] = db_row.get("status") or "stale"
        _cache_put(index_type, db_row)
        return db_row
    return None


async def get_baltic_snapshot(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    snapshot: Dict[str, Dict[str, Any]] = {}
    for index_type in ("BDTI", "BCTI", "TD3C"):
        row = await fetch_baltic_index(index_type, force_refresh=force_refresh)
        if row:
            snapshot[index_type] = row
    return snapshot


async def baltic_sync_loop(interval_seconds: int = 3600) -> None:
    global _SYNC_RUNNING
    if _SYNC_RUNNING:
        return
    _SYNC_RUNNING = True
    while _SYNC_RUNNING:
        try:
            await get_baltic_snapshot(force_refresh=True)
        except Exception as exc:
            logger.error("Baltic sync loop error: %s", exc, exc_info=True)
        await asyncio.sleep(interval_seconds)


def start_baltic_sync() -> None:
    global _SYNC_TASK
    if _SYNC_TASK and not _SYNC_TASK.done():
        return
    _SYNC_TASK = asyncio.create_task(baltic_sync_loop())


def stop_baltic_sync() -> None:
    global _SYNC_RUNNING, _SYNC_TASK
    _SYNC_RUNNING = False
    if _SYNC_TASK and not _SYNC_TASK.done():
        _SYNC_TASK.cancel()
