from __future__ import annotations

import json
from typing import Optional

import websockets

from backend.config import settings


async def fetch_latest_price(symbol: str) -> Optional[float]:
    if not settings.eodhd_api_key:
        return None

    url = f"wss://ws.eodhistoricaldata.com/ws/forex?api_token={settings.eodhd_api_key}"
    subscribe_payload = {"action": "subscribe", "symbols": symbol}

    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
            await websocket.send(json.dumps(subscribe_payload))
            while True:
                message = await websocket.recv()
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    continue
                price = payload.get("p") or payload.get("price")
                if price is not None:
                    return float(price)
    except Exception:
        return None
