$ARGUMENTS sembolü için sinyal pipeline'ını baştan sona debug et.

## Veri Katmanı
1. EODHD'den gelen raw OHLCV verisini kontrol et
2. Resample doğru çalışıyor mu? (özellikle XAUUSD 1m→5m)
3. DataHub cache'te veri var mı, TTL geçerli mi?
4. candle_cache (Supabase) ile memory cache tutarlı mı?

## Model Katmanı — Her model için ayrı ayrı:
5. ML: Feature hesaplaması (150+ indikatör) hatasız mı? Prediction olasılıkları nedir?
6. PULSE 1: 6 bileşen skoru tek tek nedir? Toplam skor?
7. PULSE 2: ML confidence + EMA + MACD üçlüsü ne diyor?
8. PULSE 3: 5m(50%) + 1H(30%) + 4H(20%) skorları ayrı ayrı?
9. EMEL: 9 kontrol noktası skorları ve final karar?
10. SMC: Aktif order block'lar, FVG'ler, yapı (CHoCH/BOS)?

## Meta Katman
11. Market Regime: Tespit edilen rejim nedir? ADX değeri?
12. Regime→Ağırlık mapping doğru uygulanıyor mu?
13. ATH zone aktif mi?
14. Fake signal timeout var mı?

## Ensemble
15. Her modelin ağırlıklı katkısı nedir?
16. Final sinyal direction + confidence nedir?
17. TP1/TP2/TP3/TP4 ve SL hedefleri hesaplandı mı?

## Lifecycle
18. prediction_logs'taki son 10 kayıt
19. Aktif sinyal var mı? Cooldown'da mı?
20. Portfolio risk durumu (%3 limit)

Sonuçları adım adım, her katmanda değerleri göstererek raporla.
Sorun tespit edersen root cause ve fix önerisi sun.
