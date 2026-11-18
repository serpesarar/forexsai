# Ön kayıt — Rejime bağlı vurkaç: 5 dk aşırı uzamadan kısa TP'li dönüş, yüksek oynaklık / korku rejiminde (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe ve defter

Kullanıcı: "kısa TP'li vurkaç; aşağı yukarı dalgalanmaları tespit edip her dalgada al-sat."

Defter:
- Koşulsuz scalp / dalga X: OLD-01, OLD-12, BZ-01/02, Y-01, §2.12 BTC.
- **YL-03/04:** 15 dk aşırı uzama dönüşü **gerçek** (TWAP z t −7,5) ama boyu 0,3–0,6 puan, maliyet 3,4–5,4 puan → X.

**Yeniden açma gerekçesi (yeni tanım + mekanizma):**
- Dönüş boyu oynaklıkla ölçeklenir, spread ölçeklenmez. Yüksek oynaklık / korku rejiminde dönüş / maliyet oranı 1'i geçebilir.
- Yön ayrılır: düşüşü al ("korku döner") ve yükselişi sat ("coşku dönmez" uyarısıyla).
- YL-04 yalnız SHORT'u ve rejimsiz hâli sınamıştı.

## 1. Tanım (NDX Dukascopy 1m)

**Dalga tespiti:**
- 5m mumlar. Her 5m kapanışında (09:45–15:30 RTH): μ = son 12 kapanışın ortalaması, σ = son 12 kapanışın standart sapması,
  z = (kapanış − μ)/σ.
- **AL:** z ≤ −zt. **SAT:** z ≥ +zt. zt ∈ {2,0, 2,5}.

**Rejim (karar anında bilinen):**
- R0: hepsi.
- R1: dünkü VIX ≥ 25.
- R2: dünkü RTH aralığı ≥ %2.
- R3: anlık oynaklık — son 12 adet 5m (h−l) ortalaması ≥ 2 × önceki ~20 günün (1.560 adet 5m) medyanı.

**Geometri (σ birimi):** TP / SL = {0,5 / 1,0, 1,0 / 1,0, 1,0 / 2,0}. Zaman durdurma 30 dk.

**İcra:**
- 5m kapanışından sonraki 1m açılışında, gerçek spread (AL ask, SAT bid).
- TP / SL 1m yolunda; aynı barda ikisi → SL.
- Hücre başına tek pozisyon.

**Izgara:** 4 rejim × 2 yön × 2 zt × 3 geometri = **48 hücre**. Ölçü R (risk = SL mesafesi).

## 2. Plasebo / taban

Her sinyal için aynı gün, aynı yön, aynı σ geometrisiyle rastgele bir RTH 5m kapanışında giriş; 10 kopya. "Dalga tespiti"nin
katkısı = gerçek − plasebo.

## 3. Seçim ve doğrulama

**Seçim** — ESKİ 2018-01 → 2021-10'da aday:
- n ≥ 100,
- ort R > 0 ve gün-küme P ≥ %90,
- plasebodan iyi (P ≥ %90),
- spread × 1,5 > 0.

Dondurma: en iyi 4.

**Doğrulama (hepsi) → B:**
1. YENİ ort R > 0, P ≥ %97,5, plasebodan iyi.
2. NQ 5m bağımsız beslemede ort R > 0 (5m çözünürlük, aynı mumda TP+SL → SL).
3. Spread × 1,5 > 0.

Kart için işlem başına beklenti ve yıllık işlem sayısı da raporlanır.
