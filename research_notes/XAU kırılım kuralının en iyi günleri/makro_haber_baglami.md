# XAU H1 20-bar kırılım BUY kuralının (MK-04 / R0B_G1) en iyi günlerinin makro, haber ve olay bağlamı

Kapsam ve yöntem notu (tüm bölümler için geçerli):
- Kural: H1 high, önceki 20 barın en yüksek değerine ulaşır → sonraki H1 açılışında BUY; SL 1,5×ATR14(H1), TP yok, 20 H1 bar sonra çıkış; spread $0,12; aynı anda tek pozisyon. Veri `mekanik/data/duka_h1.parquet`. `run_main.load_main()` veriyi **2026-06-17 öncesinde keser** (END_MAIN). Bu yüzden örneklem 2008-01 → 2026-06-16 aralığı; brifteki "2026-09" bu simülasyona girmiyor.
- `mekanik/` kodu salt-okunur olarak yeniden kullanıldı. Kendi kodum: `research/xau_best_days_20261015/makro/01_trades.py … 10_posthoc_holiday.py`, çıktılar `.../makro/out/`.
- Yeniden üretim: **3.664 işlem, toplam +290,5R**, ortalama +0,0793R, WR %35,6. Birebir `results/posthoc_onepos.txt` ile aynı.
- Gün tanımı: işlemin **GİRİŞ** barının UTC takvim günü. İşlem günü sayısı 3.047.
- ⚠️ **"R'nin %72'si en iyi 20 günden geliyor" iddiası benim hesabımda tutmadı.** Aynı tanımla en iyi 20 gün +178,9R getiriyor. Bu, toplamın **%61,6**'sı. Sinyal günüyle hesaplayınca %61,9, NY 17:00 günüyle %61,3 çıkıyor. En iyi 50 gün toplamın %127'si: geri kalan 2.997 günün toplamı negatif. Paralel araştırmacının `best_days.csv` dosyası henüz yoktu. Kendi listelerim: `out/best20.csv`, `out/best50.csv`, `out/worst20.csv`, `out/days.csv`.
- **Ex-ante / ex-post ayrımı:**
  - Makro durumlar (VIX, DXY, S&P) giriş UTC gününden önceki son ABD kapanışından (D-1) alındı.
  - Reel faiz (FRED DFII10), yayın gecikmesi nedeniyle D-2'den alındı.
  - Altının önceki gün getirisi Dukascopy'nin önceki UTC gününden geldi.
  - ATR rejimi yalnız geçmiş barlarla hesaplandı.
  - Olay takvimi yalnız önceden ilan edilen tarihlerden oluşuyor: FOMC planlı toplantıları, BLS CPI ve İstihdam yayın günleri, Jackson Hole.
  - "D" ve "D+1" gün hareketleri (`out/topdays_macro.csv`) ex-post'tur ve yalnız bağlam için kullanıldı.

## 1. En iyi günlerde dünyada ve makro piyasalarda ne oldu? Olay sınıflaması

### Takeaway
En iyi 20 günden yalnız 2'sinde ana itici planlı FOMC/CPI/NFP olayı: 2024-03-20 FOMC ve 2019-06-19 FOMC.
- **11 gün öngörülemeyen şoklar:** finansal kriz/banka (2008-09-17 AIG, 2011-08-18, 2023-03-17 SVB/CS), savaş/jeopolitik (2022-02-24 Ukrayna, 2023-10-13 Gazze), ticaret/tarife (2025-04-16, 2025-05-05), salgın (2020-02-18), hisse çöküşü (2018-10-11), politika sürprizi (2019-07-02 Lagarde, 2020-07-21 AB fonu).
- **4 gün takvimi önceden bilinen ama FOMC/CPI/NFP dışı olaylar:** seçim günü, ISM/perakende satış verisi, borç tavanı son günü.
- **3 gün belirgin bir haber katalizörü yok:** ABD tatili sonrası ince piyasa günleri.

En iyi günlerin ortak makro imzası (aynı gün, ex-post): altın vadelisi medyan **+%1,5**, ABD 10Y ~−3 bp, reel faiz ~−2/−3 bp, DXY −%0,2. Yani dolar ve reel faiz düşerken altın çok sert yükselmiş. Bütün işlem günlerinin medyanı +%0,4 altın, −1 bp reel faiz.

### Cited Findings
**En iyi 20 gün tablosu.** Sütunlar:
- **R:** kural R'si.
- **giriş→çıkış:** UTC saat.
- **SL$:** 1,5×ATR, dolar/ons.
- **D GC=F%:** aynı gün altın vadelisi değişimi.
- **D DXY%:** aynı gün DXY değişimi.
- **D 10Y bp:** aynı gün 10 yıllık getiri değişimi.
- **VIX(D-1):** girişten önceki günün VIX kapanışı.

Kaynak: repo hesapları `out/topdays_macro.csv` ve `out/09_log.txt` (yfinance DX-Y.NYB, ^TNX, ^VIX, ^GSPC, CL=F, GC=F; FRED DFII10).

