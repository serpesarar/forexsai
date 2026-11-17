# IG-ICT — "1 dakikada kârsızdan kârlıya": 9 tavsiye, sırayla (2026-11-16)

Ön kayıt `PROTOCOL.md`. Kod `src/smt.py`, `src/pm_wait.py`. Çıktılar `results/smt_ozet.json`, `smt_islemler.csv`,
`pm_ozet.json`, `pm_gunler.csv`. Defter §2.60 (IG-01, IG-02).

| # | Tavsiye | Ölçülebilir hâli | Kanıt | Hüküm |
|---|---|---|---|---|
| 1 | Her SMT gerçek değildir; gerçek olduğunu yalnız sonraki yapı teyidi gösterir | NAS100–US500 PDH/PDL + gece uçlarında uyumsuzluk → 12 bar içinde fraktal kırılımı → ters işlem | **IG-01 (yeni)** | Teyit kaybı sıfıra çeker, kâr üretmez → **X** (SMT − kontrol farkı C) |
| 2 | Günlük bias önemsiz; önemli olan son likiditeye verilen tepki | likidite süpürmesine dönüş tepkisi | SM-01…05, MZ-01…04, YL-02; günlük yapı HL-02b; bias karnesi | İkisi de yön taşımıyor; süpürme ortalamada **devam** ediyor → **X** |
| 3 | Stop olduktan sonra fiyat hedefe gidiyorsa stopu korunan tepe/dibe koy | yapısal (korunan uç) stop vs dar stop | SM-04 iz süren yapısal stop, HL-01 (stop dip − 0,1 ATR), YL-01 D/(U+D), C3b'de stop kenarı siler | Kenarsız girişte stop yerini değiştirmek yalnız isabet ile R'yi takas eder. "Stop sonrası hedefe gitti" geriye bakma yanlılığı → **X (kenar), ilke olarak zararsız** |
| 4 | 9:30 manipülasyonunu okuyamıyorsan 10:00 devamında yarım riskle işlem yap | 10:00 dönüşü/devamı, açılış aralığı kırılımı | GF-02 H5 (X), FC-01…05 (X), **ORB × VIX (NX-02, CANLI, TP 3R)** | Saatin kendisi kenar değil. Devam yalnız korku gününde (VIX ≥ 18,4) çalışıyor. Yarım risk beklentinin işaretini değiştirmez → **C** (VIX koşuluyla zaten canlıda) |
| 5 | AM'den önce 400 puandan fazla düştüyse PM seansını bekle | düşüş günü PM-ORB − AM-ORB, testere oranı | **IG-02 (yeni)** | Ters: düşüş gününde AM uzun +28…+51 bp, PM −24…−45 bp. Beklemek toparlanmayı kaçırtıyor → **X** |
| 6 | Zaman fraktaldır: 15–30 sn girişte 1m/5m FVG'ler, 1m/5m girişte 1H/4H FVG'ler likiditedir | HTF seviyesi → LTF giriş çiftleri; FVG mıknatıs/duvar | MZ-01…04 (1H→5M, 4H→15M X), YL-01/02 (13 seviye ailesi hayaletten ayrılmıyor), FC-03 / SM-01 FVG limit X | Çift sırası doğru (1H→5M en az kötü), mutlak kazanç yok → **X** |
| 7 | Yeni başlayan iki aşamalı, tecrübeli tek aşamalı prop hesabı seçsin | piyasa kenarı değil, kural geometrisi | kumarbazın iflası aritmetiği (aşağıda) | Geometri açısından kısmen doğru. Sonucu kenar belirler, hesap tipi değil → **bilgi** |
| 8 | Stopu yalnız fikrin yanlışlandığı yere koy | yapısal stop | SM-01, HL-01, MZ-01 hep yapısal stoplu | Tutarlılık ilkesi. Kenar üretmiyor; kanıtlı kurallarımızda (C3b, KSG) en iyi çıkış zaman, stop değil → **ilke, kenar değil** |
| 9 | FVG'ye stop koyuyorsan FVG'den girmiş ol; tepeden girdiysen stop tepenin ötesinde | giriş ↔ stop tutarlılığı | SM-01 kırılım FVG'sine limit + FVG ötesi stop (X), FC-03 FVG limit (X) | Mantıklı defter tutma kuralı, kenar değil → **ilke** |

