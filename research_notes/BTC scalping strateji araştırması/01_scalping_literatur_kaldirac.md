# BTC scalping (dakikalar–~1 saat): literatür, maliyet, kaldıraç ve sınanabilir hipotezler

> Kapsam notu: 2026-10-21'de, ~16 web araması/okumasıyla hazırlandı. Kaynak yoğunluğu akademik mikroyapı + borsa ücret tablolarıdır; "pratisyen" (blog/YouTube) iddiaları kanıt sayılmadı. Proje içi önceki sonuçlar [BTC trader bot kenar araştırması](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md) raporundan alındı (Binance BTCUSDT 1m, 2021-06→2026-10-20, giriş = sonraki 1m açılışı + gerçek spread/swap).

## 1. Ciddi BTC scalper'ları ve kısa vadeli quant masaları hangi girdileri kullanıyor, hangisinin yayımlanmış kısa-ufuk kanıtı var?

### Takeaway
Kısa ufukta (saniye–dakika) öngörü gücü gerçek ama küçük ve neredeyse tamamen **emir defteri / emir akışı** (OFI, defter dengesizliği, açılış-anı akışı) kaynaklı; büyüklüğü **bp'nin kesirleri** düzeyinde ve yayımlanmış çalışmaların hiçbiri bunu taban-kademe taker ücretinden sonra kârlı bir strateji olarak göstermiyor. 1m bar + OHLCV düzeyinde ölçülebilen tek akademik intraday kenar (Shen–Urquhart–Wang ilk-yarım-saat → son-yarım-saat momentumu) eski veriye dayanıyor ve projenin kendi ETF-sonrası sınamasında çökmüş.

### Cited Findings
- **OFI'nin teorik/ampirik çerçevesi (hisse, 2010 öncesi):** Cont, Kukanov & Stoikov, *The Price Impact of Order Book Events* — kısa aralıklı fiyat değişimi, en iyi kotasyonlardaki emir akışı dengesizliğiyle (OFI) neredeyse doğrusal ilişkili; eğim derinlikle ters orantılı. Bu **eşzamanlı** (contemporaneous) bir ilişkidir, ileriye dönük öngörü değildir — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402). *(Hisse verisi, eski; kripto için doğrudan kanıt değil.)*
- **Kripto OFI metodoloji uyarısı (2026-06):** Vafin, *Order-Flow Imbalance and Short-Horizon Return Predictability in Cryptocurrency Markets* — yeni ampirik tahmin raporlamıyor; ana vurgu, aynı aralıktaki işlem→fiyat **mekanik bağını** gerçek öngörüden ayırmak, OOS değerlendirme, maliyet modeli ve veri-madenciliği kontrolü — [SSRN 6938742](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6938742). *(Yani "CVD fiyatı açıklıyor" grafiklerinin çoğu eşzamanlı korelasyondur.)*
- **Binance perp, çeyrek-saat etkisi (en güçlü güncel kanıt):** *The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures* — Binance USDT-M perp, 6 kontrat (BTC, ETH, XRP, SOL, DOGE, ADA), 2021-01-01→2024-10-31, ms işlemler 10 sn/1 dk barlara toplandı — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v2):
  - Çeyrek-saat dakikalarının ilk 10 sn'sinde ~%26 daha fazla işlem, %32 daha yüksek dolar hacmi, %26 daha büyük mutlak getiri (6 kontrat ortalaması).
  - Açılış 10-sn getirisi OOS öngörülebilir (2021-07→2024-10, ~117k gözlem/varlık, 6 ay kayan eğitim, aylık yeniden-fit): birleşik model OOS R² ort. %3,37 (BTC %3,82), yön isabeti ort. %57,1, AUC 0,601.
  - Çeyrek-saat emir dengesizliği 4–12 **saat** sonrası kümülatif getiriyi öngörüyor; profil ilk yarım saatte **negatif**, sonra pozitif, 8–12 saatte tepe. **1 dakikalık ve "olağan" dengesizliğin öngörü ilişkisi çok zayıf.**
  - **Maliyet:** Sinyal-ağırlıklı gerçekleşen tahmin hedefi sınır başına ~**0,5 bp** — standart taker ücretinin (5 bp) ~onda biri, gidiş-dönüşün yirmide biri. Yazarlar net-maliyet strateji sunmuyor; tahmini "icra ve likidite sağlama girdisi" olarak çerçeveliyor.
