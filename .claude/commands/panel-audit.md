Bu proje 2 aydır production'da çalışıyor ama bazı panellerde sadece 76-80 resolved sinyal var — bu sayı çok düşük. Tüm sinyal pipeline'ını hem kod hem Supabase tarafından audit et.

---

## FAZA 1 — Supabase Veri Denetimi (Önce veriyi anla)

prediction_logs tablosundan şu sorguları çalıştır:

```sql
-- 1. Toplam sinyal sayısı, model bazlı
SELECT model_type, status, COUNT(*) 
FROM prediction_logs 
GROUP BY model_type, status 
ORDER BY model_type, status;

-- 2. Günlük sinyal dağılımı (hangi günler sinyal üretilmiş, hangileri boş?)
SELECT DATE(created_at) as day, model_type, COUNT(*) 
FROM prediction_logs 
GROUP BY day, model_type 
ORDER BY day DESC LIMIT 60;

-- 3. Sinyal aralıkları — ortalama iki sinyal arası süre
SELECT model_type, 
       AVG(EXTRACT(EPOCH FROM (lead_time - created_at))) / 60 as avg_gap_minutes
FROM (
  SELECT model_type, created_at,
         LEAD(created_at) OVER (PARTITION BY model_type, symbol ORDER BY created_at) as lead_time
  FROM prediction_logs
) sub
WHERE lead_time IS NOT NULL
GROUP BY model_type;

-- 4. Status dağılımı — expired çok mu yüksek?
SELECT model_type, status, COUNT(*),
       ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER (PARTITION BY model_type) * 100, 1) as pct
FROM prediction_logs
GROUP BY model_type, status;

-- 5. market_closed_invalid kaç tane var?
SELECT model_type, COUNT(*) 
FROM prediction_logs 
WHERE status = 'market_closed_invalid' OR notes LIKE '%market_closed%'
GROUP BY model_type;

-- 6. Cooldown'a takılan sinyaller var mı?
SELECT model_type, COUNT(*) 
FROM prediction_logs 
WHERE notes LIKE '%cooldown%' OR notes LIKE '%duplicate%' OR notes LIKE '%dedup%'
GROUP BY model_type;

-- 7. Confidence dağılımı — threshold'a takılan sinyaller
SELECT model_type,
       COUNT(CASE WHEN confidence < 40 THEN 1 END) as below_40,
       COUNT(CASE WHEN confidence BETWEEN 40 AND 55 THEN 1 END) as range_40_55,
       COUNT(CASE WHEN confidence BETWEEN 55 AND 70 THEN 1 END) as range_55_70,
       COUNT(CASE WHEN confidence > 70 THEN 1 END) as above_70
FROM prediction_logs
GROUP BY model_type;

-- 8. Son 7 gündeki sembol bazlı üretim
SELECT symbol, model_type, COUNT(*)
FROM prediction_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY symbol, model_type
ORDER BY symbol, model_type;
```

Bu sorguların sonuçlarını analiz et ve darboğazları tespit et.

---

## FAZA 2 — Panel Kod Denetimi (5 Panel Tek Tek)

### Panel 1: Meta Signal Analysis (`/api/meta/analyze/{symbol}`)
Kontrol et:
- [ ] 6 model paralel çağrılıyor mu? Hangisi timeout'a düşüyor?
- [ ] "Minimum 2 model BUY/SELL demezse HOLD" kuralı çok katı mı?
- [ ] meta_combination_stats tablosu boş mu veya yetersiz veri mi var?
- [ ] tech_score hesaplaması 8 koşulun hepsini doğru kontrol ediyor mu?
- [ ] final_confidence clamp(0-100) sonrası min_confidence (40) altına mı düşüyor?
- [ ] Cache TTL 55s — çok sık invalidation olup tekrar hesaplama mı yapılıyor?

### Panel 2: Strategy Performance Analysis (`/api/learning/strategy-performance`)
Kontrol et:
- [ ] Sadece ML model sinyallerini sayıyor — diğer modeller neden hariç?
- [ ] `model_type.startswith('ml')` filtresi doğru çalışıyor mu?
- [ ] `market_closed_invalid` filtresi çok agresif mi? Kaç sinyal siliyor?
- [ ] `reliability = clamp(0-1, resolved/8)` — 8'den az resolved varsa skor eziliyor
- [ ] `quality_score` formülündeki ağırlıklar mantıklı mı?
- [ ] Lider seçimi `≥3 resolved` — bu threshold uygun mu?

