# ForexSAI araştırma arşivinin meta-analizi — 2026-11-09

Ön kayıt: `PROTOCOL.md` (testlerden önce yazıldı). Kod ve sonuçlar bu klasörde (`ma01…ma04`, `results/`).
Canlı sisteme dokunulmadı; commit / push yok.

**Okuma kapsamı (dürüst sınır).** Defterin §0, §1 (E1–E110), §2.1–2.5, §2.9, §2.24–2.34, §3, §4 tam okundu.
§2.6–2.8 ve §2.10–2.23 satır başına kimlik + özet + hüküm olarak kısaltılmış okundu (bağlam sınırı).
Tek tek `research/*/RAPOR.md` dosyaları, 09-30 envanterinin tamamı ve decider LESSONS dosyaları açılmadı;
bu rapordaki her sayı ya defter satırından ya da bu klasördeki sonuç dosyasından gelir.

**Düzeltme (2026-11-10, MA-05 sırasında bulundu).** MA-03 tablosu hizalama adımından geçen 422 NDX işlemini
kullanıyor; 9 işlem dışarıda kalmış. Tüm 431 işlemle NDX neti **+26.995 $**, en kötü 5 gün **−21.999 $** (netin
%81'i, "tamamı" değil). Aile sıralaması ve risk payları değişmiyor. Aşağıdaki §1 ve §2-C sayıları 422 işlemlik
alt kümeye aittir; güncel tablo §7'de.

---

## 1. Yönetici özeti

Arşivde üç yapısal gerçek var. **Bir:** dayanan her bulgu aynı tek durumun üstünde duruyor — hisse endeksinde
korku fiyatlanmışken (düşüş + yüksek VIX) uzun tarafta durmak ve zamanla çıkmak; bu bir tahmin değil, zorunlu
satıcıya likidite sağlamanın primi. **İki:** elenen yüzlerce fikir tek bir bilgi sınıfı — aynı sembolün kendi
geçmiş mumlarından türetilmiş gün-içi yön sinyali; o sınıfta yön yok, yalnız hareketin büyüklüğü öngörülebiliyor.
**Üç:** botun risk bütçesi kanıtla ters orantılı — NDX'te 06-30 → 11-09 arası riskin %88'i kanıt sınıfı C/X olan
ailelerde, en kötü 5 gün (−22.001 $) toplam net kârın (+21.903 $) tamamına eşit. Bu oturumda arşivden türetip
ön-kayıtla sınadığım üç yeni hipotez de geçmedi (MA-01, MA-02, MA-04: X). Yeni yönlü kenar bulamadım; kazanılacak
yer sinyal tarafında değil, boyut ve yoğunlaşma tarafında.

---

## 2. Bulgular

### A. Pozitiflerin ortak yapısı: "korku fiyatlanınca endekste uzun, zamanla çık"

| Bulgu (defter) | Sembol | Durum koşulu | Yön | Çıkış | Sıklık |
|---|---|---|---|---|---|
| TR-C3 / C3b (§2.26) | NDX, kör US500/US30 | RSI2 < 10 | uzun | zaman / ilk yükselen kapanış; **stop zarar veriyor** (+45,7 → +11 bp) | ~15–24 / yıl |
| CAPREV GF-16/22 (§2.5) | NDX + DAX | stres günü ∧ VIX ≥ 18,4 | uzun | 16:00; **braket öldürüyor** (GF-17) | ~10 / yıl |
| ORB × VIX, HB-03 C1 (§2.25) | NDX | VIX ≥ 18,4 | uzun | 2R / seans sonu | ~60 / yıl |
| Teyitli çekiç FR-15 (§2.27) | NAS100, GER40 | alt fitil (mum içi satış reddi) | uzun | TP 5R, 24 sa | sık |
| KS-01b (§2.34) | 5 broker endeksi | stres | uzun | — | C3b'yi +19 → +64 bp |
| GR-01 (§2.9) | NDX, SPX, DAX | dün düşüş | uzun | 1 gün | **toplam getirinin %98'i düşüş sonrası günde** |

Ortak payda altı madde: hisse endeksi · uzun yön · korku / stres durumu · zaman çıkışı veya çok geniş hedef ·
saatler–günler tutma · XAU ve USOIL'de yok (TR-C3b: "GC/CL yok: endeks etkisi"). Aynaları her yerde eksi
(TR-C3 karşıt, FR-08, GF-12, TK-03 KKS, bu oturumda MA-02 ayna). Yani tek hikâye: **satmak zorunda olan biri
varken karşı tarafta durana ödeme yapılıyor; almak zorunda olan kimse olmadığı için coşkunun tersi ödemiyor.**

- **Neden göremedik:** her bulgu ayrı bir "kural" olarak kartlandı. Yan yana konunca beş kural tek durum
  değişkenini (VIX / son düşüş) paylaşıyor. Getiri korelasyonları düşük ölçülmüş (FR-17: 0,02–0,08), ama
  olaylar aynı kriz aylarında kümeleniyor (E110). Çeşitlendirme sakin dönemde var, krizde yok.
- **Bu oturumun eklediği sınır (MA-04):** aynı kural QQQ'da 2010–17'de yalnız +3,8 bp net, 2018–26'da +55,4 bp
  (`results/ma04.json`). Defter de QQQ 2014–18'i "taban altı" yazmış. Kenar çağa bağlı: sakin boğa on yılında
  yok. Bu, ileriye dönük en büyük risk.

İkinci, bağımsız ve zayıf bir faktör daha var: **altın ve BTC'de ≥ H4 ölçeğinde trend** (XS-01 Golden Donchian
bağımsız 2008–21'de +0,39R vs taban +0,15; MK-04; BTC-T03 / MAX10). USOIL'de hiçbir şey dayanmadı.

### B. Negatiflerin ortak yapısı: tek bilgi sınıfı, yüzlerce kılık

Gösterge (GC, PN: 32.741 script, HK), formasyon (MK, PM, ME), seviye ve çizgi (TK, TL, KC: gerçek = hayalet),
SMC / süpürme (SM, MZ, FC), mum gövdesi (M19), teyit türevleri — hepsi **aynı sembolün son OHLC'sinin
fonksiyonu** ve hepsi **gün-içi yön** soruyor. Sonuç tutarlı: yön yok; büyüklük var (DTS-03 %90 aralık A,
HB-03 S6 başlık yoğunluğu → |getiri| ×1,24–1,32, ME-11 oynaklık kümelenmesi).

Üç ortak öldürücü:
1. **Karşı tarafı olmayan örüntü.** Dayananların hepsinde zorunlu bir karşı taraf tarif edilebiliyor. Elenenlerde
   yok; "herkesin gördüğü şekil" kimseyi işlem yapmaya zorlamıyor.
2. **Teyit bilgiyi tüketiyor.** Fakeout dedektörü isabetli (NDX %70+) ama işlem olarak net −0,068R (CK-02);
   fitil bilgisi iki yönde gerçek (+0,1R plaseboya göre) ama mutlak kâr yalnız uzunda (FR-06).
3. **Maliyet + sürüklenme asimetrisi.** Kısa taraf sürüklenmeye karşı; limit emir ters seçilim yiyor (Y-01,
   gerçek piyasa karıştırılmış piyasadan kötü).

**Hiç denenmeyen bilgi sınıfları:** (a) göreli fiyat / çift işlemi — bu oturumda sınandı, X (MA-02);
(b) oynaklığın kendisini işlem aracı olarak kullanmak (VIX vadeli CFD'si); (c) konumlanma verisi (COT servisi
var, sinyal olarak sınanmamış); (d) yavaş rejim göstergesi (yıllık oynaklık çağı) ile kuralları açıp kapamak.

- **Neden göremedik:** her yeni fikir farklı göründü (çizgi ≠ gösterge ≠ SMC). Bilgi kaynağına göre
  sınıflanınca hepsi aynı satır.

### C. Yön dışı kenar: para boyutta ve yoğunlaşmada (MA-03, betimsel)

`results/ma03_aile.csv` — botun NDX işlemleri, 418 karar, 2026-06-30 → 11-09, net +21.903 $, ort. +0,068R:

| Aile | Karar | Risk payı | Net $ | Ort. R | Defterdeki kanıt |
|---|---|---|---|---|---|
| VIXREG SELL | 209 | %40,6 | +1.064 | +0,008 (P 0,55) | CK-01: SHADOW, "206 SELL ort. 0,000R" |
| DAYCOMBO BUY | 43 | %23,7 | +406 | +0,164 (P 0,92) | CK-03 2025 −0,030R; CK-05 2024 geçmedi |
| REENTRY BUY + SELL | 33 | %24,4 | +18.628 | +0,29 / +0,46 | M2: C, dış örneklem plasebosu geçmedi; CK-05 geçmedi |
| MOMSR + CHREV | 49 | %10,5 | +560 | −0,07 … +0,04 | CK-01: −0,014 / −0,016 |

- Toplam kârın %85'i 33 REENTRY kararından; tek gün (09-21) +16.596 $ = netin %76'sı.
- En kötü 5 gün −22.001 $ ≈ tüm net kâr. Lot Eylül'de 1 → 30'a çıkmış (DAYCOMBO), VIXREG SELL 5 → 10.
- A / A− sınıfı kurallar (C3b 2 lot, CAPREV 1, ORB × VIX 0,75, çekiç 0,5) bu dosyada henüz hiç işlem üretmemiş.
- **Neden göremedik:** otopsiler işlem başına R'ye bakıyor; R lotu gizler. Dolar eğrisini sinyaller değil,
  lot kararları çiziyor.

### D. Yanlış çerçevede sorulan sorular

1. "Hangi giriş sinyali?" yerine "**kim işlem yapmak zorunda?**" Dayananların tamamı ikinci sorunun cevabı.
2. "Yön" yerine "büyüklük": aralık A sınıfı, ama botta hiçbir karar aralığı kullanmıyor (DTS-06 bot X).
3. **Kart ölçütü 1 (≥ 150 olay) araştırmayı kenarın olmadığı ölçeğe itiyor.** Seyrek günlük kenarlar yapısal
   RED alıyor (CAPREV 107, XAU swing 86, K6 51, C3b 129 → hepsi "yalnız hacim geçmedi"). Sık gün-içi kurallar
   hacmi kolay geçiyor ama orada kenar yok. Seyrek kurallar için hacim yerine "bağımsız dönem + ≥ 3 kör piyasa"
   zaten fiilen kullanılan ölçüt; karta yazılmalı.
4. "Kural başına kart" yerine "faktör başına risk": dört canlı kural + eski BUY aileleri aynı gün aynı yöne açar.

### E. Çelişkiler ve ne söyledikleri

- **K6/K1:** Yahoo'da 12 kör piyasada geçti, 13 broker CFD'sinde düştü (BG-07). Fark swap. CFD uzun primi
  yılda ~%6,4 vergilendiriyor (FR-18); yalnız koşullu, yoğun primler (C3b günde ~45 bp) bunu taşıyor.
- **CHREV:** araştırmada %72–84, canlıda −1.024 $ (§2.3). Model sinyaline dayalı kural bar verisinden yeniden
  kurulamıyor (E22); "OOS + plasebo" yetmedi.
- **TP-01:** bot TP'sinden sonra fiyat botun yönünde devam ediyor (−33 puan @ 240 dk), sentetik olayda yok
  (TP-03). M3 "kazananı koştur" +29,5R ile aynı yöne işaret: sabit TP kazananı kesiyor. Ama post-hoc, C.
- **NDX'e özgülük:** çekiç NAS100 / GER40'ta artı, US2000'de hep eksi; KKB NDX'te var, DAX'ta yok; MA-02'de
  göreli kuralın artısı üç dönemde de yalnız NDX bacağında (+46 / +3 / +13 bp). Kaldıraçlı akış açıklamasını
  sınadım (MA-04): yarı iletken QQQ'yu geçmedi → açıklama doğrulanmadı. Neden NDX olduğu hâlâ açık soru.
- **C3 kazancının saati:** broker 2018–26'da %66'sı gece; QQQ 1999–2018'de %25'i gece (MA-01). Dilim sabit değil.

### F. Çapraz sembol / zaman / varlık

Dış değişkenler yön değil **rejim** belirliyor: VIX düzeyi dört kuralın ortak anahtarı; DXY / getiri / QQQ →
XAU ve BTC yönü X (TR-T13, BTC-X03…07). Korku ölçüsü varlığa özgü (BTC'de VIX değil kendi RV'si, §3-11).
Takvim etkileri sönmüş (KT-02) ya da besleme / rejim artefaktı (M19-07, TR-X18).

### G. Bot ve decider

- Botun girişi rastgeleden iyi değil (IO-01: −0,01R; tek olumlu NDX BUY +0,18 vs −0,05, n = 71).
- SL mekanizmaları braketin doğası (IO-02); çıkış kuralı varyantlarının hepsi X (M9, IO-07/10/16).
- Decider'da seçim alfası yok (OLD-25, DX-03); 20 XAU kuralı doğrulanmadı (DX-06…11).
- Kazancı fiilen alan kapılar **yön yasakları**: USOIL / XAU SELL (B1), NDX Cuma (B2), 1h trend hizası (B4).
  Çok koşullu skor kapıları gürültü (B10, B14, B15).
- İç tutarsızlık: 10-09 kartı VIXREG'e SHADOW dedi; aile canlı kaldı ve lotu Ekim'de 5 → 10 oldu.

### H. Serbest fikirler (savunulabilir, sınanmamış)

1. **Korkunun kendisini sat.** "Korku döner" en doğrudan VIX vadelisinde yaşar. C3b tetiğinde endeks almak
   yerine (ya da yanında) VIX vadeli CFD'si kısa. Aynı faktör, çeşitlendirme değil; kuyruk riski büyük.
2. **Amaç fonksiyonunu değiştir: kâr yerine "en kötü 5 gün".** MA-03 tek cümlede bunu söylüyor.
3. **Araştırmayı triyajla.** Arşiv bir ön-olasılık tablosu veriyor: gün-içi + kendi OHLC'si + kısa yön +
   braket → geçmiş başarı oranı sıfır. Yeni fikir bu dört özelliği taşıyorsa koşturma.
4. **Çağ anahtarı.** Kenar sakin on yılda yoksa (2010–17), yavaş bir "korku çağı" göstergesiyle tüm uzun-korku
   kurallarının boyutunu ayarla.

---

## 3. Hipotezler

Olasılıklar öznel tahmindir. $ mertebeleri NAS100 ≈ 27.800 ve mevcut lotlarla, kaba hesaptır.

### Bu oturumda sınananlar (ön kayıt → sonuç)

**MH-01 (MA-01) Gece dilimi — X.** İddia: C3 kazancı gecede birikir, 09:30'da çıkmak işlem SR'sini artırır.
Broker NAS100 M30, 2018-05 → 2026-11, n = 201 (özgün sonuç birebir: +45,7 bp, %62,2). Dilimler:
15:30→16:00 **−5,9 bp** · gece **+32,2** (tüm günler +4,5) · ertesi gündüz **+22,7** (tüm günler +3,2).
09:30'da çıkış ortalamanın %51'ini tutuyor, P(SR üstün) 0,08; 16:00 gir / 09:30 çık SR 0,259 vs 0,260.
Bağımsız QQQ 1999–2018 (n = 513): gece +8,6 / gündüz +25,0, gece payı %25. Beş ölçütün dördü düştü.
Kalan bilgi: kenar iki dilime yayılıyor, pay çağdan çağa değişiyor; zaman çıkışını kısaltma.

**MH-02 (MA-02) Göreli korku, piyasa-nötr — X.** NDX/SPX/DJI göreli RSI2 < 10 → geride kalanı al, sepeti sat.
KEŞİF 1999–2009 net +13,8 bp (P 0,98) ama yarılar +36 / −8 (dot-com). TEST 2010–18 brüt +0,6, net −6,4.
KÖR broker 2018–26 (4 endeks, n = 417) brüt +6,4, net +0,8, P 0,59. Etki 2004'ten beri yok.

**MH-03 (MA-04) Kaldıraçlı akış yoğunluğu — X.** Öngörü: yarı iletken > QQQ > savunmacı. Oynaklığa bölünmüş
getiri: QQQ 0,312 · SMH 0,241 · SOXX 0,159 · XLP 0,134 · XLU −0,047. Savunmacılar altta (✓), yarı iletken
QQQ'yu geçmedi (✗). Mekanizma doğrulanmadı.

### Sınanmayı bekleyenler

**MH-04 Boyutu kanıta bağla.** İddia: lot kanıt sınıfına göre verilirse en kötü gün küçülür, beklenen $ düşmez.
*Mekanizma:* kenarı ölçülmemiş ailede büyük lot yalnız varyans ekler. *Test:* bot kararları 06-30 → bugün;
kural: A/A− tam, B yarım, C/X ≤ 1/6 lot; ölçüt: en kötü 5 gün toplamı ≥ %50 küçülsün ve aynı kuralın 2024–25
Dukascopy yeniden üretiminde (CK-03/05 motoru) beklenen $ ≥ mevcut. Plasebo: lotları rastgele karıştır.
Sızıntı: lot kuralı karar anında bilinen sınıfa bağlı. *En yakın:* DTS-04 (sabit $-risk, X) — o risk
eşitlemeydi, bu kanıt ağırlığı. *Olasılık* %70. *En ucuz test:* MA-03 tablosunu yeniden ağırlıklandır (30 dk).
*Değer:* kuyruk küçülmesi; örneklem içinde kâr da küçülür (REENTRY kazancı 30 lotta geldi) — dürüst bedel bu.
*İlk karşı-olgu (koşuldu, örneklem içi, `results/ma03_lot_tavani.csv`):* bacak başına lot tavanı uygulansaydı —

| Lot tavanı | Net $ | En kötü 5 gün | En kötü gün | Günlük SR |
|---|---|---|---|---|
| yok (gerçek) | +21.903 | −22.001 | −8.628 | 0,111 |
| 10 | +14.036 | −9.592 | −2.875 | 0,163 |
| 5 | +9.996 | −7.842 | −2.385 | 0,154 |

Tavan kârı %36 düşürür, en kötü 5 günü %56; günlük SR 0,111 → 0,163. Yani büyük lotlu günler getiriden çok
varyans ekledi. Sınır: 72 gün, tek dönem, tek sembol; bağımsız dönem sınaması (b adımı) yapılmadı → C.

**MH-05 VIXREG SELL'i gölgeye al.** İddia: riskin %41'ini tüketen aile sıfır beklentili; kapatmak $ kaybettirmez.
*Mekanizma:* coşku dönmez. *Test:* ileri 60 gün gölge kaydı + boşalan zamana giren işlemlerin R'si (E19, E89).
Ölçüt: gölge ort. R ≤ +0,05 ve portföy $ farkı gürültü tabanında. *En yakın:* CK-01 (aynı hüküm, uygulanmadı).
*Olasılık* %80. *En ucuz:* CK-01'i 10-09 sonrası kararlarla güncelle (1 saat). *Değer:* ~0 $/ay, risk −%40.

**MH-06 Faktör tavanı.** İddia: korku gününde C3b + CAPREV + ORB + çekiç + DAYCOMBO/REENTRY BUY aynı anda uzun;
birleşik kuyruk tek tek kartların gösterdiğinden büyük. *Test:* 2018–26 işlem tablolarını (kesişim, c1_türev,
fitil sonuçları) mevcut lotlarla aynı takvime koy; 2020-02/03, 2022, 2025-04 en kötü 5 gün. Ölçüt: birleşik en
kötü gün > en büyük tekil × 1,5 ise tavan gerekir. *En yakın:* E110, FR-17 (iki kural). *Olasılık* %75.
*En ucuz:* 1 saat. *Değer:* kuyruk; tek kötü gün −5…−10 bin $ mertebesi.

**MH-07 İkinci faktörü aç: XAU günlük trend.** İddia: Golden Donchian korku faktöründen bağımsız. *Test:* kural
dondurulmuş (XS-01); gölge kaydı + günlük getiri korelasyonu C3b ile ≤ 0,2. Canlı için kart ölçütü 1'in seyrek
kural karşılığı tanımlanmalı (kullanıcı kararı). *En yakın:* XS-01 (B, hacim yüzünden gölge). *Olasılık* %60.
*Değer:* yılda ~5 işlem × +0,39R ≈ +2R/yıl; küçük ama bağımsız.

**MH-08 Sıkışma vetosu → XAU / BTC kırılımları.** KS-01c (A, 21 endeks) günlük sıkışma sonrası kırılımın
başarısız olduğunu gösterdi. Golden Donchian tam bu yapı. *Test:* XS-01'in 86 işlemini sıkışma bayrağına göre
böl; ölçüt: sıkışmalı kol ort. R < diğer kol, iki dönemde aynı işaret. *En yakın:* KS-01e (saatlik X) — burada
günlük ve başka varlık. *Olasılık* %40 (mekanizma varlığa özgü olabilir, §3-11). *En ucuz:* 1 saat.

**MH-09 Korku günü koşullu limit.** Y-01 koşulsuzdu. Likidite primi VIX ile büyüyorsa ters seçilim stres ∧ VIX
≥ 18,4 günlerinde tersine dönebilir. *Test:* Y-01a kuralı aynen, yalnız CAPREV durum günlerinde; Dukascopy
2021–26 KEŞİF/KÖR + NAS100 2016–21; martingal kontrol; ölçüt mutlak ort. R > 0, P ≥ %90, iki dönem.
*En yakın:* Y-01 (X), GF-17 "geri alım yarı etkili". *Olasılık* %20. *Değer:* CAPREV girişinde ~+0,1R × 10–25/yıl.

**MH-10 "Düşüş sonrası gün" anahtarı.** GR-01: NDX getirisinin %98'i düşüş sonrası günde. Eski BUY ailelerini
yalnız o günlerde aç. *Test:* bot BUY kararları dünün işaretine göre; taban = aynı gün sınıfında rastgele BUY
(E13). *En yakın:* GF-10 K5 (SELL tarafı), TR-KAPI. *Olasılık* %30. *En ucuz:* 30 dk.

**MH-11 Korkunun kendisini sat.** *Test:* VXX / VIXY günlük 2009→, C3b tetiğinde kısa, C3b çıkışında kapat;
2009–17 keşif, 2018–26 test; ölçüt: oynaklığa bölünmüş getiri QQQ kolundan büyük ve en kötü işlem ≤ 3× ort.
risk. Broker VIX sembolü ve spread'i ayrıca. *En yakın:* yok (yeni araç). *Olasılık* %30. *Değer:* aynı faktör.

**MH-12 Çağ anahtarı.** *Test:* QQQ 1999–2026 C3b olaylarını, girişten önceki 252 günün medyan VIX üçte birlik
dilimine göre böl (önceden bilinen); ölçüt: alt dilim ort. ≤ taban, üst iki dilim > 0, iki yarıda aynı.
*En yakın:* KS-01b (aynı günün VIX'i; bu yavaş ölçek). *Olasılık* %45. *En ucuz:* 30 dk. *Değer:* yıllarca
süren boş dönemi önceden tanımak; E110 uyarısı geçerli (Sharpe artmayabilir).

**MH-13 16:00 girişi.** MA-01 yan izi: olay günlerinde 15:30→16:00 −5,9 bp (isabet %44). *Test:* aynı ölçüm
US500/US30/US2000/GER40 kendi olaylarında + NAS100 1h 2016–18 son saat. *En yakın:* GM-01 (C), ME-06 (X),
ME-07 (sonuçsuz) — üçü de zayıf; beklenti düşük. *Olasılık* %25. *Değer:* ~+6 bp × 15/yıl, ihmal edilebilir.

---

## 4. Sıralama ve plan

Beklenen değer × olasılık / maliyet sırası: **MH-04 → MH-06 → MH-05** → MH-12 → MH-07 → MH-08 → MH-10 → MH-09 →
MH-11 → MH-13. İlk üçü yeni sinyal değil, mevcut riskin yeniden dağıtımı; hiçbiri yeni veri istemiyor.

1. **MH-04:** (a) MA-03 tablosunu kanıt ağırlıklı lotla yeniden hesapla; (b) DAYCOMBO / REENTRY'yi CK-05
   motoruyla 2024–25'te aynı lot kuralıyla yürüt; (c) sonuç ölçütü geçerse lot tablosunu `docs/KURAL_LOT_SEVIYELERI.md`
   önerisi olarak yaz. Uygulama kullanıcı kararı.
2. **MH-06:** canlı dört kuralın 2018–26 işlem tablolarını tek takvimde birleştir, en kötü günleri çıkar,
   sembol başı tavanın (4,5 lot) eski aileleri de kapsayıp kapsamadığını koddan doğrula.
3. **MH-05:** CK-01'i güncelle; 60 gün gölge; durma ölçütü önceden yazılı.

**Tek öneri: MH-04.** Gerekçe: arşivin en sağlam iki olgusu yan yana — (i) kanıtlı kenar seyrek ve küçük
lotta, (ii) botun dolar eğrisini kanıtsız ailelerin 30 lotluk günleri çiziyor. Yeni sinyal aramak yerine
bu uyumsuzluğu kapatmak, bugün eldeki veriyle yapılabilecek tek şey ve sonucu en az belirsiz olan.

## 5. Yapma listesi

1. Aynı sembolün kendi mumlarından gün-içi yön sinyali arama (gösterge, formasyon, çizgi, seviye, SMC, mum
   dizisi, bunların kesişimleri). Pine taramasının tespit sınırı +5 puan; altında bir şey varsa maliyeti geçmez.
2. NDX'te kısa taraf için kural arama ("coşku dönmez" her ölçekte ve MA-02 aynasında da aynı).
3. Limit / geri çekilme girişiyle "daha iyi fiyat" arama (Y-01, E66, E109).
4. Mevcut ailelere çıkış kuralı ekleme: BE, kilit, erken kes, TP/SL çarpanı (M9, IO-07/08/10/13/16).
5. XAU ve USOIL'de gün-içi kural ve haber başlığından yön (OLD-01/07, SM-05, TR-T2, HB-01/02).

Ek: C3'ün tutma süresini kısaltma (MA-01) ve endeks çifti geri dönüşü (MA-02) de artık bu listede.

## 6. Belirsizlikler

- Hesap büyüklüğü ve hedeflenen günlük / aylık risk bilinmiyor; $ mertebeleri buna bağlı.
- 30 lot (DAYCOMBO / REENTRY) ve VIXREG SELL 10 lot bilinçli karar mı? Dosyada yalnız sonuç var.
- CAPREV 10-09'dan beri canlı; `ndx_trades.parquet` içinde işlem yok. Hiç tetiklenmedi mi, ayrı mı kaydediliyor?
- Broker'da VIX vadeli CFD'si var mı, spread ve swap ne? (MH-11)
- Sembol başı 4,5 lot tavanı eski aileleri kapsıyor mu? Koddan doğrulanmadı.
- DAX, XAU, USOIL bot işlemleri bu oturumda incelenmedi (MA-03 yalnız NDX).
- Okuma sınırı: yukarıdaki "kapsam" notu. Kısaltılmış okunan bölümlerde gözden kaçan bir ön deneme olabilir.

---

## 7. EK — MA-05: "lot = kanıt sınıfı" sınaması (2026-11-10, ön kayıt PROTOCOL.md EK-2)

**A. Aile tam lotu hak ediyor mu? Bağımsız dönem (`results/ma05a.json`).** DAYCOMBO + ona bağlı REENTRY, kural
birebir, Dukascopy NDX 1m. CK-03 / CK-05 sayıları birebir yeniden üretildi (aile ortalamaları aynı).

| Dönem | İşlem | Gün | Ort. R | P(ort. R > 0) | 30 lotta toplam $ | En kötü gün | En derin düşüş |
|---|---|---|---|---|---|---|---|
| 2024 | 333 | 122 | +0,058 | 0,84 | +63.314 | −13.200 | −51.600 |
| 2025 | 348 | 102 | −0,049 | 0,12 | −56.579 | −13.200 | −76.862 |
| 2024 + 2025 | 681 | 224 | **+0,003** | **0,53** | +6.735 (%95: −152.961 … +157.940) | −13.200 | −88.221 |

Ölçüt (ort. R > 0, P ≥ %95, iki yıl da artı) **geçmedi**. İki yıllık bağımsız dönemde beklenti sıfırdan ayırt
edilemiyor; kuyruk ise lotla doğru orantılı. Lot başına ölçek: en kötü gün ≈ −440 $, iki yılda en derin düşüş
≈ −2.940 $, beklenen kazanç ≈ 0. Yani bu ailede lot seçimi bir getiri kararı değil, katlanılacak düşüş kararı.

**B. Lot zamanlaması beceri taşıdı mı? (`results/ma05b.json`)** 418 kararın lotları aile içinde 5.000 kez
karıştırıldı. Gerçek net (+21.903 $) dağılımın **%6,9** yüzdeliğinde; karıştırılmış lotların medyanı +37.101 $.
Gerçek günlük SR (0,111) %4,1 yüzdeliğinde; medyan 0,213. Ölçüt (≥ %95) geçmedi, sonuç ters yönde.
Neden: lot iyi giden dönemden SONRA büyütülmüş. DAYCOMBO 24 karar 1 lot, 19 karar 30 lot; lot–R korelasyonu
−0,19; sabit ortalama lotla +10.647 $ olurdu, gerçekte +406 $. REENTRY'de +24.165 $ yerine +18.628 $.

**C. Tüm semboller (`results/ma05c_semboller.csv`, 1.017 işlem, 84 gün, net +28.865 $).**

| Sembol · aile · yön | Karar | Risk payı | Net $ | Ort. R |
|---|---|---|---|---|
| NDX VIXREG SELL | 218 | %28,3 | +1.377 | +0,009 |
| NDX DAYCOMBO BUY | 44 | %16,7 | +2.770 | +0,176 |
| USOIL MOMSR BUY | 97 | %16,1 | +3.305 | +0,020 |
| NDX REENTRY BUY | 21 | %14,8 | +15.735 | +0,311 |
| DAX CHREV BUY | 22 | %4,3 | +3.433 | +0,131 |
| USOIL MOMSR SELL | 44 | %2,4 | −2.199 | −0,140 |

Sembol netleri: NDX +26.995 · DAX +3.101 · USOIL −1.125 · XAU −107. Toplam kârın %94'ü NDX'ten, onun da
%78'i REENTRY'den. Tüm hesapta en kötü 5 gün −20.677 $, en iyi 5 gün +41.348 $, günlük SR 0,120.

**Hüküm.** MH-04 bu iki aile için destekleniyor (sınıf B): bağımsız iki yılda kanıtlanmış beklenti yok, lot
artışı beceri taşımamış. Hangi lotun doğru olduğu hesabın katlanabileceği düşüşe bağlı; oran yukarıda.
Sınır: REENTRY'nin canlı 34 kararı iyi (+0,31 / +0,46R), bu n ile reddedilemez de doğrulanamaz da.
