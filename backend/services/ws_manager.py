"""
WebSocket Connection Manager
==============================
Manages WebSocket connections and broadcasts data to connected clients.

Architecture:
- Clients connect to /ws/{symbol} (e.g. /ws/NDX.INDX, /ws/XAUUSD)
- Background scheduler computes data → calls broadcast()
- All connected clients for that symbol receive the update instantly
- New connections immediately get the latest cached data (no wait)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per symbol channel."""

    def __init__(self):
        # symbol -> set of active WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # symbol -> last broadcast payload (for instant delivery to new connections)
        self._last_payload: Dict[str, str] = {}
        # Stats
        self._total_broadcasts = 0
        self._total_connections = 0

    async def connect(self, websocket: WebSocket, symbol: str):
        """Accept a new WebSocket connection and subscribe to a symbol channel."""
        await websocket.accept()
        self._connections[symbol].add(websocket)
        self._total_connections += 1
        logger.info(
            f"WS connected: {symbol} "
            f"(total={self.total_clients}, channel={len(self._connections[symbol])})"
        )

        # Immediately send last known data so client doesn't wait for next cycle
        if symbol in self._last_payload:
            try:
                await websocket.send_text(self._last_payload[symbol])
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket, symbol: str):
        """Remove a WebSocket connection."""
        self._connections[symbol].discard(websocket)
        if not self._connections[symbol]:
            del self._connections[symbol]
        logger.info(
            f"WS disconnected: {symbol} (total={self.total_clients})"
        )

    async def broadcast(self, symbol: str, data: Dict[str, Any]):
        """Broadcast data to all clients subscribed to a symbol."""
        if symbol not in self._connections or not self._connections[symbol]:
            # Still cache the payload for future connections
            try:
                payload = json.dumps(data, default=str, ensure_ascii=False)
                self._last_payload[symbol] = payload
            except Exception:
                pass
            return

        try:
            payload = json.dumps(data, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"WS broadcast serialize error for {symbol}: {e}")
            return

        self._last_payload[symbol] = payload
        self._total_broadcasts += 1

        # Send to all connected clients, remove dead connections
        dead: list[WebSocket] = []
        for ws in self._connections[symbol].copy():
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections[symbol].discard(ws)

        if dead:
            logger.debug(f"Removed {len(dead)} dead WS connections for {symbol}")

    async def broadcast_all(self, data_by_symbol: Dict[str, Dict[str, Any]]):
        """Broadcast data for multiple symbols at once."""
        for symbol, data in data_by_symbol.items():
            await self.broadcast(symbol, data)

    @property
    def total_clients(self) -> int:
        return sum(len(conns) for conns in self._connections.values())

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_clients": self.total_clients,
            "total_broadcasts": self._total_broadcasts,
            "total_connections_ever": self._total_connections,
            "channels": {
                sym: len(conns) for sym, conns in self._connections.items()
            },
            "cached_symbols": list(self._last_payload.keys()),
        }


# Global singleton
manager = ConnectionManager()
