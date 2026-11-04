# NDX çapalı / koşullu mum eşleştirme — yapısal anlarda eşleştirme +15 dk / +1 s / +1 g yönü öngörüyor mu? (2026-10-13)

Kapsam: yerel veriyle hesaplamalı çalışma. Genel kayan pencere yerine yapısal anlara çapalanmış 6 fikir (a–f), toplam
**513 konfigürasyon** (fikir × TF × N × ölçek × K × ufuk), tek seferde, ön-kayıtla koşuldu. Holdout (≥ 2025-12-01 UTC)
yükleme anında kesildi; hiçbir sonuç penceresi bu sınırı geçmiyor (kod içinde `assert`).
Klasör: `research/mum_derin_tarama_20261013/capali/` (betikler + `PROTOCOL.md` + `results/`).

## Soru 1 — Her fikir × varyant × ufuk: isabet (taban ve plaseboya karşı), işaretli hareket, bootstrap, yarılar, bağımsız olay

### Takeaway
Hiçbir fikir ve hiçbir varyant aday ölçütlerinin tamamını geçmedi. Ölçütlerin yalnız biri hariç hepsini geçen tek konfigürasyon
(ilk yarım saat yolu analoğu → son yarım saat, 30m) seçim düzeltmesinde düşüyor (düzeltilmiş p = 0,70). Görülen "taban +2 puan"
farklarının çoğu modelin iyiliğinden değil, nedensel çoğunluk tabanının o dönemde %50'nin altına düşmesinden geliyor.
Yayımlanmış piyasa gün-içi momentumu (MIM) NDX CFD'de 2016–2025'te yok.

### Cited Findings
**Yöntem (ön-kayıt, sonuçlardan önce yazıldı)** — [PROTOCOL.md](../../research/mum_derin_tarama_20261013/capali/PROTOCOL.md)
- Ortak motor: sorgu anındaki özellik vektörüne Öklid uzaklığıyla K ∈ {20, 50} en yakın geçmiş olay; komşu yalnız sonucu sorgu
  anında kapanmışsa (`end_j ≤ t_q`); kütüphanede en az 100 olay (MIN_LIB); karar = komşuların yukarı payı > 0,5 → YUKARI,
  < 0,5 → AŞAĞI, = 0,5 → çekimser. Taban = aynı çapanın nedensel kütüphanesindeki koşulsuz yukarı oranı → hep-çoğunluk çağrısı.
  Plasebo = aynı kütüphaneden aynı sayıda rastgele komşu (kural tabanlılarda çağrı vektörü karıştırılır), 40 tekrar.
  Gün-blok bootstrap 5 işlem günü, B = 2000. Aday = bağımsız gün ≥ 200 ∧ fark ≥ +2,0 puan ∧ plasebo p ≤ 0,05 ∧ P ≥ 0,975 ∧
  iki yarı > 0 ∧ işaretli hareket > 1,5 puan ∧ seçim düzeltmesi p ≤ 0,05 — [PROTOCOL.md §2–3](../../research/mum_derin_tarama_20261013/capali/PROTOCOL.md)
