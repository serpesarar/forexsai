# News AI Panel - Gap Fix, Veri Limiti & Modal Entegrasyonu

## Adımlar

- [x] **1. Backend: `data_hub.py` - Volume filtresi gevşetme**
  - `get_candles()` fonksiyonundaki `volume > 0` filtresini kaldırdık
  - Sadece tamamen geçersiz mumları (open=high=low=close=0) filtreliyoruz

- [x] **2. Frontend: `NewsChartCorrelationPanel.tsx` - Gap Fix**
  - `buildActualTimeChartCandles` yerine `buildTimelineChartCandles` kullanıldı
  - Grafik render'da `time: index` yerine timeline time kullanıldı
  - `tickMarkFormatter` güncellendi (actualTimestamp ile gerçek tarih)

- [x] **3. Frontend: `NewsChartCorrelationPanel.tsx` - Marker Eşleştirme**
  - `mappedNewsMarkers` useMemo'su `buildMappedChartMarkers` ile güncellendi
  - Timeline time bazlı eşleştirme yapılıyor

- [x] **4. Frontend: `NewsChartCorrelationPanel.tsx` - Mum Tıklama + Modal**
  - `subscribeClick` handler'ı `findTimelineChartCandle` ile güncellendi
  - `actualTimestamp` üzerinden haber eşleştirmesi yapılıyor
  - `NewsDetailModal` component'i entegre edildi (inline modal kaldırıldı)

- [x] **5. Test & Doğrulama**
  - TypeScript build test başarılı (tsc --noEmit)
