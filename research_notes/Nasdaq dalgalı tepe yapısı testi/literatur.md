# Nasdaq dalgalı tepe yapısı — yayımlanmış kanıt taraması (formasyonlar, zirve yakını oynaklık, kısa vadeli dönüş, yöntem)

> Kapsam: hisse endeksi / endeks vadelisi (NDX, SPX, ES/NQ). Tek hisse ve FX sonuçları yalnız **fikir kaynağı** olarak etiketlendi.
> Ufuk: 1 saat, 1 gün, 5 gün (aylık yalnız bağlam). Her bulguda "örneklem-içi" mi, "örneklem-dışı / maliyet sonrası / yayın sonrası" mı olduğu belirtildi.
> Not: Savin ve ark. ile Baltussen ve ark. sayıları PDF tam metinden okundu; diğerlerinin çoğu özet/abstract düzeyinde (aşağıda tek tek işaretli).

---

## 1. Tepe formasyonlarının akademik testleri (H&S, çift tepe/M, Lo-Mamaysky-Wang, Osler-Chang, Savin ve ark., Bulkowski, endeks düzeyi)

### Takeaway
Akademik testlerin hiçbiri hisse **endeksinde** 1s/1g/5g ufkunda, örneklem-dışı ve maliyet sonrası, bir tepe formasyonunun **yön** öngördüğünü göstermiyor; bulunabilen en iyi kanıt tek hisselerde (Savin ve ark. 2007). Orada H&S tepesi ham olarak para kaybettiriyor (fiyat yükselmeye devam etmiş), kâr yalnız beta/faktör düzeltmesinden sonra ortaya çıkıyor (≈%4–7/yıl, 20–60 gün ufkunda) ve kısmen "negatif momentum" ile açıklanıyor. Lo ve ark. (2000) yalnızca formasyondan sonraki 1 günlük getirinin **dağılımının** farklı olduğunu gösteriyor; yön ya da kârlılık göstermiyor.

