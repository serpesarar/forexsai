# MK-04 / R0B_G1 "ATLA" bayraklarının doğrulama sınaması — ÖN KAYIT

**Yazıldı: 2026-10-16 04:31 UTC.** Bu klasörde hiçbir sonuç hesaplanmadan, yalnız diğer üç araştırmacının
notları (`fiyat_anatomisi.md`, `makro_haber_baglami.md`, `erken_sinyal_testi.md`) ve kodları okunduktan sonra yazıldı.
Sonuçtan sonra DEĞİŞTİRİLMEZ; sapma olursa §9'a tarihli ek yazılır.

## 0. Dürüstlük beyanı
- İki bayrak (S1, S2) ve kuyruk maddesi (S3) aynı Duka 2008-01→2026-06-16 verisinde, ~54 + 18 (+2 post-hoc) özellik
  taramasından SEÇİLDİ. Bu örneklemdeki büyüklükleri bu yüzden yanlı (kazananın laneti). Bu çalışma onları yeniden
  ayarlamaz; yalnız (a) aramanın tamamını hesaba katan seçim düzeltmesi, (b) plasebo, (c) ileri veri ile sınar.
- İleri kanıt (Duka uzatması 2026-06-17→09-30 ve broker 1m kasası 06-17→10-14) AYNI takvim dönemidir, iki ayrı fiyat
  beslemesi. Bağımsız iki gözlem sayılmaz; birincil = broker (gerçek icra beslemesi), Duka uzatması tutarlılık.
- Önceki çalışmalardan bilinen: S1'in Duka uzatmasında TERS döndüğü (+0,181 vs +0,016, n=56) zaten raporlandı. Bu
  yüzden S1 için C4 sonucunu önceden kısmen biliyoruz; bu beyan edilir.

## 1. Kural ve veri (değişmez)
R0B_G1: H1 high ≥ önceki 20 H1 high → sonraki H1 açılışında BUY (+$0,12), SL = 1,5×ATR14(H1), TP yok, 20 H1 bar
(veya >3 saat boşluk öncesi son bar) zaman çıkışı, aynı anda tek pozisyon. `mekanik/` modülleri SALT-OKUNUR import.
Ana küme: `run_main.load_main()` (END_MAIN=2026-06-17) → 12.403 olay, tek-poz n=3.664, +290,5R beklenir (mutabakat şart).

## 2. Bayrak tanımları (araştırmacıların tanımı AYNEN; eşik yeniden ayarlanmaz)
- **S1 seri kırılım** (anatomi `build.py` `xa_brk_density24`): sinyal barı s için, [s−24, s−1] aralığındaki R0 olay
  barı sayısı (olay listesi `events(d,"R0",+1).sig`, sinyal barı HARİÇ, yalnız kapanmış barlar). **ATLA: ≥2.**
  Komşuluk (yalnız sağlamlık): ≥1, ≥3.
- **S2 önceki gün rallisi** (makro `04_features.py` `F_gprev_up1`): G = Duka H1 kapanışlarının UTC takvim günü son
  kapanışı (Cmt/Paz günleri dahil, olduğu gibi); giriş barının UTC gününden ÖNCEKİ son G günü g1 ve ondan önceki g2;
  gprev = g1/g2 − 1. **ATLA: gprev > +%1,00.** Komşuluk: > %0,75, > %1,25. (g1 giriş gününden önce kapanmış →
  sızıntı yok; makro kodu `add_feats` doğrudan import edilir.)
- **S3 FOMC tutma penceresinde** (makro `07_event_windows.py`): planlı FOMC açıklama anı ∈ [giriş, giriş+20 saat).
  YALNIZ KUYRUK maddesi: istatistik P(R≥3) farkı; filtre olarak önerilmez (ortalama-R farkı zaten CI sıfırı içeriyordu).
  Takvim makro `out/calendar.csv`; ileri dönem için 2026-07-29 ve 2026-09-16 FOMC (18:00 UTC) elle eklenir.

## 3. Ana istatistik ve seçim düzeltmesi (C1)
- İstatistik: tek-poz taban kümesinde d = ortR(bayrak) − ortR(¬bayrak). (S3 için ayrıca d3 = P(R≥3) farkı.)
- Boş: sonuç dizisi R (giriş sırasında) **yıl içinde dairesel kaydırılır** (erken_sinyal `circ_shift` ile aynı),
  bayraklar yerinde kalır → otokorelasyon, yıl karışımı, bayrak kümelenmesi korunur. 5.000 tekrar.
