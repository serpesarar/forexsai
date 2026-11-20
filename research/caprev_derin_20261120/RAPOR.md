# CAPREV derin — SL/TP kümeleme, SL eleme, yüksek isabetli çıkış — RAPOR (2026-11-20)

- Ön kayıt `PROTOCOL.md` (commit 8c9d8ed9, sonuçlardan önce; EK-1 sonuçlardan sonra, hükmü değiştirmez). Kod `src/cd_veri.py`,
  `src/cd_analiz.py`, `src/cd_ek1.py`; sonuçlar `results/analiz.json`, `results/ek1.json`.
- Yöntem: özellik ve çıkış seçimi **1990–2015 günlük vekil havuzunda** (NDX, S&P 500, Dow, Russell 2000, DAX; 1.264 olay),
  sınama **canlı kuralın 2018–26 işlemlerinde** (Duka NDX 101, Duka DAX 59, MT5 NAS100 101, kör MT5 US500/US30/US2000) ve 2016–26 günlük vekilde.
- Taban (canlı kural, sabit lot, net bp): Duka NDX +47,9 / isabet %57,4; DAX +37,6 / %61,0. KEŞİF havuzunda vekil taban −14 bp, isabet %46
  (aynı gün CAPREV uzun geçmişte kenarsız, CR-01 ile aynı).

## Kısa cevap
| Yol | Duka NDX isabet | Duka NDX net bp | DAX | Hüküm |
|---|---|---|---|---|
| Taban (canlı) | %57 | +48 | +38 | — |
| Girişte SL eleme: en iyi günlük filtre (dünkü aralık üst tertil) | %61 | +82 (31 işlem) | +57 (19) | **C** |
| Girişte SL eleme: lojistik / GBM (24 özellik) | %58 / %59 | −18 / −20 fark | +3 / +18 | **X** (AUC 0,55) |
| Girişte SL eleme: KEŞİF'in "tip skoru" (EK-1) | %56 | −28 fark | +11 | **X (ters)** |
| **Çıkış: kârlı ilk kapanışta çık, en çok 5 gün, felaket stopu 3×dvol** | **%89** | **+106** | **+21 (−16 fark)** | **X** (DAX) |

**Sonuç:** SL'ler girişte elenmiyor. Dört ayrı yöntem keşif verisinde çalışıp 2018–26'da düştü. Yüksek isabet + kâr yalnız **çıkış tarafında**
mümkün ve NDX'te güçlü: isabet %57 → %89, işlem başı +48 → +106 bp, Sharpe 0,71 → 1,34. Bedeli kuyruk (en kötü %5 ortalaması −250 → −475 bp),
DAX'ta çalışmıyor.

## SL ve TP grupları (KEŞİF, 1.264 olay: 582 TP / 359 SL / 323 stopsuz eksi)
p < 0,01 olan farklar iki tip veriyor:
| Özellik | SL ortalaması | TP ortalaması | p | Yorum |
|---|---|---|---|---|
| Diğer ABD endekslerinden dün stresli olan | 1,20 | 1,57 | < 0,001 | TP = geniş tabanlı satış |
| Son 10 günde stres günü | 4,20 | 3,72 | 0,003 | SL = uzayan düşüş |
| 5 günlük düşüş (dvol cinsinden) | −1,06 | −0,86 | < 0,001 | SL = daha uzun çöküş |
| 50 günlük ortalamadan uzaklık | −%6,0 | −%4,5 | 0,001 | SL = daha derin |
| VIX yıllık yüzdeliği | 0,78 | 0,71 | < 0,001 | SL = VIX zaten tepede |
| VIX/VIX3M | 1,05 | 1,02 | 0,003 | SL = ters vade eğrisi |
| VIX dünkü değişim | +%6,5 | +%8,5 | 0,002 | TP = VIX'te ani sıçrama |
- **TP tipi "ani panik":** sakin bir dönemden gelen, tek günlük, geniş tabanlı satış; VIX birden sıçramış.
- **SL tipi "uzayan çöküş":** haftalardır süren düşüş, VIX yüksekte kalmış, eğri ters, satış dar tabanlı.
- **Ama 2018–26'da (160 işlem) bu farkların hiçbiri anlamlı değil**, ve EK-1 tip skoru tersine çalıştı: elenecek "uzayan çöküş" günleri NDX'te
  ortalama **+136 bp** (2020 Mart, 2022 ayı piyasası). 1990–2015'teki SL tipi bugünkü dönemde en iyi işlemler.

## F — günlük bağlam filtresi (24 özellik, 2 biçim, ~110 aday; KEŞİF'te dondurulan 3)
| Filtre | KEŞİF | Duka NDX | DAX | MT5 NAS100 | Kör 3 | Havuz P | Hüküm |
|---|---|---|---|---|---|---|---|
| Yalnız dünkü aralık ≥ 1,9 × dvol (üst tertil) | +44, t 4,1 | +34 (%57 → %61, 31 işlem) | +19 (%61 → %74) | +34 | +61 / +21 / −6,5 | 0,50 | **C** |
| Yalnız vadeye 3 işlem günü | +66 | −8 | −88 | −22 | | | X |
| Yalnız VIX dün ≥ %9 arttı | +33 | +18 | −10 | +28 | | | X |
- Aralık filtresi işlemlerin üçte ikisini atıyor; kitap Sharpe'ı NDX'te düşüyor (sabit lot, daha az işlem). 2016–26 günlük vekilde 5 endeksin 4'ünde eksi.

