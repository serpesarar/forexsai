# CAPREV — SL / TP ayrıştırma, stop genişliği, kurtarma, gün içi TP — RAPOR (2026-11-20)

- Ön kayıt `PROTOCOL.md` (commit 8b58f4da, sonuçlardan önce; EK-1 ve EK-2 sonuçlardan sonra, hükmü değiştirmez).
  Kod `src/cr_motor.py` (canlı kuralın besleme bağımsız simülatörü), `src/cr_gunluk.py` (günlük vekil), `src/cr_analiz.py`,
  `src/ek1.py`. Sonuçlar `results/analiz.json`, `results/ek1.json`, `results/ek2.json`.
- Taban (canlı CAPREV, stop 1×dvol, aynı gün 16:00 çıkışı, sabit lot, net bp): Duka NDX 1m 101 işlem **+47,9 bp**, isabet %57,4,
  SL payı %24, Sharpe 0,71 (1m sınaması NX-01 103 işlemle örtüşüyor; fark iki veri boşluğu günü). MT5 NAS100 +46,3, DAX Duka +37,6,
  EET30 +41,8, NQ +36,6.
- Ana ölçü sabit lotta işlem başına net bp ve kitap Sharpe'ı; R stop genişliğiyle değiştiği için kullanılmadı.

## Kısa cevap
| Duka NDX 2018–26 | İsabet | İşlem başı net | Sharpe | En kötü işlem | Maks. düşüş |
|---|---|---|---|---|---|
| **Taban (canlı)** | %57,4 | +47,9 | 0,71 | −334 | −812 |
| Stop 1,5×dvol | %59,4 | +54,4 | 0,79 | | |
| Stopsuz (acil %7), aynı gün | %61,4 | +58,4 | 0,84 | −557 | −1.379 |
| TP 0,5×dvol | **%72,3** | +21,3 | 0,61 | | |
| TP 1,0×dvol (+1R) | %61,4 | +29,9 | 0,63 | | |
| **Stopsuz, ertesi gün 16:00** | %60,4 | **+99,5** | **1,13** | **−721** | **−1.634** |
| Stopsuz XP (kârdaysa 16:00, değilse ilk yükselen kapanış) | **%78,2** | +101,8 | 1,35 | | |

- **TP koymak X:** isabeti %72'ye çıkarıyor, beklentiyi yarıya indiriyor (KSG ve KORKU'yla aynı ders).
- **Stop genişliği:** stop genişledikçe beklenti hafifçe artıyor (+5…+16 bp), kuyruk ağırlaşıyor. Ön kayıtta seçilen 1,5×dvol **C**.
- **Asıl kâr gecede:** CAPREV'in kenarı 16:00'da bitmiyor. Stopsuz tutup ertesi gün 16:00'da çıkmak işlem başı +46…+55 bp ekliyor, ama
  maks. düşüş iki katına çıkıyor ve bu gece çoğu zaman canlıdaki KORKU/KSG/C3b'nin aynı gecesi → **C**.

## S — stop genişliği (D0 16:00 çıkışı)
| Hücre | Duka KEŞİF | Duka TEST | MT5 NAS100 | DAX | U 1990–2015 | Kör 3 | Hüküm |
|---|---|---|---|---|---|---|---|
| **S 1,5** (dondurulan) | +14,7 | +1,6 | +2,3 | +2,6 | +11,1 | −0,6 / −4,2 / +1,8 | **C** (havuz P 0,995, kör 1/3) |
| S 0,75 (dondurulan) | +9,9 | −7,2 | −3,4 | −6,3 | −1,1 | | **X** |
| S yok (seçilmedi) | | Duka +10,5 | +7,8 | +5,2 | +15,9 | +6,1 / −4,6 / +5,1 | betimleyici |
- Dar stop (0,5) her beslemede −12 bp. Stopsuzda en kötü işlem −334 → −557 bp, maks. düşüş −812 → −1.379. DAX'ta Sharpe düşer.

