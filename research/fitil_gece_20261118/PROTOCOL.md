# Ön kayıt — "Fitilli gece" yapısının genişletilmesi (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe

Bulunan yapı (§2.68 FK-01…03, C+): **fitilli KSG**. NDX son nakit saati aşağı ∧ son 6 sa içinde 1h büyük alt fitil (≥ %0,50,
üst ≤ alt/2) → 16:00 AL, 09:30 çık.
- Dukascopy +28,6 bp vs fitilsiz +1,9.
- MT5 +38,4 vs +3,7.
- EET30 +33,7 vs +4,4.
- NQ +26,4 vs +8,4.

**Mekanizma hipotezi:** gün içi kapitülasyon (fitil = panik satışın emilmesi) gece pozitif sürüklenmesini büyütür ("korku döner",
gecelik hâli).

Kullanıcı: "bulduğun kâr yapısını farklı bakış açılarıyla genişlet."

## 1. Veri ve dönemler

- Dukascopy NDX 1m (`lib.load_m1`).
  - **ESKİ** 2018-01 → 2021-10: seçim.
  - **YENİ** 2021-11 → 2026-11: kör doğrulama.
- Bağımsız beslemeler (doğrulama): MT5 NAS100 M30 2018-05 →, EET30 30m 2016-11 → 2025-10, NQ vadeli 5m 2019-08 → 2024-08.
- Spread: Dukascopy modeli (giriş barı) + çıkış barı. MT5 bar spread'i. EET30 1,5 puan. NQ 0,25 puan.
- Uzunda gecelik finansman.

## 2. Izgara (G1–G6, NDX)

Her işlem günü d için:

| boyut | değerler |
|---|---|
| **fitil TF** | {30m, 1h, 2h}; NY yerel saatine hizalı |
| **fitil eşiği** | alt fitil ≥ {%0,35, %0,50, %0,75} ∧ üst ≤ alt/2 |
| **pencere W** | {3, 6, 12} sa; fitil mumunun kapanışı ∈ [giriş − W, giriş] |
| **KSG koşulu** | {var: 15:00 → 16:00 (girişe kadar) getirisi < 0 · yok} |
| **giriş** | {15:30, 16:00} açılışı. 15:30 girişte KSG koşulu 15:00 → 15:30 |
| **çıkış** | {ertesi gün 04:00, 09:30, 16:00} açılışı |

Toplam: 3 × 3 × 3 × 2 × 2 × 3 = **324 hücre**. Hücre ölçüsü fitilli gecelerin ortalama net bp'si.

Aynı giriş/çıkış/KSG kombinasyonunun **fitil etiketi olmayan** geceleri "taban" sayılır.

## 3. Seçim (yalnız ESKİ)

Aday hücre:
- n_fitilli ≥ 25,
- fitilli ort > 0,
- fitilli − taban > 0,
- fark için gün-küme bootstrap P ≥ %90.

**Izgara plasebosu:** fitil mumu zamanları ±1–10 işlem günü kaydırılır (aynı saat), 20 kopya; aday sayısı dağılımı.

**Dondurma:**
- ESKİ'de fark t'sine göre en iyi en fazla 5 hücre.
- Mevcut kural (1h, %0,50, W 6, KSG var, 16:00, 09:30) ayrıca referans olarak her zaman raporlanır.
- **Yıllık işlem sayısı** ayrıca raporlanır (genişletme = daha çok işlem, benzer beklenti).

## 4. Doğrulama (dondurulmuş hücreler) — "genişletilmiş kâr yapısı" (B) ölçütü (hepsi)

1. YENİ fitilli ort > 0 ve fark P ≥ 1 − 0,10/5 = %98.
2. MT5, EET30, NQ'nun **her birinde** fitilli ort > 0 ve fitilli > taban.
3. YENİ spread × 1,5 > 0.
4. Toplam n_fitilli ≥ 150.

**Hüküm:**
- Hepsi geçerse B: kart, SHADOW, karar kullanıcıda.
- YENİ + en az 2/3 besleme geçerse C+.
- Aksi hâlde X.

## 5. G7 — mekanizma taşıması: DAX kendi seansında

DAX (Dukascopy DEUIDXEUR 1m 2018–26, aynı ESKİ / YENİ):
- Nakit kapanış 17:30 Berlin.
- "DAX-KSG": 16:30 → 17:30 Berlin getirisi < 0 ∧ son 6 sa içinde DAX 1h büyük alt fitil (aynı tanım) → 17:30 AL, ertesi gün
  09:00 Berlin açılışında çık.

Kural ve parametreler NDX'ten aynen. Tek hücre, seçim yok.

Geçme: ESKİ ve YENİ'nin ikisinde fitilli > 0 ve > taban, tüm dönem fark P ≥ %90.

Geçerse mekanizma piyasalar arası (A−); geçmezse NDX'e özgü.
