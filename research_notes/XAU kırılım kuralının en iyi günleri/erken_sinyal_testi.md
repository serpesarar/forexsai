# XAU R0B_G1 (MK-04) sağ kuyruğunu girişte önceden işaretleyen ex-ante özellik var mı? — ön-kayıtlı test

Kaynak kodu ve çıktılar: `/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/`
(ön kayıt [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/PROTOCOL.md),
sonuçlar `results/`). Bu bir web araştırması değil, nicel bir sınamadır. Aşağıdaki "kaynak"ların hepsi bu çalışmanın
yerel dosyalarıdır. Kural ve veri `research/decider_xau_tpsl_20261015/mekanik/` içinden SALT-OKUNUR import edildi. O
klasöre ve `docs/KAPI_KAYIT_DEFTERI.md`'ye dokunulmadı.

## 1. Ne ön-kayda alındı, sızıntı ve tasarım nasıl denetlendi?

### Takeaway
PROTOCOL.md 2026-10-16 04:20 UTC'de, bu çalışmada hiçbir R/gün sonucu hesaplanmadan yazıldı. İçinde 10 ex-ante özellik
var, her birinin yönü ve tek eşiği önceden sabit. Her özellik 2 kullanımla sınandı (FİLTRE / 2× BOYUT), toplam 20 test.
Keşif 2008–2016, doğrulama 2017→2026-06-16, kasa ise broker 1m 2026-06-17→10-14. Önek sızıntı testi temiz çıktı.
Ön-kayıtlı sürüklenme kontrollerinden biri (aynı-hafta) sonuç görüldükten sonra E15 tuzağı olarak tanındı. Yerine
nedensel bir kontrol konuldu ve bu sapma dosyaya tarihli olarak yazıldı.

### Cited Findings
- **Taban (aynı kod, MK-06 ile birebir):** keşifte 5.687 ham olay; tek pozisyonda n=1.794, 3,82 işlem/hafta, +0,064R,
  toplam +114,4R, en iyi 20 günün payı %139. Doğrulamada 6.716 olay; tek pozisyonda n=1.870, 3,78/hafta, +0,094R, +176,1R,
  en iyi 20 günün payı %87. İki dönemin toplamı 3.664 işlem ve +290,5R ediyor, MK-06'daki sayının aynısı —
  [main.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/main.txt)
