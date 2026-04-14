Tüm 6 modelin (ML, PULSE 1, PULSE 2, PULSE 3, EMEL, SMC) sinyal üretim akışlarını kontrol et.

Her model için şu adımları uygula:
1. İlgili endpoint'in mevcut olduğunu doğrula (router dosyasında tanımlı mı?)
2. Service dosyasındaki bağımlılıkları kontrol et (import'lar çalışıyor mu?)
3. prediction_logs tablosundan o model_type için son 5 kaydı çek
4. Confidence değerlerinin scope preset aralığında olduğunu doğrula
5. Cache TTL'lerinin doğru ayarlandığını kontrol et
6. Regime service'in tüm modellere doğru ağırlık verdiğini doğrula

Sonuçları şu formatta özetle:
```
| Model    | Endpoint | Service | Son Sinyal | Confidence | Regime Ağırlık | Durum |
|----------|----------|---------|------------|------------|----------------|-------|
| ML       | ✅/❌    | ✅/❌   | BUY 14:30  | 67%        | 0.50           | OK    |
| PULSE 1  | ...      | ...     | ...        | ...        | ...            | ...   |
```

Sorun varsa çözüm önerisiyle birlikte raporla.
