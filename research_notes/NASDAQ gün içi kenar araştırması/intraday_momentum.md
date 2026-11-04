# Piyasa gün içi momentumu (market intraday momentum) — NASDAQ-100 (NDX / Pepperstone NAS100) + DAX sınaması

Kısa sonuç: Literatürün ana bulgusu (günün o ana kadarki getirisi son 30 dakikayı tahmin eder) bizim NAS100 verimizde
2021–2026 arasında **yok**. Ana hipotez P1 canlıya alma kartında **1/6** aldı → **RED**. Son 60 dakikaya ait daha zayıf
bir istatistiksel iz var (10 yıllık regresyonda t = 6,2), ama işlem başına kazanç maliyetten sonra sıfıra yakın.
Yüksek VIX kovası (5/6) da bağımsız sınamalardan geçmedi: icra ölçütü, DAX ve yıl kuralı.

Kod ve çıktılar: `research/nasdaq_derin_20261013/intraday_momentum/`
- Ön kayıt: `PROTOCOL.md`. Sonuçtan önce yazıldı. Ek-1 yalnız saat ekseni düzeltmesidir ve yine sonuçtan önce eklendi.
- Ortak çekirdek: `imcore.py`
- Betikler:
  - `run_0_axis.py`: saat ekseni
  - `run_1_discovery.py`: keşif ve kart
  - `run_2_supp.py`: brüt, VIX kovası kartı, post-hoc
  - `run_3_lockbox_dax.py`: kasa ve DAX
  - `run_4_posthoc.py`: 15:00 dilimi
  - `diag_sources.py`: 30m ve 1m kaynak tutarlılığı
- Sonuç dosyaları: `results/kesif.json`, `kesif_ek.json`, `kasa_dax.json`, `posthoc_1500.json`, `regresyon_saglamlik.txt`
  ve `*_stdout.txt`.

Yöntem özeti (ön kayıtlı):
- **Veri:** NDX 30m 2021-06-29 → 2026-06-30 (1.246 gün), NDX 1h 2016-05-31 → 2026-06-30 (2.428 gün),
  NDX 1m 2025-01-02 → 2026-06-30 (335 gün).