## M — çok değişkenli (lojistik L2, GBM; KEŞİF'te eğitildi, ayar yok): **X**
KEŞİF içi AUC 0,64 / 0,87 (GBM ezberliyor). TEST AUC: Duka NDX 0,55 / 0,55, DAX 0,56 / 0,55, kör 0,38–0,54. "Kötü üçte biri at" filtresi
NDX'te −18 / −20 bp.

## X — yüksek isabetli çıkış (24 hücre; KEŞİF'te isabeti ≥ +10 puan olanlardan en kârlı 2)
| Hücre | Duka NDX | MT5 NAS100 | DAX | US500 | US30 | US2000 | Günlük 2016–26 (5 endeks) |
|---|---|---|---|---|---|---|---|
| **kâr, 5 gün, stop 3×dvol** isabet | %57 → **%89** | %57 → %89 | %61 → %81 | %63 → %89 | %60 → %85 | %50 → %81 | %80–88 |
| net bp farkı | **+58** | +65 | **−16** | +22 | +21 | +14 | +4…+53, 5/5 artı |
| Sharpe | 0,71 → 1,34 | 0,69 → 1,46 | 0,66 → 0,23 | 0,96 → 1,16 | 0,88 → 1,06 | 0,51 → 0,55 | |
| en kötü %5 ort. | −250 → −475 | −284 → −461 | −258 → −731 | | | −289 → −722 | |
| yükselen, 5 gün, stop 3×dvol farkı | +58 (%78) | +66 | −9 | +24 | +16 | +6 | 5/5 artı |
- Havuz P 1,00, kör 3/3, NDX Sharpe ↑ — ama Duka DAX eksi ve DAX'ta kuyruk 2 katın üstünde → ön kayıt hükmü **X**.
- NDX'te tutuş ızgarası kararlı: kâr kuralı 1 gün %75 / +91, 2 gün %83 / +98, 3 gün %87 / +94, 5 gün %90 / +101 (stopsuz); 3×dvol stop
  kuyruğu −655 → −475'e çekiyor ve beklentiyi artırıyor.

## EK-1
- **DAX neden ayrışıyor:** D0'da zararda kalan işlemlerin 5 gün içinde kâra dönme oranı NDX %77, MT5 NAS100 %74, **DAX %61**. Dönmeyenler
  NDX −473, DAX −517 bp. DAX'ta düşüş daha kalıcı; "kâra kadar tut" DAX'ta zarar biriktiriyor.
- **Birleşim:** aralık filtresi + kâr çıkışı NDX 31 işlem, %90 isabet, +125 bp, ama kitap Sharpe'ı 0,75 (taban 0,71): daha az işlem,
  aynı kitap. Tip skoru + kâr çıkışı NDX %91 / +81, Sharpe 1,19 (tip skoru tek başına X olduğundan bilgi amaçlı).
- **Örtüşme:** kâr çıkışının NDX kazancı canlı KORKU/KSG/C3b geceleriyle örtüşen günlerde +59, örtüşmeyenlerde **+56**. Örtüşmeyen günlerde isabet
  %76 → %96. CR-03'teki ertesi gün uzatmasından farklı olarak bu kazanç başka kuralların gecesine dayanmıyor.

## Sonuç ve öneri
- **SL'yi girişte elemek X.** Uzun geçmişte SL'ler "uzayan çöküş" tipinde toplanıyor, ama bu ayrım 2018–26'ya taşınmıyor; tersine dönüyor.
  KA-01 (KSG), XA-01 (KORKU) ve CR-05 ile aynı sonuç: kaybeden işlem girişte tanınmıyor.
- **Yüksek isabet çıkışla geliyor.** NDX için "kârlı ilk seans kapanışında çık, en çok 5 gün, felaket stopu 3×dvol" isabeti %89'a, işlem başı
  getiriyi iki katına çıkarıyor. Kör ABD endeksleri ve 2016–26 günlük vekilde de artı. Ön kayıt hükmü X, çünkü DAX'ta çalışmıyor ve kuyruk büyüyor.
- **Öneri: NDX bacağı için gölge etiketi.** `caprev_shadow`'a NDX işlemlerinde "kâr çıkışı (5 gün, 3×dvol)" sonucunu kaydet (CR-03 önerisindeki
  ertesi gün stopsuz / XP alanlarıyla birlikte). DAX'ta uygulanmaz. n ≥ 30 NDX gölge işleminde isabet ≥ %80 ve ortalama tabandan yüksekse karar
  kullanıcıya. Not: tutuş en çok 5 gün sürer, CAPREV pozisyonu bu sırada açık kalır (canlı kodda "tek CAPREV pozisyonu" kuralıyla çakışır;
  gölgede sorun yok).
