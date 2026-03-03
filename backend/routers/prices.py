"""
Live Prices Router
Returns current prices for all tracked symbols
"""
from fastapi import APIRouter
from typing import Dict, Any
import os

router = APIRouter(prefix="/api/prices", tags=["prices"])

# Try to import from data_hub
try:
    from services.data_hub import get_price
    DATA_HUB_AVAILABLE = True
except ImportError:
    DATA_HUB_AVAILABLE = False
    print("[Prices] DataHub not available, using mock data")

# Mock prices for testing
MOCK_PRICES = {
    "XAUUSD": {"price": 5387.26, "change": 12.50, "changePercent": 0.23},
    "NDX": {"price": 24992.60, "change": -45.20, "changePercent": -0.18},
    "DAX": {"price": 24638.00, "change": -320.50, "changePercent": -1.28},
    "USOIL": {"price": 97.55, "change": 1.20, "changePercent": 1.24},
    "VIX": {"price": 18.45, "change": 0.85, "changePercent": 4.83},
    "DXY": {"price": 103.85, "change": -0.15, "changePercent": -0.14},
}

@router.get("")
async def get_live_prices() -> Dict[str, Any]:
    """Get current prices for all tracked symbols"""
    try:
        prices = {}
        
        for symbol in ["XAUUSD", "NDX", "DAX", "USOIL", "VIX", "DXY"]:
            price_data = None
            
            # Try DataHub first
            if DATA_HUB_AVAILABLE:
                try:
                    backend_sym = {
                        "XAUUSD": "XAUUSD",
                        "NDX": "NDX.INDX",
                        "DAX": "GDAXI.INDX",
                        "USOIL": "CL.COMM",
                        "VIX": "VIX.INDX",
                        "DXY": "DXY.INDX",
                    }.get(symbol, symbol)
                    
                    price = get_price(backend_sym)
                    if price:
                        price_data = {
                            "price": price,
                            "change": 0,
                            "changePercent": 0,
                            "available": True
                        }
                except Exception as e:
                    print(f"[Prices] DataHub error for {symbol}: {e}")
            
            # Fallback to mock if no data
            if not price_data:
                mock = MOCK_PRICES.get(symbol, {"price": 0, "change": 0, "changePercent": 0})
                price_data = {**mock, "available": True, "mock": True}
            
            prices[symbol] = price_data
        
        return {
            "success": True,
            "data": prices,
            "source": "datahub" if DATA_HUB_AVAILABLE else "mock",
            "count": len(prices)
        }
        
    except Exception as e:
        print(f"[Prices] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {k: {**v, "available": True} for k, v in MOCK_PRICES.items()}
        }

@router.get("/{symbol}")
async def get_symbol_price(symbol: str) -> Dict[str, Any]:
    """Get current price for a specific symbol"""
    try:
        # Try DataHub first
        if DATA_HUB_AVAILABLE:
            backend_sym = {
                "XAUUSD": "XAUUSD",
                "NDX": "NDX.INDX",
                "DAX": "GDAXI.INDX",
                "USOIL": "CL.COMM",
                "VIX": "VIX.INDX",
                "DXY": "DXY.INDX",
            }.get(symbol.upper(), symbol.upper())
            
            price = get_price(backend_sym)
            
            if price:
                return {
                    "success": True,
                    "symbol": symbol,
                    "price": price,
                    "timestamp": datetime.utcnow().isoformat(),
                }
        
        # Fallback to mock
        mock = MOCK_PRICES.get(symbol.upper(), {"price": 0})
        return {
            "success": True,
            "symbol": symbol,
            "price": mock["price"],
            "mock": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }

from datetime import datetime
