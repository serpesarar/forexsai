from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import settings


logger = logging.getLogger(__name__)

_MARKETAUX_HEALTH: Dict[str, Any] = {
    "last_attempt_at": None,
    "last_success_at": None,
    "last_status_code": None,
    "last_error": None,
    "last_result_count": 0,
    "last_query_symbols": [],
    "used_symbol_filter": False,
}


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def get_marketaux_health() -> Dict[str, Any]:
    return {
        **_MARKETAUX_HEALTH,
        "configured": bool(settings.marketaux_api_key),
        "base_url": settings.marketaux_base_url,
    }


def _normalize_symbols(symbols: List[str]) -> Optional[str]:
    cleaned: List[str] = []
    for s in symbols:
        s = (s or "").strip()
        if not s:
            continue
        # Marketaux often doesn't like suffixes like ".INDX"
        if "." in s:
            s = s.split(".", 1)[0]
        cleaned.append(s)
    cleaned = [s for s in cleaned if s]
    return ",".join(cleaned) if cleaned else None


async def fetch_marketaux_headlines(symbols: List[str]) -> List[Dict[str, str]]:
    """
    Returns minimal headline objects used across the app.
    - Tries symbol-filtered query first
    - Falls back to general market news if filter yields empty
    """
    if not settings.marketaux_api_key:
        _MARKETAUX_HEALTH.update({
            "last_attempt_at": _utc_now_iso(),
            "last_status_code": None,
            "last_error": "MARKETAUX_API_KEY missing",
            "last_result_count": 0,
            "last_query_symbols": list(symbols or []),
            "used_symbol_filter": False,
        })
        return []

    url = settings.marketaux_base_url
    symbols_param = _normalize_symbols(symbols)
    params: Dict[str, Any] = {"api_token": settings.marketaux_api_key, "limit": 10, "language": "en"}
    if symbols_param:
        params["symbols"] = symbols_param

    _MARKETAUX_HEALTH.update({
        "last_attempt_at": _utc_now_iso(),
        "last_error": None,
        "last_query_symbols": list(symbols or []),
        "used_symbol_filter": bool(symbols_param),
    })

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            _MARKETAUX_HEALTH["last_status_code"] = response.status_code
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", []) or []

            if not data and symbols_param:
                response = await client.get(
                    url, params={"api_token": settings.marketaux_api_key, "limit": 10, "language": "en"}
                )
                _MARKETAUX_HEALTH["last_status_code"] = response.status_code
                response.raise_for_status()
                payload = response.json()
                data = payload.get("data", []) or []
    except httpx.HTTPStatusError as exc:
        logger.warning("[Marketaux] HTTP error status=%s symbols=%s", exc.response.status_code, symbols)
        _MARKETAUX_HEALTH.update({
            "last_status_code": exc.response.status_code,
            "last_error": f"HTTP {exc.response.status_code}",
            "last_result_count": 0,
        })
        return []
    except Exception as exc:
        logger.warning("[Marketaux] Request error for symbols=%s: %s", symbols, exc)
        _MARKETAUX_HEALTH.update({
            "last_error": str(exc),
            "last_result_count": 0,
        })
        return []

    _MARKETAUX_HEALTH.update({
        "last_success_at": _utc_now_iso(),
        "last_error": None,
        "last_result_count": len(data),
    })

    results = []
    for item in data:
        results.append({
            "title": item.get("title", "") or "",
            "source": item.get("source", "") or "",
            "published_at": item.get("published_at", "") or "",
            "description": (item.get("description", "") or "")[:300],
            "url": item.get("url", "") or "",
            "image_url": item.get("image_url", "") or "",
            "snippet": (item.get("snippet", "") or "")[:200],
            "entities": [e.get("symbol", "") for e in (item.get("entities", []) or []) if e.get("symbol")],
        })
    return results
