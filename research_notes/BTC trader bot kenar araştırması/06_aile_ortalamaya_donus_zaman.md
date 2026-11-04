# BTC — Ortalamaya dönüş + zaman/takvim ailesi (fam_mr_zaman): sızıntısız 5 yıllık backtest

> Kapsam: kanal-sınır dönüşü (CHREV portu), 21–23 UTC long (Quantpedia), saat/gün/hafta sonu etkileri ve ETF sonrası ABD
> saatleri, funding saati (H10), turn-of-the-candle (H11). Veri Binance BTCUSDT 1m, 2021-06-01 → 2026-10-20.
> Kaynakların hepsi yerel dosyalardır (kök: `/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/`).
> - Ön-kayıt: [prereg.md](research/btc_5y_20261021/fam_mr_zaman/prereg.md). Sonuçlardan önce yazıldı, değiştirilmedi, amendment yok.
> - Motor: [common.py](research/btc_5y_20261021/fam_mr_zaman/common.py), [run_timing.py](research/btc_5y_20261021/fam_mr_zaman/run_timing.py), [run_channel.py](research/btc_5y_20261021/fam_mr_zaman/run_channel.py), [summarize.py](research/btc_5y_20261021/fam_mr_zaman/summarize.py).
> - 110 hücrenin tamamı: [results/all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv).
>
> **Protokol özeti.** Giriş sinyal barının kapanışından sonraki 1m açılışında yapıldı. Yarım spread fiyata eklendi.
> - Spread: taban %0,0185, stres %0,028, ayrıca sabit 15 $ varyantı.
> - TP/SL 1m barlarda çözüldü. Aynı dakikada ikisi birden tetiklenirse SL sayıldı.
> - Swap rollover anında uygulandı: yaz 21:00 / kış 22:00 UTC, long −%14/365, short +%2/365.
> - Broker'ın günlük 2 dakikalık kapanışı işlem yapılamaz olarak modellendi.
> - Dönemler: KEŞİF 2021-06→2023-12, OOS 2024-01-11→2025-06, KÖR 2025-07→2026-10-20.
> - Kart TAM dönemde hesaplandı (6 ölçüt). Ek ölçütler: plasebo, KÖR işareti, OOS işareti ve çoklu sınama düzeltmesi.
> - Çoklu sınama: KEŞİF'te 110 hücre için Holm. Saat ve gün taramalarında ayrıca max-z (dairesel kaydırma).
>   Literatürden gelen 12 hücre yayın sonrası dönemde (OOS ∪ KÖR) ayrıca Holm'a sokuldu.
> - Stopsuz zaman çıkışlı kurallarda R'nin paydası nominal stop = 1×ATR14(1h). Net getiri bp olarak da raporlandı.

---

## S1. Kanal-sınır dönüşü (CHREV portu) BTC'de kenar veriyor mu?

### Takeaway
**Hayır.** 32 birincil hücreden (2 zaman dilimi × 2 tetik × 2 yön × 4 geometri) hiçbiri KEŞİF'te çoklu sınamayı geçmedi; en düşük Holm p'si 1,0. 31 hücre negatif ya da sıfır.
- **Alt banttan alım (BUY) sistematik olarak rastgele girişten kötü.** 15m RJ BUY hücrelerinin plasebo yüzdeliği %0–1,5. Yani BTC'de alt banttan almak "düşen bıçağı tutmak" oluyor.
- Tek mekanik SHADOW hücresi CH_1h_RJ_S_Gtime (+0,042R). Ancak bp cinsinden ≈ +0,3 bp. zt=2,5 sağlamlık testinde +0,009R'ye çöküyor. Bu bir kenar değil.

### Cited Findings
- **Bütün hücreler** ([channel_cells.csv](research/btc_5y_20261021/fam_mr_zaman/results/channel_cells.csv)):

