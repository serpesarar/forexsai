# (f) "Kapanış baskısı dönüşü" ipucunun tek seferlik doğrulaması — NDX holdout + DAX + plasebo (2026-10-13/14)

Kapsam: yalnız yerel hesaplama. Web araması bu oturumda kullanılamadı (oturum sınırı), bu yüzden dış kaynak alıntısı yok;
her sayı yerel dosyaya bağlı. Klasör: `research/mum_derin_tarama_20261013/dogrulama/` (ön-kayıt `PROTOCOL.md`, çekirdek
`dv_core.py`, hazırlık `dv_0_hazirlik.py`, sınama `dv_1_test.py`, çıktılar `results/`). Git commit yok; canlı sisteme dokunulmadı.

## Soru 1 — Dondurulmuş tanım ve geçme ölçütleri (sınama verisine bakmadan)

### Takeaway
Tanım keşif kodundan (`capali_ek.py`, tf = 1h) birebir alındı ve aynı kodla keşif sayıları 1e-6 hassasiyetle yeniden üretildi
(n = 2.334; %60,75 / %55,21; +13,61 / +0,50 puan). Eşikler keşif etkisinin yarısı: gece ortalaması farkı ≥ 0,043 yüzde puanı,
yükseliş oranı farkı ≥ 2,77 puan, P ≥ 0,95. Sınama öncesi güç hesabı NDX holdout'unun (205 gece) bu etkiyi yakalayamayacağını
zaten gösterdi (MDE₈₀ = keşif etkisinin 3,2 katı).

### Cited Findings
- Dondurulmuş tanım: son saat = 15:00 → 16:00 NY 1h barlarının kapanıştan kapanışa getirisi (`rl < 0` aşağı, `rl = 0` düşer);
  gece = 16:00 kapanışı → sonraki işlem gününün 09:00 NY bar kapanışı (puan ve %); erken kapanış günü (Şükran sonrası Cuma,
  24 Aralık, 3 Temmuz) ve ertesi günü dışarıda; 5 ardışık işlem günlük blok bootstrap, B = 10.000, tek yönlü — [PROTOCOL.md §1](research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md), [capali_ek.py](research/mum_derin_tarama_20261013/capali/capali_ek.py)
- Keşif yeniden üretimi birebir; B = 10.000 ile P(puan farkı > 0) 0,9987, P(% farkı) 0,9963, P(yükseliş farkı) 0,9959 — [results/hazirlik_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik_stdout.txt)
- Keşif etkisi yüzde cinsinden: aşağı-son-saat sonrası gece +0,1026 %, yukarı sonrası +0,0168 % → fark 0,0859 yüzde puanı;
  gece % SD'si 0,794 → standartlaştırılmış d_E = 0,108. Çağlar: 2016–2020 +0,026 % / +3,6 puan; 2021–2025 +0,145 % / +7,6 puan.
  Keşif koşulsuz gece yükseliş oranı %57,9 — [results/hazirlik.json](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik.json)
- Karar kuralı: GEÇER = P ≥ 0,95 ∧ fark ≥ yarı etki; ÇÜRÜTÜLDÜ = geçmez ∧ bootstrap %95'lik üst değeri < yarı etki;
  aksi SONUÇSUZ. Birincil ölçüt % farkı (puan, 2016'da ~4.500 → 2026'da ~25.000 fiyat düzeyi yüzünden karşılaştırılamaz);
  yükseliş oranı eş-birincil ama verdikti yükseltemez. Hipotez TEKRARLANDI ⇔ NDX birleşik **ve** DAX birincilde GEÇER — [PROTOCOL.md §3](research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md)
- Sınama öncesi kayıtlı değişiklikler (sonuç görülmeden): takvim = NDXCASH_close dolu günler (O/H/L 2026-07-28'de bitiyor;
  07-28'e kadar iki tanım birebir aynı gün kümesi); QQQ 07-28'de bittiği için Q-hold 07-27'de bitiyor; DAX için 30m (16:30 Berlin
  1h ızgarasında kurulamıyor) — [PROTOCOL.md §4, §8.4](research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md)