| # | Gün | R | giriş→çıkış | SL$ | D GC=F% | D DXY% | D 10Y bp | VIX(D-1) | Sınıf | Haber bağlamı |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2008-09-17 | 15,63 | 09-17 10 → 09-18 05 | 5,4 | +9,0 | −1,2 | −8 | 30,3 | ÖNGÖRÜLEMEZ – sistemik finansal kriz | AIG kurtarması + Lehman sonrası panik. Aralık altın vadelisi +$70 ile $850,50: 1980'deki $64 rekorunu aşan, dolar bazında en büyük tek gün kazancı. Dow −449 ([CNN Money](https://money.cnn.com/2008/09/17/markets/gold/index.htm); [Reuters/finance.cz](https://www.finance.cz/zpravy/reuters/MTFH22146nLH518535-update-6-gold-posts-historic-gains-on-flight-to-safety/)). Planlı FOMC bir gün önceydi (09-16) ama hareketi tetiklemedi. |
| 2 | 2023-10-13 | 11,37 | 10-13 10 → 10-13 20 | 4,0 | +3,1 | +0,1 | −8 | 16,7 | ÖNGÖRÜLEMEZ – savaş/jeopolitik | İsrail'in Gazze tahliye emri sonrası altın ~3 hafta zirvesine, $1.900 üstüne çıktı ([dptribune](https://business.dptribune.com/dptribune/news/read/43674289/investors_flock_to_safe)). Ekim'de altın %8 artışa gidiyordu ([CNBC](https://www.cnbc.com/2023/10/31/gold-on-track-for-biggest-monthly-rise-in-11-on-safe-haven-flows.html)). CPI bir gün önceydi (10-12). |
| 3 | 2012-11-06 | 10,93 | 11-06 11 → 11-07 06 | 3,3 | +1,9 | −0,2 | +6 | 18,4 | TAKVİMDE (FOMC/CPI/NFP dışı) – ABD başkanlık seçimi | Seçim günü altın ~+%1,9. Analistler Obama'nın kazanmasını ek Fed teşviki nedeniyle altına olumlu görüyordu ([CS Monitor](https://csmonitor.com/Business/Latest-News-Wires/2012/1106/Gold-prices-rise-ahead-of-presidential-election); [tradingnrg recap](https://tradingnrg.com/gold-silver-and-oil-hiked-again-on-tuesday-recap-november-6th/), tek blog kaynağı) |
| 4 | 2012-11-23 | 10,38 | 11-23 08 → 11-23 21 | **1,7** | +1,4 | −0,9 | +1 | 15,3 | TATİL-SONRASI ince piyasa, zayıf haber | Şükran Günü sonrası Cuma. Öğleden sonra spot +%0,3 ile $1.733: Alman verisi ve Yunanistan anlaşma umudu, haftalık >%1, "mali uçurum" kaygısı ([IOL/Reuters](https://iol.co.za/business-report/markets/2012-11-23-gold-tops-1730oz/)). R, dar SL ($1,7) yüzünden şişti. |
| 5 | 2016-09-06 | 9,95 | 09-06 08 → 09-07 04 | 2,3 | +2,1 | −1,1 | −5 | 12,0 | TAKVİMDE veri sürprizi (ISM) + Labor Day sonrası | ISM hizmet 51,4, 6,5 yılın dibi. Eylül faiz artırımı olasılığı ~%15'e indi, altın ~%1,5–2 yükseldi ([Business Standard/Reuters](https://www.business-standard.com/amp/article/reuters/gold-hits-over-two-week-high-as-u-s-data-trims-rate-hike-hopes-116090700298_1.html); [Tradingpedia](https://www.tradingpedia.com/2016/09/07/gold-trading-outlook-futures-trade-just-below-2-5-week-highs-as-latest-us-macroeconomic-reports-ease-rate-hike-bets/)) |
| 6 | 2020-07-21 | 9,91 | 07-21 07 → 07-22 03 | 3,5 | +1,5 | −0,7 | −1 | 24,5 | YARI-ÖNGÖRÜLEMEZ politika (AB €750 mlr fonu) + salgın rejimi | AB zirvesi €750 mlr kurtarma fonunda anlaştı, dolar her cephede geriledi. Altın 2011'den beri en yüksek seviyede, ay içi kazanç ~%20 ([Malay Mail](https://www.malaymail.com/news/money---international/2020/07/21/global-equity-markets-rebound-on-eu-fund-optimism-as-gold-edges-higher/1886408); [BusinessLive](https://www.businesslive.co.za/bd/markets/2020-07-22-world-markets-happy-with-eu-recovery-plan-as-metals-shines/)) |
| 7 | 2022-02-23 | 9,19 | 02-23 15 → 02-24 11 | 6,0 | +0,2 (D+1 +0,8) | +0,2 | +3 | 28,8 | ÖNGÖRÜLEMEZ – savaş | Pozisyon 24 Şubat gecesi Rusya'nın Ukrayna işgalini taşıdı. Spot gün içinde %3,4 artışla $1.974,34'e çıktı ([CNBC](https://www.cnbc.com/2022/02/24/russia-invades-ukraine-gold-jumps-to-highest-in-more-than-a-year.html); [BusinessLive](https://www.businesslive.co.za/bd/markets/2022-02-24-gold-surges-as-russian-invasion-of-ukraine-rattles-investors/)) |
| 8 | 2011-08-18 | 9,13 | 08-18 07 → 08-19 02 | 5,2 | +1,6 | +0,8 | −8 | 31,6 | ÖNGÖRÜLEMEZ – Avro krizi/hisse çöküşü (+ planlı CPI) | Philly Fed −30,7, DAX −%5,8. Spot altın rekor $1.825,99 ([IBTimes/Reuters](https://www.ibtimes.com/gold-new-highs-growth-fears-hit-markets-646025); [Wikipedia: August 2011 stock markets fall](https://en.wikipedia.org/wiki/August_2011_stock_markets_fall)) |
| 9 | 2023-03-17 | 8,95 | 03-17 07 → 03-17 20 | 6,2 | +2,6 | −0,7 | −19 | 23,0 | ÖNGÖRÜLEMEZ – banka krizi | SVB/Credit Suisse/First Republic. Spot +%3,1 ile $1.977,89, Nisan 2022'den beri en yüksek. Hafta +%5,8 ([Kitco/Reuters](https://www.kitco.com/news/off-the-wire/2023-03-17/global-markets-global-equities-fall-gold-surges-banking-worries-linger); [CNBC](https://www.cnbc.com/2023/03/17/gold-poised-for-best-week-since-mid-november-on-banking-sector-tension.html)) |
| 10 | 2024-03-20 | 8,02 (iki işlem: +9,02/−1) | 03-20 15 → 03-21 11 | 5,6 | +0,1 (D+1 +1,1) | −0,4 | −2 | 13,8 | **PLANLI FOMC** | Fed 2024 için üç indirim projeksiyonunu korudu. Spot ertesi gün rekor $2.222,39'a çıktı ([Kitco/Reuters](https://www.kitco.com/news/off-the-wire/2024-03-21/gold-hits-fifth-record-high-march-fed-rate-cut-view); [CNBC](https://www.cnbc.com/2024/03/21/gold-sprints-to-record-high-as-fed-sticks-to-2024-rate-cut-view.html)) |
| 11 | 2011-08-02 | 7,91 | 08-02 12 → 08-03 07 | 4,5 | +1,4 | +0,3 | −12 | 23,7 | TAKVİMDE son tarih (borç tavanı) + hisse düşüşü | Obama borç tavanı yasasını imzaladı, hisseler yine sert düştü. Aralık vadeli rekor $1.644,50'de kapandı ([APMEX kapanış raporu](https://www.apmex.com/precious-metals-market-news/590/closing-gold-silver-market-report-08-02-2011)). 5 gün sonra S&P ABD notunu indirdi ([Kitco](https://www.kitco.com/news/article/2023-02-09/heres-what-gold-price-did-during-2011-debt-ceiling-crisis-and-what-expect)) |
| 12 | 2020-02-18 | 7,83 | 02-18 00 → 02-18 19 | 2,2 | +1,1 | +0,3 | −3 | 13,7 | ÖNGÖRÜLEMEZ – salgın (+ Başkanlar Günü sonrası) | Apple koronavirüs nedeniyle satış uyarısı verdi. Altın $1.600'ün üstüne çıktı, vadeli +%1,1 ile $1.603,60'ta kapandı ([Investing.com/Reuters](https://investing.com/news/commodities-news/gold-tops-1600-as-virus-fuels-growth-fears-2088015); [Al Jazeera](https://www.aljazeera.com/ajimpact/stocks-slide-apple-virus-warning-euro-year-200218173459340.html)) |
| 13 | 2019-07-02 | 7,68 | 07-02 14 → 07-03 10 | 4,3 | +1,4 | −0,1 | −6 | 14,1 | YARI-ÖNGÖRÜLEMEZ politika (Lagarde ECB adaylığı) + küresel gevşeme | Altın ~+$29 ile ~$1.413, ABD 10Y 1,945% ([ForexLive](https://investinglive.com/news/!/forexlive-nth-american-fx-news-2-jul-20190702)). Ertesi gün vadeli 6 yılın en yüksek kapanışı, Bund rekor −%0,40 ([Metalsmine/MarketWatch](https://www.metalsmine.com/news/929865-gold-futures-score-highest-finish-in-over-6/amp)) |
| 14 | 2015-05-13 | 7,68 | 05-13 09 → 05-14 04 | 2,7 | +2,2 | −1,0 | +2 | 13,9 | TAKVİMDE veri sürprizi (perakende satış) | Nisan perakende satışları yatay geldi. DXY 3 ayın dibine (93,46) indi, altın ~%2 yükseldi ([CNBC](https://www.cnbc.com/2015/05/14/bad-news-is-serving-as-good-news-for-gold.html); [Business Standard/Reuters](https://www.business-standard.com/amp/article/reuters/dollar-declines-gold-up-after-soft-u-s-data-115051400074_1.html)) |
| 15 | 2025-05-05 | 7,61 (iki işlem) | 05-05 02 → 05-06 18 | 18–23 | +2,4 (D+1 +3,0) | −0,2 | +2 | 22,7 | ÖNGÖRÜLEMEZ – tarife şoku (+ FOMC 05-07 haftası) | Pazar günü film tarifesi duyuruldu. Haziran vadeli +$77,87 ile $3.322,3 ([Argaam](https://www.argaam.com/en/article/articledetail/id/1810438); [Kontan](https://english.kontan.co.id/news/gold-hits-two-week-high-on-safe-haven-demand-fed-decision-looms)) |
| 16 | 2025-04-15 | 7,56 | 04-15 22 → 04-16 17 | 12,9 | +0,4 (D+1 +3,3) | +0,6 | −4 | 30,9 | ÖNGÖRÜLEMEZ – ABD-Çin ticaret/teknoloji savaşı | Nvidia H20 ihracat kısıtı (5,5 mlr $ etki) ve 145%/125% tarifeler. Altın rekor ~$3.304–3.318 ([The Star/Reuters](https://www.thestar.com.my/business/business-news/2025/04/16/shares-skid-in-asia-as-nvidia-curbs-fan-worries-gold-surges-to-record); [Daily Maverick](https://www.dailymaverick.co.za/article/2025-04-16-shares-fall-in-asia-as-nvidia-curbs-fan-worries-gold-hits-record.md)) |
| 17 | 2018-10-10 | 7,46 | 10-10 19 → 10-11 15 | 3,7 | +0,2 (D+1 +2,9) | −0,2 | +2 | 15,9 | ÖNGÖRÜLEMEZ – hisse çöküşü (+ planlı CPI 10-11) | 10–11 Ekim'de S&P −%5,3. Altın Haziran 2016'dan beri en iyi gününü yaşadı, Comex +%2,9 ile $1.227,60 ([Business Standard/Reuters](https://www.business-standard.com/amp/article/reuters/gold-surges-2-percent-as-share-sell-off-sparks-flight-to-safety-118101101387_1.html); [VanEck](https://www.vaneck.com/globalassets/home/media/managedassets/etf-europe/library/commentary/vaneck-gold-commentary-2018-10_english.pdf/); [CoinNews](https://coinnews.net/2018/10/11/gold-rallies-2-9-ends-at-10-week-high)) |
| 18 | 2008-02-19 | 7,44 | 02-19 01 → 02-19 20 | 2,7 | +2,6 | −0,1 | +10 | 25,0 | KATALİZÖR BULUNAMADI (Başkanlar Günü sonrası, emtia rallisi) | Şubat ortasında platin, Güney Afrika elektrik kriziyle ardı ardına rekor kırdı. Altın 11 Şubat'ta $936,50 rekoruna yakındı ([Reuters/finance.cz](https://www.finance.cz/zpravy/reuters/MTFH51091nL15213585-update-8-platinum-hits-record-high-2-060-on-panic-buying)). Aynı gün CL=F +%4,7 (repo verisi). 19 Şubat'a özgü kaynak bulunamadı. |
| 19 | 2019-06-19 | 7,31 | 06-19 19 → 06-20 15 | 4,5 | −0,2 (D+1 +3,6) | −0,5 | −3 | 15,1 | **PLANLI FOMC** (giriş açıklamadan 1 saat SONRA) | Fed "sabırlı" ifadesini çıkardı, 17 üyeden 8'i indirim gösterdi. Altın 2013'ten beri ilk kez $1.400'ü aştı ([WGC Goldhub](https://www.gold.org/goldhub/gold-focus/2019/06/gold-breaks-out-key-multi-year-resistance-level); [BNN Bloomberg](https://www.bnnbloomberg.ca/gold-achieves-liftoff-as-prices-rocket-toward-us-1-400-an-ounce-1.1275787)) |
| 20 | 2010-01-04 | 7,01 (iki işlem: +8,01/−1) | 01-04 05 → 01-05 00 | 2,4 / **1,0** | +2,1 | −0,4 | 0 | 21,7 | YILBAŞI TATİLİ SONRASI | Haber araştırılmadı/bulunamadı. Repo verisinde SPX +%1,6, petrol +%2,7. |

**En iyi 21–50 günler (kısa sınıflama; haberler web'de AYRICA doğrulanmadı, yalnız repo takvimi ve makro hareketleri):**
- Planlı FOMC/CPI/NFP olay günleri veya olay pencereleri:
  - 2008-06-26 (FOMC 06-25 ertesi)
  - 2016-03-03 (NFP 03-04 penceresi)
  - 2013-04-05 (NFP)
  - 2022-11-04 (NFP)
  - 2025-03-13 (CPI ertesi)
  - 2016-09-21 (FOMC)
  - 2016-06-15 (FOMC + CPI)
  - 2013-09-18 (FOMC: tapering yapılmadı)
  - 2024-09-12 (CPI ertesi)
- Jackson Hole: 2019-08-23. Aynı gün ABD-Çin tarife tırmanışı da vardı (bağımsız teyit edilmedi).
- Tatil sonrası: 2012-02-21, 2019-02-19, 2026-01-20.
- Yıl dağılımı (en iyi 50): 2008:4, 2009:2, 2010:3, 2011:3, 2012:3, 2013:2, 2014:1, 2015:1, **2016:6**, 2018:1, 2019:4, 2020:2, 2021:1, 2022:2, 2023:3, **2024:6**, 2025:4, 2026:2. 2017 hiç yok (`out/08_log.txt`).

**Medyan aynı-gün makro hareketleri** (repo, `out/06_log.txt`):

| küme | altın vadelisi | 10Y | reel faiz | DXY | VIX değişimi |
|---|---|---|---|---|---|
| tüm 3.047 işlem günü | +%0,40 | −0,7 bp | −1 bp | −%0,08 | −0,09 |
| en iyi 20 | +%1,50 | −2,75 bp | −2 bp | −%0,18 | +0,48 |
| en iyi 50 | +%1,51 | −1,95 bp | −3 bp | −%0,31 | — |
| en kötü 20 | +%0,45 | +1,5 bp | — | — | — |

En kötü 20 günün ertesi günü (D+1) altın −%0,33.

**En kötü 20 gün:** Hepsi aynı gün içinde 3–4 kez ardışık SL olan, kesik kesik kırılım günleri (−3R/−4R). Olay penceresi yalnız 4'ünde var: NFP 06-05-2020, 2012-02-03, 2014-09-05; CPI 2010-02-19. 20'nin hiçbiri tatil sonrası gün değil (`out/topdays_macro.csv`, `out/10_log.txt`).

### Inferences
- En iyi günlerin çoğunun "haberi" önceden bilinemezdi: banka kurtarması, savaş, tarife duyurusu. Kural bu şokları kırılım sonrası yakalıyor, çünkü şok altını önceki 20 saatin tepesinin üstüne itiyor ve 20 saatlik tutma süresi devamı topluyor.
- **Ortak makro mekanizma:** güvenli liman talebi + düşen nominal/reel faiz + zayıf dolar. Bu, defterin "korku döner, coşku dönmez" ilkesinin altındaki XAU karşılığı: stres anında altın yukarı sürükleniyor.
- 20 günün 3'ünde (2012-11-23, 2008-02-19, 2010-01-04) belirgin bir şok yok. Bu günlerde R büyüklüğü büyük ölçüde paydanın (ATR) küçüklüğünden geliyor: tatil saatlerinde ATR14 H1 sıkışıyor. Bu, haber değil **ölçüm etkisi**. Bkz. §5 tatil testi.

### Gaps
- 2008-02-19, 2010-01-04, 2026-01-20, 2026-05-05 için güvenilir günlük haber kaynağı bulunamadı. 2026 günleri model bilgi sınırının (2026-06) yakınında, web taraması yapılmadı.
- 2011-08-02 hareketinin "zayıf tüketici harcaması"na bağlanması doğrulanmadı. Yalnız borç tavanı imzası ve hisse düşüşü kaynaklı.
- 2023-10-13 ve 2020-07-21 için kaynaklar gün içi anlık görüntüler veriyor. Kapanış rakamları kaynaklar arasında farklı.
- ECB toplantı takvimi derlenmedi. ECB etkisi test edilmedi.

## 2. Planlı olay (FOMC/CPI/NFP) günleri ile olaysız günlerin taban oranları ve işlem başına R'leri

### Takeaway
Planlı olay günleri en iyi günlerde aşırı temsil edilmiyor:
- FOMC/CPI/NFP günü, tüm işlem günlerinin %13,1'i; en iyi 20'nin %15'i; en iyi 50'nin %16'sı.
- Olay günündeki işlemlerin ortalama R'si (+0,109) ile olaysız günlerinki (+0,074) arasındaki fark +0,035R, %95 CI [−0,127, +0,196]. Anlamlı değil.
- **Tek ayırt edici sinyal sağ kuyrukta ve yalnız FOMC'de:** FOMC açıklaması 20 saatlik tutma penceresine düşen işlemlerde P(R≥3) %14,7, diğerlerinde %6,9. Fark +7,8 puan, CI [+1,0, +15,1]. İki kronolojik yarıda da aynı yönde (+7,6 / +8,2 puan). Ancak aynı geometrideki rastgele BUY'larda da benzer kuyruk artışı var (%11,3 vs %6,0). Yani bu kırılıma özgü değil, "FOMC'yi long taşımak"a özgü.

### Cited Findings
Takvim kaynakları: FOMC planlı toplantıları 2008–2015 [federalreserve.gov tarihî sayfaları](https://www.federalreserve.gov/monetarypolicy/fomchistorical2010.htm), 2016–2026 repo listesi `research/ndx_gate_forge/macro10y.py`. CPI yayın tarihleri [BLS CPI arşivi](https://www.bls.gov/bls/news-release/cpi.htm). İstihdam (NFP) yayın tarihleri [BLS Employment Situation arşivi](https://www.bls.gov/bls/news-release/empsit.htm), 2008-01-04 elle eklendi. Açıklama saatleri:
- FOMC: 14:15 ET (2013-03 öncesi), 14:00 ET (sonrası).
- CPI/NFP: 08:30 ET.

**Gün düzeyinde görülme oranı** (repo `out/feature_tests.csv`):

| özellik | tüm işlem günlerinde | en iyi 20'de | en iyi 50'de |
|---|---|---|---|
| giriş günü FOMC/CPI/NFP | %13,1 | %15 | %16 |
| FOMC günü | %3,6 | %10 | %10 |
| CPI günü | %5,0 | %5 | %2 |
| NFP günü | %4,9 | %0 | %4 |
| yayın anı tutma penceresinde | %7,7 | %15 | %16 |

**İşlem başına R:** Fark sütunu "olay − olaysız", gün-blok bootstrap 2.000 tekrar.

| koşul | n | ortR olay | ortR olaysız | fark [%95 CI] | P(R≥3) olay / olaysız | yarı farkı 2008-16 / 2017-26 |
|---|---|---|---|---|---|---|
| giriş günü FOMC/CPI/NFP | 512 | +0,109 | +0,074 | +0,035 [−0,127, +0,196] | %8,0 / %6,9 | +0,119 / −0,037 |
| FOMC günü | 147 | +0,150 | +0,076 | +0,073 [−0,246, +0,441] | %12,9 / %6,9 (P3 farkı CI [+0,8, +11,9] puan) | +0,033 / +0,109 |
| CPI günü | 190 | +0,123 | +0,077 | +0,046 [−0,207, +0,317] | %7,9 / %7,1 | +0,244 / −0,081 |
| NFP günü | 190 | +0,120 | +0,077 | +0,043 [−0,183, +0,282] | %5,3 / %7,2 | +0,108 / −0,017 |
| FOMC açıklaması pencerede | 95 | +0,137 | +0,078 | [−0,353, +0,491] | **%14,7 / %6,9** (CI [+1,0, +15,1]) | P3 +7,6 / +8,2 puan |
| CPI açıklaması pencerede | 91 | +0,385 | +0,071 | [−0,126, +0,797] | %13,2 / %6,9 (CI [−0,6, +13,6]) | ortR +0,531 / +0,102 |
| NFP açıklaması pencerede | 69 | −0,085 | +0,082 | [−0,603, +0,324] | %10,1 / %7,0 | ortR +0,417 / −0,435 (işaret dönüyor) |
| Jackson Hole pencerede | 14 | +0,862 | +0,076 | [−0,422, +2,203] | %21,4 / %7,0 | n çok küçük |

**Rastgele BUY karşılığı** (aynı SL/çıkış, 40.000 rastgele H1 bar): FOMC penceresi ortR +0,109 vs +0,035, P3 %11,3 vs %6,0. CPI +0,070 vs +0,035. NFP −0,053 vs +0,040. Kaynak: repo `out/07_log.txt`.

### Inferences
- Planlı makro takvim, büyük günlerin ana kaynağı değil. En iyi günlerin dağılımı taban orana çok yakın; FOMC hafif bir istisna.
- FOMC pencere etkisi gerçek görünüyor: iki yarıda tutarlı, rastgele BUY'da da var. Mekanizma muhtemelen şu: FOMC sonrası oynaklık patlaması, SL'si FOMC öncesi (sıkışmış) ATR'ye göre konmuş long pozisyonda sağ kuyruğu kalınlaştırıyor. Ancak:
  1. Olay sayısı küçük: 95 işlem, ≥3R olan 14.
  2. Ortalama R farkının CI'sı sıfırı içeriyor.
  3. 18+ özellik arasından seçildi (seçim yükü, E24/E30).
- NFP penceresinin işareti yarılar arasında dönüyor. CPI etkisi esas olarak 2008-16'dan geliyor. İkisi de kanıt değil.

### Gaps
- ECB, BoE, Jackson Hole dışındaki Fed konuşmaları, ISM, perakende satış ve PCE takvimleri derlenmedi. En iyi günlerin üçü (ISM, perakende satış, seçim) bu "ikinci kademe planlı" sınıfta.
- 2011–2012 bazı SEP/basın toplantılı FOMC'lerde açıklama 12:30 ET'deydi. Tüm 2008–2013-03 için 14:15 varsayıldı (±2 saat hata; pencere tanımını az etkiler).
- 2025-10 CPI'ın (hükümet kapanması) gerçek yayın tarihi, önceden ilan edilenden farklı olabilir. Örneklem 2026-06'da bittiği için etkisi yok.

## 3. Girişten önce bilinen makro rejim durumları (VIX, DXY, reel faiz, hisse düşüşü, önceki gün altın hareketi)

### Takeaway
Önceden ilan edilen 12 rejim özelliğinin hiçbiri, ortalama R farkında hem %95 CI'yı sıfırdan ayırıp hem iki yarıda aynı yönde kalmıyor. Tek istisna ters yönde: **önceki gün altın >%1 yükseldiyse** ortalama R −0,188, diğer işlemlerde +0,117. Fark −0,305 [−0,436, −0,164], iki yarıda da negatif (−0,35 / −0,25). Rastgele BUY'daki karşılığı yalnız −0,09. Bu günlerden hiçbiri en iyi 50'de değil. Yani bu bir "büyük gün YOK" bayrağı: rallinin ertesi günü kırılımı kovalamak.

VIX ≥20/25 ve S&P'nin %10+ düşüşte olması R'yi yalnız 2008-16'da artırıyor (+0,19 / +0,21 / +0,15). 2017-26'da etkisi ≈0.

### Cited Findings
Repo `out/feature_tests.csv` (05_tests.py). D-1 = girişten önceki son ABD kapanışı. Rastgele-BUY farkı aynı geometride 40.000 rastgele girişten. "Fark-içinde-fark" = kural farkı − rastgele farkı.

| özellik (ex-ante) | işlemlerin %'si | ortR açık / kapalı | fark [%95 CI] | P(R≥3) açık / kapalı | R payı | yarı farkı 08-16 / 17-26 | rastgele BUY farkı | en iyi 20 / 50'de görülme | gün tabanı |
|---|---|---|---|---|---|---|---|---|---|
| VIX(D-1) ≥ 20 | 36,8 | +0,141 / +0,043 | +0,098 [−0,020, +0,212] | 7,8 / 6,7 | %65,6 | +0,191 / +0,008 | +0,085 | %50 / %38 | %37,0 |
| VIX(D-1) ≥ 25 | 18,3 | +0,178 / +0,057 | +0,121 [−0,028, +0,279] | 8,2 / 6,8 | %41,2 | +0,214 / +0,005 | +0,051 | %25 / %18 | %18,6 |
| VIX 5 günde yükseliyor | 47,0 | +0,069 / +0,088 | −0,019 [−0,133, +0,095] | 7,3 / 6,9 | %41,2 | −0,067 / +0,029 | +0,036 | %35 / %38 | %46,9 |
| DXY 5 günde düşüyor | 48,1 | +0,066 / +0,092 | −0,025 [−0,134, +0,085] | 7,1 / 7,1 | %40,1 | +0,078 / −0,126 | +0,016 | %40 / %46 | %47,9 |
| DXY 20 günde düşüyor | 48,4 | +0,089 / +0,070 | +0,019 [−0,096, +0,130] | 7,4 / 6,8 | %54,5 | +0,054 / −0,014 | +0,032 | %55 / %48 | %48,4 |
| reel faiz (DFII10) 20 günde düşüyor | 51,2 | +0,113 / +0,044 | +0,068 [−0,048, +0,178] | 7,8 / 6,4 | %72,7 | +0,103 / +0,037 | +0,003 | %40 / %50 | %51,8 |
| S&P 252g tepeden ≥%10 aşağıda | 20,0 | +0,143 / +0,063 | +0,080 [−0,069, +0,237] | 7,9 / 6,9 | %36,1 | +0,153 / −0,013 | +0,009 | %30 / %22 | %20,1 |
| **altın önceki gün > +%1** | 12,4 | **−0,188 / +0,117** | **−0,305 [−0,436, −0,164]** | 4,4 / 7,5 (CI [−5,1, −0,9] puan) | −%29,4 | **−0,345 / −0,254** | −0,089 | **%0 / %0** | %12,2 |
| altın önceki gün < −%1 | 7,9 | +0,011 / +0,085 | −0,074 [−0,232, +0,093] | 2,4 / 7,5 | %1,1 | −0,039 / −0,118 | −0,080 | %0 / %2 | %8,4 |
| altın 20 günlük trend yukarı | 56,4 | +0,126 / +0,019 | +0,106 [−0,002, +0,221] | 7,6 / 6,4 | %89,4 | +0,071 / +0,139 | +0,032 | %60 / %62 | %56,4 |
| ATR oranı ≥ 1,5 (yüksek oynaklık) | 10,2 | +0,003 / +0,088 | −0,084 [−0,237, +0,068] | 4,6 / 7,4 | %0,4 | −0,189 / +0,006 | +0,013 | %5 / %4 | %11,3 |
| Pazartesi girişi | 16,9 | +0,047 / +0,086 | −0,039 [−0,176, +0,098] | 6,3 / 7,3 | %10,0 | −0,079 / +0,001 | −0,015 | %10 / %10 | %17,3 |

Genel referans: tüm işlemler +0,079R, P(R≥3) %7,1. Rastgele BUY +0,037R, %6,15. 2008-16 +0,064R (n 1.794), 2017-26 +0,094R (n 1.870).

Arka plan (defter): XAU için makro yön modeli zaten başarısız. Reel faiz/dolar/VIX bağları 2024-26'da işaret değiştirdi (`docs/KAPI_KAYIT_DEFTERI.md` OLD-07; hafıza notu "XAUUSD intraday + macro no edge"). Buradaki soru yön değil, kuyruk yoğunlaşması.

### Inferences
- **Stres rejimi (VIX ≥20/25, hisse düşüşü):** Kuralın R'sini artırıyor gibi görünüyor ama etkinin tamamı 2008-16'dan geliyor (GFC ve 2011). 2017-26'da sıfır. Bu, defterdeki XAU makro bağlarının işaret değiştirmesiyle tutarlı: 2022 sonrası altın düşük VIX'te de yükseldi (merkez bankası alımı). Yarı-dönem kararsızlığı yüzünden ex-ante bayrak olarak zayıf.
- **Altın 20 günlük trendi:** R'nin %89'u trend yukarıyken alınan işlemlerden geliyor (işlemlerin %56'sı). Fark +0,106, CI sınırda [−0,002, +0,221], iki yarıda +. Rastgele BUY'da yalnız +0,032. Defterdeki "XAU yalnız BUY / günlük Donchian + EMA200" bulgusuyla aynı aile. Yeni bilgi değil ama tutarlı.
- **Önceki gün rallisi sonrası kırılım:** Bu, kovalama cezasının XAU'daki karşılığı (defter meta-ders 4, GF-15). Etki büyük, iki yarıda tutarlı ve rastgele BUY'un 3 katı. Ancak 12 özellik içinden bulundu, seçim düzeltmesi yapılmadı.
- **Yüksek ATR rejimi büyük gün getirmiyor, tersine en iyi 20'de neredeyse hiç yok.** En iyi 20'nin ATR oranı medyanı 0,83, tümünde 0,95. Büyük R, SL'nin oynaklık patlamasından ÖNCE dar konduğu günlerde oluşuyor (§5).

### Gaps
- Reel faiz seviyesi (ör. DFII10 < 0) ve 2y getiri, Fed fonları vadeli fiyatlaması, CFTC pozisyonlanması, ETF akımları ve merkez bankası alım verisi test edilmedi.
- VIX kapanışı 21:15 UTC civarı; giriş günü D'de 00:00 sonrası kullanılması güvenli. Ancak yfinance'ın "günlük kapanış" alanının geçmişte gün içi değer içerme riski var (defter E20). Tarihî veride önemsiz kabul edildi.
- Çoklu karşılaştırma: 12 rejim + 6 olay özelliği = 18 test. %5 düzeyinde ~1 sahte "anlamlı" bulgu beklenir. Max-istatistik seçim düzeltmesi yapılmadı.

## 4. En iyi günler kriz rejimlerinde mi toplanıyor?

### Takeaway
Evet, güçlü biçimde, ama bu ex-post etiketle. Literatürden alınan sekiz kriz/rejim penceresi işlem günlerinin %27,8'ini kapsıyor ama toplam R'nin **%86,5**'ini taşıyor. En iyi 20'nin 11'i, en iyi 50'nin 22'si bu pencerelerde. Pencere dışında kalan 2.643 işlemin ortalaması yalnız **+0,015R**: maliyet sonrası pratikte başabaş, aynı geometrideki rastgele BUY'un (+0,037) da altında. Kuralın "kenarı" büyük ölçüde kriz ve rejim dönemlerine ait.

### Cited Findings
Repo `out/regimes.csv` (08_regimes.py). Pencere sınırları olayların bilinen tarihlerinden seçildi, yani ex-post.

| rejim penceresi | işlem | gün payı | ortR | P(R≥3) | R payı | en iyi 20 | en iyi 50 |
|---|---|---|---|---|---|---|---|
| GFC 2008-09 → 2009-06 | 179 | %4,8 | +0,140 | %8,9 | %8,6 | 1 | 3 |
| Avro krizi / ABD not indirimi 2011-07 → 12 | 95 | %2,8 | +0,293 | %6,3 | %9,6 | 2 | 2 |
| Taper / altın çöküşü 2013-04 → 12 | 134 | %3,9 | +0,003 | %3,7 | %0,1 | 0 | 2 |
| COVID 2020-02-15 → 08 | 107 | %3,1 | +0,435 | %13,1 | %16,0 | 2 | 2 |
| Ukrayna 2022-02-15 → 04 | 41 | %1,0 | +0,223 | %9,8 | %3,1 | 1 | 1 |
| SVB 2023-03-08 → 05 | 50 | %1,3 | +0,064 | %10,0 | %1,1 | 1 | 1 |
| İsrail-Hamas 2023-10-07 → 11 | 30 | %0,9 | +0,944 | %23,3 | %9,8 | 1 | 1 |
| MB alımı / tarife 2024-03 → 2025-12 | 385 | %10,1 | +0,288 | %9,4 | %38,2 | 3 | 10 |
| **herhangi bir pencere** | 1.021 | %27,8 | +0,246 | %9,1 | **%86,5** | 11 | 22 |
| pencere dışı | 2.643 | %72,2 | +0,015 | %6,3 | %13,5 | 9 | 28 |

- Yıllık toplam R (`results/posthoc_onepos.txt`): 2009 +56,4 ve 2025 +60,3 en büyük yıllar. 2012–2015 ve 2018 negatif. Bu yıllar altının ayı piyasası ve düşük stres dönemleri.
- 2013 taper çöküşü (Nisan–Aralık) kuralın en kötü rejimi: kriz var ama altın aşağı gidiyordu, kural +0,003.
- Merkez bankası alım rejimi: altın 2024'te 13 aylık zirveyi aşıp art arda rekorlar kırdı. Mart 2024'te yalnız bir ayda beş rekor ([Kitco/Reuters](https://www.kitco.com/news/off-the-wire/2024-03-21/gold-hits-fifth-record-high-march-fed-rate-cut-view)).

### Inferences
- Kriz yoğunlaşmasının mekanizması ikili:
  1. **Yön:** krizlerde altın güvenli liman olarak yukarı sürükleniyor. Taper 2013 tek "kriz ama aşağı" örneği ve kural orada çalışmadı.
  2. **Kuyruk:** kriz günlerinde 20 saatlik pencere birkaç ATR'lik hareket taşıyor.
- **Ex-ante ölçülebilenler:** VIX seviyesi, S&P düşüşü, altının 20 günlük ve 200 günlük trendi, reel faiz trendi. "MB alımı/tarife" rejimi ise yalnız fiyat trendiyle (yeni zirveler) ölçülebiliyor. §3'te VIX ve S&P düşüşü yalnız 2008-16'da işe yaradı; altın trendi iki yarıda da +.
- "Pencere dışı +0,015R" ciddi bir uyarı. Kural, sakin ve yatay altın dönemlerinde spread'e yeniliyor. MK-06'daki "en iyi 20 gün hariç +0,029" gözlemiyle tutarlı.

### Gaps
- Pencereler ex-post seçildi: hangi dönemin "kriz" sayılacağı sonuç bilinerek belirlendi. Bu tablo ex-ante bir kural değildir ve seçim yanlılığı içerir. Örneğin MB alım rejimi sonuçta yükselen altın demek.
- 2026'nın ilk yarısı (en iyi 50'de 2 gün; altın ~$4.500+) sınıflanmadı.

## 5. Ex-ante "büyük gün olası" bayrağına dönüşebilecek bulgular: aday özellikler ve ilk dürüst test

### Takeaway
Haber ve olay tarafında güvenilir bir "büyük gün" bayrağı yok. Büyük günlerin çoğu öngörülemeyen şoklar. Ex-ante adaylar arasında öne çıkanlar:
- **(a) FOMC açıklamasını tutma penceresinde taşımak:** P(R≥3) %14,7 vs %6,9, iki yarıda +. Kırılıma özgü değil, rastgele long'da da var. n=95.
- **(b) Altın 20 günlük trendi yukarı:** ortR +0,106 farkı, iki yarıda +.
- **(c) Negatif bayrak, önceki gün altın >+%1:** −0,305R, iki yarıda −, en iyi 50'de 0 gün. En sağlam bulgu.
- **(d) POST-HOC – ABD tatili / tatil sonrası günü:** En iyi 20'nin 5'i bu günlerde (taban %5,6). ortR +0,391 vs +0,061 [+0,04, +0,63]. Ancak yalnız 2008-16'da (+0,61; 2017-26 +0,06) ve rastgele BUY'da da aynı yönde (+0,22 vs +0,03). Bu bir **ATR-normalizasyon ölçüm etkisi**, haber etkisi değil.

### Cited Findings
**Aday özellikler: mekanizma, ex-ante uygunluk ve ilk test sonucu.** Tüm sayılar repo hesabı: `out/feature_tests.csv`, `out/07_log.txt`, `out/09_log.txt`, `out/10_log.txt`.

| aday | mekanizma | ex-ante mi | ilk test (ortR farkı, P3, yarılar, rastgele BUY) | durum |
|---|---|---|---|---|
| FOMC açıklaması tutma penceresinde (`F_fomcwin`) | FOMC sonrası oynaklık patlaması; SL FOMC öncesi sıkışık ATR'ye göre konmuş; gevşek Fed sürprizleri altını yukarı itiyor (2019-06, 2024-03, 2013-09) | Evet: takvim haftalar önce ilan edilir | ortR +0,137 vs +0,078 (CI sıfırı içeriyor). **P3 %14,7 vs %6,9, CI [+1,0, +15,1] puan, yarılar +7,6 / +8,2.** Rastgele BUY P3 %11,3 vs %6,0 | kuyruk ↑ tutarlı ama küçük n (14 kuyruk işlemi) ve rastgele long'da da var → **C** |
| CPI penceresi | aynı mekanizma | Evet | ortR +0,385 vs +0,071; P3 %13,2 vs %6,9 (CI alt sınırı −0,6). Ortalama etki çoğunlukla 2008-16'da | **C−** |
| NFP penceresi | aynı | Evet | işaret yarılar arasında dönüyor (+0,42 / −0,44) | **X** |
| VIX(D-1) ≥ 20/25 | stres → güvenli liman sürüklenmesi | Evet | +0,098 / +0,121; yalnız 2008-16 (+0,19 / +0,21), 2017-26 ≈0 | **X/C** (rejime bağlı; 2022 sonrası XAU-VIX bağı zayıf) |
| S&P ≥%10 düşüşte | aynı | Evet | +0,080; 2017-26'da −0,013 | **X** |
| reel faiz 20 günde düşüyor | düşen fırsat maliyeti | Evet (D-2) | +0,068 [−0,048, +0,178]; yarılar +0,10 / +0,04; rastgele BUY farkı +0,003 | **C** (yönü doğru, gücü zayıf) |
| altın 20 günlük trend yukarı | trend devamı, rejim kalıcılığı | Evet | +0,106 [−0,002, +0,221]; yarılar +0,07 / +0,14; R'nin %89'u | **B−** (defterdeki günlük swing / EMA200 bulgusunun yansıması; yeni değil) |
| **önceki gün altın > +%1 → büyük gün YOK** | kovalama/tükenme; hareketin büyük kısmı önceki gün gerçekleşmiş | Evet | **−0,305 [−0,436, −0,164]; yarılar −0,35 / −0,25; rastgele BUY −0,09; en iyi 50'de 0** | **B** (en sağlam aday; seçim düzeltmesi ve broker kasası sınaması gerek) |
| ATR oranı ≥1,5 | yüksek oynaklık zaten fiyatlanmış, SL geniş | Evet | −0,084; P3 %4,6 vs %7,4 | **X** (bayrak değil; ters gradyan) |
| *POST-HOC* düşük ATR oranı (alt beşte bir, ≤0,73) | dar SL + oynaklığın ortalamaya dönüşü → büyük R | Evet | ortR +0,122 (yarılar +0,14 / +0,10), P3 %10,7 (iki yarıda %10,7); en üst beşte bir +0,049 / %4,8. Rastgele BUY P3 %10,1 → %3,5 (aynı gradyan) ama ortR +0,022 (kırılım katkısı ~+0,10) | **C (post-hoc)**, ön-kayıtla yeniden sınanmalı |
| *POST-HOC* ABD tatili / tatil sonrası günü | tatil saatlerinde ATR14 sıkışır, ertesi günün normal hareketi büyük R olur (2012-11-23 SL $1,7; 2010-01-04 SL $1,0) | Evet: NYSE takvimi | ortR +0,391 vs +0,061 [+0,038, +0,628]; yarılar **+0,61 / +0,06**; P3 %10,2 vs %6,9. Rastgele BUY +0,219 vs +0,025. En iyi 20'de 5, en kötü 20'de 0 | **C (post-hoc; ölçüm etkisi, 2017 sonrası sönmüş)** |

**R yerine sabit-nominal % getiriyle bakınca** (lot sabit, risk sabit değil):
- Yoğunlaşma daha da artıyor: en iyi 20 gün % getirinin %80'i, en iyi 50 gün %158'i.
- Ama en iyi günlerin kümesi değişiyor: R-ilk20 ile %-ilk20'nin yalnız 5 günü ortak.
- %-ilk20, GFC (2008-11/12, 2009-01/03), COVID (2020-03-23), Brexit (2016-06-24), FOMC "tapering yok" (2013-09-18), FOMC QE (2009-03-18) ve tarife (2025-04-09, 2025-05-05) günleriyle dolu. Yani dolar bazında büyük günler daha da kriz ve Fed ağırlıklı.
- Tatil-sonrası "büyük R" günleri dolar bazında küçük hareketler: 2012-11-23 yalnız %1,0, 2020-02-18 %1,1.

Kaynak: repo hesabı (04→10 betikleri; % = R×1,5×ATR/giriş fiyatı).

### Inferences
- Pratik çıkarım: "büyük günü önceden bilmek" pek mümkün değil, çünkü katalizörlerin çoğu öngörülemeyen şoklar. Kural değerini bu şoklara açık olmasından (20 saatlik tutma, TP yok) alıyor.
- Ex-ante iyileştirme, büyük günü seçmekten çok **kötü/boş günleri elemek** yönünde daha umutlu. Önceki gün >%1 ralliden sonra kırılımı atlamak bunun örneği. Bu, rastgele long'dan bağımsız bir kırılım-kovalama cezası gibi görünüyor.
- Tatil-sonrası ve düşük ATR bulguları uyarıcı: R metriği ATR'ye normalize olduğu için en iyi gün listesinin bir kısmı ölçüm etkisi. Canlıda sabit lotla işlem yapılırsa bu günler dolar olarak küçük; sabit riskle (lotu SL$'a göre büyütmek) yapılırsa büyük olur. Ama aynı zamanda dar SL'de spread ve kayma payı büyür.
- FOMC kuyruğu ancak "olay haftasında kırılım varsa tutma süresini uzat / TP koyma" gibi bir **çıkış** ayarına dönüşebilir. Girişi filtrelemek için ortalama R kanıtı yok.

### Gaps
- Tüm testler aynı Dukascopy 2008–2026-06 verisinde. Broker kasası (2026-06-17 → 10-14) ayrı sınanmadı.
- 18 ön-tanımlı + 2 post-hoc özellik için max-istatistik seçim düzeltmesi yapılmadı (defter E24/E30). "Önceki gün >%1" adayının p_sel'i bilinmiyor.
- Plasebo olarak yalnız aynı geometride rastgele BUY kullanıldı. P1 tarzı aynı yıl ve aynı UTC saatli gün kaydırma plasebosu bu özellikler için koşulmadı.
- Tatil etkisinin 2017 sonrası neden sönükleştiği belirsiz. Olası açıklama: Dukascopy tatil likiditesindeki değişim; doğrulanmadı.
- Haber tarafında birincil kaynaklara (Reuters/Bloomberg terminali) erişilmedi. Alıntılar Reuters sendikasyon sayfalarından (Kitco, Business Standard, finance.cz) ve CNBC'den.

## Defter satırı önerileri

(`docs/KAPI_KAYIT_DEFTERI.md` §2.6'ya, MK-06'nın altına; deftere bu ajan yazmadı.)

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| MK-07 | 2026-10-16 | **R0B_G1 (MK-04) en iyi günlerinin makro ve haber bağlamı ile ex-ante "büyük gün" bayrakları** (`research/xau_best_days_20261015/makro/`; not `research_notes/XAU kırılım kuralının en iyi günleri/makro_haber_baglami.md`). Duka H1 2008-01 → 2026-06-16, tek pozisyon 3.664 işlem / 3.047 gün; gün = giriş UTC günü. Makro D-1 (DFII10 D-2); takvim FOMC planlı, BLS CPI/NFP tarihleri; 18 ön-tanımlı özellik; gün-blok bootstrap; yarılar 2008-16 / 2017-26; aynı geometride 40.000 rastgele BUY | En iyi 20 gün R'nin **%61,6**'sı (iddia edilen %72 tutmadı), en iyi 50 gün %127. En iyi 20'nin yalnız 2'si planlı FOMC/CPI/NFP olayı, 11'i öngörülemeyen şok (AIG, savaş, SVB, tarife, COVID), 4'ü FOMC/CPI/NFP dışı takvimli olay (seçim, ISM, perakende, borç tavanı), 3'ü tatil sonrası. FOMC/CPI/NFP günü taban %13,1 vs en iyi 20 %15 → yoğunlaşma yok; olay günü ortR farkı +0,035 [−0,13, +0,20]. Kriz pencereleri (ex-post) günlerin %27,8'i ama R'nin %86,5'i; pencere dışı +0,015R (rastgele BUY +0,037'nin altında). VIX ≥20/25 ve S&P düşüşü yalnız 2008-16'da +, 2017-26'da ≈0. FOMC penceresinde P(R≥3) %14,7 vs %6,9 (iki yarıda +) ama rastgele long'da da var (%11,3 vs %6,0) | X (haber/olay takvimiyle büyük gün seçimi) · C (FOMC kuyruğu, yalnız çıkış ayarı adayı) |
| MK-08 | 2026-10-16 | **Önceki gün altın > +%1 ise R0B_G1 kırılımını atla** (kovalama cezası; ex-ante, Duka önceki UTC günü) | 455 işlem (%12,4): ortR −0,188 vs +0,117, fark −0,305 [−0,436, −0,164]; yarılar −0,35 / −0,25; rastgele BUY'da yalnız −0,09; en iyi 50 günde 0. 18 özellik içinden bulundu; seçim düzeltmesi, P1 plasebosu ve broker kasası (2026-06 → 10) sınaması YAPILMADI | B− ADAY (ön-kayıtla yeniden sına → gölge) |
| MK-09 | 2026-10-16 | *POST-HOC*: ATR-normalizasyon etkisi. ABD tatili / tatil sonrası günü ve düşük ATR oranı (ATR / önceki 2.000 bar medyanı ≤0,73) | Tatil/tatil sonrası: en iyi 20'nin 5'i (taban %5,6); ortR +0,391 vs +0,061 [+0,04, +0,63] ama yalnız 2008-16 (+0,61 / +0,06); rastgele BUY'da da +0,22 vs +0,03 → haber değil, dar SL ölçüm etkisi. Düşük ATR beşte biri P3 %10,7 (iki yarıda) vs en üst %4,8, rastgele BUY'da aynı gradyan. Sabit nominal % ile en iyi 20 günün yalnız 5'i R listesiyle ortak | C (post-hoc; R metriği yorumu uyarısı) |

**Yeni kanıt hatası adayı (§1):**

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E31 | **ATR'ye normalize R'de "en iyi günler" listesi ölçüm etkisi içerir.** Tatil / ince piyasa saatleri ATR14'ü sıkıştırır; ertesi günün sıradan hareketi 10R görünür. "Büyük gün = büyük haber" varsayımı yanıltır | MK-07: R0B_G1 en iyi 20 gününün 5'i ABD tatili sonrası (2012-11-23 SL $1,7, %1,0 hareketle 10,4R); sabit nominal % ölçüsünde en iyi 20 günün yalnız 5'i ortak | En iyi gün analizini hem R hem sabit-nominal % ile yap; SL$ ve ATR oranını tabloya koy; tatil/yarım gün bayrağını kontrol et |
