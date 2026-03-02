"""
EODHD WebSocket Client
======================
Real-time market data feed from EODHD WebSocket API.
Connects to EODHD WSS endpoint and broadcasts price updates to our WebSocket manager.

EODHD WebSocket Docs:
- US Stocks: wss://ws.eodhistoricaldata.com/ws/us?api_token=...
- Forex: wss://ws.eodhistoricaldata.com/ws/forex?api_token=...
- Crypto: wss://ws.eodhistoricaldata.com/ws/crypto?api_token=...
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Callable, Dict, Optional
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

logger = logging.getLogger(__name__)

# EODHD WebSocket endpoints
EODHD_WS_URLS = {
    "us": "wss://ws.eodhistoricaldata.com/ws/us",
    "forex": "wss://ws.eodhistoricaldata.com/ws/forex",
    "crypto": "wss://ws.eodhistoricaldata.com/ws/crypto",
}

# Symbol to market mapping
SYMBOL_MARKETS = {
    "NDX.INDX": "us",
    "GDAXI.INDX": "us",  # DAX is available through US endpoint
    "XAUUSD": "forex",
    "EURUSD": "forex",
    "GBPUSD": "forex",
    "BTC-USD.CC": "crypto",
    "ETH-USD.CC": "crypto",
    # Petrol - EODHD Commodities endpoint
    "CL.F": "us",  # WTI Crude Oil Futures (US Oil ~$64-71)
    "BZ.F": "us",  # Brent Crude Oil Futures (Brent ~$71)
}

# Demo symbols (work with demo API key)
DEMO_SYMBOLS = ["AAPL.US", "BTC-USD.CC"]


class EODHDWebSocketClient:
    """
    EODHD WebSocket client for real-time price feeds.
    Handles connection, subscription, and reconnection automatically.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EODHD_API_KEY", "demo")
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.subscriptions: Dict[str, set] = {
            "us": set(),
            "forex": set(),
            "crypto": set(),
        }
        self.price_callbacks: list[Callable[[str, float, datetime], None]] = []
        self.running = False
        self.reconnect_delay = 2.0  # Start with 2 seconds
        self.max_reconnect_delay = 30.0
        self._tasks: list[asyncio.Task] = []

    def on_price_update(self, callback: Callable[[str, float, datetime], None]):
        """Register a callback for price updates: callback(symbol, price, timestamp)"""
        self.price_callbacks.append(callback)

    def subscribe(self, symbol: str):
        """Subscribe to a symbol."""
        # Map frontend symbols to EODHD symbols
        symbol_mapping = {
            "NDX.INDX": "NDX.INDX",
            "GDAXI.INDX": "GDAXI.INDX",
            "XAUUSD": "XAUUSD",
            "USOIL.FOREX": "CL.F",  # WTI Crude Oil Futures
            "USOIL": "CL.F",    # WTI Crude Oil
            "BRENT": "BZ.F",    # Brent Crude Oil
        }
        
        eodhd_symbol = symbol_mapping.get(symbol, symbol)
        market = SYMBOL_MARKETS.get(eodhd_symbol, "us")
        
        # Demo key only works with specific symbols
        if self.api_key == "demo" and eodhd_symbol not in DEMO_SYMBOLS:
            logger.warning(f"Demo key only works with {DEMO_SYMBOLS}, not {eodhd_symbol}")
            # Map to demo symbols for testing
            if "INDX" in symbol or "XAU" in symbol:
                eodhd_symbol = "AAPL.US"  # Use AAPL as proxy for testing
            elif "COMM" in symbol or "OIL" in symbol or "CL." in symbol or "BZ." in symbol:
                eodhd_symbol = "AAPL.US"  # Use AAPL as proxy for oil too
        
        self.subscriptions[market].add(eodhd_symbol)
        logger.info(f"Subscribed to {symbol} (EODHD: {eodhd_symbol}) on {market} market")
        
        # If already connected to this market, send subscribe message
        if market in self.connections and self.connections[market]:
            asyncio.create_task(self._send_subscription(market, [eodhd_symbol]))

    def unsubscribe(self, symbol: str):
        """Unsubscribe from a symbol."""
        market = SYMBOL_MARKETS.get(symbol, "us")
        self.subscriptions[market].discard(symbol)
        logger.info(f"Unsubscribed from {symbol}")

    async def start(self):
        """Start the WebSocket client."""
        self.running = True
        logger.info("Starting EODHD WebSocket client...")
        
        # Start connection tasks for each market that has subscriptions
        for market, symbols in self.subscriptions.items():
            if symbols:
                task = asyncio.create_task(self._connect_and_listen(market))
                self._tasks.append(task)

    async def stop(self):
        """Stop the WebSocket client."""
        self.running = False
        logger.info("Stopping EODHD WebSocket client...")
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Close all connections
        close_tasks = []
        for market, ws in self.connections.items():
            if ws:
                close_tasks.append(ws.close())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self.connections.clear()
        logger.info("EODHD WebSocket client stopped")

    async def _connect_and_listen(self, market: str):
        """Connect to a market WebSocket and listen for messages."""
        url = f"{EODHD_WS_URLS[market]}?api_token={self.api_key}"
        
        while self.running:
            try:
                logger.info(f"Connecting to EODHD {market} WebSocket...")
                
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    self.connections[market] = ws
                    self.reconnect_delay = 2.0  # Reset on successful connection
                    
                    logger.info(f"Connected to EODHD {market} WebSocket")
                    
                    # Subscribe to all symbols for this market
                    if self.subscriptions[market]:
                        await self._send_subscription(market, list(self.subscriptions[market]))
                    
                    # Listen for messages
                    async for message in ws:
                        await self._handle_message(market, message)
                        
            except ConnectionClosed as e:
                logger.warning(f"EODHD {market} WebSocket closed: {e}")
            except InvalidStatusCode as e:
                logger.error(f"EODHD {market} WebSocket invalid status: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"EODHD {market} WebSocket error: {e}")
            
            if not self.running:
                break
            
            # Reconnect with exponential backoff
            logger.info(f"Reconnecting to {market} in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(
                self.reconnect_delay * 1.5,
                self.max_reconnect_delay
            )

    async def _send_subscription(self, market: str, symbols: list):
        """Send subscription message for symbols."""
        if market not in self.connections or not self.connections[market]:
            return
        
        ws = self.connections[market]
        
        for symbol in symbols:
            subscribe_msg = {
                "action": "subscribe",
                "symbols": symbol
            }
            try:
                await ws.send(json.dumps(subscribe_msg))
                logger.debug(f"Subscribed to {symbol} on {market}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}")

    async def _handle_message(self, market: str, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            # EODHD message format varies by market type
            # Common fields: s (symbol), p (price), t (timestamp), v (volume)
            
            symbol = data.get("s") or data.get("symbol")
            price = data.get("p") or data.get("price") or data.get("close")
            timestamp = data.get("t") or data.get("timestamp")
            
            if not symbol or price is None:
                logger.debug(f"Skipping incomplete message: {data}")
                return
            
            # Parse timestamp
            if timestamp:
                try:
                    if isinstance(timestamp, (int, float)):
                        # Unix timestamp (milliseconds)
                        dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)
                except:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
            
            # Convert price to float
            try:
                price = float(price)
            except (TypeError, ValueError):
                logger.warning(f"Invalid price format: {price}")
                return
            
            logger.debug(f"Price update: {symbol} = {price} at {dt}")
            
            # Notify all registered callbacks
            for callback in self.price_callbacks:
                try:
                    callback(symbol, price, dt)
                except Exception as e:
                    logger.error(f"Price callback error: {e}")
                    
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message: {message[:100]}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")


# Global client instance
_eodhd_ws_client: Optional[EODHDWebSocketClient] = None


def get_eodhd_ws_client() -> EODHDWebSocketClient:
    """Get or create the global EODHD WebSocket client."""
    global _eodhd_ws_client
    if _eodhd_ws_client is None:
        _eodhd_ws_client = EODHDWebSocketClient()
    return _eodhd_ws_client


async def start_eodhd_websocket():
    """Start the EODHD WebSocket client with our symbols."""
    from services.ws_manager import manager
    
    client = get_eodhd_ws_client()
    
    # Register callback to broadcast to our WebSocket clients
    def on_price_update(symbol: str, price: float, timestamp: datetime):
        # Map EODHD symbols back to our frontend symbols
        reverse_mapping = {
            "AAPL.US": ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "USOIL", "BRENT"],  # Demo proxy
            "BTC-USD.CC": ["XAUUSD"],  # Demo proxy
            "NDX.INDX": ["NDX.INDX"],
            "GDAXI.INDX": ["GDAXI.INDX"],
            "XAUUSD": ["XAUUSD"],
            "CL.F": ["USOIL.FOREX", "USOIL"],      # WTI Crude
            "BZ.F": ["BRENT"],                  # Brent Crude
        }
        
        # Get list of symbols to broadcast to
        target_symbols = reverse_mapping.get(symbol, [symbol])
        
        # Broadcast to all mapped symbols
        for target_symbol in target_symbols:
            asyncio.create_task(manager.broadcast(target_symbol, {
                "type": "price_update",
                "symbol": target_symbol,
                "price": price,
                "timestamp": timestamp.isoformat()
            }))
    
    client.on_price_update(on_price_update)
    
    # Subscribe to our trading symbols
    # Petrol: CL.F = WTI (~$64), BZ.F = Brent (~$71)
    symbols = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
    for symbol in symbols:
        client.subscribe(symbol)
    
    # Start the client
    await client.start()


async def stop_eodhd_websocket():
    """Stop the EODHD WebSocket client."""
    global _eodhd_ws_client
    if _eodhd_ws_client:
        await _eodhd_ws_client.stop()
        _eodhd_ws_client = None
