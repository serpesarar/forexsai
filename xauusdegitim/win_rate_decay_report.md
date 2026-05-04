# Win-Rate Decay Pattern Analizi
_2026-05-04T02:57:20.596674Z — son 90 gün — rolling window 50_

**Yöntem:** Her sinyal için rolling win-rate ve rolling feature mean hesapla; Pearson korelasyon her özelliğin win-rate trendiyle birlikte hareketini ölçer.
**Yorum:**
- 🟢 (+0.3 üstü): feature artarken win-rate de artıyor — pozitif sinyal kaynağı
- 🔴 (-0.3 altı): feature artarken win-rate düşüyor — regime-shift uyarı feature'ı, yeni eğitimde inverse weight olarak kullan
- ⚪ (-0.3 / +0.3 arası): zayıf ilişki — büyük olasılıkla noise

Yeni model eğitiminde bu içgörüleri **prior** olarak kullanabilirsin: kırmızı feature'lar regime-shift uyarısı, yeşiller ise sinyal pekiştirmesi.

---

## GLOBAL — tüm sembol & model
- Sinyal sayısı: **50000**  ·  Baseline win-rate: **64.03%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · emel
- Sinyal sayısı: **171**  ·  Baseline win-rate: **73.1%**
- Win-rate dalga genişliği: **+28.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · meta
- Sinyal sayısı: **180**  ·  Baseline win-rate: **84.44%**
- Win-rate dalga genişliği: **+24.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · ml:balanced
- Sinyal sayısı: **115**  ·  Baseline win-rate: **74.78%**
- Win-rate dalga genişliği: **+22.3pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · ml:full_power
- Sinyal sayısı: **142**  ·  Baseline win-rate: **74.65%**
- Win-rate dalga genişliği: **+15.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · ml:main
- Sinyal sayısı: **168**  ·  Baseline win-rate: **77.38%**
- Win-rate dalga genişliği: **+28.7pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · pulse1
- Sinyal sayısı: **1494**  ·  Baseline win-rate: **58.37%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · pulse2
- Sinyal sayısı: **674**  ·  Baseline win-rate: **74.04%**
- Win-rate dalga genişliği: **+72.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · pulse3
- Sinyal sayısı: **1272**  ·  Baseline win-rate: **70.2%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## GDAXI.INDX · smc
- Sinyal sayısı: **273**  ·  Baseline win-rate: **58.24%**
- Win-rate dalga genişliği: **+98.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · emel
- Sinyal sayısı: **201**  ·  Baseline win-rate: **53.73%**
- Win-rate dalga genişliği: **+68.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · meta
- Sinyal sayısı: **159**  ·  Baseline win-rate: **81.76%**
- Win-rate dalga genişliği: **+32.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · ml
- Sinyal sayısı: **116**  ·  Baseline win-rate: **78.45%**
- Win-rate dalga genişliği: **+12.8pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · ml:balanced
- Sinyal sayısı: **100**  ·  Baseline win-rate: **81.0%**
- Win-rate dalga genişliği: **+17.8pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · ml:main
- Sinyal sayısı: **102**  ·  Baseline win-rate: **75.49%**
- Win-rate dalga genişliği: **+18.7pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · pulse1
- Sinyal sayısı: **1239**  ·  Baseline win-rate: **65.21%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · pulse2
- Sinyal sayısı: **840**  ·  Baseline win-rate: **72.02%**
- Win-rate dalga genişliği: **+68.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## NDX.INDX · pulse3
- Sinyal sayısı: **1152**  ·  Baseline win-rate: **64.41%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · emel
- Sinyal sayısı: **1149**  ·  Baseline win-rate: **64.32%**
- Win-rate dalga genişliği: **+68.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · meta
- Sinyal sayısı: **646**  ·  Baseline win-rate: **71.05%**
- Win-rate dalga genişliği: **+56.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml
- Sinyal sayısı: **278**  ·  Baseline win-rate: **56.83%**
- Win-rate dalga genişliği: **+28.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml:aggressive
- Sinyal sayısı: **148**  ·  Baseline win-rate: **76.35%**
- Win-rate dalga genişliği: **+22.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml:balanced
- Sinyal sayısı: **1010**  ·  Baseline win-rate: **70.2%**
- Win-rate dalga genişliği: **+54.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml:full_power
- Sinyal sayısı: **1045**  ·  Baseline win-rate: **70.43%**
- Win-rate dalga genişliği: **+52.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml:main
- Sinyal sayısı: **1174**  ·  Baseline win-rate: **70.7%**
- Win-rate dalga genişliği: **+54.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · ml:ultra_safe
- Sinyal sayısı: **124**  ·  Baseline win-rate: **80.65%**
- Win-rate dalga genişliği: **+30.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · pulse1
- Sinyal sayısı: **6678**  ·  Baseline win-rate: **70.74%**
- Win-rate dalga genişliği: **+64.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · pulse2
- Sinyal sayısı: **5219**  ·  Baseline win-rate: **70.86%**
- Win-rate dalga genişliği: **+90.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · pulse3
- Sinyal sayısı: **6245**  ·  Baseline win-rate: **71.14%**
- Win-rate dalga genişliği: **+68.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## USOIL.FOREX · smc
- Sinyal sayısı: **2422**  ·  Baseline win-rate: **85.3%**
- Win-rate dalga genişliği: **+58.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · emel
- Sinyal sayısı: **464**  ·  Baseline win-rate: **38.58%**
- Win-rate dalga genişliği: **+70.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · meta
- Sinyal sayısı: **571**  ·  Baseline win-rate: **64.97%**
- Win-rate dalga genişliği: **+58.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · ml:aggressive
- Sinyal sayısı: **139**  ·  Baseline win-rate: **44.6%**
- Win-rate dalga genişliği: **+44.6pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · ml:balanced
- Sinyal sayısı: **612**  ·  Baseline win-rate: **51.96%**
- Win-rate dalga genişliği: **+68.5pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · ml:full_power
- Sinyal sayısı: **648**  ·  Baseline win-rate: **48.61%**
- Win-rate dalga genişliği: **+62.8pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · ml:main
- Sinyal sayısı: **681**  ·  Baseline win-rate: **49.63%**
- Win-rate dalga genişliği: **+58.8pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · ml:ultra_safe
- Sinyal sayısı: **110**  ·  Baseline win-rate: **43.64%**
- Win-rate dalga genişliği: **+50.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · pulse1
- Sinyal sayısı: **3986**  ·  Baseline win-rate: **40.94%**
- Win-rate dalga genişliği: **+94.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · pulse2
- Sinyal sayısı: **2467**  ·  Baseline win-rate: **49.01%**
- Win-rate dalga genişliği: **+98.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · pulse3
- Sinyal sayısı: **3694**  ·  Baseline win-rate: **51.6%**
- Win-rate dalga genişliği: **+100.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---

## XAUUSD · smc
- Sinyal sayısı: **1375**  ·  Baseline win-rate: **49.24%**
- Win-rate dalga genişliği: **+82.0pp** (rolling window=50 sinyal)

_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._

---