| hücre | n | WR | başabaş WR | ortR | bp | P(EV>0) | KEŞİF/OOS/KÖR ortR | stres | iyimser | tek-poz | plasebo %ile | taban | kart |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15m CZ L Gbot | 4697 | .578 | .586 | −0,012 | −1,8 | .22 | −.013/−.017/−.005 | −.020 | +.002 | −.025 | 79,5 | −.022 | 1 |
| 15m CZ L Gatr | 4698 | .553 | .601 | −0,080 | −3,4 | .00 | −.075/−.069/−.102 | −.103 | −.020 | −.089 | 9,0 | −.064 | 1 |
| 15m CZ L Gtime | 4699 | .391 | .414 | −0,051 | −1,2 | .01 | −.063/−.026/−.054 | −.072 | +.004 | −.064 | 34 | −.044 | 1 |
| 15m CZ L Gmid | 4698 | .388 | .413 | −0,059 | −1,8 | .00 | −.049/−.071/−.064 | −.084 | −.002 | −.073 | 72 | −.068 | 1 |
| 15m CZ S Gbot | 4547 | .577 | .575 | +0,003 | +0,4 | .57 | +.006/+.017/−.019 | −.003 | +.014 | −.002 | 89 | −.008 | 1 |
| 15m CZ S Gatr | 4547 | .575 | .600 | −0,042 | −1,4 | .00 | −.029/−.039/−.067 | −.066 | +.007 | −.044 | 40 | −.042 | 1 |
| 15m CZ S Gtime | 4549 | .392 | .404 | −0,028 | −1,0 | .11 | −.009/−.023/−.071 | −.048 | +.021 | −.045 | 74 | −.045 | 1 |
| 15m CZ S Gmid | 4547 | .397 | .414 | −0,041 | −1,3 | .02 | −.026/−.042/−.069 | −.060 | +.015 | −.046 | 55 | −.042 | 1 |
| 15m RJ L Gbot | 7331 | .554 | .581 | −0,041 | −6,1 | .00 | −.071/−.029/+.010 | −.048 | −.031 | −.042 | **1,0** | −.022 | 2 |
| 15m RJ L Gatr | 7332 | .551 | .602 | −0,084 | −3,4 | .00 | −.082/−.090/−.081 | −.105 | −.038 | −.091 | **1,0** | −.064 | 1 |
| 15m RJ L Gtime | 7333 | .392 | .428 | −0,074 | −3,0 | .00 | −.097/−.077/−.021 | −.096 | −.034 | −.080 | **1,5** | −.044 | 1 |
| 15m RJ L Gmid | 6896 | .479 | .526 | −0,088 | −3,8 | .00 | −.092/−.092/−.077 | −.113 | −.045 | −.092 | **0,0** | −.065 | 2 |
| 15m RJ S Gbot | 6709 | .569 | .568 | +0,001 | +0,2 | .54 | +.022/−.007/−.034 | −.005 | +.013 | +.003 | 82,5 | −.008 | 2 |
| 15m RJ S Gatr | 6711 | .575 | .599 | −0,040 | −0,5 | .00 | −.026/−.023/−.088 | −.063 | +.006 | −.041 | 50 | −.042 | 1 |
| 15m RJ S Gtime | 6711 | .401 | .417 | −0,034 | −0,7 | .04 | −.038/+.005/−.070 | −.061 | +.011 | −.029 | 71 | −.045 | 1 |
| 15m RJ S Gmid | 6272 | .492 | .515 | −0,044 | −0,9 | .00 | −.027/−.036/−.089 | −.068 | −.007 | −.045 | 36,5 | −.040 | 1 |
| 1h CZ L Gbot | 1188 | .561 | .589 | −0,044 | −6,6 | .04 | −.087/+.030/−.055 | −.050 | −.036 | −.069 | 14 | −.021 | 2 |
| 1h CZ L Gatr | 1188 | .584 | .603 | −0,032 | −0,8 | .10 | −.054/+.004/−.033 | −.049 | −.012 | −.045 | 35,5 | −.022 | 1 |
| 1h CZ L Gtime | 1188 | .395 | .418 | −0,050 | −1,6 | .12 | −.092/−.006/−.028 | −.063 | −.025 | −.060 | 9 | −.007 | 2 |
| 1h CZ L Gmid | 1188 | .396 | .418 | −0,052 | −0,8 | .09 | −.081/−.004/−.057 | −.069 | −.027 | −.052 | 25 | −.032 | 2 |
| 1h CZ S Gbot | 1140 | .561 | .582 | −0,032 | −4,8 | .12 | −.070/−.022/+.031 | −.034 | −.024 | −.044 | 23 | −.007 | 2 |
| 1h CZ S Gatr | 1140 | .588 | .599 | −0,019 | −0,5 | .24 | −.057/+.015/+.017 | −.039 | +.004 | −.031 | 67 | −.022 | 1 |
| 1h CZ S Gtime | 1140 | .416 | .416 | −0,000 | +1,1 | .49 | −.045/+.043/+.036 | −.013 | +.023 | −.010 | 69 | −.022 | 1 |
| 1h CZ S Gmid | 1139 | .395 | .409 | −0,032 | −2,2 | .22 | −.093/+.006/+.042 | −.042 | −.013 | −.056 | 52 | −.038 | 1 |
| 1h RJ L Gbot | 1860 | .539 | .582 | −0,066 | −9,9 | .00 | −.093/−.018/−.073 | −.074 | −.054 | −.067 | **0,0** | −.021 | 2 |
| 1h RJ L Gatr | 1860 | .567 | .602 | −0,058 | −6,4 | .00 | −.069/−.046/−.050 | −.065 | −.038 | −.074 | 3 | −.022 | 2 |
| 1h RJ L Gtime | 1860 | .382 | .391 | −0,021 | −4,6 | .28 | −.069/+.069/−.036 | −.030 | −.002 | −.035 | 25,5 | −.007 | 1 |
| 1h RJ L Gmid | 1753 | .487 | .521 | −0,065 | −7,6 | .01 | −.075/−.037/−.080 | −.071 | −.050 | −.076 | 1,5 | −.022 | 2 |
| 1h RJ S Gbot | 1676 | .567 | .577 | −0,015 | −2,2 | .26 | −.022/−.031/+.016 | −.022 | −.006 | −.025 | 34,5 | −.007 | 1 |
| 1h RJ S Gatr | 1676 | .570 | .598 | −0,046 | −7,2 | .02 | −.038/−.046/−.063 | −.057 | −.032 | −.055 | 8,5 | −.022 | 2 |
| **1h RJ S Gtime** | 1676 | .406 | .387 | **+0,042** | **+0,3** | .86 | +.040/+.042/+.047 | +.033 | +.057 | +.033 | 96 | −.022 | **5** |
| 1h RJ S Gmid | 1553 | .486 | .514 | −0,053 | −7,5 | .04 | −.081/−.040/−.016 | −.063 | −.037 | −.064 | 22 | −.031 | 2 |

  Tanımlar:
  - **CZ** = botun z-skoru (son 50 kapanışın doğrusal regresyonu, |z| ≥ 2).
  - **RJ** = t−1'de biten kanal t'ye uzatılır. Fitil banda değer, kapanış bandın içinde kalır, kapanış barın lehte yarısındadır.
  - **Gbot** = TP %1,04 / SL %1,49 (bot USOIL scope'u birebir), 24 saat üst sınır.
  - **Gatr** = TP 1,0 / SL 1,5 ATR, 48 bar üst sınır.
  - **Gtime** = SL 1,5 ATR, 12 bar zaman çıkışı.
  - **Gmid** = TP kanalın orta çizgisi, SL 1,5 ATR.
  - "taban" = aynı dönemde her bar kapanışında aynı yön ve geometriyle açılan işlemlerin ortR'si.
- **Çoklu sınama:** KEŞİF'te en iyi t = 1,04 (15m RJ S Gbot). Holm(110) düzeltilmiş p bütün CH hücrelerinde 1,0. — [all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv)
- **Tek SHADOW hücresinin (1h RJ S Gtime) sağlamlığı** ([channel_diag.csv](research/btc_5y_20261021/fam_mr_zaman/results/channel_diag.csv)):
  - zt = 2,5'te n = 1034 ve ortR +0,009 (dönemler +0,015 / −0,017 / +0,026).
  - ADX<25 × eğim 2×2 hücrelerinin işaretleri dönemden döneme değişiyor. Örnek: ADX<25 ∧ eğim lehte için KEŞİF −0,006, OOS −0,055, KÖR +0,315.
  - Kartta düştüğü ölçüt: P(EV>0) = 0,86 < 0,90.
- **Dar stop uyarısı:** 15m ATR geometrilerinde 1,5×ATR14 stop, barların %24'ünde fiyatın %0,3'ünün altında. Yıla göre oran: 2023'te %40, 2025–26'da %34. Minimum stop %0,03. Bu yüzden 15m Gatr, Gtime ve Gmid hücreleri "broker verisiyle teyit gerekir" diye bayraklandı. Ancak bu hücreler zaten negatif. — yerel hesap (btc_15m.parquet)

### Inferences
- NDX/DAX/USOIL'de "WR liftleri" olarak görülen kanal-sınır dönüşü, BTC'de net R'ye dönüşmüyor. BUY tarafı rastgele girişin bile altında kalıyor.
  - Bu, defterdeki "sabit uzak TP'de mean-reversion edge'i ters dönüyor" bulgusuyla (OLD-09, gösterge ayrımı notu) ve canlı CHREV kartıyla (−0,016R, RED) aynı yönde.
  - BTC'nin 15m–1h ölçeğinde düşüş tarafında devam (momentum) davranışı baskın görünüyor. Literatürün "1–4 saatte negatif otokorelasyon" bulgusu bu kurallarda maliyet sonrası paraya dönüşmüyor.
- SELL tarafı BUY'dan biraz daha iyi, ama tabanın üzerinde değil. Short tarafının swap alacağı (+%2/yıl) da sonucu değiştirmiyor.

### Gaps
- Broker BTCUSD M1 verisi yalnız 16 gün; dar stoplu hücreler için ileri kasa sınaması yapılamadı.
- Pulse sinyaline bağlı orijinal CHREV kapısı, BTC'de panel sinyali olmadığı için sınanamaz. Bu çalışma bar-tabanlı vekildir (defter E22).

---

## S2. Literatürdeki 21:00–23:00 UTC long BTC'de maliyet sonrası tutuyor mu (swap kesimiyle ve kesimsiz)?

### Takeaway
**Yönü tutuyor, ama kanıt seviyesinde değil.**
- Swap'tan kaçınan varyantların neti +3,3–3,7 bp/işlem: QB rollover'dan 1 dk sonra giriyor, QA swap'sız hesaplanıyor.
  - Aynı günlerde rastgele saatlere göre plasebo yüzdeliği %98,5–100.
  - OOS ve KÖR pozitif, iki yarı pozitif, stres pozitif.
- **Ama** P(EV>0) yalnız 0,90–0,91. Kartın 5. ölçütü (icra farkı) düşüyor çünkü kenar ≈ 2 spread büyüklüğünde. Yayın sonrası Holm p'si 0,63–0,88.
  - 2022'de (−5,5 bp) ve 2026'da (−3,2 bp) negatif.
  - Mekanik verdikt: **SHADOW**.
- **Broker'ın gerçek icrasında "21:00 gir" (QA, swap'lı) yalnız +2,1 bp (P 0,66).** Sebebi kış aylarında pencerenin 22:00 rollover'ını kesip swap ödemesi: kışın −2,55 bp/işlem.