## IG-01 — SMT + yapı teyidi (yeni sınama)
Veri: Pepperstone MT5 M5, NAS100 + US500, 2025-06-18 → 2026-11-13 (360 gün). Olaylar: 547 SMT, 322 kontrol (iki endeks de seviyeyi aynı
5m barında aşmış). Seviye-yön başına ilk süpürmelerin %63'ünde öbür endeks geride kalıyor. Yani SMT çok sık görülüyor; "her SMT
gerçek değildir" sözü bu anlamda doğru.

| hücre (2R, gerçek spread) | n (gün) | ort R | P(EV>0) | 1. yarı | 2. yarı |
|---|---|---|---|---|---|
| SMT · teyitsiz (sonraki bar) | 461 (273) | **−0,222** | 0,00 | −0,312 | −0,133 |
| SMT · yapı teyitli (videonun kuralı) | 151 (124) | +0,037 | 0,65 | +0,228 | **−0,151** |
| kontrol · yapı teyitli | 152 (125) | −0,116 | 0,11 | −0,023 | −0,207 |
| kontrol · teyitsiz | 291 (214) | −0,293 | 0,00 | −0,148 | −0,438 |

- Ölçüt 1 (ort > 0, P ≥ %90): ✗ (P 0,65). Ölçüt 2 (iki yarı ≥ 0): ✗ (2. yarı −0,15). Ölçüt 5 (spread × 1,5): +0,031.
  1R ve 3R hedefleri de ≈ 0 (+0,004 / +0,009).
- Ölçüt 3, SMT − kontrol (ikisi de teyitli): **+0,153R, P 0,887** (eşik %90'ın hemen altında).
- Ölçüt 4, teyitli − teyitsiz: +0,259R, P 0,988. Videonun "teyit şart" iddiası göreli olarak doğru. Ama bunu sağlayan, teyidin
  kâr üretmesi değil; teyitsiz girişin süpürmenin devamına yakalanması (MZ-04 ile aynı mekanizma).
- Alt kırılım (sonradan, hüküm dışı): tepe tarafı (PDH +0,18, ONH +0,13) artı, dip tarafı (PDL −0,18, ONL −0,21) eksi.
  Tek bir boğa dönemiyle tutarlı, ayrı kenar sayılmaz.
- **Hüküm X** (işlem kuralı olarak). SMT'nin süpürmeye göre göreli bilgisi **C**: tek broker, 17 ay, P 0,89. Yeniden açmak için
  Dukascopy USA500 + NDX 1m 2018 → ile bağımsız dönem gerekir.

## IG-02 — "400 puan düştüyse PM'i bekle" (yeni sınama)
Veri: Dukascopy NDX 1m 2018-01-03 → 2026-11-12 (2.080 tam gün). Düşüş = 09:30 açılışı − önceki 16:00 kapanışı.

| | gün | AM getiri | PM getiri | AM testere | PM testere | AM-ORB R | PM-ORB R | PM − AM | etkileşim (P) |
|---|---|---|---|---|---|---|---|---|---|
| P400 (≤ −400 puan) | 24 | **+50,7 bp** (P 0,94) | −45,2 | 0,59 | 0,58 | +0,22 | +0,36 | +0,18 (P 0,67) | +0,26 (0,74) |
| R16 (≤ −%1,6) | 75 | **+27,8 bp** (P 0,97) | −23,9 (P 0,05) | 0,48 | 0,49 | +0,16 | −0,00 | −0,16 (P 0,21) | −0,08 (0,34) |
| kontrol | ~2.000 | +2,6 | +1,4 | 0,38 | 0,40 | +0,02 | −0,06 | −0,08 | — |

- R16 dönem yarıları ters işaretli: 2018-21 etkileşim +0,18, 2022-26 −0,28. P400'ün 20 günü 2022 sonrasında (mutlak puan eşiği,
  NDX ucuzken bu düşüş nadirdi).
- Testere: düşüş günlerinde iki seans da kontrol günlerinden fazla iki yöne vuruyor (0,48–0,59 vs 0,38–0,40). AM daha kaotik değil,
  günün tamamı daha oynak (eşik geçmiş aralıkla ölçekli; bu oynaklık etkisidir).
