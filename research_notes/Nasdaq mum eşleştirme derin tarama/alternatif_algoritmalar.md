# Alternatif benzerlik algoritmaları ile NDX (NAS100) 10–50 mum pencere eşleştirmesi — +15 dk / +1 saat / +1 gün yön tahmini (sızıntısız ileri yürüme, 2026-10-13)

> Hesaplamalı çalışma, yerel veri. Holdout (bar bitişi ≥ 2025-12-01 00:00 UTC) yükleme anında kesildi ve `assert` ile denetlendi;
> hiçbir sorgu, kütüphane ya da sonuç bu sınırı geçmedi. Kod, ön-kayıt ve tüm çıktılar:
> `research/mum_derin_tarama_20261013/algoritmalar/` (PROTOKOL.md · alg_tarama.py · alg_ozet.py · alg_tani.py · _kontrol.py · results/).
> Başka hiçbir mevcut dosya değiştirilmedi, commit yapılmadı. Toplam hesap: 2 süreç, `nice -n 10`, ≈21 dk duvar saati.

**Tek cümle:** Altı yeni aile (z-normalize şekil/MASS, DTW, getiri korelasyonu, SAX/n-gram, Nadaraya–Watson, çok-ölçekli özet) × W × K × TF × ufuk × karar kuralı = **2.002 yapılandırmanın hiçbiri aday değil**; hepsi rastgele komşu düzeyinde (%51,1–51,7) ve hep-çoğunluk tabanının (%53,5–53,8) altında; aile çapında seçim düzeltmeli p = 0,70; gerçek veri, etiketleri tam hafta kaydırılmış boş verilerden ayırt edilemiyor.

---

## Soru 1 — Her aile × W × TF × ufuk için yön isabeti; tabanlar, plasebo, hareket, bootstrap, iki yarı

### Takeaway
Hiçbir aile, hiçbir pencere boyu, TF, ufuk veya K'da hep-çoğunluk tabanını anlamlı geçmedi: n ≥ 200 olan 921 yapılandırmanın **0'ı** P ≥ 0,975'e ulaştı, 393'ü anlamlı olarak tabanın altında. Ortalama isabet aileden bağımsız olarak rastgele komşu isabetine eşit (fark −0,27…+0,15 puan), tabanın 1,7–2,7 puan altında.

### Cited Findings

