# TradingView topluluk (kullanıcı yapımı) göstergeleri × ForexSAI

Tarih: 2026-10-25 · Claude Code · Resmî katalog karşılaştırmasının devamı: [../sistem_karsilastirma_claude/RAPOR.md](../sistem_karsilastirma_claude/RAPOR.md)

Çıktılar:
- [AILELER.md](AILELER.md): 71 ailenin tablosu, en popüler örnekleri, sistem durumu ve defter kanıtı.
- [KATALOG.csv](KATALOG.csv): 33.389 scriptin tamamı; ad, yazar, boost, yıl, tür, aile ve bağlantı. Excel'de açılır.
- Üreticiler: [crawl_tv_community.py](crawl_tv_community.py) ve [classify.py](classify.py). Ham `data/*.jsonl` dosyaları git dışında.

## 1. Ne toplandı, nasıl?

TradingView Public Library'de 150.000'i aşkın script var. Merkezî bir indirme listesi yok ve sıralama yalnız "en yeni" ya da "popülerlik" seçeneklerini sunuyor; tüm zamanların sıralaması yok. Bu yüzden iki kanaldan sayfa sayfa topladım:

| Kanal | Akış | Kayıt |
|---|---:|---:|
| Tag akışları (`/scripts/<tag>/`): kategori tag'leri + gösterge adları | 145 | 48.019 |
| Arama akışları (`/scripts/search/<q>/`): 31 ünlü Pine yazarı (LazyBear, ChrisMoody, LuxAlgo, KivancOzbilgic, jdehorty, HPotter, LonesomeTheBlue…) + 54 ünlü gösterge adı + Editors' picks arşivi | 85 | 20.673 |
| **Tekrarlar ayıklandıktan sonra benzersiz script** | | **33.389** |

Bunların 29.628'i gösterge, 3.118'i strateji, 643'ü kütüphane. Yıllara göre 2014'ten 2026'ya uzanıyorlar.

Kayıtlar yalnız kamuya açık liste sayfalarından okundu. Giriş yapılmadı ve hiçbir scriptin kodu indirilmedi.

**Sınırlar:**
- Her akış en fazla 1.000 kayıt döndürüyor. RSI, ATR, EMA gibi büyük tag'lerde bu yalnız en yeni 1.000 script demek. Örneklem bu yüzden yeniye kayık: kayıtların %41'i 2026 tarihli. Eski ünlüler yazar/isim aramalarıyla tamamlandı.
- Boost bir **popülerlik** ölçüsü. Kârlılık, doğruluk ya da yeniden çizmeme (non-repaint) hakkında bilgi vermez.
- Açık kaynak / korumalı ayrımı liste verisinde ayrışmıyor, bu yüzden raporlanmadı.
- Aile ataması ad ve açıklama üzerinden regex ile yapıldı. Bir script birden fazla aileye düşebilir; örneğin LuxAlgo SMC hem yapı, hem OB, hem FVG ailesinde sayılıyor. Bu yüzden aile sayıları toplanamaz. Scriptlerin %8,8'i (2.950) hiçbir aileye düşmedi; en popülerleri `AILELER.md`'nin sonunda listeli.

## 2. Topluluğun en popüler 15 göstergesi ve bizdeki karşılığı

| # | Script (yazar, yıl) | Boost | Bizde |
|---:|---|---:|---|
| 1 | Smart Money Concepts [LuxAlgo] 2022 | 176.279 | **Var**: SMC modeli (BOS/CHoCH/OB/FVG) |
| 2 | Squeeze Momentum [LazyBear] 2014 | 117.568 | **Benzeri**: bot SQZ = ATR oranı; BB-in-Keltner değil. Defter: C/X |
| 3 | SuperTrend [KivancOzbilgic] 2020 | 84.239 | **Yok** |
| 4 | MacD Custom MTF [ChrisMoody] 2014 | 82.550 | **Var**, ama bizim ML/Pulse MACD'mizin sinyal çizgisi 0. Defter: X |
| 5 | Support & Resistance Levels with Breaks [LuxAlgo] | 66.714 | **Var**: pivot/fraktal S/R. Defter: X (HK-03) |
| 6 | CM Williams VIX Fix [ChrisMoody] 2014 | 66.018 | **Benzeri**: gerçek VIX kullanıyoruz (VIXREG, A). VIX Fix sentetik |
| 7 | Market Structure Break & Order Block [EmreKb] | 64.104 | **Var**: SMC |
| 8 | WaveTrend Oscillator [LazyBear] 2014 | 61.320 | **Yok** |
| 9 | UT Bot Alerts [QuantNomad] 2020 | 60.939 | **Yok** (ATR trailing-stop yön değişimi) |
| 10 | ICT Killzones + Pivots [TFO] 2023 | 59.141 | **Benzeri**: seans kapılarımız var, ICT zaman modelleri yok |
| 11 | Trendlines with Breaks [LuxAlgo] 2022 | 53.583 | **Yok** |
| 12 | Bollinger + RSI Double Strategy [ChartArt] | 49.083 | Bileşenleri var. Defter: X |
| 13 | Support Resistance Channels [LonesomeTheBlue] | 48.117 | **Var** (S/R bölgeleri) |
| 14 | Sessions [LuxAlgo] | 43.299 | **Var**: seans kapıları (A/B) |
| 15 | Liquidity Swings [LuxAlgo] 2023 | 41.336 | **Var**: SMC likidite + fakeout (NDX A) |

