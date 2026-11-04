# BTC gölge portföyünün bağımsız dönem sınavı: dondurulmuş P-PRE 2017-08 → 2021-05 Binance verisinde

Kapsam: 2026-10-22. 08 notundaki dondurulmuş kollar ve portföyler, önceki turların hiçbir aşamasında görülmemiş 2017-08-17 → 2021-05-31
Binance verisinde **tek seferlik**, parametre ayarı yapılmadan sınandı. Ön kayıt sonuçtan önce yazıldı:
[prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/prereg.md) (12:17 UTC; EK-1 veri düzeltmesi sonuçtan
önce, EK-2 duyarlılıklar sonuçtan sonra; verdikti değiştirmez). Kod/çıktı kökü:
[btc_indep_2017_2021/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/). Dondurulmuş kod SHA256'lı kaynaklardan **birebir
kopyalandı**; yalnız veri yolu, ızgara başlangıcı, bölme ve tarih aralığı sabitleri değişti
([PORT_DIFF.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/scripts/port/PORT_DIFF.txt),
[MANIFEST.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/scripts/port/MANIFEST.txt)). Kutuya/Supabase'e
dokunulmadı, başka repo dosyası değişmedi, commit yok. Tablolarda ondalık nokta, metinde virgül.

**Kısa hüküm:** Ön-kayıtlı kurala göre **P-PRE bağımsız dönemde TUTUYOR**: n 2.123, **+0,039R/işlem (+14,8 bp)**, gün-bloklu
P(EV>0) **%99,9** [GA +0,013; +0,065], kart **6/6**, plasebo %100. Bu, POST'taki +0,026R'nin %95 GA'sı içinde (tutarlı). Ama kenar
**ince ve maliyet-koşullu**: başabaş RT maliyeti ≈ **10 bp** (dondurulmuş 1,85 bp'nin ~5 katı), sabit 15 $ modelinde **−0,042R**,
en iyi 20 gün çıkınca **+0,005R**, 2018 ayı yılı **−0,026R**. Kenarı üç kol taşıyor (CORE, MAX10, QB); **X04 bağımsız dönemde işaret
değiştirdi (−0,013R)**. Post-hoc CAPREV-RV pozitif kaldı (+0,236R, n 46, P %93,6), OF02 karar verilemeyecek kadar küçük (n 15),
DV04c negatif.

---

## 1. Veri ve motor bağımsız dönemde doğru kuruldu mu?

### Takeaway
Evet. 46 spot + 17×5 perp arşivi SHA256 ile doğrulandı; motor yeni veride kaba döngüyle **3.000/3.000** ve `lib_trend.M1.simulate` ile
**268/268** birebir. İki veri sürprizi bulundu ve sonuçtan önce düzeltildi/kaydedildi: perp arşivi 2020-01'de başlıyor; 2017-12 ve
2018-02'de iki blok spot barı dakika-dışı damgalı.

### Cited Findings
- İndirme: spot BTCUSDT 1m 2017-08 → 2021-05 (46 dosya), UM perp klines/premium/mark/index/funding 2020-01 → 2021-05 (17'şer dosya),
  sorunlu 0 — [01_download.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/01_download.log). S3 listesi:
  UM klines arşivi `BTCUSDT-1m-2020-01.zip` ile başlıyor (günlükte tek ek gün 2019-12-31); metrics 2020-09-01'de —
  [00_list.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/00_list.log)
- Spot kalite: ilk bar 2017-08-17 04:00, son 2021-05-31 23:59; 1.984.629 satır, eksik 8.091 dk, ≥5 dk boşluk 30 (en büyükleri
  2018-02-08 00:28 → 02-09 09:59 ≈33,5 s; 2018-06-26 10 s; 2019-05-15 10 s); sıfır hacimli bar 23.931 (23.696'sı 2017); OHLC tutarsızlığı 0 —
  [btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/data/btc_quality_report.json)
- Dakika-dışı damga: 21.602 bar (+20,799 s ve +14,789 s), tabanlandı; tek çakışma düşürüldü; üst TF OHLC'leri öncesi/sonrası birebir —
  [offgrid_fix_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/data/offgrid_fix_report.json),
  [02b_floor.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/02b_floor.log)
- Perp: 744.480 satır, eksik 0, sıfır hacim 61; baz (perp/spot) medyanı +3,6 bp, %0,1–%99,9 [−34,5; +42,7] bp; premium endeksiyle
  korelasyon 0,92 — [futures log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/03_build_futures.log),
  [btc_scalp_1m_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/data/btc_scalp_1m_report.json)
- Makro (yfinance): QQQ/VIX/DXY/TNX/NDX 2017-01-03 → 2021-06-30, 1.131 gün, NaN 0 —
  [04_macro.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/04_macro.log)
- Motor: "(a) T03 n=268 lib_trend ile uyuşmazlık: 0 … (b) kaba döngü: 3000 karşılaştırma, uyuşmazlık 0" —
  [08_selftest.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/08_selftest.log); OF özellikleri önek
  (sızıntı) testi "OK" (kesim 2020-09-15) — [06_of_build.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/06_of_build.log)
- Rollover/DST: RO saatleri 2017-11-03 21, 11-06 22, 2018-03-09 22, 03-12 21 … 2021-03-15 21 UTC; QB girişleri 872× 21:01, 510× 22:01
  (zoneinfo `America/New_York` 17:00; sabit ofset yok).
- Sıcak dakika eşiği dondurulmuş sayı **29,298 bp** (eski DISC p99, eski veriden yeniden okundu); bağımsız dönemde dakikaların %4,46'sı
  bu eşiğin üstünde (dönemin kendi p99'u 59,1 bp) → kayma varsayımı muhafazakâr —
  [sensitivity.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/sensitivity.json)

### Inferences
- Sapmalar sonucu etkilemiyor: metrics indirilmedi (hiçbir kol okumuyor); dakika-dışı bloklar 2017-12/2018-02'de ve yalnız 1m birleştirmeyi
  (scalp kolları, 2020+) ilgilendiriyordu; perp başlangıcının 2020-01 olması yalnız OF02/DV04c'nin örneklemini küçülttü.

### Gaps
- Pepperstone'un 2017–2021'deki gerçek BTC CFD spread/swap'ı ölçülmedi (veri yok); dondurulmuş 2026 maliyet modeli uygulandı (§3).

---

## 2. P-PRE ve diğer portföyler bağımsız dönemde ne verdi?

### Takeaway
P-PRE IND penceresinde **6/6** ve P(EV>0) %99,9; iki alt pencerede de pozitif (2017-08 → 2020-01-10: +0,042R, P %99,5; perp dönemi
2020-01-11 → 2021-05: +0,035R, P %95,4). P-ALL−DV de 6/6 (+0,044R). P-ALL, DV04c yüzünden perp penceresinde 4/6'ya düşüyor.

### Cited Findings
— [cards_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/cards_table.csv),
[cards.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/cards.json),
[10_portfolio.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/10_portfolio.log) (vetosuz; kol başı tek pozisyon)

| portföy | pencere | n | ortR | bp | P(EV>0) [GA] | yarılar | stres | $15 | icra farkı | küresel tek-poz | en iyi 5 / 20 gün hariç | maxDD R | plasebo % (ort) | kart |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P-PRE** | **IND** | **2123** | **+0.039** | **+14.8** | **0.999 [+0.013, +0.065]** | +0.032 / +0.046 | +0.035 | −0.042 | 0.010 | +0.030 | +0.026 / **+0.005** | 19.4 | 100 (+0.005) | **6/6** |
| P-PRE | A (→2020-01-10) | 1291 | +0.042 | +15.9 | 0.995 | +0.005 / +0.078 | +0.038 | −0.062 | 0.009 | +0.038 | — / −0.007 | 19.4 | 99.5 | 6/6 |
| P-PRE | PERP (2020-01-11→) | 832 | +0.035 | +13.1 | 0.954 | +0.010 / +0.060 | +0.032 | −0.012 | 0.010 | +0.018 | — / −0.032 | 8.5 | 86.5 | 6/6 |
| P-ALL−DV | IND | 2184 | +0.044 | +17.3 | 1.000 [+0.018, +0.070] | +0.034 / +0.054 | +0.040 | −0.036 | 0.011 | +0.039 | +0.031 / +0.010 | 18.4 | 100 (+0.005) | 6/6 |
| P-ALL−DV | PERP | 869 | +0.048 | +18.7 | 0.988 | +0.029 / +0.067 | +0.044 | +0.001 | 0.012 | +0.039 | — / −0.019 | 7.8 | 95.5 | 6/6 |
| P-ALL | IND | 2710 | +0.030 | +14.1 | 0.978 [+0.001, +0.059] | +0.038 / +0.022 | +0.021 | −0.073 | 0.014 | +0.034 | +0.019 / −0.005 | 27.8 | 100 (−0.016) | 6/6 |
| P-ALL | PERP | 1382 | +0.017 | +12.1 | 0.772 | +0.014 / +0.021 | +0.003 | −0.082 | 0.019 ✗ | +0.021 | — / −0.046 | 27.5 | 97.0 | 4/6 |
| P-CORE | IND | 106 | +0.227 | +38.7 | 0.960 [−0.030, +0.487] | +0.118 / +0.337 | +0.227 | +0.203 | 0.020 | +0.227 | +0.138 / −0.187 | 7.2 | 69.0 | 5/6 (n<150) |

- Yıl bazında P-PRE (n, ortR): **2017k 203 +0.064 · 2018 502 −0.026 · 2019 569 +0.090 · 2020 604 +0.051 · 2021k 245 +0.005**; P-ALL−DV
  2020 +0.060, 2021k +0.027; P-ALL 2021k −0.012 — aynı dosya. BTC al-tut aynı yıllarda: 2017k +%220, 2018 −%72, 2019 +%90, 2020 +%302,
  2021k +%27 — [sensitivity.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/sensitivity.json)
- 08 notu POST'ta P-PRE +0,026R, P %95,7, GA [−0,004; +0,057], kart 5/6 (icra ✗), BLIND +0,014, son 12 ay −0,008 —
  [08_strateji_insasi.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20scalping%20strateji%20ara%C5%9Ft%C4%B1rmas%C4%B1/08_strateji_insasi.md)
- ΣR katkısı (IND, R): CORE +24,1 · MAX10 +20,6 · QB +42,7 · X04 −4,4 · CAPREV +10,9 · OF02 +2,2 · DV04c −15,3 —
  [contrib.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/contrib.json). Kol korelasyonları (günlük ΣR)
  en çok CORE–MAX10 0,17, MAX10–QB 0,11, diğerleri |ρ| ≤ 0,11 — [corr_post.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/corr_post.csv)
- P-PRE işlemlerinin %90'ı long; QB'siz P-PRE (CORE+MAX10+X04) n 741 +0,054R, P %96,6 [−0,002; +0,113].

### Inferences
- Ön-kayıtlı H1 karşılandı ve sonuç POST ile **tutarlı** (+0,039, POST GA'sının içinde; tersine POST'un +0,026'sı da bağımsız GA'nın içinde).
  İşaret iki ayrı alt pencerede ve beş takvim yılının dördünde pozitif; tek negatif yıl 2018 ayı piyasası.
- Plaseboya göre fark gerçek: aynı yıl × aynı saat × aynı yönde rastgele günlerde portföy ortalaması +0,005R; gerçek +0,039R. Yani long
  ağırlıklı portföyün kazancı yalnız dönemin yükseliş drift'i değil. Ancak portföyün %100 plasebo yüzdeliği büyük-n etkisidir (E-ST3);
  kol yüzdelikleri 69 / 98 / 100 / 60.
- **Kırılganlık:** en iyi 20 gün çıkınca P-PRE +0,005R; 2.123 işlemin kenarı az sayıda büyük günde (CORE/MAX10'un trend günleri) yoğun.

### Gaps
- Bağımsız dönem "B" sınıfı kanıt ekledi ama portföy hâlâ broker icrasında (gerçek spread/kayma/swap, rollover-açılışı spread'i) ölçülmedi.

---

## 3. Kenar maliyete ne kadar duyarlı? (sabit 15 $ ve başabaş spread)

### Takeaway
Çok. Dondurulmuş % modelinde (1,85 bp RT) +0,039R; RT maliyet 5 bp'de +0,026R (P %97,5), 7,5 bp'de +0,014R (P %86,5), **10 bp'de +0,002R
(başabaş)**, 15 bp'de −0,022R. Sabit 15 $ modelinde (2018–2019 fiyatlarında 15 $ ≈ 15–50 bp) −0,042R. Kenarın çoğu QB'den geliyor ve
QB **≈7,5 bp RT'de** sıfırlanıyor; CORE/MAX10 20 bp'de bile pozitif.

### Cited Findings
— [cost_sweep.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/cost_sweep.csv),
[11_sensitivity.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/11_sensitivity.log) (EK-2; ön-kayıtlı DEĞİL, yalnız bilgi)

| RT maliyet (bp) | P-PRE ortR | P-PRE bp | P(EV>0) | CORE | MAX10 | QB | X04 | CAPREV | OF02 | DV04c | P-ALL−DV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.85 (dondurulmuş) | +0.039 | +14.8 | 0.999 | +0.227 | +0.073 | +0.031 | −0.013 | +0.236 | +0.146 | −0.029 | +0.044 |
| 2.775 (stres) | +0.035 | +14.0 | 0.997 | +0.227 | +0.072 | +0.026 | −0.015 | +0.235 | +0.141 | −0.061 | +0.040 |
| 5 | +0.026 | +11.8 | 0.975 | +0.226 | +0.069 | +0.014 | −0.023 | +0.232 | +0.132 | −0.098 | +0.031 |
| 7.5 | +0.014 | +9.0 | 0.865 | +0.225 | +0.066 | −0.001 | −0.034 | +0.228 | +0.121 | −0.163 | +0.019 |
| 10 | +0.002 | +6.3 | 0.557 | +0.205 | +0.064 | −0.016 | −0.041 | +0.224 | +0.110 | −0.206 | +0.007 |
| 15 | −0.022 | +1.2 | 0.048 | +0.175 | +0.058 | −0.045 | −0.055 | +0.216 | −0.007 | −0.307 | −0.017 |
| 20 | −0.045 | −4.0 | 0.001 | +0.149 | +0.053 | −0.073 | −0.071 | +0.208 | −0.174 | −0.395 | −0.040 |

- Sabit 15 $ RT, P-PRE yıl bazında (n, ortR$15 / ortR%): 2017k 203 +0.004 / +0.064 · 2018 502 **−0.122** / −0.026 · 2019 569 −0.036 / +0.090 ·
  2020 604 −0.016 / +0.051 · 2021k 245 +0.002 / +0.005 — [sensitivity.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/sensitivity.json)
- Diğer ön-kayıtlı duyarlılıklar: dönemin kendi sıcak eşiği (59,1 bp) → P-PRE +0,0394 (değişmez); >%5 fitil işaretli 37 günde giren/çıkan
  74 işlem hariç → +0,036R, P %99,8; swap −%22,5 → CORE +0,227 → +0,212, MAX10 +0,073 → +0,071 (QB/X04 gece taşımıyor) — aynı dosya.

### Inferences
- "Bağımsız dönemde tutuyor" hükmü **dondurulmuş maliyet modeline koşullu**. 2017–2019'da perakende BTC CFD maliyetlerinin bugünkü
  1,85 bp'den yüksek olduğu neredeyse kesin; bu dönemin gerçek bir perakende hesabında P-PRE (özellikle QB) büyük olasılıkla kâr etmezdi.
  Sınav, kuralın **sinyal** kenarının farklı rejimde işaretini koruduğunu gösterir; kârlılık ise bugünkü maliyetin gerçekten ~2 bp
  olmasına bağlı (gölgede ölçülecek: 08 notu GO ölçütü vi).
- QB'nin bağımsız dönemdeki brüt kenarı (≈11,8 bp; stopsuz dondurulmuş hâli +11,1 bp net) POST'tan (+4,25 bp) büyük; bu kolun kenarı
  rollover-sonrası iki saatlik penceredeki sistematik yükselişten geliyor ve broker'ın tam o dakikadaki (RO+1) spread'ine aşırı duyarlı.

### Gaps
- Pepperstone/benzeri CFD'lerin 2017–2021 BTC spread geçmişi için güvenilir kaynak aranmadı/bulunamadı; maliyet taraması yerine konan kanıttır.

---

## 4. Kollar tek tek: hangisi bağımsız dönemde ayakta kaldı?

### Takeaway
Ön-kayıtlı kollardan **üçü ayakta (CORE, MAX10, QB), biri düştü (X04)**. Post-hoc kollardan CAPREV-RV pozitif (P %93,6, n 46), OF02
belirsiz (n 15), DV04c negatif (zaten "geçersiz" sayılmıştı).

### Cited Findings
— [cards_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/cards_table.csv),
[sleeve_reproduction.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/sleeve_reproduction.csv) (IND, kol-içi tek pozisyon; POST sütunu 08 notundan)

| kol | etkin başlangıç (ilk işlem) | n | ortR | bp | P(EV>0) [GA] | yarılar | en iyi 20 gün hariç | plasebo % | kart | yıl (n ortR) | POST (08) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 CORE | 2018 (EMA200 ısınması) | 106 | **+0.227** | +38.7 | 0.960 [−0.030, +0.487] | +0.12 / +0.34 | −0.19 | 69.0 | 5/6 | 18: 6 −1.02 · 19: 32 +0.51 · 20: 49 +0.30 · 21k: 19 −0.05 | 96 +0.110 |
| S2 MAX10 | 2017-08 | 281 | **+0.073** | +64.6 | 0.995 [+0.017, +0.134] | +0.09 / +0.06 | −0.02 | 98.0 | **6/6** | 17k: 37 +0.14 · 18: 46 −0.02 · 19: 69 +0.13 · 20: 93 +0.08 · 21k: 36 +0.01 | 194 +0.029 |
| S3 QB (2×ATR1h) | 2017-08 | 1382 | **+0.031** | +9.9 | 0.997 [+0.009, +0.053] | +0.02 / +0.04 | +0.007 | 100 | **6/6** | 17k: 136 +0.07 · 18: 364 +0.00 · 19: 365 +0.04 · 20: 366 +0.04 · 21k: 151 +0.01 | 1014 +0.016 |
| S4 X04 | 2017-09 | 354 | **−0.013** | −12.7 | 0.370 [−0.090, +0.074] | −0.03 / +0.00 | −0.14 | 60.0 | 1/6 | 17k: 30 −0.05 · 18: 86 −0.08 · 19: 103 +0.11 · 20: 96 −0.07 · 21k: 39 −0.01 | 267 +0.035 |
| S5 CAPREV-RV (post-hoc) | 2018 | 46 | +0.236 | +148 | 0.936 [−0.072, +0.553] | +0.07 / +0.40 | −0.48 | 92.0 | 5/6 | 18: 8 +0.07 · 19: 16 +0.00 · 20: 6 +0.83 · 21k: 16 +0.33 | 44 +0.245 |
| S6 OF02 (post-hoc) | 2020-02 | 15 | +0.146 | −33.3 | 0.735 [−0.317, +0.590] | +0.37 / −0.05 | — | 85.5 | 2/6 | 20: 10 +0.15 · 21k: 5 +0.13 | 57 +0.205 |
| S7 DV04c (geçersiz) | 2020-01 | 526 | −0.029 | +0.9 | 0.289 [−0.126, +0.068] | −0.04 / −0.02 | −0.18 | 90.0 | 1/6 | 20: 315 −0.01 · 21k: 211 −0.06 | 117 +0.273 (DISC 352 −0.061) |

- CORE örtüşmeli tüm olaylar (bilgi): 268 olay +0,295R; tek-poz zinciri 106 işlem +0,227R. QB dondurulmuş stopsuz hâli: n 1.382,
  +0,075 ATR1h, +11,08 bp — [09_events.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/logs/09_events.log)
- OF02'nin ortR'si pozitif ama ortalama bp'si −33: 2020-03-13 COVID çöküşündeki tek işlem −625 bp (SL 300 $ ≈ 62 bp; ATR'ye bağlı geniş stop),
  2021-05-19 −184 bp; R ölçeği bunları SL birimine indiriyor — [portfolio_trades.pkl](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/portfolio_trades.pkl)
- Gölge vetolarının IND'de sildikleri (bilgi; portföy vetosuz): X04 V3 62 işlem ort −0,138R, QB V2 35 işlem +0,100R —
  [vetoes.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/results/vetoes.csv)

### Inferences
- **X04 düştü:** POST'ta zaten "DISC-seçili, POST'ta sönümlü" (+0,035) olan kol bağımsız dönemde −0,013R, plasebo %60 → QQQ açılış
  boşluğu tersine gitme etkisi 2017–2021'de yok. P-PRE'nin bağımsız başarısı X04'e rağmen; X04 portföyden çıkarılsa P-PRE büyürdü (ama bu
  çıkarım sonuca bakılarak yapılır → ileri gölgede ayrıca sınanmalı, burada portföy tanımı değiştirilmez).
- **CORE ve MAX10 (trend/kırılım long'ları) bağımsız dönemde POST'tan daha güçlü** (CORE +0,227 vs +0,110; MAX10 +0,073 vs +0,029); ikisi de
  2018 ayısında negatif, boğa yıllarında pozitif → beklenen trend-takip profili. Plasebo MAX10 için %98 (aynı yıl rastgele gün), CORE için %69.
- **CAPREV-RV** ilk bağımsız sınavında işaretini korudu (+0,236R) ama A yarısı (2018–2019) ≈0 (+0,025), kazancın tamamı 2020-03 ve 2021
  çöküş-dönüşlerinde; n 46 → C'den en fazla B−'ye.
- **DV04c**'nin "geçersiz" sınıfı doğrulandı (bağımsız −0,029R, 1/6). OF02'nin 15 işlemi hiçbir yöne hüküm taşımıyor.

### Gaps
- OF02/DV04c için perp arşivi 2020-01'den önce yok; bu iki kolun bağımsız örneklemi 17 ay ile sınırlı.

---

## Bağımsız dönem hükmü

### Takeaway
**Ön-kayıtlı H1: P-PRE TUTUYOR.** IND (2017-08-17 → 2021-05-31) n 2.123, ortR **+0,039** (> 0), gün-bloklu P(EV>0) **%99,9** (≥ %90),
kart **6/6** (≥ 4/6). İki alt pencerede ve 5 yılın 4'ünde pozitif; POST ile tutarlı. **Ama:** (i) kenar ~2 spread kadar ince ve
başabaş RT maliyeti ≈10 bp — sabit 15 $ modelinde negatif; (ii) en iyi 20 gün hariç +0,005R; (iii) X04 kolu çöktü, kenarı CORE+MAX10+QB
taşıyor; (iv) kanıt sınıfı yükselir ama canlıya geçiş hâlâ 2. KURAL kartı + broker icra ölçümü (spread/kayma/swap) ister.

### Cited Findings
| H | birim | kural | sonuç | hüküm |
|---|---|---|---|---|
| H1 | P-PRE (IND) | ortR > 0 ∧ P ≥ %90 ∧ kart ≥ 4/6 | +0.039, 0.999, 6/6 | **TUTUYOR** |
| H2 | S1 CORE | ortR > 0 ∧ P ≥ %90 | +0.227, 0.960 (kart 5/6, n 106) | tutuyor |
| H2 | S2 MAX10 | " | +0.073, 0.995, 6/6 | tutuyor |
| H2 | S3 QB | " | +0.031, 0.997, 6/6 | tutuyor (maliyet-hassas, başabaş ~7,5 bp) |
| H2 | S4 X04 | " | −0.013, 0.370, 1/6 | **TUTMUYOR** (işaret döndü) |
| H2 | S5 CAPREV-RV | " | +0.236, 0.936, 5/6 (n 46) | tutuyor (n küçük, A yarısı ≈0) |
| H2 | S6 OF02 | " | +0.146, 0.735, 2/6 (n 15) | teyit yok (n yetersiz) |
| H2 | S7 DV04c | " | −0.029, 0.289, 1/6 | tutmuyor |
| H3 | P-ALL−DV (IND / PERP) | H1 kuralı | +0.044 / +0.048; 1.000 / 0.988; 6/6 / 6/6 | tutuyor |
| H3 | P-ALL (IND / PERP) | H1 kuralı | +0.030 / +0.017; 0.978 / 0.772; 6/6 / 4/6 | IND tutuyor, PERP zayıf |
| tutarlılık | P-PRE IND vs POST GA [−0.004, +0.057] | önceden ilan | +0.039 içeride | tutarlı |

### Inferences
- Pratik sonuç: 08 notundaki "GÖLGE + ileri sınama" önerisi **güçlenir, değişmez**. Bağımsız dönem, P-PRE'nin sinyal kenarının
  2017–2021 rejiminde de var olduğunu gösterdi; ileri gölgenin asıl sorusu artık "kenar var mı?"dan çok "**gerçek broker maliyeti ~2 bp mı,
  yoksa 7–10 bp'ye mi yakın?**" sorusudur (özellikle QB'nin RO+1 dakikasında). 08'deki GO kuralı (vi) bunu zaten ölçüyor.
- Kol bazında: X04 ileri gölgede "durdurma" adayıdır (bağımsız dönemde de kenar yok); CAPREV-RV log-kolu olarak kalmayı hak etti.

### Gaps
- 1. KURAL (Evrim Paneli oturum notu/backlog) ve 3. KURAL (defter satırları) yazma kısıtı yüzünden bu ajan tarafından yapılmadı.
  Önerilen backlog: "P-PRE gölge: X04 durdurma kuralı n=50/100 bakışında öncelikli izlenmeli" (decision, medium) · "BTC CFD gerçek RT maliyeti
  ve RO+1 spread ölçümü (QB başabaşı ~7,5 bp)" (experiment, high).

---

## Kol tablosu (özet)

| kol | ön-kayıtlı? | IND n | IND ortR | P(EV>0) | kart | POST (08) ortR | bağımsız işaret | not |
|---|---|---|---|---|---|---|---|---|
| S1 CORE | evet (DISC-seçili) | 106 | +0.227 | 0.960 | 5/6 | +0.110 | + | n<150; 2018 −1,02 (n 6) |
| S2 MAX10 | evet | 281 | +0.073 | 0.995 | 6/6 | +0.029 | + | 2018 −0,02 |
| S3 QB | evet | 1382 | +0.031 | 0.997 | 6/6 | +0.016 | + | +9,9 bp; başabaş ~7,5 bp RT |
| S4 X04 | evet | 354 | −0.013 | 0.370 | 1/6 | +0.035 | **−** | plasebo %60 |
| S5 CAPREV-RV | hayır (post-hoc) | 46 | +0.236 | 0.936 | 5/6 | +0.245 | + | ilk bağımsız sınav; 2018–19 ≈0 |
| S6 OF02 | hayır (post-hoc) | 15 | +0.146 | 0.735 | 2/6 | +0.205 | (+) | n yetersiz; perp 2020+ |
| S7 DV04c | hayır (geçersiz) | 526 | −0.029 | 0.289 | 1/6 | +0.273 | − | "geçersiz" teyit |

---

## Defter satırı taslağı (`docs/KAPI_KAYIT_DEFTERI.md` §2.11'e; biçim §6; kanıt kökü `research/btc_indep_2017_2021/`)

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-IND01 | 2026-10-22 | **P-PRE (CORE+MAX10+QB+X04) dondurulmuş, bağımsız dönem tek seferlik sınavı** — Binance spot 1m 2017-08-17 → 2021-05-31, aynı motor/maliyet (1,85 bp RT), ön kayıt `prereg.md` | n 2.123, **+0,039R (+14,8 bp)**, P %99,9 [+0,013; +0,065], kart 6/6, plasebo %100 (ort +0,005); A +0,042 / PERP +0,035; yıllar 17k +0,064 · 18 −0,026 · 19 +0,090 · 20 +0,051 · 21k +0,005; en iyi 20 gün hariç +0,005; sabit 15 $ −0,042. POST ile tutarlı. Kanıt `results/cards_table.csv` | B− → B (sinyal kenarı bağımsız teyitli; kârlılık maliyete koşullu, GÖLGE sürer) |
| BTC-IND02 | 2026-10-22 | P-PRE maliyet taraması (% RT 1,85…20 bp, EK-2, ön-kayıtsız) | başabaş ≈ **10 bp RT** (P-PRE), QB ≈ 7,5 bp, CORE/MAX10 20 bp'de pozitif; P ≥ %90 ancak ≤ 5 bp'de. Kanıt `results/cost_sweep.csv` | A (olgu: maliyet hassasiyeti) |
| BTC-IND03 | 2026-10-22 | CORE (BTC-T03) tek-poz, bağımsız dönem | n 106 +0,227R, P %96, kart 5/6 (n<150), plasebo %69; 2018 −1,02 (n 6); örtüşmeli 268 olay +0,295 | B (bağımsız teyit, n küçük) |
| BTC-IND04 | 2026-10-22 | MAX10 (BTC-T02), bağımsız dönem | n 281 +0,073R (+64,6 bp), P %99,5, 6/6, plasebo %98; 2018 −0,02 | B |
| BTC-IND05 | 2026-10-22 | QB (BTC-M02, 2×ATR1h felaket stoplu), bağımsız dönem | n 1.382 +0,031R (+9,9 bp), P %99,7, 6/6, plasebo %100 (aynı gün rastgele saat); stopsuz +11,1 bp; başabaş ~7,5 bp RT; sabit 15 $'da negatif | B− (maliyet-hassas) |
| BTC-IND06 | 2026-10-22 | X04 QQQ boşluk tersi, bağımsız dönem | n 354 **−0,013R** (−12,7 bp), P %37, 1/6, plasebo %60; yalnız 2019 pozitif | X (bağımsız dönemde kenar yok) |
| BTC-IND07 | 2026-10-22 | CAPREV-RV D0 (post-hoc), ilk bağımsız sınav | n 46 +0,236R, P %93,6, 5/6, plasebo %92; 2018–19 (n 24) +0,025, 2020–21 (n 22) +0,467 | C → B− |
| BTC-IND08 | 2026-10-22 | OF02 W15 θ5 + DV04c-U b3 (perp 2020-01 → 2021-05) | OF02 n 15 +0,146 (P %74; karar yok); DV04c n 526 −0,029 (P %29, 1/6) | OF02 C (belirsiz) / DV04c X |
| BTC-IND09 | 2026-10-22 | P-ALL−DV / P-ALL bağımsız dönem | P-ALL−DV +0,044 P %100 6/6 (PERP +0,048, 6/6); P-ALL +0,030 6/6, PERP +0,017 4/6 (DV04c −15,3R) | C (post-hoc kollar içerir; bilgi) |

---

## Yeni yöntem tuzakları

### Takeaway
Dört öneri (numara koordinatöre; "E-IND" öneki).

### Cited Findings
| öneri | Tuzak | Vaka | Önlem |
|---|---|---|---|
| E-IND1 | **Binance spot 1m arşivinde dakika-dışı açılış damgaları**: bakım sonrası bloklarda `open_time` dakikaya hizalı değil; `ts` ile ızgara birleştirmesi bu barları sessizce "eksik" sayar, `//60` tabanlayan yollar ise sayar → iki hat farklı veri görür | 2017-12-04 → 12-18 (+20,799 s, 20.401 bar), 2018-02-09 → 02-10 (+14,789 s, 1.201 bar); tabanlamada 1 çakışma | inşada `ts == ts.floor('1min')` iddiası; değilse tabanla + çakışmayı raporla (`02b_floor_offgrid.py`) |
| E-IND2 | **Arşiv başlangıcını varsayma**: UM perp klines arşivi borsa açılışında (2019-09) değil 2020-01'de başlıyor; metrics 2020-09 | ön kayıt öncesi S3 listesiyle yakalandı | ön kayıttan önce S3 listesini al, kolların etkin başlangıcını ondan yaz |
| E-IND3 | **Bugünün maliyet modelini geçmiş döneme uygulamak** sınavı "sinyal kenarı" sınavına çevirir, "o dönemde kâr ederdi" sınavına değil; sabit-$ modeli düşük fiyat yıllarında işareti tersine çevirir | P-PRE % modelinde +0,039, sabit 15 $'da −0,042 (2018 −0,122) | bağımsız dönem kartını daima başabaş RT maliyetiyle (tarama) birlikte raporla; hükmü "maliyet ≤ X bp ise" diye koşullu yaz |
| E-IND4 | **Long-ağırlıklı portföyü boğa ağırlıklı bağımsız dönemde sınamak** drift'i kenar sanma riskidir (BTC 2017-08 → 2021-05 ≈ 8,6×; P-PRE %90 long) | aynı-yıl/aynı-saat plasebo ort +0,005 vs gerçek +0,039; 2018 ayısında −0,026 | plaseboyu aynı takvim yılı içinde çek (yapıldı) ve ayı yılını ayrı raporla; drift'i kontrol etmeyen "bağımsız teyit" kabul etme |

### Inferences
- Bu turun yöntem dersi: bağımsız dönem sınavı ancak **(a) kodun birebir taşındığı kanıtlanırsa** (SHA256 + yalnız-sabit fark dosyası + kaba
  döngü) ve **(b) sonuç maliyet/drift bağlamıyla birlikte** verilirse karar değeri taşır; "6/6 geçti" tek başına yanıltıcı olurdu.