#### Kurulum (ön-kayıtlı; sonuçlardan önce yazıldı)
- Veri: 1m/5m Dukascopy 2025 (`bars_1m/5m.parquet`, 2025-01-01→2025-11-30), 15m Pepperstone (2023-10-01→2025-11-30), 1h Pepperstone (2016-05-29→2025-11-28). Holdout kesimi: `ts + TF < 2025-12-01` ve `assert` — [PROTOKOL.md](research/mum_derin_tarama_20261013/algoritmalar/PROTOKOL.md), [alg_tarama.py](research/mum_derin_tarama_20261013/algoritmalar/alg_tarama.py) `load()`.
- Hedef: karar anı = sorgu barının bitişi; y = close(t + h) − close(t) NDX puanı (bitişi t+h'ye birebir eşit bar; 1m'de ≤4 dk tolerans); yön = sign(y). 11 TF×ufuk hücresi (1h TF'de +15 dk yok) — [alg_tarama.py](research/mum_derin_tarama_20261013/algoritmalar/alg_tarama.py) `prep()`.
- Sızıntı kuralları: komşu yalnız te_j + h ≤ t; kütüphane = kayan 5 yıl (veri ne kadarsa: 1m/5m'de 2–11 ay, 15m'de 3–26 ay); komşu penceresi sorguyla çakışmaz (j ≤ q − kapsam − 1); seçilen komşular arası ≥ h/TF bar (sonuç pencereleri çakışmaz); normalizasyon yalnız pencere içi/öncesi (ATR = önceki 14 bar TR ortalaması; n-gram σ = önceki 100 getiri) — [PROTOKOL.md](research/mum_derin_tarama_20261013/algoritmalar/PROTOKOL.md).
- Sızıntı denetimi: 1m'de 60 sorgu × tüm aileler × 2 ufukta 5.478 komşu listesi tek tek denetlendi (sonuç kapanmış mı, pencere çakışması, 5 yıl, komşu sonuç çakışması, geçerlilik) → **0 ihlal** — [_kontrol.py](research/mum_derin_tarama_20261013/algoritmalar/_kontrol.py).
- Sorgu setleri (bağımsız olaylar, aralık ≥ ufuk): 1m 3.698 (2025-03-02→11-30, saatlik) + 1g seti 150; 5m 3.568 + 149; 15m 5.409 (2024-01-01→2025-11-28, 2 saatte bir) + 393; 1h 6.579 (2017-05-29→2025-11-28, 8 saatte bir) + 1g seti 1.746 (25 saat aralık → saat döner) — [run.log](research/mum_derin_tarama_20261013/algoritmalar/results/run.log).
- Aileler (W ∈ {10,20,30,50}; K ∈ {20,50,100}; kural R1 "tüm" = çoğunluk oyu, R2 "güçlü" = |pay − 0,5| ≥ 0,2):
  - **a `zED`**: z-normalize kapanış yolunda Öklid. MASS'in tanımladığı "distance profile" ile aynı mesafe (z-normalize Öklid, kayan nokta çarpımları); FFT yerine matris çarpımıyla birebir hesaplandı — MASS tanımı: [Mueen, MASS](https://www.cs.unm.edu/~mueen/FastestSimilaritySearch.html). **a2 `zED_amp`**: + pencere menzili sorgununkinin 0,5–2 katı.
  - **b `DTW`**: z-yol, Sakoe–Chiba bandı r = max(1, round(0,1·W)); tüm havuzda LB_Keogh → en düşük 1.000 LB (yetmezse ×4, en çok 16.000) → tam DTW → tekilleştirme. LB_Keogh ≤ DTW teoremi ve Sakoe–Chiba zarfı: [Keogh & Ratanamahatana, KAIS 2004](https://www.cs.ucr.edu/~eamonn/KAIS_2004_warping.pdf).
  - **c `retcorr`**: W log-getiri dizisinin Pearson korelasyonu, en yüksek K.
  - **d1 `SAXyol`**: z-yol → PAA (w parça) → Gauss eş-olasılıklı kırılımlarla a harf; (a,w) ∈ {(3,4),(3,8),(5,4),(5,8)}; tam kelime eşleşmesi, en yeniden geriye tekilleştirilmiş ≤ 200 eşleşme. SAX tanımı (PAA + Gauss kırılımları): [Lin, Keogh, Wei, Lonardi 2007](https://www.cs.ucr.edu/~stelo/papers/DMKD07b.pdf), [Keogh SAX sayfası](https://www.cs.ucr.edu/~eamonn/SAX.htm). **d2 `ngram`**: bar getirisi/σ → a ∈ {3,4,5} sembol, son w ∈ {4,6,8} sembol kelime (Markov n-gram).
  - **e `NW`**: ATR-normalize W bar getiri vektörü, Öklid; tekilleştirilmiş en yakın 300 aday üzerinde Gauss çekirdeği, bant = K'ncı komşunun mesafesi (sabit kural); tahmin = Σw·(y/ATR)/Σw.
  - **f `cokolcek`**: son 1,2,4,8,16,32 barın kümülatif getirisi + menzili, ATR ve √s ölçekli (12 boyut), Öklid.
  - **ref `refR7`**: ME-02'nin elenmiş ATR-ham 7 mum kNN'i, aynı sorgularda kıyas için (aile içine sayıldı).
- Tabanlar: hep-çoğunluk = havuzun (o andaki kütüphane) yukarı oranı; aynı-saat = aynı UTC saatindeki havuz oranı; plasebo = aynı uygun havuzdan aynı sayıda rastgele komşu, 20 tekrar ("geçer" = 20 tekrarın hepsinden yüksek). Fark = isabet − max(çoğunluk, saat), aynı çağrı kümesinde. Gün-blok bootstrap (h ≤ 1s → 1 gün, 1g → 7 gün blok), B = 2.000 — [alg_tarama.py](research/mum_derin_tarama_20261013/algoritmalar/alg_tarama.py) `run_eval()`.

#### Sonuç sayıları
- 2.002 yapılandırma (11 hücre × 182), n ≥ 200 çağrılı 921; her biri `tum_yapilandirmalar.csv`'de — [tum_yapilandirmalar.csv](research/mum_derin_tarama_20261013/algoritmalar/results/tum_yapilandirmalar.csv).
- Ön-kayıt ölçütlerini geçen yapılandırma sayısı (921 içinde): n ≥ 200: 921 · fark ≥ +2,0 puan: 10 · plaseboyu geçer: 78 · **P ≥ 0,975: 0** · iki yarıda da +: 9 · tahmin yönünde hareket > 1,5 puan: 199 · seçim düzeltmesi p ≤ 0,05: 0. **Seçim düzeltmesi hariç tüm ölçütleri geçen: 0; ADAY: 0** — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).
- Aile ortalamaları (n ≥ 200 yapılandırmalar) — [ozet_aile.csv](research/mum_derin_tarama_20261013/algoritmalar/results/ozet_aile.csv):

| Aile | yap. | isabet | hep-çoğunluk | aynı saat | plasebo | ort. fark | en iyi fark | anlamlı iyi / kötü |
|---|---|---|---|---|---|---|---|---|
| zED (MASS) | 137 | %51,41 | %53,66 | %52,62 | %51,30 | −2,33 | +2,25 | 0 / 54 |
| zED_amp | 136 | %51,14 | %53,80 | %52,61 | %51,29 | −2,71 | +2,46 | 0 / 69 |
| DTW | 136 | %51,27 | %53,76 | %52,60 | %51,31 | −2,59 | +2,89 | 0 / 62 |
| retcorr | 136 | %51,41 | %53,64 | %52,59 | %51,32 | −2,34 | +5,67 | 0 / 68 |
| SAXyol | 138 | %51,53 | %53,62 | %52,59 | %51,81 | −2,10 | +2,45 | 0 / 46 |
| ngram | 62 | %51,61 | %53,82 | %52,60 | %51,57 | −2,25 | +0,57 | 0 / 19 |
| NW | 108 | %51,68 | %53,84 | %52,79 | %51,53 | −2,16 | −0,56 | 0 / 57 |
| cokolcek | 34 | %51,21 | %53,51 | %52,31 | %51,33 | −2,32 | +5,87 | 0 / 12 |
| refR7 (ME-02) | 34 | %52,00 | %53,67 | %52,50 | %51,17 | −1,70 | +0,88 | 0 / 6 |

- TF × ufuk (n ≥ 200, aileler ortalaması): isabet / hep-çoğunluk / plasebo — 1m 15dk %50,3/%51,7/%50,2; 1m 1s %50,9/%53,0/%50,7; 5m 15dk %50,2/%53,2/%50,5; 5m 1s %50,9/%53,3/%50,9; 15m 15dk %50,5/%52,1/%50,3; 15m 1s %50,7/%53,1/%51,0; 15m 1g %55,1/%58,3/%55,1; 1h 1s %51,3/%53,6/%51,0; 1h 1g %54,4/%57,0/%54,5. Hiçbir hücrede anlamlı iyi yapılandırma yok (0/921); anlamlı kötü 6–75/hücre — [ozet_tf_ufuk.csv](research/mum_derin_tarama_20261013/algoritmalar/results/ozet_tf_ufuk.csv). 1m/5m 1g hücreleri yalnız 150/149 olay (n ≥ 200 ölçütüne baştan giremez).
- Kanonik yapılandırma ızgarası (K=50, R1, W=20; SAX a3w4; ngram a3w6): 99 hücrenin 93'ünde fark negatif; pozitifler +0,10…+0,84 puan (ör. 15m/1g retcorr +0,84, 5m/1g refR7 +0,72, 1m/15dk SAXyol +0,70); en kötü 1m/1g retcorr −11,5 puan (n≈150) — [ozet_kanonik.csv](research/mum_derin_tarama_20261013/algoritmalar/results/ozet_kanonik.csv).
- Hareket (spread 1,5 puan): kısa ufuklarda tahmin yönündeki ortalama hareket model −0,07 puan, taban +0,53 puan; 753 kısa-ufuk yapılandırmasının 41'i > 1,5 puan. 1g ufkunda model +12,2 puan, taban (hep-çoğunluk ≈ hep YUKARI) +16,2 puan; 168'in yalnız 45'inde model tabanı geçiyor. Ortalama |hareket|: 15 dk 16,9 puan, 1 s 32,0 puan → 1,5 puan ölçütünü 1g'de yalnız yükseliş sürüklenmesi geçiriyor — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- Taban seçimi: 921'in 878'inde hep-çoğunluk aynı-saatten güçlü (kısa ufuklar %52,8 vs %51,5) — aynı-saat tabanı bu ufuklarda zayıf; yine de modeller ikisinin de altında — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- DTW tam-seçim sertifikası (100. komşunun DTW'si ≤ dışarıda kalan adayların LB_Keogh'u): 5m/15m/1h kısa ufuklarda %92–97, 1h/1g %96; 1m'de %45 (15dk/1s), 1m/1g %4, 5m/1g %28 (aday tavanı 16.000 bağlayıcı, kütüphane 280 bin pencere) → 1m DTW'si yaklaşık (LB'si en düşük 16.000 aday içinde tam) — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).

### Inferences
- Yeni temsil aileleri, ME-02'deki elenmiş temsillerle aynı tabloyu verdi: komşu seçimi yön açısından rastgele seçimden farksız; tabanın altında kalmanın nedeni, gürültülü oyun zaman zaman yükseliş sürüklenmesine karşı "AŞAĞI" demesi (rastgele komşular da aynı kaybı yaşıyor).
- 1g ufkundaki %54–60 isabetler ve 12–23 puanlık "tahmin yönünde hareket" bilgi değil, 2017–2025 NDX yükseliş sürüklenmesi; hep-çoğunluk aynı sorgularda daha iyi (E13 tuzağı).
- 1m DTW'nin yaklaşık olması sonucu değiştirmez: DTW, kesin seçildiği 5m/15m/1h hücrelerinde de zED ile aynı düzeyde (çağrı korelasyonu 0,30).

### Gaps
- 1m/5m için kütüphane yalnız 2–11 ay (Dukascopy 2025; holdout öncesi 1m verisi bu kadar); 1m/5m 1g hücreleri 150 olayla ölçüt dışında. Daha uzun 1m geçmişi olmadan bu iki TF'nin 1g ufku sınanamaz.
- 1m/5m (Dukascopy) ile 15m/1h (Pepperstone) farklı besleme; kaynaklar arası tutarlılık ayrıca sınanmadı.
- Büyüklük ("kaç puan") hedefi bu çalışmada yeniden sınanmadı (görev yön odaklıydı; ME-02/ME-03'te saatin tipik hareketi kazanmıştı).
- MASS FFT ile değil matris çarpımıyla hesaplandı (matematiksel olarak aynı mesafe); matris-profil motif keşfi (sorgusuz, en sık tekrar eden motifler) yapılmadı.

---

## Soru 2 — Tutarlı bir yapı (güçlü-oy alt kümeleri, belirli ufuklar) tabanları geçiyor mu? Seçim düzeltmesinden sağ çıkıyor mu?

### Takeaway
Hayır. Ailenin en iyi yapılandırması (t = 1,57) tam-hafta kaydırılmış boş dağılımın **medyanının** (1,78) bile altında; aile p = 0,70. Güçlü-oy alt kümeleri tabandan daha kötü (%49,9 vs %53,2). Holdout'ta sınanacak **dondurulmuş aday YOK**.

### Cited Findings
- **Seçim düzeltmesi (ön-kayıtlı, maxT):** etiket dizisi tam hafta dairesel kaydırıldı (saat/gün korunur; 1m+5m ortak, 15m ve 1h ayrı kaydırma), 2.002 yapılandırmanın TAMAMI 200 kez yeniden değerlendirildi; istatistik = blok-t (fark/blok-SE), n ≥ 200 içinde maksimum. Gerçek maxT = **1,565**; boş maxT yüzdelikleri 50/90/95/99 = 1,78 / 2,39 / 2,59 / 2,88 → **aile p = 0,697**. Gerçek en büyük fark +5,87 puan; boş en büyük fark medyanı +6,05, %95'i +9,25. Bonferroni (921): tüm p_bonf = 1 — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt), [secim_duzeltmesi_null.npz](research/mum_derin_tarama_20261013/algoritmalar/results/secim_duzeltmesi_null.npz).
- Aile içi maxT (yalnız o ailenin yapılandırmaları): en küçük ayarlı p cokolcek 0,060; SAXyol 0,38; retcorr 0,41; ngram 0,56; diğerleri ≥ 0,73 — [ozet_aile.csv](research/mum_derin_tarama_20261013/algoritmalar/results/ozet_aile.csv).
- **Gerçek veri boş veriden ayırt edilemiyor:** gerçek ortalama t = −1,735, boş ortalamanın %5–95 aralığı [−2,06; −1,62]; gerçek t > 1,96 sayısı 0 (boşta medyan 0, %95'i 2); gerçek t < −1,96 sayısı 379 (boşta medyan 425,5, %5–95: 348–506). Yani 393 "anlamlı kötü" yapılandırma da bilgisiz oylamanın beklenen davranışı (iyi/kötü asimetrisi E26'nın tersi yönde değil, boşla aynı) — [alg_ozet.py](research/mum_derin_tarama_20261013/algoritmalar/alg_ozet.py) çıktısı, ek denetim komutu [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- **Neden tabanı geçemiyor (cebir):** model − taban = s·(2a − 1); s = modelin tabana karşı çıktığı çağrı payı (%32–35), a = o çağrılarda isabet. Havuzlanmış a = **%47,3** (aile aralığı %47,1–47,7; TF×ufuk %41,3–48,8); tabanı geçmek için a > %50 gerekir. Model "AŞAĞI" dediği anlarda gerçek yukarı oranı %52,7, genel %53,8 → en fazla ~1 puanlık sinyal, sürüklenmeyi yenmeye yetmiyor — [tani_celiski.csv](research/mum_derin_tarama_20261013/algoritmalar/results/tani_celiski.csv).
- **Güçlü-oy alt kümeleri (R2):** n ≥ 200 olan 127 yapılandırmada ortalama isabet %49,87, hep-çoğunluk %53,15, plasebo %50,42; anlamlı iyi 0, kötü 11. n < 200 olan 196 güçlü yapılandırmada P ≥ 0,975 yalnız 1 (beklenen tesadüf ≈ 5), P ≤ 0,025 44 — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- Tek göze çarpan küçük alt küme: `ngram` 15m/15dk a=3 w=6 güçlü — n = 141 (< 200), isabet %62,4 vs çoğunluk %49,7, P = 0,9925, iki yarı +14,0/+10,9 puan. Komşu parametrelerde yok (a3w4: hiç güçlü çağrı; a3w8 n=37 +2,7; a4w6 n=40 0,0; a5w4 n=103 −5,8 puan) ve aynı parametre 1h/1s'de **−10,6 puan, P = 0,0095** (anlamlı kötü), 5m/15dk +1,5, 15m/1s −2,1 → izole, 2.002 içinden seçilmiş tesadüf — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- Yakın kaçanlar (n ≥ 200): (1) `retcorr` 5m/15dk W=50 K=20 güçlü — n 282, +5,67 puan, plaseboyu geçer, iki yarı +1,5/+9,3, hareket 1,58 puan, ama P = 0,897 ve maxT ayarlı p = 0,95 (7 ölçütten 5'i). (2) `cokolcek` 15m/15dk K=20 güçlü — n 409, +5,87 puan, P = 0,93, hareket 1,75 puan, ama plasebo maksimumu (%54,3) model isabetinin (%53,6) üstünde; bu alt kümede taban yalnız %47,7 (alt küme düşüş-ağırlıklı anlara düşüyor, bilgi komşulardan değil alt kümeden) — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).
- Plasebo-geçme oranı: 921'in 78'i (%8,5; tesadüf 1/21 = %4,8) 20 plasebo tekrarının hepsinden yüksek; ama simetrik alt kuyrukta (plasebo ortalamasının aynı uzaklık altında) 57 yapılandırma var ve ortalama isabet − plasebo = 0,00 puan → fazlalık büyük ölçüde yapılandırılmış komşu kümelerinin rastgele kümeden daha yüksek varyansı. Asimetri yalnız refR7'de (6 üst / 0 alt) — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- Keşif (ön-kayıt DIŞI, karar kanıtı değil): 9 ailenin kanonik çağrılarında ≥6/7/8 aile YUKARI derse isabet tabanla birebir aynı (taban da YUKARI); ≥6–8 aile AŞAĞI derse fark işaret değiştiriyor: 5m/1s ≥6 n=390 +9,2 puan, 1h/1s ≥6 n=427 −5,4, 15m/1s ≥7 n=81 −21,0, 15m/15dk ≥8 n=31 −41,9 → tutarlı yön yok — [kesif_uzlasi.csv](research/mum_derin_tarama_20261013/algoritmalar/results/kesif_uzlasi.csv).
- **Dondurulmuş aday tanımı:** yok (ADAY ölçütlerinin tamamını geçen 0; seçim düzeltmesi hariç tamamını geçen de 0). Yeniden üretim (holdout'a dokunmaz): proje kökünden `nice -n 10 /opt/homebrew/Cellar/python@3.13/3.13.9_1/bin/python3.13 research/mum_derin_tarama_20261013/algoritmalar/alg_tarama.py` (≈20 dk, 2 süreç) → `alg_ozet.py` → `alg_tani.py`. Not: zsh'deki `python3` takma adı 3.13'tür; `nice python3` 3.14'ü çağırır ve numba yoktur — tam yol kullanılmalı.

### Inferences
- Bu aile için holdout (2025-12-01 sonrası) harcanmamalı: sınanacak aday yok; yakın kaçanlar boş dağılımın medyanı düzeyinde ve tek tek seçilip holdout'ta denenmeleri seçim yanlılığını (E12/E23/E24) yeniden üretir.
- "Güçlü oy = daha isabetli" sezgisi bu ailede de tutmuyor; güçlü oy çoğunlukla az görülen yöne (AŞAĞI) yapılan aşırı-güvenli çağrıdır ve sürüklenmeye karşı kaybeder (ME-02 bulgusuyla aynı).
- Yönde çıkarılabilecek tek sinyal, model "AŞAĞI" dediğinde yukarı oranının ~1 puan düşmesi; bu hem plasebo-üstü olarak zayıf hem de 1,5 puan spread karşısında işlem değeri taşımıyor.

### Gaps
- 1m/5m kaydırma grubu ~47 haftalık seri yüzünden yalnız 44 farklı kaydırma değeri üretebildi (200 tekrar bu 44 değeri yineliyor); 15m/1h grupları daha çeşitli (1h'de 168 farklı). Aile çapındaki boş dağılım üç grubun ortak maksimumu olduğu için çözünürlük yeterli, ama 1m/5m'ye özgü alt aile p'leri ~1/45 çözünürlüklü.
- Seçim istatistiği blok-t; ham fark (puan) üzerinden ikincil boş dağılım da raporlandı ama ön-kayıtlı karar maxT'ye göre.
- Uzlaşı analizi ön-kayıt dışı keşiftir; herhangi bir uzlaşı kuralı ancak yeni veride ön-kayıtla sınanabilir.

---

## Soru 3 — Aileler birbirine ve önceki elenmiş yöntemlere göre nasıl?

### Takeaway
Altı yeni ailenin hepsi aynı gürültü bandında (isabet %51,1–51,7, plaseboya göre −0,27…+0,15 puan); aralarında anlamlı bir sıralama yok. Aynı sorgularda çalıştırılan eski ME-02 temsili (ATR-ham 7 mum kNN) yeni ailelerden biraz iyi (%52,0; plasebo +0,83 puan) ama o da tabanın altında. Yani şekil eşleştirmesini "daha iyi benzerlik ölçüsü" ile kurtarmak mümkün olmadı.

### Cited Findings
- Aile isabet − plasebo ortalaması (puan): DTW −0,04 · NW +0,15 · SAXyol −0,27 · cokolcek −0,12 · ngram +0,04 · retcorr +0,08 · zED +0,10 · zED_amp −0,15 · **refR7 +0,83** — [tani.txt](research/mum_derin_tarama_20261013/algoritmalar/results/tani.txt).
- Önceki elenmiş yöntemler (ME-02, 98.260 sorgu, 4 sembol): piramit-33 %51,69 / taban %53,34 / rastgele %51,49; R7 %51,69 / %53,34 / %51,51 — [RAPOR_KALDIRMA_TESTI.md](research/mum_eslestirme_20261012/RAPOR_KALDIRMA_TESTI.md). Bu çalışmada aynı R7 yalnız NDX'te: %52,00 / %53,67 / %51,17; yeni aileler %51,14–51,68 → önceki raporla tutarlı, yeni aileler daha iyi değil — [ozet_aile.csv](research/mum_derin_tarama_20261013/algoritmalar/results/ozet_aile.csv).
- ME-03'te bağlam (VIX, stres, saat, oynaklık) ve çapraz-sembol eklemek yönde 0–1/69 hücre kazandırmıştı — [RAPOR_BAGLAM_TESTI.md](research/mum_eslestirme_20261012/RAPOR_BAGLAM_TESTI.md); bu çalışmada temsil değiştirmek de 0/921.
- Aileler arası çağrı korelasyonu (1h TF, 1 s ufuk, kanonik yapılandırmalar): zED–zED_amp 0,49; zED–DTW 0,30; zED_amp–DTW 0,20; retcorr–NW 0,17; diğer tüm çiftler ≤ 0,13 (çoğu ≤ 0,08) → aileler birbirinden neredeyse bağımsız çağrılar üretiyor, ama hiçbiri bilgi taşımıyor — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).
- K etkisi: K=20 %50,79, K=50 %51,77, K=100 %51,99 isabet; büyük K komşu oyunu havuz çoğunluğuna (tabana) yaklaştırıyor, bilgi eklemiyor. W etkisi yok: W=10/20/30/50 → %51,24/%51,56/%51,33/%51,45 — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).
- Kural etkisi: R1 "tüm" 794 yapılandırma %51,67, fark −2,13 puan; R2 "güçlü" 127 yapılandırma %49,87, fark −3,63 puan — [ozet.txt](research/mum_derin_tarama_20261013/algoritmalar/results/ozet.txt).
- Defterdeki ilgili önceki X sonuçlar: PM (formasyon tekrarı yön tabanı ±2 puan, çoklu test sonrası 0), OLD-13 (CORTEX analog-kNN yön öngörmüyor), ME-02/ME-03 (X) — [KAPI_KAYIT_DEFTERI.md](docs/KAPI_KAYIT_DEFTERI.md) §2.4 (OLD-13), §2.6 (PM), §2.8 (ME-02/03).

### Inferences
- Şekil-benzerliği tabanlı yön tahmini NDX'te temsil (ham mum, piramit, z-yol, DTW, getiri korelasyonu, sembolik kelime, çekirdek regresyonu, çok-ölçekli özet), bağlam ve sembol ekseninde artık geniş biçimde elenmiş durumda; sıradaki deneylerin "başka bir benzerlik ölçüsü" olması beklenen getiriyi düşük kılar. Kenar aranacaksa defterin §3 ilkelerine göre günlük rejim/bilgi şoku (CAPREV benzeri) veya stratejinin kendi yapısı (geometri, zaman çıkışı) tarafında aranmalı.
- refR7'nin yeni ailelerden hafif iyi olması, ATR birimli mutlak mum boylarının (z-normalize şekilde kaybolan) oynaklık bilgisini taşımasıyla tutarlı (ME-02'de büyüklükte rastgeleye göre +%2–3 bulunmuştu); bu yönde değil oynaklıkta bir bilgi.
- Önerilen defter satırı (bu çalışma görevin "başka dosyaya dokunma" kısıtı yüzünden deftere YAZMADI; koordinatör ekleyebilir): `| MT-A1 | 2026-10-13 | Alternatif benzerlik aileleri (zED/MASS, zED_amp, DTW Sakoe–Chiba+LB_Keogh, retcorr, SAXyol, ngram, Nadaraya–Watson, çok-ölçekli özet; W 10–50, K 20/50/100, R1/R2) NDX 1m/5m/15m/1h × +15dk/+1s/+1g, holdout 2025-12-01 öncesi, ön-kayıt PROTOKOL.md | 2.002 yapılandırma (921 n≥200): isabet %51,1–51,7 = plasebo, hep-çoğunluk %53,5–53,8; P≥0,975 0, anlamlı kötü 393 (boşta beklenen 425); tam-hafta kaydırmalı maxT p=0,70; çelişki isabeti %47,3; güçlü oy %49,9; aday 0 | X |` ve §1'e öneri: "Seçim düzeltmesinde gerçek 'anlamlı kötü' sayısı da boş dağılımla kıyaslanmalı — sürüklenmeye karşı gürültülü oy yapısal olarak kötü hücre üretir; kötü hücre ≠ ters bilgi."

### Gaps
- Yalnız NDX; DAX/XAU/OIL ve çok değişkenli (OHLC) DTW, mum-tabanlı SAX (gövde/fitil sembolleri) ve sorgusuz matris-profil motif keşfi denenmedi.
- Evrim Paneli oturum notu (1. KURAL) ve defter satırı (3. KURAL) görev kısıtı nedeniyle yazılmadı; koordinatörün eklemesi gerekiyor.
- Web kaynakları yalnız algoritma tanımları için kullanıldı (MASS, LB_Keogh/Sakoe–Chiba, SAX); Nadaraya–Watson ve çok-ölçekli özetin uygulama tanımı yalnız yerel betikte (`alg_tarama.py`) belgeli.