- **Aile (aramanın yeniden kurulumu):** her tekrarda aşağıdaki TÜM bayrakların d'si yeniden hesaplanır;
  z = (d − boş ort)/boş sd; **max |z|** (iki yönlü — araştırmacılar yönü sonradan seçti) dağılımı → p_sel.
  (a) anatomi: 33 ex-ante `xa_` sürekli/ikili özellik → sürekliler için Q1 (alt beşte bir) ve Q5 (üst beşte bir)
      bayrakları (tam örneklem beşli sınırları, anatomi beşli taramasının aynısı), ikililer için =1; + Asya/Londra/NY
      seans, Pzt/Cum; + `extra.py` 8 aday dilim (S1 dahil). (b) makro: 18 `F_` özelliği + FOMC/CPI/NFP/JH pencereleri
      + post-hoc tatil/tatil-sonrası + post-hoc düşük gvol (≤0,73). (c) erken_sinyal: F1–F10 (F9 eşiği params.json).
  Tekrarlanan/eşdeğer bayraklar bırakılır (max'ı yükseltmez, yalnız korelasyon). Aile boyutu raporlanır.
- Ayrıca tek yönlü (yalnız negatif, "atla" yönü) max-z p ve Holm (aile içinde) raporlanır.
- **C1 geçer: iki yönlü p_sel ≤ 0,10.**

## 4. Plasebo (C2) — P1-F
Her kural işlemi için aynı yıl × aynı UTC saati × AYNI bayrak durumundaki tüm geçerli H1 barlarından 40 rastgele BUY
(aynı geometri, $0,12) → olay başına plasebo ortalaması P. exc = R − P. DiD = ort(exc|bayrak) − ort(exc|¬bayrak);
gün-blok bootstrap 4.000. Ayrıca rastgele BUY'larda bayrağın kendi farkı (aynı yıl×saat ağırlıklı) raporlanır.
- **C2 geçer: DiD < 0 ve P(DiD<0) ≥ 0,90.** Geçmezse ama ham etki varsa etiket: "piyasa geneli sürüklenme etkisi"
  (ör. "+%1 günden sonra altın ortalamaya döner"); bu etiket verdikti en çok B ile sınırlar.

## 5. Çağ kararlılığı (C3)
Çağlar: 2008-12, 2013-16, 2017-20, 2021-26/06. Her çağda d ve her biri çıkarılınca kalan d.
- **C3 geçer: d<0 en az 3/4 çağda VE dört "bir çağ hariç" d'nin hepsi <0.**

## 6. İleri kanıt (C4)
(i) Duka 2026-06-17→09-30: veriyi 2026-10-01'e kadar yükle, tek-pozisyonu TÜM seri üstünde yürüt, sinyali ≥06-17
olanları al. (ii) Broker 1m 06-17→10-14: erken_sinyal `02_holdout.py` yöntemi (Duka geçmişi + broker H1 eki; sinyal
H1'den, yol 1m). Bayraklar aynı tanımla eklenmiş seride hesaplanır.
- **C4 geçer: broker kasasında d ≤ 0 (yalnız işaret; n küçük).** Duka uzatması tutarlılık için raporlanır.

## 7. Pratik etki (C5) — filtre olarak yeniden yürütme
Bayraklı OLAYLAR atlanır, tek-pozisyon tüm olaylarda yeniden yürütülür (atlanan olay pozisyon kilidi oluşturmaz).
Ölçüler (taban ve her filtre): işlem/hafta, ortR, toplam R, maks. düşüş (R), pozitif hafta %, en iyi 20 günün R payı,
en iyi 20 gün hariç ortR, R/hafta (takvim haftası, işlemsiz hafta = 0), haftalık Sharpe.
Boş: (R, süre) yıl-içi dairesel kaydırma + aynı filtre + yeniden yürütme, 2.000 tekrar → ortR artışının p'si.
- **C5 geçer: ortR artar VE boş p ≤ 0,10 VE R/hafta ≥ taban VE maks. düşüş tabandan kötü değil.**
- Ayrıca soru: filtre en iyi günlere bağımlılığı AZALTIYOR mu (top-20 payı, hariç ortR)?

## 8. Verdikt şeması (her bayrak için, ön tanımlı)
- **A**: C1–C5 hepsi geçer.
- **B**: C1 ve C3 geçer, {C2, C4, C5}'ten en çok biri düşer. C2 düşerse "B (piyasa geneli etki)".
- **C**: C1 düşer ama p_sel ≤ 0,50 ve C3 geçer; VEYA C1 geçer ama {C2, C4, C5}'ten ≥2'si düşer → yalnız gölge kaydı.
- **RED**: diğer tüm durumlar (ör. p_sel > 0,50, ya da C1 ve C3 birlikte düşer).
- **S3 (kuyruk)**: C1-kuyruk = aile P(R≥3) farklarında max|z| p_sel ≤ 0,10; C2-kuyruk = P1-F DiD (P(R≥3) üzerinden) > 0,
  P ≥ 0,90; C3 = 4 çağın ≥3'ünde P3 farkı > 0. Giriş filtresi DEĞİL; en iyi ihtimalle "çıkış ayarı adayı" (C).
- **Birleşik (S1 ∨ S2)**: yalnız ikincil, C5 ölçüleri raporlanır; verdikt verilmez.

## 9. Sapmalar
- 2026-10-16 04:37 UTC (aile kurulumu sırasında, sonuç tablosu okunmadan önce kodlandı): aileye anatomi `placebo_feat.py`
  etkileşim dilimi "tekil ∧ ATH≤%2" de eklendi (8 değil 9 aday dilim) — aramanın parçasıydı, aileyi yalnız büyütür
  (daha muhafazakâr). Birebir aynı/tümleyen bayraklar ayıklandı (erken F1 bir anatomi bayrağıyla özdeş) → K = 105
  (anatomi 74, makro 22, erken_sinyal 9). Anatomi gün-düzeyi 54 özelliğin ex-post olanları (xp_) ve gün-düzeyi AUC
  istatistiği aileye girmedi: ex-post özellikler filtre olamaz; istatistik türü farklı.
- C5'in boş p'si keşif verisinde hesaplanır (bayrak bu veride seçildi) → seçim düzeltmeli DEĞİL; yalnız C1 düzeltir.
