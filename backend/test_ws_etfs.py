import asyncio
import json
import websockets

API_TOKEN = '6989161fc498d3.47082906'

async def test_ws():
    try:
        async with websockets.connect(f"wss://ws.eodhistoricaldata.com/ws/us?api_token={API_TOKEN}") as ws:
            symbols = "QQQ,USO,GLD,EWG,SPY"
            print(f"✅ Baglandi. Subscribe: {symbols}")
            await ws.send(json.dumps({
                "action": "subscribe",
                "symbols": symbols
            }))
            
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    if data.get('p') is not None:
                        print(f"{data.get('s')} | Fiyat: {data.get('p')}")
                except asyncio.TimeoutError:
                    pass
    except BaseException as e:
        print(f"Hata: {e}")

if __name__ == '__main__':
    asyncio.run(test_ws())
