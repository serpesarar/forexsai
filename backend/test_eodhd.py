import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def test_endpoint(url):
    print(f"\n--- Testing {url} ---")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"api_token": API_TOKEN, "fmt": "json"})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"Success! Last item: {data[-1]}")
            else:
                print(f"Data: {data}")
        else:
            print(f"Error {resp.status_code}: {resp.text[:100]}")

async def main():
    endpoints = [
        "https://eodhistoricaldata.com/api/intraday/XAUUSD.FOREX?interval=1m&limit=1",
        "https://eodhistoricaldata.com/api/intraday/USOIL.FOREX?interval=1m&limit=1",
        "https://eodhistoricaldata.com/api/intraday/CL.COMM?interval=5m&limit=1",
        "https://eodhistoricaldata.com/api/eod/XAUUSD.FOREX?limit=1",
        "https://eodhistoricaldata.com/api/eod/USOIL.FOREX?limit=1",
        "https://eodhistoricaldata.com/api/eod/CL.COMM?limit=1"
    ]
    for ep in endpoints:
        await test_endpoint(ep)

if __name__ == '__main__':
    asyncio.run(main())