### Cited Findings
- Kart ([timing_cells.csv](research/btc_5y_20261021/fam_mr_zaman/results/timing_cells.csv), [all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv)):

| hücre | n | WR | ortR | net bp | %95 GA (R) | P | yarılar | stres R | 15$ R | iyimser R | tek-poz | plasebo %ile (TAM/KÖR) | bp KEŞİF/OOS/KÖR | yayın sonrası p / Holm12 | kart | verdikt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| QA swap'lı | 1958 | .499 | +0,009 | +2,10 | [−.036, +.056] | .66 | −.021/+.040 | −.007 | −.019 | +.042 | +.009 | 91/— | +0,5/+4,8/+2,3 | .15 / 1,0 | 2 | RED |
| QA swap'sız | 1958 | .509 | +0,029 | +3,31 | [−.016, +.075] | .90 | +.001/+.057 | +.013 | +.001 | +.062 | +.029 | 98,5/98,5 | +1,7/+6,1/+3,3 | .052 / .63 | 5 (ölçüt 5 ✗) | SHADOW |
| QB rollover sonrası | 1958 | .517 | +0,029 | +3,68 | [−.013, +.071] | .91 | +.008/+.049 | +.013 | +.001 | +.060 | +.029 | 100/94,5 | +3,1/+6,8/+1,4 | .080 / .88 | 5 (ölçüt 5 ✗) | SHADOW |
| QC rollover öncesi çıkış | 1958 | .507 | +0,022 | +2,02 | [−.020, +.067] | .85 | +.004/+.040 | +.006 | −.006 | +.055 | +.022 | 99,5/— | +1,2/+4,2/+1,1 | .087 / .88 | 4 | RED |

  Plasebo ortalaması (aynı gün, rastgele saat, aynı uzunluk) yaklaşık −0,026…−0,030R.

  Varyant tanımları:
  - **QA:** giriş 21:00 UTC, çıkış 23:00.
  - **QB:** giriş rollover + 1 dk (yaz 21:01, kış 22:01), swap yok.
  - **QC:** kışın rollover'dan önce 21:58'de çık.
  - Yazın broker 20:59–21:00 kapalı olduğu için QA girişi 21:01'e kayıyor ve rollover'dan sonra açılıyor. Bu yüzden yaz ayları dört varyantta da aynı (+4,26 bp).