## H — tutuş / kurtarma
| Hücre | Duka KEŞİF | Duka TEST | MT5 NAS100 | DAX | U 1990–2015 | Kör 3 | Hüküm |
|---|---|---|---|---|---|---|---|
| **D1 16:00 stopsuz** | +61,4 | +45,7 | +54,8 | +38,9 | +36,0 | +12,6 / −8,9 / −0,3 | **C** (havuz P 1,00; kör 1/3) |
| **XP stopsuz** | +49,7 | +56,5 | +59,7 | **−19,2** | +33,7 | +22,8 / −2,9 / −5,7 | **C** (DAX eksi, kör 1/3) |
| D1 16:00 stoplu (= canlı gölgenin `R_d1`'i) | | +13,1 | +21,0 | +28,8 | +14,1 | | betimleyici |
| R0 stopsuz (16:00'da zarardaysa ertesi 16:00'a tut) | | +43,6 | +49,9 | +11,6 | +31,8 | | betimleyici |
- Sharpe: D1 16:00 stopsuz Duka 0,71 → 1,13, MT5 0,69 → 1,18, DAX 0,66 → 0,79, U −0,16 → +0,29. Diğer NDX beslemeleri EET30 +50,
  NQ +69, MT5 uzun 1h +56.

## T — gün içi TP (stop 1,0): **X**
TP 1,0 TEST −31,3 / MT5 −10,0 / U −13,9 (havuz P 0,001); TP 2,0 TEST −16,9 / MT5 −11,0. TP 0,5 isabet %72, beklenti +21 bp.
CP'nin "+1R hedef" bulgusu yeni beslemelerde de toplamı düşürüyor.

## E — giriş anında SL'yi TP'den ayırmak: **C** (pratikte X)
- SL ve TP grupları 12 özelliğin hiçbirinde ayrışmıyor: Duka, DAX ve U'da bütün permütasyon p'leri > 0,1. 44 sınamada tek p < 0,05
  (U 2016+ dvol, p 0,036; şans düzeyi).
- KEŞİF'te seçilen filtre "VIX 23–27,8 arasını atla" (orta tertil, mekanizması yok): TEST +19, MT5 TEST +21, DAX −2,3, U +9,2,
  havuz P 0,80 → C. Önerilmez.

## SL olan işlemlerin anatomisi (Duka NDX, 24 SL)
- Stop ortalaması −172,5 bp. Stop olmasa aynı gün 16:00'da −128,3 bp, ertesi gün 16:00'da −39,6 bp.
- SL'lerin %67'sinde 16:00'a kadar beklemek stoptan daha az kaybettirirdi. Ama yalnız %17'si o gün artıya dönerdi.
  Stop çoğunlukla "kaybeden günü erken kesiyor", kazanana dönen günü değil.
- DAX'ta aynı tablo (14 SL: −144 → 16:00'da −108 → ertesi gün −35).
- SL / TP / stopsuz eksi kapanış dağılımı: Duka 24 / 58 / 19, DAX 14 / 36 / 9.

## EK-1 — mekanizma ve canlı kitapla çakışma
- **Ayrıştırma (D1 16:00 stopsuz − taban):** D0 içinde stopu kaldırmak +10,5 (Duka) / +7,8 (MT5) / +5,2 (DAX) / +15,9 (U);
  **D0 16:00 → D1 16:00 gecesi +41,1 / +47,0 / +33,7 / +20,1.** Kazancın büyük kısmı gece.
- **E116 karşı kolu (16:00 → ertesi 16:00):** CAPREV günü Duka +56,0 (n 101), MT5 +62,3, DAX +32,3; stres ∧ VIX ≥ 18,4 olup tetik
  olmayan gün **−21,7 / −27,1 / −16,8**; stressiz gün +4,0. Gece primi genel stres sürüklenmesi değil, CAPREV'e özgü (dibi kıran stres günü).
