$ARGUMENTS sembolü için sinyal pipeline'ını baştan sona debug et.

## 1. MT5 Bridge & Redis Katmanı
1. Redis bağlantısı aktif mi? `mt5_redis_client.py` çalışıyor mu?
2. `mt5:tick` pub/sub kanalından son tick ne zaman geldi? Gecikme var mı?
3. `mt5:bar:5m` stream'inde bu sembol için son bar timestamp'i nedir?
4. Bar verisi beklenen formatta mı? (symbol, open, high, low, close, volume, timestamp, closed=true)

## 2. DataHub Katmanı
5. DataHub'da bu sembol için `_prices` kaydı var mı? Source etiketi ne? (`mt5_redis` / `yahoo_fallback`)
6. `_candles_5m` dolu mu? Kaç bar var? Son bar timestamp'i güncel mi?
7. Türetilmiş timeframe'ler kontrol et:
   - 15m → `derived_from_5m` mi?
   - 30m → `derived_from_5m` mi?
   - 1h → XAUUSD için `derived_from_30m`, diğerleri `derived_from_5m` mi?
   - 4h → `derived_from_30m` mi?
8. `persistent_cache` ile memory cache tutarlı mı? (Supabase candle_cache karşılaştır)

## 3. data_fetcher.py & market_data_service.py
9. `fetch_latest_price(symbol)` → DataHub'dan doğru fiyat dönüyor mu?
10. `fetch_ohlc_data(symbol, "5m", 300)` → 300 bar dolu mu, eksik/boş slot var mı?
11. Herhangi bir MT5/yfinance çağrısı tetikleniyor mu? (Olmamalı — fiyat/mum için MT5/yfinance kullanılmıyor)

## 4. Model Katmanı — Her model için ayrı ayrı
12. ML: Feature hesaplaması (150+ indikatör) hatasız mı? Prediction olasılıkları nedir?
13. PULSE 1: 6 bileşen skoru tek tek nedir? Toplam skor?
14. PULSE 2: ML confidence + EMA + MACD üçlüsü ne diyor?
15. PULSE 3: 5m(%50) + 1H(%30) + 4H(%20) skorları ayrı ayrı?
16. EMEL: 9 kontrol noktası skorları ve final karar?
17. SMC: Aktif order block'lar, FVG'ler, yapı (CHoCH/BOS)?

## 5. Meta Katman
18. Market Regime: Tespit edilen rejim nedir? ADX değeri?
19. Regime→Ağırlık mapping doğru uygulanıyor mu?
20. ATH zone aktif mi?
21. Fake signal timeout var mı?

## 6. Ensemble & Lifecycle
22. Her modelin ağırlıklı katkısı nedir?
23. Final sinyal direction + confidence nedir?
24. TP1/TP2/TP3/TP4 ve SL hedefleri hesaplandı mı?
25. prediction_logs'taki son 10 kayıt
26. Aktif sinyal var mı? Cooldown'da mı?
27. Portfolio risk durumu (%3 limit)

Sonuçları adım adım, her katmanda değerleri göstererek raporla.
Veri katmanında sorun varsa (Redis lag, DataHub boş, türetme hatası) önce onu çöz — model katmanına geçme.
Sorun tespit edersen root cause ve fix önerisi sun.