### Panel 3: Signal Performance (`/api/learning/accuracy-by-model`)
Kontrol et:
- [ ] `status != "active"` filtresi — expired sinyaller doğru sayılıyor mu?
- [ ] Expired ama target hit olan sinyaller hem expired hem target_hit'e mi ekleniyor?
- [ ] ml_accuracy hesaplamasında division by zero koruması var mı?
- [ ] Tüm model_type'lar doğru gruplanıyor mu? (emel_inverse ayrı mı sayılıyor?)

### Panel 4: AI Panel Signal Performance (`/api/learning/ai-panel-performance`)
Kontrol et:
- [ ] `is_primary_session_open OR is_us_cash_open` kontrolü doğru timezone'da mı?
- [ ] NY 09:30-16:00 saati UTC'ye doğru çevrilmiş mi?
- [ ] DeepSeek API timeout/error durumlarında sinyal loglanmıyor mu?
- [ ] 60 dakikalık interval — son çağrıdan beri 60dk geçti kontrolü nasıl?
- [ ] HOLD dönen sinyaller loglanmıyor — bu çok sinyal kaybettiriyor mu?

### Panel 5: Smart Money Zones Performance (`/api/learning/smc-performance`)
Kontrol et:
- [ ] `min_score = 45` çok yüksek mi? Kaç OB bu eşiği geçemiyor?
- [ ] `max_tests = 3` — 3 test sonrası invalidation doğru çalışıyor mu?
- [ ] `min_displacement_atr = 1.0` — bazı enstrümanlarda çok katı mı?
- [ ] Cadence collapse kaç sinyali eziyor?
- [ ] 4 timeframe (5m, 15m, 1h, 4h) hepsi aktif üretiyor mu?

---

## FAZA 3 — Darboğaz Analizi

Veri + kod bulgularını birleştirerek şu soruları cevapla:

1. **Hangi model en az sinyal üretiyor?** Neden?
2. **Cooldown + dedup kaç sinyali engelliyor?** Oranı makul mü?
3. **Market open kontrolü doğru mu?** Hafta sonları haricinde gereksiz blok var mı?
4. **Confidence threshold'ları çok mu yüksek?** Ortalama confidence nedir?
5. **Expired sinyal oranı nedir?** %50'den fazlaysa TP/SL mesafeleri yanlış
6. **Signal lifecycle 3dk interval** — sinyal TP/SL vurduğunda 3dk geç mi kalıyor?

---

## FAZA 4 — Optimizasyon Önerileri

Bulguları değerlendir ve şunları öner (veya direkt uygula):

### Gereksiz Tekrar Kontrolü
- Signal Performance ile Strategy Performance arasında overlap var mı?
- Aynı sinyal birden fazla panelde farklı sayılıyor mu?
- Birleştirilebilecek paneller var mı?

### Threshold Optimizasyonu
- Confidence minimum'larını güncel win rate'e göre ayarla
- Cooldown sürelerini sinyal sıklığına göre optimize et
- Market open saatlerini sembol bazlı doğrula

### Pipeline Sağlığı
- Hangi adımda en çok sinyal kaybediliyor? (funnel analizi)
- Log seviyesi yeterli mi? Debug için eksik log var mı?
- Error handling sessiz fail yapıyor mu?

---

## ÇIKTI FORMATI

Sonuçları şu şekilde raporla:

```
## 🔍 AUDIT SONUÇLARI

### Supabase Verileri
[Sorgu sonuçları özet tablo]

### Panel Bazlı Bulgular
| Panel | Durum | Sorun | Önerilen Fix |
|-------|-------|-------|-------------|
| Meta Signal | ⚠️ | ... | ... |
| Strategy Perf | ✅ | ... | ... |
| ... | ... | ... | ... |

### Darboğaz Sıralaması (en kritikten başla)
1. [En çok sinyal kaybettiren sorun]
2. ...

### Uygulanan Değişiklikler
- [x] dosya.py: satır X — threshold 58→52 düşürüldü
- [x] ...

### Önerilen Ama Onay Bekleyen Değişiklikler
- [ ] ...
```