Devamında Order Block Finder, Lorentzian Classification (jdehorty), Nadaraya-Watson Envelope, Breakout Probability (Zeiierman), SuperTrend AI, Chandelier Exit ve Pivot Point Supertrend geliyor. İlk 100'ün tamamı `KATALOG.csv`'nin başında.

## 3. 71 aile × bizim sistem

| Sistemde | Aile | Script (aile üyeliği) | Toplam boost |
|---|---:|---:|---:|
| **K** karar yolunda | 29 | 43.799 | 30,4 M |
| **~** benzeri var, aynı formül değil | 17 | 19.919 | 13,9 M |
| **B / M / G / R** bağlam, ML girdisi, gölge, risk | 8 | 5.951 | 4,6 M |
| **–** hiç yok | 17 | 8.249 | 6,7 M |

Boost ağırlığıyla topluluk ilgisinin **~%55'i** bizim zaten karar yolunda kullandığımız ailelerde. Bunlar S/R, ATR, swing/fraktal, momentum, RSI, likidite, SMC yapısı, FVG, OB, seans, MACD ve Bollinger. Topluluğun en çok ilgilendiği konularla sistemimizin kapsamı büyük ölçüde örtüşüyor.

### Bizde hiç olmayan 17 aile (popülerliğe göre)

| Aile | Script | Boost | En bilinen örnek | 4 piyasamız için not |
|---|---:|---:|---|---|
| Gelişmiş/uyarlanabilir MA (Hull, KAMA, ALMA, T3, ZLEMA, JMA) | 1.237 | 900 K | CM Ultimate MA MTF | Gecikmeyi azaltır; yön kenarı iddiası yok. EMA kesişimi X (HK-01) |
| **Supertrend ve türevleri** | 693 | 900 K | SuperTrend (Kivanc), Pivot Point ST, SuperTrend AI | ATR bandı + trend dönüşü. **En popüler eksik aile**; sınanmadı |
| Otomatik trend çizgisi kırılımı | 514 | 623 K | Trendlines with Breaks [LuxAlgo] | Pivot tabanlı ve **yeniden çizme riski** var. S/R kırılımı X (HK-03) |
| Heikin Ashi / Renko / Kagi | 726 | 496 K | Scalping PullBack Tool | Mum dönüştürme. Renko geriye dönük testte yanıltır |
| Ehlers / DSP (SuperSmoother, MESA, Laguerre) | 631 | 363 K | CM Laguerre PPO | Filtre aileleri; sınanmadı |
| **HalfTrend / UT Bot / SSL / Range Filter** | 259 | 347 K | UT Bot Alerts | ATR trailing yön değişimi; Supertrend'in akrabası |
| Ichimoku | 703 | 285 K | Ichimoku (HPotter) | Yalnız boş sütun adı var. Chikou ileri kaydırma = **sızıntı tuzağı** |
| **WaveTrend / Market Cipher** | 212 | 265 K | WaveTrend [LazyBear] | Kanal-normalize osilatör; sınanmadı |
| Keltner kanalı | 397 | 260 K | Squeeze Momentum'un parçası | BB-in-KC sıkışması bizim SQZ'den farklı tanım |
| Elliott / Wyckoff | 290 | 248 K | Elliott Wave [LuxAlgo] | Öznel. ZigZag'a dayalı olduğu için **yeniden çizer** |
| CCI | 241 | 222 K | (çoklu diverjans scriptleri) | Yalnız araştırma endpoint'inde var |
| Kernel regresyon / Nadaraya-Watson | 166 | 221 K | Nadaraya-Watson Envelope [LuxAlgo] | LuxAlgo'nun orijinali **yeniden çiziyor**; nedensel sürüm gerekir |
| Gann / yuvarlak sayı / Murrey | 388 | 209 K | CM Gann Swing | Yuvarlak sayı hücresi elendi (GF-02) |
| Fisher / Schaff | 225 | 134 K | | Sınanmadı |
| **QQE** | 64 | 131 K | QQE signals | Az script ama **en yüksek medyan boost (630)**; sınanmadı |
| Kalman | 143 | 81 K | Kalman Trend Levels [BigBeluga] | Sınanmadı |
| Alarm/bot/backtest çatısı | 1.360 | 968 K | | Gösterge değil, kapsam dışı |