- Ölçütlerin hiçbiri tutmadı (PM − AM P ≥ %90 değil, etkileşim tutarsız, AM testeresi PM'den kötü değil) → **X**.
- **Bedel:** "bekle" kuralı günün en iyi kısmını atlatıyor. Büyük düşüşle açılan günde sabah ortalamada toparlıyor, öğleden sonra
  geri veriyor. Bu bulgu NX-11 S1 (korku açılış boşluğu → 09:30 AL, C) ve CAPREV ailesiyle aynı yönde ("korku döner").

## 7 — Prop hesabı aritmetiği (piyasa verisi gerekmez)
Kenarsız (sürüklenmesiz) bir trader için, küçük işlemlerle hedef T'ye düşüş limiti D'den önce varma olasılığı: sabit limitte D/(T+D),
izleyen (trailing) limitte ≈ e^(−T/D). Tipik kurallarla:

| hesap | kural | geçme olasılığı (kenar 0) |
|---|---|---|
| iki aşamalı | %10 hedef + %5 hedef, %10 sabit limit | 0,50 × 0,67 = **0,33** |
| tek aşamalı, sabit | %10 hedef, %6 sabit limit | **0,38** |
| tek aşamalı, izleyen | %10 hedef, %6 izleyen limit | **0,19** |

Kurallar firmaya göre çok değişir; tablo yalnız mekanizmayı gösterir. Limitin hedefe oranı ve limitin sabit mi izleyen mi olduğu belirleyici.
Yaygın tek aşamalı hesaplardaki izleyen limit yeni başlayanı daha çok eler; videonun önerisi bu açıdan tutarlı. Ama kenar negatifse
iki hesap tipi de kaybettirir, pozitifse aşama sayısı yalnız süreyi ve ücreti etkiler. Hesap tipi kârlılık yaratmaz.

## Genel sonuç
Videodaki 9 maddenin hiçbiri bu projenin verisinde kendi başına beklenti üretmiyor. Üç tanesi (8, 9 ve kısmen 3) tutarlılık ve risk
ilkesi olarak zararsız. 5. madde ölçülebilir biçimde ters: büyük düşüş sabahı, kanıtlı tek gün-içi kenar ailemizin (korku dönüşü)
çalıştığı andır. Videoya en yakın kanıtlı kenar 4. maddenin VIX koşullu hâli: ORB × VIX, canlıda TP 3R ile çalışıyor.

---

# EK-1 — Derin tur: seans dilimi × haftanın günü × eşik (2026-11-16)

Kullanıcı: "daha detaylı incele, farklı seans dilimlerinde ve gün bazında test et, bir yerde bir şey olmalı."
Ön kayıt `PROTOCOL.md` EK-1 / EK-1b. Kod `src/derin_lib.py`, `derin_f45.py`, `derin_f2.py`, `derin_f3.py`, `derin_f6.py`,
`smt_grid.py`, `smt_devam.py`. Dönem: KEŞİF 2018–2022 · TEST 2023–2026-11 (Duka NDX 1m, 2.228 tam gün); SMT'de KEŞİF 2021-01 →
2023-06 · TEST 2023-07 → 2025-06 (broker M30) · BAĞIMSIZ 2025-06 → 2026-11 (broker M5).
Hücre geçer = KEŞİF |t| ≥ 2 ∧ TEST aynı işaret t ≥ 1,65 ∧ TEST n ≥ 30. Aile geçer = geçen sayısı plasebonun %95'inin üstünde.

## Özet tablo — toplam ~12.000 hücre

| aile (madde) | hücre / uygun | geçen | plasebo ort / %95 | KEŞİF ilk-20 → TEST aynı işaret | hüküm |
|---|---|---|---|---|---|
| F5 düşüş/yükseliş × 9 dilim × gün (5) | 2.376 / 342 | **0** | 0,9 / 4 | %35 (işaretli −3,6 bp) | X |
| F4 açılış / 10:00 devamı / Judas × boşluk × VIX × gün (4) | 2.376 / 1.233 | 2 | 3,2 / 10 | %30 (−4,6 bp) | X (bir iz C) |
| F2 bias vs likidite tepkisi (2) | 648 / 369 | 4 (tek olay kümesi) | 1,1 / 4 | %20 | X |
| F3 stop yeri + yazı-tura plasebosu (3) | 3 başlangıç × 4 stop × 5 gün | — | — | — | X (geometri) |
| F6 FVG mıknatısı 5m/1H/4H × yaş × dilim (6) | 36 | 0 (hayalet sonrası) | — | — | X |
| F1 SMT seans × seviye × teyit × hedef × gün (1) | 3.308 / 1.892 | **artı yönde 0** (336'sı tutarlı eksi) | artı 1,0 / 5 | eksi yönde %100 | X |

Hiçbir aile plaseboyu geçmedi. Aşağıda her aile ayrıntılı.

## F5 — "400 puan düştüyse PM'i bekle", her dilim ve günde (madde 5)
44 koşul (kapanış→09:30 ve 18:00→09:30; düşüş/yükseliş; 150–600 puan, %0,5–2,5, z 1–2,5) × 9 dilim × 6 gün grubu.
**Örüntü dönemden döneme ters dönüyor.** Kontrol günlerine göre fark (bp):

| koşul | dönem | 09:30-10 | 10-11 | 11-12 | 12-13:30 | 13:30-15 | 15-16 | AM | PM |
|---|---|---|---|---|---|---|---|---|---|
| kapanıştan ≥ %1 düşüş (n 119 / 72) | KEŞİF 2018-22 | +2 | −7 | +4 | +7 | +3 | +15 | −1 | **+18** |
| | TEST 2023-26 | +4 | +3 | +4 | −3 | −15 | +1 | **+13** | **−14** |
| kapanıştan ≥ %1,6 düşüş (54 / 28) | KEŞİF | +10 | +4 | +5 | −1 | −3 | +7 | +19 | +4 |
| | TEST | +20 | +7 | +7 | −11 | −14 | +3 | +33 | −11 |

"PM'i bekle" 2018–22'de doğruydu (PM +18 bp), 2023–26'da yanlış (PM −14, AM +13). İlk turdaki "AM uzun +, PM −" bulgusu yalnız
son döneme ait. 400 puanlık mutlak eşik KEŞİF'te yalnız 4 gün (NDX ucuzken nadir) → sınanamaz. Gün kırılımında hiçbir hücre iki dönemde
tutmadı. Hüküm X.

## F4 — 9:30 manipülasyonu ve 10:00 devamı (madde 4)
Giriş 09:45/10:00/10:15/10:30, açılış hareketi yönünde; çıkış 11:00/12:00/16:00; Judas (ilk 15 dk bir yön, sonra açılışın öbür tarafı)
var/yok × boşluk × VIX × gün. Koşulsuz devam her saatte ≈ 0 (−1,6…+6,4 bp, |t| ≤ 2,1). Judas koşulu hiçbir yerde tutarlı değil.
Geçen 2 hücre plasebo ortalamasının (3,2) altında.
**Tek iz (C, sonradan):** aşağı boşluk (< −0,5σ) ∧ dünkü VIX < 18,4 → açılış yönünde devam. 12 giriş × çıkış komşusunun 12'si iki dönemde
artı (KEŞİF +0,3…+21 bp, TEST +2,4…+12 bp, n 81/98); en iyi 10:15→12:00 +11,7 (t 2,32) / +10,6 (t 2,50). Yüksek VIX'te karışık.
Ayrı ön kayıt + bağımsız veri olmadan kullanılmaz (backlog).

## F2 — bias mı, son likiditeye tepki mi (madde 2)
29.054 olay (PDH/PDL/ONH/ONL'ye RTH'de ilk dokunuş × tepki 5/15/30 dk × çıkış). Tavsiyenin doğrudan iddiası: aynı girişlerde
tepki-yönü − bias-yönü farkı **KEŞİF −0,9 / −0,9 / +1,8 bp, TEST −0,8 / −0,9 / −1,6 bp, |t| ≤ 0,63** → ikisi eşit derecede bilgisiz.
Sinyal başına ortalama: tepki KEŞİF +2,3 / TEST −0,7 bp; gece yönü (b4) KEŞİF'te 16 hücre |t| ≥ 2 ama TEST'te aynı işaret %28.
Geçen 4 hücrenin dördü aynı 33 günlük TEST kümesi (gece tepesine ilk dokunuş öğle saatinde → gece yönünde gir), plasebo %95'i = 4.

## F3 — "stop olduktan sonra hedefe gitti" (madde 3)
15 dk aralık kırılımı 09:30 / 10:00 / 13:30, hedef fiyatı sabit, dört stop türü; aynı anda **yazı-tura yön** plasebosu.

| | taban stop sonrası hedefe varma ("pişmanlık") |
|---|---|
| gerçek kırılım yönü | %5,0 – %13,2 |
| yazı-tura yönü | %6,4 – %14,2 |

Pişmanlık rastgele yönde de aynı sıklıkta yaşanıyor: bu bir bilgi değil, stop mesafesinin geometrisi. Korunan uç stopu tabanla
neredeyse aynı yerde (medyan 1,0× risk) ve beklentisi tabandan farksız. Geniş stop isabeti yükseltip R'yi düşürüyor, dar stop tersini yapıyor.
Hiçbir stop türü üç başlangıç saatinin hepsinde, iki dönemde birden üstün değil. Gün kırılımında Cuma 09:30 kırılımı +0,18 / +0,14R
(t 2,25 / 1,49) eşiğin altında kalıyor; 15 hücreden biri.

## F6 — üst TF FVG'leri likidite mi (madde 6)
131.733 5m, 11.913 1H, 3.268 4H FVG; 191.069 ızgara noktası. Her noktada en yakın dolmamış üst/alt FVG kenarına yarış. Gözlenen ≈ D/(U+D).
Tek tutarlı fark (1H, gece/ön seans, +2,3 / +1,8 puan "önce üst") aynı mesafelerdeki **hayalet** seviyelerde de çıkıyor:
FVG − hayalet = +0,2 / +0,5 puan. Bu NDX'in gece yükseliş eğilimi, FVG bilgisi değil. 36 hücrenin hiçbirinde FVG − hayalet iki dönemde
aynı işaretli ve |t| ≥ 2 değil. YL-01/02 (13 seviye ailesi) ile aynı: seviye = kumarbazın iflası geometrisi.

## F1 — SMT ızgarası (madde 1)
5 seans (Asya, Londra, NY sabah, öğle, öğleden sonra) × 6 seviye (PD, gece, Asya, Londra, sabah, son 60 dk) × 3 teyit (yok, fraktal,
seviyenin içine geri kapanış) × 4 hedef × 6 gün grubu; 215.256 işlem.
- **Artı yönde tutan hücre 0** (plasebo ort 1,0, en çok 10). 336 tutarlı hücrenin tamamı eksi; çoğu teyitsiz giriş (284) ve
  "içeri kapanış" (51).
- Teyit kaybı azaltıyor: 2R'de teyitsiz SMT −0,22, içeri kapanış −0,10…−0,14, fraktal teyidi −0,01…−0,08R. Ama hiçbir dönemde artıya
  geçmiyor. Bağımsız M5'te fraktal teyidi −0,010R.
- SMT − kontrol (aynı barda iki endeks): 1.576 eşleşik hücrede KEŞİF ve TEST aynı işaret **%51** → yazı-tura. İlk turdaki +0,15R farkı
  (P 0,89) daha uzun veride tekrarlamadı.
- **Ters yön (süpürmenin devamı), sonradan tanı:** "ters = −brüt" yaklaşımı 40 hücreyi üç dönemde artı gösterdi. Ama bu, aynı barda
  stop + hedef belirsizliğinin tersine iyimser sayılmasıydı (E142). Temkinli ayrı simülasyonda devam −0,13…−0,36R (t −6…−32);
  108 hücreden 1'i üç dönemde artı (+0,01R). 30m barda stop bar içinde kaldığında iki yön de bu çözünürlükte ölçülemiyor. 1m'deki karşılığı
  MZ-04: devam +0,03R, dönüş −0,1R. Maliyet sonrası iki yönde de kenar yok.

## Derin tur hükmü
"Bir yerde bir şey olmalı" sorusunun cevabı: ~12.000 hücrede, şansın üretebileceğinden fazla tutarlı kazanan çıkmadı. Ayakta kalan tek iz
madde 4'ün dar bir hâli (aşağı boşluk ∧ düşük VIX'te açılış yönünde devam, 12/12 komşu iki dönemde artı, C). Bu da "korku günü değil,
sakin gün" koşuluna bağlı. Videonun genel kuralı olarak (her gün 10:00 devamı) ≈ 0. Madde 5'in (PM bekle) iki dönemde işaret değiştirmesi
de bir bulgu: tavsiye bir rejimde doğru, öbüründe yanlış. Yani dinamik bir kural değil, geçmiş bir dönemin gözlemi.