- A-priori MDE₈₀ (keşif bootstrap SD'sinden ölçekli): NDX birleşik 205 gece → 0,27 yüzde puanı (keşif etkisinin 3,2 katı,
  eşiğin 6,3 katı), yükseliş oranında 17,7 puan; DAX 1.403 gece → d 0,130 (d_E'nin 1,2 katı) — [PROTOCOL.md §8.5](research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md)
- Hizalama denetimleri (getiri hesaplamadan): 15m→1h toplamı `long_1h` ile iki haftada %100 eşleşme; 2026-07-15 sonrası 15m,
  bağımsız 1m kaynağıyla kayma 0'da %99,3 eşleşme (±15/±60 dk'da ≤ %8); 16:00 NY kapanışı NDXCASH kapanışıyla her holdout ve
  uzatma ayında kayma 0'da en kararlı; DAX eksen düzeltmesi sonrası Xetra açılışı (09:00 Berlin) yıl × DST sınıfı gruplarının
  17/18'inde en geniş 30m dilim (düzeltmesiz 11/18) — [results/hazirlik_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik_stdout.txt)

### Inferences
- Holdout'u bu ipucuna harcamak, sınamadan önce bilinen bir güç sorunuyla yapıldı: 205 gecede ancak keşif etkisinin üç katı
  bir fark güvenle görülebilirdi. Bu yüzden NDX tarafında "SONUÇSUZ" en olası sonuçtu; bilgi asıl DAX'tan gelecekti.
- Keşifte kullanılan `long_1h` dosyasının 2017-11 → 2018-02 eksen kusuru sonucu değiştirmiyor (düzeltmeli +0,0862 % / +5,24 puan).

### Gaps
- Xetra tatil takvimi kural tabanlı (takvim kitaplığı yok, web kapalı); Pfingstmontag'ın her yıl işlem günü olduğu ve 24/31
  Aralık'ın kapalı olduğu varsayıldı, doğrulanamadı.
- Gece finansmanı (swap) hesaba katılmadı; yalnız başka bir ön-kayıttaki kalibrasyon not edildi (Soru 5).

## Soru 2 — Sınama 1: NDX holdout (≥ 2025-12-01) + 15m→1h uzatma

### Takeaway
Yön keşifle aynı ve büyüklük keşiften büyük (aşağı-son-saat sonrası gece %60,8 yükseldi, yukarı sonrası %48,1), ama ön-kayıtlı
birincil ölçüt geçmedi (P = 0,906 < 0,95) → **SONUÇSUZ**. Yükseliş oranı eş-birincili geçti (+12,7 puan, P 0,967). Güç
düşük; bu sonuç ne doğrulama ne çürütme.

### Cited Findings
Tablo (gece = 16:00 → ertesi 09:00 NY; Δ = aşağı − yukarı) — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json), [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)

| Set | gece (aşağı) | yükseliş aşağı / yukarı / koşulsuz | gece % aşağı / yukarı | Δ% (P, MDE₈₀) | Δyükseliş (P) | Δpuan (P) | verdikt % / yükseliş |
|---|---|---|---|---|---|---|---|
| N-H holdout 2025-12-02 → 2026-07-13 | 150 (66) | %59,1 / %50,0 / %54,0 | +0,113 / +0,045 | +0,068 (0,76; 0,26) | +9,1 (0,90) | +17,5 (0,76) | SONUÇSUZ / SONUÇSUZ |
| N-X uzatma 2026-07-14 → 09-29 | 55 (31) | %64,5 / %41,7 / %54,5 | +0,196 / −0,102 | +0,298 (0,87; 0,66) | +22,8 (0,90) | +85,5 (0,87) | SONUÇSUZ / SONUÇSUZ |
| **N-HX birleşik** | **205 (97)** | **%60,8 / %48,1 / %54,1** | **+0,139 / +0,012** | **+0,127 (0,906; 0,25)** | **+12,7 (0,967)** | **+35,0 (0,905)** | **SONUÇSUZ / GEÇER** |

- N-HX ay bazında Δ% 10 ayın 9'unda pozitif (yalnız 2026-03 −0,085); en büyük 2026-07 +0,46, 2026-02 +0,36 — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- Bootstrap Δ% %90 aralığı [−0,035; +0,293]: hem sıfırı hem keşif etkisini (0,086) hem yarısını (0,043) içeriyor → ÇÜRÜTÜLDÜ
  koşulu (üst sınır < 0,043) sağlanmıyor, GEÇER koşulu da (P ≥ 0,95) — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json)
- Gerçekleşen MDE₈₀ 0,246 yüzde puanı (a-priori 0,27 ile tutarlı); gecelik % SD 0,877 (keşifte 0,794) — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json)

### Inferences
- Nokta tahmini keşiften 1,5 kat büyük ve aylara yayılı; ipucu NDX'te "ölmedi". Ama yükseliş oranı GEÇER'i tek başına anlamlı
  değil: aynı ölçüt plasebo saatinde de büyük çıkıyor (Soru 4) ve ön-kayıt gereği verdikti yükseltemez.
