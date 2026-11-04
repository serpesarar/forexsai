# TradingView — Türkçe gösterge ve araç kataloğu

İnceleme tarihi: 25 Ekim 2026.

## Kapsam ve tamamlanma durumu

Bu belge, TradingView Yardım Merkezi’nin aşağıdaki dört resmî bölümünde listelenen **239 sayfanın tamamının** adını, Türkçe çalışma özetini ve doğrudan kaynak bağlantısını içerir:

| Resmî bölüm | Sayfa sayısı |
|---|---:|
| Built-in Indicators | 209 |
| Chart Patterns | 20 |
| Volume Profiles | 8 |
| TPO | 2 |

**Bu sayı, TradingView üzerindeki bütün benzersiz indikatörlerin sayısı değildir.** Yardım kataloğunda kripto ağ metrikleri, analist tahminleri, genel kullanım yazıları ve stratejiler de bulunur. Aynı adlı iki Transaction fees sayfası ayrı kaynaklarıyla korunmuştur. Dolayısıyla 239 sayfa = 239 farklı teknik indikatör değildir.

TradingView’in topluluk kütüphanesi, resmî Pine belgelerine göre 150.000’den fazla script içerir; bu toplam indikatör, strateji ve kütüphaneleri kapsar. Bu dosya topluluk yayınlarının toplu envanterini, hesap sahibinin özel scriptlerini, davet gerektiren yayınları veya bütün finansal veri alanlarını kapsamaz. Ayrı Patterns menüsündeki bütün mum formasyonlarının eksiksiz canlı arayüz envanteri de doğrulanmamıştır. Kullanıcı hesabına giriş yapılmamıştır ve bu belge bir grafik üzerinde tek tek uygulama testi değildir.

Her satırdaki ad, ilgili resmî açıklamayı açar. Türkçe özetler açıklamalardan hazırlanmıştır; kaynak kodu doğrulaması veya performans testi anlamına gelmez. Parametrelerin tamamı, veri gereksinimleri ve ayrıntılı hesap kuralları bağlantılı sayfalardadır.

## Okuma anahtarı

- **Trend:** Fiyatın yönünü veya yönlü hareketin tutarlılığını inceler. Trend gücü ile trend yönü aynı ölçü değildir.
- **Momentum:** Fiyat değişiminin hızını/büyüklüğünü veya aralık içindeki konumunu ölçer.
- **Oynaklık:** Hareket büyüklüğünü inceler; ATR gibi araçlar tek başına yön söylemez.
- **Hacim:** Kullanılan piyasa ve veri kaynağı önemlidir. Alt mumlardan üretilen Volume Delta/CVD, doğrudan borsa emir akışını ölçmez.
- **Seviye ve formasyon:** Destek/direnç veya fiyat yapısı işaretler. Pivot onayı gecikebilir; Zigzag’ın son bacağı ve otomatik çizimler değişebilir.
- **Ağ verisi / türev verisi / temel veri:** Fiyat mumlarından türeyen klasik teknik indikatörlerden farklı veri kaynaklarına dayanır.

“Aşırı alım” tek başına satış, “aşırı satım” tek başına alış emri değildir. Tarihsel çizimlerde güzel görünmek, karar anında aynı bilginin mevcut olduğunu veya gerçek maliyetler sonrası kârlılığı göstermez. Burada yeni bir işlem filtresi önerilmemiş veya canlı sisteme değişiklik yapılmamıştır.

## 1. Built-in Indicators — 209 resmî sayfa

