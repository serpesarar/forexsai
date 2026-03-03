const WebSocket = require('ws');
const API_TOKEN = '6945c91024ee47.12893127'; // User's actual API key from .env

const wsStocks = new WebSocket(`wss://ws.eodhistoricaldata.com/ws/us?api_token=${API_TOKEN}`);
const wsForex = new WebSocket(`wss://ws.eodhistoricaldata.com/ws/forex?api_token=${API_TOKEN}`);

console.log('🔍 4 Sembol Test Başlıyor...\n');

wsStocks.onopen = () => {
  console.log('✅ [STOCKS] Bağlandı (NASDAQ & DAX)');
  wsStocks.send(JSON.stringify({
    "action": "subscribe",
    "symbols": "NDX,^IXIC,^GDAXI,DAX,QQQ,EWG,USOIL,XTIUSD,CL.COMM,CL.F,BZ.F"
  }));
};

wsStocks.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('[STOCKS]', data.s, '| Fiyat:', data.p, '| Hacim:', data.v);
};

wsStocks.onerror = (e) => console.error('[STOCKS] Hata:', e);

wsForex.onopen = () => {
  console.log('✅ [FOREX] Bağlandı');
  wsForex.send(JSON.stringify({
    "action": "subscribe",
    "symbols": "XAUUSD,XTIUSD,USOIL.FOREX"
  }));
};

wsForex.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('[FOREX]', data.s, '| Fiyat:', data.p, '| Zaman:', new Date().toLocaleTimeString());
};

wsForex.onerror = (e) => console.error('[FOREX] Hata:', e);

setTimeout(() => {
  console.log('Test bitti, kapatılıyor...');
  wsStocks.close();
  wsForex.close();
  process.exit(0);
}, 10000); // 10 saniye bekle
