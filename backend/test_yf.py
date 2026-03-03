import asyncio
import httpx

async def get_yahoo_price(symbol):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                meta = data['chart']['result'][0]['meta']
                price = meta['regularMarketPrice']
                print(f"✅ Yahoo {symbol}: {price}")
            else:
                print(f"❌ Yahoo {symbol} Error: {resp.status_code}")
        except Exception as e:
            print(f"Error {symbol}: {e}")

async def main():
    symbols = ["GC=F", "CL=F", "^IXIC", "^GDAXI"]
    for sym in symbols:
        await get_yahoo_price(sym)

if __name__ == '__main__':
    asyncio.run(main())
