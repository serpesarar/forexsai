# BTC gün-içi ve kısa ufuklu anomaliler — yayımlanmış kanıtın taraması (2026-10 itibarıyla)

> Kapsam notu: Bu not ~25 arama/çekme ile hazırlandı. Birçok makalenin tam metnine erişilemedi (Reading/Centaur bot koruması, ScienceDirect 403). Özet/abstract'tan gelen bilgiler öyle işaretlendi. **"Maliyet dahil mi / OOS var mı" bilgisi kaynakta yoksa "belirtilmemiş" yazıldı. Bu, maliyetin dahil olmadığı anlamına gelmez, sadece doğrulanamadığı anlamına gelir.** Önce 2020 öncesi veriyle bulunan sonuçlar ⚠️ ile işaretlendi (bozulmuş olabilir).

---

## 1. Saat ve gün etkileri: 21–23 UTC, hafta sonu, Pazartesi, CME boşluğu, funding saatleri

### Takeaway
Hafta sonu ve gece **düşük hacim** etkisi tutarlı bir yapısal gerçek. Getiri anomalileri ise kırılgan. En çok alıntılanan **21:00–23:00 UTC long** etkisi 2015–2023 Gemini verisinde var ama 2022–23'te zayıfladı. Bulunan hiçbir kaynakta maliyet ya da resmi OOS testi yok. Pazartesi etkisi 2015 sonrasında kayboluyor. CME boşluğu "dolma" istatistikleri birincil veriye dayanmıyor. Funding saatlerine (00/08/16 UTC) ait fiyat örüntüsü üzerine hakemli bir çalışma bulunamadı.

