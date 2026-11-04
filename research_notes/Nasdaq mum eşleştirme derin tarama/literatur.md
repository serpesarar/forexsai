# Endeks getirileri için analog / en-yakın-komşu / mum-formasyonu eşleştirme tahminleri — literatür haritası, gün-içi öngörülebilirlik ve veri-madenciliği metodolojisi (NASDAQ-100 odaklı)

> Kapsam notu: Yerel çalışma (mum-mum tolerans eşleştirme, ATR-normalize 7-mum Öklid kNN, 33-mum log-zaman piramidi, VIX/stres/seans/volatilite koşullandırma, NDX/DAX/XAU/OIL ortak eşleştirme) yönde rastgele komşu düzeyinde kaldı (≈%51,7, çoğunluk tabanı %53,3); büyüklükte saat-bazlı tipik hareket hepsini yendi. Aşağıdaki notlar bu sonucu literatürle konumlandırır ve *farklı* olup kanıtı olan yöntemlere odaklanır. Tek-hisse kesitsel sonuçlar "fikir kaynağı" olarak etiketlidir.

## 1. Endekslerde NN / analog / örüntü-tanıma tahmini test eden yayınlar: veri, ufuk, OOS sonuç, maliyet, replikasyon

### Takeaway
Endeks yönü için "geçmişte benzer fiyat örüntüsünü bul → sonraki hareketi tahmin et" yaklaşımının maliyet sonrası ve çoklu-test düzeltmeli, sağlam OOS kanıtı **yok**. Erken NN çalışmaları ya anlamsız ya da parametreye/döneme aşırı duyarlı. Lo–Mamaysky–Wang yalnızca dağılımsal "bilgi içeriği" gösterdi, işlem kârı göstermedi. Tek güçlü görsel-örüntü kanıtı (Jiang–Kelly–Xiu CNN) tek-hisse *kesitsel* ve büyük hisselerde belirgin zayıflıyor. NASDAQ-100 vadelisinde (MNQ) 2021–2025 için yapılan sistematik yanlışlama çalışması da OHLCV-tabanlı 14 sinyal ailesinin hiçbirinin geçmediğini raporluyor. Yerel "rastgele komşu düzeyi" sonucu literatürle tam uyumlu.

