# QS-02 — QS-01'den türeyen senaryo ailesi: "coşku kırılması" ve kardeşleri — ön kayıt (2026-11-11)

Kullanıcı: "QS-01'i baz alarak farklı araştırmalar türet; özellikle bütün gün güçlü yükselişten sonra ertesi gün aşağı
boşlukla açılış. Farklı farklı açılardan düşün." Bu dosya sonuçlar görülmeden yazıldı; hücre listesi kapalıdır.

## Defter taraması / yeniden açma gerekçesi
- GF-02 H3 koşulsuz açılış boşluğu fade/go (09:30–10:15) X; ME-06(e) "önceki gün + boşluk" şekil eşleştirmesi X;
  FC-06/07 boşlukla hizalı kırılım X; GF-12 coşku aynası (dün ≥ +%1,5 → BUY yok) X — "korku döner, coşku dönmez" (§3-2).
- **Yeni olan:** iki günlük DİZİ koşulu (dün güçlü yön günü ∧ bugün ters/aynı yön boşluk) × gün içi kontrol noktası
  (10:00, 15:00) × tutuş penceresi (gün, son saat, gece, iki gün). Koşulsuz boşluk sınaması bu kesişimi ölçmedi.
- §3-2 öngörüsü: coşku sonrası aşağı boşluk **alınır** (A1 +); korku sonrası yukarı boşluk **sürer** (B1 +).

## Tanımlar (broker saatinden ET, `kazanan_turev_20261111/ortak.py` Mkt)
- C(d) = 16:00 barının açılışı; O(d) = 09:30 barının açılışı; P_t(d) = t'de başlayan barın açılışı (= önceki barın kapanışı).
- Gün tepesi/dibi (RTH) = 09:30…15:30 barları. 15:00 durumu (QS-01 ile aynı) = 09:30…14:30 barları, fiyat P_900.
- r(d) = C(d)/C(d−1) − 1; aralık konumu k(d) = (C − dip)/(tepe − dip).
- **E (coşku günü):** r(d−1) ≥ +%1,5 ∧ k(d−1) ≥ 0,75. **F (korku günü):** r(d−1) ≤ −%1,5 ∧ k(d−1) ≤ 0,25.
- **G− aşağı boşluk:** O/C(d−1) − 1 ≤ −%0,3. **G+ yukarı boşluk:** ≥ +%0,3. QS-01 eşiği ±%0,6 C ailesinde.
- SMA50 = son 50 C(d−1) ortalaması (dün dahil). Güçlü 15:00: P_900 > O ∧ k15 > 0,77. Zayıf 15:00: P_900 < O ∧ k15 < 0,23.
- Maliyet: Mkt.cost (RTH max(spread, medyan) × 1,5); gece 1,8 bp/devir (Cuma ×3). Uzun = (çıkış − giriş − maliyet)/giriş;
  kısa = (giriş − çıkış − maliyet)/giriş. Stop yok (zaman çıkışı; §3-5 "braket ≠ zaman"); en kötü işlem raporlanır.

