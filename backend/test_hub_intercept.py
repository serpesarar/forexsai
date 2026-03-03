import asyncio
from services.data_hub import _fetch_price_from_api, _fetch_candles_from_api

async def test():
    print("Testing US OIL...")
    price = await _fetch_price_from_api("USOIL.FOREX")
    print(f"US OIL Price: {price}")
    
    candles = await _fetch_candles_from_api("USOIL.FOREX", "5m", 2)
    print(f"US OIL Candles: {candles}")
    
    print("\nTesting Gold...")
    price2 = await _fetch_price_from_api("XAUUSD")
    print(f"Gold Price: {price2}")
    
    candles2 = await _fetch_candles_from_api("XAUUSD", "1h", 1)
    print(f"Gold Candles: {candles2}")

if __name__ == '__main__':
    asyncio.run(test())
