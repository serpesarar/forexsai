from __future__ import annotations

from typing import Dict, List

import httpx

from backend.config import settings


async def fetch_marketaux_headlines(symbols: List[str]) -> List[Dict[str, str]]:
    if not settings.marketaux_api_key:
        return []

    params = {
        "api_token": settings.marketaux_api_key,
        "symbols": ",".join(symbols),
        "limit": 10,
        "language": "en",
    }
    url = settings.marketaux_base_url
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        return [
            {"title": item.get("title", ""), "source": item.get("source", "")}
            for item in payload.get("data", [])
        ]
