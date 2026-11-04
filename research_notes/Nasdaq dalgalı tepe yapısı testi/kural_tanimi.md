# Nasdaq "dalgalı tepe aralığı" — kural tabanlı (yorumlanabilir özellik) tanım ve 10 yıllık sonuç testi (ME-10)

Kapsam: kullanıcının NAS100 1h grafiklerinde işaretlediği üç bölge (T1 2026-07-06→07-21, T2 07-17→07-29, T3 08-13→08-20)
şekil eşleştirmesinden bağımsız olarak, birkaç şeffaf kural ile tanımlandı; kurallar sonuç görülmeden donduruldu ve
yapı oluşurken / tamamlandıktan sonra +1 saat, +1 gün (24 bar), +5 gün (120 bar) getiriler getiri+oynaklık eşli tabana,
koşulsuz tabana ve plaseboya karşı, olay (bölüm) düzeyinde, iki yarıda ve DAX'ta sınandı. Tüm sayılar bu oturumda yerel veriyle
hesaplandı (web kaynağı kullanılmadı; kaynaklar yerel dosyalardır). Kod/çıktı: `research/benzerlik_tepe_20261019/kural/`.

## 1. Şablonların özellik profili (sonuçtan önce, yalnız veriden)

### Takeaway
Üç örneği ortak ve seçici biçimde ayıran tek özellik **"son ~2 haftalık pencerenin dibine düşüşle bitmek, pencere tepesi son 60
günün tepesine yakınken"**; kullanıcının "oynak, çalkantılı, derin geri çekilmeli" izlenimi T2 dışında ölçüde görünmüyor
(oynaklık, salınım sayısı ve verimlilik geçmiş yılın medyanı civarında).