- **LOB tabanlı BTC/USD işaret tahmini:** *Forecasting Bitcoin price movements using multivariate Hawkes processes and limit order book data* (Springer, 2026) — LOB türevli özelliklerle mid-price getirisinin zamanlaması ve işaretini tahmin ediyor; Busetto & Formentin (2023) defter-dengesizliği → gelecek getiri ilişkisinin üzerine kurulu — [Springer](https://link.springer.com/article/10.1007/s10203-026-00570-z). *(Ücret sonrası kârlılık iddiası arama özetinde yok — tam metin okunmadı.)*
- **Binance futures bid-ask dengesizliği → anlık getiri (tez, 2025):** BTC/ETH/LTC — [Charles Univ. tezi](https://dspace.cuni.cz/bitstream/handle/20.500.11956/200516/120505902.pdf?sequence=1). *(Ayrıntılı sayılar okunmadı.)*
- **Günlük/haftalık akış:** Anastasopoulos & Gradojevic (EFMA 2025) — "dünya emir akışı" kesitsel kripto getirilerini açıklıyor ve öngörüyor; Makarov & Schoar (2020) BTC için emir akışı ile **ertesi gün** getirisi arasında **negatif** ilişki bulmuş (ufka göre işaret dönüyor) — [EFMA 2025 PDF](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2025-Greece/papers/OrderFlowpaper.pdf). Günlük dengesizliğin çöküş riskini 7 güne kadar öngördüğü daha eski çalışma — [PMC10040314](https://pmc.ncbi.nlm.nih.gov/articles/PMC10040314/).
- **Intraday zaman-serisi momentumu (BTC):** Shen, Urquhart & Wang, *Bitcoin intraday time series momentum* (2022) — hacimle tanımlanan "piyasa zamanında" ilk yarım saat getirisi son yarım saati IS ve OOS öngörüyor (eğim 0,968, NW t=4,38, R² %1,44); sondan-ikinci yarım saat **negatif**; mekanizma likidite sağlama, özellikle düşüş dönemlerinde — [Reading kabul edilmiş metin](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf). 2013-03→2020-05 verisinde momentum **ve** dönüşün birlikte olduğunu bulan çalışma — [ResearchGate](https://www.researchgate.net/publication/361202793_Intraday_return_predictability_in_the_cryptocurrency_markets_momentum_reversal_or_both). *(Örneklem ETF öncesi, büyük olasılıkla çürümüş — aşağıya bkz.)*
- **Proje içi karşı kanıt:** Gün-içi TSMOM (ETF sonrası) n=696, ort −0,039R, RED (BTC-T07); saat-of-gün 48 hücrenin 46'sı negatif (BTC-M03); funding saati −0,8…−2,9 bp (BTC-M06); turn-of-the-candle 2021'de +0,57 bp brüt → net −1,72 bp (BTC-M07); 5m Donchian48 −0,204R (BTC-T08) — [önceki rapor](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md).
- **Çapraz-borsa lead-lag:** CME futures BTC'de Hasbrouck payı 0,52–0,56, lead-lag süresi **0,055–0,15 saniye**; 2024-08-05'te pay 0,158'e çöküyor (yalnız 5 seçilmiş gün, 2024) — [arXiv 2506.08718](https://arxiv.org/abs/2506.08718). Binance spot+perp birincil fiyat keşif kaynağı; Coinbase gibi düzenlenmiş spot borsalar NY 16:00 fixing'inde göreli olarak daha etkili — [Cosenza & Stalder, SSRN 4983566](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4983566). Coinbase'in Binance'e önderliği USDT düzeltmesiyle azalıyor ama tersine dönmüyor (hakemsiz) — [SharpeEdge](https://sharpeedgecapital.com/research/bitcoin-price-discovery-an-empirical/). 2021 SEC eki: CME ayların %90'ında spotu IS bazında yönlendirmiş (eski) — [SEC](https://www.sec.gov/files/rules/sro/nysearca/2021/34-93445-ex3a.pdf).
- **Perp mikroyapı zamanlaması:** Spread'ler standart funding settlement saatlerinden ~2 saat sonra tepe yapıyor (getiri değil, spread bulgusu) — [MDPI IJFS 14/5/103](https://www.mdpi.com/2227-7072/14/5/103).

### Inferences
- Kısa ufuk öngörüsü **mikrosaniye–saniye ve sub-bp** ölçeğinde yaşıyor; 1m bar kapanışında karar verip sonraki 1m açılışında market emirle giren bir botun ulaşabileceği bilgi seti bu kenarın çoğunu zaten fiyata yansımış hâlde görür. Lead-lag 0,05–0,15 sn olduğundan Coinbase/CME → CFD "öncü" sinyali 1m çözünürlükte büyük olasılıkla ölüdür.
- Literatürde "scalping" kârının büyük kısmı **yön tahmininden değil**, maker rebate/spread yakalama ve envanter yönetiminden gelir (bkz. §3). Retail CFD trader bu gelir kaynağına erişemez — o spread'i **öder**.
- Çeyrek-saat makalesi önemli bir yön gösteriyor: perp'te açılış-anı akışı 4–12 saat ufkunda öngörü veriyor — yani akış verisi, scalp değil **intraday swing** filtre/bağlam olarak daha umut verici.
- Sinyal ailelerinin kanıt durumu (özet): OFI/LOB = güçlü ama sub-bp/saniye; açılış-anı akışı = orta (4–12 sa); intraday TSMOM = eski, projede çöktü; funding/OI/liq = kısa ufukta **akademik kanıt bulunamadı** (§2); VWAP/hacim profili/seans açılışı = akademik kanıt bulunamadı.

### Gaps
- VWAP / anchored VWAP / hacim profili / "liquidity sweep" kavramları için kripto-spesifik, maliyet-dahil, OOS akademik çalışma **bulunamadı**; bunlar pratisyen folklorü olarak ele alınmalı.
- "Whale print" / işlem büyüklüğü sınıflamasının BTC'de dakika-ufuk öngörüsüne dair güncel kanıt bulunamadı.
- Hawkes/LOB makalesinin ücret-sonrası sonuçları tam metin okunmadığı için doğrulanmadı.
- Taker buy/sell oranının (1m kline'daki taker-buy hacmi) 1–60 dk ufkunda tek başına öngörü gücüne dair yayımlanmış BTC çalışması bulunamadı; çeyrek-saat makalesi 1 dk dengesizliğin "çok zayıf" olduğunu söylüyor.

## 2. Likidasyon kaskadları, funding uçları ve OI sıçramaları: devam mı dönüş mü?

### Takeaway
Kaskad sonrası fiyat davranışını (devam/dönüş, ufuk) ölçen hakemli bir BTC olay çalışması **bulunamadı**; mevcut güncel çalışmalar kaskadın **önce** sinyali üzerine ve olaylar arası heterojenlik buluyor. Funding'in kısa ufuk getiri öngörüsü için de doğrudan kanıt yok — literatür funding'in kendisinin tahmin edilebilirliğini ve baz yakınsamasını inceliyor. Bu alan ancak kendi olay çalışmamızla (hipotez H3–H6) açılabilir; ve veri kısıtı var: Binance intraday likidasyon anlık görüntülerini artık servis etmiyor.

### Cited Findings
- **7 kaskad, erken-uyarı (2026 ön-baskı):** *Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades* — Binance USD-M BTC; olaylar 2022-05 (LUNA), 2022-11 (FTX), 2024-08 (yen carry), 2024-12, 2025-02 (tarife), 2025-04 ("Liberation Day"), 2025-10 (rekor teminat-depeg); 1m kline (~88k bar/pencere) + 5m metrikler (OI, top-trader L/S, global L/S, taker buy/sell oranı) — [arXiv 2607.27070](https://arxiv.org/html/2607.27070v1):
  - "Hiçbir değişken olaydan bağımsız değil" — fiyat otokorelasyonu 7 olayın 5'inde sinyal veriyor (2025-02 ve 2025-10'da yok); OI, L/S, taker oranı olaydan olaya değişiyor.
  - Taker-akış varyansı kullanılabilir 6 olayın 6'sında önce **düşüyor** (medyan τ −0,13…−0,44); 300 olağan başlangıca karşı plasebo Fisher p≈5×10⁻⁶ — ama 2 olay tek tek null içinde → popülasyon düzeyi öncü, olay bazlı alarm değil.
  - **Kaskad sonrası** davranış analiz edilmiyor. Funding 8 saatte bir ödendiği için intraday analiz için "fazla kaba" bulunmuş. **Intraday likidasyon anlık görüntüleri artık servis edilmiyor**; bu yüzden kaldıraç değişkenleri likidasyon durumunun proxy'si olarak kullanılmış.
- **Kaskad mekanizması:** zorunlu satışlar fiyatı bir sonraki marjin eşiğine iter → kendini besleyen döngü (aynı makale). 2025-10-10 kaskadında BTC tek seansta ~122k$→~104k$; Hyperliquid'de ADL algoritması nedeniyle ~653 M$ gereksiz kesinti iddiası (ikincil kaynak) — [ResearchGate](https://www.researchgate.net/publication/396645981_Anatomy_of_the_Oct_10-11_2025_Crypto_Liquidation_Cascade_Macroeconomic_Triggers_Market_Microstructure_and_Systemic_Risk_Lessons); 2025-11 kaskadı blog analizi — [Coinchange](https://www.coinchange.io/blog/bitcoins-2-billion-reckoning-how-novembers-liquidations-cascade-exposed-cryptos-structural-fragilities) (zayıf kaynak).
- **BitMEX marjin çalışması (eski, 2021):** günlük zorunlu likidasyon / açık pozisyon: long %3,51, short %1,89; likide edilen yatırımcıların ortalama kaldıracı ~**60x**; veri kaynağı likidasyonun tam zamanını vermediği için likidasyonlar günlük uç fiyatlarda varsayılmış — [arXiv 2102.04591](https://arxiv.org/abs/2102.04591) / [Applied Economics](https://www.tandfonline.com/doi/abs/10.1080/00036846.2021.1922597).
- **Likidasyon nominali ≠ kayıp:** 2020-03 BitMEX'te 24 saatte >190 M$ likidasyon; Nic Carter gerçek kaybı ~22 M$ tahmin etmiş — [Al Jazeera](https://www.aljazeera.com/economy/2020/3/9/crypto-burn-traders-stung-by-forced-liquidations).
- **Funding:** Inan, *Predictability of Funding Rates* — Binance/Bybit BTC funding seviyesi OOS tahmin edilebilir (double AR modeller no-change benchmark'ı yeniyor); **getiri** öngörüsü değil — [SSRN 5576424](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5576424). Funding δ'nın spottan sapmayı disipline ettiği (baz yakınsaması) — [AEA 2026](https://www.aeaweb.org/conference/2026/program/paper/ByyFEfr4); perp temel fiyatlaması — [arXiv 2212.06888](https://arxiv.org/html/2212.06888v7). BitMEX funding–fiyat Granger çalışması eski/sınırlı — [arXiv 1912.03270](https://www.arxiv.org/pdf/1912.03270).
- **Proje içi:** "Coşku dönmez": 1 saatlik yukarı şoku satmak −0,194R, plasebonun %0,5 yüzdeliğinde (BTC-S06, veto adayı); 1 saatlik negatif şoku almak −0,021R (BTC-S05) — [önceki rapor](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md). Bu, kaskad-fade'in (özellikle short-squeeze fade'in) OHLCV-proxy'siyle zaten olumsuz olduğu anlamına geliyor.

### Inferences
- "Likidasyon kümesinden sonra dön" bir **pratisyen iddiası**; akademik destek yok ve proje içi OHLCV-şok proxy'leri (S05/S06) negatif. OI verisi eklemek *yeni tanım* sayılır (defter kuralı: yeniden açmak için yeni veri/tanım şart) — fark: fiyat şoku + **OI düşüşü** (zorunlu kapanış) ile fiyat şoku + **OI artışı** (yeni pozisyon) ayrımı. Bu ayrım OHLCV'de yoktu.
- Kaskadlar nadir ve heterojen (7 olay / 4 yıl ölçeğinde büyükler); ≥150 olay ölçütünü tutturmak için eşik "mikro-kaskad" düzeyine (5m OI z-skoru) indirilmeli — bu da etkiyi sulandırabilir.
- Funding 8 saatlik ödeme olduğundan dakika-ufuk sinyali değil; en fazla bağlam/rejim filtresi (kalabalık taraf).

### Gaps
- Kaskad sonrası 5/15/60 dk getiri profili (dönüş vs devam) için hakemli BTC olay çalışması bulunamadı.
- Binance tarihsel 5m "metrics" dosyalarının (OI, L/S, taker oranı) data.binance.vision'da ne kadar geriye gittiği bu oturumda doğrulanmadı — sınamadan önce kontrol edilmeli. Tarihsel tek tek likidasyon kayıtları (forceOrder) artık REST'te servis edilmiyor (arXiv 2607.27070); CoinGlass vb. ücretli agregatörler gerekebilir.
- OI/funding uçlarının dakika-saat ufkunda öngörü gücüne dair Kaiko/Glassnode/Amberdata yayımları bu taramada bulunamadı.

## 3. Kârlı scalping arketipleri: kim yapabilir, kenar kaç bp, retail MT5 CFD (1,5–2 bp, 1m karar) yakalayabilir mi?

### Takeaway
Kripto kısa-ufuk kârının ana kaynakları (piyasa yapıcılık, latency/lead-lag arbitrajı, açılış-anı akış alfası) **sub-bp ile birkaç bp** büyüklüğünde ve ya maker rebate + kuyruk önceliği ya da milisaniye gecikme gerektiriyor; 1m-bar kararlı, spread ödeyen bir CFD botu bunlara erişemez. Retail'in teorik olarak oynayabileceği tek alan, ortalama hareketi **maliyetin ≥10–20 katı** olan seyrek, olay-tetikli girişlerdir (likidasyon/şok sonrası, seans/makro açılış, sweep) — ve bunların hiçbiri için yayımlanmış maliyet-dahil OOS kanıt bulunamadı.

### Cited Findings
- **Açılış-anı akış alfası:** ~0,5 bp/sınır, taker ücretinin ~1/10'u; yazarlar bunu bağımsız strateji değil icra/likidite sağlama girdisi olarak konumluyor — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v2). (Çeyrek-saat patlamalarında yuvarlak-olmayan işlem büyüklükleri → algoritmik katılım tutarlı.)
- **Lead-lag:** CME→spot lead süresi 0,055–0,15 sn — [arXiv 2506.08718](https://arxiv.org/abs/2506.08718). 1m karar veren bot için erişilemez.
- **Kaldıraçlı retail davranışı:** 2020 Binance çalışmasına atfen müşterilerin %79'u >20x kaldıraçla işlem yapmış; rastgele giriş/çıkış simülasyonunda 75x kaldıraçta işlemlerin %97,3'ü likide olmuş; Binance yeni hesaplara ilk 60 gün >20x'i kısıtlamış — [NYU Stern, Duron-Carielo](https://www.stern.nyu.edu/sites/default/files/assets/documents/Duron-Carielo_Is%20There%20A%20Future%20In%20Perpetual%20Futures.pdf).
- **Funding arbitrajı:** funding δ spottan sapmayı disipline eder; delta-nötr taşıma getirisi funding seviyesine bağlıdır (mekanizma) — [AEA 2026](https://www.aeaweb.org/conference/2026/program/paper/ByyFEfr4). CFD'de funding yok, yerine swap (long −%14/yıl) var — [önceki rapor](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md).

### Inferences
| Arketip | Kim yapabilir | Tahmini kenar (bp/işlem) | Retail CFD 1m bot? |
|---|---|---|---|
| Piyasa yapıcılık (spread yakalama) | Maker rebate'li VIP/MM, co-location, kuyruk önceliği | spread'in bir kısmı, <1–2 bp, yüksek devir | **Hayır** — CFD'de spread'i broker alır; perp taban maker 2 bp ücret öder, rebate almaz |
| Latency / lead-lag arbitrajı (CME/Coinbase→Binance) | ms gecikmeli HFT | sub-bp…birkaç bp, sn-altı | **Hayır** (lead 0,05–0,15 sn) |
| Açılış-anı akış alfası (çeyrek-saat) | Algoritmik icra masaları | ~0,5 bp | **Hayır** (maliyetin 1/4'ü) |
| Funding / baz taşıma (delta-nötr) | Spot+perp hesabı, sermaye | funding seviyesi (yıllık %), scalp değil | CFD'de **yok**; ayrı ürün |
| Momentum/kırılım, likidite sweep, momentum ignition | Herkes; kenarı belirsiz | Bilinmiyor; proje 5m Donchian −0,204R | Mümkün ama kanıtsız; maliyet/hedef oranı belirleyici |
| VWAP'a ortalama dönüş | Herkes | Bilinmiyor; proje kanal-RJ −0,084R | Mümkün ama kanıtsız |
| Likidasyon-fade | Herkes (veri gerekli) | Bilinmiyor; proje şok-fade S05 −0,021R, S06 −0,194R | Mümkün; yalnız OI ile yeni tanım |
- Kâğıt üzerindeki her yön sinyali için belirleyici kısıt: **ortalama hareket / maliyet** oranı. CFD maliyeti ~1,85 bp iken 10 bp'lik scalp hedefi maliyeti hedefin %18'ine çıkarır; 50 bp hedefte %3,7. Bu yüzden "scalp" ufku pratikte 15–60 dk ve ≥30–50 bp hareket hedefleyen olay-tetikli girişlere itilir.

### Gaps
- Gerçek MM/prop masalarının BTC'deki işlem başı kenarına dair kamuya açık güvenilir rakam bulunamadı.
- Pepperstone'un volatilite/haber/hafta sonu anlarında BTC spread genişlemesi istatistiği bulunamadı (CFD icrasının en büyük gizli maliyeti olabilir).

## 4. Venue maliyetleri 2026: perp maker/taker, funding, kayma vs CFD spread

### Takeaway
Taban kademede USDT-M perp **taker-taker gidiş-dönüş ~10–11 bp**, maker-maker ~4 bp; Pepperstone BTC CFD spread'i ~1,4–1,9 bp. Yani taban kademe retail için **CFD daha ucuz** — perp'e geçiş maliyet avantajı değil, **veri** (OI, funding, likidasyon, L2) ve limit-emir kontrolü avantajı sağlar. En mantıklı mimari: sinyal Binance futures verisinden, icra (gerekirse) CFD'de — ama CFD fiyat beslemesi ile Binance arasındaki fark ve haber anı spread genişlemesi ölçülmeli.

### Cited Findings
- **Binance USDⓈ-M:** taban (30g <15 M$ hacim veya <25 BNB) maker %0,02 / taker %0,05; BNB ile ödemede %10 indirim; VIP hacim eşikleri spotun 5 katı — [Finder](https://www.finder.com/binance-futures-fees); resmi yapı — [Binance destek](https://www.binance.com/es/support/articles/360033544231). (Resmi ücret sayfası bu oturumda doğrudan okunmadı; ikincil kaynaklar tutarlı.)
- **Bybit USDT perp taban:** maker %0,02 / taker %0,055 — [Bitsgap](https://bitsgap.com/blog/bybit-trading-fees-explained-what-it-costs); [Trader's Second Brain](https://traderssecondbrain.com/tools/exchange-fees).
- **OKX futures regular:** maker %0,02 / taker %0,05; 2026-04-08'den itibaren 9 VIP kademesi — [BitDegree](https://www.bitdegree.org/crypto/tutorials/okx-fees); [GitHub ücret tablosu](https://github.com/otvjn39/okx-futures-taker-fee). Bazı bloglar %0,06/%0,08 diyor — muhtemelen eski/spot karışıklığı.
- **Derinlik/kayma:** Kaiko'ya göre BTC'nin agregat %2 derinliği 2025 zirvesinden ~%30 düşmüş (2025 sonu, ikincil kaynak) — [MEXC/Kaiko](https://www.mexc.com/news/317547); 2023-11'de Binance %0,1 ve %1 derinlik ~150 M$ / ~180 M$'ın altına inmiş (perp değil, top kriptolar) — [CoinDesk](https://coindesk-coindesk-prod.cdn.arcpublishing.com/markets/2023/11/22/trading-crypto-on-binance-becomes-challenging-as-order-book-liquidity-tanks-25/); 100k$ BTC satışında en likit USD ve USDT çiftlerinde ~%0,1 kayma (tarih belirsiz) — [Kaiko](https://research.kaiko.com/insights/the-state-of-liquidity-in-crypto-markets).
- **Pepperstone BTCUSD CFD:** spread ~15$ (≈1,4–1,9 bp), long swap −%14/yıl, short +%2/yıl, rollover NY 17:00; önceki çalışmada spread tabanı %0,0185, stres %0,028 — [önceki rapor](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md).

### Inferences
- 0,1–5 BTC market emirlerinde Binance BTCUSDT perp'te kayma normal koşulda büyük olasılıkla <1 bp (top-of-book derinliği tipik olarak bunun üzerinde), ama haber/kaskad anında birkaç bp–onlarca bp olabilir — sayısal kanıt bu oturumda **bulunamadı**, kendi defter kayıtlarıyla ölçülmeli.
- <1 saat tutulan pozisyonda funding ancak settlement anını (00/08/16 UTC, Binance standart) geçerse işler; tipik %0,01/8s funding ≈ 1 bp — taker ücretinin yanında küçük ama sıfır değil. CFD'de swap yalnız rollover'ı geçerse: −%14/yıl ≈ 3,8 bp/gece.

### Gaps
- Binance resmi 2026 ücret sayfası ve "standart funding = %0,01/8s" varsayımı bu oturumda birincil kaynaktan doğrulanmadı.
- BTCUSDT perp için 0,1/1/5 BTC ölçekli güncel kayma ölçümü (Kaiko/Amberdata) bulunamadı.

## 5. Kaldıraç: ne değiştirir, ne değiştirmez; retail neden kaybeder

### Takeaway
Kaldıraç beklentiyi **risk birimi (R) başına** değiştirmez; yalnız pozisyon büyüklüğünü ve dolayısıyla özkaynak getirisinin ortalama ve varyansını ölçekler. Scalping'de asıl tehlike kaldıraç değil, **dar stop**: maliyet R cinsinden stop mesafesiyle ters orantılı büyür. Kaldıraçlı retail kaybının belgelenmiş nedenleri: aşırı kaldıraç (ort. 60x likide olanlar), negatif-beklentili sık işlem, maliyet. Disiplinli trader'ın kaldıracı bir **girdi değil, çıktıdır** (risk%/stop%).

### Cited Findings
- **ESMA (2018):** AB ülkelerindeki NCA analizleri: retail CFD hesaplarının **%74–89'u** para kaybediyor, müşteri başı ort. kayıp 1.600–29.000 €; kaldıraç sınırları 30:1'den 2:1'e (dayanak varlığa göre — kripto 2:1), hesap başı marjin kapatma kuralı ve negatif bakiye koruması — [ESMA](https://www.esma.europa.eu/node/84933); [RPC özeti](https://rpclegal.com/thinking/financial-services-regulatory-and-risk/esma-cracks-down-on-the-sale-of-binary-options-and-cfds-to-retail-investors).
- **BitMEX:** likide edilen yatırımcıların ort. kaldıracı ~60x; günlük zorunlu likidasyon/OI long %3,51 short %1,89 — [arXiv 2102.04591](https://arxiv.org/abs/2102.04591).
- **Binance:** müşterilerin %79'u >20x (2020 Binance çalışması, ikincil atıf); rastgele işlem simülasyonu 75x'te %97,3 likidasyon — [NYU Stern](https://www.stern.nyu.edu/sites/default/files/assets/documents/Duron-Carielo_Is%20There%20A%20Future%20In%20Perpetual%20Futures.pdf).
- **Gün-içi trader hesap verisi (kripto dışı):** Brezilya — >300 gün devam eden 1.551 day-trader'ın %97'si ücretler sonrası kaybetmiş (Chague, De-Losso & Giovannetti, *Day Trading for a Living?*) — [SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101); Tayvan (Barber vd.) — %1'den azı yıldan yıla öngörülebilir kârlı; bazıları maliyet öncesi kârlı, sonrası zararlı — [riskstock özet](https://riskstock.com/article-why-most-day-traders-lose-money.html) (ikincil). 
- **Kripto retail:** hesap-düzeyi büyük bir kripto day-trader çalışması **bulunamadı**; 2025-08 anketi: ilk yıl %84 kayıp, %58 sermayenin neredeyse tamamını kaybetmiş (anket, hesap verisi değil) — [Business Money](https://www.business-money.com/announcements/crypto-day-trading-success-real-stats-strategies-for-profitable-returns/) (zayıf kaynak).

### Inferences
- Tayvan/Brezilya bulgusu scalping için en kritik ders: **brüt** kârlı küçük bir azınlık maliyetle zarara geçiyor → işlem sıklığı arttıkça maliyet/kenar oranı belirleyici hale geliyor.
- Disiplinli bir scalp botu için makul çerçeve (matematikten türetilmiş, kaynaklı "pratisyen standardı" değil): işlem başı risk %0,25–1 özkaynak, kaldıraç = risk%/stop% → 20 bp stop ve %0,5 risk ≈ 2,5x efektif kaldıraç. 1:20 limiti bu bot için bağlayıcı değildir; bağlayıcı olan likidasyon/stop-out mesafesinin stop'tan **çok** uzakta kalmasıdır.

### Gaps
- "Disiplinli BTC scalper'ları işlem başı ne risk / ne kaldıraç kullanıyor" sorusuna güvenilir birincil kaynak bulunamadı (yalnız pazarlama blogları).
- Pepperstone'un kendi "retail hesapların %X'i kaybediyor" güncel beyanı ve hangi düzenleyici kuruluş altında 1:20 BTC kaldıracı verildiği (ESMA retail sınırı 2:1) bu oturumda doğrulanmadı — kutudaki hesap türü kontrol edilmeli.

## 6. Scalping faktör haritası

| Faktör | Mekanizma | Kanıt gücü (BTC, 2022–26) | Gereken veri | Ufuk |
|---|---|---|---|---|
| OFI / L1-L2 defter dengesizliği | Eşzamanlı fiyat etkisi; çok kısa öngörü | **Güçlü ama sub-bp, eşzamanlı ağırlıklı** (Cont vd.; Hawkes/LOB 2026) | L2 tick, ms zaman damgası | sn–dk |
| Çeyrek-saat açılış akışı | Periyodik algoritmik icra | **Orta-güçlü, OOS** ama ~0,5 bp; 4–12 sa ufukta dengesizlik öngörüsü (arXiv 2607.09426) | aggTrades (perp) | 10 sn; 4–12 sa |
| 1m taker buy/sell (CVD) | Agresif akış basıncı | **Zayıf** (1 dk dengesizlik "çok zayıf") | 1m kline taker-buy hacmi | 1–60 dk |
| OI değişimi (5m) | Yeni pozisyon vs zorunlu kapanış ayrımı | **Kanıt yok** (yalnız kaskad öncesi heterojen) | Binance 5m metrics | 5–60 dk |
| Likidasyon kümesi | Zorunlu akış → aşma → dönüş? | **Kanıt yok**; proje OHLCV şok-fade negatif | forceOrder (artık REST'te yok) / CoinGlass | 5–60 dk |
| Funding seviyesi/değişimi | Kalabalık taraf, taşıma maliyeti | **Kanıt yok** (yalnız funding tahmini); proje funding saati negatif | 8s funding, premium index | saat–gün |
| Long/short oranları (top vs global) | Akıllı para vs kalabalık | **Kanıt yok**; kaskad öncesi olaydan olaya değişken | 5m metrics | saat |
| Baz (perp−spot premium) | Kaldıraç talebi | Mekanizma kanıtlı (yakınsama), öngörü kanıtı yok | spot+perp 1m | saat |
| Coinbase premium / CME lead | Fiyat keşfi | Lead 0,05–0,15 sn → 1m'de **ölü** | Coinbase/CME tick | sn-altı |
| VWAP / hacim profili | Kurumsal referans, dönüş | **Akademik kanıt yok**; proje kanal-RJ negatif | 1m OHLCV | 15–60 dk |
| Volatilite sıkışması | Rejim geçişi | Kanıt yok (proje SQZ diğer sembollerde C) | 1m OHLCV | 15–60 dk |
| Seans açılışı (13:30 UTC, Asya) | Likidite/haber akışı | Shen vd. momentum (ETF öncesi); proje ETF sonrası TSMOM −0,039R → **çürümüş** | 1m OHLCV | 30–60 dk |
| Makro (CPI/FOMC) | Bilgi şoku | BTC-özel dakika çalışması bulunamadı | Takvim + 1m | 1–60 dk |

## 7. Kaldıraç ve risk matematiği

(Türetilmiş formüller; kaynak gerektirmeyen standart matematik.)

- **Beklenti R cinsinden (kaldıraçtan bağımsız):** E[R] = p·W̄ − (1−p)·L̄ − c/s, burada W̄, L̄ = ortalama kazanç/kayıp (R), c = gidiş-dönüş maliyet (bp), s = stop mesafesi (bp). Kaldıraç L yalnız özkaynak getirisini ölçekler: r_eq = L·r_fiyat.
- **Maliyetin R'deki ağırlığı:** c_R = c/s. CFD c=1,85 bp: s=10 bp → 0,185R; s=20 → 0,093R; s=50 → 0,037R. Perp taker-taker c≈10 bp: s=20 → **0,5R**.
- **Başabaş isabet (simetrik TP=SL=d bp):** p* = ½ + c/(2d). Genel: p* = (L̄ + c/s)/(W̄ + L̄) (R cinsinden, W̄=TP/s).
- **Pozisyon büyüklüğü:** Q = f·E / (s·P) (adet); efektif kaldıraç L_eff = f/s (oran olarak). f=%0,5, s=%0,2 → 2,5x.
- **Kelly:** ikili sonuç f* = p − (1−p)/b (b = W̄/L̄); sürekli yaklaşım f* ≈ μ/σ² (işlem başı getiri ort./varyans). Pratikte ½–¼ Kelly (tahmin hatası). Kelly-optimal kaldıraç L* = μ/σ²; geometrik büyüme g ≈ L·μ − ½L²σ² → L>2L*'de g<0 (pozitif kenarla bile iflasa sürüklenme).
- **Perp izole marjin likidasyon fiyatı (yaklaşık):** long: P_liq ≈ P₀·(1 − 1/L + mmr); short: P_liq ≈ P₀·(1 + 1/L − mmr). 20x, mmr %0,4 → long için −%4,6. Kural: stop mesafesi ≪ |P₀−P_liq|.
- **CFD stop-out:** ESMA tipi hesap-düzeyi kapatma marjin seviyesi %50'ye inince; 1:20'de (marjin %5) tek pozisyon tüm özkaynağı marjin olarak kullanırsa ≈ −%2,5 fiyat hareketinde kapanma.
- **Batma olasılığı (sürekli yaklaşım):** D oranında düşüşe hiç ulaşmama olasılığı için P(DD ≥ D) ≈ exp(−2·μ_e·ln(1/(1−D))/σ_e²), μ_e, σ_e = özkaynağın işlem başı log-getiri ort./std. μ_e ≤ 0 ise P=1 (negatif beklentide kaldıraç sadece batışı hızlandırır).
- **Kenar/maliyet çıtası:** gerekli brüt ortalama hareket |E[Δ]| ≥ k·c, k≥2 (stres spread ×1,5 + kayma tamponu).

## 8. Sınanabilir scalp hipotezleri (1m bar + Binance futures verisi)

**Ortak protokol (tüm H'ler):** veri Binance BTCUSDT perp 1m kline (taker-buy hacmi dahil) + 5m metrics (OI, top-trader L/S, global L/S, taker oranı) + 8s funding; dönemler KEŞİF 2021-06→2023-12 / OOS 2024-01-11→2025-06 / KÖR 2025-07→2026-10 (önceki raporla aynı). Sinyal bar *t* kapanışında hesaplanır, giriş **t+1 açılışı**; tek pozisyon; maliyet iki senaryo: CFD 1,85 bp (stres 2,8 bp) ve perp maker-giriş/taker-çıkış 7 bp, taker-taker 10 bp. 5m metrik satırı ancak kendi 5m penceresi kapandıktan sonra kullanılır (sızıntı koruması; damga anlamı doğrulanmalı). **Geçme ölçütü (her H):** CLAUDE.md 6 ölçütlü kart (≥150 olay; ortR>0 ve P(EV>0)≥%90; iki kronolojik yarı ≥0; spread ×1,5'te pozitif; sonraki-M1 icrası; tek-pozisyon) **+** aile içi Holm p<0,05 **+** aynı yıl/UTC-saat rastgele giriş plasebosunda ≤%5 yüzdelik **+** brüt ortalama ≥ 2×maliyet. Parametre yalnız KEŞİF'te; onay OOS∪KÖR. Kapı defterine (docs/KAPI_KAYIT_DEFTERI.md) önce bakılmalı — S05/S06/T07/T08/M06 ile örtüşenler aşağıda "yeni tanım" gerekçesiyle işaretli.

| # | Ad | Tam tanım | Çıkış | Not |
|---|---|---|---|---|
| H1 | Akış patlaması devamı | Signed flow F_t=(2·TB_t/V_t−1)·V_t; z_F = (F_t−ort₆₀)/std₆₀ ≥ 3 **ve** r_t aynı işaretli, |r_t| ≥ 1,5·ATR1m(60) → akış yönünde | Zaman 15 dk; ek varyant TP/SL = 1,0/1,0×ATR15m | Negatif kontrol ile kıyas: aynı |r_t| ama |z_F|<1 |
| H2 | Emilim (absorption) fade | z_F ≥ 3 ama |r_t| ≤ 0,25·ATR1m(60) (akış var, fiyat gitmiyor) → akışın **tersine** | 15 dk / TP-SL 1×ATR15m | Pratisyen "delta divergence" iddiasının operasyonel hali |
| H3 | Long-likidasyon proxy fade | 5m: r₅ ≤ −3·σ₅(288) **ve** ΔOI₅/OI ≤ −%0,5 (veya z ≤ −3) → BUY t+1 | 30 dk ve 60 dk zaman çıkışı; SL = olay dibi −0,25×ATR15 | S05'ten fark: OI düşüşü şartı (yeni veri) |
| H4 | Yeni-short devamı | r₅ ≤ −3σ₅ **ve** ΔOI₅ z ≥ +2 (yeni pozisyon açılıyor) → SELL | 30/60 dk | H3'ün ayna kontrolü; H3 dönüş, H4 devam öngörür |
| H5 | Short-squeeze fade (kontrol) | r₅ ≥ +3σ₅ **ve** ΔOI₅ z ≤ −3 → SELL | 30/60 dk | Ön beklenti: **kaybeder** ("coşku dönmez", S06 −0,194R); geçerse şüphe |
| H6 | Kalabalık funding + ilk karşı şok | Son funding ≥ 90. yüzdelik (365g kayan) **ve** global L/S ≥ 90. yüzdelik; sonra ilk 1m bar r ≤ −2·ATR1m(60) → SELL (kalabalık long'un çözülmesi); ayna short için | 60 dk | M06 (funding saati) değil: koşul = funding **seviyesi** + tetik |
| H7 | Funding-öncesi taşıma kayması | |funding_tahmini| ≥ %0,03 iken settlement'tan 30 dk önce **ödeme alan** tarafta gir, settlement+5 dk çık | sabit | M06'ya göre yeni tanım: işarete koşullu |
| H8 | Likidite sweep reddi | Önceki 4s (veya Asya 00–07 UTC) tepesi/dibi ≤0,3×ATR15m aşılıp 3 bar içinde aralığın içine kapanış **ve** kırılım barında z_F ≥ 2 (sıkışan agresörler) → ters yönde | SL = sweep ucu +0,1×ATR15; TP = aralık ortası; zaman 60 dk | Kanal-RJ (M01) negatifti; fark: akış teyidi |
| H9 | ABD açılış momentumu | 13:30–14:00 UTC getirisi |r| ≥ 0,5σ (20g) **ve** aynı yönlü kümülatif z_F>0 → 14:00 açılışında yön | 15:00 UTC zaman çıkışı | Shen vd. replikasyonu; T07 ETF sonrası negatif → ön beklenti zayıf |
| H10 | VWAP dönüşü, sakin rejim | 00:00 UTC çapalı VWAP'tan sapma ≥ 2·std(sapma, 24s) **ve** 1s RV alt tercile **ve** |ΔOI₆₀| < medyan → VWAP'a doğru | TP = VWAP; SL = 1,5×sapma; 60 dk | Rejim şartı yeni tanım |
| H11 | Sıkışma kırılımı + akış | 1m BB(60) genişliği son 24s'in alt %5'i; kapanış bandın dışı **ve** z_F ≥ 2 aynı yönde → yön | 30 dk / TP-SL 2/1×ATR15 | SQZ hükmü (C) diğer sembollerde; BTC'de akış teyidi yeni |
| H12 | Makro açılış devamı vs dönüş | CPI/NFP (12:30 UTC) ve FOMC (18:00 UTC) günleri; olay dakikası r_0 işaretiyle, giriş 12:32 açılışı | 5/15/60 dk; devam ve fade iki ayrı hücre (ön-kayıtlı) | n<150 riski (yalnız ~3,5 yıl × ~30 olay) → sadece GÖLGE kanıtı olabilir |
| H13 | Top-trader vs kalabalık ıraksaması | 5m: top-trader pozisyon L/S oranı 24s z ≥ +2 **ve** global hesap L/S z ≤ −1 → top-trader yönünde | 60 dk | 5m metrics şart |
| H14 | Hacim tükenme fadi | 1m hacim z ≥ 5 (60 bar) **ve** fitil ≥ bar aralığının %60'ı → fitil yönünün tersine değil, fitil reddi yönünde (ör. uzun alt fitil → BUY) | 15 dk | Saf OHLCV; kontrol hipotezi |
| H15 | Çapraz venue (ölüm testi) | Coinbase BTC-USD 1m kapanış − Binance BTCUSDT (USDT/USD düzeltmeli) premium z ≥ 3 → premium yönünde CFD | 5/15 dk | Lead-lag sn-altı → ön beklenti: **geçmez**; geçerse sızıntı denetimi |

## 9. Venue karşılaştırması ve başabaş

| Venue / emir tipi | Gidiş-dönüş maliyet c (bp) | Kaldıraç | Taşıma | p* @ TP=SL=10 bp | p* @ 20 bp | p* @ 50 bp | Not |
|---|---|---|---|---|---|---|---|
| Pepperstone BTCUSD CFD (taban) | ~1,85 (stres 2,8) | 1:20 | Long −%14/yıl, short +%2 (rollover) | %59,3 | %54,6 | %51,9 | Kaynak: [önceki rapor](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md); haber anı spread genişlemesi ölçülmedi |
| Binance perp maker-maker | 4 (+ dolmama riski) | ≤125x (yeni hesap 60g ≤20x) | Funding 8s | %70 | %60 | %54 | Ücretler: [Finder](https://www.finder.com/binance-futures-fees); dolmayan emirler kazananları seçici kaçırır (adverse selection) |
| Binance perp maker giriş / taker çıkış | 7 | aynı | aynı | %85 | %67,5 | %57 | Stop çıkışı taker olmak zorunda |
| Binance perp taker-taker | 10 (BNB ile 9) + kayma | aynı | aynı | **%100** | %75 | %60 | Taban kademe scalping için en pahalı |
| Bybit perp taker-taker | 11 | — | Funding | %105 (imkânsız) | %77,5 | %61 | [Bitsgap](https://bitsgap.com/blog/bybit-trading-fees-explained-what-it-costs) |
| OKX perp taker-taker | 10 | — | Funding | %100 | %75 | %60 | [BitDegree](https://www.bitdegree.org/crypto/tutorials/okx-fees) |

(p* = ½ + c/(2d); kayma ve funding hariç.)

**Okuma:** Taban kademede CFD, perp'ten **3–5 kat ucuz**. 10–20 bp'lik klasik scalp hedefleri perp taker'da matematiksel olarak ya imkânsız ya da %75 isabet gerektiriyor; CFD'de bile 10 bp hedef %59 isabet ister. Uygulanabilir alan: **≥30–50 bp ortalama hareketli, 15–60 dk tutulan, seyrek, olay-tetikli** girişler; sinyal Binance futures verisinden (OI/akış/funding), icra CFD'de. Perp'e geçiş ancak (a) maker-ağırlıklı icra kurulabilir ve dolmama yanlılığı ölçülürse ya da (b) VIP kademe/rebate'e ulaşılırsa anlamlıdır — bu bot ölçeğinde gerçekçi değil.
