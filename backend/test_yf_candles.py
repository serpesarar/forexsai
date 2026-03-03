import asyncio
import httpx

async def _fetch_yahoo_candles(yahoo_symbol: str, interval: str, limit: int) -> list:
    yf_interval = interval
    if interval == "1h": yf_interval = "60m"
    elif interval == "1d" or interval == "eod": yf_interval = "1d"
    
    yf_range = "5d"
    if yf_interval == "60m": yf_range = "1mo"
    elif yf_interval == "1d": yf_range = "1y"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval={yf_interval}&range={yf_range}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            result = resp.json()['chart']['result'][0]
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            
            candles = []
            for i in range(len(timestamps)):
                if quote['open'][i] is not None:
                    candles.append({
                        "timestamp": timestamps[i],
                        "open": quote['open'][i],
                        "high": quote['high'][i],
                        "low": quote['low'][i],
                        "close": quote['close'][i],
                        "volume": quote['volume'][i] if 'volume' in quote and quote['volume'][i] is not None else 0
                    })
            return candles[-limit:]
        return []

async def main():
    candles = await _fetch_yahoo_candles("CL=F", "5m", 2)
    print("CL=F 5m candles:", candles)

if __name__ == '__main__':
    asyncio.run(main())