### Cited Findings
- Şablon süreleri (20:00 UTC sorgu günü): T1 kullanıcı 12 gün (07-17'ye inceltilmiş 10 gün), T2 9 gün, T3 6 gün → kural penceresi
  W = 9 gün (medyan) seçildi — [01_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/01_stdout.txt)
- İnceltme: kullanıcı yapıyı "düşüşle biten" diye tarif ediyor; T1'in son 5 işlem günündeki en düşük kapanış 2026-07-17 (28.566);
  kullanıcının 07-21 sonu kısmi toparlanmayı içeriyor (pencere içi konum pos 0,55). T2 (07-29) ve T3 (08-20) için aynı kural kullanıcı
  sonunu verdi — [01_sablon_ozellikleri.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/01_sablon_ozellikleri.json)
- W = 9 sondaki pencerede değerler [geliştirme 2017-03→2025-11 yüzdeliği], T1(07-17) / T2 / T3:
  pos (kapanışın pencere aralığındaki yeri) 0,221 [14] / 0,035 [3] / 0,093 [6];
  9 günlük net getiri −3,90σ [11] / −5,97σ [5] / −1,52σ [22] (≈ −%3,8 / −%6,4 / −%1,6);
  pencere tepesinin son 60 gün tepesine uzaklığı −%3,0 [25] / −%5,2 [17] / −%1,7 [34] (σ: −3,02 / −4,83 / −1,64);
  1h oynaklık / son 1 yılın medyanı 1,12 [61] / 1,59 [84] / 0,74 [20];
  ≥ 1σ zigzag salınımı 6 [60] / 11 [86] / 3 [26]; verimlilik |net|/yol 0,101 [64] / 0,128 [75] / 0,064 [42];
  alçalan tepe sayısı 1 / 4 / 0 — [01_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/01_stdout.txt)
- Mutlak oynaklık: T3 yıllıklandırılmış %13,8 (10 yılın 32. yüzdeliği, son 60 günün medyanının 0,58'i); T1 %19,9 (62.); T2 %28,7 (84.)
  — bu oturumdaki ek ölçüm (PROTOCOL §3'te kayıtlı) — [PROTOCOL.md](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/PROTOCOL.md)
- Dağılım bağlamı: 9 günlük pencere tepesi günlerin ~%83'ünde son 60 günün tepesinin 4,83σ yakınında; medyan gün 5 salınım,
  verimlilik 0,077, pos 0,71 — [01_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/01_stdout.txt)
- Özellik kodunun önek-sızıntı testi: veri 2019-06, 2022-03, 2025-11'de kesildiğinde önceki tüm sorgu günlerinin özellik farkı 0 (NDX ve DAX)
  — [00_sizinti_denetimi.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/00_sizinti_denetimi.txt)

### Inferences
- Görsel "dalgalı/oynak" algı büyük ölçüde grafik ölçeğinden geliyor olabilir: 2026'nın geçmiş yılı (2025-07→2026-07) zaten oynak
  olduğundan pencereler göreli olarak sıradan. Tarif edilen yapı nicel olarak "yakın-tepeden 1,5–6σ'lık düşüşle aralığın dibine inen
  1,5–2 haftalık pencere"ye indirgeniyor.
- T2 kalıbı (en oynak, en çok salınımlı, en çok alçalan tepeli) diğer ikisinden belirgin farklı; T3 ise kısa ve sakin bir tepe+düşüş.
  Üç örnek tek bir sıkı kurala sığmıyor; "en gevşek şablon değeri" ilkesi oynaklık/salınım koşullarını bağlayıcı olmaktan çıkarıyor.

### Gaps
- Kullanıcının bölge sınırları yaklaşık (el çizimi); T1 sonu inceltmesi bir araştırmacı tercihi (kullanıcı sonuyla ayrı duyarlılık koşuldu, §3).
- Capital.com CFD (kullanıcının grafiği) ile kullanılan NDX CFD 1h serisi farklı beslemeler: gün tepeleri genelde uyumlu (07-10 ve 07-15
  tepeleri ~29.850 her ikisinde), fitillerde göz kararı 50–150 puan fark var (07-17 dibi grafikte ~28.360, veride 28.209; 07-29 dibi ~26.990
  vs 27.050). Bar bar karşılaştırma yapılmadı; σ-birimli kurallar bu farka duyarsız olmalı ama kanıtlanmadı.

## 2. Kural setleri, sıklık ve şablonlarda yanma

### Takeaway
Üç ön-kayıtlı kural (K1 gevşek, K2 çalkantı-vurgulu, K3 tepe-şartsız kontrol) şablonlarda yapı gereği yanıyor ve seyrek
(K1 günlerin %3,8'i, yılda ~4 bölüm); dedektör olarak çalışıyor.

### Cited Findings
- Dondurulmuş kurallar (eşikler şablon değerlerinden, 3 ondalığa dışa yuvarlanmış): **K1** pos ≤ 0,222 ∧ net ≤ −1,524σ ∧ tepeye uzaklık ≥ −4,827σ ∧
  oynaklık oranı ≥ 0,742 ∧ ≥ 3 salınım ∧ verimlilik ≤ 0,129; **K2** (T1+T2) K1 + net ≤ −3,901σ, oynaklık ≥ 1,115, ≥ 6 salınım, ≥ 1 alçalan tepe;
  **K3** = K1 eksi yakın-tepe koşulu. Oluşum = bölümün ilk yanan günü (bölüm ayırıcı > 10 gün); tamamlanma = kural ≥ 2 gün yanıp söndüğü ilk gün
  (aynı 10 gün kümelemesiyle ilk sinyal) — [PROTOCOL.md](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/PROTOCOL.md)
- NDX geliştirme (2017-03→2025-11, 8,74 yıl): K1 günlerin %3,76'sı, 36 oluşum bölümü (yılda 4,1), 14 tamamlanma, bölüm başına medyan 2 yanan gün;
  K2 %1,24, 16 bölüm, 4 tamamlanma; K3 %5,55, 46 bölüm, 20 tamamlanma; K1-lit (kullanıcının T1 sonu) %13,9, 55 bölüm, 46 tamamlanma —
  [02_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_stdout.txt)
- Şablonlarda: K1 ve K3 T1(07-17), T2(07-29), T3(08-20)'de yanıyor, kullanıcının T1 sonunda (07-21) yanmıyor; K2 T1 ve T2'de yanıyor, T3'te değil;
  K1-lit dördünde de yanıyor — [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)
- 2026 yazında K1'in yandığı günler: 06-05, 06-26, 07-17, 07-23, 07-24, 07-29, 08-20 (07-07/08 ve 07-13 düşüşleri yanmadı); 2026 oluşumları
  01-20, 02-04, 03-20, 06-05, 06-26, 07-17, 08-20; tamamlanmalar 02-06, 07-27 — [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)
- NDX K1 geliştirme olaylarının çoğu 9 günlük pencerede 60 günlük tepeyi içeriyor (tepeye uzaklık 0) — örn. 2018-02-02, 2020-09-08, 2021-12-01,
  2024-07-18, 2025-02-24 — [02_olaylar.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_olaylar.csv)
- W duyarlılığı (aynı yöntemle yeniden türetilmiş K1): W = 6 → günlerin %4,4'ü, 44 bölüm; W = 12 → %2,4, 30 bölüm —
  [02_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_stdout.txt)

### Inferences
- K1 ile K3 neredeyse aynı olay kümesini seçiyor (36 ↔ 46 bölüm): yakın-tepe koşulu (son 60 gün tepesinin ≤ ~%5 altı) boğa piyasasında
  az şey eliyor. K2 kullanıcının sözel tarifine en yakın ama tamamlanma olayı çok az (4) → sınanabilir değil.
- Tamamlanma tanımı (≥ 2 ardışık yanan gün) olay sayısını oluşumun ~%40'ına düşürüyor; ≥ 20 bağımsız olay ölçütü tamamlanma hücrelerinde
  K1/K2 için baştan karşılanamıyordu (güç hesabı ön-kayıttan önce yapılmalıydı — ME-07 dersinin tekrarı).

### Gaps
- Kuralların kullanıcının gözüyle "aynı yapı" olarak onaylanıp onaylanmadığı sınanmadı (ME-08'deki gibi bir etiketleme turu yapılmadı);
  `02_olaylar.csv` tarih listesi bunun için hazır.

## 3. Sonuç testi — oluşurken ve tamamlandıktan sonra (+1 s, +1 g, +5 g), NDX geliştirme ve doğrulama

### Takeaway
Ön-kayıtlı 18 hücrenin hiçbiri hiçbir yönde P ≥ 0,975'e ulaşmadı (0/18 aşağı, 0/18 yukarı): yapı ne "tepe → aşağı devam"ı ne de
"düşüş sonrası tabandan fazla toparlanma"yı öngörüyor; NDX nokta tahminleri hafif pozitif ama yarılarda tutarsız ve anlamsız.

### Cited Findings
- NDX K1 oluşum (n = 36): eşli fark +1 s +6,8 bp (P(>0) 0,88), +1 g +23,2 bp (0,76; medyan +58,5; yarılar −18,6 / +60,5), +5 g +26,1 bp
  (0,68; yarılar −6,8 / +55,5); plasebo yüzdeliği %91 / %82 / %66 — [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- NDX K1 tamamlanma (n = 14; +5 g'de 13): +1 s +8,7 (P(>0) 0,968), +1 g +52,4 (0,82), +5 g +64,6 (0,82; olayların %38'i negatif) —
  [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- Koşulsuz taban (tüm geliştirme günleri): +1 s −0,02 bp, +1 g +7,2 bp, +5 g +36,3 bp; K1 oluşum ham getirisi +5,8 / +20,6 / +22,4 bp —
  [02_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_stdout.txt)
- K2 oluşum (n = 16): +1 g +75 bp (P(>0) 0,96, plasebo %98), +5 g +138 bp (0,92) — n < 20, ölçüt dışı; K2 tamamlanma 4 olay.
  K3 oluşum (46): +1 s +4,2, +1 g +13,3, +5 g −40,8 (P(<0) 0,73); K3 tamamlanma (20): +8,5 (P(>0) 0,94), +32,6 (0,76), +12,2 (0,56) —
  [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- Aile özeti: 18 hücre, P(fark<0) ≥ 0,975 → 0, P(fark>0) ≥ 0,975 → 0, geçen hücre yok; NDX nokta tahminlerinin 15/18'i pozitif —
  [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)
- Olay düzeyi (E6): K1 oluşumun en kötü olayları 2018-02-02 (+5 g fark −547 bp), 2018-03-21 (−618), 2019-08-02 (+1 g −572); en iyileri
  2021-12-20 (+5 g +642), 2024-10-31 (+547), 2020-01-31 (+517) — [02_olaylar.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_olaylar.csv)
- Gün düzeyi (tüm yanan günler, E6 uyarılı): NDX K1 82 gün, +5 g eşli +69,7 bp (P(>0) 0,93) —
  [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- "Oluşurken" yol: K1 oluşumdan bir sonraki tamamlanmaya (14 bölüm) medyan 4,5 gün, ortalama −103 bp, medyan −97 bp, %57 negatif
  (tanım gereği kısmen mekanik: tamamlanma ≥ 2 gün dipte kalmayı gerektiriyor) — [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)
- Aile dışı duyarlılık: K1-lit tamamlanma +1 g +33,5 bp, P(>0) 0,99, yarılar +16 / +49, n = 46, %67 pozitif (temel ölçütü geçiyor; Bonferroni
  0,9986 altında; DAX'ta +11 bp, P 0,73; +5 g yarıları +178 / −26). W = 12 K1 oluşum +1 g +48 bp P(>0) 0,97 (DAX −10); W = 6 K1 tamamlanma
  +1 g −34 bp (P(<0) 0,86) — [03_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/03_stdout.txt);
  [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- Doğrulama 2025-12-01 → 2026-10-02 (şablon penceresi/ufkuyla çakışanlar hariç): NDX K1 6 oluşum (2025-12-15, 2026-01-20, 02-04, 03-20, 06-05,
  06-26), +1 g ort. eşli fark +86 bp, +5 g +109 bp (n = 5); 1 tamamlanma (2026-02-06: +1 g +117, +5 g −36). MDE₈₀: +1 s 43 bp, +1 g 223 bp,
  +5 g 397 bp → güç yok — [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)

### Inferences
- Kural, düşüşü sonuç öncesi özellik olarak içerdiği için eşli taban (aynı 9 günlük getiri × oynaklık ondalığı) "düştü" bilgisini
  zaten kontrol ediyor; yapının buna ek bir şey taşımadığı görülüyor. Bu, şekil-benzerliği hattının (ME-02…ME-08) sonucuyla aynı —
  sonuç tanım yönteminden (şekil mesafesi vs yorumlanabilir kural) bağımsız.
- NDX'te kısa ufuk nokta tahminlerinin pozitif eğilimi meta-ders 2 ("korku döner") / GR-01 yönüyle uyumlu ama eşli tabanın üstünde
  anlamlı değil; K1-lit +1 g sonucu, test edilen ~24 hücre × 2 yönde beklenen ~1,2 tesadüfi temel geçişle uyumlu.
- Eşli taban 100 hücreli (hücre başına ~22 gün) → hücre ortalamasının kendi standart hatası +5 g'de ~40–70 bp; bootstrap bunu içermiyor
  (P'ler hafif iyimser) — sonuç zaten negatif olduğundan kararı değiştirmez.

### Gaps
- +15 dakika ufku sınanmadı (1h veri).
- Tamamlanma hücreleri K1/K2'de ≥ 20 olaya ulaşmadığından tamamlanma için "kanıt yok" ile "güç yok" ayrımı yapılamıyor (K3: 20 olay, yine anlamsız).
- Doğrulama döneminde yeterli olay yok; holdout sonuç taşımıyor.

## 4. Bağımsız piyasa: DAX (2020-01 sonrası veri, eksen düzeltilmiş 1h)

### Takeaway
Aynı kurallar DAX'ta da benzer sıklıkta yanıyor (K1 %4,7, yılda 5,2 bölüm) ama sonuç NDX ile tutarlı değil: +1 s / +1 g'de işaretler
çoğunlukla aynı (pozitif, anlamsız), +5 g'de ters (negatif) ve W seçimine göre işaret değiştiriyor.

### Cited Findings
- DAX geliştirme 2020-09-21 → 2025-11 (5,19 yıl): K1 %4,74 gün, 27 oluşum, 10 tamamlanma; K2 %0,23, 3 oluşum, 0 tamamlanma; K3 %6,32, 30 / 14 —
  [02_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_stdout.txt)
- DAX K1 oluşum: +1 s +5,6, +1 g +12,5 (P(>0) 0,73), +5 g −55,3 bp (P(<0) 0,84); tamamlanma: +1 s −0,6, +1 g +40,5 (P(>0) 0,97, n = 10),
  +5 g −184 bp (P(<0) 0,95, n = 9, plasebo %0,7) — [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- İşaret tutarlılığı: NDX–DAX aynı işaret 10/15 hücre (+1 s/+1 g 9/10, +5 g 1/5); DAX'ta 15 hücrenin 8'i pozitif —
  [02_hucreler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_hucreler.csv)
- DAX K1 tamamlanma +5 g, W = 12'de +148 bp (P(>0) 1,00, n = 10) — W = 9'daki −184 bp'nin tersi —
  [03_stdout.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/03_stdout.txt)
- DAX zaman ekseni: kış etiketleri 60 dk erken; düzeltilmiş kopya kullanıldı (`caprev_dax_recheck/data_fixed`) — [dogrulama/PROTOCOL.md](file:///Users/melihcanodacioglu/Desktop/panel/research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md)

### Inferences
- n ≈ 10'luk DAX tamamlanma hücrelerinde büyük ve işaret değiştiren +5 g sonuçları tek olaylara bağlı (örn. 2025-03-31: −1.198 bp) — gürültü.
- Bağımsız piyasa NDX'teki zayıf pozitif +5 g eğilimini doğrulamıyor; yapı için piyasalar arası taşınan bir sonuç yok.

### Gaps
- DAX'ta 2020 öncesi 1h seyrek → yarılar 2020-09→2022-12 / 2023→2025-11; K2 DAX'ta sınanamayacak kadar seyrek.

## 5. Bugün: kural son mevcut barda yanıyor mu?

### Takeaway
NDX'te hayır (son veri 2026-10-02 04:00 UTC'de fiyat 60 günlük tepede, pencere üst kısmında); DAX'ta 2026-10-01 kapanışında K1
yanıyordu, son barda sınırın hemen üstünde söndü. Tarihsel karşılık yön bilgisi taşımadığından bunun işlem anlamı yok.

### Cited Findings
- NDX son sorgu günü 2026-10-01 20:00 UTC kapanış 30.527,1: pos 0,71, net +2,53σ, tepeye uzaklık 0 (60 günlük tepede), oynaklık oranı 0,82,
  6 salınım → K1/K2/K3/K1-lit hepsi YANMIYOR; son bar 2026-10-02 04:00 (30.673,6) aynı. NDX'te K1'in son yandığı gün 2026-08-20 (= T3) —
  [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)
- DAX 2026-10-01 19:00 UTC (24.974,5): pos 0,14, net −1,69σ, 60 günlük tepenin %3,0 altı, oynaklık oranı 1,06, 8 salınım, 3 alçalan tepe →
  K1 ve K3 YANIYOR (K2 hayır); son bar 2026-10-02 04:00 (25.070,6) pos 0,24 → K1 sönük, K1-lit yanıyor —
  [02_sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/kural/results/02_sonuc.json)

### Inferences
- "Bugün" = son mevcut veri; gerçek tarih 2026-10-19 → 17 günlük veri boşluğu var. Güncel durum için veri yenilenmeli.

### Gaps
- 2026-10-02 sonrası veri yerelde yok; canlı/güncel değerlendirme yapılamadı.