## Karar hücreleri (18, yön önceden)
| ID | Koşul | İşlem | Mekanizma / öngörü |
|---|---|---|---|
| A1 | E ∧ G− | uzun 09:30→16:00 | coşku dönmez → boşluk alınır (+) |
| A3 | E ∧ G− ∧ P_600 < O | kısa 10:00→16:00 | boşluk-devam teyidi, kırılma (+) |
| A4 | E ∧ G− ∧ P_600 > O | uzun 10:00→16:00 | dip alındı teyidi (+) |
| A5 | E ∧ G− ∧ zayıf 15:00 | kısa 15:00→16:00 | gün içi momentum, satış kapanışa sürer (+) |
| A6 | E ∧ G− ∧ P_900 > C(d−1) | uzun 15:00→16:00 | boşluk kapandı, QS-01 benzeri güç (+) |
| A7 | E ∧ G− ∧ C(d) < O(d) | uzun 16:00→ertesi 09:30 | kırmızı günün gecesi, gece primi + korku dönüşü (+) |
| A8 | E ∧ G− ∧ C(d) < O(d) | uzun 16:00→ertesi 16:00 | iki günlük dönüş (+) |
| B1 | F ∧ G+ | uzun 09:30→16:00 | korku döner, rahatlama boşluğu sürer (+) |
| B2 | F ∧ G+ ∧ güçlü 15:00 | uzun 15:00→16:00 | QS-01'in korku-sonrası tetikli hâli (+) |
| B3 | E ∧ G+ (≥ +%0,6) | uzun 09:30→16:00 | coşku dönmez, devam (+) |
| B4 | E ∧ G+ (≥ +%0,6) ∧ zayıf 15:00 | kısa 15:00→16:00 | tükenme gün içi sürer (+) |
| C1 | C(d−1) > SMA50 ∧ G+ (≥ %0,6) ∧ güçlü 15:00 | uzun 15:00→16:00 | QS-01 boğa rejiminde (+, zayıf) |
| C2 | C(d−1) > SMA50 ∧ G− (≤ −%0,6) ∧ zayıf 15:00 | kısa 15:00→16:00 | QS-01 aynası (+) |
| C3 | C(d−1) < SMA50 ∧ G− (≤ −%0,6) ∧ güçlü 15:00 | uzun 15:00→16:00 | ayıda başarısız aşağı boşluk, açık kapama (+) |
| C4 | C(d−1) < SMA50 ∧ G+ (≥ %0,6) ∧ P_900 < O | kısa 15:00→16:00 | ayı rallisi söndü (+) |
| C5 | QS-01 sinyali (4 koşul) | uzun 16:00→ertesi 09:30 | QS-01 gücü geceye taşar mı (+) |
| D5 | r(d−1)>0 ∧ r(d−2)>0 ∧ C(d−1)/C(d−3)−1 ≥ +%3 ∧ G− | uzun 09:30→16:00 | çok günlük coşku kırılması alınır (+) |
| D6 | C(d−1) = son 250 C'nin en yükseği ∧ G− | uzun 09:30→16:00 | zirvede aşağı boşluk alınır (+) |

Her hücrenin **tabanı:** aynı pencere, aynı yön, tüm günler (tutuş gecesi olanlarda aynı gece yapısı).

## Veri
- **KEŞİF/birincil:** broker NAS100 M30 2018-05→2026-11.
- **Kör:** US500, US30, US2000 M30 (aynı kurallar, her biri kendi verisiyle).
- **Bağımsız dönem (günlük hesaplanabilen hücreler: A1, A7, A8, B1, B3, D5, D6):** QQQ günlük 1999-03→2018-04
  (temettü düzeltmeli; açılış×(Adj/Close)); maliyet 2 bp gidiş-dönüş, gece 0 ek (ETF). Gün tepesi/dibi = günlük H/L.
- **Birebir (hayatta kalanlara):** Dukascopy NDX 1m 2021-11→2026-11, dakika girişleri.

## Geçme ölçütleri (hücre başına)
1. NAS100 net ort > 0; gün-blok bootstrap tek yönlü p = 1 − P(ort>0); 18 hücrede **Holm ≤ 0,10**.
2. Kronolojik iki yarı ≥ 0.
3. Taban farkı (hücre − taban) > 0.
4. Kör: üç endeksin havuz ort > 0 ve ≥ 2/3 artı.
5. Bağımsız dönem (varsa): QQQ 1999-2018 net ort > 0, P ≥ %90.
Sınıf: 1–5 → **B** (kart adayı); 2–5 geçer, Holm düşer ama ham P ≥ %95 → **C+**; ham P ≥ %90 ve 4 veya 5'ten biri → **C**; diğer → **X**.
n < 20 olan hücre karar dışı (betimsel). Betimsel (karar dışı): A1 boşluk dozu (−0,3/−0,6/−1,0), VIX ≥ 18,4 katmanı, Pazartesi alt kümesi.

## Sızıntı denetimi
Koşullar yalnız giriş anından önce kapanmış barlar ve önceki günlerle. A7/A8 koşulu C(d) < O(d) 16:00'da bilinir, giriş 16:00 barının
açılışı (aynı fiyat; ortak.py "16:00 girişi" ile aynı kabul — KT-01 A2). E/F d−1'in RTH kapanışıyla.