- 2026'nın yüksek oynaklıklı dönemi (Şubat, Temmuz) farkın büyük kısmını taşıyor — keşifteki 2021–2025 yığılmasıyla aynı
  rejim-bağımlılık şüphesi (defter §1 E17/E23) geçerli.

### Gaps
- Holdout tek bir 10 aylık dönem; bağımsız bir NDX dönemi daha (ör. 2026-10 sonrası ileri gölge) olmadan güç sorunu çözülemez.

## Soru 3 — Sınama 2: bağımsız piyasalar (DAX Xetra; vekiller)

### Takeaway
Bağımsız piyasada iz yok: DAX'ta Xetra son saati (16:30 → 17:30 Berlin) aşağı/yukarı kapanınca ertesi 09:00'a gece getirisi
neredeyse aynı (Δ% +0,001, d = 0,002, P 0,51; 1.403 gece) → ön-kayıt kuralıyla **SONUÇSUZ**, ama nokta tahmini sıfır ve tam
keşif boyutundaki etki tek yönlü %95 üst sınırın dışında. DAX 1h vekili negatif (ÇÜRÜTÜLDÜ, ikincil). QQQ günlük vekili zaman
olarak bağımsız tek dilimde ters işaretli, holdout dilimde NDX ile aynı yönde.

### Cited Findings
- **D-30 (birincil, eksen düzeltmeli 30m, 2021-03-18 → 2026-09-30):** n = 1.403 (aşağı 659); gece yükselişi aşağı sonrası
  %57,2, yukarı sonrası %55,4, koşulsuz %56,2; gece % +0,0267 vs +0,0255 → Δ% +0,0012 (P 0,506; %90 aralık [−0,066; +0,072];
  eşik 0,0388 = 0,0541 × SD 0,717 %; MDE₈₀ 0,104); Δyükseliş +1,8 puan (P 0,75); Δpuan +1,6 (P 0,57) — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json)
- D-30 kronolojik yarılar Δ% −0,021 / +0,022; yıllar 2021 +0,042, 2022 −0,046, 2023 −0,023, 2024 −0,096, 2025 +0,076, 2026 +0,095
  (3/6 pozitif) — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- Keşif boyutundaki etkinin DAX karşılığı d_E × SD = 0,0775 %; D-30 bootstrap %95'lik üst değeri 0,0717 → tam boyutlu etki
  dışlanıyor, yarı boyutlu (0,0388) dışlanmıyor — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json)
- **D-1h vekil** (kapanışı içeren 17:00 → 18:00 Berlin saati, gece 18:00 → 09:00; 2020-01-02 → 2026-09-30): n = 1.712,
  Δ% −0,031 (P 0,24; %95'lik üst 0,041 < eşik 0,045 → ÇÜRÜTÜLDÜ), Δyükseliş −0,6 puan; 30m'nin kapsamadığı 2020-01 → 2021-03-16
  alt dönemi (n = 306) Δ% −0,172, Δyükseliş −12,0 puan — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- **QQQ günlük vekil** (CLV < 0,5 = "aşağı kapanış"; gece = kapanış → ertesi açılış; karar yok): Q-pre 2015-01 → 2016-05
  (keşiften önce, n = 342) Δ% −0,072 (P 0,22); Q-ovl 2016-05 → 2025-11 (keşifle çakışık, n = 2.343) +0,040 (P 0,87);
  Q-hold 2025-12 → 2026-07-27 (n = 160) +0,213 (P 0,976), Δyükseliş +7,7 (P 0,86) — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- DAX eksen kusuru (NY standart saatinde etiket 60 dk erken) paralel çalışmada bulunmuştu; bu sınama aynı düzeltmeyi kendi
  yükleyicisinde uyguladı ve doğruladı — [caprev_dax_recheck/fix_data.py](research/nasdaq_derin_20261013/caprev_dax_recheck/fix_data.py), [results/hazirlik_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik_stdout.txt)

### Inferences
- "Kapanış akışı bilgisiz iter, gece geri döner" mekanizması gerçekse ve endekse özgü değilse DAX'ta da görülmeliydi; DAX'ın gücü
  NDX holdout'unun ~2,4 katı (MDE 0,104 vs 0,246 yüzde puanı) ve sonuç sıfır. Mekanizma ya NDX/ABD'ye özgü (ör. ABD kaldıraçlı
  ETF yeniden dengelemesi; burada ölçülmedi) ya da keşif bulgusu NDX'e özgü bir tesadüf/rejim etkisi.
- QQQ vekilinin holdout'ta NDX ile aynı yönü göstermesi bağımsız teyit değil: aynı piyasa, aynı geceler; zaman olarak bağımsız
  tek dilim (2015–16) ters işaretli. Vekil tanımı (gün içi kapanış konumu) son saatle aynı şey değil.
- DAX 1h vekili mekanizmayı iyi temsil etmiyor (kapanıştan sonra 30 dk içeriyor); ÇÜRÜTÜLDÜ etiketi ikincil ve birincil 30m
  sonucuyla birlikte okunmalı.

### Gaps
- Bağımsız ABD piyasası (ör. S&P 500 vadelisi/SPY) gün içi verisi yerelde yok; SPX günlük açılışı bayat-açılış sorunu taşıdığı için kullanılmadı.
- QQQ verisinin temettü ayarlı olup olmadığı doğrulanmadı (yılda ~4 gece etkilenir).

## Soru 4 — Plasebo: kapanış olmayan saat (11:00 → 12:00)

### Takeaway
Holdout'ta etki kapanışa özgü değil: öğlen saatinin (bitişi 12:00 NY) işareti de aynı geceyi aynı yönde ayırıyor (Δ% +0,078,
Δyükseliş +5,9 puan); son saatin plaseboyu geçme olasılığı yalnız 0,61. Keşifte ise plasebo ters işaretliydi (−0,034 %, eşli P 0,994).
DAX'ta ikisi de sıfır civarı.

