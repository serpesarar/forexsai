import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def main():
    symbols = ["XAU-USD.CC", "GOLD.COMM", "GC", "GC.COMM", "WTI.COMM", "USO", "OIL.COMM", "USOIL"]
    async with httpx.AsyncClient() as client:
        for sym in symbols:
            print(f"\n--- Testing {sym} ---")
            try:
                rt = await client.get(f"https://eodhistoricaldata.com/api/real-time/{sym}", params={"api_token": API_TOKEN, "fmt": "json"})
                print(f"Real-time {sym}: {rt.text[:150]}")
            except Exception as e:
                pass
            
            try:
                intra = await client.get(f"https://eodhistoricaldata.com/api/intraday/{sym}", params={"api_token": API_TOKEN, "fmt": "json", "interval": "5m", "limit": 1})
                try:
                    data = intra.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"Intraday {sym} Last Tick: {data[-1]}")
                except:
                    print(f"Intraday {sym}: {intra.text[:100]}")
            except Exception as e:
                pass

if __name__ == '__main__':
    asyncio.run(main())
