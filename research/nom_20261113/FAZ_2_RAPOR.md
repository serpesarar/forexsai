# FAZ 2 — Özellik mühendisliği (NOM, 2026-11-13)

Kod (tek kod yolu, eğitim = canlı): `backend/services/nom/features.py`, `backend/services/nom/bars.py`.
Testler: `backend/tests/test_nom_features.py` (sentetik), `src/faz2_audit.py` (gerçek veri).
Çıktı: `data/features_v1.parquet` (321.841 karar × 132 özellik), `results/faz2_feature_catalog.csv` (tanım, TF, gecikme,
NaN payı, sızıntı testi, önem), `results/faz2_importance_*.csv`, `results/faz2_leak_real.json`.

## Katalog (132 özellik)
| Grup | Adet | İçerik |
|---|---|---|
| M5 / M15 / H1 / H4 / D1 göstergeleri | 5 / 22 / 24 / 3 / 6 | RSI 7/14/21 + eğim + uyumsuzluk, MACD hist/ATR, Stokastik, ROC/ATR, EMA20/50/200 uzaklık+eğim+dizilim, ADX, Kaufman ER, Bollinger genişlik/%B/sıkışma, PSAR (H1), ATR rejim oranı |
| Seviyeler (ölçülmüş S/R) | 21 | M15/H1/D1 fraktal pivotları (k bar sonra teyit), önceki gün H/L/C, gece H/L, ORB15 H/L, 20 gün H/L, yuvarlak 100/500/1000; en yakın üst/alt uzaklık (ATR H1), aradaki "oda", ±0,5 ATR içindeki seviye sayısı, en yakın seviyenin test sayısı ve son testten geçen saat |
| Gün-içi (1m) | 25 | gerçekleşen oynaklık 30/120 dk / 10 gün medyanı, çarpıklık, en büyük 1m hareket, ardışık bar dizisi, 15/60 dk getiri, seans aralığı/ADR, seans içi konum, nakit açılış boşluğu, TWAP z, H1 yapısı (HH/HL), ATR oranları |
| Zaman/takvim | 10 + 6 | NY dakikası (sin/cos), seans fazı, gün, yarım gün, tatil, ay sonu/başı, nakit açılış/kapanışa dakika; FOMC/CPI/NFP/bilanço öncesi/sonrası dakika |
| Günlük makro | 16 | VIX düzey/1-5g değişim/252g yüzdelik/≥18,4, VIX9D/VIX, VIX/VIX3M, NDX−SPX 5g göreli güç, NDX 1/5g, DXY 1/5g, TNX düzey/5g, NDX–TNX 20g korelasyon, QQQ hacim z |

Bilinçli dışlananlar: **hacim** ve **spread** (eğitim/canlı tanım uyuşmazlığı, Faz 0), D1 EMA200 (240 gün canlı
pencerede yakınsamaz), **MiroShark 9-ajan bias'ı**: `bias_test_log`'da NDX için yalnız 21 gün (2026-07-09 → 08-10)
var ve tamamı kilitli final test döneminde → eğitimde kullanılamaz; sızıntısızlık kanıtı bu nedenle konu dışı kaldı.

## Sızıntı ve eğitim/servis eşdeğerliği
1. **Sentetik (pytest, 6/6 geçti):** (i) t'de kesilmiş veriyle hesap = tam veri, 12 rastgele an × 132 özellik birebir;
   (ii) t sonrası barlar ±50 puan rastgele bozulunca t'deki hiçbir özellik değişmiyor; (iii) makro d günü değeri
   17:10 ET'de görünmüyor, 18:05 ET'de görünüyor; (iv–vi) etiket: aynı bar → SL, giriş sürtünmeli, ufuk dışı bar etkisiz.
2. **Gerçek veri:** 25 rastgele karar anında 400 günlük önekle yeniden hesap = tam geçmiş hesabı, **0 uyuşmazlık**
   (tüm 132 özellik "GEÇTİ").
3. **Canlı pencere yeterliliği:** 75 günlük 1m penceresi D1 özelliklerini %6–20 saptırdı (Wilder/EMA ısınması) →
   `LIVE_HISTORY_DAYS = 240`; 240 günde >%1 sapan özellik **yok**.
HTF kuralı yapısal: her HTF barı kapanış zamanı (`end`) taşır, karar anı t'de yalnız `end ≤ t` görülür; pivotlar
k bar sonra teyit edilir. mom_cont tipi sol-etiket sızıntısı (E16) bu tasarımda oluşamaz ve testle yakalanır.

## Önem (geliştirme dönemi: eğit 2021-12→2024-12, değerlendir 2025; final dokunulmadı)
Log-loss becerisi (düz iklim tabanına göre): 1s long 0,125 · 1s short 0,129 · 4s long 0,150 · 15dk long 0,082.

En önemli özellikler (permütasyon Δlog-loss, TreeSHAP ile aynı sıra):
- **1s long 1/1:** NY dakikası (sin 0,090, cos 0,021), seans fazı 0,025, M15 ATR oranı 0,007, kapanışa dakika 0,005,
  rv30 oranı 0,004, H1 ATR oranı 0,003 … ilk yön-bilgili özellik **M5 RSI14 0,0012**, ret15 0,0012.
- **4s long 1/1:** NY dakikası (0,110 / 0,084), tatil 0,012, ATR M5/H1 0,008, seans fazı 0,007, bilanço/CPI'ya dakika,
  VIX9D/VIX, ORB tepesine uzaklık.
- 132 özelliğin 45'i (1s) / 58'i (4s) değerlendirme döneminde ≤ 0 katkı.

**Okuma:** Becerinin büyük kısmı **günün saati ve oynaklık rejimi** — yani bariyere ulaşma hızı (P(zaman aşımı)
ve |hareket|). Yön bilgisi taşıyabilecek özellikler (RSI, EMA, seviye uzaklığı, TWAP z) permütasyonda iki büyüklük
mertebesi küçük. Bu, Faz 0'daki ön beklentiyle (GC-02, DTS-03) tutarlı. Düz iklim tabanı bu yüzden yetersiz bir
rakip: Faz 4'te taban **NY saati kovasına göre iklim** olacak (ön kayıt §E); asıl soru bunun üstünde beceri kalıp
kalmadığıdır. Özellik ayıklama yapılmadı (seçim yanlılığı riski); düşük katkılılar ağaçta zaten ağırlık almıyor.