### Cited Findings
- N-HX plasebo (n = 205): Δ% +0,078 (P 0,74), Δyükseliş +5,9 (P 0,78), Δpuan +24,0; eşli P(son saat − plasebo > 0) = 0,61 →
  "kapanışa özgü" = hayır. N-H'de plasebo son saatten büyük (+0,161 vs +0,068); N-X'te ters (−0,144 vs +0,298, eşli P 0,89) — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- Keşif (2016–2025, n = 2.329): plasebo Δ% −0,034 (P 0,14), Δyükseliş −2,8; eşli P 0,994 — [results/hazirlik.json](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik.json)
- D-30 plasebo (11→12 Berlin, n = 1.401): Δ% −0,016 (P 0,34), eşli P 0,60; D-1h plasebo −0,043 — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)

### Inferences
- Holdout'taki büyük farkın bir kısmı "gün içinde aşağı giden gün → gece toparlanma" türünden genel bir gün-içi/gece dönüşü olabilir
  (her gün-içi saatin işareti günün yönüyle ilişkili); keşifteki kapanışa özgüllük holdout'ta tekrarlanmadı. Bu, ipucunu
  "kapanış akışı" mekanizmasından uzaklaştırıyor.

### Gaps
- Tek bir plasebo saati ön-kayıtlıydı; saat-saat tam profil (her gün içi saat → gece) holdout'a ikinci bakış olacağı için yapılmadı.

## Soru 5 — Zamanlama bilgisi mi, işlenebilir yön mü? Gece hareketi vs 1,5 puan spread

### Takeaway
Keşifte saf zamanlama bilgisi (iki koşullu yükseliş oranı da %50'nin üstünde); holdout'ta yukarı-son-saat sonrası oran %48,1'e
düştü ama ortalama ≈ 0 (+0,012 %) → açığa satış spread sonrası negatif. Spread gece hareketinin yanında önemsiz (ort. mutlak gece
183 puan); belirleyici maliyet gece finansmanı. DAX'ta koşullu ve koşulsuz oranlar aynı (≈ %56) → yalnız gece sürüklenmesi var.

### Cited Findings
- Keşif: aşağı sonrası %60,8, yukarı sonrası %55,2, koşulsuz %57,9; ort. gece +6,9 puan koşulsuz, +13,6 aşağı sonrası — [results/hazirlik.json](research/mum_derin_tarama_20261013/dogrulama/results/hazirlik.json)
- N-HX: aşağı sonrası %60,8, yukarı sonrası %48,1, koşulsuz %54,1. Spread düşülmüş gecelik ort.: her gece AL +17,7 puan;
  yalnız aşağı-son-saat gecesi AL +36,2 puan (97 gece); yukarı-son-saat gecesi SAT −4,1 puan. Toplam: her gece AL +3.629 puan
  (205 gece) vs aşağı-sonrası AL +3.508 puan (97 gece). Ort. mutlak gece hareketi 183 puan — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- D-30: aşağı sonrası %57,2, yukarı %55,4, koşulsuz %56,2; spread sonrası her gece AL +3,8, aşağı-sonrası AL +4,6, yukarı-sonrası SAT
  −6,1 puan/gece; ort. mutlak gece 83 puan — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)