### Cited Findings
- **Padysak & Vojtko (2022), "Seasonality, Trend-following, and Mean Reversion in Bitcoin"**: Gemini'nin saatlik verisi kullanılıyor (Ekim 2015 – Şubat 2022). En güçlü getiriler 21:00–23:00 UTC'de, yani büyük hisse borsaları kapalıyken toplanıyor. Kural "21:00'de al, 23:00'te sat". Raporlanan getiri yıllık ≈%33, oynaklık ve düşüş buy-and-hold'dan düşük. Makalenin net mi brüt mü olduğu belirtilmemiş. Yazar "spot ücretleri ~%0,1 veya altı yönetilebilir ama canlıda dahil edilmeli" diyor. — [PapersWithBacktest özeti](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)
- **Quantpedia uzatılmış örneklem (9 Eki 2015 – 30 Haz 2023, Gemini saatlik, UTC)**: 22:00 ve 23:00 UTC saat getirileri diğer saatlerden anlamlı biçimde yüksek. 21→23 stratejisi yıllık %40,64 getiri, Calmar 1,79 ve MaxDD −%22,7 veriyor (BTC buy-and-hold'da >−%70). **Strateji 2022 ve 2023'te zayıf dönem geçirdi.** **İşlem maliyeti ve OOS testi belirtilmemiş.** Gün kırılımında en güçlü gün Cuma, ardından Perşembe ve sonra Cumartesi-Pazar. Yüksek oynaklık filtresi (30g oynaklık > 1 yıllık medyan) ile yıllık %37,26 getiri ve MaxDD −%18,87. Fiyat 10/20/50/200g ortalamanın üstündeyken (yükseliş trendi günleri) 22–23 penceresi daha güçlü. — [Quantpedia: The Seasonality of Bitcoin](https://quantpedia.com/the-seasonality-of-bitcoin/)
- Aynı Gemini verisiyle yapılan önceki Quantpedia analizi şunu buluyor: hafta sonu ve tatillerde gün-içi getiri baskın, NYSE açık günlerde ise "overnight" getiri baskın. ⚠️ Bu bağımsız bir teyit değil, aynı veri seti. — [Quantpedia: Intraday or Overnight Anomalies in Bitcoin](https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/)
- 2024 takip çalışması (Beluská & Vojtko) veriyi Ağustos 2024'e kadar uzattı. Bulunan özet seans etkisinin 2024'e kadar sürüp sürmediğini açıkça söylemiyor, yalnızca MAX/MIN stratejileri için "etkili kaldı" diyor. — [PapersWithBacktest](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)
- **Mueller (2024), "Revisiting seasonality in cryptocurrencies", Finance Research Letters 64, 105429**: Kripto seasonality kanıtı sağlam değil. BTC'nin pozitif Pazartesi etkisi iç geçerliliğe sahip ama **2015 sonrası veride sürmüyor**. Sağlam getiri anomalisi bulunmuyor. Sağlam olan bulgu **hafta sonu düşük işlem aktivitesi** ve bu 500 coin'de tutuyor. Coin kesitinde Pazartesi etkisi genelde negatif ama güven aralıkları geniş. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/finlet/v64y2024ics1544612324004598.html)
- ⚠️ Eski çalışmalar: Caporale & Plastun (2013–2017) BTC'de "ters Pazartesi" etkisi buluyor (Pazartesi getirisi yüksek). Baur, Cahill, Godfrey & Liu (FRL 2019, 15 milyondan fazla gözlem, 7 borsa) ise zamana göre değişen ama tutarsız etkiler, düşük hafta sonu hacmi ve yüksek Pazartesi getirisi raporluyor ve piyasanın etkin olduğu sonucuna varıyor. — [Quantpedia calendar effects](https://quantpedia.com/are-there-any-simple-calendar-effects-in-bitcoin-market/)
- ⚠️ Eross, McGroarty, Urquhart & Wolfe (2019), "The intraday dynamics of bitcoin" (5 dk veri): Hacim gün boyunca zirve yapıyor ve ~16:00'dan gece yarısına düşüyor. Gerçekleşen oynaklık görece sabit ama büyük borsalar açılırken en yüksek. Likidite sabah erken saatlerde en ince. — [Centaur/Reading PDF](https://centaur.reading.ac.uk/81745/3/2.R&R.Manuscript.pdf)
- **Kurdi & Nadarajah (2026), Computational Economics** (Binance 1 dk, 2017–2025): Günlük fiyat zirveleri ~18:00 UTC civarında, minimum hacim ~00:31 UTC civarında kümeleniyor. Bu çalışma yön değil, zamanlama dağılımı ölçüyor. — [Springer](https://link.springer.com/article/10.1007/s10614-026-11438-0)
- **Shanaev, Vasenin & Stepanov (2023), "Turn-of-the-candle effect", Heliyon 9(3)**: 1 dk veri, 7 borsa, Aralık 2021'e kadar. Pozitif getiriler dakika :00/:15/:30/:45'te yoğunlaşıyor, 2021 Bitfinex'te dönüm-dakikası başına ort. **0,58 bp**. Chow testlerine göre etki 2020 ortası-sonu ortaya çıkmış. Bitfinex'te ücret ve spread sonrası yıllık %74,18 (B&H %60,27), ancak varsayım sıfır-ücret hacim kademesi. **OOS (Oca–Ağu 2022) katsayılar ~0,9'dan 0,11–0,29'a düştü.** Belgelenmiş bir çürüme var. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/)
- **CME boşluğu:** Hakemli bir çalışma ya da CME'nin resmi bir çalışması bulunamadı. Dolaşan "%90–95 dolar" rakamları birincil veriye izlenemiyor. Aynı kaynak sitede "en az %65" diyen de var. CoinDesk'e atfedilen "80 boşluğun 79'u doldu" iddiası ikinci el. CME BTC vadelisi Pazar–Cuma 23 saat işlem görüyor, spot 7/24. — [TradingView fikir sayfası](https://www.tradingview.com/ideas/cmegaps/); [haber özeti](https://rss.boorghani.com/?p=289567)
- **Funding saatleri:** Funding genelde 8 saatte bir hesaplanıyor (perp ile spot farkının önceki aralık ortalaması), bazı borsalar daha kısa aralık kullanıyor. — [Coin Metrics docs](https://docs.coinmetrics.io/market-data/market-data-overview/funding-rates/funding-rates); [arXiv 2212.06888](https://arxiv.org/pdf/2212.06888). 00/08/16 UTC çevresindeki getiri örüntüsünü test eden bir makale bulunamadı. "Aşırı negatif funding sonrası rahatlama rallisi" iddiası (ör. 24+ saat −%0,03 altı funding sonrası bir haftada %5–15) yalnızca uygulayıcı sitesinde var ve doğrulanmamış. — [Sharpe.ai](https://www.sharpe.ai/funding-rate/bitcoin)

### Inferences
- 21–23 UTC etkisinin bilinen tüm kanıtı **tek bir veri setinden (Gemini), tek bir araştırma grubundan (Quantpedia/Vojtko)** geliyor. Maliyet ve resmi OOS yok, ve 2022–23'te zayıfladığı bizzat yazarlarca not edilmiş. Bu nedenle "kanıtlanmış" değil, ancak **ön-kayıtlı test adayı** sayılır.
- **Kritik çakışma:** Kaiko'nun ETF NAV/benchmark penceresi 15–16 ET, yani 20–21 UTC (EST'de 21–22 UTC). Pepperstone kripto rollover'ı da sunucu gece yarısında (00:00 sunucu = 5pm NY ≈ 21:00 UTC yaz / 22:00 UTC kış). 21–23 UTC penceresi bu nedenle hem ETF kapanış akışıyla hem de **CFD swap kesim anıyla** örtüşüyor. CFD'de bu pencereyi tutmak her gece swap ödetebilir ve rollover anındaki spread genişlemesine maruz bırakır (bkz. §6). Bu bir çıkarımdır ve broker'ın sunucu saati doğrulanmalı.
- Pazartesi/hafta sonu **getiri** etkileri için kanıt zayıf. **Hacim/likidite** etkisi ise güçlü, bu yüzden hafta sonu bir "maliyet kapısı" olarak ele alınmalı, getiri sinyali olarak değil.
- Turn-of-the-candle etkisinin 0,58 bp/dk büyüklüğü, tipik CFD spread'inin (~1–2 bp, §6) altında. Perakende CFD için **yapısal olarak işlenemez**.

### Gaps
- 21–23 UTC etkisinin **2024-01 ETF sonrası** ve **2025–2026** performansı için bağımsız bir kaynak bulunamadı.
- Funding-saati getiri örüntüsü üzerine hakemli kanıt bulunamadı.
- CME boşluğu dolma oranı için birincil dataset ya da plasebo karşılaştırması (rastgele referans seviyelerinin "dolma" oranı) bulunamadı.

---

## 2. Gün-içi momentum (ilk yarım saat → son yarım saat) ve kısa vadeli dönüş

### Takeaway
Hakemli kanıt **ikisinin birlikte var olduğunu** söylüyor. Hacim-tanımlı seansta ilk yarım saat son yarım saati öngörüyor (Shen-Urquhart-Wang 2022, OOS dahil). Öte yandan 1–4 saat ufkunda negatif otokorelasyon ve büyük hareket sonrası dönüş var (De Nicola 2021). Büyük ve likit coin'ler günlük/haftalık momentum, küçük ve illikit coin'ler reversal gösteriyor. 2022 sonrası çürüme ve maliyet sonrası performans için kaynak bulunamadı.

### Cited Findings
- **Shen, Urquhart & Wang (2022), "Bitcoin intraday time series momentum", Financial Review 57(2):319–344, DOI 10.1111/fire.12290**: BTC 7/24 işlem gördüğü için seans başlangıcı **hacimle** tanımlanıyor. İlk yarım saatin getirisi son yarım saatin getirisini öngörüyor. Öngörü gücü en yüksek hacim/oynaklık seanslarında daha güçlü. Momentum stratejileri piyasa zamanlaması ve varlık dağılımında "önemli ekonomik kazanç" veriyor, **özellikle BTC düşüş dönemlerinde**. Yazarlar mekanizmayı FX'teki gibi likidite sağlanmasına bağlıyor, geç-bilgilenen işleme değil. — [Univ. of Birmingham kaydı](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/). Arama özetine göre testler in-sample ve out-of-sample, veri Bitfinex, Bitstamp, CEX.IO, Coinbase ve Kraken'den. — [ResearchGate](https://www.researchgate.net/publication/355603160_Bitcoin_intraday_time_series_momentum). ⚠️ Tam metne erişilemedi. Örneklem büyük olasılıkla ≤2020 (kabul 2021). Maliyet ve R² değerleri doğrulanamadı.
- Hisse senedi orijinali Gao ve ark. (2018), ABD ETF'leri üzerinde: öngörü yüksek oynaklık günlerinde, resesyonda ve makro haber günlerinde daha güçlü. — [Alpha Architect](https://alphaarchitect.com/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- **De Nicola (2021), "On the Intraday Behavior of Bitcoin", Ledger 6:58–80**: 1, 2 ve 4 saatlik getirilerde **anlamlı negatif birinci-derece otokorelasyon** var, daha büyük hareketler yüzde olarak daha güçlü dönüş üretiyor. Açıklama aşırı tepki, aşırı oynaklık ve **zincirleme likidasyonlar**. Basit bir algoritmik strateji geriye dönük uygulanmış. Maliyet ve OOS özette belirtilmemiş. — [LMU ePub](https://epub.ub.uni-muenchen.de/97651/)
- "Intraday Bitcoin price shocks: when bad news is good news": Saatlik veride **negatif şoklar sonrası açık aşırı tepki** (dönüş) var, 12 ve 24 saatlik tutuşlarda devam örüntüsüne dönüyor. — [Tandfonline](https://www.tandfonline.com/doi/full/10.1080/15140326.2022.2151253)
- Hisse piyasalarındaki büyük salınımlar sonrasında gün-içi BTC dönüşü görülüyor ve aşırı tepki hipotezini destekliyor. Gelişmiş piyasa hareketleri sonrası dönüş daha güçlü. — [ScienceDirect (IREF 2023)](https://www.sciencedirect.com/science/article/abs/pii/S1059056023004446)
- "Intraday return predictability in the cryptocurrency markets: Momentum, reversal, or both", NAJEF 2022 (DOI 10.1016/j.najef.2022.101733): Arama özetine göre gün-içi dönüşün kriptoya özgü olduğunu ve aşırı tepki/aşırı güvene bağlanabileceğini öne sürüyor. ⚠️ Abstract doğrulanamadı (403). — [IDEAS](https://ideas.repec.org:443/a/eee/ecofin/v62y2022ics1062940822000833.html)
- **Zaremba ve ark. (2021), "Up or down?", IRFA 78**: Günlük veri, 3.600'den fazla coin. Düşük önceki-gün getirisi daha iyi performansı öngörüyor (reversal) ve bu illikiditeye bağlı. **En büyük ve likit coin'ler ise günlük momentum gösteriyor.** — [IDEAS](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002349.html)
- Fičura (2023): Haftalık dönüş esas olarak küçük ve illikit coin'lerde görülüyor, büyük ve likit coin'ler haftalık momentum gösteriyor. — [IDEAS](https://ideas.repec.org/p/prg/jnlwps/v5y2023id5.003.html)

### Inferences
- BTC'de iki farklı ufuk görünüyor. **Dakikalar–4 saat ufkunda büyük şok sonrası dönüş**, **12–24 saat ve günlük ufukta ise devam (momentum)**. Bu, projenin NDX'te gördüğü "korku döner" asimetrisiyle yapısal olarak uyumlu, çünkü negatif şokta aşırı tepki belgelenmiş. Pozitif şokun dönüp dönmediği ayrıca test edilmeli.
- ETF sonrası "seans" tanımı muhtemelen değişti (ABD saatleri, 20–21 UTC fixing, §5). Shen ve ark.'nın hacim-tanımlı seansı 2024 sonrası verinin kendi hacim profilinden **yeniden** türetilmeli. Eski seans saatleri kullanılmamalı.

### Gaps
- Shen ve ark.'nın tam örneklem dönemi, OOS R² değeri ve maliyet varsayımı doğrulanamadı (tam metin erişimi engellendi).
- 2022 sonrası ve ETF sonrası BTC gün-içi momentum/reversal'ın bağımsız tekrarı bulunamadı. GitHub'daki BTCUSDT 30 dk uygulaması sadece kod, sonuç değil. — [GitHub PR](https://github.com/HCH725/alpha-strategy-research/pull/170)

---

## 3. Kırılım ve trend takibi (Donchian, MA, TSMOM) 2018–2026

### Takeaway
BTC'de günlük trend takibi (10 günlük zirve alımı, fiyat/MA oranı) uzun örneklemde buy-and-hold'u risk-ayarlı geçiyor. Ancak bulunan kaynakların çoğu ya maliyet ya da OOS bilgisini açıkça vermiyor. Tek tek BTC'ye özgü, 2022 dahil, maliyetli ve resmi OOS'lu bir Donchian testi **bulunamadı**. En yakın kanıt çok-coin portföyleri. Maliyet duyarlılığı yüksek: bir çalışmada Sharpe 0 bp maliyette 2,87 iken 12 bp'de 1,62.

### Cited Findings
- **Padysak & Vojtko (2022)** (Gemini, 2015–2022):
  - **MAX10**: fiyat son 10 günün zirvesindeyken al. 10–50 gün bakışlar test edildi, en iyisi 10. B&H'ye göre daha yüksek getiri ve daha düşük oynaklık.
  - **MIN10**: 10 günlük dipte al. Daha düşük getiri, daha sığ düşüş.
  - **İkisi birlikte**: yıllık ≈%98 getiri, ≈%48 oynaklık, getiri/risk >2, ancak **en iyi stratejide bile >%40 düşüş**. B&H ≈%65 getiri, %75 oynaklık, >%80 düşüş.
  - Net/brüt durumu belirtilmemiş, holdout yok. Beluská & Vojtko (2024) Ağustos 2024'e kadar "etkili kaldı" diyor. Bu yayın-sonrası bir dönem ama resmi OOS değil.
  — [PapersWithBacktest](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)
- **Detzel ve ark. (2021)**: Fiyat/hareketli ortalama oranları günlük BTC getirisini in-sample **ve out-of-sample** öngörüyor, B&H'ye göre alfa ve Sharpe kazancı var. — [arama özeti, Concretum/ResearchGate bağlamı](https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/). ⚠️ Örneklem 2021 öncesi, 2022 ayı piyasası dahil değil.
- **Zarattini, Pagani & Barbon (2025), "Catching Crypto Trends"**: Farklı bakışlı Donchian ensemble'ı, 20 coin rotasyonu. Sharpe >1,5 "net of fees", BTC'ye göre yıllık %10,8 alfa. Sayfada örneklem dönemi, maliyet varsayımı, 2022 performansı ve OOS ifadesi yok. Sonuç **BTC tekil değil, portföy**. — [Concretum Group](https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/)
- **AdaptiveTrend (arXiv 2602.11708, 2026)**: Kripto TSMOM varyantı. **OOS Ocak 2022 – Aralık 2024**, 4 bp taker ücreti + kayma + funding dahil. Maliyet duyarlılık tablosunda Sharpe 0 maliyette 2,87, 12 bp'de **1,62**. Yazarlar aylık yeniden-optimizasyonun **ileriye bakma yanlılığı** yarattığını kendileri not ediyor. — [arXiv](https://arxiv.org/html/2602.11708v1)
- MA çalışmalarında kayma ve maliyetin özellikle **kısa MA'larda** kârlılığı ciddi etkilediği belirtiliyor. — [ResearchGate](https://www.researchgate.net/publication/389395534_Bitcoin_Financial_Forecasting_Analyzing_the_Impact_of_Moving_Average_Strategies_on_Trading_Performance)

### Inferences
- Günlük kırılım (MAX10/Donchian), projenin altında kanıtlanmış "günlük Donchian + yalnız BUY" ailesinin BTC'deki doğal karşılığı ve en olası aday. Ancak CFD'de **swap maliyeti** (long ≈ −%18–22,5/yıl, §6) çok günlük tutuşu doğrudan vurur. Günde ~6 bp ve 10 gün tutuşta ~60 bp maliyet demek. Spot/ETF tabanlı makalelerde bu maliyet yok.
- 2022 ayı piyasasında long-only trend kuralları çoğunlukla nakitte kalarak korunur. Kuralın 2022'de "kaybetmemesi" ile "kazanması" ayrı ölçülmeli.
- Raporlanan büyük Sharpe değerleri tam örneklem ve tek veri setinden geliyor. Projenin 6 ölçütlü canlıya alma kartı (iki yarı, ×1,5 sürtünme, sonraki-bar icrası) bunları büyük olasılıkla ciddi şekilde küçültecek.

### Gaps
- BTC'ye özgü, 2022–2026 kapsayan, swap ve spread dahil ve resmi OOS'lu Donchian/MA testi bulunamadı.
- Haftalık TSMOM'un BTC'de 2022 sonrası performansı için güvenilir kaynak bulunamadı.

---

## 4. Aşırı hareket, likidasyon zinciri ve oynaklık patlaması sonrası ortalamaya dönüş

### Takeaway
Hakemli kanıt **1–4 saat ufkunda büyük hareket sonrası dönüşü** ve **negatif şoklarda aşırı tepkiyi** destekliyor. Likidasyon zincirleri bir mekanizma olarak öneriliyor. Ancak likidasyon olaylarını sayıp sonraki getirileri ölçen sağlam bir çalışma bulunamadı. "Korku döner, coşku dönmez" asimetrisi kriptoda doğrudan test edilmiş değil. Yalnız negatif şokta aşırı tepki bulgusu bu yönde.

### Cited Findings
- De Nicola (2021): 1–4 saatte negatif otokorelasyon var, büyük hareketler daha büyük yüzde dönüş üretiyor. Kısmen yüksek kaldıraçla gelen zincirleme likidasyonlara bağlanıyor. — [LMU ePub](https://epub.ub.uni-muenchen.de/97651/)
- Saatlik BTC'de **negatif şoklar sonrası açık aşırı tepki** var, 12–24 saat tutuşta devam örüntüsüne dönüyor. Aşırı tepki olaydan 6–24 saat sonra daha belirgin. — [Tandfonline](https://www.tandfonline.com/doi/full/10.1080/15140326.2022.2151253); [ResearchGate: Prevalence of Price Overreactions](https://www.researchgate.net/publication/340627203_The_Prevalence_of_Price_Overreactions_in_the_Cryptocurrency_Market). ⚠️ İki kaynakta ufuk ifadeleri çelişkili görünüyor (dönüş ↔ 12–24 saatte devam / 6–24 saatte aşırı tepki). Tam metinler doğrulanamadı.
- Delphi Digital: 6 büyük fitilli olayın hepsinde BTC sonunda likidasyon diplerini yeniden ziyaret etti. n=6, istatistik testi yok. — [Delphi](https://members.delphidigital.io/feed/price-action-apathy-continues-as-expected)
- Likidasyon öncesi OI ve ELR eşik iddiaları kaynaksız (uygulayıcı rehberi). — [axeladlerjr](https://axeladlerjr.com/bitcoin-liquidation-cascades-guide/)
- MIN10 (10 günlük dipte alım) daha düşük getiri ama daha sığ düşüş veriyor. Günlük ufukta dip alımı tek başına zayıf, momentum ile birleştirilince işe yarıyor. — [PapersWithBacktest](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)

### Inferences
- Projenin NDX'teki CAPREV ("stres günü sonrası açılış + dip kırılımı BUY, zaman çıkışı") mantığının BTC'deki karşılığı şöyle olur: **büyük negatif 1 saatlik şok → 1–4 saatlik long fade, zaman çıkışlı.** Pozitif şok fade'i ayrı kol olarak sınanmalı ve asimetri bu iki kolun farkı olarak ölçülmeli.
- Şok anında CFD spread'i genişler (§6). Fade girişi şok barının kapanışından değil, **sonraki M1 açılışı + o anki gerçek spread** ile ölçülmeli (go-live kartının 5. ölçütü). Bu tam da iyimser simülasyonun en çok yanıldığı yer.

### Gaps
- Olay sayımlı likidasyon zinciri → ileri getiri çalışması bulunamadı. Hyperliquid 10 Eki 2025 olay panelinin sonuçlarına erişilemedi.
- Kriptoda pozitif ve negatif şok asimetrisini doğrudan test eden çalışma bulunamadı.

---

## 5. Çapraz varlık bağlantıları (Nasdaq, VIX, DXY) ve spot-ETF sonrası gün-içi yapı

### Takeaway
BTC–Nasdaq korelasyonu 2020 sonrasında yükseldi ama **kararsız**. Bir kaynak Nasdaq'ın BTC için güvenilir bir **öncü gösterge olmadığı** sonucuna varıyor. VIX ile negatif ilişki ve VIX'in duyarlılık vekili olduğu raporlanıyor, ancak 2022–2026'da "VIX rejimi BTC yönünü öngörür" diyen sağlam OOS çalışma bulunamadı. ETF sonrası hacim ABD saatlerine ve özellikle 15–16 ET fixing penceresine kaydı. Hafta sonu hacim payı tarihi dipte.

### Cited Findings
- **Kaiko (27 Haz 2024)**:
  - 15–16 ET benchmark fixing penceresi tüm hacmin **%6,7'sinin üstüne** çıktı (Q1 2024). Q4 2023'te bu oran %4,5'ti.
  - Hafta içi ABD kapanışı benchmark borsalarda hacmin %6,6'sından fazlası, hafta sonu ise ~%4.
  - **Hafta sonu BTC hacim payı 2024'te %16 ile tüm zamanların en düşüğü** (2019 zirvesi %28).
  - ABD borsalarının BTC derinlik payı Ekim sonrası %45'e çıktı (bir yıl önce %35).
  - Q1 2024'te hafta içi 20–21 UTC hacmi 17,6 milyar $'ın üstünde.
  - Gün-içi oynaklığın artabileceği yalnızca öngörü olarak söyleniyor, ölçülmemiş.
  — [Kaiko](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure)
- Bloomberg'in aktardığı Kaiko verisine göre ABD piyasa saatleri, 2024'ün Nisan'a kadarki kümülatif hacminin **%46'sı** ile rekor kırdı. ABD saatlerinde payın en yüksek olduğu gün Perşembe. — [Bloomberg](https://www.bloomberg.com/news/articles/2024-05-21/share-of-bitcoin-volume-during-us-market-hours-surges-to-record)
- Daha yeni bir Kaiko özetine göre ABD seansı küresel spot hacmin **%47'si** (ETF öncesi %38). ⚠️ İkinci el. — [DailyCoin](https://dailycoin.com/bitcoins-weekend-gap-etfs-shift-liquidity-to-u-s-hours/)
- S&P Global: BTC–Nasdaq-100 korelasyonu son dönemde ≈0,3 (2017–19'a göre yüksek). BTC, VIX ile negatif ilişkili kalıyor. — [S&P Global](https://www.spglobal.com/en/research-insights/special-reports/bitcoin-volatility-trends-deep-dive)
- arXiv 2501.09911 (2018–2025): Nasdaq 100 ve S&P 500 ile korelasyonlar ETF lansmanı gibi kurumsal dönüm noktalarından sonra arttı, zirve 0,87. — [arXiv](https://arxiv.org/pdf/2501.09911)
- Coin Bureau (Mayıs 2019 – Mayıs 2024, hakemsiz): Korelasyon pozitif ile negatif arasında salınıyor, Nasdaq BTC için güvenilir ileri gösterge değil. — [Coin Bureau](https://coinbureau.com/analysis/bitcoin-and-stock-market-correlation)
- Kantil regresyon (2017–2021): Yatırımcı duyarlılığı (VIX vekil) BTC getirisi ve oynaklığını öngörüyor ama doğrusal olmayan biçimde, kantillere göre değişiyor. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1057521922003337)
- Hisse piyasası büyük salınımları sonrası gün-içi BTC dönüşü var (bkz. §2). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1059056023004446)

### Inferences
- Projenin NDX VIX-rejim kenarı (VIX≥18,4 → BUY lehte) BTC'ye **taşınabilir mi** sorusu literatürde yanıtsız. Bu yüzden saf bir ön-kayıt sorusu. Korelasyonun kararsızlığı, kenar çıksa bile iki-yarı kararlılık ölçütünün kritik olacağını gösteriyor.
- ETF sonrası "BTC'nin ana seansı" fiilen ABD nakit seansı ve 20–21 UTC fixing. Projenin NDX seans/saat kapıları BTC'ye uyarlanacaksa bölünme **2024-01-11 öncesi/sonrası** yapılmalı. Ön-ETF verisi bugünün yapısını temsil etmiyor.
- Gece Nasdaq/QQQ hareketinin BTC'yi öncelediğine dair doğrudan kanıt bulunamadı. "Hisse büyük salınımı → BTC dönüşü" bulgusu ise **öncülük değil, aşırı tepki** yönünde.

### Gaps
- 2022–2026 için VIX seviyesi/rejimi → BTC yönü OOS çalışması bulunamadı.
- DXY → BTC gün-içi öngörüsü için güvenilir kaynak bulunamadı.
- ETF sonrası gün-içi oynaklık dağılımının ölçülmüş değişimi bulunamadı (Kaiko yalnızca öngörüyor).

---

## 6. Perakende CFD mikro yapı gerçekleri: spread, swap, hafta sonu, kayma

### Takeaway
BTCUSD CFD'de hafta içi spread fiyatın ~1–2,5 bp'si iken hafta sonu ~11–40 bp'ye çıkıyor. Long swap tipik olarak **yıllık −%18–22,5**, yani **gecelik ~5–6 bp**. Rollover sunucu gece yarısında oluyor (≈21–22 UTC) ve **hafta sonu dahil her gün** kesiliyor. Bu rakamlarla, Turn-of-the-candle gibi 1 bp altı edge'ler ölü doğar. 21–23 UTC penceresi ve çok günlük trend tutuşları ise ciddi maliyet yer.

### Cited Findings
- **Pepperstone Limited "Cost and Charges" (Haziran 2026)**, kripto swap örneği (Örnek 4):
  - BTCUSD **long −%22,5/yıl**, **short +%7,5/yıl** (alacak).
  - 1 kontrat @95.000 için long gün başına −59,375 $ ((1×95000)×−0,225/360). Short gün başına +19,79 $.
  - Kripto overnight funding, **sunucu saati 00:00:00'da** tutulan pozisyonlara günlük işletiliyor. Genel rollover "5pm New York (23:59 server time)". Güncel oran platformun "Specifications" bölümünde.
  - Kripto komisyonu spread'e gömülü, ayrı komisyon yok.
  - ⚠️ Bunlar "örnek" rakamlar, güncel oranlar MT5 spesifikasyonundan okunmalı.
  — [Pepperstone Cost & Charges PDF (Haz 2026)](https://eu-assets.contentstack.com/v3/assets/bltaec35894448c7261/bltb3f65365f20ef593/6a1ebf2ab3c954c1e626efea/Pepperstone_Limited_Cost_and_Charges_-_June_2026.pdf); [Pepperstone swaps sayfası](https://pepperstone.com/en/forex-trading/swaps)
- **FXNX rehberi** (broker blogu, tek broker):
  - Normal hafta içi BTCUSD spread'i **~8–20 $**. **Cuma 21:00 UTC – Pazar 22:00 UTC arası ~100–350 $+**. Örnek: hafta içi 20 $ spread hafta sonu 300 $'a çıkıyor.
  - Long swap örneği −%18,25/yıl: 90.000 $'da 1 lot için ≈ −45 $/gece, −315 $/hafta, −1.350 $/30 gün.
  - Rollover hafta sonu dahil her gün, BTCUSD'de Çarşamba üçlü swap yok.
  - Offshore kaldıraç tipik 1:5–1:10, prop firmalarda 1:2–1:5.
  — [FXNX](https://fxnx.com/en/blog/btcusd-cfd-contract-specs-lot-size-margin-weekend-swap)
- Bitget CFD: Bazen 3 günlük swap uygulanabiliyor. Hafta sonu çarpanı konusunda kaynaklar çelişiyor, broker'ın kendi spesifikasyonu esas. — [Bitget](https://www.bitget.com/support/articles/12560603840553). MT5'te swap modu (puan / taban para / yüzde) aynı görünen sayının farklı anlamlar taşımasına yol açabiliyor. Gün sayımı 360 veya 365 olabiliyor. — [MQL5 makalesi](https://www.mql5.com/en/articles/23469)
- Bybit MT5: Swap sunucu saati 00:00'ı geçen pozisyonlara uygulanıyor. — [Bybit](https://www.bybit.com/en/help-center/article/MT5-Trading-Fees-Explained)

### Inferences (hesap, kaynak rakamlarından türetilmiştir)
- Gecelik long swap: %22,5/360 ≈ **6,25 bp/gece**, %18,25/365 ≈ 5 bp/gece.
- Hafta içi spread: 20 $ / 90.000 $ ≈ **2,2 bp gidiş-dönüş**. Hafta sonu 300 $ ≈ **33 bp**.
- 21–23 UTC stratejisinin brüt getirisi (yıllık %33–40, günde bir işlem) ≈ işlem başına **8–9 bp**. Pencere rollover'ı (≈21:00/22:00 UTC) kesiyorsa swap ~6 bp ve spread ~2 bp eder. Bu durumda **net ≈ 0 veya negatif.** Rollover'dan sonra girmek (örn. sunucu 00:01 = 21:01 UTC yaz) bu maliyetin büyük kısmını kaldırabilir. Bu, broker'a özel olarak doğrulanması gereken bir çıkarım.
- Projede MT5 sunucu saati UTC+3 kaydı var (bkz. MEMORY "MT5 kutusu operasyon gerçekleri"). O durumda sunucu 00:00 = **21:00 UTC**.
- Short taraf bazı brokerlerde swap **alır** (+%7,5). Bu durum BTC'de SELL tutuşlarına yapısal bir taşıma avantajı verir ve long/short karşılaştırmasında simetriyi bozar.
- 5 dk – 1 saat ufkunda, 1 ATR'lik hedef büyüklüğüyle kıyaslandığında 2 bp spread küçük. Spread'in öldürücü olduğu yerler dakika-altı ve 1 bp civarı edge'ler, ayrıca hafta sonu.

### Gaps
- Projede kullanılacak broker'ın (kutudaki MT5) BTCUSD'si için gerçek swap ve spread zaman serisi ölçülmeli. Literatürden çıkarılamaz.
- Broker bakım pencereleri (örn. hafta sonu kısa kesintiler) için genel bir kaynak bulunamadı.

---

## 7. Halving döngüsü ve ay mevsimselliği

### Takeaway
İstatistiksel olarak anlamlı sayılamaz. Yalnızca 3–4 tamamlanmış halving döngüsü var, ay etkilerinde çoklu karşılaştırma ve çakışan pencere sorunları mevcut. Aylık ortalama tablolarında (Kasım yüksek, Eylül zayıf) çıkarımsal test yok.

### Cited Findings
- Yalnızca üç tamamlanmış halving (2012, 2016, 2020) var. Örneklem bir "yasa" için çok küçük ve hayatta kalma yanlılığı söz konusu. — [Eco3min](https://eco3min.fr/en/crypto-seasonality-cycles-signal-illusion/)
- BTC, istatistiksel olarak anlamlı mevsimsel sonuç için "çok genç". — [Rektelligence](https://rektelligence.substack.com/p/buy-bitcoin-in-november)
- Takvim ayları halving tarihleriyle hizalı değil. — [Substack](https://david06280728.substack.com/p/beware-of-calendar-month-price-predictions)
- UNWE (2025) makalesinde aktif strateji 13 çakışan pencerenin 10'unda pasifi geçiyor, alfa %5 düzeyinde anlamlı. ⚠️ Pencereler çakıştığı için bağımsız değil. — [UNWE PDF](https://www.unwe.bg/doi/FABA/2025.2/FABA.2025.2.10.pdf)
- Ortalama aylık getiriler (2010'dan bu yana): Kasım %43,74, Ekim %19,46, Eylül en zayıf. Test yok. — [Bitcoin Magazine/Nasdaq](https://www.nasdaq.com/articles/what-bitcoin-price-history-predicts-february-2025)

### Inferences
- Gün-içi bot için halving ve ay etkileri **karar katmanına alınmamalı**. Taban ve plasebo kıyasıyla bile n (döngü sayısı) çok küçük.

### Gaps
- Çoklu karşılaştırma düzeltmeli, bağımsız pencereli hakemli bir halving testi bulunamadı.

---

## Proje için sınanabilir hipotezler

### Takeaway
Literatürde **maliyet ve OOS ile hayatta kalmış** BTC gün-içi anomalisi neredeyse yok. Hipotezler bu nedenle "kanıtlanmış edge'i taşı" değil, "zayıf kanıtlı adayları projenin 6 ölçütlü kartıyla sına" mantığıyla kuruldu.

Tüm hipotezlerde ortak kurallar geçerli:
- Veri broker'ın kendi MT5 BTCUSD'si ve broker saatinden **UTC'ye çevrilmiş** (offset ölçülerek; CLAUDE.md §9).
- Geçmiş karar anı `_bars_upto.py` ile yeniden kuruluyor.
- Giriş = sinyal barından **sonraki M1 açılışı + o anki gerçek spread**. Swap, broker spesifikasyonundan ve gerçek rollover saatinden hesaplanıyor.
- Dönem bölünmesi: **Keşif ≤ 2023-12-31 · ETF-sonrası OOS 2024-01-11 → 2025-06-30 · Kör test 2025-07-01 → bugün** (kör test bir kez açılır).
- Ölçütler ve tanımlar sonuçlara bakmadan sabitlenir. Önce `docs/KAPI_KAYIT_DEFTERI.md` okunur, sonra kayıt eklenir.

Ortak "GEÇER" tanımı (G6) go-live kartından alındı:
- Kör testte ≥150 olay (seyrek hipotezlerde ≥100).
- Ort. net R > 0 **ve** bootstrap P(EV>0) ≥ %90.
- Kronolojik iki yarı ≥ 0.
- Spread ×1,5 stresinde net > 0.
- İcra farkı < ort.R/2.
- Tek-pozisyon kısıtıyla da pozitif.
- Ek olarak, ilgili hipotezde **plasebo** (rastgele zaman/eşik) dağılımında ≥ %95 yüzdelik.

### Cited Findings
- Hipotezlerin dayanağı yukarıdaki bölümlerdir: 21–23 UTC ([Quantpedia](https://quantpedia.com/the-seasonality-of-bitcoin/)), gün-içi TSMOM ([Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/)), 1–4 saat dönüşü ([LMU](https://epub.ub.uni-muenchen.de/97651/)), MAX10/MIN10 ([PwB](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)), ETF yapısı ([Kaiko](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure)), maliyetler ([Pepperstone](https://eu-assets.contentstack.com/v3/assets/bltaec35894448c7261/bltb3f65365f20ef593/6a1ebf2ab3c954c1e626efea/Pepperstone_Limited_Cost_and_Charges_-_June_2026.pdf), [FXNX](https://fxnx.com/en/blog/btcusd-cfd-contract-specs-lot-size-margin-weekend-swap)), seasonality'nin sağlamsızlığı ([Mueller 2024](https://ideas.repec.org/a/eee/finlet/v64y2024ics1544612324004598.html)), turn-of-candle çürümesi ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/)).

### Inferences (hipotez listesi)

**H1. 21–23 UTC long penceresi (1m/1h)**
- Kural: Pazartesi–Cuma, broker rollover'ından *sonraki* ilk M1 açılışında long aç, 23:00 UTC'de piyasa kapanışıyla çık. Rollover ≈21:00 UTC (yaz) / 22:00 UTC (kış) olabileceği için iki varyant ön-kayıtlıdır: (a) sabit 21:00→23:00 UTC giriş-çıkış ve swap dahil, (b) rollover+1 dk → 23:00 UTC.
- Taban: aynı günlerin rastgele 2 saatlik pencereleri (plasebo, 1000 çekiliş).
- GEÇER: G6 + kör testte plasebo yüzdeliği ≥ %95 + ETF-sonrası dönemde ort. net getiri > 0.
- Beklenti: literatür 2022–23 zayıflaması ve swap çakışması nedeniyle düşük.

**H2. Hafta sonu maliyet kapısı**
- Kural: Botun mevcut momentum/kanal-dönüş sinyallerini BTC'de üret, Cuma 21:00 – Pazar 22:00 UTC arası sinyalleri ayrı bir kol olarak ölç.
- GEÇER (kapı lehine): hafta sonu kolu net ort.R < 0 **ve** (hafta içi − hafta sonu) farkının bootstrap %90 GA'sı > 0.
- Geçerse hafta sonu girişleri bloklanır.

**H3. ETF-sonrası gün-içi TSMOM (5m)**
- Seans tanımı: 13:30–14:00 UTC ilk yarım saat (DST'ye göre ABD nakit açılışı) ve 19:30–20:00 UTC son yarım saat (ABD kapanışından bir önceki yarım saat; fixing 20–21 UTC).
- Kural: ilk-yarım-saat getirisinin işaretiyle son yarım saate gir.
- GEÇER: G6 (≥150 gün) + OOS Campbell–Thompson R²_OS > 0 + yüksek oynaklık günlerinde (ATR(1d) > 60g medyan) ort.R tüm günlerden büyük. Bu son koşul Shen ve ark.'nın yan tahmini.

**H4. Negatif şok sonrası 1–4 saatlik fade (5m/1h, "korku döner")**
- Tetik: 60 dakikalık getiri ≤ −2,5×σ, σ = önceki 30 günün 60 dakikalık getirilerinin standart sapması. Yalnızca BUY.
- Giriş tetik barından sonraki M1 açılışında. Çıkış zaman bazlı (4 saat) ve SL = 1×ATR(1h).
- Bağımsızlık için olaylar arasında ≥4 saat boşluk.
- GEÇER: G6 (≥100 bağımsız olay) + rastgele zaman plasebosunda ≥ %95 yüzdelik.

**H5. Asimetri testi (H4'ün ikiz kolu)**
- Kural: +2,5σ pozitif şok sonrası SELL fade, aynı geometriyle.
- GEÇER (asimetri var): ort.R(H4) − ort.R(H5) > 0 ve bootstrap P > %95.
- Ayrıca H5 tek başına G6'yı geçmemeli. Geçmezse "coşku dönmez" BTC'de teyit edilmiş olur.

**H6. Günlük MAX10 kırılımı, yalnız long (1d)**
- Kural: kapanış son 10 günün en yükseği → sonraki gün açılışında long. Çıkış kapanış 10 günün en düşüğüne inince ya da 20 günlük zaman sınırında.
- Maliyetler: **gerçek long swap** (bugünkü spesifikasyon oranı) ve spread ×1,5 stresi.
- Ön-kayıtlı karşılaştırmalar: Donchian 20/55 ve B&H.
- GEÇER: 2018–2026'da yıllık işlem başına net ort.R > 0, 2022 alt-döneminde B&H'den düşük düşüş, ETF-sonrası dönemde net > 0 ve iki yarı ≥ 0.
- Bu bir swing hipotezi. Olay sayısı 150'nin altında kalabilir. O durumda verdikt en fazla SHADOW olur.

**H7. VIX rejimi → BTC ertesi gün yönü (1d)**
- Kural: VIX önceki kapanış ≥18,4 (projenin NDX eşiği, değiştirilmeden) ise ertesi günün BTC long getirisini, eşik altındaki günlerin SELL getirisiyle kıyasla.
- Plasebo: eşiği [12, 30] aralığında rastgele seçmek ve VIX serisini blok-karıştırmak.
- GEÇER: rejim farkı > 0, permütasyon p < 0,05, keşif/OOS/kör üçünde de aynı işaret.
- Not: VIX yalnız NYSE günlerinde var. Hafta sonu BTC getirileri ayrıca raporlanır.

**H8. NDX açılış hareketi → BTC sonraki 2 saat (5m)**
- Kural: NDX 13:30–14:00 UTC getirisi |r| > 0,5×ATR(NDX, 5m günlük ortalama) ise BTC'de 14:00–16:00 UTC aynı yönde (öncülük) **ve** ters yönde (aşırı tepki) iki kol, ikisi de ön-kayıtlı.
- GEÇER: Bir kol G6'yı geçer ve diğer kolun işareti tutarlıdır (biri + iken diğeri −). İki kol birden "kazanıyorsa" bu bir hata belirtisidir.

**H9. CME boşluğu "dolma" (1h)**
- Boşluk tanımı: CME BTC vadelisinin Cuma kapanış saati (≈21:00 UTC) ile Pazar açılış (≈22:00/23:00 UTC) arasındaki broker BTCUSD fiyat farkı, eşik |boşluk| ≥ 0,5×ATR(1d).
- Hipotez: boşluk Pazartesi–Cuma içinde dolar.
- Plasebo: Cuma kapanışı yerine rastgele hafta-içi saat referans seviyelerinin aynı süre içinde "dolma" oranı.
- GEÇER: dolma oranı plasebodan ≥ 10 puan yüksek **ve** "boşluğa doğru fade, dolunca çık, 5 günlük zaman çıkışı" işlemi G6'yı geçer.
- Beklenti: dolma oranı yüksek ama plasebo da yüksek çıkacağı için edge muhtemelen yok.

**H10. Funding saati etkisi (1m) — öldürme testi**
- Ölçüm: 00/08/16 UTC'nin ±15 dakikalık getirisi, diğer saatlerin aynı uzunluktaki pencereleriyle kıyaslanır.
- GEÇER: 24 pencere için Bonferroni-düzeltmeli p < 0,05 **ve** ortalama |getiri| > gidiş-dönüş hafta içi spread (~2,2 bp).
- Beklenti: geçmez (kaynak yok).

**H11. Turn-of-the-candle (1m) — maliyet kalibrasyon testi**
- Kural: :00/:15/:30/:45 dakikalarının getirisi ile diğer dakikaların getirisi kıyaslanır, broker spread'i düşülür.
- GEÇER: net ort. > 0 ve G6.
- Beklenti: kesin geçmez (0,58 bp brüt < 2 bp spread, 2022'de katsayı 1/3–1/8'e düştü).
- Amaç: simülatörün maliyet modelinin "bilinen ölü edge'i öldürdüğünü" doğrulamak, yani bir sağlık kontrolü.

**H12. ETF-sonrası seans yoğunlaşması → seans kapısı tasarımı (5m, betimsel + kapı)**
- Ölçüm: günlük mutlak getirinin 13:30–21:00 UTC payı, 2022–2023 ile 2024-01-11 sonrası arasında.
- GEÇER (yapısal değişim var): pay ≥ 5 puan arttı ve blok-bootstrap %95 GA'sı > 0.
- Geçerse botun momentum scope'u BTC'de yalnız bu pencerede ve kapı olarak sınanır (G6). Asya seansı (00–07 UTC) sinyalleri ayrı kol olarak raporlanır.

### Gaps
- Hipotezlerin hiçbiri literatürde perakende CFD maliyetiyle ve 2024 sonrasıyla test edilmiş değil. Bu nedenle tümünün önsel başarı olasılığı düşük kabul edilmeli. En umut verici adaylar H4 (negatif şok fade, mekanizma + hakemli kanıt), H6 (günlük kırılım, uzun kanıt geçmişi ama swap riski) ve H3 (hakemli OOS kanıtı, ama eski örneklem).
- Kutudaki broker'ın BTCUSD geçmiş derinliği (kaç yıllık M1 var) bilinmiyor. Keşif dönemi için exchange verisi (Binance/Coinbase) gerekirse **besleme farkı** ayrıca ölçülmeli (bkz. MEMORY "Backend emtia = Yahoo vadelisi").
