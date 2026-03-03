import asyncio
import httpx
import json

API_TOKEN = '6989161fc498d3.47082906'

async def search(query):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://eodhistoricaldata.com/api/search/{query}",
            params={"api_token": API_TOKEN, "fmt": "json", "limit": 10}
        )
        try:
            print(f"\n--- Search results for '{query}' ---")
            for item in resp.json():
                print(f"{item.get('Code')}.{item.get('Exchange')} - {item.get('Name')} ({item.get('Type')})")
        except:
            print(resp.text)

async def main():
    await search("WTI")
    await search("Crude Oil")
    await search("Gold")
    await search("XAUUSD")

if __name__ == '__main__':
    asyncio.run(main())
