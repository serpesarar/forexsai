from __future__ import annotations

 codex/generate-full-stack-trading-dashboard-code-cvecet
from typing import Dict, List
=======
from typing import List, Dict
main

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
 codex/generate-full-stack-trading-dashboard-code-cvecet
    url = settings.marketaux_base_url
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        return [
            {"title": item.get("title", ""), "source": item.get("source", "")}
            for item in payload.get("data", [])
        ]
=======
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.marketaux_base_url, params=params)
        response.raise_for_status()
        data = response.json()
    return [
        {"title": item.get("title", ""), "source": item.get("source", "")}
        for item in data.get("data", [])
    ]
 main