- **Alt kırılımlar (QB)** ([q_subreports.csv](research/btc_5y_20261021/fam_mr_zaman/results/q_subreports.csv)):
  - Pzt–Cum +2,9 bp, Cmt–Paz +5,6 bp.
  - Yaz +4,3 bp, kış +2,5 bp.
  - ETF öncesi +3,1 bp, ETF sonrası +4,2 bp.
  - Yıllar: 2021 +5,1 / 2022 +0,3 / 2023 +4,7 / 2024 +9,7 / 2025 +4,9 / 2026 −3,2 bp.
  - QA swap'lı varyantta kış alt kümesi −2,55 bp (P 0,03), 2022 −6,9 bp.
- **Uç günlere bağımlılık:**
  - QB'de net toplamın ≈%93'ü en iyi 20 günden geliyor (toplam 7.214 bp, en iyi 20 gün 6.723 bp). En iyi 20 gün çıkarılınca ortalama +0,25 bp.
  - Simetrik kırpmada (en iyi 20 ve en kötü 20 gün atılınca) ortalama +3,0 bp.
  - Dağılım ağır kuyruklu; ortalama kuyruk olaylarına duyarlı. — yerel hesap
- Literatürle kıyas: Quantpedia (Gemini 2015–2023, maliyetsiz) 22:00/23:00 saat getirilerini en yüksek buluyor ve 2022–23'te zayıflama not ediyor. Bizim 2022 sonucumuz da en zayıf yıl. — [03_literatur §1](research_notes/BTC trader bot kenar araştırması/03_literatur_btc_anomaliler.md); [Quantpedia](https://quantpedia.com/the-seasonality-of-bitcoin/)

