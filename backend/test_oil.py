import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def search(query):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://eodhistoricaldata.com/api/search/{query}",
            params={"api_token": API_TOKEN, "fmt": "json", "limit": 50}
        )
        try:
            print(f"\n--- Search results for '{query}' ---")
            for item in resp.json():
                print(f"{item.get('Code')}.{item.get('Exchange')} - {item.get('Name')} ({item.get('Type')})")
        except:
            print(resp.text)

async def test_endpoint(sym):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://eodhistoricaldata.com/api/real-time/{sym}", params={"api_token": API_TOKEN, "fmt": "json"})
            if resp.status_code == 200:
                data = resp.json()
                if "close" in data and data["close"] != "NA":
                    print(f"✅ {sym} Real-time price: {data['close']}")
                else:
                    print(f"❌ {sym} Real-time NA: {data}")
            else:
                print(f"❌ {sym} Real-time Error: {resp.status_code}")
                
            resp2 = await client.get(f"https://eodhistoricaldata.com/api/intraday/{sym}", params={"api_token": API_TOKEN, "fmt": "json", "interval": "5m", "limit": 1})
            if resp2.status_code == 200:
                data2 = resp2.json()
                if isinstance(data2, list) and len(data2) > 0:
                    print(f"✅ {sym} Intraday price: {data2[-1].get('close')}")
                else:
                    print(f"❌ {sym} Intraday Empty: {data2}")
            else: pass
        except Exception as e:
            print(f"Error testing {sym}: {e}")

async def main():
    print("Testing potential Forex/CFD pairs for WTI Oil:")
    tests = ["XTIUSD.FOREX", "WTIUSD.FOREX", "USOIL.FOREX", "WTICOUSD.FOREX", "XBRUSD.FOREX"]
    for t in tests:
        await test_endpoint(t)
        
    await search("XTI")
    await search("Spot Crude")

if __name__ == '__main__':
    asyncio.run(main())