| No | Resmî ad / kaynak | Çalışma özeti |
|---:|---|---|
| 1 | [1 year active supply %](https://www.tradingview.com/support/solutions/43000773986-1-year-active-supply/) | Son 365 günde en az bir kez hareket eden benzersiz coin miktarının arz içindeki payını izler. |
| 2 | [24-hour Volume](https://www.tradingview.com/support/solutions/43000668584-24-hour-volume/) | Son 24 saatteki işlem hacmini para birimi cinsinden toplar; takvim günü hacminden farklı bir kayan penceredir. |
| 3 | [Accumulation Distribution (ADL)](https://www.tradingview.com/support/solutions/43000501770-accumulation-distribution-adl/) | Kapanışın mum aralığındaki konumunu hacimle ağırlıklandırıp biriktirir; fiyatla uyumsuzluklar incelenebilir. |
| 4 | [Active addresses with contracts](https://www.tradingview.com/support/solutions/43000778587-active-addresses-with-contracts/) | Gönderen, alan veya akıllı sözleşme çağıran aktif benzersiz adresleri sayar; yalnız başarılı işlemleri içerir. |
| 5 | [Addresses with balance ≥ X (% of supply)](https://www.tradingview.com/support/solutions/43000773987-addresses-with-balance-x-of-supply/) | Toplam arzın seçilen yüzdesine eşit veya daha fazla bakiye tutan adreslerin sayısını gösterir. |
| 6 | [Addresses with balance ≥ X (USD)](https://www.tradingview.com/support/solutions/43000773988-addresses-with-balance-x-usd/) | Güncel dolar değeri seçilen eşiği aşan kripto bakiyelerine sahip adresleri sayar. |
| 7 | [Advance/Decline Line](https://www.tradingview.com/support/solutions/43000589092-advance-decline-line/) | Yükselen hisse sayısından düşenleri çıkarıp farkı biriktirir; piyasa hareketinin yaygınlığını gösterir. |
| 8 | [Advance/Decline Ratio](https://www.tradingview.com/support/solutions/43000589093-advance-decline-ratio/) | Yükselen hisse sayısını düşen hisse sayısına böler; piyasa genişliği ölçüsüdür. |
| 9 | [Advance/Decline Ratio (Bars)](https://www.tradingview.com/support/solutions/43000644914-advance-decline-ratio-bars/) | Seçilen sembolün belirli penceredeki yükseliş mumlarını düşüş mumlarına oranlar; hisse evreni genişliği değildir. |
| 10 | [Analyst price forecast](https://www.tradingview.com/support/solutions/43000678409-analyst-price-forecast/) | Veri sağlayıcısının analist tahminlerini minimum, ortalama ve maksimum fiyat seviyeleri olarak sunar; teknik fiyat formülü değildir. |
| 11 | [Arnaud Legoux Moving Average](https://www.tradingview.com/support/solutions/43000594683-arnaud-legoux-moving-average/) | Gauss ağırlıkları ve kaydırma parametresiyle fiyatları ortalar; yumuşaklık ile tepki hızını ayarlamaya çalışır. |
| 12 | [Aroon Indicator](https://www.tradingview.com/support/solutions/43000501801-aroon-indicator/) | Pencerenin en yüksek ve en düşük fiyatından bu yana geçen mum sayılarını iki çizgiye dönüştürür. |
| 13 | [Aroon Oscillator](https://www.tradingview.com/support/solutions/43000773004-aroon-oscillator/) | Aroon Up değerinden Aroon Down değerini çıkarır; sonucu -100 ile +100 arasında gösterir. |
| 14 | [Auto fib extension](https://www.tradingview.com/support/solutions/43000612397-auto-fib-extension/) | Seçilen fiyat salınımlarından Fibonacci uzatma seviyelerini otomatik çizer; olası devam hedeflerini görselleştirir. |
| 15 | [Auto Fib Retracement](https://www.tradingview.com/support/solutions/43000585089-auto-fib-retracement/) | Fiyat salınımının iki ucuna Fibonacci geri çekilme oranları uygular; uç noktalar değişince seviyeler güncellenebilir. |
| 16 | [Auto key levels](https://www.tradingview.com/support/solutions/43000783958-auto-key-levels/) | Farklı dönemlerin POC, değer alanı sınırları ve OHLC seviyelerini hacim histogramı yerine yatay çizgilerle gösterir. |
| 17 | [Auto Pitchfork](https://www.tradingview.com/support/solutions/43000657911-auto-pitchfork/) | Geçmiş salınımlardan otomatik Andrews Pitchfork kanalı oluşturur; merkez ve paralel çizgiler referans seviyeleridir. |
| 18 | [Auto trendlines](https://www.tradingview.com/support/solutions/43000741165-auto-trendlines/) | Zigzag pivotlarını bağlayarak küçük ve büyük destek/direnç çizgileri üretir; yeni pivotlar çizimleri değiştirebilir. |
| 19 | [Average Daily Range (ADR) indicator](https://www.tradingview.com/support/solutions/43000695003-average-daily-range-adr-indicator/) | Günlük en yüksek ve en düşük fiyat arasındaki farkların ortalamasını hesaplar; tipik günlük hareket aralığını gösterir. |
| 20 | [Average Directional Index (ADX)](https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/) | Yönlü hareket ölçülerinden trendin gücünü hesaplar; ADX tek başına yükseliş veya düşüş yönünü söylemez. |
| 21 | [Average transaction volume](https://www.tradingview.com/support/solutions/43000773989-average-transaction-volume/) | Zincir üzerindeki toplam işlem değerini işlem adedine böler; ortalama transfer büyüklüğü hakkında bilgi verir. |
| 22 | [Average True Range (ATR)](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/) | Yüksek-düşük aralığı ve önceki kapanışa olan boşlukları içeren true range değerlerini yumuşatır; yön değil oynaklık ölçer. |
| 23 | [Awesome Oscillator (AO)](https://www.tradingview.com/support/solutions/43000501826-awesome-oscillator-ao/) | Mum orta fiyatının 5 dönemlik SMA değerinden 34 dönemlik SMA değerini çıkarır; momentum histogramı üretir. |
| 24 | [Balance of Power (BOP)](https://www.tradingview.com/support/solutions/43000589100-balance-of-power-bop/) | Kapanış-açılış farkını yüksek-düşük aralığına oranlar; mum içindeki alıcı/satıcı dengesini yaklaşık ölçer. |
| 25 | [Basis](https://www.tradingview.com/support/solutions/43000784536-basis/) | Vadeli fiyat ile referans endeks fiyatı arasındaki mutlak fiyat farkını gösterir. |
| 26 | [BBTrend](https://www.tradingview.com/support/solutions/43000726749-bbtrend/) | Kısa ve uzun iki Bollinger bandı hesabını karşılaştırıp trend yönü ve gücü için histogram oluşturur. |
| 27 | [Block height](https://www.tradingview.com/support/solutions/43000778555-block-height/) | Başlangıç bloğundan beri ana zincire eklenen blokların toplam yüksekliğini gösterir. |
| 28 | [Blocks mined](https://www.tradingview.com/support/solutions/43000778556-blocks-mined/) | Seçilen dönem boyunca ana zincire eklenen yeni blok sayısını gösterir. |
| 29 | [Bollinger Bands (BB)](https://www.tradingview.com/support/solutions/43000501840-bollinger-bands-bb/) | Hareketli ortalamanın çevresine standart sapma bantları yerleştirir; bantlar oynaklığa göre genişler veya daralır. |
| 30 | [Bollinger Bands %b (%b)](https://www.tradingview.com/support/solutions/43000501971-bollinger-bands-b-b/) | Fiyatın alt ve üst Bollinger bandına göre konumunu normalize eder; bant dışındaki fiyatlarda 0-1 aralığı aşılabilir. |
| 31 | [Bollinger BandWidth (BBW)](https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/) | Üst-alt Bollinger bandı farkını orta banda oranlar; bant daralması ve genişlemesini izler. |
| 32 | [Bollinger Bars](https://www.tradingview.com/support/solutions/43000742575-bollinger-bars/) | Mum gövdesini ve fitillerini farklı renklerle, sabit görsel genişlikle sunar; alternatif mum gösterimidir. |
| 33 | [Bull Bear Power](https://www.tradingview.com/support/solutions/43000717955-bull-bear-power/) | En yüksek ve en düşük fiyatın EMA çevresindeki uzaklıklarından boğa ve ayı baskısı bileşenleri üretir. |
| 34 | [Chaikin Money Flow (CMF)](https://www.tradingview.com/support/solutions/43000501974-chaikin-money-flow-cmf/) | Kapanışın mum aralığındaki konumuyla ağırlıklandırılan hacmi dönem boyunca toplar ve toplam hacme böler. |
| 35 | [Chaikin Oscillator](https://www.tradingview.com/support/solutions/43000501979-chaikin-oscillator/) | Accumulation/Distribution çizgisinin kısa EMA değerinden uzun EMA değerini çıkarır; hacim akışının momentumunu gösterir. |
| 36 | [Chande Kroll Stop](https://www.tradingview.com/support/solutions/43000589105-chande-kroll-stop/) | True range ve fiyat uçlarından uzun/kısa pozisyonlar için oynaklığa bağlı takip eden stop çizgileri üretir. |
| 37 | [Chande Momentum Oscillator (CMO)](https://www.tradingview.com/support/solutions/43000589109-chande-momentum-oscillator-cmo/) | Dönemdeki yükseliş ve düşüş toplamlarının farkını bunların toplamına böler; yönlü momentumu normalize eder. |
| 38 | [Chandelier Exit](https://www.tradingview.com/support/solutions/43000773013-chandelier-exit/) | Yerel en yüksek/en düşük fiyatlardan ATR katı uzaklıkta takip eden çıkış seviyeleri oluşturur. |
| 39 | [Chop Zone](https://www.tradingview.com/support/solutions/43000589111-chop-zone/) | EMA çevresindeki fiyat ve trend yapısını renk bölgelerine dönüştürür; yatay ve yönlü dönemleri görselleştirir. |
| 40 | [Choppiness Index (CHOP)](https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/) | Toplam true range ile pencerenin toplam fiyat aralığını karşılaştırır; yataylık derecesini ölçer, yönü ölçmez. |
| 41 | [Commodity Channel Index (CCI)](https://www.tradingview.com/support/solutions/43000502001-commodity-channel-index-cci/) | Tipik fiyatın ortalamasından sapmasını ortalama mutlak sapmayla normalize eder; uç momentum bölgelerini gösterir. |
| 42 | [Connors RSI (CRSI)](https://www.tradingview.com/support/solutions/43000502017-connors-rsi-crsi/) | Kısa fiyat RSI değerini, ardışık yükseliş/düşüş serisinin RSI değerini ve değişimin yüzdelik sırasını ortalar. |
| 43 | [Coppock Curve](https://www.tradingview.com/support/solutions/43000589114-coppock-curve/) | İki farklı ROC hesabının toplamını ağırlıklı ortalamayla yumuşatır; uzun vadeli fiyat momentumunu izler. |
| 44 | [Correlation Coefficient (CC)](https://www.tradingview.com/support/solutions/43000502022-correlation-coefficient-cc/) | İki fiyat serisinin birlikte değişme derecesini -1 ile +1 arasında ölçer; ilişki nedensellik anlamına gelmez. |
| 45 | [Created UTXOs](https://www.tradingview.com/support/solutions/43000778564-created-utxos/) | Seçilen dönemde oluşturulan yeni harcanmamış Bitcoin işlem çıktılarının sayısını gösterir. |
| 46 | [Cumulative Volume Delta](https://www.tradingview.com/support/solutions/43000725058-cumulative-volume-delta/) | Alt zaman dilimlerinin fiyat yönünden tahmin edilen hacim deltalarını belirli ankraj dönemi boyunca biriktirir; doğrudan emir akışı değildir. |
| 47 | [Cumulative Volume Index (CVI)](https://www.tradingview.com/support/solutions/43000589126-cumulative-volume-index-cvi/) | Yükselen hisselerin hacminden düşen hisselerin hacmini çıkarıp biriktirir; piyasa genelindeki hacim katılımını gösterir. |
| 48 | [Detrended Price Oscillator (DPO)](https://www.tradingview.com/support/solutions/43000502246-detrended-price-oscillator-dpo/) | Fiyattan geçmişe kaydırılmış hareketli ortalamayı çıkararak kısa döngüleri ayırmaya çalışır; geçmişe yerleştirilmesi karar zamanında dikkate alınmalıdır. |
| 49 | [Difficulty](https://www.tradingview.com/support/solutions/43000778562-difficulty/) | Yeni Bitcoin bloğu bulmak için gereken tahmini hash iş yükünü gösterir; fiyat momentum göstergesi değildir. |
| 50 | [Directional Movement (DMI)](https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/) | +DI, -DI ve ADX bileşenlerini birlikte gösterir; yönlü baskı ile trend gücünü ayrı değerlendirmeyi sağlar. |
| 51 | [Dividend Yield](https://www.tradingview.com/support/solutions/43000589129-dividend-yield/) | Yıllık temettüyü hisse fiyatına oranlayıp yüzdeye çevirir; şirketin temettü verimini gösterir. |
| 52 | [Donchian Channels (DC)](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/) | Son N mumun en yüksek ve en düşük fiyatını kanal sınırları yapar; orta çizgi bu ikisinin ortasıdır. |
| 53 | [Double Exponential Moving Average (EMA)](https://www.tradingview.com/support/solutions/43000589132-double-exponential-moving-average-ema/) | DEMA = 2 × EMA(fiyat) − EMA(EMA(fiyat)); klasik EMA gecikmesini azaltmaya çalışır. |
| 54 | [Ease of Movement (EOM)](https://www.tradingview.com/support/solutions/43000502256-ease-of-movement-eom/) | Fiyatın orta noktasındaki değişimi hacim ve fiyat aralığıyla ilişkilendirir; hareketin hacme göre kolaylığını yaklaşık ölçer. |
| 55 | [El Salvador Government balance](https://www.tradingview.com/support/solutions/43000778575-el-salvador-government-balance/) | El Salvador hükümetinin kamuya açıklanan adreslerindeki Bitcoin bakiyesini BTC veya dolar cinsinden izler. |
| 56 | [Elder's Force Index (EFI)](https://www.tradingview.com/support/solutions/43000502259-elder-s-force-index-efi/) | Fiyat değişimini hacimle çarpar ve yumuşatır; hareketin yönü ile hacim büyüklüğünü birleştirir. |
| 57 | [Envelope (ENV)](https://www.tradingview.com/support/solutions/43000502260-envelope-env/) | SMA veya EMA etrafına kullanıcı tarafından belirlenen sabit yüzde uzaklığında alt ve üst bant çizer. |
| 58 | [ETF balances](https://www.tradingview.com/support/solutions/43000778590-etf-balances/) | Belirli bir spot kripto ETF fonunun tuttuğu varlık miktarını coin veya dolar cinsinden gösterir. |
| 59 | [ETF flows](https://www.tradingview.com/support/solutions/43000778591-etf-flows/) | Belirli bir spot kripto ETF fonunun varlık miktarındaki günlük net değişimi tahmin eder; doğrudan işlem hacmi değildir. |
| 60 | [Ethereum new deposits](https://www.tradingview.com/support/solutions/43000778578-ethereum-new-deposits/) | Seçilen dönemde Ethereum staking mevduat sözleşmesine yapılan 32 ETH yatırma işlemlerini sayar. |
| 61 | [Ethereum new unique depositors](https://www.tradingview.com/support/solutions/43000778580-ethereum-new-unique-depositors/) | Seçilen dönemde Ethereum staking sözleşmesine 32 ETH gönderen yeni benzersiz adresleri sayar. |
| 62 | [Ethereum new value staked](https://www.tradingview.com/support/solutions/43000778579-ethereum-new-value-staked/) | Seçilen dönemde Ethereum staking mevduat sözleşmesine aktarılan ETH değerini toplar. |
| 63 | [Ethereum total number of deposits](https://www.tradingview.com/support/solutions/43000778581-ethereum-total-number-of-deposits/) | Ethereum staking mevduat sözleşmesine başlangıçtan itibaren yapılan yatırma işlemlerinin kümülatif sayısını gösterir. |
| 64 | [Ethereum total unique depositors](https://www.tradingview.com/support/solutions/43000778582-ethereum-total-unique-depositors/) | Başlangıçtan itibaren Ethereum staking sözleşmesine mevduat gönderen benzersiz adreslerin birikimli sayısını gösterir. |
| 65 | [Ethereum total value staked](https://www.tradingview.com/support/solutions/43000778583-ethereum-total-value-staked/) | Ethereum staking mevduat sözleşmesinde tutulan toplam ETH miktarını veya dolar değerini gösterir. |
| 66 | [Exponential Moving Average](https://www.tradingview.com/support/solutions/43000592270-exponential-moving-average/) | Yeni fiyatlara daha yüksek ağırlık veren yinelemeli ortalamadır; alfa genellikle 2/(N+1) olarak seçilir. |
| 67 | [Fisher Transform](https://www.tradingview.com/support/solutions/43000589141-fisher-transform/) | Normalize edilmiş fiyat serisine Fisher dönüşümü uygular; aşırı değerleri belirginleştirerek dönüş bölgelerini incelemeyi sağlar. |
| 68 | [Funding rate: a guide to market sentiment](https://www.tradingview.com/support/solutions/43000762390-funding-rate-a-guide-to-market-sentiment/) | Sürekli vadeli kontratlarda long ve short taraflar arasındaki dönemsel fonlama oranını gösterir; pozitif oranda long taraf short tarafa öder. |
| 69 | [Hash Rate](https://www.tradingview.com/support/solutions/43000778561-hash-rate/) | Madencilerin saniyede ürettiği tahmini hash sayısını gösterir; ağın hesaplama gücü ölçüsüdür. |
| 70 | [Held tokens in addresses ≥ X (% of supply)](https://www.tradingview.com/support/solutions/43000773992-held-tokens-in-addresses-x-of-supply/) | Arzın belirli yüzdesinden fazlasını tutan adreslerdeki toplam coin miktarını izler; sahiplik yoğunlaşmasını gösterir. |
| 71 | [Held tokens in addresses ≥ X (tokens)](https://www.tradingview.com/support/solutions/43000773991-held-tokens-in-addresses-x-tokens/) | Bakiyesi seçilen token adedi eşiğini aşan adreslerin elindeki toplam token miktarını gösterir. |
| 72 | [Held tokens in addresses ≥ X (USD)](https://www.tradingview.com/support/solutions/43000773990-held-tokens-in-addresses-x-usd/) | Dolar bakiyesi seçilen eşiği aşan adreslerin elindeki toplam yerel kripto miktarını gösterir. |
| 73 | [Historical Volatility](https://www.tradingview.com/support/solutions/43000589145-historical-volatility/) | Geçmiş fiyat getirilerinin dağılımından istatistiksel oynaklık hesaplar; fiyatın yönünü tahmin etmez. |
| 74 | [Hull Moving Average](https://www.tradingview.com/support/solutions/43000589149-hull-moving-average/) | Farklı uzunluklardaki ağırlıklı ortalamaları birleştirip yeniden yumuşatır; gecikmeyi azaltmayı amaçlar. |
| 75 | [Ichimoku Cloud](https://www.tradingview.com/support/solutions/43000589152-ichimoku-cloud/) | Farklı dönemlerin yüksek-düşük orta noktalarından Tenkan, Kijun ve bulut çizgileri üretir; bazı çizgiler ileri/geri kaydırılır. |
| 76 | [Index price](https://www.tradingview.com/support/solutions/43000784533-index-price/) | Birden çok spot piyasa kaynağından türetilen referans endeks fiyatını gösterir; türev fiyatıyla karşılaştırılabilir. |
| 77 | [Kaufman's Adaptive Moving Average (KAMA)](https://www.tradingview.com/support/solutions/43000773012-kaufman-s-adaptive-moving-average-kama/) | Fiyat hareketinin verimlilik oranına göre yumuşatma katsayısını değiştirir; trendde hızlanıp gürültüde yavaşlamaya çalışır. |
| 78 | [Keltner Channels (KC)](https://www.tradingview.com/support/solutions/43000502266-keltner-channels-kc/) | Hareketli ortalama etrafına ATR veya seçilen aralık ölçüsünün katlarıyla kanal yerleştirir. |
| 79 | [Klinger Oscillator](https://www.tradingview.com/support/solutions/43000589157-klinger-oscillator/) | Fiyat yönü ve hacimden bir hacim kuvveti serisi oluşturup bunun farklı EMA değerlerini karşılaştırır. |
| 80 | [Know Sure Thing (KST)](https://www.tradingview.com/support/solutions/43000502329-know-sure-thing-kst/) | Dört farklı dönem ROC serisini yumuşatıp ağırlıklı toplar; çok dönemli momentum osilatörüdür. |
| 81 | [Large transaction volume](https://www.tradingview.com/support/solutions/43000773993-large-transaction-volume/) | Değeri en az 100.000 dolar olan zincir işlemlerinin toplam hacmini gösterir; büyük transferleri ayırır. |
| 82 | [Learn using seasonals](https://www.tradingview.com/support/solutions/43000745201-learn-using-seasonals/) | Farklı yılların aynı takvim dönemindeki fiyat değişimlerini aynı alanda karşılaştırır; mevsimsel tekrarları incelemeyi sağlar. |
| 83 | [Least Squares Moving Average](https://www.tradingview.com/support/solutions/43000599877-least-squares-moving-average/) | Son N fiyat üzerine en küçük kareler doğrusu uydurur ve bu doğrunun ilgili uç değerini her mumda gösterir. |
| 84 | [Linear Regression](https://www.tradingview.com/support/solutions/43000644936-linear-regression/) | Seçilen fiyat bölgesine regresyon doğrusu ve standart sapma kanalları uygular; genel eğilim ve sapmaları görselleştirir. |
| 85 | [Liquidation data: what to watch and why it matters](https://www.tradingview.com/support/solutions/43000762400-liquidation-data-what-to-watch-and-why-it-matters/) | Borsadan sağlanan zorunlu kaldıraçlı pozisyon kapatma verilerini gösterir; kapsam veri sağlayıcısı ve sembole bağlıdır. |
| 86 | [Long / Short Ratio Accounts](https://www.tradingview.com/support/solutions/43000762399-long-short-ratio-accounts/) | Net long tutan hesapların sayısını net short tutanların sayısına oranlar; pozisyon büyüklüğünü ölçmez. |
| 87 | [Long Short Accounts %](https://www.tradingview.com/support/solutions/43000762397-long-short-accounts/) | Long ve short tutan hesapların yüzde paylarını ayrı gösterir; hesap sayısı dağılımıdır. |
| 88 | [MA Cross](https://www.tradingview.com/support/solutions/43000599879-ma-cross/) | Varsayılan 9 ve 21 dönemlik iki hareketli ortalamayı çizer ve kesişim mumlarını işaretler. |
| 89 | [Mark price](https://www.tradingview.com/support/solutions/43000784534-mark-price/) | Türev borsasının marjin ve tasfiye hesaplarında kullandığı adil değer referansını gösterir; son işlem fiyatından ayrışabilir. |
| 90 | [Mass Index](https://www.tradingview.com/support/solutions/43000589169-mass-index/) | Yüksek-düşük aralığının EMA oranlarını biriktirir; aralık genişleyip daraldığında olası dönüş koşullarını araştırır. |
| 91 | [McGinley Dynamic](https://www.tradingview.com/support/solutions/43000589175-mcginley-dynamic/) | Ortalamanın güncelleme hızını fiyat/ortalama ilişkisine göre değiştirir; değişken piyasa hızına uyum sağlamayı amaçlar. |
| 92 | [Mean block interval](https://www.tradingview.com/support/solutions/43000778557-mean-block-interval/) | Ardışık bloklar arasındaki sürenin aritmetik ortalamasını saniye cinsinden gösterir. |
| 93 | [Mean block size in bytes](https://www.tradingview.com/support/solutions/43000778560-mean-block-size-in-bytes/) | Dönemdeki toplam blok boyutunu blok sayısına böler; ortalama blok veri boyutunu gösterir. |
| 94 | [Mean gas used](https://www.tradingview.com/support/solutions/43000778551-mean-gas-used/) | Toplam kullanılan gas miktarını işlem sayısına böler; ortalama işlem hesaplama tüketimini gösterir. |
| 95 | [Mean transaction fees](https://www.tradingview.com/support/solutions/43000778548-mean-transaction-fees/) | Toplam işlem ücretlerini işlem sayısına böler; yerel para veya dolar cinsinden ortalama maliyettir. |
| 96 | [Mean transaction gas limit](https://www.tradingview.com/support/solutions/43000778584-mean-transaction-gas-limit/) | İşlem gönderenlerin belirlediği azami gas limitlerinin dönem ortalamasını gösterir; fiilen tüketilen gas ile aynı değildir. |
| 97 | [Mean transaction gas price](https://www.tradingview.com/support/solutions/43000778553-mean-transaction-gas-price/) | İşlemlerde ödenen gas fiyatlarının ortalamasını Gwei veya dolar cinsinden gösterir. |
| 98 | [Mean transaction size in bytes](https://www.tradingview.com/support/solutions/43000778574-mean-transaction-size-in-bytes/) | İşlemlerin veri boyutlarının byte cinsinden ortalamasını gösterir. |
| 99 | [Mean transfer volume](https://www.tradingview.com/support/solutions/43000778538-mean-transfer-volume/) | Başarılı transferlerin değerini ortalar; yerel coin veya dolar cinsinden ortalama transfer büyüklüğüdür. |
| 100 | [Mean UTXO value created](https://www.tradingview.com/support/solutions/43000778566-mean-utxo-value-created/) | Yeni oluşturulan harcanmamış işlem çıktılarındaki coin değerinin ortalamasını gösterir. |
| 101 | [Mean UTXO value spent](https://www.tradingview.com/support/solutions/43000778569-mean-utxo-value-spent/) | Harcanan işlem çıktılarındaki coin değerinin ortalamasını gösterir. |
| 102 | [Median](https://www.tradingview.com/support/solutions/43000644897-median/) | Mum orta fiyatlarının medyanını, bunun EMA karşılaştırmasını ve ATR tabanlı kanalı gösterir. |
| 103 | [Median block interval](https://www.tradingview.com/support/solutions/43000778558-median-block-interval/) | Ardışık bloklar arasındaki süre dağılımının ortanca değerini gösterir; uç gecikmelerden ortalamaya göre daha az etkilenir. |
| 104 | [Median gas used](https://www.tradingview.com/support/solutions/43000778552-median-gas-used/) | İşlem başına kullanılan gas dağılımının ortanca değerini gösterir. |
| 105 | [Median transaction fees](https://www.tradingview.com/support/solutions/43000778549-median-transaction-fees/) | İşlem ücretlerinin yerel para veya dolar cinsinden ortanca değerini gösterir. |
| 106 | [Median transaction gas limit](https://www.tradingview.com/support/solutions/43000778585-median-transaction-gas-limit/) | İşlemlerin belirlenen azami gas limitlerinin ortanca değerini gösterir. |
| 107 | [Median transaction gas price](https://www.tradingview.com/support/solutions/43000778554-median-transaction-gas-price/) | Ödenen işlem gas fiyatlarının Gwei veya dolar cinsinden ortanca değerini gösterir. |
| 108 | [Median transfer volume](https://www.tradingview.com/support/solutions/43000778539-median-transfer-volume/) | Başarılı transfer değerlerinin ortancasını yerel coin veya dolar cinsinden gösterir. |
| 109 | [Median UTXO value created](https://www.tradingview.com/support/solutions/43000778567-median-utxo-value-created/) | Yeni oluşturulan UTXO değerlerinin ortancasını BTC veya dolar cinsinden gösterir. |
| 110 | [Median UTXO value spent](https://www.tradingview.com/support/solutions/43000778570-median-utxo-value-spent/) | Harcanan UTXO değerlerinin ortancasını BTC veya dolar cinsinden gösterir. |
| 111 | [Momentum](https://www.tradingview.com/support/solutions/43000589187-momentum/) | Güncel fiyat ile N mum önceki fiyatın farkını hesaplar; fiyat hareketinin mutlak momentumunu izler. |
| 112 | [Money Flow (MFI)](https://www.tradingview.com/support/solutions/43000502348-money-flow-mfi/) | Tipik fiyat ve hacimden pozitif/negatif para akışları oluşturup 0-100 aralığına dönüştürür. |
| 113 | [Moon Phases](https://www.tradingview.com/support/solutions/43000599884-moon-phases/) | Yeni ay, dolunay ve ara evreleri takvim üzerinde işaretler; hesaplanan veri Ay evresidir, fiyat sinyali değildir. |
| 114 | [Moving average convergence divergence (MACD) indicator](https://www.tradingview.com/support/solutions/43000502344-moving-average-convergence-divergence-macd-indicator/) | Kısa ve uzun ortalama farkını, bunun sinyal ortalamasını ve aradaki histogram farkını gösterir; varsayılanlar genellikle 12/26/9 EMA değerleridir. |
| 115 | [Moving Average Ribbon](https://www.tradingview.com/support/solutions/43000644913-moving-average-ribbon/) | Dört adede kadar farklı uzunluk ve türde hareketli ortalamayı birlikte çizer; ayrışma ve kesişimler incelenir. |
| 116 | [Moving Averages](https://www.tradingview.com/support/solutions/43000502589-moving-averages/) | Fiyatları seçilen ortalama yöntemine göre yumuşatan gösterge ailesini açıklar; ayrı bir kârlılık modeli değildir. |
| 117 | [MovingAvg Cross](https://www.tradingview.com/support/solutions/43000599885-movingavg-cross/) | Kapanış hareketli ortalamanın üstündeyken long, altındayken short simülasyonu açan yerleşik stratejidir. |
| 118 | [MovingAvg2Line Cross](https://www.tradingview.com/support/solutions/43000599886-movingavg2line-cross/) | Hızlı ortalama yavaşı yukarı kestiğinde long, aşağı kestiğinde short simülasyonu açan stratejidir. |
| 119 | [Multi-Time Period Charts indicator](https://www.tradingview.com/support/solutions/43000502591-multi-time-period-charts-indicator/) | Üst zaman diliminin fiyat veya Heikin Ashi aralıklarını mevcut grafik üzerinde kutularla gösterir. |
| 120 | [Negative Volume Index (NVI)](https://www.tradingview.com/support/solutions/43000773005-negative-volume-index-nvi/) | Yalnızca hacmin önceki muma göre azaldığı mumlarda fiyatın yüzdesel değişimini endekse işler. |
| 121 | [Net Volume](https://www.tradingview.com/support/solutions/43000589192-net-volume/) | Yükselişle ilişkili hacimden düşüşle ilişkili hacmi çıkarır; hacmi yönüne göre sınıflandıran bir ölçüdür. |
| 122 | [On Balance Volume (OBV)](https://www.tradingview.com/support/solutions/43000502593-on-balance-volume-obv/) | Kapanış yükselirse mum hacmini ekler, düşerse çıkarır; hacim ve fiyat uyumsuzluğunu izlemek için kullanılır. |
| 123 | [Open Interest](https://www.tradingview.com/support/solutions/43000685269-open-interest/) | Henüz kapanmamış veya vadesi dolmamış türev kontratların toplam açık miktarını gösterir; birimi piyasaya bağlıdır. |
| 124 | [Parabolic SAR (SAR)](https://www.tradingview.com/support/solutions/43000502597-parabolic-sar-sar/) | İvme katsayısı ve fiyat uçlarıyla fiyatı izleyen stop noktaları oluşturur; yön değişince noktalar fiyatın diğer tarafına geçer. |
| 125 | [Percentage Price Oscillator (PPO)](https://www.tradingview.com/support/solutions/43000502346-percentage-price-oscillator-ppo/) | İki ortalama arasındaki farkı uzun ortalamaya oranlayıp yüzdeye çevirir; MACD mantığının ölçekten bağımsız karşılığıdır. |
| 126 | [Percentage Volume Oscillator (PVO)](https://www.tradingview.com/support/solutions/43000591350-percentage-volume-oscillator-pvo/) | Kısa ve uzun hacim ortalamalarının farkını uzun hacim ortalamasına oranlar; hacim momentumunu ölçer. |
| 127 | [Performance](https://www.tradingview.com/support/solutions/43000736064-performance/) | Seçilen sembol ve dönemlerdeki fiyat değişimlerini yüzdesel bir performans tablosunda gösterir. |
| 128 | [Pivot Points High Low](https://www.tradingview.com/support/solutions/43000589195-pivot-points-high-low/) | Her iki yanında daha düşük tepeler veya daha yüksek dipler bulunan pivotları işaretler; sağdaki mumların oluşmasını bekler. |
| 129 | [Pivot Points Standard](https://www.tradingview.com/support/solutions/43000521824-pivot-points-standard/) | Önceki dönemin OHLC verilerinden pivot ve destek/direnç seviyeleri üretir; Traditional, Fibonacci, Woodie gibi yöntemler seçilebilir. |
| 130 | [Positive Volume Index (PVI)](https://www.tradingview.com/support/solutions/43000773006-positive-volume-index-pvi/) | Yalnızca hacmin önceki muma göre arttığı mumlarda fiyatın yüzdesel değişimini endekse işler. |
| 131 | [Power-Law Model](https://www.tradingview.com/support/solutions/43000778576-power-law-model/) | Bitcoin fiyatının başlangıçtan geçen gün sayısıyla uzun vadeli tarihsel ilişkisini kuvvet yasası modeliyle temsil eder. |
| 132 | [Premium](https://www.tradingview.com/support/solutions/43000784535-premium/) | Vadeli fiyat ile endeks fiyatı arasındaki farkı göreli olarak gösterir; mutlak fark olan Basis değerinden ayrılır. |
| 133 | [Price Momentum Oscillator (PMO)](https://www.tradingview.com/support/solutions/43000773010-price-momentum-oscillator-pmo/) | Mumdan muma ROC değerine iki aşamalı yumuşatma uygular; sonucun EMA değeri sinyal çizgisidir. |
| 134 | [Price target - indicator](https://www.tradingview.com/support/solutions/43000730980-price-target-indicator/) | Veri sağlayıcısının analistlerden topladığı bir yıllık minimum, ortalama ve maksimum fiyat hedeflerini grafikte gösterir. |
| 135 | [Price Volume Trend (PVT)](https://www.tradingview.com/support/solutions/43000502345-price-volume-trend-pvt/) | Fiyatın yüzdesel değişimini hacimle çarpıp biriktirir; OBV değerinden farklı olarak fiyat değişiminin büyüklüğünü de kullanır. |
| 136 | [Pring's Special K](https://www.tradingview.com/support/solutions/43000773011-pring-s-special-k/) | Çok sayıda kısa, orta ve uzun dönem yumuşatılmış ROC değerini ağırlıklı birleştirir. |
| 137 | [Rank Correlation Index (RCI)](https://www.tradingview.com/support/solutions/43000765570-rank-correlation-index-rci/) | Fiyat sıralaması ile zaman sıralamasının korelasyonunu ölçer; fiyat hareketinin tek yönde tutarlılığını inceler. |
| 138 | [Rate of Change (ROC)](https://www.tradingview.com/support/solutions/43000502343-rate-of-change-roc/) | Güncel fiyatın N dönem önceye göre yüzde değişimini hesaplar; sıfır üstü/altı momentum yönünü gösterir. |
| 139 | [RCI Ribbon](https://www.tradingview.com/support/solutions/43000765571-rci-ribbon/) | Üç farklı uzunlukta Rank Correlation Index çizerek kısa ve uzun dönem yön tutarlılığını karşılaştırır. |
| 140 | [Realized market cap](https://www.tradingview.com/support/solutions/43000773994-realized-market-cap/) | Her coin birimini son zincir hareketindeki dolar fiyatıyla değerleyip toplar; güncel fiyatla hesaplanan piyasa değerinden farklıdır. |
| 141 | [Receiving addresses](https://www.tradingview.com/support/solutions/43000778535-receiving-addresses/) | Dönem içinde sıfırdan büyük kripto transferi alan benzersiz adresleri sayar. |
| 142 | [Relative Strength Index (RSI)](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/) | Yumuşatılmış ortalama kazanç ve kayıp oranını 0-100 ölçeğine dönüştürür; 70/30 yaygın eşiklerdir, otomatik dönüş garantisi değildir. |
| 143 | [Relative Vigor Index](https://www.tradingview.com/support/solutions/43000591593-relative-vigor-index/) | Kapanış-açılış hareketini mumun yüksek-düşük aralığıyla karşılaştırıp yumuşatır; kapanış yönünün kuvvetini inceler. |
| 144 | [Relative Volatility Index](https://www.tradingview.com/support/solutions/43000594684-relative-volatility-index/) | Fiyat değişimlerinin standart sapma bileşenlerini yönlerine göre değerlendirir; RSI benzeri 0-100 oynaklık ölçüsü üretir. |
| 145 | [Relative Volume at Time](https://www.tradingview.com/support/solutions/43000705489-relative-volume-at-time/) | Günün aynı anındaki normal veya birikimli hacmi geçmiş dönemlerin eş zamanlı ortalamasıyla karşılaştırır. |
| 146 | [Rob Booker - ADX Breakout](https://www.tradingview.com/support/solutions/43000591333-rob-booker-adx-breakout/) | ADX tabanlı trend gücünü ve uzun süre zayıf trendden sonraki hareketlenme koşullarını inceleyen Rob Booker göstergesidir. |
| 147 | [Rob Booker - Knoxville Divergence](https://www.tradingview.com/support/solutions/43000591336-rob-booker-knoxville-divergence/) | Fiyat-momentum uyumsuzluğunu RSI aşırı bölge koşuluyla birleştirir; olası ters yön hareketlerini çizgiyle işaretler. |
| 148 | [Rob Booker Intraday Pivot Points](https://www.tradingview.com/support/solutions/43000594546-rob-booker-intraday-pivot-points/) | Saatlik, dört saatlik veya sekiz saatlik dönemlerden gün içi pivot seviyeleri oluşturur. |
| 149 | [Rob Booker Missed Pivot Points](https://www.tradingview.com/support/solutions/43000594678-rob-booker-missed-pivot-points/) | Fiyatın temas etmediği günlük, haftalık ve aylık pivotları gösterir; daha sonra incelenecek referans seviyeleri oluşturur. |
| 150 | [Rob Booker Reversal](https://www.tradingview.com/support/solutions/43000599840-rob-booker-reversal/) | MACD sıfır geçişini Stochastic aşırı bölge koşuluyla birleştirir; koşul sağlanırsa renkli dönüş üçgeni çizer. |
| 151 | [Rob Booker Ziv Ghost Pivots](https://www.tradingview.com/support/solutions/43000594679-rob-booker-ziv-ghost-pivots/) | Mevcut fiyat bilgisiyle gelecek dönemin olası pivotunu projekte eder; dönem kapanana kadar seviye değişebilir. |
| 152 | [RSI divergence indicator](https://www.tradingview.com/support/solutions/43000589127-rsi-divergence-indicator/) | Fiyat pivotları ile RSI pivotları arasındaki düzenli veya gizli uyumsuzlukları arar; pivot onayı sinyalin gecikmesine yol açabilir. |
| 153 | [RVT ratio, 90 days](https://www.tradingview.com/support/solutions/43000773995-rvt-ratio-90-days/) | Gerçekleşmiş piyasa değerini 90 günlük yumuşatılmış işlem hacmiyle karşılaştırır; uzun vadeli zincir değerleme oranıdır. |
| 154 | [Seasonality](https://www.tradingview.com/support/solutions/43000723025-seasonality/) | Geçmiş yılların aylık getirilerini ısı haritası ve özet grafiklerle gösterir; mevsimsel davranışları karşılaştırır. |
| 155 | [Sending addresses](https://www.tradingview.com/support/solutions/43000778534-sending-addresses/) | Dönem içinde sıfırdan büyük kripto transferi gönderen benzersiz adresleri sayar. |
| 156 | [Simple Moving Average](https://www.tradingview.com/support/solutions/43000696841-simple-moving-average/) | Son N kaynağın aritmetik ortalamasını çizer; her muma eşit ağırlık verir. |
| 157 | [SMI Ergodic Indicator](https://www.tradingview.com/support/solutions/43000594669-smi-ergodic-indicator/) | Fiyat değişimlerine çift yumuşatma uygulayan TSI benzeri momentum hesabını sinyal EMA çizgisiyle birlikte gösterir. |
| 158 | [SMI Ergodic Oscillator](https://www.tradingview.com/support/solutions/43000594671-smi-ergodic-oscillator/) | SMI Ergodic değeriyle onun sinyal EMA değeri arasındaki farkı histogram olarak gösterir. |
| 159 | [Smoothed Moving Average](https://www.tradingview.com/support/solutions/43000591343-smoothed-moving-average/) | Önceki ortalamayı yeni fiyatla yinelemeli günceller; uzun geçmişin etkisini koruyan yavaş bir yumuşatma sağlar. |
| 160 | [Spent Output Profit Ratio (SOPR)](https://www.tradingview.com/support/solutions/43000778537-spent-output-profit-ratio-sopr/) | Harcanan UTXO değerini harcama anındaki dolar değeriyle oluşturulma anındaki dolar değerine oranlar; 1 üstü toplu kâr gerçekleşmesine işaret eder. |
| 161 | [Spent UTXOs](https://www.tradingview.com/support/solutions/43000778565-spent-utxos/) | Yeni işlemlerde girdi olarak kullanılan mevcut işlem çıktılarının sayısını gösterir. |
| 162 | [Stochastic (STOCH)](https://www.tradingview.com/support/solutions/43000502332-stochastic-stoch/) | Kapanışın son N mumun yüksek-düşük aralığındaki yerini hesaplar; %K ve bunun yumuşatılmış %D çizgisini gösterir. |
| 163 | [Stochastic Momentum Index (SMI)](https://www.tradingview.com/support/solutions/43000707882-stochastic-momentum-index-smi/) | Kapanışın fiyat aralığı orta noktasına uzaklığını yumuşatıp normalize eder; Stochastic göstergesinden farklı merkezleme kullanır. |
| 164 | [Stochastic RSI (STOCH RSI)](https://www.tradingview.com/support/solutions/43000502333-stochastic-rsi-stoch-rsi/) | Stochastic hesabını fiyat yerine RSI serisine uygular; RSI değerinin kendi son aralığındaki yerini ölçer. |
| 165 | [Stock-to-Flow Ratio in USD](https://www.tradingview.com/support/solutions/43000778577-stock-to-flow-ratio-in-usd/) | Bitcoin mevcut arzını yıllık yeni üretime oranlayan kıtlık modelini dolar fiyatıyla karşılaştırır; model uyumu gelecekteki fiyatı garanti etmez. |
| 166 | [Supertrend](https://www.tradingview.com/support/solutions/43000634738-supertrend/) | ATR katı ile oluşturulan bantları fiyat yönüne göre takip eder; bant aşılınca gösterilen trend çizgisi taraf değiştirir. |
| 167 | [Supply Equality Ratio](https://www.tradingview.com/support/solutions/43000773996-supply-equality-ratio/) | En küçük adreslerin tuttuğu arzı en büyük %1 adres grubunun arzıyla karşılaştırır; sahiplik eşitliğini ölçmeye çalışır. |
| 168 | [Technical Ratings](https://www.tradingview.com/support/solutions/43000614331-technical-ratings/) | Bir grup hareketli ortalama ve osilatörün puanlarını birleştirip normalize eder; birleşik teknik al/sat sınıflaması üretir. |
| 169 | [Time Weighted Average Price](https://www.tradingview.com/support/solutions/43000692939-time-weighted-average-price/) | Ankraj dönemindeki kaynak fiyatları zaman bakımından eşit ağırlıkla ortalar; varsayılan kaynak OHLC4 değeridir, hacim ağırlığı kullanmaz. |
| 170 | [Top trader long/short accounts](https://www.tradingview.com/support/solutions/43000784529-top-trader-long-short-accounts/) | Borsanın üst düzey yatırımcı olarak sınıfladığı hesapların long ve short yüzde dağılımını gösterir. |
| 171 | [Top trader long/short accounts ratio](https://www.tradingview.com/support/solutions/43000784530-top-trader-long-short-accounts-ratio/) | Üst düzey yatırımcı grubundaki long hesap payını short hesap payına oranlar; pozisyon büyüklüğünü ölçmez. |
| 172 | [Top trader long/short positions](https://www.tradingview.com/support/solutions/43000784531-top-trader-long-short-positions/) | Üst düzey yatırımcıların toplam pozisyon büyüklüğünün long/short yüzde dağılımını gösterir; hesap sayısından farklıdır. |
| 173 | [Top trader long/short positions ratio](https://www.tradingview.com/support/solutions/43000784532-top-trader-long-short-positions-ratio/) | Üst düzey yatırımcı grubunun long pozisyon büyüklüğünü short pozisyon büyüklüğüne oranlar. |
| 174 | [Total block size in bytes](https://www.tradingview.com/support/solutions/43000778559-total-block-size-in-bytes/) | Dönem içinde üretilen tüm blokların toplam veri boyutunu byte cinsinden gösterir. |
| 175 | [Total gas used](https://www.tradingview.com/support/solutions/43000778550-total-gas-used/) | Dönem içindeki işlemler ve akıllı sözleşmeler tarafından tüketilen toplam gas miktarını gösterir. |
| 176 | [Total transactions size in bytes](https://www.tradingview.com/support/solutions/43000778573-total-transactions-size-in-bytes/) | Dönemdeki tüm işlemlerin toplam veri boyutunu byte cinsinden gösterir. |
| 177 | [Total UTXO value created](https://www.tradingview.com/support/solutions/43000778568-total-utxo-value-created/) | Yeni oluşturulan UTXO değerlerini toplar; BTC veya dolar cinsinden ifade eder. |
| 178 | [Total UTXO value spent](https://www.tradingview.com/support/solutions/43000778572-total-utxo-value-spent/) | Harcanan işlem çıktılarındaki toplam coin değerini BTC veya dolar cinsinden gösterir. |
| 179 | [Total UTXOs](https://www.tradingview.com/support/solutions/43000778563-total-utxos/) | Bitcoin ağındaki mevcut harcanmamış işlem çıktılarının toplam sayısını gösterir. |
| 180 | [Trading Sessions](https://www.tradingview.com/support/solutions/43000729030-trading-sessions/) | Seçilen saat dilimindeki özel işlem seanslarını grafikte renkli kutularla işaretler; seans karşılaştırmasını kolaylaştırır. |
| 181 | [Transaction fees](https://www.tradingview.com/support/solutions/43000773997-transaction-fees/) | Madenci veya doğrulayıcılara ödenen işlem ücretlerinin dönem toplamını yerel para veya dolar cinsinden gösterir. |
| 182 | [Transaction fees](https://www.tradingview.com/support/solutions/43000778547-transaction-fees/) | Ayrı bir resmî sayfada aynı isimle listelenen toplam işlem ücreti metriğidir; mükerrer katalog kaydı olarak korunmuştur. |
| 183 | [Transaction rate](https://www.tradingview.com/support/solutions/43000778543-transaction-rate/) | Ağın saniyede işlediği başarılı işlem sayısını gösterir; tek işlem birden fazla transfer içerebilir. |
| 184 | [Transfer count](https://www.tradingview.com/support/solutions/43000778541-transfer-count/) | Dönem boyunca yapılan başarılı varlık transferlerini sayar; işlem sayısıyla birebir aynı değildir. |
| 185 | [Transfer rate](https://www.tradingview.com/support/solutions/43000778542-transfer-rate/) | Saniyedeki başarılı, sıfırdan büyük varlık transferlerini sayar; ağdaki değer hareketi hızını gösterir. |
| 186 | [Trend Strength Index](https://www.tradingview.com/support/solutions/43000730926-trend-strength-index/) | Kapanış fiyatlarıyla mum sıra numaraları arasındaki Pearson korelasyonunu hesaplar; -1/+1 tutarlı yönü gösterir. |
| 187 | [Triple EMA](https://www.tradingview.com/support/solutions/43000591346-triple-ema/) | TEMA = 3 × EMA1 − 3 × EMA2 + EMA3; ardışık EMA değerlerini birleştirip gecikmeyi azaltmaya çalışır. |
| 188 | [TRIX](https://www.tradingview.com/support/solutions/43000502331-trix/) | Üç kez EMA ile yumuşatılmış fiyatın değişim oranını hesaplar; düşük frekanslı momentum çizgisi üretir. |
| 189 | [True Strength Index](https://www.tradingview.com/support/solutions/43000592290-true-strength-index/) | Fiyat değişiminin çift yumuşatılmış değerini mutlak değişimin çift yumuşatılmış değerine oranlar; yönlü momentum ölçer. |
| 190 | [Ulcer Index](https://www.tradingview.com/support/solutions/43000773115-ulcer-index/) | Önceki zirvelerden yüzdesel düşüşlerin derinliğini ve sürekliliğini ölçer; aşağı yönlü risk ölçüsüdür. |
| 191 | [Ultimate Oscillator (UO)](https://www.tradingview.com/support/solutions/43000502328-ultimate-oscillator-uo/) | Alım baskısı ve true range oranlarını üç farklı pencere boyunca ağırlıklı birleştirir; çok dönemli momentum ölçer. |
| 192 | [Understanding crypto open interest](https://www.tradingview.com/support/solutions/43000762388-understanding-crypto-open-interest/) | Kripto türevlerinde açık kontrat miktarının yorumlanmasını ve veri kapsamını açıklar; Open Interest ailesinin açıklama kaydıdır. |
| 193 | [Up/Down Volume](https://www.tradingview.com/support/solutions/43000672561-up-down-volume/) | Alt zaman dilimi fiyat yönlerine göre hacmi yukarı ve aşağı bileşenlere ayırır; gerçek alıcı/satıcı işlemlerinin doğrudan kaydı değildir. |
| 194 | [US spot crypto ETF balances](https://www.tradingview.com/support/solutions/43000778588-us-spot-crypto-etf-balances/) | ABD borsalarında işlem gören spot kripto ETF fonlarının toplam coin veya dolar bakiyesini gösterir. |
| 195 | [US spot crypto ETF flows](https://www.tradingview.com/support/solutions/43000778589-us-spot-crypto-etf-flows/) | ABD spot kripto ETF fonlarının toplam varlığındaki günlük net değişimi tahmin eder. |
| 196 | [Visible Average Price](https://www.tradingview.com/support/solutions/43000678766-visible-average-price/) | Yalnızca grafikte görünen mumların kaynak fiyatını ortalar; yakınlaştırma veya kaydırma sonucunda değer yeniden hesaplanır. |
| 197 | [Volatility Stop](https://www.tradingview.com/support/solutions/43000594676-volatility-stop/) | Seçilen oynaklık ölçüsünün katını bir fiyat referansından uzaklaştırarak stop mesafesi oluşturur; parametreler stop genişliğini belirler. |
| 198 | [Volume](https://www.tradingview.com/support/solutions/43000591617-volume/) | Her mumdaki işlem miktarını gösterir; birim ve gerçek işlem hacmi/tick hacmi ayrımı veri kaynağına bağlıdır. |
| 199 | [Volume Delta](https://www.tradingview.com/support/solutions/43000725057-volume-delta/) | Alt zaman dilimi mumlarının yönüne göre hacmi pozitif/negatif sınıflandırıp mum başına farkını tahmin eder. |
| 200 | [Volume Weighted Average Price (VWAP)](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/) | Ankrajdan itibaren fiyat × hacim toplamını hacim toplamına böler; dönemsel hacim ağırlıklı ortalama fiyat üretir. |
| 201 | [Volume-Weighted Moving Average (VWMA)](https://www.tradingview.com/support/solutions/43000592293-volume-weighted-moving-average-vwma/) | Kayan son N mumun fiyat × hacim toplamını aynı pencerenin hacim toplamına böler. |
| 202 | [Vortex Indicator](https://www.tradingview.com/support/solutions/43000591352-vortex-indicator/) | Ardışık mumlar arasındaki çapraz yüksek-düşük hareketlerini true range toplamıyla normalize edip VI+ ve VI− çizgilerini oluşturur. |
| 203 | [VWAP Auto Anchored](https://www.tradingview.com/support/solutions/43000652199-vwap-auto-anchored/) | VWAP hesabını seçilen dönem veya otomatik ankraj koşulunun başlangıcından başlatır; ankraj değişince hesap penceresi değişir. |
| 204 | [Weighted Moving Average](https://www.tradingview.com/support/solutions/43000594680-weighted-moving-average/) | Son fiyatlara doğrusal olarak daha fazla ağırlık veren hareketli ortalamadır. |
| 205 | [Williams %R (%R)](https://www.tradingview.com/support/solutions/43000501985-williams-r-r/) | Kapanışın son N mumun zirvesine göre konumunu -100 ile 0 arasında ölçekler; dip bölgesine yakınlık daha negatif değer üretir. |
| 206 | [Williams Alligator](https://www.tradingview.com/support/solutions/43000592305-williams-alligator/) | Farklı dönem ve kaydırmalara sahip üç yumuşatılmış ortalama çizer; çizgilerin ayrılması veya iç içe geçmesi izlenir. |
| 207 | [Williams fractal indicator](https://www.tradingview.com/support/solutions/43000591663-williams-fractal-indicator/) | Genellikle beş mumluk yapıda, ortadaki tepe/dibi iki yandaki mumlarla karşılaştırır; sağdaki mumlar oluşmadan onaylanmaz. |
| 208 | [Woodies CCI](https://www.tradingview.com/support/solutions/43000594673-woodies-cci/) | Hızlı 6 ve yavaş 14 dönem CCI çizgilerini histogramla birleştirir; momentum ve olası dönüş yapıları incelenir. |
| 209 | [Zigzag indicator](https://www.tradingview.com/support/solutions/43000591664-zigzag-indicator/) | Belirli büyüklüğü aşan salınımların pivotlarını düz çizgilerle bağlar; son bacağı yeni fiyatla değişebilir ve geriye bakış yanılsaması yaratabilir. |

## 2. Formasyonlar — 20 resmî sayfa

| No | Resmî ad / kaynak | Çalışma özeti |
|---:|---|---|
| 210 | [All Chart Patterns](https://www.tradingview.com/support/solutions/43000706927-all-chart-patterns/) | Birden fazla klasik formasyonu birlikte tarar; oluşum durumunu, sınırlarını ve varsa hesaplanan hedefleri grafikte gösterir. |
| 211 | [Auto chart patterns on TradingView](https://www.tradingview.com/support/solutions/43000690464-auto-chart-patterns-on-tradingview/) | Otomatik formasyon araçlarının menüdeki yerini ve genel kullanımını anlatır; tek başına ayrı bir indikatör değildir. |
| 212 | [Chart Pattern Bearish Flag](https://www.tradingview.com/support/solutions/43000697936-chart-pattern-bearish-flag/) | Sert düşüşün ardından oluşan düzeltme kanalını ve aşağı kırılım koşulunu arar; düşüş bayrağıdır. |
| 213 | [Chart Pattern Bearish Pennant](https://www.tradingview.com/support/solutions/43000697937-chart-pattern-bearish-pennant/) | Düşüş sonrası daralan üçgensel konsolidasyonu ve aşağı devam koşulunu arar; düşüş flamasıdır. |
| 214 | [Chart Pattern Bullish Flag](https://www.tradingview.com/support/solutions/43000653209-chart-pattern-bullish-flag/) | Sert yükseliş sonrası oluşan düzeltme kanalını ve yukarı devam koşulunu arar; yükseliş bayrağıdır. |
| 215 | [Chart Pattern Bullish Pennant](https://www.tradingview.com/support/solutions/43000653215-chart-pattern-bullish-pennant/) | Yükseliş sonrası daralan üçgensel konsolidasyonu ve yukarı devam koşulunu arar; yükseliş flamasıdır. |
| 216 | [Chart Pattern Cup and Handle](https://www.tradingview.com/support/solutions/43000732556-chart-pattern-cup-and-handle/) | U biçimli çanak ve ardından oluşan daha küçük kulp yapısını arar; olası devam kırılımını işaretler. |
| 217 | [Chart Pattern Double Bottom](https://www.tradingview.com/support/solutions/43000690659-chart-pattern-double-bottom/) | Yakın seviyedeki iki dip ve aradaki tepeyi tanır; boyun çizgisi üzerindeki hareket olası yükseliş dönüşü koşuludur. |
| 218 | [Chart Pattern Double Top](https://www.tradingview.com/support/solutions/43000653211-chart-pattern-double-top/) | Yakın seviyedeki iki tepe ve aradaki dibi tanır; boyun çizgisi altındaki hareket olası düşüş dönüşü koşuludur. |
| 219 | [Chart Pattern Falling Wedge](https://www.tradingview.com/support/solutions/43000697938-chart-pattern-falling-wedge/) | Aşağı eğimli ve birbirine yaklaşan sınırlar arasındaki fiyat salınımını arar; düşen kama yapısını çizer. |
| 220 | [Chart Pattern Head And Shoulders](https://www.tradingview.com/support/solutions/43000653213-chart-pattern-head-and-shoulders/) | Ortadaki daha yüksek olmak üzere üç tepe ve ara diplerden boyun çizgisi oluşturur; aşağı kırılım incelenir. |
| 221 | [Chart Pattern Inverse Head And Shoulders](https://www.tradingview.com/support/solutions/43000690666-chart-pattern-inverse-head-and-shoulders/) | Ortadaki daha düşük olmak üzere üç dip ve ara tepelerden boyun çizgisi oluşturur; yukarı kırılım incelenir. |
| 222 | [Chart Pattern Inverted Cup and Handle](https://www.tradingview.com/support/solutions/43000732559-chart-pattern-inverted-cup-and-handle/) | Ters U biçimli çanak ve küçük düzeltme yapısını arar; olası düşüş devam koşullarını gösterir. |
| 223 | [Chart Pattern Rectangle](https://www.tradingview.com/support/solutions/43000653216-chart-pattern-rectangle/) | Yatay destek ve direnç arasındaki salınımları tanır; kırılım yönüne göre hedef projeksiyonu oluşturabilir. |
| 224 | [Chart Pattern Rising Wedge](https://www.tradingview.com/support/solutions/43000653219-chart-pattern-rising-wedge/) | Yukarı eğimli ve birbirine yaklaşan sınırlar arasındaki fiyat salınımını arar; yükselen kama yapısını çizer. |
| 225 | [Chart Pattern Triangle](https://www.tradingview.com/support/solutions/43000653217-chart-pattern-triangle/) | Yakınsayan sınırlar arasında sıkışan fiyat salınımlarını tanır; yukarı veya aşağı kırılım incelenir. |
| 226 | [Chart Pattern Triple Bottom](https://www.tradingview.com/support/solutions/43000690660-chart-pattern-triple-bottom/) | Yakın seviyelerde üç dip ve aralarındaki tepeleri arar; üst sınır kırılımı olası yükseliş dönüşünü gösterir. |
| 227 | [Chart Pattern Triple Top](https://www.tradingview.com/support/solutions/43000653218-chart-pattern-triple-top/) | Yakın seviyelerde üç tepe ve aralarındaki dipleri arar; alt sınır kırılımı olası düşüş dönüşünü gösterir. |
| 228 | [Elliott wave theory and tools](https://www.tradingview.com/support/solutions/43000653212-elliott-wave-theory-and-tools/) | Fiyat hareketlerini Elliott dalga yapılarıyla inceleyen teori ve araçları açıklar; sayım değişebilir ve yoruma bağlıdır. |
| 229 | [Gaps](https://www.tradingview.com/support/solutions/43000675999-gaps/) | Ardışık mumlar arasındaki işlem görmemiş fiyat boşluklarını işaretler; fiyat boşluğu doldurdukça gösterimi günceller. |

## 3. Hacim profilleri — 8 resmî sayfa

| No | Resmî ad / kaynak | Çalışma özeti |
|---:|---|---|
| 230 | [I cannot find the Volume Profile indicators](https://www.tradingview.com/support/solutions/43000653375-i-cannot-find-the-volume-profile-indicators/) | Hacim profili araçlarının indikatör menüsündeki yerini açıklar; ayrı bir hesaplama göstergesi değildir. |
| 231 | [Volume profile indicators: basic concepts](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/) | Fiyat seviyelerine düşen hacmi histogramla gösterir; POC en yoğun seviye, VAH/VAL seçilen değer alanının sınırlarıdır. |
| 232 | [Fixed Range Volume Profile indicator](https://www.tradingview.com/support/solutions/43000480324-fixed-range-volume-profile-indicator/) | Kullanıcının belirlediği sabit başlangıç-bitiş aralığındaki hacmi fiyat seviyelerine dağıtır. |
| 233 | [Session Volume Profile HD](https://www.tradingview.com/support/solutions/43000557450-session-volume-profile-hd/) | Seans içi hacim profilini gösterir ve yakınlaştırmaya göre ayrıntı seviyesini otomatik ayarlar. |
| 234 | [Periodic Volume Profile](https://www.tradingview.com/support/solutions/43000703071-periodic-volume-profile/) | Seçilen tekrarlayan dönemlerin her biri için ayrı fiyat-hacim profili oluşturur. |
| 235 | [Session Volume Profile](https://www.tradingview.com/support/solutions/43000703072-session-volume-profile/) | Her işlem seansı veya seçilen alt seans için fiyat seviyelerine göre hacim profili üretir. |
| 236 | [Visible Range Volume Profile](https://www.tradingview.com/support/solutions/43000703076-visible-range-volume-profile/) | Grafikte görünen aralığın hacim profilini hesaplar; görünür alan değiştiğinde profil de değişir. |
| 237 | [Auto Anchored Volume Profile](https://www.tradingview.com/support/solutions/43000703077-auto-anchored-volume-profile/) | Seçilen otomatik ankraj koşuluna göre başlangıç belirleyip bu noktadan itibaren hacim profilini oluşturur. |

## 4. TPO / zaman-fiyat profilleri — 2 resmî sayfa

| No | Resmî ad / kaynak | Çalışma özeti |
|---:|---|---|
| 238 | [Time price opportunity (TPO) indicator](https://www.tradingview.com/support/solutions/43000713306-time-price-opportunity-tpo-indicator/) | Fiyat seviyelerinin hangi zaman bloklarında ziyaret edildiğini harf/blok profiliyle gösterir; hacimden farklı olarak zaman katılımını ölçer. |
| 239 | [Session Time Price Opportunity (STPO) indicator](https://www.tradingview.com/support/solutions/43000719900-session-time-price-opportunity-stpo-indicator/) | Her günün belirlenen seansları için ayrı TPO profili üretir; zaman bloklarının kapsaması seans sınırlarıyla birebir örtüşmeyebilir. |

## Ek: Katalog dışında kalan mum formasyonları ve kaynak kodu erişimi

TradingView, mum formasyonlarını da otomatik tespit eden araçlar sunar. Bu dört yardım bölümünün envanteri, grafikteki Patterns sekmesinin tüm mum formasyonu öğeleriyle aynı şey değildir. Tam arayüz envanteri olmadan bunları “tamamı tarandı” şeklinde sunmak doğru olmaz. Menü ve çalışma biçimi için [Automatic candlestick pattern detection](https://www.tradingview.com/support/solutions/43000584462-candlestick-patterns/) sayfasına bakılabilir.

Yerleşik araçların çoğunun Pine kaynak kodu açılabilir. Bazı Volume Profile ve Chart Pattern araçlarının Pine kodu bulunmaz. Topluluk scriptlerinde açık kaynak, korumalı ve davet gerektiren erişim biçimleri farklıdır. Kaynak kodu görünmeyen bir yayının iç algoritmasını yalnız açıklamasına bakarak eksiksiz doğrulamak mümkün değildir.

## Ana kaynaklar

- [Resmî indikatör yardım merkezi](https://www.tradingview.com/support/categories/indicators/)
- [Built-in Indicators kataloğu](https://www.tradingview.com/support/folders/43000587405-built-in-indicators/)
- [Chart Patterns kataloğu](https://www.tradingview.com/support/folders/43000587407-chart-patterns/)
- [Volume Profiles kataloğu](https://www.tradingview.com/support/folders/43000587408-volume-profiles/)
- [TPO kataloğu](https://www.tradingview.com/support/folders/43000592009-tpo/)
- [Pine Script: First steps — topluluk kapsamı ve kaynak okuma](https://www.tradingview.com/pine-script-docs/primer/first-steps/)
- [Yerleşik script kaynak koduna erişim](https://www.tradingview.com/support/solutions/43000481659-i-want-to-see-the-source-code-of-a-built-in-script/)

### Teknik doğruluk notu

TWAP yardım yazısının girişinde hacim ağırlıklı ortalamayı tarif eden bir cümle bulunuyor. Bu belgede TWAP, zaman ağırlıklı fiyat ortalaması olarak açıklanmıştır; ilgili sayfanın ankraj ve OHLC4 kaynak ayarlarıyla birlikte değerlendirilmelidir. Göstergeyi yeniden uygulamadan önce erişilebiliyorsa güncel Pine kodu kontrol edilmelidir.
