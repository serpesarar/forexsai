from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from config import settings


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
        return []

    url = settings.marketaux_base_url
    symbols_param = _normalize_symbols(symbols)
    params: Dict[str, Any] = {"api_token": settings.marketaux_api_key, "limit": 10, "language": "en"}
    if symbols_param:
        params["symbols"] = symbols_param

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", []) or []

            if not data and symbols_param:
                response = await client.get(
                    url, params={"api_token": settings.marketaux_api_key, "limit": 10, "language": "en"}
                )
                response.raise_for_status()
                payload = response.json()
                data = payload.get("data", []) or []
    except Exception:
        return []

    return [{"title": item.get("title", "") or "", "source": item.get("source", "") or ""} for item in data]
