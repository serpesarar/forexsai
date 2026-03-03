import asyncio
import json
import logging
import websockets

API_TOKEN = '6989161fc498d3.47082906'

async def test_ws():
    print('🔍 4 Sembol Test Basliyor...\n')
    
    async def listen_stocks():
        try:
            async with websockets.connect(f"wss://ws.eodhistoricaldata.com/ws/us?api_token={API_TOKEN}") as ws:
                print('✅ [STOCKS] Baglandi (NASDAQ & DAX)')
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "symbols": "NDX,^IXIC,^GDAXI,DAX,QQQ,EWG,USOIL,XTIUSD,CL.F,BZ.F"
                }))
                
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(message)
                        if data.get('s'):
                            print(f"[STOCKS] {data.get('s')} | Fiyat: {data.get('p')} | Hacim: {data.get('v')}")
                        else:
                            print(f"[STOCKS] {data}")
                    except asyncio.TimeoutError:
                        print("[STOCKS] Waiting...")
        except BaseException as e:
            print(f"[STOCKS] Hata: {e}")

    async def listen_forex():
        try:
            async with websockets.connect(f"wss://ws.eodhistoricaldata.com/ws/forex?api_token={API_TOKEN}") as ws:
                print('✅ [FOREX] Baglandi')
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "symbols": "XAUUSD,XTIUSD,USOIL.FOREX"
                }))
                
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(message)
                        if data.get('s'):
                            print(f"[FOREX] {data.get('s')} | Fiyat: {data.get('p')}")
                        else:
                            print(f"[FOREX] {data}")
                    except asyncio.TimeoutError:
                        print("[FOREX] Waiting...")
        except BaseException as e:
            print(f"[FOREX] Hata: {e}")

    # Run for 15 seconds
    st_task = asyncio.create_task(listen_stocks())
    fx_task = asyncio.create_task(listen_forex())
    
    await asyncio.sleep(15)
    
    st_task.cancel()
    fx_task.cancel()
    print('Test bitti, kapatiliyor.')

if __name__ == '__main__':
    asyncio.run(test_ws())
