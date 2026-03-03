import asyncio
import json
import websockets

API_TOKEN = '6989161fc498d3.47082906'

async def test_ws():
    async def listen_endpoint(endpoint, symbols):
        try:
            async with websockets.connect(f"wss://ws.eodhistoricaldata.com/ws/{endpoint}?api_token={API_TOKEN}") as ws:
                print(f"✅ [{endpoint.upper()}] Baglandi. Subscribe: {symbols}")
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "symbols": symbols
                }))
                
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        data = json.loads(message)
                        # Print only if price is present OR if it's an error message
                        if data.get('p') is not None:
                            print(f"[{endpoint.upper()}] {data.get('s')} | Fiyat: {data.get('p')}")
                        elif data.get('status_code'):
                            print(f"[{endpoint.upper()}] {data}")
                    except asyncio.TimeoutError:
                        pass
        except BaseException as e:
            print(f"[{endpoint.upper()}] Hata: {e}")

    # Test batches to avoid max symbols limits
    us_symbols_1 = "NDX,NDX.INDX,^IXIC,.IXIC,IXIC,QQQ,DAX,^GDAXI"
    us_symbols_2 = "USO,CL.F,BZ.F,USOIL"
    fx_symbols = "XAUUSD,EURUSD,XTIUSD,BRENT"
    
    t1 = asyncio.create_task(listen_endpoint("us", us_symbols_1))
    t2 = asyncio.create_task(listen_endpoint("us", us_symbols_2))
    t3 = asyncio.create_task(listen_endpoint("forex", fx_symbols))
    
    await asyncio.sleep(15)
    
    t1.cancel()
    t2.cancel()
    t3.cancel()
    print('Test bitti.')

if __name__ == '__main__':
    asyncio.run(test_ws())