- Veri (holdout öncesi): 5m Dukascopy 2025-01→11 (228 gün), 15m Pepperstone 2023-10→2025-11 (543 gün), 30m 2021-06→2025-11
  (1.110 gün), 1h 2016-05→2025-11 (2.390 gün), günlük NDX nakit 2015-01→2025-11 (2.744 gün). Her kaynakta en geniş ortalama
  bar aralığı 09:30 NY dilimine (1h'te 09:00/10:00 barlarına) düşüyor → saat ekseni doğru (E2/E4 kontrolü) —
  [capali_veri.py](../../research/mum_derin_tarama_20261013/capali/capali_veri.py)
- Sızıntı denetimi: veri 2025-06-02'de kesilip aile yeniden kurulduğunda, sonucu kesimden önce biten 271.461 olayın komşu
  kümeleri/kural çağrıları 509 konfigürasyonun hepsinde birebir aynı (fark 0) — [capali_sizinti_testi.py](../../research/mum_derin_tarama_20261013/capali/capali_sizinti_testi.py)
- Tüm 513 konfigürasyon tek tabloda (isabet, taban, plasebo, P, yarılar, hareket, t, düzeltilmiş p) — [results/aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)

**Fikir başına özet** (sütunlar 2–10 tüm konfigürasyonlar üzerinden sayım; son iki sütun yalnız yeterli olanlar, n_bağımsız ≥ 200) — [results/aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)

| Fikir | konfig | yeterli | fark ≥ 2 | plaseboyu geçen | P ≥ 0,975 | iki yarı + | hareket > 1,5 | seçim hariç hepsi | ADAY | en iyi fark (yeterli) | medyan fark (yeterli) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| (a) seans yolu | 164 | 100 | 23 | 26 | 0 | 16 | 78 | 0 | 0 | +4,24 | −1,28 |
| (b) gece yolu | 24 | 24 | 1 | 2 | 0 | 1 | 4 | 0 | 0 | +3,21 | −1,09 |
| (c) MIM + analog | 27 | 18 | 6 | 1 | 1 | 8 | 3 | 1 | 0 | +5,36 | +0,42 |
| (d) olay tetikli | 240 | 81 | 33 | 9 | 3 | 22 | 92 | 0 | 0 | +5,85 | −1,81 |
| (e) günlük şekil + boşluk | 16 | 16 | 0 | 3 | 0 | 0 | 14 | 0 | 0 | −0,32 | −2,07 |
| (f) kapanış baskısı dönüşü | 42 | 33 | 2 | 6 | 0 | 1 | 24 | 0 | 0 | +1,61 | −2,57 |
| **Toplam** | **513** | **272** | 65 | 47 | 4 | 48 | 215 | **1** | **0** | | |

**(a) Seans-çapalı gün yolu** (09:30 NY + N dk; özellik her bar H/L/C − 09:30 açılışı, ATR veya %; K 20/50) — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)
- 30m (2021–2025, ~860–930 gün), seansın kalanı (hROS) 12 konfig ortalaması: isabet %55,07 · taban %55,86 · plasebo %52,64 → plasebonun
  +2,4 puan üstü ama tabanın altı. En iyisi `a|30m|N60|pct|hROS|K50`: %57,56 vs %55,52 (+2,04), plasebo p = 0,024, P = 0,91,
  yarılar +3,65/+0,43, hareket +8,2 puan, n = 933 → P ve seçim düzeltmesi geçmiyor.
- 30m +1 g: en iyi `a|30m|N90|pct|h1d|K50` %55,84 vs %53,36 (+2,49), P = 0,92, ikinci yarı −1,08.
- 15m (2023-10→, ~375–400 gün): en iyi `a|15m|N60|atr|h60|K50` %51,12 vs taban %46,88 (+4,24) — ama plasebo %49,84 (p = 0,24),
  hareket −1,7 puan; fark, tabanın %50'nin altına düşmesinden.
- 5m (yalnız 2025): sorgu 85–104 → **yetersiz** (en iyi +8,4 puan, n = 95).
- Oy kovası (30m hROS K50, sonradan tanımsal): komşu yukarı payı 0,5–0,7 olan sorgularda (n ≈ 400–575) gerçekleşen yükseliş
  %49–60; < 0,4 kovasında %39–46 ama n = 5–31 → bilgi az sayıdaki uç sorgularda, ana kütle %50'nin üstünde kaldığı için "aşağı" çağrısı
  tabanı yenemiyor — [results/ek_tanimsal.json](../../research/mum_derin_tarama_20261013/capali/results/ek_tanimsal.json)

**(b) Gece yolu analoğu** (önceki 16:00 → 09:30 yolu, 8–9 saat noktası + gece yüksek/düşük) — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)
- 1h (2016–2025, ~1.850–2.070 gün): 09:00→10:00 isabet %49,1–50,4 vs taban %51,3–51,7; 09:00→11:00 %49,8–52,3 vs %50,9–51,9 (fark −1,2…+0,97).
- 30m: 8 konfigürasyonun hepsinde fark < 0. 15m'in en iyisi (`pct|o15|K50`, +3,21) tabanın %44,4'e düşmesinden; plasebonun altında (%47,6 vs %49,5).