### Inferences
- Pencerenin rastgele saatlere göre üstünlüğü (yaklaşık +6 bp brüt fark, plasebo %100) BTC'de gerçek bir **saat yapısı** olabilir. Ancak mutlak net kazanç bir spread çifti kadar.
  - Spread %0,028'e çıkınca kenar +1,3 bp'ye iniyor. Sabit 15 $ spread'de 2022'nin düşük fiyatları yüzünden ≈0.
  - Tek-pozisyonda yılda yaklaşık 365 işlem ve işlem başına +0,03R ile pratik getiri çok küçük.
- Broker'da uygulanacaksa yalnız **QB biçimi** anlamlı: rollover'dan sonra gir, 23:00'te çık, böylece hiç swap ödenmez. "21:00 gir" kışın swap yüzünden zarar ediyor.
- Literatürün maliyetsiz yıllık %33–40 iddiası CFD'de bu büyüklükte değil: brüt ≈ 5,5 bp/gün, net ≈ 3,5 bp/gün.

### Gaps
- Broker'ın 2021–2025 rollover ve spread davranışı bilinmiyor; bugünkü takvim geçmişe varsayıldı.
- Rollover çevresinde spread genişlemesi (tick düzeyinde p99 ~40 $) modelde yok. Model sabit %0,0185 kullanıyor.

---

## S3. Saat-of-gün, haftanın günü ve hafta sonu etkileri ile ETF sonrası ABD nakit saatleri yoğunlaşması

### Takeaway
**Maliyet sonrası sağlam işaretli saat kovası yok.**
- 48 saat hücresinin (24 saat × 2 yön) hiçbiri düzeltmeyi geçmiyor.
  - KEŞİF'teki en iyi net t = 0,73 (20:00 long). Max-z boş dağılımının %95 eşiği 1,74, en iyi max-z p'si 0,65.
  - 48 hücrenin 46'sı net negatif. Yalnız 22:00 long (+1,5 bp) ve 20:00 long (+0,3 bp) pozitif.
- **Gün etkileri:** Çarşamba long, Perşembe short, Pazar long ve hafta sonu long TAM dönemde pozitif. Çarşamba long ve hafta sonu long kart 6/6 geçip mekanik SHADOW oldu.
  - Ancak bu hücrelerin hiçbiri düzeltmeyi geçmiyor (Holm p 1,0; max-z p 0,37–0,90).
  - Plasebo yüzdeliği %65–96 aralığında. Perşembe short ve Pazar long dönemler arasında işaret değiştiriyor.
- **ETF sonrası yoğunlaşma (H12) ön-kayıtlı ölçütü geçmiyor:** ABD saatlerinin mutlak hareket payı yalnız +1,36 puan arttı (eşik 5 puan). Artışın çoğu ETF'ten önce 2021→2023 arasında gerçekleşti.

### Cited Findings
- **HOD, net bp (KEŞİF / OOS / KÖR):**
  - En iyiler:
    - 22:00 L +1,5 (+1,8 / +2,3 / +0,0), maxz p 0,91, plasebo %96,5.
    - 20:00 L +0,3 (+1,8 / −2,4 / +0,6).
    - 13:00 S −0,9 (−2,8 / +1,5 / +0,1).
  - En kötüler: 22:00 S −5,2, 20:00 S −4,0, 21:00 S −3,7, 19:00 L −3,6.
  - Tümü: [all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv) (fam = HOD). Max-z %95 eşiği: [h12_us_share.json](research/btc_5y_20261021/fam_mr_zaman/results/h12_us_share.json).
- **DOW/WE** (gün başına n ≈ 278–280; net bp TAM, KEŞİF / OOS / KÖR):