### Benzeri olan ama aynı formülü kullanmadığımız aileler

- **Squeeze/TTM:** bizdeki SQZ ATR14/ATR100 oranı; TTM'in Bollinger-Keltner tanımını kullanmıyoruz.
- **VIX Fix:** sentetik VIX yerine gerçek VIX kullanıyoruz.
- **ICT zaman modelleri** (killzone, silver bullet, PO3, CRT): seans kapılarımız var ama bu modeller yok.
- **Lorentzian/kNN:** analog-kNN denendi, X.
- **Delta/CVD/footprint:** bizdeki CVD mum renginden türetilen sentetik değer; gerçek tick-delta yok.
- **Diğerleri:** Darvas/aralık tespiti, N-bar dönüş dedektörleri ve üst zaman dilimi mum katmanı.

Hepsi `AILELER.md`'de.

## 4. Yön tahmini açısından okuma

1. **Topluluk popülerliği ile bizim kanıtımız ters yönde.** Kendi sızıntısız sınamalarımızda çöken aileler topluluğun en sevdikleri arasında:

   | Aile | Topluluktaki boost | Bizim sınamamız |
   |---|---:|---|
   | S/R kırılımı | 3,6 M | X (HK-03) |
   | RSI diverjansı | 1,1 M | X (HK-04) |
   | MACD kesişimi | | X (OLD-12) |
   | Mum formasyonları | | X (MK-01/02/05) |
   | Klasik formasyon SELL'leri | | X (%22,6) |
   | Hacim profili değer alanı | | X (HK-02) |

   Boost, bir göstergenin grafikte ne kadar ikna edici göründüğünü ölçüyor; sonraki barı ne kadar iyi öngördüğünü değil.
2. **Yeniden çizme (repaint) uyarısı.** Bazı popüler aileler geçmişte geleceği görüyor: Nadaraya-Watson (LuxAlgo orijinali), ZigZag/Elliott, pivot tabanlı trend çizgileri, SMC "onaylı" yapılar ve Ichimoku Chikou. Bunlar TradingView grafiğinde mükemmel görünür ama canlıda aynı sinyali vermez. Defterin E1/E16 sızıntı dersleri burada birebir geçerli. Bu ailelerden biri sınanacaksa, her bar yalnız o ana kadarki veriyle hesaplanmalı (`_bars_upto.py` mantığı).
3. **Sınanmaya değer olabilecek eksikler.** Supertrend, UT Bot/HalfTrend, QQE ve WaveTrend:
   - Neden bunlar: hepsi nedensel (yeniden çizmiyor) ve ATR/EMA tabanlı. Bizim veriyle (MT5 M1→M5/M15/H1) doğrudan hesaplanabiliyorlar. Topluluk ilgisi de en yüksek bunlarda.
   - Ama: defterdeki örüntü, fiyat-türevi trend/osilatör kurallarının bu dört piyasada **tek başına** kenar vermediği yönünde. Ayakta kalanlarımızın hepsi rejim/bağlam: VIX, EMA50 hizası, seans, uzak hedef, NDX fakeout. Gerçekçi beklenti, bunların en fazla **mevcut bir girişe filtre** olarak katkı vermesi.
   - Sınama protokolü: ön kayıt, kapısız taban, plasebo, bağımsız dönem ve 2. KURAL icra koşulları. Backlog'da (bl_c105e8c756) aday sete eklendi.

## 5. Tekrar üretme

```bash
cd research/indicator_atlas_20261025/topluluk_taramasi
python3 crawl_tv_community.py probe && python3 crawl_tv_community.py crawl 42
python3 crawl_tv_community.py probe-search && python3 crawl_tv_community.py crawl-search 42
python3 classify.py
```

Tarama ~2.800 sayfa ve ~1,2 GB indirme demek: 4 paralel istek, istek arası 0,35 sn, ~25 dk. Sonuç her gün değişir, çünkü topluluğa her gün yüzlerce yeni script ekleniyor.