- **Giriş ve çıkış:** Giriş, karar barından sonraki barın açılışıdır (1m'de sonraki 1m açılışı). Çıkış 16:00 ET kapanışıdır.
- **Maliyet:** işlem başına 1,5 puan (stres testinde ×1,5).
- **R birimi:** R = puan / (giriş × dvol). dvol, NDXCASH günlük getirisinin önceki güne kadarki 20 günlük std'sidir
  (CAPREV kartıyla aynı "1× günlük oynaklık" birimi). 2025–26'da 0,01R ≈ 3 puan.
- **Tabanlar:** aynı pencerede hep-AL ve işaret permütasyonu (2.000 karıştırma). İkincil hipotezlerde Holm düzeltmesi.
- **Bağımsız sınamalar:** kasa (2026-07-01 → 09-30) bir kez açıldı. DAX bağımsız piyasa olarak kullanıldı.

---

## 1. Literatür tam olarak ne buluyor? (örneklem, etki büyüklüğü, R², yayın sonrası, piyasalar, oynaklık, gamma/LETF)

### Takeaway
Etki ABD endekslerinde 1993–2020 arasında istatistiksel olarak güçlü. Etki büyüklüğü şöyle:
- R² %1,6–4,7.
- NQ'da rest-of-day (gün içi kalan) sinyaliyle R² %4,1, örneklem dışı R² %3,8.
- Yüksek oynaklıkta ve negatif dealer-gamma günlerinde yoğunlaşıyor; pozitif gamma günlerinde yok.

Yayın sonrası kanıt zayıflama yönünde ve maliyetler hakemli makalelerin çoğunda ya yok ya kaba.

### Cited Findings
**Gao, Han, Li & Zhou (2018, JFE 129:394–414) — SPY ve 10 ETF**
- Örneklem SPY 1993–2013. "İlk yarım saat" getirisi **önceki günün 16:00 kapanışından 10:00'a** kadar ölçülüyor, yani
  geceyi de içeriyor (bizim S1 = r_ONFH). Eğim ×100 = 6,94, R² = %1,6. İkinci-son yarım saat (r12) tek başına R² %1,1,
  ikisi birlikte %2,6.
  — [Gao+ çalışma kâğıdı, Ara 2015](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf);
  yayın künyesi: [WUSTL profil](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)
- Kriz dönemi (2007-12 → 2009-06): eğim 13,6, R² %4,1, iki sinyalle %6,9. Kriz günleri çıkarılınca r1'in R²'si %0,8'e
  düşüyor. — [Gao+](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Örneklem dışı R² %1,2 (r1), iki sinyalle %1,8. — [Gao+](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Oynaklık etkisi: ilk-30 dk oynaklık tertillerinde R² düşük/orta/yüksek = %0,6 / %1,0 / %3,3. Örneklem dışı zamanlama
  getirisi yıllık %0,54 / %4,75 / %14,73. — [Gao+](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- η(r1) zamanlama stratejisi: yıllık %6,67, std %6,19, Sharpe 1,08. Maliyet sonrası (2001 ondalıklaşması sonrası)
  %7,96'dan %6,52'ye iniyor. — [Gao+](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- **QQQ (1999–2013):** örneklem içi R² %1,43, örneklem dışı R² %0,70 (10 ETF arasında en düşük), yıllık %7,75, std %7,89.
  — [Gao+ Tablo 12](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)

**Baltussen, Da, Lammers & Martens (2021, JFE 142:377–403) — 60+ vadeli, 1974–2020**
- Sinyal r_ROD = önceki kapanış → kapanıştan 30 dk önce. Hedef son 30 dk. Hisse endeksi vadelilerinde havuzlanmış
  β_ROD = 4,18 (t = 7,29), R² %2,45, örneklem dışı R² %2,88. Gao tipi r_ONFH tek başına R² %1,49 ama örneklem dışı R²
  **−%1,71**. — [Baltussen+ 2021](https://academicweb.nd.edu/~zda/intramom.pdf)
- **NQ (1996-04-12 → 2020-05-01, 6.017 gün):**
  - β_ONFH = 7,45 (R² %2,01, örneklem dışı %1,83)
  - β_ROD = 6,36 (t = 7,97, R² %4,10, örneklem dışı %3,76)
  - NDX endeksi 1997–2020: β_ROD 6,69, R² %4,74
  — [Baltussen+ Tablo B1/C](https://academicweb.nd.edu/~zda/intramom.pdf)
- Alt dönemler (hisse): 1974–1999 β_ROD 5,96 (R² %3,41); 2000–2020 β_ROD 3,98 (R² %2,34). Etki iki yarıda da var ama
  ikinci yarıda daha küçük. — [Baltussen+ Tablo 5](https://academicweb.nd.edu/~zda/intramom.pdf)
- Strateji (hisse 1/N, maliyetsiz):
  - η(ROD): yıllık %6,86, std %3,96, Sharpe 1,73, isabet %55
  - η(ONFH, ROD) aynı işaretli: Sharpe 1,60, isabet %61
  - Son 30 dk hep-AL: yıllık %0,44, Sharpe 0,11

  Maliyet hesaba katılmamış. Yazarlar yalnızca "S&P 500 vadelisinde 1 tick maliyetle net Sharpe pozitif" diyor.
  — [Baltussen+ Tablo 6 ve §3.5](https://academicweb.nd.edu/~zda/intramom.pdf)
- **Gamma kanalı:** S&P 500 opsiyon dealer'larının net gamma'sı (NGE, 1996–2020). NGE ≥ 0 günlerinde β_ROD 0,82, R²
  %0,05 (etki yok). NGE < 0 günlerinde β_ROD 6,63 (***), R² %3,58. Örneklemde 2.930 negatif, 3.158 pozitif NGE günü var.
  — [Baltussen+ Tablo 7](https://academicweb.nd.edu/~zda/intramom.pdf)
- **LETF kanalı:** Cheng & Madhavan'ın (2010) tahminine göre LETF yeniden dengelemesi, piyasa %1 (%5) hareket ettiğinde
  kapanış emri hacminin %16,8'ini (%50,2'sini) oluşturuyor. LETF hedge talebi kesitte ve zamanda etkinin büyüklüğünü
  açıklıyor. Son 30 dakikanın öngörülebilirliği sonraki günlerde tersine dönüyor (geçici fiyat baskısı). 16:00 sonrası
  vadeli getirisine taşınmıyor. — [Baltussen+](https://academicweb.nd.edu/~zda/intramom.pdf)

**Eleştiriler ve ters kanıt**
- Ivanov & Lenkey (2018, JFM): 2006–2014 ABD hisse LETF'lerinde sermaye akımları yeniden dengeleme talebini büyük ölçüde
  dengeliyor. Akımlar hesaba katılınca kapanış getirisi ve oynaklık üzerindeki etki ekonomik olarak önemsiz.
  — [IDEAS](https://ideas.repec.org/a/eee/finmar/v41y2018icp36-56.html)
- Rosa (2022, J. Futures Markets): geceden son yarım saate (overnight → LH) öngörülebilirlik **örneklem dışında
  kayboluyor**. Eşikli (yalnız güçlü sinyal) strateji her gün işlem yapandan iyi.
  — [IDEAS](https://ideas.repec.org/a/wly/jfutmk/v42y2022i12p2218-2234.html)
- Zhang & Hua (2024, Risks 12(11):180): 2007–2018 ve 2022–2024 ABD verisinde gece etkileri ve gün içi momentum
  zamanla zayıflamış (büyüklük özette verilmiyor). — [IDEAS](https://ideas.repec.org/a/gam/jrisks/v12y2024i11p180-d1519783.html)
- S&P 500 ve CSI 300 çalışması (2021): ilk yarım saat son yarım saati tahmin ediyor, ama pandemi şokunda etki anlamsız.
  — [ZČU](https://dspace5old.zcu.cz/handle/11025/46501?locale=en)
- Li, Sakkas & Urquhart (2022, JFM): 16 gelişmiş piyasada gün içi zaman serisi momentumu çoğu ülkede örneklem içinde ve
  dışında anlamlı. Düşük likidite, yüksek oynaklık ve kesikli haber akışında daha güçlü.
  — [IDEAS](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html)
- Uygulayıcı tarafı (farklı tasarım): Zarattini/Aziz/Barbon (2024) SPY "noise area" kırılım momentumu, 2007–2024 başı,
  net Sharpe 1,33 ve yıllık %19,6. Strateji yazarları/tanıtıcıları tarafından raporlanmış; bağımsız tekrar bulamadım.
  — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy)

### Inferences
- Literatürde "ilk 30 dk" çoğunlukla geceyi içerir (Gao). Baltussen'e göre de asıl sinyal ROD'dur. Yalnız ilk 30 dakikayı
  (09:30–10:00, gecesiz) kullanmak literatürün en zayıf varyantıdır.
- Mekanizma gamma ve LETF hedge'i ise etki rejime bağlıdır: negatif dealer gamma ve yüksek oynaklık günlerinde var,
  pozitif gamma'da yok. 2023 sonrası 0DTE opsiyon hacmi ve dealer gamma konumu değiştiyse etki de değişmiş olabilir.
  Bunu doğrudan ölçemedik.

### Gaps
- Baltussen+ ve Gao+ için 2020 sonrası örneklem dışı güncelleme bulamadım. NQ/QQQ için 2021–2026 hakemli tekrar da yok.
- Zhang & Hua 2024'ün 2022–2024 büyüklüklerini tam metne erişmeden alamadım.
- Lenkey 2024 derlemesinin ayrıntıları yalnız arama özetinden görüldü; doğrudan atıf yapılmadı.

---

## 2. Bizim NDX verimizde ilk 30 dk (+gece) / ROD son 30 ve son 60 dakikayı tahmin ediyor mu? (maliyet sonrası, tabana karşı)

### Takeaway
**Son 30 dakika için hayır.** Hiçbir sinyal maliyet sonrası pozitif değil ve hep-AL tabanını geçen yok:
- P1 (ROD → 15:30–16:00): ortR −0,012
- Gao sinyali: ortR −0,020

**Son 60 dakikada zayıf bir iz var:**
- 10 yılda tabanı +0,014R geçiyor (permütasyon p = 0,067).
- Brüt +2,2 bp/işlem, ama maliyet sonrası ortR −0,007.
- Regresyon t = 6,2 olsa da etki birkaç uç güne ve yıla (2020, 2022, 2023) dayanıyor.

### Cited Findings
**Saat ekseni** — [run_0_axis.py, results/axis_check.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/axis_check.txt)
- NDX 1m ve 30m'de her yıl en büyük medyan bar aralığı 09:30 ET'de. 1m'de 2025 Şubat–Nisan aylarında tepe 10:00'da
  (makro veri saati).
- CFD 16:00 kapanışı NDXCASH kapanışına aylık medyan farkla en yakın: 30m'de 64/64 ay, 1m'de 20/20 ay.
- 1h uzun veride 2017-12 → 2018-02 etiketleri 60 dk geç bulundu. O kış (2017-11-05 → 2018-03-11) sonuçlara bakılmadan
  çıkarıldı (PROTOCOL Ek-1).

**Keşif sonuçları (NY tarihi < 2026-07-01, maliyet 1,5 puan)** — [results/kesif.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| ID | sinyal → pencere | veri | n | ortR | puan | WR | P(EV>0) | 1./2. yarı | hep-AL ortR | fark | perm p | Holm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P1** | ROD (önc. 16:00→15:30) → 15:30–16:00 | 30m 2021–26 | 1233 | **−0,0120** | −2,41 | %47,9 | 0,036 | −0,002/−0,022 | −0,005 | −0,007 | 0,75 | — |
| S1 | ONFH (önc. 16:00→10:00, Gao) → LH | 30m | 1231 | −0,0196 | −3,23 | %47,4 | 0,003 | −0,035/−0,004 | −0,005 | −0,015 | 0,97 | 1,0 |
| S2 | yalnız ilk 30 dk (09:30→10:00) → LH | 30m | 1244 | −0,0200 | −3,40 | %46,1 | 0,001 | −0,023/−0,017 | −0,005 | −0,015 | 0,97 | 1,0 |
| S3 | ONFH ve ROD aynı işaret → LH | 30m | 921 | −0,0184 | −3,26 | %47,4 | 0,007 | — | −0,004 | −0,015 | 0,93 | 1,0 |
| S4 | geç gün 12:00→15:30 → LH | 30m | 1243 | −0,0164 | −3,51 | %47,1 | 0,007 | −0,009/−0,024 | −0,005 | −0,012 | 0,91 | 1,0 |
| S5 | SLH 15:00→15:30 → LH | 30m | 1241 | +0,0013 | 0,00 | %48,7 | 0,58 | +0,008/−0,006 | −0,005 | +0,006 | 0,09 | 0,54 |
| S6 | ROD60 (önc. 16:00→15:00) → 15:00–16:00 | **1h 2016–26** | 2407 | −0,0067 | +0,97 | %49,4 | 0,16 | −0,020/+0,007 | −0,021 | **+0,014** | 0,067 | 0,47 |
| S7 | ONFH → 15:00–16:00 | 1h | 2405 | −0,0178 | −0,95 | %48,2 | 0,003 | — | −0,021 | +0,004 | 0,56 | 1,0 |
| S6 | ROD60 → 15:00–16:00 | 30m 2021–26 | 1234 | +0,0046 | +1,49 | %51,5 | 0,70 | +0,023/−0,013 | −0,012 | +0,016 | 0,077 | — |

**Brüt (maliyetsiz)** — [results/kesif_ek.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif_ek.json)

| ID | brüt ortR | brüt bp | P(EV>0) |
|---|---|---|---|
| P1 | −0,0043 | −0,18 | — |
| S1 | −0,0119 | — | — |
| S2 | −0,0124 | — | — |
| S5 | +0,0089 | — | 0,91 |
| S6 (1h) | +0,0096 | +2,20 | 0,93 |
| S6 (30m) | +0,0123 | — | 0,91 |

- Maliyetin R karşılığı yıllara göre (N1h medyan): 2016'da 0,041, 2017'de 0,049, 2020'de 0,009, 2025'te 0,0056.
  Endeks seviyesi yükseldikçe 1,5 puanın R karşılığı küçülüyor.

**1m tekrar (2025-01 → 2026-06)** — [results/kesif.json "1m"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| ID | n | ortR | puan | perm p |
|---|---|---|---|---|
| P1 | 296 | −0,0122 | −4,98 | 0,74 |
| S1 | 288 | +0,0058 | — | 0,23 |
| S2 | 308 | +0,0044 | — | 0,24 |
| S4 | 308 | −0,0348 | — | — |
| S5 | 316 | −0,0017 | — | — |
| S6 | 295 | +0,0077 | — | 0,22 |

- 30m ve 1m kaynakları çakışan 335 günde tutarlı: son 30 dk getirisi korelasyonu 0,999.
  — [diag_sources.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/diag_sources.py)

**Regresyon (literatür ölçeğinde, ×100, maliyetsiz getiri)** — [results/regresyon_saglamlik.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/regresyon_saglamlik.txt)

| Kapsam | b×100 | t | R² | Not |
|---|---|---|---|---|
| ROD → LH, 30m 2021–26 | 0,40 | 0,64 | %0,03 | Baltussen NQ: 6,36 / R² %4,10 |
| ONFH → LH | −1,32 | −1,45 | — | — |
| SLH → LH | 14,72 | 4,5 | %1,6 | 2021 korelasyon 0,32, 2022'de 0,28, 2023–25'te ~0; Spearman 0,035 |
| ROD60 → L60, 1h 2016–26 | 4,28 | 6,16 | %1,55 | — |
| ROD60 → L60, 2016–20 | 6,20 | — | %2,69 | — |
| ROD60 → L60, 2021–26 | 2,92 | — | %0,85 | — |
| ROD60 → L60, 2020 hariç | 2,52 | 3,8 | — | — |
| ROD60 → L60, %1 kırpılmış | 2,64 | 4,26 | — | Spearman 0,058 |

- ROD60 → L60 yıllara göre eğim: pozitif 6/11 yıl (2018, 2020, 2022, 2023, 2025, 2026), negatif 5/11.
- ROD → LH yıllara göre (30m): yalnız 2022'de pozitif ve anlamlıya yakın (t = 1,79).

**Saat plasebosu.** Sinyal önceki 16:00 → t, işlem t → t+30 (N30). 10:30–15:30 arasındaki 11 dilimin ortR'si −0,024 ile
+0,015 arasında. Yalnız **15:00–15:30** dilimi anlamlı (+0,015, perm p ≈ 0). Asıl literatür penceresi 15:30–16:00 ise
−0,012. — [results/kesif.json "saat_plasebosu_N30"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

**Post-hoc 15:00 dilimi (ön kayıt dışı).** — [results/posthoc_1500.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/posthoc_1500.json)
- Keşif: 30m +0,0150 (P 0,996), 1m +0,0177.
- Kasa: 30m −0,0083, 1m −0,0074.
- DAX karşılığı (16:30–17:00): −0,0050 (P 0,18).

Sonuç: dilim tutmuyor.

**Post-hoc sürekli pozisyon** (sinyal/dvol, ±2): P1 −0,015, S1 −0,017, S6 −0,001 → regresyon eğimi işlem kazancına
dönüşmüyor. — [results/kesif_ek.json "POSTHOC_surekli"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif_ek.json)

### Inferences
- Literatürün ana etkisi (ROD → son 30 dk) Pepperstone NAS100'da 2021–2026'da yok. Eğim Baltussen NQ'nun ~1/16'sı,
  R² %0,03. İşaret stratejisinin brüt getirisi bile negatif (−0,18 bp). Yayın sonrası (2018/2021) zayıflama literatürle
  tutarlı (Rosa 2022, Zhang & Hua 2024).
- Son 60 dakikada momentum izi daha kalıcı ama küçük ve kuyruk bağımlı. Sıralama korelasyonu yalnız 0,058, 10 yılın
  ancak 6'sında eğim pozitif. Brüt ~2 bp/işlem; 1,5 puan maliyet NDX ~24.000'de ~0,6 bp. Net beklenti 2021–26 30m'de
  +0,005R (≈1,5 puan), P = 0,70.
- Gecesiz "ilk 30 dk" (S2) ve Gao sinyali (S1) en kötüleri: tabanın 0,015R altında. "İlk 30 dk son 30 dk'yı tahmin eder"
  önermesi bizim veride çürük.
- Hep-AL son 30/60 dk tabanı 10 yılda maliyet yüzünden negatif (−0,005 / −0,021R). Brüt olarak +0,003 / −0,005R:
  NDX sürüklenmesi kapanışa yığılmıyor.

### Gaps
- 1m verisi yalnız 2025-01 → 2026-06 (2026-01-01 → 02-10 boşluk) olduğundan 10 yıllık LH (15:30–16:00) ölçülemedi. 1h veri
  09:30 ve 15:30 sınırlarını çözemiyor, bu yüzden 10 yıl yalnız son 60 dk için var.
- Dealer gamma (NGE), 0DTE hacmi ve LETF varlıkları verisi yok. Literatürün mekanizma koşulu sınanamadı.
- Pepperstone gerçek spread'i kapanış dakikalarında 1,5 puandan geniş olabilir; ölçülmedi.

---

## 3. Yüksek oynaklık günlerinde (VIX ≥ 18,4, yüksek ilk-30 aralığı) etki güçleniyor mu? (ön kayıtlı bölmeler)

### Takeaway
Son 30 dakikada (P1, S1) hayır: yüksek VIX ve yüksek ilk-30 aralığı kovalarında da negatif. Güçlü sinyal kovası en kötüsü.
Son 60 dakikada (S6) yalnız VIX ≥ 18,4 kovası literatürle uyumlu:
- +0,0175R, P 0,944, tabana fark +0,032, perm p 0,009.

Ama bu kova bağımsız sınamaları geçmiyor (bkz. 4 ve 5).

### Cited Findings
**P1 kovaları** — [results/kesif.json "bolmeler"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| Kova | n | ortR | P(EV>0) |
|---|---|---|---|
| VIX ≥ 18,4 | 576 | −0,0100 | 0,17 |
| VIX < 18,4 | 657 | −0,0137 | — |
| İlk-30 aralığı üst tertil (nedensel) | 356 | −0,0125 | — |
| Güçlü sinyal (abs(ROD) ≥ dvol) | 399 | −0,0266 | — |

**S1 kovaları** — [results/kesif.json "bolmeler"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| Kova | n | ortR |
|---|---|---|
| VIX ≥ 18,4 | 576 | −0,0206 |
| İlk-30 aralığı üst tertil | — | −0,0152 |
| Güçlü sinyal | 201 | −0,0561 |

**S6 kovaları (1h, 10 yıl)** — [results/kesif.json "bolmeler"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| Kova | n | ortR | P(EV>0) | 1./2. yarı | hep-AL ortR | perm p |
|---|---|---|---|---|---|---|
| VIX ≥ 18,4 | 984 | +0,0175 | 0,944 | +0,020/+0,015 | −0,014 | 0,009 |
| VIX < 18,4 | 1423 | −0,0235 | — | — | — | — |
| İlk-30 aralığı üst tertil | 764 | −0,0137 | — | — | — | — |
| Güçlü sinyal | 687 | −0,0019 | — | — | — | — |

- S6 VIX alt kovaları (post-hoc ayrıntı) — [results/kesif_ek.json "S6_vix_kovalari"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif_ek.json)

  | VIX aralığı | n | ortR | hep-AL ortR |
  |---|---|---|---|
  | ≤ 15 | 812 | −0,035 | — |
  | 15–18,4 | 611 | −0,008 | — |
  | 18,4–25 | 630 | +0,019 | — |
  | 25–35 | 295 | +0,008 | — |
  | > 35 | 59 | +0,043 | +0,061 |

- S6 | VIX ≥ 18,4 çapraz kontrolleri ve uç gün bağımlılığı:
  - Yıllar: N1h'te 6/10 yıl pozitif (2018, 2020, 2021, 2022, 2023, 2025). Önceden yazılı eşik %70; bu %60.
  - 30m 2021–26: +0,0130 (P 0,82). 1m 2025–26: +0,0062 (n 134, P 0,58).
  - Toplam +17,3R'nin 7,3R'si en iyi 5 günden geliyor. En iyi 5 gün hariç +0,0102, en iyi 10 gün hariç +0,0043.

  — [results/kesif_ek.json "kart_S6_VIXhi"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif_ek.json)

### Inferences
- Literatürün yön iddiası (yüksek oynaklıkta daha güçlü) son 60 dakika için kısmen tekrarlandı. 18 ön kayıtlı kova
  (3 hipotez × 6) arasında tek pozitif ve anlamlı kova bu. Bonferroni ile p ≈ 0,16, yani seçim yükü taşıyor.
- "Güçlü sinyal" (Rosa'nın eşik fikri) ve "yüksek ilk-30 aralığı" (Gao'nun oynaklık tertili) bizde ters yönde.
  Literatürün ilk-30 oynaklığı tertil bulgusu bu veride yok.
- Bu kova projenin VIXREG bulgusuyla (OLD-10, GF-05) aynı rejim sinyaline dayanıyor. Yeni ve ortogonal bir kenar değil;
  VIX ≥ 18,4 günlerinde kapanışa doğru trend sürüyor olabilir.

### Gaps
- VIX vade yapısı, gamma ve dealer pozisyonuyla koşullandırma yapılmadı (veri yok, ön kayıtta da yoktu).

---

## 4. Kasada (2026-07-01 → 10-02) ve DAX'ta (bağımsız piyasa) tutuyor mu?

### Takeaway
Hayır:
- **Kasa:** P1 hafif pozitif (+0,008…+0,010R, n = 64, P ≈ 0,62–0,65, anlamsız). S6 negatif (−0,021…−0,023R). VIX ≥ 18,4
  olan yalnız 6 gün var, yani yüksek VIX kovası kasada sınanamıyor.
- **DAX:** son 30 dk etkisi istatistiksel olarak küçük ama var (eğim t = 3,0). Maliyet sonrası ise ≈0
  (+0,0012R, 0,17 puan). VIX ≥ 18,4'te son 60 dk kovası DAX'ta negatif (−0,0019R).

### Cited Findings
**Kasa (bir kez açıldı; makro veri 2026-09-30'da bittiği için 64 / 63 gün)**
— [results/kasa_dax.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kasa_dax.json)

| ID | veri | n | ortR | puan | P(EV>0) | perm p | hep-AL ortR |
|---|---|---|---|---|---|---|---|
| P1 | 30m | 64 | +0,0077 | +2,67 | 0,62 | 0,37 | −0,030 |
| P1 | 1m | 63 | +0,0101 | +3,27 | 0,65 | 0,34 | −0,029 |
| S6 | 30m | 64 | −0,0233 | −9,15 | 0,28 | — | — |
| S6 | 1m | 63 | −0,0207 | — | — | — | — |
| S6 \| VIX ≥ 18,4 | — | 6 | +0,010 | — | — | — | — |

- Kasa döneminde VIX medyanı 15,8, en yüksek 20,7.
  — [macro_daily_patched.csv](/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data/macro_daily_patched.csv)

**DAX (2021-03-18 → 2026-10-01, 1.413 gün, Berlin 09:00–17:30, maliyet 1,5 puan)**
- Kaynak, ABD standart saatinde 60 dk erken etiketliydi. NY yaz saati dışındaki dönemlerde +60 dk düzeltildi; düzeltme
  sonrası açılış tepesi 68/68 ayda Berlin 09:00'da (PROTOCOL Ek-1).
- Sonuçlar — [results/kasa_dax.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kasa_dax.json)

  | ID | sinyal → pencere | n | ortR | puan | P(EV>0) | perm p | Not |
  |---|---|---|---|---|---|---|---|
  | P1_DAX | önceki 17:30 → 17:00; 17:00–17:30 | 1384 | +0,0012 | +0,17 | 0,60 | 0,016 | eğim ×100 1,36, t 2,98, R² %0,64; yıllar 2/6 pozitif; kasa (n 67) −0,0435 |
  | P1_DAX \| VIX ≥ 18,4 | aynı | 608 | +0,0081 | — | 0,84 | — | — |
  | S1_DAX (ONFH) | önceki 17:30 → 09:30 | — | −0,0067 | — | — | — | — |
  | S2_DAX (09:00–09:30) | — | — | −0,0054 | — | — | — | — |
  | S6_DAX (ROD → 16:30–17:30) | — | 1383 | +0,0051 | — | 0,75 | 0,029 | — |
  | S6_DAX \| VIX ≥ 18,4 | — | 608 | −0,0019 | — | 0,44 | — | — |
  | S6_DAX \| VIX < 18,4 | — | — | +0,0106 | — | — | — | — |

### Inferences
- DAX, kapanışa doğru momentumun istatistiksel olarak var ama ekonomik olarak işlenemez olduğunu teyit ediyor. Etki
  maliyet sonrası ~0,2 puan/işlem, rastgele yönden ayırt edilebilir (perm p 0,016), tradeable değil.
- NDX'teki tek umut verici kova (S6 | VIX ≥ 18,4) DAX'ta ters işaretli. "Yüksek VIX'te son saat momentumu" bağımsız
  piyasada taşınmıyor (E23 riski gerçekleşti).
- Kasada P1'in hafif pozitif çıkması tek başına anlam taşımıyor (n = 64, P 0,62). Kasada son 30 dk hep-AL −0,03R
  olduğundan P1'in tabana farkı +0,037 görünüyor, ama keşifteki 1.233 gün bunun tersini söylüyor.

### Gaps
- Kasa 3 ay ve düşük VIX'li bir dönem; yüksek oynaklık hipotezini sınamaya yetmiyor.
- DAX spread'i 1,5 puan varsayıldı (Pepperstone GER40 tipik ~1,0–1,2), ölçülmedi. Daha düşük maliyet P1_DAX'ı pozitife
  çeker ama kartın 2. ölçütünü geçirmez (P 0,60).

---

## 5. Canlıya alma kartı (6 ölçüt) — geçiyor mu? Verdikt

### Takeaway
**P1 (ana, ön kayıtlı): 1/6 → RED.** Yalnız hacim ölçütü geçti.
**S6 | VIX ≥ 18,4 (ön kayıtlı kova): 5/6** (icra ölçütü ✗). Ek olarak:
- DAX ✗
- yıl kuralı ✗ (%60 < %70)
- kasa sınanamadı (n = 6)

Ön kayıtlı eşlemeye göre o da **RED**. Literatürdeki gün içi momentum bu projede canlı ya da gölge strateji adayı değildir.

### Cited Findings
**P1 kartı (N30 keşif 2021-06 → 2026-06)** — [results/kesif.json "kart_P1"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif.json)

| # | Ölçüt | Değer | Sonuç |
|---|---|---|---|
| 1 | Hacim | 1.233 | ✓ |
| 2 | Beklenti | ortR −0,0120, P(EV>0) 0,036 | ✗ |
| 3 | Kararlılık (iki yarı) | −0,0023 / −0,0217 | ✗ |
| 4 | Sürtünme (spread ×1,5) | −0,0158 | ✗ |
| 5 | İcra | 1m'de iyimser −0,0072 vs gerçek −0,0122; 30m'de −0,0049 vs −0,0120 (ortR ≤ 0) | ✗ |
| 6 | Tek pozisyon | günde 1 işlem, ortR −0,0120 | ✗ |

- Ek ölçüt: hep-AL farkı −0,0074, perm p 0,75 ✗.

**S6 | VIX ≥ 18,4 kartı (N1h 2016–2026)** — [results/kesif_ek.json "kart_S6_VIXhi"](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/results/kesif_ek.json)

| # | Ölçüt | Değer | Sonuç |
|---|---|---|---|
| 1 | Hacim | 984 | ✓ |
| 2 | Beklenti | ortR +0,0175, P 0,944 (20 günlük blokla 0,953), %95 GA [−0,004; +0,039] | ✓ |
| 3 | Kararlılık (iki yarı) | +0,0202 / +0,0149 | ✓ |
| 4 | Sürtünme (spread ×1,5) | +0,0133 | ✓ |
| 5 | İcra | N1h'te fark 0,0082 (< ortR/2 = 0,0088, sınırda geçer); ön kayıtlı ölçüm yeri N1m'de iyimser +0,0103 vs gerçek +0,0062, fark 0,0041 > ortR/2 = 0,0031 | ✗ |
| 6 | Tek pozisyon | — | ✓ |

- Ek: tabana fark +0,032, perm p 0,009.
- İcra farkının tamamına yakını spread'den geliyor: kenar maliyete göre ince.

**Ortak not:** Ölçütler `backend/research/go_live_gate.py` ile aynı eşiklerde. Kart JSON'u
`backend/data/evolution/go_live_cards/`'a **yazılmadı** (görev kısıtı: backend'e dokunma). Kart verisi
`research/nasdaq_derin_20261013/intraday_momentum/results/` altında.

**Defter karşılaştırması.** GF-02 H1 ("kapanış akışı", Baltussen; 15:00–15:50'de güne karşı yönü engelleyen kapı) X idi.
Bu çalışma tanımı (zamanlanmış strateji, braketsiz zaman çıkışı), veriyi (10 y 1h, 30m 5 y, DAX, kasa) ve sinyal
ailesini (Gao/Baltussen/geç gün) değiştirdi. Sonuç aynı yönde: kenar yok.
— [docs/KAPI_KAYIT_DEFTERI.md §2.5](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- **Verdikt:**
  - P1: RED.
  - S1–S7: RED. Hiçbiri Holm sonrası anlamlı değil (en düşük S6 Holm p 0,47) ve hiçbiri maliyet sonrası pozitif ve kararlı değil.
  - S6 | VIX ≥ 18,4: RED (5/6, bağımsız piyasada ters, yıl kuralı ✗).
  - Post-hoc 15:00 dilimi: kasa ve DAX'ta çöktü.
- Literatür etkisinin kaybolması için olası açıklamalar:
  - yayın sonrası arbitraj (McLean–Pontiff tipi);
  - LETF akımlarının yeniden dengelemeyi dengelemesi (Ivanov & Lenkey);
  - 0DTE dönemiyle dealer gamma konumunun değişmesi (sınanmadı).

  Bunlar gözlemle uyumlu ama ayırt edilemedi.
- Projenin meta dersleriyle uyum:
  - §3/1 "rastgele girişte durum kapısı yok": takvim ve zaman tabanlı yön sinyalleri de bu kategoride.
  - §3/5 "braket ≠ zaman": burada zaman çıkışı denendi, yine kenar yok.
  - Yüksek VIX'te son saat izi VIXREG rejim etkisinin (GF-05: ~0,01R/işlem) bir yansıması olabilir. Aynı büyüklükte ve
    aynı şekilde işlenemez.
- **Deftere önerilen satır** (§2.5'e; bu oturum backend'e/deftere yazmadı, koordinatör eklemeli):
  `| GF-23 | 2026-10-13 | Piyasa gün içi momentumu (Gao+ 2018 / Baltussen+ 2021): sign(ROD) → 15:30–16:00 ana (P1) + ONFH/ilk-30/geç-gün/SLH → LH, ROD60/ONFH → 15:00–16:00; ön kayıt research/nasdaq_derin_20261013/intraday_momentum/PROTOCOL.md | P1 30m 2021–26 1.233 gün ortR −0,012 (−2,4 p), P 0,04, taban farkı −0,007 → kart 1/6; Gao/ilk-30 −0,020; ROD→LH eğimi 0,40 (NQ literatürü 6,36); son 60 dk 10 y: brüt +2,2 bp, net −0,007R, regresyon t 6,2 ama Spearman 0,058 ve kuyruk; VIX≥18,4 kovası +0,0175R P 0,944 (5/6, icra ✗) ama DAX −0,002, yıllar 6/10, kasa n 6; DAX ROD→LH t 3,0 ama net +0,001R; kasa P1 +0,008 (n 64) S6 −0,023 | X |`
- **E listesine aday:** E27. Bu veri setlerinde iki ayrı saat ekseni hatası bulundu:
  - `ndx_gate_forge/data/dax_*.parquet` ABD standart saatinde 60 dk erken.
  - `long_1h` 2017-11 → 2018-03 60 dk geç.

  Önlem: CFD 16:00 kapanışını NDXCASH kapanışıyla aylık eşleştir; açılış tepesini ay bazında kontrol et (yıl bazında
  maskeleniyor). DAX'ı kullanan önceki sonuçlar (GF-18, GF-22 CAPREV DAX bacağı, MK-01/02 DAX) kendi düzeltmelerini
  yapmadıysa bu kaymadan etkilenmiş olabilir. **Ayrıca doğrulanmalı.**

### Gaps
- Kart JSON'u ve Evrim Paneli oturum notu (1. KURAL) görev kısıtı nedeniyle yazılmadı. Koordinatörün
  `python3 backend/scripts/evolution_session_log.py "..." --files ...` çalıştırması ve defter satırını eklemesi gerekir.
- DAX saat kaymasının CAPREV DAX bacağını (GF-22, canlı) etkileyip etkilemediği bu oturumda kontrol edilmedi. Yüksek öncelikli.
  Ek kontrol (bu oturum): aynı kayma `dax_1h.parquet` ve `dax_15m.parquet`'te de var.
  - ABD standart saatinde medyan aralık Berlin 08:00 etiketinde 80,5 puan, 09:00'da 54,4 (1h, 2021–26).
  - ABD yaz saatinde tersi: 51,3 / 90,5.

  `research/ndx_gate_forge/cross_market.py` bu dosyaları düzeltmeden `tz_convert("Europe/Berlin")` ile okuyor. GF-18 ve
  GF-22'nin DAX kanıtında, yılın ~%30'unda Xetra seans sınırları 60 dk kaymış olabilir. Canlı bot MT5'ten okuduğu için
  canlı icra muhtemelen etkilenmez; ama **kartın DAX kanıtı yeniden üretilmeli.**
