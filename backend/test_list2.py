import asyncio
import httpx

API_TOKEN = '6989161fc498d3.47082906'

async def get_exchange(exch):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://eodhistoricaldata.com/api/exchange-symbol-list/{exch}",
            params={"api_token": API_TOKEN, "fmt": "json"}
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                name = item.get('Name', '').upper()
                code = item.get('Code', '').upper()
                if 'XTI' in code or 'WTI' in code or 'OIL' in name or 'XTI' in name:
                    print(f"{code}.{exch} - {name} ({item.get('Type')})")
        else:
            print(f"Error for {exch}: {resp.status_code} {resp.text[:100]}")

async def main():
    await get_exchange("FOREX")

if __name__ == '__main__':
    asyncio.run(main())