### Cited Findings
**Klasik en-yakın-komşu (NN) çalışmaları**
- Mizrach (1992, *Journal of Applied Econometrics* 7(S), 151–163), çok değişkenli NN, EMS döviz kurları (endeks değil): üç kurdan yalnız birinde rastgele yürüyüşü geçti; liretin günlük getirisinde MSE'de %4,5 düşüş, **istatistiksel olarak anlamsız**; çapraz-doğrulama iyileşmenin sağlam olmadığını gösterdi — [IDEAS/RePEc](https://ideas.repec.org/a/jae/japmet/v7y1992isps151-63.html)
- Fernández-Rodríguez, Sosvilla-Rivero & García-Artiles (1999), "Dancing with bulls and bears: Nearest-neighbour forecasts for the Nikkei Index", *Japan and the World Economy* 11, 395–413 (künye) — [FEDEA DT-2001-16 kaynakçası](https://documentos.fedea.net/documento/dt-2001-16/texto). Arama özetine göre Nikkei 225 (1986–1997) için NN tahminleri Theil-U ile **rastgele yürüyüşten kötü**, yalnız yön tahmininde daha iyi (ikincil özet; tablo doğrulanmadı) — [ULPGC deposu](https://accedacris.ulpgc.es/handle/10553/48010)
- Andrada-Félix, Fernández-Rodríguez, García-Artiles & Sosvilla-Rivero, "An empirical evaluation of non-linear trading rules" (çalışma kâğıdı 2001; *Studies in Nonlinear Dynamics & Econometrics* 2003): NYSE günlük verisi (eğitim 3 Ocak 1966'dan itibaren), gömme boyutu m=2,3,4, komşu sayısı k=130/140/150, filtre 0,50/0,75, tek yön maliyet %0,15 ve %0,25 → **18 parametre hücresi**; NN kuralı yalnız yükseliş trendli 1998–1999'da al-tut'u geçti, 2000'de eşit getiri / al-tut daha yüksek Sharpe; hücreler arasında işaret değişiyor (ör. 1998, m=2, filtre 0,75: −0,06 ile −0,10 arası fazla getiri) — [FEDEA DT-2001-16 tam metin](https://documentos.fedea.net/documento/dt-2001-16/texto)
- Aynı çalışmanın 2003 yayımlanmış hâli 1997–2002 NYSE'de maliyet sonrası üstünlüğü 2000 ve 2001 **hariç** raporluyor; 2004–05 çalışma kâğıdı ise tüm yıllarda üstünlük diyor → aynı yazarların versiyonları arasında sonuçlar değişiyor (çoklu-test düzeltmesi yok) — [ULPGC deposu](https://accedacris.ulpgc.es/handle/10553/48010); [FEDEA DT-2002-05](https://documentos.fedea.net/documento/dt-2002-05/texto)
- Clyde & Osler (1997) NN tahmin tekniğini grafik formasyon yöntemlerinin (omuz-baş-omuz, bayrak, flama vb.) bir genellemesi olarak gösterdi (yukarıdaki çalışmanın motivasyonu) — [FEDEA DT-2001-16](https://documentos.fedea.net/documento/dt-2001-16/texto)

**Kernel-regresyon ile otomatik formasyon tanıma**
- Lo, Mamaysky & Wang (2000, *Journal of Finance* 55, 1705–1765): kernel regresyonla formasyon (omuz-baş-omuz vb.) tanıma, ABD hisseleri 1962–1996; formasyon sonrası günlük getiri dağılımı koşulsuz dağılımla karşılaştırıldı; "birkaç gösterge artımsal bilgi sağlıyor" — **işlem kârı/maliyet testi değil**, tek-hisse — [MIT sayfası](https://web.mit.edu/Alo/www/Papers/techanal.html); [NBER w7613](https://www.nber.org/papers/w7613)
- Savin, Weller & Zvingelis (2007, *Journal of Financial Econometrics* 5(2), 243–265): LMW algoritmasının değiştirilmiş hâli, S&P 500 ve Russell 2000 hisseleri 1990–1999; omuz-baş-omuz koşullu stratejide riske göre düzeltilmiş fazla getiri yılda %5–7; başarının bir kısmı **negatif momentumlu hisseleri seçmesinden** geliyor (yani formasyon kısmen bilinen bir faktörü yeniden keşfediyor) — [Iowa PDF](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf); [Iowa kaydı](https://iro.uiowa.edu/esploro/outputs/journalArticle/The-Predictive-Power-of-Head-and-Shoulders-Price/9984963212902771)
- Chong & Poon, LMW ve SWZ algoritmalarının formasyonun trend içindeki göreli konumunu yok saydığını savunup filtre öneriyor — [MPRA 60825](https://mpra.ub.uni-muenchen.de/60825/1/MPRA_paper_60825.pdf)

**Görüntü tabanlı derin öğrenme (fikir kaynağı — tek-hisse kesitsel)**
- Jiang, Kelly & Xiu (2023, *Journal of Finance* 78(6), 3193–3249, DOI 10.1111/jofi.13268): hisse fiyat grafiklerinin görüntüsünden CNN ile getiri yönü olasılığı; özete göre görüntü-tabanlı desil spread'leri OOS **brüt** yıllık Sharpe eşit-ağırlıkta 7,2'ye, değer-ağırlıkta 1,7'ye kadar; en yakın rakipler TREND ve haftalık kısa-vade reversal (WSTR) 2,9 / 2,8 — [Yale PDF](https://economics.yale.edu/sites/default/files/2023-11/The%20Journal%20of%20Finance%20-%202023%20-%20JIANG%20-%20Re%25E2%2580%2590%20Imag%20in%20ing%20Price%20Trends_0.pdf); [SSRN 3756587](https://papers.ssrn.com/abstract=3756587)
- İkincil özet: eğitim 1993–2000, OOS 2001–2019; 5/20/60 günlük görüntü modelleri için EW Sharpe 7,2 / 6,8 / 4,9; evren en büyük 500 hisseye daraltılınca Sharpe "1'in biraz üzeri"ne düşüyor — [BSIC özeti](https://bsic.it/technical-analysis-on-steroids/)
- Öğrenilen örüntüler bilinen trend sinyallerinden büyük ölçüde farklı; kısa ölçekte öğrenilen örüntü uzun ölçekte de çalışıyor, ABD'de öğrenilen uluslararası piyasalarda da tahmin ediyor (bağlamdan bağımsızlık iddiası) — [Yale Economics](https://economics.yale.edu/research/re-imagining-price-trends); [HKUST seminer özeti](https://calendar.hkust.edu.hk/node/33183)

**Matrix profile / motif keşfi ve DTW**
- Finansta matrix profile uygulamaları (Cartwright, Crane & Ruskin, DCU) benzer davranış dönemlerini/motifleri *tanımlıyor* (S&P 500 dahil), tahmin doğruluğu raporlamıyor — [DCU DORAS](https://doras.dcu.ie/30047/1/Obtaining%20quantitative%20information%20from%20time%20series%20patterns.pdf)
- Uygulayıcı kaynak: piyasalarda tesadüfi yakın-tekrar çok fazladır; bir motifin tekrar etmesi tahmin değeri olduğunu göstermez, aynı OOS disiplini gerekir — [LuxAlgo Matrix Profile](https://www.luxalgo.com/library/concept/matrix-profile.md)

**NASDAQ-100 vadelisinde doğrudan yanlışlama (hakemsiz ön baskı)**
- Mesfin (arXiv 2605.04004, v1 Mayıs 2026, v3 Eylül 2026): MNQ 5 dk barlar, 947 işlem günü (2021–2025), genişleyen pencere walk-forward, 14 OHLCV sinyal ailesi; geçme ölçütleri: OOS net-getiri t ≥ 2,0, kat başına ≥30 işlem, sürtünme sonrası pozitif, 2023/2024/2025'te aynı yön, permütasyon p < 0,001. **Hiçbiri geçmedi**; 11 ailenin brüt getirisi 0,07–1,50 puan, 2,0 puanlık sürtünme tabanının altında; Opening Range Breakout (long) t=0,88; gap devamı (short) brüt +16,53 puan, t=1,46 ama yıl-kararsız. Pozitif kontroller (RTH Confluence t=3,11; London Session Signal B t=4,30) yöntemin gerçek kenarı yakalayabildiğini göstermek için — [arXiv 2605.04004](https://arxiv.org/abs/2605.04004)

**Bayrak formasyonu (yazar iddiası)**
- Arévalo, García, Guijarro & Peris (2017, *Expert Systems with Applications* 81, 177–192): DJIA'da dinamik bayrak-formasyonu kuralının önceki bayrak stratejilerinden üstün olduğu iddiası (yazarların kendi iddiası; veri-madenciliği düzeltmesi raporlanmamış) — [datalearner kaydı](https://datalearner.com/academic/journal-papers/0957-4174/volumes-and-issues/285/paper-detail/13687); DAX/DJIA/IBEX üzerinde UPV tezi al-tut'tan yüksek risk-düzeltilmiş getiri bildiriyor — [UPV RiuNet](https://riunet.upv.es/handle/10251/102317)

### Inferences
- NN literatürünün ortak deseni: (i) tek veya az sayıda kısa OOS yılı, (ii) birden çok parametre hücresi (m, k, filtre) raporlanıp en iyisinin "önerilen" seçilmesi, (iii) White/Hansen tipi çoklu-test düzeltmesi yok. Yerel çalışmadaki "rastgele komşu plasebosu" bu literatürün çoğundan daha sıkı bir test; bu yüzden yerel negatif sonuç literatürdeki pozitif NN sonuçlarıyla çelişmiyor, onları büyük olasılıkla açıklıyor.
- Yön isabetinin (%51,7) çoğunluk tabanının (%53,3) **altında** olması, kNN'nin "her zaman yukarı" kuralından kötü olduğunu gösterir. Literatürde (GHLZ, Baltussen vd.) standart karşılaştırma ölçüsü Campbell–Thompson OOS R²'dir (tahmin vs. genişleyen tarihsel ortalama); yerel değerlendirme bu ölçüye de çevrilmeli.
- Savin vd.'nin "kârın kaynağı negatif momentum" bulgusu ve JKX'nin "en yakın rakip WSTR/TREND" bulgusu, başarılı görünen örüntü yöntemlerinin çoğunlukla bilinen basit faktörleri (momentum/reversal) yeniden keşfettiğini düşündürür → yeni bir eşleştirme yöntemi test edilirken basit momentum/reversal ve saat-bazlı drift **taban model** olarak her zaman yan yana konmalı.
- JKX kesitsel bir sıralama sorunudur (hangi hisse diğerlerinden iyi); tek bir endeksin zaman serisi yönünü tahmin etmek farklı ve çok daha zor bir problemdir (bağımsız gözlem sayısı çok daha az). Büyük-500 hissede Sharpe'ın ~1'e inmesi NDX gibi mega-cap endekste beklentiyi daha da düşürür.
- Mesfin'in MNQ bulgusu (11 ailede brüt hareket < sürtünme) NASDAQ CFD'si için de geçerli olması beklenen yapısal bir sınırı işaret ediyor: 5 dk OHLCV sinyallerinin brüt beklentisi işlem başına birkaç puanın altında ise spread tek başına öldürür. Hakemsiz ve tek yazarlı olduğu için yöntemi (pozitif kontroller, 5 ölçüt) ilham olarak, sayıları dikkatle kullanmak gerekir.

### Gaps
- DTW (dynamic time warping) tabanlı analog tahminin ABD endekslerinde maliyet sonrası OOS değerlendirmesini yapan güvenilir bir hakemli kaynak bulunamadı; bulunanlar düşük kaliteli konferans/dergi çalışmaları gibi görünüyor (doğrulanmadı).
- Matrix-profile motiflerinin endeks getirisi *tahmini* için titiz OOS testi bulunamadı.
- Leigh ve ark. "bull flag" şablon-eşleştirme çalışmaları (NYSE Composite) aramada bulunamadı; içerik doğrulanamadı.
- "Dancing with bulls and bears" Nikkei sonuçlarının sayısal tabloları doğrudan okunmadı (ikincil özet).
- JKX'nin 5/20/60 gün Sharpe değerleri ve büyük-hisse sonuçları ikincil kaynaktan (BSIC); orijinal tablolar okunmadı. CNN'in endeks zaman serisine uygulandığı hakemli bir replikasyon bulunamadı.

## 2. Belgelenmiş ve replike edilmiş gün-içi / kısa-vade endeks öngörülebilirliği (tanımlar, etki büyüklükleri, dönem, sonraki teyit/çürüme)

### Takeaway
Endeks düzeyinde en sağlam belgelenen dört düzenlilik: (1) **piyasa gün-içi momentumu** — günün geri kalanının (önceki kapanıştan kapanışa 30 dk kalana) getirisi son 30 dakikayı öngörür (iki JFE makalesi, 60+ vadeli, 1974–2020, 16 gelişmiş piyasa; etki opsiyon piyasa yapıcılarının negatif gamma'sında yoğunlaşıyor, 2 gün içinde geri dönüyor); (2) **günlük endeks getirisinde 2000'lerden beri negatif seri bağımlılık** (endeks ürünlerinin yükselişiyle); (3) **gece kayması (overnight drift)** — ABD endeks getirisi Avrupa açılış saatlerinde pozitif, özellikle satış günlerinden sonra; (4) **gün-içi volatilite mevsimselliği** (U-şekli). Çürüme işaretleri var: pre-FOMC kayması 2015 sonrası kayboldu, GHLZ'nin 2013 sonrası zayıfladığına dair ikincil iddia var, COVID şokunda son yarım saat etkisi anlamsızlaştı.

### Cited Findings
**Piyasa gün-içi momentumu — Gao, Han, Li & Zhou (GHLZ, 2018, JFE 129, 394–414)**
- Veri: SPY, 1 Şubat 1993 – 31 Aralık 2013 (erken taslak 1999–2012). r1 = önceki kapanıştan 10:00 ET'ye (gece dahil ilk yarım saat), r12 = 15:00–15:30, r13 = 15:30–16:00 — [WUSTL kaydı](https://profiles.wustl.edu/en/publications/market-intraday-momentum/); [çalışma kâğıdı PDF](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Çalışma kâğıdı sayıları: r1 → r13 eğim (×100) 6,94, %1 düzeyinde anlamlı, R² %1,6; r12 tek başına R² %1,1; ikisi birlikte R² %2,6. **OOS R²** (Campbell–Thompson, tarihsel ortalamaya karşı): r1 %1,2, r12 %0,7, ikisi %1,8; 2004 sonrası başlatılınca %2,08 / %1,19 / %3,18 — [çalışma kâğıdı PDF](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Koşullu güç: ilk yarım saat volatilitesi düşükken R² %0,6 (r1 katsayısı anlamsız), orta %1,0, yüksekken %3,3; hacim düşük/orta/yüksek → R² %1,1 / %2,3 / %3,1; resesyon ve büyük makro haber günlerinde daha güçlü — aynı kaynak
- Zamanlama stratejisi (r1 işaretiyle son yarım saat al/sat): yıllık ort. %6,67, std %6,19, **Sharpe 1,08**; "her zaman long son yarım saat" Sharpe −0,18, al-tut Sharpe 0,29; başarı oranı %54,37 (her zaman long %50,42); r1 ve r12 aynı işaretliyse işlem → ort. getiri %4,39'a düşüyor ama başarı oranı %77,05 — aynı kaynak
- Maliyet: ondalık fiyatlama (Temmuz 2001) sonrası alt dönemde maliyet ortalama getiriyi 1,22 puan düşürüp %4,30'a indiriyor; başka bir senaryoda %7,96 → %6,52; komisyon ihmal edilmiş — aynı kaynak
- Kapsam: diğer 10 likit ETF'de r1'in öngörü gücü %1 düzeyinde anlamlı; FTSE 100 ve Euro Stoxx 50 vadelilerinde de var (2003–2015); döviz ve emtia vadelilerinde **yok**; S&P 500'de ETF yerine vadeli kullanmak benzer sonuç veriyor — aynı kaynak

**Hedging demand — Baltussen, Da, Lammers & Martens (2021, JFE 142, 377–403)**
- 60+ vadeli (hisse endeksi, tahvil, emtia, döviz), Aralık 1974 – Mayıs 2020; öngörücü rROD = önceki kapanıştan kapanışa 30 dk kalana kadarki getiri, hedef rLH = son 30 dk; "her yerde" güçlü gün-içi momentum; varlık sınıfı düzeyinde yıllık Sharpe 0,87–1,73 (maliyetsiz) — [Notre Dame PDF](https://www3.nd.edu/~zda/intramom.pdf); [EUR Pure](https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/)
- rROD, GHLZ'nin rONFH'sini (ilk yarım saat) yeniyor: hisse vadelilerinde rROD t=7,29 ve en yüksek havuzlanmış OOS R² %2,88; 17 hisse endeksi vadelisinin 14'ünde OOS R² pozitif ve anlamlı; etki 1974–1999 ve 2000–2020 alt dönemlerinin ikisinde de var — [Notre Dame PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Mekanizma: S&P 500 opsiyon piyasa yapıcılarının net gamma maruziyeti (NGE) negatifken momentum çok daha güçlü; **NGE pozitif günlerde anlamlı gün-içi momentum yok**; SqueezeMetrics hesapları OptionMetrics ile 2002–2017'de doğrulanmış; kaldıraçlı ETF yeniden dengelemesi de katkı veriyor — aynı kaynak
- Getiri hisse ve emtia vadelilerinde **iki gün içinde** geri dönüyor (bilgi değil fiyat baskısı imzası) — aynı kaynak
- Maliyet: makale maliyeti hesaba katmıyor, ancak S&P 500 vadelisinde işlem başına bir tick maliyet varsayımıyla net Sharpe pozitif kalıyor — aynı kaynak

**Bağımsız teyit ve zayıflama işaretleri**
- Li, Sakkas & Urquhart (2022, *Journal of Financial Markets* 57, 100619): 16 gelişmiş piyasa, ilk yarım saat (gece dahil) → son yarım saat 16'nın 12'sinde anlamlı; çoğu ülkede örneklem içi ve dışı ekonomik olarak büyük; düşük likidite, yüksek volatilite ve kesikli bilgi gelişinde daha güçlü — [IDEAS](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html); [Nottingham deposu](https://nottingham-repository.worktribe.com/output/5273197)
- Asya-Pasifik piyasalarında etki ABD kadar yaygın değil — [IDEAS (Pacific-Basin Finance Journal 65)](https://ideas.repec.org/a/eee/pacfin/v65y2021ics0927538x21000068.html)
- Bir tez, "Rosa"nın 2013 sonrası veride öngörülebilirlikte düşüş raporladığını aktarıyor (orijinal çalışma okunamadı; ikincil) — [St. Gallen Alexandria](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- COVID-19 şoku sırasında S&P 500 ve CSI 300'de son yarım saat gün-içi momentum üzerinde anlamlı etki göstermedi (kriz alt dönemi) — [TUL dspace](https://dspace.tul.cz/items/669afa97-267f-429d-bbf5-b78e0abd0c7c/full)
- Zarattini, Aziz & Barbon (2024, SFI Research Paper 24-97, hakemsiz): "noise area" sınırlarıyla gün içinde erken giriş + dinamik trailing stop, SPY 2007–2024 başı: toplam %1.985 (maliyet sonrası), yıllık %19,6, Sharpe 1,33; volatilite rejimi, dealer gamma dengesizliği, haftanın günü ve komisyon/kayma etkisi inceleniyor — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy); [Concretum özeti](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- MNQ 2021–2025 yanlışlama çalışmasında Opening Range Breakout (long) t=0,88 ile geçemedi — [arXiv 2605.04004](https://arxiv.org/abs/2605.04004)

**Günlük endeks getirisinde negatif seri bağımlılık — Baltussen, van Bekkum & Da (2019, JFE 132, 26–48)**
- 15 ülkede 20 büyük endeks: seri bağımlılık 1990'lara kadar pozitif, **2000'lerden beri negatif**; istatistiksel ve ekonomik olarak anlamlı; endeks ürünlerinin (vadeli, ETF, endeks fonu) yaygınlaşmasıyla bağlantılı, zaman trendiyle açıklanmıyor; Nikkei 225 ağırlıkları ve S&P 500 üyeliği testleriyle teyitli — [Notre Dame PDF](https://www3.nd.edu/~zda/Indexing.pdf); [EUR Pure](https://pure.eur.nl/en/publications/indexing-and-stock-market-serial-dependence-around-the-world/)
- Ölçü MAC(5): birkaç gecikmedeki otokorelasyonların ağırlıklı ortalaması; MAC(5)'e karşı işlem yapan strateji 2 Mart 1999 sonrası tüm endekslerle yıllık Sharpe 0,63, **yalnız S&P 500 ile 0,67**; likit endeks vadelilerinde otokovaryansa dayalı kârlar negatif (−0,05) ve işlem maliyetlerini aşıyor (seminer versiyonu) — [CXO Advisory özeti](https://www.cxoadvisory.com/technical-trading/effect-of-tracking-products-on-short-term-equity-index-trendingreversal); [EUR repub](https://repub.eur.nl/pub/113320)
- Uygulayıcı notu: basit kapanıştan-kapanışa reversal fikrinin son dönemde kenarını kaybetme eğiliminde olduğu belirtiliyor (blog; düşük kanıt kalitesi) — [Quantreturns](https://quantreturns.substack.com/p/overnight-mean-reversion)

**Gece kayması ve gece/gündüz ayrışması**
- Boyarchenko, Larsen & Whelan, "The Overnight Drift" (NY Fed Staff Report 917, Şubat 2020, rev. Ağustos 2022): ABD hisse getirileri **Avrupa piyasalarının açılış saatlerinde** büyük ve pozitif; önceki ABD seansının kapanışındaki emir dengesizlikleriyle güçlü ilişkili; satış günlerinden sonra güçlü pozitif gece reversal'ı, ralliler sonrası çok daha zayıf (asimetri, zamanla değişen dealer risk taşıma kapasitesiyle açıklanıyor) — [NY Fed SR917](https://www.newyorkfed.org/research/staff_reports/sr917)
- Vadeli piyasada piyasa yapıcılar likidite sağlamaya zorunlu olmadığından gün-içi fiyat baskısı negatifken risk taşıma kapasitesi çok daha küçük (ikincil özet) — [BSIC](https://bsic.it/the-overnight-puzzle/)
- Lou, Polk & Skouras ("A Tug of War"): firma düzeyinde gece ve gün-içi getirilerde kendi içinde güçlü süreklilik, dönemler arası dengeleyici reversal (tek-hisse; fikir kaynağı) — [LSE PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)

**Aynı-saat sürekliliği (fikir kaynağı — tek-hisse kesitsel)**
- Heston, Korajczyk & Sadka (2010, JF 65(4), 1369–1407): gün 13 yarım saate bölünüyor; gün içinde yakın aralıklarla negatif ilişki (bid-ask sıçraması, <1 saatlik likidite dengesizliği), ama **tam gün katlarındaki gecikmelerde (13, 26, 39 …) pozitif süreklilik**, en az 40 işlem günü sürüyor; ilk ve son yarım saatte daha belirgin; hacim/emir dengesizliği/volatilite benzer desen gösterse de getiri desenini açıklamıyor — [Houston PDF](https://www.bauer.uh.edu/departments/finance/documents/Heston_Korajczyk_Sadka_paper_UH.pdf); [ar5iv](https://ar5iv.arxiv.org/html/1005.3535)
- 2024 replikasyonu: İngiltere ve Brezilya hisselerinde desen var, Çin'de zayıf — [Aston](https://publications.aston.ac.uk/id/eprint/46518)

**Takvim/olay kaynaklı ve çürüyen etki**
- Lucca & Moench (2015) planlı FOMC toplantıları öncesinde Eylül 1994 – Mart 2011 arasında büyük ortalama fazla getiri buldu; Kurov, Wolfe & Gilbert (2021, *Finance Research Letters* 40) örneklemi Aralık 2019'a uzatınca pre-FOMC kaymasının **2015 sonrası esasen kaybolduğunu** (basın toplantılı ve toplantısız duyurularda) gösterdi — [IDEAS](https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html)

**Volatilite mevsimselliği (büyüklük için)**
- Andersen & Bollerslev (1997, *Journal of Empirical Finance* 4, 115–158): döviz ve hisse piyasalarında yaygın gün-içi volatilite periyodikliği; gün-içi volatilite dinamiğini tanımlamadan önce periyodikliğin modellenmesi gerekli — [IDEAS](https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html); S&P 500'de mutlak 5 dk getirilerle U-şekli (ikincil aktarım) — [arXiv 2310.19992](https://arxiv.org/pdf/2310.19992)

**Yayın sonrası çürüme (genel)**
- McLean & Pontiff (2016, JF): 97 kesitsel öngörücüde portföy getirileri örneklem dışında %26, yayın sonrası **%58** daha düşük — [PDF](https://Www.Gwern.net/doc/economics/2016-mclean.pdf)

### Inferences
- Gün-içi momentum, yerel yöntemlerden **yapısal olarak farklı**: şekil eşleştirmiyor; saat-sabitli tek bir kümülatif getiriyi (rROD) belirli bir saat penceresine (son 30 dk) bağlıyor ve arkasında ölçülmüş bir akış mekanizması (gamma hedging, kaldıraçlı ETF yeniden dengelemesi, geç bilgili işlem) var. Bu, yerel bulgunun "saat-bazlı tipik hareket kazanır" sonucuyla uyumlu: endekste öngörülebilirlik *saat yapısında*, şekil benzerliğinde değil.
- Etki büyüklükleri küçük (OOS R² %1–3) ama 30 dakikalık ufuk için ekonomik olarak anlamlı; mekanizma NGE>0 günlerde kaybolduğundan, koşulsuz test gücü düşük kalabilir. NDX'te QQQ/NQ opsiyonlarının gamma'sı S&P'den farklı olabilir; varsayım olarak taşınmamalı, ölçülmeli.
- Negatif günlük seri bağımlılık (Baltussen vd. 2019) ile gün-içi momentumun 2 gün içinde geri dönmesi (Baltussen vd. 2021) aynı resmin iki yüzü: gün içinde akış kaynaklı devam, günler arasında geri dönüş. 1 günlük ufuk için doğal aday "reversal", 30 dk–1 saat ufku için "son yarım saat momentumu".
- Gece kayması, NAS100 CFD'nin 24 saat işlem görmesi sayesinde doğrudan test edilebilir — ancak CFD'de gecelik finansman (swap) maliyeti ve broker rollover saati eklenmeli.
- Post-yayın çürümesi (pre-FOMC'nin tamamen kaybolması, McLean–Pontiff %58) göz önüne alınınca, yayımlanmış etki büyüklükleri yarıya indirilmiş beklentiyle ön-kayıt edilmeli; 2021–2026 NDX verisi bu etkiler için doğal bir "yayın sonrası" test dönemidir.

### Gaps
- GHLZ sayıları çalışma kâğıdı versiyonundan alındı; yayımlanmış JFE tablolarıyla birebir karşılaştırılmadı. GHLZ'nin 11 ETF'i arasında QQQ'nun ve Baltussen vd.'nin 17 hisse vadelisi arasında NASDAQ-100 vadelisinin olup olmadığı doğrulanmadı.
- "Rosa" 2013 sonrası düşüş çalışması okunamadı; GHLZ'nin S&P 500'de yayın sonrası doğrudan, hakemli replikasyonu bulunamadı.
- Gece kaymasının kesin saat penceresi (ET), enstrüman ve büyüklüğü NY Fed sayfasından doğrulanamadı (PDF okunmadı).
- MAC(5)'in tam ağırlık şeması ve "MAC(5)'e karşı işlem" kuralının tam tanımı doğrulanmadı.
- Lucca–Moench'in orijinal etki büyüklüğü (baz puan) ve pencere tanımı doğrulanamadı (Skidmore PDF 404).
- Açılış aralığı (opening range) stratejilerinin hakemli endeks-vadeli kanıtı aranmadı/bulunamadı; tek veri noktası MNQ ön baskısı (negatif).

## 3. Endekslerde mum-formasyonu çalışmaları: maliyet ve veri-madenciliği düzeltmesinden sonra bir şey kalıyor mu?

### Takeaway
Hayır, kayda değer bir şey kalmıyor. Tek güçlü pozitif sonuç Caginalp & Laurent'in (1998) 1992–1996 S&P 500 hisselerindeki üç-günlük reversal formasyonları; aynı döneme yakın DJIA hisselerinde (1992–2002) Marshall–Young–Rose hiçbir değer bulmadı, DAX/Bund vadelilerinde gün-içi mumlar maliyetsiz bile rastgele işlemlerden iyi değil, 5 dk DJIA hisselerinde veri-madenciliği + maliyet düzeltmesinden sonra hiçbir kural kalmıyor. Sonuçlar tutma kuralı seçimine duyarlı — bu da "çatallanan yollar" sorununun işareti.

### Cited Findings
- Caginalp & Laurent (1998, *Applied Mathematical Finance*): tüm S&P 500 hisselerinin 1992–1996 günlük OHLC'si; büyüklük koşulları kaldırılmış standart üç-günlük mum tanımları (ör. three white soldiers / three black crows); OOS testlerde sıfır hipotezinden 36 standart sapma, iki günlük tutmada yaklaşık %1 kâr — [PDF (forum aynası)](https://c.mql5.com/forextsd/forum/210/The%20Predictive%20Power%20of%20Price%20Patterns.pdf); [Taylor & Francis DOI](https://informahealthcare.com/doi/abs/10.1080/135048698334637)
- Marshall (2005 doktora tezi; Marshall, Young & Rose 2006 makalesinin temeli): DJIA bileşenleri 1992–2002, rastgele OHLC üreten genişletilmiş bootstrap; mum teknik analizinin değeri yok, mum takipçisi piyasayı geçmiyor — [Massey Research Online](https://mro.massey.ac.nz/handle/10179/1604)
- 28 sinyal, 10 günlük tutma: yükseliş sinyallerinden sonra getiriler yarıdan az sıklıkla pozitif; bir yükseliş sinyali güvenilir şekilde *negatif* getiri öngörüyor — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/candlesticks-fiddlesticks/)
- Fock, Klein & Zwergel (2005, *Journal of Derivatives*): DAX ve Bund vadelileri gün-içi, 2002–2003, bilgisayarla nesnel mum tanımı; sonuçlar **maliyetsiz bile** zayıf, çoğu durumda rastgele işlem benchmark'ından anlamlı olarak iyi değil; tek başına veya momentum gibi göstergelerle birlikte öngörü gücü yok — [Augsburg OPUS](https://opus.bibliothek.uni-augsburg.de/opus4/frontdoor/index/index/year/2017/docId/35176); [Kassel kaydı](https://forschung.uni-kassel.de/converis/portal/detail/Publication/2462413)
- Duvinage, Mazza & Petitjean (2013): 5 dk DJIA hisseleri; mum kurallarının yaklaşık üçte biri muhafazakâr Bonferroni düzeyinde al-tut'u geçiyor, ancak veri-madenciliği düzeltmesi ve işlem maliyeti sonrası **üstünlük kanıtı yok** — [UCLouvain DIAL](https://dial.uclouvain.be/pr/boreal/en/object/boreal%3A136070/datastream/PDF_02/view)
- 2014 çalışma kâğıdı: tutma kuralı belirleyici — üç-günlük reversal + Caginalp–Laurent tutma kuralı %0,5 maliyette kârlı, aynı formasyonlar Marshall–Young–Rose tutma kuralıyla kârsız — [IDEAS (SIN WP 14-A010)](https://ideas.repec.org/p/sin/wpaper/14-a010.html)
- Tayland (2017): yükseliş/düşüş reversal mumlarının çoğunun ortalama getirisi sıfırdan farklı değil — [SAGE Open](https://journals.sagepub.com/doi/10.1177/2158244017736799); JSE (2021, C–L yöntemi): sekiz formasyondan yalnız "Three Outside Down" öngörü gücü gösteriyor — [UCT OpenUCT](https://open.uct.ac.za/handle/11427/35958)
- Gün-içi mum sinyallerinin değeri tahminden çok **icra zamanlaması** olabilir: sinyal anında tam emir gönderildiğinde işlem maliyeti daha düşük — [AUT AFM 2012-039](https://acfr.aut.ac.nz/__data/assets/pdf_file/0013/30064/AFM_2012_039.pdf)

### Inferences
- Yerel "mum-mum tolerans eşleştirmesi" mum formasyonu literatürünün kesintisiz bir genellemesi (her mumun gövde/fitil oranlarının eşleşmesi); bu literatürün negatif sonuçları yerel sonucu doğrular. Caginalp–Laurent'in tek pozitif sonucu (1992–96, tek-hisse, iki günlük tutma) ile 5 dk–1 saatlik NDX tahmini arasında hem ufuk hem enstrüman uçurumu var.
- "Tutma kuralına göre sonuç değişiyor" bulgusu, her (formasyon × tutma × tolerans) kombinasyonunun ayrı bir deneme sayılması gerektiğini gösterir (bkz. 4. bölüm, N sayımı).
- Mumları tahmin aracı değil, ancak başka bir kaynaktan gelen sinyalin **giriş zamanlaması** için kullanmak (AUT bulgusu) maliyetle sınırlı bir kazanım sağlayabilir; bu da bir kenar değil, sürtünme azaltımıdır.

### Gaps
- Lu, Shiu & Liu (Tayvan) ve Marshall–Young–Cahan (Japonya) çalışmaları bu turda doğrulanmadı.
- Marshall, Young & Rose (2006, *Journal of Banking & Finance*) yayımlanmış makalesine doğrudan erişilmedi; özet tez ve CXO üzerinden.
- ABD endeks vadelilerinde (ES/NQ) gün-içi mum formasyonu üzerine hakemli, maliyet ve veri-madenciliği düzeltmeli bir çalışma bulunamadı.

## 4. Metodoloji: çok sayıda konfigürasyon aranırken kendini kandırmamak (RC, SPA, Romano–Wolf, STW, PBO, DSR, t>3)

### Takeaway
Literatürün ortak reçetesi: denenen **her** konfigürasyonu (atılanlar dahil) say; "en iyi kural"ı tüm evrene karşı bootstrap ile sına (White RC → Hansen SPA → stepwise SPA/Romano–Wolf); seçimin kendisinin kalıcı olup olmadığını sına (persistence / PBO); Sharpe'ı deneme sayısına ve kalın kuyruklara göre deflate et (DSR); yeni bulgu için t>3 çıtası kullan; maliyeti en baştan dahil et; dokunulmamış son dönemi bir kez kullan. Teknik kurallar üzerindeki en büyük testler (100+ yıl DJIA) bu düzeltmelerden sonra yakın dönem ve maliyet sonrası kâr bulamadı.

### Cited Findings
- Sullivan, Timmermann & White (1999, JF 54(5), 1647–1691): White'ın Reality Check bootstrap'ı ile Brock–Lakonishok–LeBaron'un 26 kuralını genişletilmiş evrene (7.846 kural) taşıdılar, 100 yıllık DJIA günlük verisi; maliyet öncesi 100 yıllık örneklemde en iyi kural veri-madenciliği sonrası bile üstün görünüyor — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/119144); [FMG DP 303](https://www.fmg.ac.uk/sites/default/files/2020-11/dp303.pdf)
- İkincil aktarım: sonraki 10 yılda (1987–1996) en iyi kuralın getirisi yılda %8,63 ve **istatistiksel olarak anlamsız** (maliyet öncesi); başka bir özet DJIA, S&P 500 ve S&P 500 vadelisi için anlamlı kârlı kural bulunmadığını belirtiyor — [EFMA 2008 Bajgrowicz](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2008-Athens/papers/Bajgrowicz.pdf); [Martin Sewell veri-madenciliği sayfası](https://data-snooping.martinsewell.com/)
- Hansen (2005, *Journal of Business & Economic Statistics* 23(4), 365–380), SPA testi: en iyi modelin benchmark'tan iyi olup olmadığını sınar; White RC'ye göre gücü iyileştirilmiş — [arch dokümantasyonu](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html); [Hansen & Lunde replikasyon vinyeti](https://archive.linux.duke.edu/cran/web/packages/forecastdom/vignettes/hl2005-spa-garch.html)
- Romano & Wolf (2005, *Econometrica* 73(4), 1237–1282): adım adım (stepwise) çoklu test, aile-bazlı hata oranını (FWER) asimptotik kontrol eder, tek adımlı yöntemlerden güçlü, test istatistiklerinin bağımlılık yapısını örtük yakalar; SPA tek bir evet/hayır verirken stepwise yöntem *hangi* modellerin üstün olduğunu döndürür — [Econometrica](https://jstor.econometricsociety.org/publications/econometrica/2005/07/01/stepwise-multiple-testing-formalized-data-snooping); [UPF WP 712](https://econ-papers.upf.edu/papers/712.pdf); [arch dokümantasyonu](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html)
- Hsu, Hsu & Kuan (2010, *Journal of Empirical Finance* 17(3), 471–484): stepwise SPA (Romano–Wolf stepwise RC'den güçlü); 16.000+ kural, 3 ABD ve 6 gelişen piyasa endeksi + ETF'leri; teknik kurallar anlamlı öngörü gücü gösteriyor ama **ETF'ler piyasaya girdikten sonra kanıt zayıflıyor** — [HKU deposu](https://repository.hku.hk/handle/10722/141768); [arXiv 1504.06397 (atıf)](https://arxiv.org/pdf/1504.06397)
- Bajgrowicz & Scaillet (2012, JFE 106(3), 473–491): DJIA 1897–2011, False Discovery Rate (FDR) ile veri-madenciliği kontrolü; **kalıcılık testleri**: daha güçlü FDR ile bile yatırımcı gelecekte en iyi olacak kuralları önceden seçemezdi; örneklem içi performans bile düşük işlem maliyetiyle tamamen siliniyor — [IDEAS](https://ideas.repec.org:443/a/eee/jfinec/v106y2012i3p473-491.html); [UNIGE arşivi](https://archive-ouverte.unige.ch/unige:79889)
- Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting" (*Journal of Computational Finance* 20(4), 2017): hold-out ve benzeri teknikler yatırım backtest'lerinde güvenilmez; model-bağımsız, parametrik olmayan **CSCV** (combinatorially symmetric cross-validation) ile PBO tahmini; R paketi `pbo` mevcut — [SSRN 2326253](https://papers.ssrn.com/abstract=2326253); [eScholarship](https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf); [CRAN pbo](https://packages.oit.ncsu.edu/cran/web/packages/pbo/readme/README.html)
- Minimum Backtest Length örneği: yalnız 5 yıllık günlük veri varsa bir stratejinin 45'ten fazla varyasyonu denenmemeli; aksi hâlde salt şansla Sharpe ≥ 1,0 bulunması olası — [CXO Advisory özeti](https://www.cxoadvisory.com/big-ideas/insidiousness-of-overfitting-investment-strategies-via-iterative-backtests); [Bailey/Borwein PDF](https://carmamaths.org/jon/backtest2.pdf)
- Deflated Sharpe Ratio (Bailey & López de Prado 2014): çoklu test altındaki seçim yanlılığını ve normal olmayan getirileri düzeltir; Probabilistic Sharpe Ratio'nun eşiği tüm denenen stratejileri yansıtacak şekilde yükseltilmiş hâli; Minimum Track Record Length ile bağlantılı — [SSRN 2460551](https://papers.ssrn.com/abstract=2460551); [eScholarship](https://escholarship.org/content/qt2329p290/qt2329p290.pdf)
- Harvey, Liu & Zhu (2016, RFS): 316 faktörlük yayın evreni üzerinden çoklu-test çerçevesi (testler arası korelasyon ve eksik veriye izin veriyor); yeni keşfedilen bir faktör için **t > 3,0** çıtası; "finansal ekonomide iddia edilen bulguların çoğu muhtemelen yanlış" — [NBER w20592](https://www.nber.org/papers/w20592); [SSRN 2513152](https://papers.ssrn.com/abstract=2513152)
- Karşı görüşler: yayımlanmamış anlamsız sonuçlar eksik olduğu için çıtayı tahmin eden ekstrapolasyon zayıf tanımlı; %5 FDR yeterli sayılırsa klasik çıta yükseltilmek zorunda değil — [arXiv 2204.10275](https://arxiv.org/pdf/2204.10275); HLZ verisi yeniden incelenince iddia edilen bulguların çoğu muhtemelen doğru — [arXiv 2206.15365](https://arxiv.org/pdf/2206.15365)
- Pratik bir yanlışlama şablonu (MNQ ön baskısı): OOS net t ≥ 2, kat başına ≥30 işlem, sürtünme sonrası pozitif, her test yılında aynı yön, permütasyon p < 0,001, artı yöntemin kenar yakalayabildiğini gösteren **pozitif kontroller** — [arXiv 2605.04004](https://arxiv.org/abs/2605.04004)

### Inferences
**"Bir şey çalışana kadar ayar değiştirme" durumunda pratik kurallar**
1. **N'i dürüst say.** Yerel çalışmada şimdiye kadar denenen her varyant (tolerans değerleri, pencere uzunlukları 7/33, k, normalizasyon, VIX/stres/seans/volatilite koşulları, çapraz-sembol kombinasyonları, her ufuk 15m/1h/1g) tek bir deneme ailesidir. Yeni bir fikir test edilirken DSR ve SPA'ya verilen N bu geçmiş denemeleri de içermeli (Bailey–LdP'nin "seçim yanlılığı" tanımı tam olarak budur).
2. **Ön-kayıt (pre-registration).** Tanım, ufuk, karar kuralı, maliyet varsayımı ve geçme ölçütü sonuçlara bakmadan yazılır (projenin 3. KURALI ile uyumlu). Yalnız ön-kayıtlı ikincil varyantlar (≤ birkaç) denenir.
3. **Evrensel bootstrap testi.** Tüm konfigürasyonların aynı değerlendirme penceresindeki günlük (veya işlem başı) net getiri serileri bir matrise konur; Hansen SPA (en iyi model benchmark'ı geçiyor mu) ve stepwise SPA / Romano–Wolf (hangileri geçiyor) uygulanır; Python'da `arch.bootstrap` modülü SPA ve StepM içerir (arch dokümantasyonu yukarıda). Benchmark, sıfır getiri değil **"saat-bazlı drift"** ve **"her zaman yukarı"** olmalı.
4. **Kalıcılık / PBO.** Zaman ekseni S (ör. 16) bloğa bölünür; tüm C(S, S/2) eğitim/test bölünmelerinde eğitimde en iyi konfigürasyonun testteki sıralaması kaydedilir; testte medyanın altına düşme oranı = PBO. PBO > ~%50 ise seçim süreci şanstan ayırt edilemiyor demektir. Bajgrowicz–Scaillet'in kalıcılık testinin pratik karşılığı budur.
5. **DSR.** Seçilen konfigürasyonun Sharpe'ı, N denemenin beklenen maksimum Sharpe'ına karşı sınanır. (Hafızadan, doğrulanmalı: E[max SR] ≈ √V[SR_n]·((1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(N·e))), γ≈0,5772; DSR = Φ((SR̂−SR₀)√(T−1)/√(1−γ₃SR̂+((γ₄−1)/4)SR̂²)). Kontrol: N=45 için E[max] ≈ 2,24σ → yıllık SR=1 hedefi için ≈ 5 yıl; bu, kaynaklı "5 yıl → 45 deneme" örneğiyle tutarlı.)
6. **t-çıtası.** Yeni ve mekanizması önceden belirtilmemiş bir örüntü için t ≥ 3 (HLZ); literatürde önceden belgelenmiş ve ön-kayıtlı bir replikasyon (ör. gün-içi momentum) için t ≥ 2 makul (Chen'in FDR argümanı) — ama yayın sonrası çürüme nedeniyle etki büyüklüğü beklentisi yarıya indirilerek güç hesabı yapılmalı.
7. **Maliyet baştan.** NAS100 CFD'de spread + kayma işlem başına sabit puan olarak düşülür; Mesfin'in "brüt hareket < sürtünme tabanı" testi ilk filtre olarak uygulanır (brüt beklenti spread'in ≥2–3 katı değilse sinyali hiç test etme).
8. **Plasebo + pozitif kontrol.** Yerel çalışmanın rastgele-komşu plasebosu korunur; buna ek olarak bilinen bir etki (ör. saat-bazlı volatilite mevsimselliği veya gün-içi momentum) aynı boru hattında pozitif kontrol olarak koşulur — boru hattı bilinen etkiyi bulamıyorsa negatif sonuçlar yorumlanamaz.
9. **Tek kullanımlık son dönem.** Son 12–18 ay (ör. 2025-04 → 2026-10) hiçbir ayar için bakılmadan kilitlenir; yalnız nihai, ön-kayıtlı tek konfigürasyon bir kez test edilir. Bailey vd.'nin hold-out eleştirisi (tek hold-out da tekrar tekrar bakılırsa aşırı uyar) bu kuralın "bir kez" kısmını zorunlu kılar.
10. **Sıra bağımlılığı ve icra.** Projenin canlıya alma kartı (sonraki M1 açılışı + gerçek spread, aynı anda tek pozisyon) literatürdeki "maliyet + kalıcılık" ölçütlerinin pratik karşılığıdır; literatür bu kartı ikame etmez, destekler.

### Gaps
- White (2000, *Econometrica*) "A Reality Check for Data Snooping" birincil metni bu turda açılmadı (STW ve SPA kaynakları üzerinden).
- PBO'nun CSCV prosedürünün ve MinBTL/DSR formüllerinin tam ifadeleri birincil PDF'ten satır satır doğrulanmadı (yukarıdaki formüller hafızadan, sayısal tutarlılık kontrolüyle).
- Harvey & Liu "Backtesting" (Sharpe haircut) makalesi aranmadı. Harvey & Liu (2020, JF) "False (and Missed) Discoveries in Financial Economics" (çift-bootstrap ile belirli bir FDR'ye karşılık gelen t-çıtası) yalnız arama özetinde geçti; birincil kaynak açılmadı.

## 5. Kanıta dayalı, yerelde denenmemiş, uygulanabilir fikirler (kesin tanımlarla, kanıt kalitesine göre sıralı)

### Takeaway
Yerel testlerin hepsi "şekil benzerliği" ailesindendi ve başarısız oldu; literatürde kanıtı olan yöntemler ise **saat-sabitli akış/mikroyapı etkileri** (son yarım saat momentumu, günlük reversal, gece kayması, aynı-saat sürekliliği, volatilite mevsimselliği) ve bunların **mekanizma değişkenleriyle koşullandırılması** (gamma, ilk-yarım-saat volatilitesi, makro haber günü). En güçlü kanıtlı aday: NDX'te rROD → son 30 dk momentumu; ikincisi günlük negatif seri bağımlılık; üçüncüsü satış sonrası gece kayması. Büyüklük için saat faktörü × günlük volatilite tahmini, yerel "saat-bazlı tipik hareket" bulgusunun doğal genellemesi.

### Cited Findings
- rROD (önceki kapanış → kapanışa 30 dk) son 30 dakikayı öngörür; hisse vadelilerinde t=7,29, havuzlanmış OOS R² %2,88; 17 hisse vadelisinin 14'ünde OOS R² pozitif-anlamlı; 1974–1999 ve 2000–2020'nin ikisinde de var; NGE>0 günlerde yok; 2 günde geri dönüyor; S&P vadelisinde 1 tick maliyetle net Sharpe pozitif — [Baltussen vd. 2021 PDF](https://www3.nd.edu/~zda/intramom.pdf)
- r1 (önceki kapanış → 10:00 ET) ve r12 (15:00–15:30) son yarım saati öngörür; OOS R² %1,2/%0,7/%1,8; yüksek ilk-yarım-saat volatilitesinde R² %3,3 (düşükte %0,6); yüksek hacimde %3,1; makro haber günlerinde daha güçlü; r1 işaret stratejisi Sharpe 1,08; r1 ve r12 aynı işaretliyken başarı %77 — [GHLZ çalışma kâğıdı](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- 16 gelişmiş piyasanın 12'sinde teyit; düşük likidite/yüksek volatilitede güçlü — [Li, Sakkas & Urquhart 2022](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html)
- Endeks günlük seri bağımlılığı 2000'lerden beri negatif; MAC(5)'e karşı strateji S&P 500'de 1999 sonrası Sharpe 0,67 — [Baltussen, van Bekkum & Da](https://www3.nd.edu/~zda/Indexing.pdf); [CXO](https://www.cxoadvisory.com/technical-trading/effect-of-tracking-products-on-short-term-equity-index-trendingreversal)
- Avrupa açılış saatlerinde pozitif ABD endeks getirisi; satış günlerinden sonra güçlü, rallilerden sonra zayıf reversal; önceki kapanıştaki emir dengesizliğiyle ilişkili — [NY Fed SR917](https://www.newyorkfed.org/research/staff_reports/sr917)
- Aynı yarım saatin tam gün katı gecikmelerinde (≥40 gün) pozitif süreklilik, ilk/son yarım saatte en güçlü (tek-hisse) — [Heston, Korajczyk & Sadka](https://www.bauer.uh.edu/departments/finance/documents/Heston_Korajczyk_Sadka_paper_UH.pdf)
- Gün-içi volatilite periyodikliği modellenmeden volatilite dinamiği tanımlanamaz; S&P 500'de U-şekli — [Andersen & Bollerslev 1997](https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html); [arXiv 2310.19992](https://arxiv.org/pdf/2310.19992)
- Noise-area gün-içi momentum, SPY 2007–2024: yıllık %19,6, Sharpe 1,33, maliyet sonrası toplam %1.985 (hakemsiz, uygulayıcı-akademik ortak) — [SFI 24-97](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy); karşı kanıt: MNQ'da ORB t=0,88, 11 ailede brüt < sürtünme — [arXiv 2605.04004](https://arxiv.org/abs/2605.04004)
- Pre-FOMC kayması 2015 sonrası kayboldu — [Kurov vd. 2021](https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html)
- Görüntü-CNN kesitsel: büyük-500 evreninde Sharpe ~1'e düşüyor (ikincil) — [BSIC](https://bsic.it/technical-analysis-on-steroids/)
- Mum formasyonları maliyet + veri-madenciliği sonrası değersiz — [Duvinage vd.](https://dial.uclouvain.be/pr/boreal/en/object/boreal%3A136070/datastream/PDF_02/view); [Fock vd.](https://opus.bibliothek.uni-augsburg.de/opus4/frontdoor/index/index/year/2017/docId/35176)

### Inferences
Kanıt notu ölçeği (benim değerlendirmem): **A** = birden çok hakemli üst-dergi + bağımsız replikasyon + mekanizma; **B** = tek hakemli kaynak veya yalnız tek-hisse kanıtı; **C** = hakemsiz / uygulayıcı / çürüme kanıtı var. Tüm saatler **America/New_York (DST-doğru)**; broker sunucu saati (UTC+2/+3) kullanılmamalı. "Kapanış" = 16:00 ET cash-seans fiyatı (CFD 16:00'dan sonra da işlem görür; etiket bu saatten alınır).

**Fikir 1 — Son yarım saat momentumu, rROD versiyonu (Kanıt: A−)**
- Girdiler: P_prev = önceki işlem günü 16:00 ET kapanış; P_1530 = bugün 15:30 ET; P_1600 = bugün 16:00 ET.
- rROD = ln(P_1530 / P_prev); hedef rLH = ln(P_1600 / P_1530).
- Karar: 15:30 ET'de sign(rROD) yönünde pozisyon, 16:00 ET'de kapat. Ufuk 30 dk. Ön-kayıtlı ikincil: 15:45→16:00 (15 dk ufku) ve 15:00→16:00 (1 saat ufku; öngörücü önceki kapanış → 15:00).
- Değerlendirme: Campbell–Thompson OOS R² (genişleyen tarihsel ortalamaya karşı), işaret isabeti vs. "son 30 dk her zaman long" tabanı, işlem başına NAS100 spread'i düşülmüş net R; 2 günlük geri dönüşü ayrıca raporla.
- Neden yerel testlerden farklı: şekil eşleştirmesi yok, tek bir saat-sabitli kümülatif getiri; mekanizma (gamma/kaldıraçlı ETF akışı) önceden belli.

**Fikir 2 — GHLZ r1/r12 çift-onay + rejim koşulu (Kanıt: A−, Fikir 1'in varyantı; aynı aileden sayılır)**
- r1 = ln(P_1000 / P_prev) (gece dahil), r12 = ln(P_1530 / P_1500).
- Karar: sign(r1) = sign(r12) ise 15:30'da o yönde 30 dk; aksi halde işlem yok.
- Ön-kayıtlı koşul: ilk yarım saat (09:30–10:00) realize volatilitesinin genişleyen-pencere tercili; yalnız üst tercilde işlem. İkinci koşul: CPI/NFP/FOMC günleri (projenin takvim verisiyle).
- Not: Yerelde başarısız olan VIX-rejim koşullandırmasından farkı, koşulun yayımlanmış ve mekanizmaya bağlı tek bir ölçü (ilk yarım saat vol) olması; yine de N'e eklenir.

**Fikir 3 — Gamma koşullu momentum/reversal (Kanıt: B+, veri gerekirse)**
- Girdi: S&P 500 (veya mümkünse NDX/QQQ) opsiyon dealer net gamma tahmini (NGE; SqueezeMetrics türü GEX serisi — Baltussen vd. SqueezeMetrics'i OptionMetrics ile doğrulamış).
- Karar: NGE_t < 0 ise Fikir 1 uygulanır; NGE_t > 0 ise işlem yok (veya ön-kayıtlı olarak son 30 dk'da −sign(rROD), reversal hipotezi).
- Uyarı: NDX'in kendi opsiyon gamma'sı S&P'den farklı olabilir; S&P NGE'si vekil olarak kullanılırsa bu açıkça yazılmalı.

**Fikir 4 — Günlük endeks reversal'ı (negatif seri bağımlılık) (Kanıt: A−)**
- Girdiler: r_t = 16:00→16:00 ET günlük log getiri.
- Sinyal (yaklaşım; makaledeki MAC(5) ağırlıkları doğrulanmadı): s_t = Σ_{k=1..5} w_k · r_{t−k+1}, w = (5,4,3,2,1)/15. Ek koşul: son 250 günde tahmin edilen ağırlıklı otokorelasyon ortalaması (ρ1..ρ5) < 0 ise pozisyon_{t+1} = −sign(s_t), değilse işlem yok.
- Ufuk 1 gün (16:00→16:00). Ön-kayıtlı alternatif: yalnız k=1 (dünün getirisine karşı).
- Birleşik varyant: Baltussen vd.'nin "gün-içi momentum 2 günde geri döner" bulgusuna göre, ertesi gün pozisyonu −sign(r_ROD,t + r_LH,t).

**Fikir 5 — Satış günü sonrası gece kayması (Kanıt: B+)**
- Girdiler: D_t = 09:30→16:00 ET cash-seans getirisi; σ20 = son 20 günün D standart sapması.
- Olay: D_t < −1·σ20 (satış günü). Pozisyon: 16:00 ET (veya CFD'nin yeniden açılışı) long → çıkış penceresi.
- Çıkış penceresi: kesin saat literatürden doğrulanmadığı için **önce yalnız eğitim döneminde** saat-saat gece getiri profili çıkarılır, Avrupa açılışını (≈02:00–04:00 ET) kapsayan pencere bir kez seçilip dondurulur; test döneminde değiştirilmez.
- Kontrol: aynı kural ralli günleri (D_t > +1σ20) için de koşulur — literatür asimetri öngörüyor (ralli sonrası zayıf); asimetri çıkmazsa mekanizma tutmuyor demektir.
- Maliyet: CFD gecelik finansman (rollover saatini geçiyorsa) + spread.

**Fikir 6 — Aynı-saat sürekliliği (Kanıt: B; tek-hisse kanıtı, endeks için fikir kaynağı)**
- Girdiler: cash seans 13 yarım saatlik kova h ∈ {09:30, 10:00, …, 15:30}; r_{h,t} = kova getirisi.
- Sinyal: m_{h,t} = (1/20)·Σ_{d=1..20} r_{h,t−d} (aynı kovanın son 20 gündeki ortalaması); alternatif gecikme seti d ∈ {1,…,40}.
- Karar: kova h başında sign(m_{h,t}) yönünde, kova sonunda kapat (30 dk). 15 dk (26 kova) ve 1 saat (7 kova) versiyonları ön-kayıtlı ikincil.
- Bağlantı: yerel "saat-bazlı tipik hareket büyüklükte kazanır" bulgusunun *yön* karşılığı; HKS'ye göre etki ilk ve son yarım saatte en güçlü → önce h=09:30 ve h=15:30 test edilir.

**Fikir 7 — Büyüklük: saat faktörü × günlük volatilite tahmini (Kanıt: volatilite için A; yön değil)**
- Girdiler: 5 dk getirilerden günlük realize volatilite RV_t; kova h için diurnal faktör f_h = son 60 günde ortalama(|r_{h,d}| / √RV_d).
- Tahmin: E|r_{h,t+1}| = f_h · √(RV̂_{t+1}), RV̂ HAR tipi regresyonla (günlük, haftalık, aylık RV ortalamaları) veya VXN/VIX ile; makro haber günü çarpanı ön-kayıtlı.
- Değerlendirme: yerel kazanan (salt saat-bazlı tipik hareket) taban alınarak MAE/QLIKE kıyası; kazanırsa projedeki ATR merdiveni TP/SL geometrisine girdi olur.
- Not: HAR-RV için birincil kaynak bu turda doğrulanmadı (Gaps).

**Fikir 8 — Noise-area gün-içi momentum (Kanıt: C+)**
- Tanım (hafızadan, SSRN orijinalinden doğrulanmalı): her dakika-of-day τ için σ_τ = son 14 günde ortalama |P_τ / P_açılış − 1|; üst bant = max(açılış, önceki kapanış)·(1+σ_τ), alt bant = min(açılış, önceki kapanış)·(1−σ_τ); yalnız :00/:30'da kontrol; fiyat üst bandın üstündeyse long, altındaysa short; bant/VWAP trailing stop, en geç 16:00 kapanış.
- Neden ilginç: "gürültü" eşiği tam olarak yerelde büyüklükte kazanan saat-bazlı tipik hareket; yerel bulgu ile doğal köprü.
- Uyarı: hakemsiz, tek dönem (2007–2024), SPY; MNQ'da ORB ve OHLCV momentum aileleri sürtünmeyi geçemedi → güçlü şüphecilikle, sıkı maliyetle.

**Fikir 9 — Görüntü-CNN'in kesitsel kullanımı → endeks genişliği (Kanıt: C; fikir kaynağı)**
- NDX-100 bileşenlerinin 20 günlük OHLC görüntülerinde JKX tipi CNN ile her hisse için P(up, 5 gün); endeks sinyali = ağırlıklı ortalama olasılık − 0,5. Ufuk 1–5 gün.
- Uyarı: kanıt kesitsel sıralama içindir, endeks zaman serisi için değil; büyük hisselerde Sharpe ~1 (brüt); veri ve hesap maliyeti yüksek. Öncelik düşük.

**Fikir 10 — Negatif/pozitif kontroller olarak kullanılacaklar (öneri değil)**
- Pre-FOMC kayması (2015 sonrası kayboldu) → boru hattının "çürümüş etkiyi" bulmaması gerektiğini sınayan çürüme kontrolü.
- Üç-günlük mum reversal'ı (Caginalp–Laurent tanımı) → yerel mum eşleştirmesiyle aynı ailede negatif kontrol.
- Saat-bazlı volatilite mevsimselliği → pozitif kontrol (her boru hattı bunu bulmalı).

**Sıralama özeti:** 1 (rROD) > 2 (r1/r12 + vol) ≈ 4 (günlük reversal) > 5 (gece kayması) > 3 (gamma, veri varsa) > 7 (büyüklük) > 6 (aynı-saat) > 8 (noise-area) > 9 (CNN). Fikir 1–3 tek aile sayılmalı (aynı öngörücü/hedef); aile içi en iyi seçilirse SPA/stepwise-SPA zorunlu.

### Gaps
- NDX/QQQ'ya özgü dealer gamma geçmiş serisinin erişilebilirliği ve S&P NGE'sinin NDX için vekil geçerliliği doğrulanmadı.
- Noise-area stratejisinin kesin tanımı (bant formülü, 14 gün, kontrol saatleri, stop kuralı) birincil metinden doğrulanmadı.
- HAR-RV (Corsi) ve VXN tabanlı volatilite tahmininin NDX gün-içi büyüklük tahmini için literatür karşılaştırması bu turda aranmadı.
- Gece kayması penceresinin kesin saatleri ve NQ (NASDAQ vadelisi) için ayrı sonuç doğrulanmadı.
- Chinco, Clark-Joseph & Ye (2019) tipi 1 dakikalık çapraz-varlık gecikmeli getiri (LASSO) öngörülebilirliği — endeks/CFD için olası bir fikir kaynağı — bu turda araştırılmadı.