- **Özellikler (yönleri ön-kayıtlı):**
  - F1 H1 BB sıkışması: önceki barda BB(20,2) genişliği, son 120 barın %20'liğinin altında. R4 tanımının aynısı.
  - F2 D1 NR4 veya inside day.
  - F3 kapanışla kabul: kapanış önceki 20 barın tepesinin üstünde ve kapanış konumu ≥0,6.
  - F4 hacim: aynı UTC saatinin önceki 20 günlük medyan hacminin ≥1,5 katı.
  - F5 D1 kapanışı EMA200'ün üstünde.
  - F6 H1 tepesi, son 20 kapanmış D1'in tepesini aşıyor (çok zaman dilimli kırılım).
  - F7 52 haftalık (250 D1) tepe.
  - F8 UTC 07–15 seansı.
  - F9 6 barlık momentum/ATR, keşif olaylarının %66,7'liğinin üstünde. Eşik sonuçlara bakılmadan, yalnız özellik
    dağılımından hesaplandı: 2,556.
  - F10 önceki günün VIX kapanışı ≥20.
  - DXY bilerek alınmadı (OLD-07/OLD-10: XAU'da makro yön bağı işaret çevirdi) —
    [PROTOCOL.md §0, §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/PROTOCOL.md)
- **Önek sızıntı testi:** veri 3 rastgele noktada kesildi (2018-04, 2018-11, 2022-07). Kesimden önceki 62–88 bin barda 17
  özellik sütununun hiçbiri tam veriyle farklı çıkmadı —
  [00_leak.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/00_leak.txt)
- **Rastgele alt küme boşu (E24):** sonuç ikilisi (R, süre) her yıl içinde dairesel kaydırıldı, 1.000 tekrar. Böylece
  boş küme kuralın KENDİ işlemlerinden oluşuyor, aynı büyüklükte, aynı yıl karışımında ve kümelenmesi korunmuş. 20 test
  aynı kaydırmayı paylaştı; bu max-T düzeltmesini mümkün kıldı —
  [01_main.py](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/01_main.py)
- **Sapma (E15'in hafta ölçeği):** ön-kayıtlı M2 kontrolü "aynı ISO haftasındaki tüm barlarda BUY" idi. Kırılım olan
  haftalar zaten yükselen haftalar; haftanın kırılımdan önceki barlarının 20 barlık ileri getirisi o hareketi içeriyor.
  Doğrulamada kural +0,111R iken bu "kontrol" +0,279R verdi. c5 geçersiz sayıldı. Yerine nedensel P1-F kondu: aynı yıl,
  aynı UTC saati ve aynı bayrak durumundan rastgele bar, 40 çekim —
  [posthoc.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/posthoc.txt);
  [PROTOCOL.md §10](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/PROTOCOL.md)

### Inferences
- Sapma hiçbir verdikti değiştirmiyor: 20 testin 20'si zaten c1'de (seçim düzeltmeli anlamlılık) düştü.
- Yine de bu yeni bir yöntem dersi. "Aynı dönemden kontrol" (E29'un önerisi) dönemi olayın kendi sonucuyla seçerse
  geleceğe bakar. Kontrol penceresi kararın ÖNCESİNE (geçmiş hafta) ya da sonuçtan bağımsız bir anahtara (yıl×saat×bayrak)
  bağlanmalı.

### Gaps
- Doğrulama Duka 2026-06-16'da kesildi. Görev "2026-09'a kadar" diyordu, ama 06-17 sonrası broker kasasıyla çakışacaktı.
  Duka'nın 06-17→09-30 kısmı ayrıca koşulmadı.
- Görevde geçen Pazartesi boşluğu, kırılım öncesi aralık uzunluğu ve DXY özellikleri kapsam dışı bırakıldı (≤10 özellik sınırı).

## 2. Her özellik için içeride/dışarıda R, sağ kuyruk ve en iyi gün lifti

### Takeaway
Doğrulama döneminde hiçbir özellik, kuralın kendi işlemlerinden çekilmiş rastgele alt kümeyi anlamlı biçimde geçemedi
(ham p en iyi 0,137). İçeride/dışarıda farkları +0,02…+0,06R düzeyinde, rastgele alt kümenin sd'si (0,05–0,15) içinde kaldı.

En güçlü keşif bulgusu F2 (D1 NR4/inside). Keşifte etkisi çok büyüktü ve seçim düzeltmesinden de geçiyordu: z 3,9–4,5,
max-T p 0,000. Doğrulamada etki dörtte birine indi, kasada ters döndü. Bu tam bir E12/E17 örüntüsü.

### Cited Findings
Tek pozisyonlu taban kümesinde ortR içeride/dışarıda, P(R≥3) içeride/dışarıda ve en iyi 20 gündeki bayrak lifti (keşif → doğrulama):

| Özellik | işlem payı (D) | ortR iç/dış K | ortR iç/dış D | P(R≥3) iç/dış D | en iyi-20 lift K → D |
|---|---|---|---|---|---|
| F1 H1 sıkışma | %45 | +0,087 / +0,046 | +0,106 / +0,084 | %8,0 / %7,2 | 1,60 → 1,16 |
| F2 D1 NR4/inside | %35 | **+0,274 / −0,053** | +0,135 / +0,072 | %9,0 / %6,8 | 1,95 → 1,24 |
| F3 kapanışla kabul | %45 | +0,032 / +0,093 | +0,039 / +0,140 | %6,5 / %8,4 | 0,64 → 0,67 |
| F4 hacim | %27 | −0,045 / +0,090 | +0,108 / +0,089 | %6,6 / %7,9 | 0,90 → 1,14 |
| F5 D1>EMA200 | %78 | +0,120 / +0,002 | +0,090 / +0,110 | %7,5 / %7,7 | 1,41 → 1,01 |
| F6 D1 20-gün kırılımı | %15 | +0,021 / +0,070 | +0,152 / +0,084 | %8,5 / %7,4 | 0,33 → 0,87 |
| F7 52-hafta tepesi | %6,5 | −0,040 / +0,069 | +0,136 / +0,091 | %9,0 / %7,4 | 0,96 → 1,33 |
| F8 Londra+NY seansı | %62 | +0,069 / +0,055 | +0,048 / **+0,170** | %7,0 / %8,5 | 0,88 → 0,56 |
| F9 6-bar momentum | %20 | +0,166 / +0,040 | +0,144 / +0,081 | %7,9 / %7,4 | 0,69 → 1,51 |
| F10 VIX≥20 | %32 | +0,179 / −0,021 | +0,110 / +0,087 | %7,6 / %7,5 | 1,13 → 1,09 |
— [tail.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/tail.csv)

- **Rastgele alt kümeye karşı d (doğrulama):**

  | Özellik | FİLTRE d (ham p) | BOYUT2 d (ham p) |
  |---|---|---|
  | F1 | +0,015 (0,58) | +0,022 (0,40) |
  | F2 | +0,031 (0,32) | +0,064 (0,14) |
  | F3 | −0,004 | −0,101 |
  | F4 | +0,036 (0,53) | +0,019 (0,37) |
  | F5 | −0,005 (0,93) | −0,021 (0,92) |
  | F6 | +0,088 (0,22) | +0,068 (0,37) |
  | F7 | +0,215 (0,21) | +0,044 (0,66) |
  | F8 | +0,006 | −0,122 |
  | F9 | −0,028 | +0,063 (0,27) |
  | F10 | +0,028 (0,55) | +0,023 (0,63) |

  Boşun ortalaması sıfır değil. Örneğin F5 BOYUT2'de +0,107, çünkü bayrak yıllarla ilişkili ve FİLTRE + tek pozisyon
  yeniden yürütmesi kendi başına yaklaşık +0,03 üretiyor. Ham "içeride daha iyi" farkı bu yüzden yanıltıcı —
  [tests.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/tests.csv)
- **Nedensel sürüklenme kontrolü (P1-F DiD):** DiD = (R − aynı yıl/saat/bayrak rastgele BUY), içeride eksi dışarıda.
  Gün-blok bootstrap ile:

  | Özellik | Keşif | Doğrulama |
  |---|---|---|
  | F2 | +0,123 (P 0,90) | +0,029 (P 0,64) |
  | F7 | +0,018 | +0,221 (P 0,93) |
  | F6 | −0,024 | +0,104 (P 0,86) |
  | F10 | +0,040 | +0,052 (P 0,73) |
  | F3 | −0,069 | −0,061 (iki dönemde de P(>0) ≈ 0,06) |
  | F1 | +0,010 | −0,003 |
  | F5 | −0,007 | −0,068 |
  | F9 | −0,065 | −0,006 |

  Hiçbir özellik iki dönemde birden anlamlı değil —
  [did_causal.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/did_causal.csv)
- **F2'nin yıl yıl dökümü (POST-HOC):** bayraklı eksi bayraksız fark 2008–16'da 9 yılın 8'inde pozitif
  (2016 +0,90, 2008 +0,48). 2017–26'da 10 yılın yalnız 6'sında pozitif (2017 −0,35, 2021 −0,21, 2026 −0,23).
  F10 VIX≥20 yıllara göre işaret değiştiriyor: 2020 −0,42, 2021 −0,32, 2022 +0,52. F7'de pozitif yıl sayısı 0/4 ve 1/8 —
  [posthoc.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/posthoc.txt)
- **Broker kasası (2026-06-17→10-14):** taban 205 ham olay +0,145R, tek pozisyonda 56 işlem +0,122R.
  - F2: FİLTRE −0,437, BOYUT2 −0,934 (bayraklı 23 işlem).
  - F5: −0,343 / −0,565.
  - F1: −0,069 / −0,358.
  - F6: +0,288 / +0,193 (10 işlem).
  - F4: +0,577 / +2,161 (yalnız 4 işlem).
  - F7: kasada 0 olay.
  - F10: 1 işlem.
  - n çok küçük; yalnız işaret okunabilir —
  [holdout.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/holdout.csv)

### Inferences
- **"Önceden işaretlenebilir sağ kuyruk" bu 10 özellikte yok.** Doğrulamada P(R≥3) içeride ile dışarıda arasındaki fark
  en çok +2,2 puan (F2). En iyi 20 gün lifti en çok 1,5 (F9), ve bu F9'un keşifte 0,69 olan liftini tersine çeviriyor.
  Kaba bir tahminle en iyi 20 günde yaklaşık 40 işlem var; %35 oranlı rastgele bir bayrağın lift sd'si bu durumda
  yaklaşık 0,2 olur. Yani 1,1–1,5 liftler gürültü bandında. Bu sd'yi resmi olarak hesaplamadım; aşağıda boşluk olarak duruyor.
- **F5 (D1 trend) MK-07 bulgusunu bayrak olarak da doğruluyor.** Etkinin tamamı yıl seçimi (boşun ortalaması +0,107).
  Yıl içinde bayraklı işlemler daha kötü (−0,021).
- **F3 (kapanışla kabul) iki dönemde de ön-kayıtlı yönün tersine çalışıyor.** Fitille kırılım, kapanışla kırılımdan
  iyi: doğrulamada +0,140'a karşı +0,039. Ama E28'e göre "kötü hücre ≠ ters sinyal"; kasada da işaret ters (+0,127).
  Bu yüzden ters kural olarak önerilmiyor.
- **F8 doğrulamada Asya kırılımlarının daha iyi olduğunu gösteriyor (+0,170'e karşı +0,048).** Keşifte fark yaklaşık
  sıfır. Rejime bağlı görünüyor, ön-kayıtlı mekanizmayı desteklemiyor.

### Gaps
- En iyi gün liftinin boş dağılımı resmi olarak hesaplanmadı (yalnız kaba binom tahmini var).
- Kasada F4 ve F10 için n ≤ 4: işaret bile anlamsız.

## 3. Çoklu sınama düzeltmesi (Holm + max-T)

### Takeaway
Doğrulamadaki 20 testin hiçbiri düzeltmeden geçmedi: en küçük max-T p 0,869 (F2 BOYUT2), Holm p'lerinin hepsi 1,0.
Keşifte yalnız F2 max-T'yi geçmişti (p 0,000). Seçim düzeltmesinden geçen bir keşif bulgusu bile ileri dönemde
taşınmadı.

### Cited Findings
- Doğrulama max-T p: F2 BOYUT2 0,869; F7 FİLTRE 0,933; F6 FİLTRE 0,945; geri kalanların hepsi ≥0,978 —
  [verdicts.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/verdicts.csv)
- Keşifte F2: FİLTRE d +0,193 (z 3,88), BOYUT2 +0,327 (z 4,51), max-T p'leri 0,000. Diğer 18 testte max-T p ≥0,79 —
  [tests.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/tests.csv)

### Inferences
- E12/E17/E24 burada bir kez daha görülüyor. 9 yıllık bir keşif döneminde tek-özellikli, max-T'den geçen ve yıl yıl
  8/9 tutarlı bir etki, sonraki 9,5 yılda gürültüye dönüştü. Altın 2008–16 ile 2017–26 arasında farklı bir rejimde
  (2011–15 ayı piyasası, sonra 2019+ boğa). D1 sıkışmasının kırılım kuyruğu üzerindeki etkisi rejime bağlı olabilir.

### Gaps
- Bu dönem bölünmesinde F2'nin neden söndüğü (rejim mi, keşifteki şans mı) ayrıştırılamıyor; bunun için bağımsız bir
  piyasa ya da yeni veri gerekir.

## 4. Sermaye eğrisi: en iyi günlere bağımlılık, düşüş, haftalık ölçüler

### Takeaway
Doğrulama döneminde hiçbir FİLTRE ya da BOYUT2 stratejisi, en iyi 20 gün çıkarıldıktan sonra tabandan (+0,013R)
anlamlı ölçüde daha iyi değil. Haftalık Sharpe'ı tabanı (0,107) aşan kullanımlar F2 BOYUT2 (0,108) ve F6 BOYUT2
(0,109); ikisi de pratikte eşit. Kuyruğa bağımlılığı azaltan bir özellik bulunmadı.

### Cited Findings
- **Taban (doğrulama):** 3,78 işlem/hafta, +0,356 R/hafta, haftalık Sharpe 0,107, pozitif hafta %45,1, maks. düşüş
  −47,7R, en iyi 20 gün hariç +0,013, P(EV>0) 0,993. Keşif tabanında aynı ölçü −0,025, maks. düşüş −59,1R —
  [strat.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/strat.csv)
- **FİLTRE (doğrulama):**

  | Özellik | n | işlem/hafta | ortR | Sharpe | maks. düşüş | en iyi-20 hariç |
  |---|---|---|---|---|---|---|
  | F2 | 705 | 1,42 | +0,125 | 0,083 | −35,5 | −0,041 |
  | F7 | 171 | 0,35 | +0,309 | 0,090 | — | −0,230 |
  | F6 | 412 | 0,83 | +0,182 | 0,098 | — | −0,076 |
  | F8 | — | 3,04 | +0,100 | 0,101 | −28,7 | +0,001 |
  | F10 | 606 | 1,22 | +0,123 | 0,078 | — | −0,079 |

  Ortalama R'yi yükselten filtreler bunu kuyruğu yoğunlaştırarak yapıyor: F7'de en iyi 20 günün payı %164, F2'de %132.
- **Keşifte F2 FİLTRE çarpıcıydı:** +0,257R, maks. düşüş −15,3R (taban −59,1), Sharpe 0,160 (taban 0,080), en iyi 20 gün
  hariç +0,040 (taban −0,025). Doğrulamada bunların hiçbiri tekrarlanmadı.
- **BOYUT2 riski büyütüyor:** maks. düşüş doğrulamada −48…−80R (taban −47,7R). Risk başına R değişmiyor.

### Inferences
- Kuralın sağ kuyruğu (2008–09, 2020, 2024–25 gibi çok günlü altın rallileri) giriş anındaki H1/D1 durumundan ya da
  önceki günün VIX'inden okunamıyor. Kuyruk, girişten SONRA gelen 20 saatlik yolun bir özelliği. Bu, "braket ≠ zaman"
  (§3 meta-ders 5) dersiyle tutarlı: kenar tetikte değil, tutuşta.
- Pratik sonuç: MK-04'ü canlıya alma kararı (B+) bu çalışmadan sonra da değişmiyor. Boyutlandırma ya da filtreleme
  kuyruğa bağımlılığı azaltmıyor. Tek pozisyon, 1×, filtresiz kural hâlâ en temiz sürüm.

### Gaps
- Swap/finansman maliyeti modellenmedi (MK-06'daki ile aynı).
- Çok özellikli birleşimler bilerek sınanmadı (ön kayıt §8). Tek özelliklerin hiçbiri taşınmadığı için bir birleşimin
  taşınması beklenmez.

## 5. Verdikt ve gerçek zamanlı entegrasyon tarifi

### Takeaway
Ön-kayıtlı şemaya göre **20 testin 20'si RED**. Doğrulamada hiçbirinde "d > 0 ve ham p ≤ 0,10" sağlanmadı, bu yüzden
C bile çıkmadı. Canlıya ya da gölgeye bağlanacak bir bayrak yok. En fazla, MK-04 gölgesinin kayıtlarına F2/F6/F7
bayrakları sıfır maliyetle eklenip ileride yeni veriyle bakılabilir.

### Cited Findings
- Verdikt tablosu (c1–c6 sütunları ve verdikt) —
  [verdicts.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/verdicts.csv)
- F2 ve F7'nin bot/decider'da gerçek zamanlı hesaplanması, kapanmış D1 barlarından (NY 17:00 sınırı) yapılır. Önek
  testi bu hesabın geleceğe bakmadığını gösterdi:
  - F2: son kapanmış günün aralığı ≤ son 4 günün minimumu, ya da inside day.
  - F7: H1 tepesi ≥ son 250 kapanmış D1 tepesinin maksimumu.

  Kaynak: [features.py](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/features.py);
  [00_leak.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/erken_sinyal/results/00_leak.txt)

### Inferences
- **Özellik başına verdikt:**
  - F1 RED.
  - F2 RED: keşifte A adayı gibiydi, doğrulamada söndü, kasada ters.
  - F3 RED: ters yönde tutarlı, ama E28 gereği ters sinyal sayılmaz.
  - F4 RED.
  - F5 RED: yalnız sürüklenme yılı seçiyor.
  - F6 RED: keşifte negatif, doğrulamada pozitif.
  - F7 RED: n küçük, kuyruğa bağımlı, kasada olay yok.
  - F8 RED.
  - F9 RED.
  - F10 RED: yıllara göre işaret değiştiriyor.
- **Entegrasyon:** yok. İsteğe bağlı bir adım olarak `yeni deneme/xau_shadow.py` (MK-04 gölgesi) her kayda
  `f2_d1_nr4_inside`, `f6_d1_dc20`, `f7_d1_hh250`, `vix_prev` alanlarını yazabilir. Bunlar yalnız ileride yeni veriyle
  bakmak içindir, emir ya da boyut kararına girmez. Bu çalışmada koda dokunulmadı.

### Gaps
- Kasa n'si (56 tek pozisyonlu işlem) özellik bazında işaret testini bile güçsüz kılıyor. Gölge birikimi yıllar sürer.

### Defter satırı önerileri
(§2.6 MK serisine; biçim §6. Defter bu çalışmada değiştirilmedi.)

| ID | Tarih | Fikir | Sonuç | Sınıf |
|---|---|---|---|---|
| MK-08 | 2026-10-16 | **R0B_G1 (MK-04) sağ kuyruğunu girişte işaretleyen ex-ante bayrak** (`research/xau_best_days_20261015/erken_sinyal/`, ön kayıt PROTOCOL.md 04:20 UTC). 10 bayrak: H1 BB sıkışma, D1 NR4/inside, kapanışla kabul, hacim ≥1,5× saat medyanı, D1>EMA200, D1 20-gün kırılımı, 52-hafta tepesi, UTC 07–15, 6-bar momentum üst tercil, VIX(d−1)≥20. 2 kullanım: FİLTRE (+ tek pozisyonu yeniden yürüt) ve 2× BOYUT. Keşif Duka 2008–16, doğrulama 2017→2026-06, kasa broker 1m 06-17→10-14. Boş: yıl-içi dairesel kaydırılmış kendi işlemleri + max-T, Holm, nedensel P1-F DiD | **20/20 RED.** Doğrulamada en iyi ham p 0,137 (F2 2×), max-T ≥0,87. **F2 D1 NR4/inside:** keşifte +0,274 / −0,053 (z 4,5, max-T p 0,000, 9 yılın 8'i +, maks. düşüş −15R vs −59R), doğrulamada +0,135 / +0,072 (p 0,14), kasada −0,93 → E12/E17. D1>EMA200 yalnız yıl seçiyor (boş +0,107, gerçek −0,021). Kapanışla kabul iki dönemde de TERS (+0,039 vs +0,140), kasada değil. P(R≥3) farkı ≤2 puan, en iyi 20 gün lifti ≤1,5 (gürültü bandı). Hiçbir kullanım en iyi 20 gün hariç ortR'yi (+0,013) ya da haftalık Sharpe'ı (0,107) belirgin iyileştirmiyor | **X** (kuyruk girişte okunmuyor; MK-04 1× filtresiz kalır) |

§1'e önerilen tuzak:

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E31 | **Aynı-hafta (aynı-dönem) sürüklenme kontrolü, dönem olayın kendi sonucuyla seçildiğinde geleceğe bakar.** Bu, E15'in hafta ölçeğidir: kırılım olan hafta yükselen haftadır; haftanın kırılım öncesi barlarının ileri getirisi kırılım hareketini içerir | MK-08: ön-kayıtlı M2 kontrolü kuralı +0,111R'ye karşı "aynı-hafta rastgele BUY" +0,279R gösterdi. F1 "sürüklenme üstü" P 0,994 sahte çıktı, nedensel kontrolde −0,003 | kontrolü kararın öncesine (geçmiş hafta) ya da sonuçtan bağımsız bir anahtara (yıl × UTC saati × bayrak durumu, P1-F) bağla; E29'un "aynı gün eşlemesi" de ancak o günün kalan yolunu kontrol içine almıyorsa geçerlidir |
