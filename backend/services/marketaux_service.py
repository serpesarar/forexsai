from __future__ import annotations

from typing import List, Dict

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
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.marketaux_base_url, params=params)
        response.raise_for_status()
        data = response.json()
    return [
        {"title": item.get("title", ""), "source": item.get("source", "")}
        for item in data.get("data", [])
    ]