### Cited Findings
**Lo, Mamaysky & Wang (2000), "Foundations of Technical Analysis", Journal of Finance 55:1705–1765 (örneklem-içi, tek hisse)**
- Formasyon tanıma, çekirdek (kernel) parametrik-olmayan regresyonla otomatikleştirildi; ABD hisseleri, 1962–1996 — [MIT özet sayfası](https://web.mit.edu/Alo/www/Papers/techanal.html)
- Yöntem: günlük getirilerin koşulsuz dağılımı ile H&S, çift dip vb. formasyonlara **koşullu** dağılımı karşılaştırılıyor; "birkaç göstergenin ek bilgi taşıdığı" ve "pratik değeri olabileceği" sonucuna varılıyor — [NBER w7613](https://www.nber.org/papers/w7613); [MIT](https://web.mit.edu/Alo/www/Papers/techanal.html)
- CFA Institute özetine göre klasik H&S "en iyi" formasyon olmayabilir ve etkiler Nasdaq hisselerinde daha güçlü — [CFA Digest 2001](https://rpc.cfainstitute.org/-/media/documents/article/cfa-digest/2001/dig-v31-n1-811-pdf.pdf)
- Lo ve ark.'nın kurulumu (Savin ve ark.'nın aktarımıyla): 38 işlem günlük kayan pencere; ufuk **1 gün**; H&S = beş ardışık uç nokta E1..E5 için (R1) E1 maksimum, (R2) E3>E1, (R3) E3>E5, (R4) E1 ve E5 ortalamalarının %1,5'i içinde, (R5) E2 ve E4 ortalamalarının %1,5'i içinde. Savin ve ark. ayrıca Lo ve ark.'nın "fiyat öngörülebilirliğine değil, koşullu dağılımın bilgi içeriğine" odaklandığını açıkça yazıyor — [Savin, Weller & Zvingelis WP, Ekim 2006](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)

**Savin, Weller & Zvingelis (2007), "The Predictive Power of 'Head-and-Shoulders' Price Patterns in the U.S. Stock Market", J. Financial Econometrics 5(2):243–265 (tek hisse, tek on yıl, örneklem-dışı dönem YOK)**
- Veri: S&P 500 ve Russell 2000 hisseleri, 1990–1999. Pencere n=63 işlem günü (Bulkowski'nin ortalama tamamlanma süresi). Boyun çizgisi (E2–E4) kırılımı şart; getiri E6'dan 3 gün sonra ölçülüyor. Ufuklar 20/40/60 işlem günü — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- **Ham yön:** S&P 500 hisselerinde H&S'ye göre açılan kısa pozisyonun tüm ufuk ve bant genişliklerinde ortalama aşırı getirisi anlamlı biçimde **zarardı**; yani H&S tepesinden sonra fiyat ortalamada yükseldi (dönem balon olarak nitelenen 1990'lar; piyasayı açığa satmak −%11,4/yıl kazandırırdı) — [aynı kaynak](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- **Risk düzeltmeli:** Fama-French 3 faktör regresyonunda 60 günlük ufukta S&P 500 için sabit −%0,4/ay = **%4,8/yıl** risk-düzeltmeli aşırı getiri; Russell 2000 için %5,4–6,6/yıl. Ham 60 günlük getiri ise −%3,5/yıl (yani "kazanç" stratejinin piyasaya göre daha az kaybetmesinden geliyor) — [aynı kaynak](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- **Momentum kontrolü:** Momentum faktörü eklenince anlamlı yükleme çıkıyor; S&P 500'de 60 günlük fazla getiri 18–25 baz puan/aya düşüyor, Russell 2000'de 41 bp/ay (%4,9/yıl) kalıyor. Yazarlar başarının bir kısmını "negatif momentum hisselerini tespit etmesine" bağlıyor — [aynı kaynak](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- **Maliyet:** Tek başına strateji olarak Russell 2000'de başabaş tek-yön maliyet 20/40/60 gün için 6/26/39,5 bp; yazarlar "tek başına kârlı olduğu iddiasına çok az destek" diyor. Faktör-düzeltmeli getiri, 20 bp tek-yön maliyetle S&P 500'de %3,6/yıl, Russell 2000'de %4,2/yıl — [aynı kaynak](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- **Elle seçilmiş örneklere kalibrasyon işe yaramadı:** Bulkowski'nin 11 örnek H&S'sine göre ayarlanan ek filtreler (R4a/R5a %4 tolerans, R6–R9 omuz/baş oranları, simetri) formasyon sayısını %30 azalttı (6.406 → 4.452) ama aşırı getiriye **hiç etki etmedi** — [aynı kaynak](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- Özet ve yayın künyesi: [Iowa IRO kaydı](https://iro.uiowa.edu/esploro/outputs/journalArticle/The-Predictive-Power-of-Head-and-Shoulders-Price/9984963212902771)
- Takip çalışması (MPRA 60825, aramada Chong & Poon 2014 olarak özetlendi; tam metin doğrulanmadı): H&S'nin trend içindeki göreli konumunu hesaba katan filtre, H&S tepesi için risk-düzeltmeli getiriyi genelde iyileştiriyor — [MPRA 60825](https://mpra.ub.uni-muenchen.de/60825/)

**Osler & Chang (1995) / Chang & Osler (1999) — FX, yalnız fikir kaynağı**
- NY Fed Staff Report No. 4: majör döviz kurları, günlük, 1973–1994 ortası; teknik analiz kılavuzlarındaki kurallarla formasyon tespiti; kârlar 10.000 bootstrap rassal yürüyüş serisiyle kıyaslandı — [IDEAS/RePEc](https://ideas.repec.org/p/fip/fednsr/4.html)
- Yayımlanmış hali (Economic Journal 1999, "Methodical Madness"): H&S kuralı kârlı ama **verimsiz**; daha basit kurallar (momentum/MA tipi) onu domine ediyor — [IDEAS EJ](https://ideas.repec.org/a/ecj/econjl/v109y1999i458p636-61.html)
- Brezilya hisselerinde Osler-Chang yönteminin tekrarı: temel formasyon pozitif getiri verdi, ters formasyon vermedi; vergi ve işlem maliyetinden sonra getiriler sağlam kalmadı — [Boainain & Pereira 2009, IDEAS](https://ideas.repec.org/a/brf/journl/v7y2009i3p265-303.html)

**Friesen, Weller & Dunham (2009), Journal of Banking & Finance 33(6):1089–1100 — teorik mekanizma**
- Doğrulama yanlılığı (confirmation bias) modeli, H&S ve çift tepe gibi formasyonları ve otokorelasyonu üretebiliyor; ampirik olarak hisselerde ardışık fiyat sıçramalarında anlamlı **pozitif** otokorelasyon buldular — [UNL Digital Commons](https://digitalcommons.unl.edu/financefacpub/11)

**Bulkowski (uygulayıcı, AKADEMİK DEĞİL; tek hisse, günlük, taban/maliyet yok, "mükemmel işlem" varsayımı)**
- Eve & Eve çift tepe (klasik): başabaş başarısızlık oranı %20, ortalama düşüş %16, 942 "mükemmel işlem", boğa piyasası sonuçları — [thepatternsite eedt](https://www.thepatternsite.com/eedt.html)
- Adam & Eve çift tepe: başarısızlık %21, ortalama düşüş %16, geri çekilme (pullback) oranı %64, 651 işlem — [thepatternsite aedt](https://www.thepatternsite.com/aedt.html); Eve & Adam: %21 / %15 / pullback %64, 662 işlem — [thepatternsite eadt](https://www.thepatternsite.com/eadt.html)
- 2000 tarihli makale: 1.280 ikiz tepe; teyit (onay noktası altında kapanış) öncesi başarısızlık %65, teyitten sonra %17; teyitsiz ikiz tepeler sitede %60 başarısız deniyor — [Traders.com 2000](https://www.traders.com/Documentation/FEEDbk_docs/2000/09/Abstracts_new/Bulkowski/Bulkowski.html); [arama özetiyle](https://www.thepatternsite.com/eedt.html)
- Savin ve ark. de Bulkowski'nin bilgisayar taramasına tamamen dayanmadığını ve bunun veri gözetleme (data snooping) sorusu doğurduğunu not ediyor — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)

**Endeks düzeyi, "zirveye yakınlık" (aylık — yalnız bağlam)**
- Li & Yu (2012, JFE 104:401–419): Dow'un **52 haftalık zirvesine yakınlık** gelecekteki toplam piyasa getirisini **pozitif**, **tarihi zirveye yakınlık** ise negatif öngörüyor; G7'de sağlam — [SUFE özet](https://academicnewsletter.sufe.edu.cn/info/356820)

### Inferences
- "Tepe formasyonu → düşüş" iddiasının akademik karşılığı **mutlak yön** değil, **göreli/faktör-düzeltmeli** getiri. Endeks için piyasa betası tanım gereği 1'dir; yani Savin tipi "beta-düzeltmeli" kazanç bir endekste aynı biçimde var olamaz. Endekste geriye kalan şey ham yöndür ve ham yön Savin'de S&P 500 hisselerinde **ters** çıkmış.
- Savin'in 60 günlük ≈0,4%/ay risk-düzeltmeli etkisini yayın sonrası aşınma için yarıya indirip (≈0,2%/ay) 5 güne orantılarsak birkaç baz puan eder; bu, NAS100 spread + kayma maliyetinin altında. 1 saatlik ufukta pratikte sıfır.
- Lo ve ark.'nın "koşullu dağılım farklı" bulgusu, formasyondan sonra **oynaklık/basıklık** değişmesiyle de tamamen açıklanabilir (dağılım testi yönü ayırmaz). Bu, projenin "mum şekli benzerliği yön öngörmüyor, büyüklüğü saat-içi tipik hareket öngörüyor" bulgusuyla tutarlı.
- Li & Yu, "son zirvelere yakın" olmanın endekste ortalama olarak **olumlu** sinyal olduğunu söylüyor (aylık ufuk). Kullanıcının seçtiği tepe örnekleri bu genel tabana karşı test edilmeli; zirve yakınında olmak tek başına ayı kanıtı değil.
- Bulkowski'nin "teyitten sonra başarısızlık %17" sayısı, düşüşün bir kısmı **zaten gerçekleştikten sonra** koşullandırılmış bir istatistik ve tabanı yok (rastgele bir tarihte "onay noktası altında kapanış" sonrası aynı istatistik ölçülmemiş). Hindsight ile seçilmiş tepe örneklerine benzer bir koşullandırma.

### Gaps
- NDX/SPX endeksi veya ES/NQ vadelisi üzerinde H&S/çift tepe/dağıtım aralığının 1s/1g/5g ufkunda, örneklem-dışı ve maliyet sonrası test edildiği hakemli bir çalışma **bulamadım**.
- Lo ve ark.'nın H&S ve DTOP için Kolmogorov-Smirnov sonuçları ve tam DTOP tanımı çıkarılamadı (NBER PDF'i taranmış görüntü; metin katmanı yok).
- Osler-Chang'ın döviz bazında hangi kurlarda kâr bulduğu (hafızamda DM ve yen) bu taramada doğrulanmadı.
- Li & Yu'nun regresyon ufku (aylık/çok aylık) tam metinden doğrulanmadı.
- Bulkowski'nin "ortalama düşüş" ölçüsünün tanımı (kırılımdan nihai dibe mi?) bu taramada kaynakla doğrulanmadı.

---

## 2. Zirve yakını oynaklık rejimleri: yön mü, risk mi? (volatility-managed portföyler, kaldıraç etkisi, VIX vade yapısı, çöküş olasılığı)

### Takeaway
Güçlü ve tekrarlanmış kanıt **riskin** öngörülebildiğini gösteriyor, **yönün** değil: oynaklık kalıcıdır, negatif getiriler günlerce yüksek oynaklığı öngörür (kaldıraç etkisi), büyük kayıplar yüksek oynaklık dönemlerinde kümelenir ve hızlı yükselişler ortalama getiriyi düşürmeden **çöküş olasılığını** artırır. Yüksek oynaklığın daha düşük **Sharpe** getirdiği (beklenen getiri oynaklıkla orantılı artmıyor) örneklem-içi güçlü, ama gerçek zamanlı/örneklem-dışı ve maliyet sonrası kanıt zayıf ve tartışmalı.

### Cited Findings
**Oynaklık-yönetimli portföyler**
- Moreira & Muir (2017, JF 72(4):1611–1644): oynaklık yüksekken pozisyon küçülten portföyler büyük alfa ve yüksek Sharpe üretiyor; çünkü oynaklık değişimleri beklenen getirideki orantılı değişimle telafi edilmiyor; strateji resesyonlarda daha az risk alıyor (örneklem-içi) — [NBER w22208](https://www.nber.org/papers/22208)
- Cederburg, O'Doherty, Wang & Yan (2020, JFE 138:95–117): 103 hisse stratejisinde, gerçek zamanlı yatırımcı açısından oynaklık-yönetimli versiyonlar yönetilmeyenleri doğrudan kıyaslamada **güvenilir biçimde yenmiyor**; yayılma (spanning) regresyonundaki pozitif alfa gerçek zamanda uygulanamıyor; makul örneklem-dışı versiyonların Sharpe'ı ve kesinlik-eşdeğeri genelde **daha düşük**; neden yapısal kararsızlık — [Lehigh PDF](https://www.lehigh.edu/~xuy219/research/COWY.pdf); [Alpha Architect özeti](https://alphaarchitect.com/does-portfolio-timing-based-on-volatility-signals-outperform-buy-and-hold/)
- DeMiguel, Martín-Utrera & Uppal (2024, JF) literatürü özetliyor: Cederburg ve ark. stratejilerin örneklem-dışı başarısız olduğunu, Barroso & Detzel işlem maliyetinden sağ çıkmadığını gösterdi; kendi çok-faktörlü versiyonlarının örneklem-dışı ve maliyet sonrası çalıştığını iddia ediyorlar — [LBS PDF](https://lbsresearch.london.edu/id/eprint/3716/1/The%20Journal%20of%20Finance%20-%202024%20-%20DeMIGUEL%20-%20A%20Multifactor%20Perspective%20on%20Volatility%E2%80%90Managed%20Portfolios.pdf)
- Aşağı-yön oynaklığıyla yönetilen faktörlerin gerçek zamanlı örneklem-dışı performansı toplam-oynaklık versiyonundan daha iyi (çalışma kağıdı) — [Lehigh "Downside" PDF](https://www.lehigh.edu/~xuy219/research/Downside.pdf)
- Harvey ve ark. (2018, J. Portfolio Management 45(1):14–33): oynaklık hedefleme Sharpe'ı yalnız riskli varlıklarda (hisse, kredi) iyileştiriyor ve bu kaldıraç etkisine bağlanıyor; **tüm** varlık sınıflarında aşırı getiri (sol kuyruk) olasılığını azaltıyor, çünkü büyük kayıplar yüksek oynaklık dönemlerinde kümeleniyor; ABD hissesinde oynaklığın oynaklığı %4,6'dan %1,8'e iniyor. 60 varlık, günlük veri 1926'dan — [Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf); [Alpha Architect özeti](https://alphaarchitect.com/volatility-targeting-improves-risk-adjusted-returns/). (Hisse Sharpe'ı ≈0,40 → ≈0,48–0,51 rakamı yalnız ikincil özetlerden; tam metinden doğrulanmadı.)

**Kaldıraç etkisi / yön ↔ oynaklık nedenselliği (endeks, yüksek frekans)**
- Bollerslev, Litvinova & Tauchen (2006, JFEC 4(3):353–384): yüksek frekanslı toplam endeks verisinde, mutlak getiriler ile **cari ve geçmiş** getiriler arasındaki korelasyon **birkaç gün boyunca** anlamlı negatif ("uzamış kaldıraç etkisi"); **ters yönlü** çapraz korelasyonlar (oynaklıktan gelecekteki getiriye) genelde ihmal edilebilir — [IDEAS/RePEc](https://ideas.repec.org/a/oup/jfinec/v4y2006i3p353-384.html)
- Dufour, García & Taamouti: 5 dakikalık S&P 500 vadelisi + gerçekleşen ve ima edilen oynaklık; yalnız getiri ve gerçekleşen oynaklıkla **ilk üç günde güçlü dinamik kaldıraç etkisi**, oynaklık-geri-besleme tüm ufuklarda ihmal edilebilir; ima edilen oynaklık eklenince geri-besleme görünür hale geliyor — [CIRANO 2011s-27](https://cirano.qc.ca/en/summaries/2011s-27). (BLT 2006 ile vurgu farkı var: kaldıraç her ikisinde güçlü, geri-besleme tartışmalı.)

**Yön öngörüsü neden oynaklıktan türeyebilir — ve neden kısa ufukta çok zayıftır**
- Christoffersen & Diebold (2006, Management Science 52:1273–1287): oynaklık bağımlılığı, beklenen getiri **sıfır değilse** işaret (yön) bağımlılığı üretir; zayıf koşullu-ortalama bağımlılığı güçlü işaret ve oynaklık bağımlılığıyla uyumludur; işaret otokorelasyonu, runs testi gibi klasik araçlar bu doğrusal-olmayan bağımlılığı yakalayamaz; işaret bağımlılığı **çok yüksek ve çok düşük frekansta olası değil**, ara ufuklarda daha olası — [NBER w10009](https://www.nber.org/papers/w10009)
- Takip (Christoffersen, Diebold, Mariano, Tay & Tse): gelişmiş hisse piyasalarında oynaklıktan türetilen yön olasılık tahminleri Brier skoruyla değerlendirildiğinde "bir miktar başarı"; çarpıklık ve basıklık koşullaması önemli — [Penn WP 06-016](https://www.econ.upenn.edu/sites/default/files/filevault/working-papers/06-016.pdf)

**Hızlı yükseliş / zirve yakını → çöküş riski (ortalama getiri değil)**
- Greenwood, Shleifer & You (2019, JFE 131(1):20–43): keskin **sektör** fiyat yükselişleri olağandışı düşük ortalama getiri öngörmüyor (Fama ile uyumlu) ama **çöküş olasılığını** belirgin artırıyor; yükselişin oynaklığı, işlem hacmi, ihraç ve fiyat yolu çöküşü öngörmeye yardım ediyor — [Harvard yayın sayfası](https://shleifer.scholars.harvard.edu/publications/bubbles-fama)
- Aynı çalışmanın 2016 taslağı (yayımlanmış sayılar farklı olabilir): çöküş = 2 yıl içinde %40 düşüş; önceki 2 yıllık sektör piyasa-üstü getirisi %50'den %100'e çıkınca çöküş olasılığı %19'dan %54'e, %150'de %81; çöküş olasılığındaki artış "yalnız geçmiş oynaklıktan beklenenin ötesinde" — [NBER w23191](https://www.nber.org/system/files/working_papers/w23191/w23191.pdf)
- Chen, Hong & Stein (2001, JFE 61:345–381): hisselerde negatif çarpıklık, son 6 ayda hacmin trende göre arttığı ve son 36 ayda getirinin pozitif olduğu hisselerde en belirgin; **toplam piyasa** çarpıklığı için benzer sonuçlar var ama istatistiksel güç sınırlı — [NBER w7687](https://nber.org/papers/w7687)

**İma edilen oynaklık vade yapısı**
- Johnson (2017, JFQA 52(6)): VIX vade yapısının ikinci temel bileşeni (SLOPE) S&P 500 varyans swap'ı, VIX vadelisi ve straddle getirilerini öngörüyor (düşük eğim → yüksek getiri); vade yapısı VIX'in gelecekteki **değişimini** değil, varyans riskinin **fiyatını** taşıyor — [IDEAS/RePEc](https://ideas.repec.org/a/cup/jfinqa/v52y2017i06p2461-2490_00.html); [CXO özeti](https://www.cxoadvisory.com/volatility-effects/vix-term-structure-slope-and-variance-asset-future-returns/)
- Aynı yazarın 2011 çalışma kağıdı: VIX tek başına S&P 500 getirisi için az öngörü gücüne sahip; vade yapısı **sonraki çeyrek** S&P 500 getirisini düzeltilmiş R² %5,2 ile öngörüyor (yayımlanmış sürümün odağı değil; çeyreklik ufuk) — [Bauer seminer PDF](https://www.bauer.uh.edu/departments/finance/documents/seminars/Johnson_020712.pdf)

### Inferences
- Kullanıcının örneklerindeki "derin geri çekilmeler + alçalan tepeler" tanım gereği **artan gerçekleşen oynaklık** ve **yakın geçmişte negatif getiriler** içerir. BLT (2006) ve Dufour ve ark.'na göre bu iki özellik birkaç gün boyunca **daha yüksek oynaklığı** öngörür. Dolayısıyla "bu yapıdan sonra büyük hareket geldi" gözlemi yön bilgisi olmadan, sırf oynaklık kalıcılığıyla beklenir. Hindsight ile seçilen örneklerde bu büyük hareketin "düşüş" olanları hatırlanır.
- Christoffersen-Diebold mantığıyla sayısal örnek (varsayıma dayalı, kaynak değil): yıllık Sharpe ≈0,5 olan bir endekste, saatlik getiri için μ/σ ≈ 0,5/√(252×7) ≈ 0,012 → P(yükseliş) ≈ Φ(0,012) ≈ %50,5. Oynaklık arttıkça μ/σ daha da küçülür; yani yüksek oynaklıklı tepe rejiminde 1 saatlik yön olasılığı **%50'ye yaklaşır**. 5 günlük ufukta bile μ/σ ≈ 0,07 → ≈%52,8. Gerçekçi bir "yön" kenarı bu tabanı ancak birkaç puan aşabilir.
- Moreira-Muir'in örneklem-içi iddiası ("yüksek oynaklık → daha düşük Sharpe") projeye **pozisyon boyutu** olarak taşınabilir (yön sinyali olarak değil). Cederburg ve ark. bu kazancın gerçek zamanda güvenilir olmadığını söylediği için beklenen faydayı Sharpe'ta değil **sol kuyrukta** aramak daha savunulabilir (Harvey ve ark.).
- Greenwood ve ark. ile Chen-Hong-Stein, "zirve yakını oynaklık" ile **drawdown olasılığı** arasında bir bağ öneriyor; ama sektör/hisse düzeyinde ve 2 yıl / 6–36 ay ufkunda. 1s–5g endeks ufkuna aktarılabilirliği kanıtlanmamış.

### Gaps
- "Fiyat zirveye yakınken gerçekleşen/ima edilen oynaklığın artması" durumunu endekste 1g–5g ufkunda doğrudan test eden hakemli bir çalışma bulamadım (yalnız uygulayıcı yorumları var, kaynak olarak kullanılmadı).
- Cederburg ve ark.'nın özellikle **piyasa faktörü** için gerçek zamanlı sonucu tam metinden çıkarılamadı.
- Greenwood ve ark.'nın yayımlanmış sürümdeki çöküş olasılığı sayıları doğrulanmadı (taslak sayıları raporlandı).
- VIX vade yapısı tersine dönmesinin (backwardation) 1g–5g endeks **yönü** için öngörü gücü hakkında güvenilir hakemli kaynak bulamadım.

---

## 3. Endeks düzeyinde aralık/konsolidasyon ve kısa vadeli ortalamaya dönüş (1 saat – 5 gün); "dalgalı aralık" trendden nasıl ayrılır?

### Takeaway
2000'lerden beri hisse endekslerinde günlük ve haftalık getiriler **negatif seri bağımlılık** gösteriyor (Baltussen ve ark. 2019; Nasdaq 100 örneklemde). Yani 1–5 günlük ufukta beklenen şey, düşüşten sonra kısmi **geri dönüş**tür, devam değil. Bu, projenin "korku döner, coşku dönmez" bulgusuyla uyumlu. Gün içinde (yarım saat/1 saat) ise iki zayıf ama yayımlanmış düzenlilik var: ilk yarım saatin son yarım saati öngörmesi (endeks ETF'i) ve aynı saat diliminin günler arasında süreklilik göstermesi (tek hisse). "Dalgalı tepe aralığı"nı trendden ayıran, literatürde ayrı bir rejim olarak tanımlanmış değil; en yakın ölçü çok-gecikmeli otokorelasyon / varyans oranıdır.

### Cited Findings
**Baltussen, van Bekkum & Da (2019), "Indexing and stock market serial dependence around the world", JFE 132(1):26–48 (20 endeks, 15 ülke; Nasdaq 100 dahil, seri başlangıcı 1985)**
- Günlük AR(1) katsayıları 1951'den beri ≈ **+0,05** civarındaydı, 1980'lerden beri düşüyor, 2000'lerde işaret değiştirip **negatif** kaldı; haftalık AR(1) 2000'den bile önce negatife döndü — [Notre Dame PDF](https://academicweb.nd.edu/~zda/Indexing.pdf)
- 1999 öncesi pozitif günlük bağımlılık, **bir günlük uygulama gecikmesi** eklenince sıfırdan ayırt edilemiyor (eşzamansız işlem / mikroyapı yanlılığı). 1999 sonrası günlük AR(1) 20 endeksin 16'sında negatif, 7'sinde ve panelde anlamlı negatif (gecikmeli de); haftalık AR(1) **20 endeksin 20'sinde** negatif; günlük p'inci gecikme otokorelasyonları p=1,2,3,5 için anlamlı negatif — [aynı kaynak](https://academicweb.nd.edu/~zda/Indexing.pdf)
- Çok-dönemli otokorelasyon MAC(5) (gecikme 1–4'e 4,3,2,1 ağırlık; varyans oranına eşlenebilir) ile karşı-pozisyon stratejisi: Mart 1999 sonrası tüm endekslerde yıllık Sharpe **0,63**, yalnız S&P 500'de **0,67** (maliyet öncesi); vadeli ve ETF'lerde benzer Sharpe; yazarlar sık yeniden dengeleme nedeniyle **maliyet sonrası birçok yatırımcı için uygulanamayabileceğini** yazıyor — [aynı kaynak](https://academicweb.nd.edu/~zda/Indexing.pdf)
- Önerilen mekanizma: endeks ürünleri (vadeli, ETF, endeks fonları) ve arbitraj; zaman trendi değil, kesitsel ve Nikkei 225 ağırlık / S&P 500 üyeliği testleriyle doğrulandı — [Erasmus repository](https://repub.eur.nl/pub/113320); [CFA Digest 2019](https://rpc.cfainstitute.org/research/cfa-digest/2019/12/dig-v49-n12-3)

**Gün içi (1 saat ufku için en yakın kanıt)**
- Gao, Han, Li & Zhou (2018, JFE "Market intraday momentum"): S&P 500 ETF, 1993–2013; ilk yarım saat getirisi (önceki kapanıştan, yani gece hareketi dahil) **son yarım saat** getirisini öngörüyor; daha **oynak**, yüksek hacimli, resesyon ve makro haber günlerinde daha güçlü; 10 başka aktif ETF'te de var — [WUSTL kaydı](https://profiles.wustl.edu/en/publications/market-intraday-momentum/); [SUFE özet](https://academicnewsletter.sufe.edu.cn/info/356150)
- Aynı çalışmanın 2014 taslağı SPY (1999'dan) ve QQQ (Mart 1999'dan) yarım saatlik getirileri kullanıyor; örneklem-içi R² ≈ 0,02 (yayın öncesi sayı) — [Alpha Architect 2014](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- Heston, Korajczyk & Sadka (2010, JF 65(4):1369–1407) — **tek hisse, fikir kaynağı**: günü 13 yarım saate bölünce, yakın aralıklarla negatif ilişki (alış-satış sıçraması), ama tam gün katlarındaki gecikmelerde (13, 26, 39…) anlamlı **pozitif** süreklilik, en az 40 işlem günü sürüyor; hacim, oynaklık, spread benzer desen gösteriyor ama getiri desenini açıklamıyor; ilk ve son yarım saatte daha belirgin — [arXiv/ar5iv](https://ar5iv.arxiv.org/html/1005.3535)

**Teknik kural evreni, endeks düzeyinde (aralık/trend kurallarının genel kaderi)**
- Sullivan, Timmermann & White (1999, JF 54:1647–1691): White Reality Check ile 100 yıllık günlük DJIA; Brock-Lakonishok-LeBaron kurallarını 1987–1996'ya taşıyınca en iyi kural, maliyet öncesi anlamsız %8,63/yıl üretti; sonraki özetlere göre DJIA, S&P 500 endeksi ve S&P 500 vadelisinde anlamlı kârlı kural yok — [FMG DP303](https://www.fmg.ac.uk/sites/default/files/2020-11/dp303.pdf); [SUFE özet](https://academicnewsletter.sufe.edu.cn/info/361689)
- Aynı çerçeveyi kullanan sonraki bir çalışma (aramada Hsu & Kuan olarak geçiyor; ikincil kopya): "genç" piyasalarda (NASDAQ Composite, Russell 2000) anlamlı kârlı basit kurallar var, "olgun" piyasalarda (DJIA, S&P 500) yok — [ikincil PDF kopyası](https://c.mql5.com/forextsd/forum/211/Re-Examining%20the%20Profitability%20of%20Technical%20Analysis%20with%20Whitets%20Reality%20Check%20and%20Hansen9s%20SPA%20Tes.pdf)

### Inferences
- "Dalgalı aralık sonunda düşüş" anlatısının **sonrasında** literatürün beklediği şey kısa vadeli geri dönüştür (negatif seri bağımlılık + kaldıraç etkisi kaynaklı oynaklık artışı). Bu, düşüşten sonra 1–5 günlük **yükseliş** eğilimi demek; projedeki "düşüş günlerini kazanç izler" bulgusunun dış doğrulaması gibi okunabilir.
- Baltussen'in 1999 öncesi pozitif bağımlılığın **1 günlük gecikmeyle yok olması**, projenin 2. Kural'daki "sonraki bar açılışından gir" ölçütünün neden şart olduğunun yayımlanmış bir örneği: sinyal-barı kapanışından ölçülen otokorelasyon mikroyapı artefaktı olabilir.
- "Dalgalı aralık" ile "trend"i ayırmanın operasyonel yolu: MAC(5) / varyans oranı < 1 (dönüşçü) ile > 1 (trend) karşılaştırması. Ancak Baltussen bunu ortalama özellik olarak ölçüyor; "aralık rejiminde dönüş daha güçlü" diye **koşullu** bir sonuç vermiyor.
- Gao ve ark.'nın "oynak günlerde daha güçlü" bulgusu, tepe-rejiminde gün içi tek kullanılabilir yön ipucunun bu olabileceğini düşündürüyor; ama R² ≈ %2 (yarıya indirilince ≈ %1) ve NAS100'ün 23 saatlik CFD seansında "ilk yarım saat"in karşılığı tanımlanmalı.

### Gaps
- Baltussen tablosundan Nasdaq 100'e özgü günlük/haftalık AR(1) değerleri temiz biçimde çıkarılamadı (PDF tablo düzeni bozuk); yalnız örneklemde olduğu doğrulandı.
- "Dar/dalgalı aralık (konsolidasyon) sonrası" endekste 1–5 günlük getiriyi trend dönemlerine kıyasla test eden hakemli çalışma bulamadım.
- Zaman serisi momentumu (aylık ufuk) bu taramada aranmadı; yalnız bağlam olarak gerekli olabilir.

---

## 4. Yöntem: hangi tabanlar gerekli, hindsight ile seçilmiş örneklerde data-snooping nasıl düzeltilir?

### Takeaway
Bir "tepe formasyonu etkisi"nin gerçek olduğunu iddia etmek için en az üç taban gerekli: (a) aynı **oynaklık** düzeyi (oynaklık kalıcılığı ve kaldıraç etkisi büyük hareketi zaten açıklar), (b) aynı **trend/momentum** düzeyi (Savin'de H&S getirisinin bir kısmı negatif momentumdu), (c) oynaklık kümelenmesini koruyan **plasebo/bootstrap** dağılımı. Kural/parametre evreni için Reality Check / FDR ve t ≥ 3 eşiği; sonuçlar için yayın sonrası %50 civarı aşınma beklentisi. Kullanıcının elle seçtiği 3 örnek **sonuca göre** seçildiği için yalnız tanımı kalibre etmeye yarar, kanıt sayılmaz.

### Cited Findings
- Lo ve ark.'nın tabanı, formasyona **koşullu** günlük getiri dağılımı ile **koşulsuz** dağılım arasındaki farktır (yön değil, dağılım testi) — [NBER w7613](https://www.nber.org/papers/w7613); Savin ve ark. ise bunun teknik analiz iddialarını doğrudan test etmediğini söyleyip işaret/büyüklük testine ve faktör (FF3 + momentum) düzeltmesine geçiyor — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- Savin ve ark.'nda momentum faktörü eklenince H&S etkisi S&P 500'de belirgin küçülüyor (60 günlük, 18–25 bp/ay); yani trend kontrolü olmadan ölçülen "formasyon etkisi" kısmen momentum — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- Osler & Chang: formasyon kârlarını 10.000 bootstrap rassal yürüyüş serisinde aynı algoritmanın ürettiği kâr dağılımıyla kıyasladı (plasebo tabanı) — [IDEAS/RePEc](https://ideas.repec.org/p/fip/fednsr/4.html)
- Greenwood ve ark. (taslak): çöküş olasılığı artışının "yalnızca geçmiş oynaklıktan beklenenin ötesinde" olduğu ayrıca gösterilmiş; yani oynaklık kontrolü açıkça yapılmış — [NBER w23191](https://www.nber.org/system/files/working_papers/w23191/w23191.pdf)
- Sullivan, Timmermann & White (1999): White Reality Check, test edilen **tüm kural evreni** üzerinden veri-gözetleme yanlılığını ölçüp düzeltiyor — [FMG DP303](https://www.fmg.ac.uk/sites/default/files/2020-11/dp303.pdf)
- Bajgrowicz & Scaillet (2012, JFE 106:473–491): DJIA 1897–2011, yanlış keşif oranı (FDR) ile; kalıcılık testleri FDR ile bile yatırımcının gelecekte en iyi çalışacak kuralları **önceden seçemeyeceğini** gösteriyor; düşük işlem maliyetleri **örneklem-içi** performansı bile tamamen siliyor — [IDEAS/RePEc](https://ideas.repec.org:443/a/eee/jfinec/v106y2012i3p473-491.html); [EFMA 2008 sürümü](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2008-Athens/papers/Bajgrowicz.pdf)
- Harvey, Liu & Zhu (2016, RFS 29(1):5–68): yaygın veri madenciliği nedeniyle yeni bir faktörün t-oranı ≈ **3,0**'ı aşması gerekiyor; t > 2,0 eşiğinin ekonomik/istatistiksel gerekçesi yok; testler arası korelasyonu hesaba katan çoklu-test çerçevesi — [NBER w20592](https://www.nber.org/papers/w20592)
- McLean & Pontiff (2016, JF): 97 öngörücüde getiri **örneklem-dışı %26**, **yayın sonrası %58** düşüyor; örneklem-içi getirisi yüksek olanlarda düşüş daha büyük — [Ivey PDF](https://ivey.uwo.ca/media/3775549/pontiff.pdf)
- Christoffersen & Diebold: işaret otokorelasyonu ve runs testi gibi klasik araçlar doğrusal-olmayan yön bağımlılığını kaçırır; takip çalışması yön olasılıklarını **Brier skoru** gibi olasılık-puanlama kurallarıyla değerlendiriyor — [NBER w10009](https://www.nber.org/papers/w10009); [Penn WP 06-016](https://www.econ.upenn.edu/sites/default/files/filevault/working-papers/06-016.pdf)
- Elle seçilmiş örneklere kalibrasyonun doğrudan kanıtı: Savin ve ark.'nda Bulkowski'nin 11 "tipik" örneğine göre ayarlanmış filtreler tespit sayısını %30 azalttı ama öngörü gücüne hiçbir şey katmadı — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- Bulkowski'nin istatistikleri "mükemmel işlemler" üzerine kurulu (ideal giriş/çıkış) — [thepatternsite eedt](https://www.thepatternsite.com/eedt.html)

### Inferences
- **Sonuca göre seçim yanlılığı:** Kullanıcının üç örneği "bir düşüşle bitti" diye seçildi. Bu, bağımlı değişkene göre örneklem seçmektir; isabet oranı tanım gereği %100 görünür. Doğru test: tanımı yalnız t anına kadarki bilgiyle yaz, tüm geçmişte **her** tespiti say (düşüşle bitmeyenler dahil), tanımı test öncesi dondur (ön-kayıt).
- **Oynaklık-eşleştirmeli taban:** Her olay için aynı saat-of-day, aynı gerçekleşen oynaklık kovası (ör. RV 5g desil), aynı zirveye uzaklık kovası (ATR cinsinden) ve aynı önceki 20 günlük trend tercilindeki **formasyonsuz** barlar taban seçilmeli. Aksi halde "formasyon sonrası büyük hareket" yalnız oynaklık kalıcılığıdır (Bölüm 2).
- **Plasebo:** Osler-Chang'ın rassal yürüyüş bootstrap'i oynaklık kümelenmesini yok eder ve yanıltıcı biçimde **kolay** bir taban üretir. Daha uygun olanı blok/durağan bootstrap veya GARCH-dirençli simülasyon; ya da gerçek seride olay tarihlerini rastgele kaydırma (aynı oynaklık rejimi içinde).
- **Simetri kontrolü:** Aynı tanımın ayna versiyonu ("dip yakınında dalgalı aralık, yükselen dipler") da test edilmeli; yalnız ayı versiyonu test edilirse bu, projenin önceki ayı-yanlılığı vakasının (tartışma motoru) yöntemsel karşılığı olur.
- **Ölçek:** Parametre ızgarası (pencere, pivot k, tolerans, eşik) evrenindeki tüm varyantlar sayılıp Reality Check / SPA / FDR uygulanmalı; tek bir "en iyi" konfig raporlanmamalı. t ≥ 3 eşiği + yayın sonrası %50 aşınma varsayımı birlikte kullanılmalı.
- **Olay bağımsızlığı:** 1 saatlik barlarda üst üste binen pencereler aynı epizodu onlarca kez sayar; epizod düzeyinde (ör. tespitten sonra N gün soğuma) birim seçilmeli. Projenin "aylık basamak" testinde de sonuç epizod düzeyinde yazı-tura çıkmıştı.

### Gaps
- Elle/hindsight ile seçilmiş grafik örneklerinin yarattığı seçim yanlılığını özel olarak ölçen bir finans çalışması bulamadım; yukarıdaki öneriler genel veri-gözetleme literatüründen türetildi.
- Oynaklık ve trende **eşleştirilmiş** (matched) taban kullanan bir formasyon çalışması bulamadım; Savin faktör regresyonu, Greenwood oynaklık kontrolü kullanıyor ama ikisi de eşleştirme değil.

---

## 5. NASDAQ-100 1 saatlik barlara uygulanabilir somut tanımlar/testler (kanıt kalitesine göre sıralı) ve beklenen etki büyüklükleri

### Takeaway
En güçlü kanıt, bu rejimlerde **oynaklık ve drawdown riskinin** öngörülebildiği yönünde; en zayıf kanıt, H&S/çift tepe gibi şekil formasyonlarının **yön** öngördüğü yönünde. Önerilen sıralama: (1) gelecek oynaklık/drawdown tahmini, (2) oynaklık-ölçekli pozisyon, (3) düşüş sonrası 1–5 günlük geri dönüş, (4) gün içi ilk-yarım-saat momentumu, (5) zirve yakını + alçalan tepe → drawdown olasılığı, (6) H&S/çift tepe → yön. Yayımlanmış etkileri yarıya indirince (2)–(6)'nın çoğu NAS100 maliyetlerinin sınırında ya da altında kalıyor.

### Cited Findings
(Bu bölümdeki her etki büyüklüğü, ilgili yayımlanmış kaynaktan; "yarıya indirme" McLean & Pontiff'in %58 yayın sonrası aşınmasına dayanıyor — [Ivey PDF](https://ivey.uwo.ca/media/3775549/pontiff.pdf).)
- Kaldıraç etkisi birkaç gün sürüyor (getiri → gelecek oynaklık), ters yön ihmal edilebilir — [BLT 2006, IDEAS](https://ideas.repec.org/a/oup/jfinec/v4y2006i3p353-384.html); S&P 500 vadelisinde 5 dakikalık veride ilk 3 gün güçlü — [CIRANO 2011s-27](https://cirano.qc.ca/en/summaries/2011s-27)
- Oynaklık hedefleme hisse endekslerinde sol kuyruğu azaltıyor, Sharpe'ı artırıyor (yalnız ikincil özet: ≈0,40 → ≈0,48–0,51) — [Harvey ve ark. Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf); [Alpha Architect](https://alphaarchitect.com/volatility-targeting-improves-risk-adjusted-returns/); gerçek zamanlı kazanç tartışmalı — [Cederburg ve ark.](https://www.lehigh.edu/~xuy219/research/COWY.pdf)
- Endekste negatif günlük/haftalık seri bağımlılık; S&P 500 MAC(5) karşı-stratejisi Sharpe 0,67 (maliyet öncesi, 1999 sonrası) — [Baltussen ve ark.](https://academicweb.nd.edu/~zda/Indexing.pdf)
- İlk yarım saat → son yarım saat momentumu, oynak günlerde daha güçlü; taslak R² ≈ 0,02 — [WUSTL](https://profiles.wustl.edu/en/publications/market-intraday-momentum/); [Alpha Architect 2014](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- Hızlı yükseliş + oynaklık/hacim → çöküş olasılığı artar, ortalama getiri değil (sektör, 2 yıl) — [Greenwood ve ark.](https://shleifer.scholars.harvard.edu/publications/bubbles-fama); toplam piyasa çarpıklığı için zayıf güç — [Chen-Hong-Stein](https://nber.org/papers/w7687)
- H&S: tek hissede risk-düzeltmeli ≈%4,8/yıl (60 gün), momentum sonrası 18–25 bp/ay, ham olarak zarar; Lo/Savin tanım kuralları (R1–R9, %1,5 / %4 toleranslar, boyun çizgisi kırılımı, 63 günlük pencere) — [Savin ve ark. WP](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf)
- Zirveye (52 hafta) yakınlık endekste aylık ufukta pozitif getiri öngörüyor — [Li & Yu, SUFE özet](https://academicnewsletter.sufe.edu.cn/info/356820)

### Inferences
Aşağıdaki tanımlar **önerimdir** (literatürden türetildi; parametreler kaynaktan değil). Ortak kurallar: yalnız t'ye kadarki bilgi; pivotlar k bar sonra teyit edildiği anda kullanılabilir; giriş = **sonraki 1s barın açılışı + gerçek spread** (projenin 2. Kural ölçüt 5'i); geçmiş karar anları `_bars_upto.py` ile kurulur; birim = epizod (tespitten sonra ≥ 5 işlem günü soğuma); çıktılar r(+1s), r(+1g), r(+5g), 5 gün içindeki maksimum düşüş (ATR cinsinden), gelecek gerçekleşen oynaklık; taban = aynı saat × RV desili × zirveye uzaklık kovası × 20 günlük trend tercili içindeki formasyonsuz barlar; plasebo = aynı rejim içinde rastgele kaydırılmış olay tarihleri; ayna (dip) versiyonu zorunlu; tüm parametre ızgarası için FDR/Reality Check ve t ≥ 3.

1. **[Kanıt A] T1 — Zirve-yakını oynaklık rejimi → gelecek oynaklık/drawdown (yön DEĞİL).**
   Durum: kapanış son 20 işlem günü zirvesinin ≤ 2×ATR14(1s) altında **ve** RV(son 5 gün)/RV(son 60 gün) ≥ 1,3. Test: HAR tipi regresyon RV(+1g / +5g) ~ RV_g + RV_h + RV_a + negatif-getiri terimi (kaldıraç) + Durum kuklası; ayrıca P(5 gün içinde ≥ 3×ATR düşüş) için lojistik model. Beklenti: Durum kuklası **tek başına** gelecek oynaklık/drawdown'ı anlamlı öngörür, ama HAR + kaldıraç terimi eklendikten sonra katkısı ~0'a yakın olmalı; yön katsayısı ~0. Bu testin değeri, "örneklerden sonra büyük hareket geldi" gözleminin ne kadarının yalnız oynaklık kalıcılığı olduğunu ölçmesi.
2. **[Kanıt A (risk) / B− (getiri)] T2 — Oynaklık-ölçekli pozisyon üstüne katkı testi.**
   Pozisyon ∝ hedef σ / tahmin σ (HAR). Soru: T1 durumunda **ek** küçültme, salt oynaklık ölçeklemenin üstüne sol kuyruğu ya da Sharpe'ı iyileştiriyor mu? Beklenti (yarıya indirilmiş): hisse endeksi Sharpe'ında +0,04–0,05 civarı, esas fayda sol kuyrukta; gerçek zamanlı kazanç Cederburg'a göre güvenilir değil, bu yüzden ön-kayıtlı ileri dönem şart.
3. **[Kanıt B] T3 — Yapının "düşüşle bitmesi" sonrası 1–5 günlük geri dönüş.**
   Tetik: T1 durumu sırasında 1 günlük getiri ≤ −1,5×σ(60g) (veya 1s barlarda son 7 barın toplamı). Çıktı: r(+1g), r(+5g), MAC(5) ağırlıklı (4,3,2,1). Taban: T1 dışında **aynı büyüklükte** düşüşler. Soru: tepe bağlamı, endeksin genel negatif seri bağımlılığını değiştiriyor mu? Beklenti: genel geri dönüş var (Baltussen; S&P 500 maliyet öncesi Sharpe 0,67 → yarıya indirilince ≈0,33, maliyet sonrası daha az); "tepe bağlamı" ek etkisi bilinmiyor, büyük olasılıkla küçük.
4. **[Kanıt B−] T4 — Gün içi momentum, tepe rejimine koşullu.**
   r(son 60 dk, RTH) ~ r(önceki RTH kapanışı → RTH'nin ilk yarım saati sonu; yaz saatinde 13:30–14:00 UTC, kışın 14:30–15:00 UTC) × [T1 durumu]. Beklenti: taslak R² ≈ 0,02 → yarıya indirilmiş ≈ 0,01; "oynak günlerde daha güçlü" bulgusu tepe rejiminde hafif artış öngörür. NAS100 CFD'nin 23 saatlik seansında yalnız RTH saatleri kullanılmalı; projede "saat-of-day büyüklüğü" en iyi öngörücü olduğu için saat sabit etkisi zorunlu kontrol.
5. **[Kanıt C] T5 — Alçalan tepe dizisi + derin geri çekilme (kullanıcının yapısı) → drawdown olasılığı.**
   Fraktal pivot (sol/sağ k=5 bar; k bar gecikmeyle teyit). Koşul: son 3 pivot tepe kesin azalan (H1 > H2 > H3), H1 son 20 gün zirvesinin ≤ 1×ATR altında, aradaki her pivot dip önceki tepeden ≥ 1,5×ATR aşağıda; sinyal anı = H3'ün teyit barı. Çıktı: P(+5g içinde ≥ 3×ATR düşüş), r(+1g), r(+5g). Ayna: yükselen dipler dizisi dip yakınında. Beklenti: Greenwood/Chen-Hong-Stein analojisiyle **drawdown olasılığında** hafif artış olabilir (sektör/hisse, uzun ufuk kanıtı — 5 güne aktarılabilirliği kanıtsız); yön için T1 tabanının üstünde etki beklenmez.
6. **[Kanıt D] T6 — H&S / çift tepe (Lo-Mamaysky-Wang / Savin algoritması, 1s'e uyarlanmış) → yön.**
   Çekirdek regresyonla yumuşatma, kayan pencere n (ör. 63–150 bar; ızgarada), uç noktalar E1..E5; Lo kuralları R1–R5 (yüzde tolerans yerine 0,5×ATR kullanılabilir) veya Savin R4a/R5a + R6–R9; **boyun çizgisi kırılımı** şart; giriş kırılımı tespit eden barın **sonraki** açılışı. Çift tepe önerisi: iki pivot tepe aralarında ≥ 20 bar, yükseklik farkı ≤ 0,5×ATR, aradaki dip ≥ 1,5×ATR aşağıda, teyit = o dibin altında 1s kapanış. Beklenti: Savin'in tek hisse sonucu ham yönde **ters** (zarar), risk-düzeltmeli ≈0,4%/ay (60g) → yarıya indirilip 5 güne orantılanınca birkaç bp; 1s–5g ufkunda NAS100 maliyetinin altında. Bu test yalnız "kullanıcı sezgisini kapatmak" için değerli; önceden başarısızlık beklenir.

Diğer çıkarımlar:
- Projenin mevcut bulgularıyla uyum: "mum şekli benzerliği yön vermiyor" ↔ T6 beklentisi; "saat-of-day büyüklüğü en iyi öngörücü" ↔ Heston ve ark. aynı-saat sürekliliği + oynaklık periyodikliği; "korku döner" ↔ T3 (Baltussen) ve kaldıraç etkisi; "aylık basamak sonrası yazı-tura" ↔ Li & Yu (zirve yakını ortalamada olumlu) ve Greenwood (ortalama getiri değil, kuyruk riski değişir).
- Kart tasarımı: T1/T5'in çıktısı **risk** kartıdır (ör. pozisyon küçült, SL genişlet/daralt kararı), yön kapısı değil. Go-live kartının 6 ölçütü (≥150 olay, P(EV>0) ≥ %90 vb.) yalnız T3/T4/T6 gibi yön iddiası taşıyan testlere uygulanır; T1/T5 için karşılığı "risk tahmininde HAR tabanına göre örneklem-dışı kayıp-fonksiyonu (QLIKE/Brier) iyileşmesi" olmalı.

### Gaps
- Yukarıdaki parametreler (2×ATR, 1,3 RV oranı, k=5, 1,5×ATR, 20 bar) hiçbir yayından alınmadı; ön-kayıt sırasında ızgara olarak tanımlanıp çoklu test düzeltmesine dahil edilmeli.
- NASDAQ-100'e özgü yayımlanmış etki büyüklüğü (seri bağımlılık katsayısı, gün içi momentum R²'si) bu taramada tam metinden çıkarılamadı; S&P 500 / SPY değerleri vekil olarak verildi.
- 1 saatlik ufukta tepe formasyonlarını endekste ölçen hiçbir hakemli çalışma bulunamadığı için T5/T6'nın 1s beklentileri tamamen çıkarıma dayanıyor.