- **Canlı kurallarla örtüşme (Duka):** 101 CAPREV gününün 56'sında aynı akşam KORKU T30, KSG ya da C3b de AL veriyor (KORKU 22,
  KSG 47, C3b 19). Gece parçası örtüşen günlerde +55,8, örtüşmeyenlerde +22,9 bp. Uzatma, kazancın çoğunu zaten canlıda alınan geceden
  ikinci kez alır (aynı yön, lot üst üste).
- **Kuyruk:** D1 16:00 stopsuz en kötü işlemler −721 / −702 / −422 bp (2020-03-12, 2020-02-27, 2020-02-26; hepsi Covid çöküşü, −700'ler acil %7 stop). Maks. düşüş Duka −812 → −1.634, MT5 −1.244 → −1.670,
  DAX −644 → −1.585. En iyi 5 hariç fark NDX'te +28, DAX'ta **−1,8** (DAX kazancı kuyruktan). Yıllar Duka 7/9 artı (2021 −27, 2025 −89).

## EK-2 — kör endeksler uzun geçmişte (günlük vekil 1990–2015; açılışı olmayan yıllar atıldı)
| Endeks (dönem) | Taban | D1 16:00 stopsuz farkı | XP stopsuz farkı | Yıl artı (D1) |
|---|---|---|---|---|
| NDX (2000–15) | −6,4 | +29,6 | +34,4 | 11/15 |
| S&P 500 (2007–15) | +0,4 | −7,4 | −0,8 | 6/9 |
| Dow (1994–2015) | −11,6 | +11,0 | +37,3 | 12/19 |
| Russell 2000 (2007–15) | −21,9 | +26,2 | −0,9 | 7/9 |
Uzun geçmişte kör endekslerin 2'si artı. Hüküm değişmez (ön kayıt ölçütü MT5 kör beslemelerdi).

## Ayrıca: tabanın kendisi uzun geçmişte zayıf
Günlük vekilde canlı CAPREV (aynı gün çıkış) 1990–2015'te **−9,2 bp** (500 işlem, Sharpe −0,16), 2000–15'te −6,4. 2016+'da aynı vekil
+30,0 bp. 1m sınamasında da 2018–21 zayıftı (NX-01: +0,065R, P 0,64). CAPREV'in aynı gün hâli bugünkü dönemin kenarı. Ertesi gün
stopsuz hâli uzun geçmişte daha dayanıklı: 1990–2015 +26,7 bp, Sharpe +0,29; tabana farkı 23 yılın 19'unda artı. Vekil saatlik tetiği değil
dokunuşu kullanıyor; KT-01 D'de dokunuş girişi 2016–26'da tabanla aynı çıkmıştı.

## Sonuç
- **Canlıya bağlanacak B yok.** TP X, dar stop X, geniş stop C, ertesi gün stopsuz C, XP stopsuz C, giriş filtresi C (pratikte X).
- SL'yi girişte tanımak mümkün değil (KA-01 ile aynı). SL'yi azaltmanın tek yolu stopu genişletmek ya da kaldırmak. O da kuyruğu
  büyütüyor ve beklentiye az katkı veriyor.
- Gerçek bulgu: CAPREV'in kârının yarısı **16:00'dan sonraki gecede**. Bu kâr CAPREV'e özgü, ama canlıda KORKU/KSG/C3b ile aynı geceye
  düşüyor. Ayrı bir CAPREV uzatması aynı riski ikinci kez almak demek.
- **Öneri: gölge etiketi.** `caprev_shadow`a "D1 16:00 stopsuz" ve "XP stopsuz" sonuçlarını ekle (bugün yalnız stoplu `R_d1` var).
  Örtüşmeyen gecelerde (canlı başka kural yok) n ≥ 30'da ortalama > 0 ise yalnız o geceler için uzatma kararı kullanıcıya.
