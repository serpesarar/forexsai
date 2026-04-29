# 🔧 Claude Code'a Yapıştıracağın Prompt

Aşağıdaki prompt'u Claude Code terminaline olduğu gibi yapıştır.
Tek seferde tüm işi yapacak.

---

```
Projemde 5 performans paneli var ve 2 aydır production'da çalışmasına rağmen bazı panellerde sadece 76-80 resolved sinyal var — bu sayı kabul edilemez düşük. Senden kapsamlı bir audit istiyorum: hem kod hem Supabase tarafını birlikte kontrol et, darboğazları bul ve düzelt.

## Supabase Erişimin Var — Şu Sorguları Çalıştır:

prediction_logs tablosundan:
1. model_type + status bazlı toplam sinyal sayıları
2. Son 60 günün günlük sinyal dağılımı (hangi günler üretim yok?)
3. Model bazlı ortalama sinyal aralığı (dakika cinsinden)
4. Status dağılımı yüzdeleriyle (expired oranı ne?)
5. market_closed_invalid etiketli sinyal sayısı
6. Cooldown/dedup'a takılan sinyal sayısı (notes alanından)
7. Confidence dağılımı (40 altı, 40-55, 55-70, 70+ grupları)
8. Son 7 gün sembol × model bazlı üretim

## 5 Paneli Tek Tek Kontrol Et:

### 1. Meta Signal Analysis (/api/meta/analyze/{symbol})
- 6 model paralel çağrısında timeout olan var mı?
- "Min 2 model BUY/SELL demezse HOLD" kuralı ne kadar sinyal engelliyor?
- meta_combination_stats tablosu yeterli veri içeriyor mu?
- tech_score 8 koşulun tamamını doğru hesaplıyor mu?
- min_confidence=40 sonrası kaç sinyal HOLD'a düşüyor?

### 2. Strategy Performance (/api/learning/strategy-performance)
- Sadece ML sinyalleri sayması doğru mu? Diğer modeller neden hariç?
- market_closed_invalid filtresi kaç sinyal siliyor?
- reliability=resolved/8 formülü — 8'den az resolved'da skor eziliyor mu?

### 3. Signal Performance (/api/learning/accuracy-by-model)
- Expired + target hit durumu çift sayılıyor mu?
- emel_inverse ayrı mı yoksa emel ile birleşik mi?
- Division by zero koruması var mı?

### 4. AI Panel Performance (/api/learning/ai-panel-performance)
- Timezone kontrolü: NY 09:30-16:00 UTC'ye doğru çevrilmiş mi?
- 60dk interval son log'dan mı yoksa sabit saatten mi hesaplanıyor?
- DeepSeek API hatalarında sinyal sessizce kayboluyor mu?
- HOLD dönen sinyaller loglanmıyor — bu ne kadar sinyal kaybettiriyor?

### 5. Smart Money Zones (/api/learning/smc-performance)
- min_score=45 eşiği kaç OB'yi filtreliyor?
- min_displacement_atr=1.0 her sembol için uygun mu?
- Cadence collapse kaç sinyali eziyor?
- 4 timeframe (5m/15m/1h/4h) hepsi aktif üretiyor mu?

## Beklentilerim:

1. **Funnel analizi yap:** Ham sinyal adayı → filtreler → cooldown → dedup → final log. Her adımda kaç sinyal kaybediliyor?

2. **Gereksiz tekrar var mı?** Signal Performance ile Strategy Performance overlap ediyor mu? Birleştirilebilir mi?

3. **Threshold'ları optimize et:** Mevcut win rate'lere göre confidence minimum'ları, cooldown süreleri ve market open kontrolleri ayarlanmalı

4. **Bulduğun sorunları direkt düzelt** — ama kırılgan değişiklikleri (threshold değiştirme gibi) yapmadan önce mevcut değeri ve yeni değeri açıkla

5. **CLAUDE.md'yi güncelle:** Panel bilgilerini, yeni threshold'ları ve değişiklikleri CLAUDE.md'ye ekle

Önce Supabase sorgularını çalıştır, sonra kod taraması yap, sonra bulguları birleştirip aksiyon al.
```