| hücre | net bp TAM (KEŞİF / OOS / KÖR) | P | kart | max-z p | plasebo %ile |
|---|---|---|---|---|---|
| Çarşamba L | +33,8 (+31,9 / +58,6 / +9,9) | .953 | 6/6 | .85 | 90,5 |
| Perşembe S | +25,4 (+28,0 / +3,9 / +44,7) | .941 | 6/6 | .37 | 96 |
| Pazar L | +17,2 (+25,9 / −3,1 / +22,9) | .889 | 5 | — | — |
| Cmt+Paz L | +13,6 (+21,9 / −0,4 / +12,9) | .929 | 6/6 | — | 65,5 |
| Pazartesi L | +10,8 (−18,7 / +54,9 / +19,0) | — | — | — | — |
| Salı L | −10,7 | — | — | — | — |

  - Perşembe short'un OOS ortR'si negatif (−0,014), bu yüzden RED.
  - Mekanik verdikt: Çarşamba L ve Cmt+Paz L **SHADOW**, diğerleri RED.
- **USC** (hafta içi NY 09:30–16:00):
  - Long −7,4 bp (P 0,08), short +3,7 bp (P 0,76, kart 4).
  - Plasebo: short %97, long %3. — aynı dosya
- **H12** ([h12_us_share.json](research/btc_5y_20261021/fam_mr_zaman/results/h12_us_share.json)):
  - Hafta içi Σ|5m getiri| içinde 13:30–21:00 UTC payı: 2022–23'te 0,393, 2024-01-11 sonrasında 0,407.
  - Fark +1,36 puan, %95 GA [+0,62, +2,09].
  - Yıllara göre: 2021 0,332 / 2022 0,380 / 2023 0,406 / 2024 0,407 / 2025 0,413 / 2026 0,397. Tekdüze dağılımda beklenen pay 0,3125.

### Inferences
- Saat taraması, defterdeki GF-03 dersini ("gün×saat takvimleri çağlar arasında taşınmaz") BTC'de de doğruluyor. 46/48 hücre negatif; spread tek başına her saat kovasını eksiye çekmeye yetiyor.
- Gün etkileri büyük bp sayıları gösteriyor, ama bunlar günlük oynaklığın (~280 bp) içinde gürültü düzeyinde (gün başına n ≈ 280 hafta). Seçim düzeltmesi ve plasebo bunları kenar saymıyor.
  - Çarşamba long'un SHADOW çıkması ön-kayıtlı şemanın mekanik sonucudur, kanıt değildir. Holm ve max-z bunu reddediyor (Mueller 2024 "sağlam seasonality yok" ile uyumlu).
- ETF sonrası "seans yoğunlaşması" küçük ve ETF'ten önce başlamış. ABD saatleri kapısı tasarlamak için yapısal bir gerekçe yok.
- Not: Gün tutuşlarında R paydası 1×ATR(1h) olduğu için R değerleri (±0,3–0,6) şişkin görünüyor. Gün hücrelerini bp üzerinden yorumlayın (E32).

### Gaps
- Ön-kayıt gereği hafta sonu yalnız tek kol (Cmt 00:00 → Pzt 00:00) olarak test edildi. Cuma 21:00 → Pazar 22:00 tanımı sınanmadı.
- Hafta sonu broker spread'i (tick p90 17,25 $) sabit spread modelinde yok.

---

## S4. Funding saati etkisi (H10) — öldürme testi

### Takeaway
**Ölü.**
- 00/08/16 UTC çevresindeki 30 dk'lık pencerelerin brüt ortalaması −0,16 / +0,95 / −0,14 bp. Diğer saatlerin pencereleriyle aynı düzeyde.
- 24 pencerenin hiçbiri Bonferroni'yi geçmiyor. En düşük düzeltilmiş p 0,33 ve o pencere funding saati değil (22:00).
- Hiçbir funding penceresinde |ortalama| 1,85 bp spread'i aşmıyor. 6 işlem hücresinin hepsi net negatif ve P(EV>0) ≤ 0,02.

### Cited Findings
- [fund_kill_24h.csv](research/btc_5y_20261021/fam_mr_zaman/results/fund_kill_24h.csv): her saat için merkezli 30 dk pencere, n ≈ 1967.
  - 00:00 −0,16 bp (t −0,18), 08:00 +0,95 bp (t 1,31), 16:00 −0,14 bp (t −0,13).
  - En büyük t 22:00'de: +2,29 bp, t 2,47, Bonferroni p 0,33.
  - Diğer pencerelerin ortalaması da ≈0 ±1,3 bp.
- İşlem hücreleri, net bp: FUND_00 L/S −2,2/−1,5, FUND_08 L/S −0,8/−2,9, FUND_16 L/S −2,1/−1,6. Kart 1/6. Yayın sonrası Holm p 1,0. — [all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv)

### Inferences
- Literatürde funding saati fiyat örüntüsü için hakemli kanıt yoktu ([03_literatur §1](research_notes/BTC trader bot kenar araştırması/03_literatur_btc_anomaliler.md)). Bu test de etkinin olmadığını gösteriyor. 22:00 penceresinin öne çıkması S2'deki 21–23 saat yapısıyla tutarlı, funding ile ilgisi yok.

