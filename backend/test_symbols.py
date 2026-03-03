import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def search_symbol(query):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://eodhistoricaldata.com/api/search/{query}",
            params={"api_token": API_TOKEN, "fmt": "json", "limit": 10},
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
        return []

async def test_prices(symbols):
    async with httpx.AsyncClient() as client:
        results = {}
        for sym in symbols:
            try:
                resp = await client.get(
                    f"https://eodhistoricaldata.com/api/real-time/{sym}",
                    params={"api_token": API_TOKEN, "fmt": "json"},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    results[sym] = resp.json().get("close", "N/A")
                else:
                    results[sym] = f"Error {resp.status_code}"
            except Exception as e:
                results[sym] = f"Error {e}"
        return results

async def main():
    print("Testing Oil symbols...")
    oil_symbols = ["CL.COMM", "CL.F", "USOIL.FOREX", "USOIL", "WTI.COMM", "WTI", "CRUD.LSE", "USO", "BRENT.COMM"]
    oil_prices = await test_prices(oil_symbols)
    for sym, price in oil_prices.items():
        print(f"Oil {sym}: {price}")
        
    print("\nTesting Gold symbols...")
    gold_symbols = ["XAUUSD.FOREX", "XAU.FOREX", "XAUUSD", "GC.COMM", "GC.F", "XAUUSD.F"]
    gold_prices = await test_prices(gold_symbols)
    for sym, price in gold_prices.items():
        print(f"Gold {sym}: {price}")

    print("\nTesting Dax symbols...")
    dax_symbols = ["GDAXI.INDX", "DAX.INDX", "DAX", "^GDAXI"]
    dax_prices = await test_prices(dax_symbols)
    for sym, price in dax_prices.items():
        print(f"DAX {sym}: {price}")

    print("\nTesting Nasdaq symbols...")
    ndx_symbols = ["NDX.INDX", "IXIC.INDX", "^IXIC"]
    ndx_prices = await test_prices(ndx_symbols)
    for sym, price in ndx_prices.items():
        print(f"NDX {sym}: {price}")

if __name__ == '__main__':
    asyncio.run(main())