**(c) Piyasa gün-içi momentumu (Gao, Han, Li & Zhou 2018) — aynen ve analog** — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv), [ek_tanimsal.json](../../research/mum_derin_tarama_20261013/capali/results/ek_tanimsal.json)
- Yayımlanmış tanım: r1 = önceki gün 16:00 kapanışı → 10:00; r12 = 15:00→15:30; r13 = 15:30→16:00 (tahmin edilen) — [Limkriangkrai, Chai & Zheng 2023, Pacific-Basin Finance Journal 80, 102086 (Gao vd. 2018'i izleyerek)](https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf)
- Yayımlanmış büyüklük: SPY 1996–2013 replikasyonunda r1 katsayısı 7,15 (×100 ölçekli), R² %1,7; r12 R² %0,9; ikisi birlikte %2,6 — [Limkriangkrai vd. 2023](https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf)
- Uygulamadaki varyant: r1 ve sondan bir önceki yarım saat aynı işaretliyse o yönde al/sat, VIX < 20 iken kapalı — [QuantRocket "first-last" örneği](https://www.quantrocket.com/codeload/first-last/first_last/Introduction.ipynb.html)
- Makale künyesi: Journal of Financial Economics 129 (2018) 394–414 — [WUSTL yayın sayfası (arama sonucu)](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)
- NDX'te kural aynen (c1 = işaret(r1)): 30m n = 987 → %48,94 vs taban %47,92 (+1,01), plasebo %50,05 (p = 0,78), P = 0,65, hareket −2,1 puan;
  1h (hedef son saat 15:00→16:00) n = 2.234 → %50,67 vs %50,81 (−0,13); 15m n = 427 → −1,87; 5m n = 77 yetersiz.
- c2 (r1 ∧ r12 aynı işaret): 30m %48,31 vs %49,62; 15m %46,12 vs %50,23. c4 (+ önceki gün VIX ≥ 20): 30m n = 197 (eşiğin altında)
  %51,78 vs %47,72 (+4,06, P = 0,74); 1h c4' n = 730 → +1,51 (P = 0,71).
- Regresyon biçimi (sonradan tanımsal, Newey-West gecikme 5): 30m β = −0,017 (t = −1,33, R² %0,28); 15m β = −0,020 (t = −1,07);
  5m β = −0,029 (t = −0,90); 1h son saat β = +0,045 (t = 1,25, R² %0,82; yarılar +0,098 (t 1,48) / −0,002 (t −0,12)).
- Analog c3 (boşluk + ilk yarım saatin barları → son yarım saat): `c|30m|c3_analog|pct|LH30|K50` n = 895 → %52,85 vs taban %47,49
  (+5,36), plasebo %49,38 (p = 0,024), P = 0,987, yarılar +1,57/+9,15, hareket +4,1 puan, t = 2,38 → **6/7 ölçüt; seçim düzeltmesi
  p = 0,70**. Aynı tanım başka TF'de tutmuyor: 15m +1,28 (P 0,62), 1h son saat −1,95, 5m 0,00.

**(d) Olay-tetikli eşleştirme** (E2 aralık ≥ 2×ATR14, E3 ≥ 3×ATR14, HI20/LO20 20-bar kapanış kırılımı — NY 10:00–15:30;
GAP |açılış − önceki kapanış| ≥ 0,5 günlük ATR; olay barı + m ∈ {1,3,5} bar) — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)
- 81 yeterli konfigürasyonun en iyisi `d|15m|E2|m5|p15|K50` (306 gün): %53,19 vs %47,34 (+5,85), plasebo p = 0,098, P = 0,975,
  hareket 1,8 puan, düzeltilmiş p = 0,995 → plasebo ve seçim geçmiyor. `d|30m|LO20|m3|p60|K50` +4,93 ama isabet %49,49 ≈ plasebo %49,43.
- En yüksek P'ler (0,994/0,998) `d|5m|HI20|m3|p15` (K20/K50, %57,7/%55,7 vs %47,6/%46,8) yalnız 2025, 129–130 bağımsız gün → **yetersiz**;
  aynı tip 15m'de (2023-10→) ortalama fark −1,51.
- E3 ve GAP çoğunlukla yetersiz: 15m E3 ~43 gün, GAP ~29 gün; 30m E3 190–220, GAP ~125; 5m E3/GAP sorgu 0.

**(e) Önceki gün şekli + açılış boşluğu (günlük nakit 2015–2025)** — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)
- 16 konfig, 2.196–2.464 bağımsız gün: isabet %51,7–55,2 vs taban %53,6–57,3 → hepsinde fark < 0 (en iyi −0,32); plasebo %51,3–54,9.

**(f) Kendi fikrim — kapanış baskısının dönüşü** (mekanizma sınamadan önce yazıldı: LETF yeniden dengeleme/MOC/kapanışa endeksli
akış son yarım saati bilgisiz iter, likidite talebi bitince geri döner; kural = −işaret(son yarım saat; 1h'te son saat)) — [aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv), [ek_tanimsal.json](../../research/mum_derin_tarama_20261013/capali/results/ek_tanimsal.json)
- Ön-kayıtlı kural tabanı yenemiyor: 1h gece (16:00 → ertesi 09:00) n = 2.237 → %52,93 vs hep-yukarı %58,02 (−5,10); kapanış sonrası saat
  (16:00→17:00) %49,78 vs %54,89. Çağrı plasebodan iyi (%50,00, p = 0,02) — yani yönde bilgi var ama gece sürüklenmesi daha güçlü.
- Tanımsal (sonradan): 1h 2016–2025 n = 2.334 — son saat AŞAĞI kapanınca gece yükseliş %60,8, ort. +13,6 puan; YUKARI kapanınca %55,2,
  +0,5 puan (fark için blok-bootstrap P = 0,998). 2016–2020: %62,1 vs %58,5 (+8,1 vs +5,7 puan, P = 0,74); 2021–2025: %59,6 vs %52,0
  (+18,4 vs −4,6 puan, P = 1,000); yıllara göre ortalama fark 10 yılın 8'inde pozitif (2018, 2019 negatif). 30m/15m/5m (hepsi 2021–25
  içinde, bağımsız değil) aynı işaret.

### Inferences
- **Taban tuzağı (yeni kanıt hatası önerisi, E27):** fark ≥ +2 puan olan 19 yeterli konfigürasyonun 14'ünde taban isabeti < %50; yeterli
  konfigürasyonlarda fark ile (50 − taban isabeti) arasında r = 0,52. Gerçek yukarı oranı ≈ %50 olan hedeflerde (son yarım saat, +15 dk,
  +1 s) nedensel "hep çoğunluk" tabanı kütüphane oranı 0,5 etrafında salındıkça kendisi yazı-tura gibi davranıp %47'ye düşebiliyor →
  "taban + 2 puan" kolaylaşıyor. Bu yüzden plasebo kıyası ve seçim düzeltmesi zorunlu; tek başına "fark ≥ 2" yanıltıcı.
- **Zayıf ama işe yaramayan bilgi:** yeterli konfigürasyonlarda isabet − plasebo ortalaması +0,52 puan (%64'ü pozitif). Fikir düzeyinde
  kaydırma boş dağılımına göre yalnız (a) seans yolu belirgin: ortalama fark −1,19 vs boş medyan −2,01 (%95'lik −1,40), p = 0,005
  (6 fikir için Bonferroni ≈ 0,03); ama ortalama hâlâ tabanın 1,2 puan altında. Açılış yolunun şekli, rastgele geçmiş günden biraz daha
  iyi bir "gün tipi" bilgisi taşıyor; gün içi yönün çoğunluk yönünden sapacağı anları yakalayacak kadar değil (oy kovalarında ana kütle %50'nin üstünde).
- **MIM NDX CFD'de yok:** 30m/15m/5m (2021–2025) eğim negatif, 1h son saatte (2016–2025) pozitif ama anlamsız ve son yarıda sıfır.
  SPY 1996–2013'teki R² %1,7 ile kıyaslanınca bu dönem/enstrümanda etki ya kaybolmuş ya hiç olmamış. (Yayın sonrası zayıflama literatürü
  burada doğrulanmadı.)
- **(f) "yön" değil "zamanlama/büyüklük" bilgisi:** iki koşullu yükseliş oranı da %50'nin üstünde kaldığı için hiçbir yön çağrısı hep-yukarıyı
  yenemez (aday ölçütü yapısal olarak geçilemez). Ama "gece pozisyonu yalnız son saat aşağı kapanınca" gibi bir zamanlama kuralı ortalama
  +13,6 vs +0,5 puan ayrımı veriyor; etki 2020–2025'e yığılmış (E17/E23 riski) ve sonradan bulundu → **aday değil**, ayrı ön-kayıtla
  bağımsız piyasada (SPY/QQQ kapanış→açılış, DAX) ve holdout dışı yeni dönemde sınanacak bir **ipucu**. Mekanizma (LETF varlıklarının
  2020'lerde büyümesi) bu yığılmayla tutarlı olabilir ama burada ölçülmedi.
- Meta-derslerle tutarlılık: §3-1 (rastgele girişte durum kapısı yok) ve ME-02/ME-03 (şekil eşleştirmesi yön vermiyor) çapalı tanımlarla da
  geçerli; §3-2 "korku döner" ile (f)'nin aşağı-kapanış-sonrası güçlü gece yükselişi aynı yönde.
- Deftere önerilen satır (dosya bu görevde değiştirilmedi): `| CP-01 | 2026-10-13 | Çapalı eşleştirme: (a) 09:30+N seans yolu, (b) gece yolu,
  (c) MIM r1→r13 aynen + analog, (d) olay mumu (2/3×ATR, 20-bar kırılım, boşluk) + m bar, (e) önceki gün + boşluk günlük, (f) kapanış baskısı
  dönüşü; 513 konfig, kaydırma-düzeltmeli | aday 0; en iyi c3 30m (+5,4 puan, P 0,987) düzeltilmiş p 0,70; MIM 30m β −0,017, 1h +0,045 (anlamsız);
  (f) yön tabanı yenemiyor, gece +13,6 vs +0,5 puan ipucu (post-hoc) | X |` ve §1'e E27 (taban < %50 tuzağı).

### Gaps
- 1m/5m yalnız 2025 (holdout öncesi ~228 gün) → istenen ince çözünürlüklü seans yolu (5m) yapısal olarak yetersiz kaldı; daha uzun
  Dukascopy 1m çekimi olmadan 1m/5m'de ≥ 200 sorgu kurulamıyor.
- MIM'in tam tanımı (son yarım saat) yalnız 30m/15m/5m'de (2021+); 2016–2020 için yalnız "son saat" vekili var. Gao vd.'nin tam metnine
  (yüksek oynaklık/hacim/haber günü alt-örnekleri) erişilmedi; tanım ikincil kaynaktan (Limkriangkrai vd. 2023) doğrulandı.
- Hiçbir fikir bağımsız piyasada (DAX, SPX/QQQ) sınanmadı; (f) ipucu için bu ilk sıradaki eksik.
- Planlanmış makro açıklama (CPI/NFP/FOMC) olay-tetikli fikri takvim verisi ve olay sayısı (≈100) yetersiz olduğu için denenmedi.
- Seçim düzeltmesindeki boş dağılım t istatistiği üzerinden; bootstrap P değeri her kaydırmada yeniden hesaplanmadı (bunun yerine t ≥ 1,96 vekili).
- Hacim/tick verisi kullanılmadı; erken kapanış günleri kural tabanlı tespit edildi (Şükran sonrası Cuma, 24 Ara, 3 Tem).

## Soru 2 — Seçim düzeltmesinden geçen çapalı / koşullu bir yapı var mı?

### Takeaway
Hayır. Ailenin tamamı (513) üzerinden sonuç-kaydırma boş dağılımında gözlenen en yüksek t (2,38) boş dağılımın %95'lik değerinin
(3,31) altında; en küçük düzeltilmiş p 0,70, Bonferroni en küçük 0,77. Ölçütleri (seçim hariç) geçen konfigürasyon sayısı 1, boş
ortalama 1,09 → tesadüf düzeyi. **Holdout bu aileden hiçbir tanım için harcanmamalı.**

### Cited Findings
- Seçim düzeltmesi: S = 200 kaydırma; her TF'nin gün listesi içinde sonuçlar tam gün dairesel kaydırıldı (aynı saat korunur; u ~ U(0,02, 0,98),
  aynı u tüm TF'lerde), komşu kümeleri ve kural çağrıları sabit, taban kaydırılmış sonuçlardan yeniden; ailenin tamamı her kaydırmada yeniden
  değerlendirildi — [capali_test.py](../../research/mum_derin_tarama_20261013/capali/capali_test.py)
- Gözlenen maks t = 2,38 (tüm aile ve yeterliler aynı konfig); boş maks t %95'lik: 3,31 (tüm aile), 3,04 (yalnız yeterli 272) —
  [results/null_ozet.json](../../research/mum_derin_tarama_20261013/capali/results/null_ozet.json)
- Vekil ölçütleri geçen (n ≥ 200, fark ≥ 2, t ≥ 1,96, iki yarı > 0, hareket > 1,5): gözlenen 1, boş ortalama 1,09, %95'lik 4 → p = 0,59 —
  [results/null_ozet.json](../../research/mum_derin_tarama_20261013/capali/results/null_ozet.json)
- Yeterli konfigürasyonların ortalama farkı −1,40 puan; boş dağılımın %5–95 aralığı −2,21…−1,43 (gözlenen %95'liğin hemen üstünde, p ≈ 0,05: kNN oylarında
  rastgeleden biraz fazla bilgi var, ama tabanı yenmiyor) — [results/null_ozet.json](../../research/mum_derin_tarama_20261013/capali/results/null_ozet.json)
- En yakın aday `c|30m|c3_analog|pct|LH30|K50`: düzeltilmiş p 0,70; kendi kaydırma dağılımında ham p 0,010 — 513 deneme içinde
  beklenen düzeyde — [results/aile.csv](../../research/mum_derin_tarama_20261013/capali/results/aile.csv)
- Hesap: tek süreç, `nice`, kurulum 2 sn + değerlendirme ve 200 kaydırma 34 sn + ekler ve sızıntı testi < 1 dk (90 dk bütçenin çok altında).

### Inferences
- Donmuş aday tanımı **yok** (aday 0). En yakın konfigürasyon (c3 30m) üç nedenle holdout'a gönderilmemeli: seçim düzeltmesi p 0,70;
  diğer TF'lerde aynı tanım tutmuyor; farkın büyük kısmı tabanın %47,5'e düşmesinden (plaseboya göre yalnız +3,5 puan).
- Tüm aileyi aynen yeniden üretmek (ör. ileride yeni veriyle) için komutlar (repo kökünden):
  `nice -n 10 python3.13 research/mum_derin_tarama_20261013/capali/capali_kur.py` →
  `nice -n 10 python3.13 research/mum_derin_tarama_20261013/capali/capali_test.py` →
  (tanımsal) `capali_ek.py`, (sızıntı) `capali_sizinti_testi.py`. Holdout sınırı `capali_veri.py::HOLDOUT`'ta tek yerde; holdout testi
  yapılacaksa yalnız önceden dondurulmuş tek tanım için ve bu aileden değil.
- Sonraki mantıklı adım (yeni ön-kayıt ister): (f)'nin zamanlama biçimi — "16:00'da son saat aşağıysa gece AL, değilse dışarıda" vs
  "her gece AL" — R/puan ve risk birimiyle, SPY/QQQ günlük (kapanış→açılış) ve DAX'ta, 2016–2020 ile 2021–2025 ayrı; yön isabeti ölçütüyle
  değil beklentiyle.

### Gaps
- Kaydırma boşu t-istatistiğine dayanıyor; gün-içi olay kümelenmesi (d fikri) t'yi şişirir, ama aynı şişme boş dağılımda da olduğundan
  karşılaştırma adil; bootstrap'lı tam boş dağılım hesaplanmadı.
- Bu çalışma NDX geçmişine yapılan 5.+ tur bakıştır (E23); olumsuz sonuç bu yüzden güvenilir, olumlu bir sonuç çıksaydı bile bağımsız
  piyasa gerekirdi.