### Gaps
- Funding oranının işareti ve büyüklüğüne koşullu test (ör. aşırı pozitif funding) yapılmadı; veri setinde funding serisi yok.

---

## S5. Turn-of-the-candle (H11) — maliyet modeli kalibrasyonu

### Takeaway
**Kalibrasyon geçti: maliyet modeli bilinen ölü kenarı öldürüyor.**
- :00/:15/:30/:45 dakikalarının brüt getirisi literatürdeki çürümeyi aynen gösteriyor:
  - 2021'de +0,57 bp (Shanaev vd.'nin 0,58 bp'si).
  - 2022'de +0,20, 2023'te +0,13, 2024'te +0,01, 2025'te +0,08, 2026'da −0,08 bp.
- Net getiri −1,72 bp (long) ve −1,98 bp (short), P(EV>0) = 0. Aile durdurulmadı.

### Cited Findings
- [toc_gross_by_year.csv](research/btc_5y_20261021/fam_mr_zaman/results/toc_gross_by_year.csv): TAM dönemde dönüm dakikaları +0,127 bp, diğer dakikalar −0,004 bp; n = 186.919.
- TOC_L: n = 185.914, net −1,72 bp, KEŞİF/OOS/KÖR −1,60/−1,79/−1,90 bp, kart 1/6. TOC_S: −1,98 bp. — [all_cells_verdict.csv](research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv)
- Literatür: 2021 Bitfinex'te 0,58 bp; 2022 OOS'ta katsayılar 1/3–1/8'e düşüyor. — [PMC (Shanaev vd. 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/)

### Inferences
- Simülatör hem brüt etkiyi doğru büyüklükte yakalıyor hem de spread ile öldürüyor. Bu, diğer ailelerin "maliyet sonrası negatif" sonuçlarının model hatasından gelmediğine dair bir sağlık kontrolüdür.
- 2021 brüt değerinin literatürle birebir örtüşmesi veri setinin dakika etiketlerinin doğru olduğunu da destekliyor. Dakikalar sola etiketli ve bar açılışı = UTC.

### Gaps
- Yok.

---

## S6. Defter satırı taslağı ve yeni yöntem tuzakları

### Takeaway
Ailede **LIVE adayı yok.**
- 110 hücrenin 105'i RED, 5'i mekanik SHADOW: QA swap'sız, QB, CH 1h RJ S Gtime, Çarşamba L, Cmt+Paz L.
- Bu 5 hücrenin hiçbiri çoklu sınama düzeltmesini geçmiyor.
- Bot için tek anlamlı izleme adayı **BTC 21:01→23:00 UTC long (QB)**. Bu da gölge izleme olarak, kanıt sınıfı C ile.