---
## EK-1 (Tur 2) — sonuçtan sonra türeyen hipotezler, yeni veride ön kayıt (2026-11-11)
Tur 1: 18 hücrenin 18'i X. Görülen iz (sonradan, bu yüzden yalnız bağımsız veride karar): A1 uzun NAS100 −12,3 bp,
QQQ 1999-2018 −22,6 bp (n 129, P(>0) 0,10) → **coşku kırıldığında (E ∧ G−) satış gün içinde sürüyor**. Bu §3-2'nin
("coşku dönmez") devamı değil, kırılma hâli: coşkunun ertesi günü aşağı açılış = alıcının tükendiği gün.

**Hipotezler (yön önceden):**
- **H2a** E ∧ G− → KISA 09:30→16:00 (A1'in tersi).
- **H2c** F ∧ G− (korku günü ertesi daha da aşağı açılış, kapitülasyon) → UZUN 09:30→16:00 (§3-2 "korku döner").
- **H2f** Haftalık coşku: son 5 günün getirisi ≥ +%3 ∧ bugün Pazartesi ∧ G− → KISA 09:30→16:00.
- Betimsel: H2a doz (E eşiği %1/%1,5/%2/%3 × boşluk −%0,3/−%0,6), H2a ertesi gün (16:00→ertesi 16:00 kısa).

**Bağımsız veri (bu tur için hiç bakılmadı):**
- ABD ETF: SPY, IWM 1999-03→2018-04 (QQQ ile aynı günler → zayıf bağımsızlık; destek olarak).
- **Yabancı endeksler** (`geri_cekilme_20261106/data`, Yahoo günlük): AEX, AXJO, BSESN, BVSP, FCHI, GSPTSE, IBEX, JKSE,
  KS11, MXX, SSMI, TWII + DJI, RUT, IXIC (ABD, 2018 öncesi). Her biri kendi E/F/G tanımıyla. Geçerlilik: Yahoo açılışı
  önceki kapanışa eşitse veya H = L ise gün atılır; geçerli gün oranı < %90 olan yıllar dışarıda. Maliyet 3 bp (yabancı),
  2 bp (ETF). Tüm piyasalarda dönem ≤ 2018-04 (broker KEŞİF dönemiyle çakışmaz).
- NAS100 broker 2018-26 + kör US500/US30/US2000 yalnız rapor (H2a için zaten görüldü).

**Ölçüt (hipotez başına):**
1. Yabancı + ABD-öncesi havuz (piyasa eşit ağırlıklı ortalama) > 0 ve piyasaların ≥ %60'ı artı; işaret testi p ≤ 0,10.
2. SPY ve IWM ikisi de > 0.
Sınıf: 1 ∧ 2 → **B−** (sonradan doğdu; canlı öncesi broker kartı ve gölge şart) · yalnız 1 → **C** · diğer → **X**.

---
## EK-2 (Tur 3) — büyük boşlukta coşku kırılması (2026-11-11, sonuç görülmeden)
Tur 2 sonucu: H2a X, H2c X, H2f B− ölçütünü geçti ama kontrol hücresi (coşkusuz Pazartesi ∧ G− kısa, havuz +31,0, 11/11)
artının tamamen Pazartesi boşluğundan geldiğini gösterdi ve broker 2018-26'da dört endekste de eksi → **H2f X** (karıştırıcı).
NAS100 doz izi (sonradan): E ∧ boşluk ≤ −%1 uzun −74 bp (n 23); A3 kör 3/3 artı ama en iyi 5 hariç her yerde eksi.
- **H3** E ∧ boşluk ≤ −%1,0 → KISA 09:30→16:00. Kontrol: E'siz boşluk ≤ −%1,0 kısa (aynı veri).
- Veri/ölçüt EK-1 ile aynı (yabancı 12 + ABD ön-2018, SPY/IWM; hipotez havuzu ≥ %60 artı, işaret p ≤ 0,10, SPY ∧ IWM > 0)
  **ve ek:** H3 − kontrol farkının havuzu > 0 (coşku şartı bilgi taşımalı). Üçü → B−; havuz geçer, fark düşer → X (karıştırıcı).
Bu tur ailenin son turu; deneme sayacı: Tur 1 18 + Tur 2 3 + Tur 3 1 = 22 karar hücresi.
