import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def test_endpoint(sym):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://eodhistoricaldata.com/api/real-time/{sym}", params={"api_token": API_TOKEN, "fmt": "json"})
            if resp.status_code == 200:
                data = resp.json()
                if "close" in data and str(data["close"]) != "NA":
                    print(f"✅ {sym} Real-time price: {data['close']}")
                else:
                    print(f"❌ {sym} Real-time NA")
            else:
                print(f"❌ {sym} Real-time Error: {resp.status_code}")
        except Exception as e:
            pass

async def main():
    print("Testing additional symbols for WTI Crude...")
    tests = ["WTIC.INDX", "WTI.INDX", "USOIL", "WTICO", "USOIL.CC", "CL", "WTI.CC", "UCO", "WTI.US"]
    for t in tests:
        await test_endpoint(t)

if __name__ == '__main__':
    asyncio.run(main())