### Cited Findings
Defter §6 biçiminde taslak satırlar (yeni bölüm önerisi: "2.11 BTC — `research/btc_5y_20261021/fam_mr_zaman/`", ön kayıt `prereg.md`):

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-M01 | 2026-10-21 | **Kanal-sınır dönüşü (CHREV portu)**: linreg n=50, 15m ve 1h; tetik CZ (z≤−2/≥+2) ve RJ (uzatılmış banda dokun-reddet mumu); 4 geometri (bot %1,04/%1,49 · ATR 1/1,5 · 12 bar · orta çizgi); iki yön; epizod başına ilk tetik | Binance 1m 2021-06→2026-10: 32 hücrenin 31'i ≤0. KEŞİF Holm p hepsinde 1,0. Alt banttan BUY rastgele girişin altında (15m RJ L plasebo %0–1,5; −0,04…−0,09R). Taban üstü SELL yok. Kanıt: `results/channel_cells.csv` | X |
| BTC-M02 | 2026-10-21 | **21:00–23:00 UTC long (Quantpedia)**: 7/7 gün; QA 21:00 giriş (swap'lı / swap'sız), QB rollover+1 dk giriş, QC kışın rollover öncesi çıkış; çıkış 23:00 | QB n=1958, net +3,7 bp (+0,029R), P 0,91, yarılar +/+, stres +0,013R, OOS +6,8 / KÖR +1,4 bp, plasebo (rastgele saat) %100. Ölçüt 5 ✗ (icra farkı 0,031 > 0,014), yayın sonrası Holm p 0,88; 2022 +0,3 ve 2026 −3,2 bp; net toplamın %93'ü en iyi 20 günden. "21:00 gir" swap'lı +2,1 bp (kış −2,6 bp) → RED. Literatür yönü tutuyor, kenar ≈ 2 spread. `results/timing_cells.csv`, `q_subreports.csv` | C (QB gölge adayı) |
| BTC-M03 | 2026-10-21 | **Saat-of-gün** (24 UTC saati × L/S, 1 saatlik tutuş, swap kuralı dahil) | 46/48 hücre net negatif. En iyi 22:00 L +1,5 bp (KÖR +0,0). KEŞİF max-z p ≥ 0,65 (%95 eşik t 1,74), Holm 1,0 | X |
| BTC-M04 | 2026-10-21 | **Haftanın günü + hafta sonu** (UTC günü 00→24 L/S × 7; Cmt+Paz L/S) | Çarşamba L +33,8 bp/gün ve Cmt+Paz L +13,6 bp kart 6/6 → mekanik SHADOW. Ancak KEŞİF Holm 1,0, max-z p 0,85 / —, plasebo %90,5 / %65,5. Perşembe S ve Pazar L dönemler arasında işaret değiştiriyor → gürültü (n ≈ 280 hafta) | X (mekanik SHADOW kanıt sayılmaz) |
| BTC-M05 | 2026-10-21 | **ABD nakit saatleri** (NY 09:30–16:00 L/S) + **H12** (hafta içi Σ\|5m\| içinde 13:30–21:00 UTC payı, 2022–23 vs ETF sonrası) | USC L −7,4 bp, S +3,7 bp (P 0,76). H12: pay 0,393 → 0,407 (+1,36 puan, GA [0,62; 2,09]) < 5 puan eşiği; artış 2021→2023'te gerçekleşti | X |
| BTC-M06 | 2026-10-21 | **Funding saati (H10)**: 00/08/16 UTC ±15 dk, L/S; 24 pencere Bonferroni | Funding pencereleri −0,16 / +0,95 / −0,14 bp brüt; Bonferroni en iyi p 0,33 (22:00, funding değil); işlem hücreleri −0,8…−2,9 bp net | X |
| BTC-M07 | 2026-10-21 | **Turn-of-the-candle (H11)** — maliyet kalibrasyonu: :00/:15/:30/:45 dakikası L/S | Brüt 2021 +0,57 → 2026 −0,08 bp (literatürdeki çürüme), net −1,72 bp, P 0. Simülatör bilinen ölü kenarı öldürüyor ✓ | X (kalibrasyon ✓) |
| BTC-M08 | 2026-10-21 | CH 1h RJ SELL + 12 bar zaman çıkışı (BTC-M01'in tek pozitif hücresi) | +0,042R ama bp ≈ +0,3; P 0,86; zt=2,5'te +0,009R; ADX×eğim 2×2 dönemler arasında işaret değiştiriyor → R pozitifliği oynaklık ağırlıklandırmasından geliyor (E32) | X |

### Inferences
**Yeni yöntem tuzakları (defter §1'e öneri):**
- **E40 (öneri): Sabit UTC saat penceresi + DST'ye bağlı broker rollover'ı = mevsime göre değişen maliyet.**
  - Aynı "21:00 gir" kuralı yazın broker kapanışı yüzünden 21:01'de, rollover'dan sonra dolar ve swap ödemez. Kışın aynı kural 22:00 rollover'ını keser ve gece başına swap öder.
  - Etkisi: kış alt kümesi −2,55 bp, yaz +4,26 bp.
  - Önlem: zaman pencereli kuralları broker sunucu saatine göre tanımla ve sonuçları yaz/kış ayrı raporla.
- **E32'nin BTC'deki yeni bir örneği.** Nominal stop olarak ATR(1h) kullanan zaman çıkışlı kurallarda R pozitif ama bp ≈ 0 olabiliyor: BTC-M08'de +0,042R'ye karşılık +0,3 bp. R ve bp işaret/büyüklük olarak ayrışıyorsa R'ye güvenme.
- **Kart ölçütü 5 spread'in hâkim olduğu zaman kurallarında "net ≥ 2 × spread" anlamına geliyor.** İyimser senaryo zaten yalnız spread ve rollover kayması kadar farklı. Bu ölçüt bp düzeyindeki takvim kenarlarını yapısal olarak eler; bu isteniyorsa doğru, ama "icra hatası" olarak yorumlanmamalı.
- **BTC'de 15m ATR stopları sık sık %0,3'ün altına iniyor** (barların %24'ü, 2023'te %40). Bunlar broker'ın %12 daha gürültülü 1m kotasyonunda Binance'ten farklı tetiklenir. 15m ATR geometrili her BTC kuralı broker M1 ile teyit gerektirir.

### Gaps
- Evrim Paneli oturum notu (1. KURAL) ve defter güncellemesi yapılmadı. Görev kısıtı yalnız `fam_mr_zaman/` altına yazmaya izin veriyordu. Koordinatör bu taslak satırları deftere ve oturum notuna taşımalı.
- QB için broker ileri kasası (MT5 BTCUSD M1, ~16 gün) bu ailede koşulmadı; gölge izleme bunu üretecek.
