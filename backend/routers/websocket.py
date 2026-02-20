"""
WebSocket Router
=================
Provides real-time data streaming to frontend clients.

Endpoints:
- /ws/{symbol}  — Subscribe to real-time updates for a symbol
- /ws/all       — Subscribe to updates for ALL symbols
- /api/ws/stats — GET endpoint showing WebSocket connection stats
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.ws_manager import manager
from services.redis_client import cache_get

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

VALID_SYMBOLS = {"NDX.INDX", "XAUUSD", "GDAXI.INDX", "CL.COMM"}


@router.websocket("/ws/all")
async def websocket_all(websocket: WebSocket):
    """Subscribe to updates for ALL tracked symbols."""
    symbols_subscribed = list(VALID_SYMBOLS)

    # Connect to all channels
    for sym in symbols_subscribed:
        if sym == symbols_subscribed[0]:
            await manager.connect(websocket, sym)
        else:
            # Don't re-accept, just add to channel
            manager._connections[sym].add(websocket)

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                try:
                    msg = json.loads(raw)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except (json.JSONDecodeError, KeyError):
                    pass
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WS /all error: {e}")
    finally:
        for sym in symbols_subscribed:
            manager.disconnect(websocket, sym)


@router.websocket("/ws/{symbol}")
async def websocket_symbol(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time symbol data.
    
    Client connects → immediately receives last cached data →
    then receives broadcasts every time the scheduler computes new data.
    """
    symbol = symbol.upper()

    # Normalize common aliases
    if symbol in ("NASDAQ", "NDX"):
        symbol = "NDX.INDX"

    await manager.connect(websocket, symbol)

    try:
        # Keep connection alive — listen for client messages (ping/pong, symbol change)
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                # Handle client commands
                try:
                    msg = json.loads(raw)
                    cmd = msg.get("type") or msg.get("cmd")

                    if cmd == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))

                    elif cmd == "subscribe":
                        new_symbol = (msg.get("symbol") or "").upper()
                        if new_symbol and new_symbol != symbol:
                            manager.disconnect(websocket, symbol)
                            symbol = new_symbol
                            await manager.connect(websocket, symbol)

                    elif cmd == "get_cached":
                        # Client explicitly requests current cached data
                        cached = cache_get(f"broadcast:{symbol}")
                        if cached:
                            await websocket.send_text(
                                json.dumps({"type": "snapshot", "symbol": symbol, "data": cached})
                            )
                except (json.JSONDecodeError, KeyError):
                    pass  # Ignore malformed messages

            except asyncio.TimeoutError:
                # No message in 60s — send keepalive ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WS error for {symbol}: {e}")
    finally:
        manager.disconnect(websocket, symbol)


@router.get("/api/ws/stats")
async def ws_stats():
    """Get WebSocket connection statistics."""
    from services.redis_client import get_redis_info

    return {
        "websocket": manager.get_stats(),
        "redis": get_redis_info(),
    }


@router.get("/api/ws/test-panels/{symbol}")
async def test_panel_cache(symbol: str):
    """Debug endpoint: check what panel data is cached for broadcast."""
    try:
        from services.background_scheduler import _get_cached_panel_data
        panels = _get_cached_panel_data(symbol.upper())
        return {
            "symbol": symbol,
            "panels_cached": list(panels.keys()),
            "panel_count": len(panels),
            "panel_sizes": {k: len(str(v)) for k, v in panels.items()},
            "hint": "Panels get cached when served via HTTP. Call the panel API first to populate cache.",
        }
    except Exception as e:
        import traceback
        return {
            "symbol": symbol,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