- Gece finansmanı referansı (bu sınamada hesaplanmadı): paralel ön-kayıt NAS100 2026 long swap'ını kutunun gerçek işleminden
  −5,03 puan/lot/gece (Cuma ×3) olarak kalibre etmiş — [nasdaq_derin_20261013/overnight/PROTOCOL.md §3](research/nasdaq_derin_20261013/overnight/PROTOCOL.md)
- QQQ sütunları dolar cinsinden (pay başına ~0,3–1,1 $ gece hareketi); 1,5 "puan" spread QQQ'ya uygulanamaz, oradaki işlem satırları anlamsız — [results/test_stdout.txt](research/mum_derin_tarama_20261013/dogrulama/results/test_stdout.txt)

### Inferences
- Holdout'ta zamanlama kuralı gece başına "her gece AL"ın iki katı getirdi ama gecelerin yarısında pozisyonsuz kalarak toplamda
  aynı yere vardı; swap (~7 puan/gece ortalama, hafta sonu dahil) her iki kuralı da düşürür, zamanlama kuralı daha az gece taşıdığı
  için swap'tan daha az etkilenir. Bu, işlem kartı (2. KURAL) olmadan bir kenar iddiası değildir; DAX sıfır sonucu ve kapanışa
  özgüllüğün kaybı kart açmayı gerekçelendirmiyor.

### Gaps
- Gerçek icra (09:00'da değil 09:30 açılışında çıkış, 16:00 kapanış müzayedesine yakın giriş) ve swap dahil net R ölçülmedi.

## Soru 6 — Sonuç ve kayıt

### Takeaway
Ön-kayıtlı hipotez verdikti **SONUÇSUZ** (NDX birleşik SONUÇSUZ, DAX SONUÇSUZ). Dürüst okuma: NDX'te yön ve büyüklük korunuyor
ama güç yetersiz ve etki holdout'ta kapanışa özgü değil; bağımsız piyasada (DAX) nokta tahmini sıfır. İpucu **aday değil**;
ek holdout harcanmamalı. Bulgular deftere (ME-04…ME-07, E27, E28) ve Evrim Paneli oturum notuna yazıldı.

### Cited Findings
- Hipotez verdikti: `{"N_HX": "SONUÇSUZ", "D_30": "SONUÇSUZ", "sonuc": "SONUÇSUZ"}` — [results/test_sonuc.json](research/mum_derin_tarama_20261013/dogrulama/results/test_sonuc.json)
- Sınama tek koşumda yapıldı; sonuç görüldükten sonra hiçbir tanım/eşik/dönem değişmedi (değişiklikler yalnız sınama öncesi,
  PROTOCOL §8.4) — [PROTOCOL.md](research/mum_derin_tarama_20261013/dogrulama/PROTOCOL.md)
- Defter satırları: §2.8'e ME-04 (harfiyen 10–50 mum ±%0,015), ME-05 (alternatif benzerlik aileleri), ME-06 (çapalı/olay fikirleri
  + MIM), ME-07 (bu doğrulama); §1'e E27 (taban ≈ %50 yazı-tura tuzağı) ve E28 (anlamlı-kötü sayısını da boşla kıyasla) — [docs/KAPI_KAYIT_DEFTERI.md](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- Yöntem dersi (ME-07 satırında): post-hoc bir ipucu için holdout açmadan önce güç hesabı yapılmalı; 200 gecelik bir pencerede
  %0,09'luk gece farkı görülemez. Bağımsız piyasa daha güçlü bir sınamadır ve burada belirleyici oldu.
- `literal_tanim.md`'nin önerdiği üçüncü kanıt hatası adayı (sabit-çağrılı zaman-kaydırma null'u alt-küme tabanını taklit etmez)
  görev tanımı gereği deftere eklenmedi; koordinatörün kararına bırakıldı.

### Gaps
- NDX'e özgü bir mekanizma (ABD kaldıraçlı ETF yeniden dengelemesinin 2020'lerdeki büyüklüğü) bu çalışmada ölçülmedi; yeniden
  açmak için bu yeni veri/gerekçe ve ileri (2026-10 sonrası) gölge dönemi gerekir.
