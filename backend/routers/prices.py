"""
Live Prices Router
Returns current prices for all tracked symbols
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/prices", tags=["prices"])

# Import from data_hub
from services.data_hub import get_price

# Symbol mappings
SYMBOL_MAP = {
    "XAUUSD": "XAUUSD",
    "NDX": "NDX.INDX",
    "NDX.INDX": "NDX.INDX",
    "DAX": "GDAXI.INDX",
    "GDAXI.INDX": "GDAXI.INDX",
    "USOIL": "CL.COMM",
    "CL.COMM": "CL.COMM",
    "VIX": "VIX.INDX",
    "VIX.INDX": "VIX.INDX",
    "DXY": "DXY.INDX",
    "DXY.INDX": "DXY.INDX",
}

@router.get("")
async def get_live_prices() -> Dict[str, Any]:
    """Get current prices for all tracked symbols"""
    try:
        prices = {}
        
        # Try to get prices from data_hub
        for frontend_sym, backend_sym in [
            ("XAUUSD", "XAUUSD"),
            ("NDX", "NDX.INDX"),
            ("DAX", "GDAXI.INDX"),
            ("USOIL", "CL.COMM"),
            ("VIX", "VIX.INDX"),
            ("DXY", "DXY.INDX"),
        ]:
            price = get_price(backend_sym)
            
            # If not found, try alternative keys
            if price is None:
                price = get_price(frontend_sym)
            
            prices[frontend_sym] = {
                "price": price or 0,
                "change": 0,  # DataHub doesn't store change
                "changePercent": 0,
                "timestamp": None,
                "available": price is not None
            }
        
        return {
            "success": True,
            "data": prices,
            "count": len([p for p in prices.values() if p["available"]])
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }

@router.get("/{symbol}")
async def get_symbol_price(symbol: str) -> Dict[str, Any]:
    """Get current price for a specific symbol"""
    try:
        backend_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
        price = get_price(backend_sym)
        
        if price is None:
            # Try frontend symbol directly
            price = get_price(symbol.upper())
        
        if price is None:
            return {
                "success": False,
                "error": f"Price not available for {symbol}",
                "symbol": symbol
            }
        
        return {
            "success": True,
            "symbol": symbol,
            "price": price,
            "timestamp": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }
