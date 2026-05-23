# DAY STRUCTURE ALGORITMIK TRADING SISTEMI: Kapsamli Arastirma ve Uygulama Rehberi

## TL;DR (Kisa Ozet)

Day Structure algoritmik trading sistemi, bir trading gunu icerisinde olusan **en yuksek (Day High) ve en dusuk (Day Low)** seviyeleri, **onceki gunun (PDH/PDL) ve haftanin (PWH/PWL) referans seviyelerini**, **Pivot noktalarini (R1/R2/S1/S2)**, **son saatlerde fiyatin dondugu yerleri (Swing Highs/Lows)**, **trend kanalini** ve **"fiyat buraya 3 kez geldi, oradan dondu" hafizasini** entegre eden butunlesik bir analiz cercevesidir. Bu sistem, **ATR (Average True Range)** bazli **sapma paylari (tolerance thresholds)** ile birlikte calisir ve **Break-Retest-Confirmation** mekanizmasi uzerine kuruludur. Python implementasyonunda **scipy.signal.argrelextrema** ile swing tespiti, **VWAP (Volume Weighted Average Price)** ile hacim agirlikli ortalama analizi, **lineer regresyon** ile trend kanali tespiti ve **kumulatif dokunma sayisi** ile fiyat hafizasi algoritmalari kullanilir. Sistem, **multi-timeframe confluence** (coklu zaman dilimi uyumu) prensibiyle calisir ve **piyasa rejimi tespiti (trending/ranging/volatile)** ile adaptif hale getirilebilir. Backtesting icin **VectorBT** kutuphanesi onerilir. Kullanici tarafindan istenen tum bilesenler (gunluk high/low, haftalik referanslar, pivot noktalari, swing tespiti, trend kanali ve fiyat hafizasi) bu sistemde karsilanmaktadir.

---

## 1. DAY STRUCTURE ANALIZI: TEMEL KAVRAMLAR VE TEORIK CERCEVE

### 1.1 Day Structure Nedir ve Neden Onemlidir?

Day Structure (Gun Yapisi), bir finansal enstrumanin **tek bir trading gunu icerisindeki fiyat hareketlerinin orgusel yapisi**ni inceleyen analiz yontemidir. Bu yapi, piyasanin o gun icerisindeki **psikolojik durumunu, katilimci davranislarini ve likidite dagilimini** ortaya koyar. Day Structure analizi, yalnizca teknik seviyelerin tespiti degil, ayni zamanda **piyasanin "hafizasini"** anlamaya calisan butuncul bir yaklasimdir. Bir borsa gunu acildiginda, piyasa katilimcilari (bireysel yatirimcilar, kurumsal fonlar, algoritmik trading sistemleri) cesitli referans noktalari uzerinden kararlarini verirler. Bu referans noktalari, **onceki gunun en yuksek ve en dusuk seviyeleri**, **haftanin kritik seviyeleri**, **hesaplanmis destek ve direncleri** ve **fiyatin son donemde tekrar tekrar yon degistirdigi yerleri** icerir. Bu nedenle, Day Structure analizi, bir gunluk trading faaliyetinin **iskeletini** olusturan kritik yapilarin sistematik olarak tespit edilmesi surecidir [^15^].

Gun yapisi analizinin onemi, piyasanin **belirgin davranis kaliplari gosterme egiliminde oldugu kritik bolgeleri** ortaya cikarmasindan kaynaklanir. Ornegin, **Onceki Gunun En Yuku (Previous Day High - PDH)** ve **Onceki Gunun En Dusugu (Previous Day Low - PDL)** piyasada yaygin olarak bilinen ve takip edilen iki temel referans noktasidir. Fiyat bu seviyelere ulastiginda, piyasa katilimcilarinin psikolojik olarak tepki verme olasiligi yukselir. Eger fiyat PDH'nin uzerine cikarsa, bu genellikle **yukari yonlu bir kiranin (breakout)** gerceklestigine dair bir sinyal olarak yorumlanir ve piyasanin daha yuksek seviyeleri hedefleyebilecegi dusunulur. Aksine, fiyat PDL'nin altina duserse, **asagi yonlu bir kiranin** isaretidir ve satis baskisinin arttigi yorumlanir [^14^], [^16^]. Bu seviyeler, **self-fulfilling prophecy (kendini gerceklestiren kehanet)** ozelligi tasirlar; cunku cok sayida trader bu seviyeleri izledigi icin, bu seviyelerde onemli hacimli islemler gerceklesir ve fiyat bu noktalarda gercekten tepki verir [^15^].

Day Structure analizi ayrica, gun ici fiyat hareketlerinin **karmaasasindan duzen cikarmayi** hedefler. Piyasa, gun boyunca surekli olarak yukari ve asagi hareketler yapar. Ancak bu hareketlerin tamami esit oneme sahip degildir. Bazi hareketler, **ana trendin bir parcasidir**; bazilari ise **karsit trend (corrective) hareketler** veya **"gurultu" (noise)** olarak degerlendirilebilir. Day Structure, gun icerisindeki **en yuksek ve en dusuk seviyeleri**, **fiyatin donus yaptigi onemli noktalari (swing points)** ve **bu noktalari birlestiren trend cizgilerini** belirleyerek, gunluk hareketin ana yapici taslarini ortaya cikarir. Bu yapici taslar, gun ici trading kararlarinin temelini olusturur. Ornegin, gun ici en yuksek seviyenin kirilmasi, gunun geri kalaninda yeni bir yukari trendin basladigini gosterebilirken, gunun ilk yarisinda olusan bir destek seviyesinin kirilmasi, gunluk trendin zayifladiginin bir isareti olabilir. Bu baglamda, Day Structure analizi, **gunluk trading stratejilerinin bel kemigini** olusturan yapisal bir cerceve saglar [^28^], [^66^].

### 1.2 Algoritmik Trading Acisindan Day Structure

Algoritmik trading sistemleri icin Day Structure, **nesnel ve tekrarlanabilir karar kurallari** olusturmak acisindan paha bicilmez bir kaynaktir. Insan traderlarinin sezgisel olarak yaptigi analizler (ornegin, "fiyat onceki gunun en yukseginde takildi gibi gorunuyor"), algoritmik sistemlerde **matematiksel kosullar** ifade edilebilir. Bu donusum, trading kararlarinin **tutarliligi ve objektifligi**ni buyuk olcude artirir. Algoritmik bir sistem, her gun ayni kural setini uygulayarak, **insan psikolojisinden kaynaklanan hatalari** (asiri given, korku, ac gozluluk) elimine eder. Day Structure bilesenlerinin (PDH, PDL, pivotlar, swing noktalari) hepsi **gecmis fiyat verilerinden hesaplanabilir** olduklari icin, bir algoritma tarafindan otomatik olarak tespit edilmeleri ve trading kararlarinda kullanilmalari son derece kolaydir [^37^], [^42^].

Algoritmik sistemler, Day Structure'i **multi-timeframe analiz** ile birlestirerek daha saglam sinyaller uretebilir. Sistem, **gunluk (daily) grafikte** PDH/PDL gibi ana referanslari belirleyebilirken, **daha dusuk zaman dilimlerinde** (ornegin 15, 5 veya 1 dakikalik grafikler) bu seviyelere yaklasildiginda veya kirildiginda **giriste (entry) ve cikista (exit)** hassasiyeti saglayabilir [^39^]. Ornegin, bir algoritma gunluk grafikte yukari yonlu bir trendin varligini tespit ettikten sonra, 5 dakikalik grafikte fiyatin PDH'yi kiridiktan sonra geri donup bu seviyeyi bir destek olarak **retest etmesini** bekleyebilir. Bu retest sirasinda belirli bir **onay (confirmation)** meydana geldiginde (ornegin, bir sonraki mumun yesil kapanmasi), algoritma long pozisyon acabilir. Bu tur bir yaklasim, **yanlis kiralardan (false breakouts)** kaynaklanan zararlari onemli olcude azaltir [^5^], [^35^].

Day Structure'in algoritmik tradingdeki bir diger kritik rolu, **risk yonetimi** acisindan oynanir. Algoritmik sistemler, stop-loss ve take-profit seviyelerini Day Structure'in sundugu yapisal seviyelere gore **dinamik olarak ayarlayabilir**. Ornegin, PDH uzerinde bir long islem acildiginda, stop-loss seviyesi dogrudan PDH seviyesinin biraz altina konabilir. Cunku eger fiyat PDH'yi yeniden asagi yonde kirarsa, bu durum kiranin gecersiz oldugunu ve fiyatin daha dusuk seviyelere gerilemek isteyebilecegini gosterir. Benzer sekilde, kar hedefleri de bir sonraki gunluk direnc seviyesine veya R1/R2 pivot noktalarina gore belirlenebilir. Bu yontem, **risk/odul oraninin (risk/reward ratio)** her islem icin onceden bilinmesini ve kontrol edilmesini saglar. Ayrica, sistem gun icerisinde olusan **yeni swing high ve low'lari** takip ederek trailing stop-loss'u dinamik olarak guncelleyebilir, boylece kazanc elde edilen bir pozisyonun korunmasina yardimci olur [^3^], [^59^].

### 1.3 Kullanici Isteklerinin Sistemle Karsilastirilmasi

Kullanici tarafindan iletilen istekler, bu Day Structure algoritmik sisteminin temelini olusturmaktadir ve her bir bilesen, arastirma sonucunda elde edilen bilgilerle dogrudan karsilanabilmektedir. Asagida kullanici istekleri ile sistem bilesenleri arasindaki eslestirme ayrintili olarak sunulmustur:

**Istenen Bilesen: "Bugunun High/Low'u (Day High / Day Low)"**
Bu istek, Day Structure'in en temel ve ilk bilesenidir. Sistem, trading gunu icerisinde gerceklesen en yuksek ve en dusuk fiyatlari surekli olarak takip eder. Bu seviyeler, gunun volatilitesini olcmek, gunluk fiyat araligini (daily range) belirlemek ve gun ici diger seviyelerin (ornegin, pivot noktalarinin hesaplanmasi icin) hesaplanmasi icin temel veri saglar. Algoritmik sistem, bu seviyelere ulasildiginda veya kirildiginda aninda sinyal uretebilir. Ornegin, gun ici en yuksek seviyenin kirilmasi, yukari yonlu bir ivme kazanildiginin onemli bir gostergesidir [^1^], [^62^].

**Istenen Bilesen: "Dun ve haftanin referans seviyeleri"**
Bu istek, **PDH (Previous Day High)**, **PDL (Previous Day Low)**, **PWH (Previous Week High)** ve **PWL (Previous Week Low)** seviyelerini kapsar. Bu seviyeler, piyasanin "hafizasinda" yer eden ve cok sayida katilimci tarafindan takip edilen kritik referans noktalardir. PDH ve PDL, bir onceki gunun fiyat kesif surecinin ust ve alt sinirlarini temsil eder ve yeni gunun acilisinda piyasa yonunun belirlenmesinde kilit rol oynar [^15^]. Haftalik seviyeler ise daha buyuk resmi gosterir ve gunluk hareketin bu haftalik cerceve icinde nereye oturdugunu anlamak icin kullanilir. Algoritmik sistem, bu seviyeleri otomatik olarak hesaplar ve fiyatin bu seviyelere olan uzakligini veya etkilesimini (dokunma, kirilma, retest) surekli olarak monitorler [^19^].

**Istenen Bilesen: "Pivot noktalari (R1/R2/S1/S2)"**
Pivot noktalari, **Floor Trader's Formula** olarak da bilinen matematiksel bir yontemle onceki gunun yuksek, dusuk ve kapanis fiyatlarindan hesaplanan onceden belirlenmis destek ve dirench seviyeleridir. **PP (Pivot Point)** ana direnc veya destek olarak kabul edilirken, **R1, R2 (Resistance 1, 2)** yukari yonlu direnc seviyelerini ve **S1, S2 (Support 1, 2)** asagi yonlu destek seviyelerini temsil eder. Bu seviyeler, gun boyunca potansiyel donus veya duraklama noktalarini tahmin etmek icin kullanilir ve algoritmik sistem tarafindan gun basinda hesaplanarak tum gun boyunca referans alinir [^1^], [^2^], [^6^].

**Istenen Bilesen: "Son saatlerde fiyatin 'dondugu' yerler (swing highs/lows)"**
Bu istek, **argrelextrema** gibi algoritmik yontemlerle tespit edilen **lokal maksimum (swing high)** ve **lokal minimum (swing low)** noktalarini ifade eder. Bu noktalar, fiyatin yon degistirdigi yerlerdir ve trendin yapici taslarini olusturur. Bir dizi **yuksek tepeler ve yuksek dipler (higher highs & higher lows)** yukselen bir trendi, **dusuk tepeler ve dusuk dipler (lower highs & lower lows)** ise dusen bir trendi gosterir. Algoritmik sistem, bu swing noktalarini kullanarak trend yonunu belirler ve bu noktalardan gecen cizgiler ile **dinamik destek ve direncler** tanimlayabilir. Ayrica, bu seviyeler fiyat hafizasi algoritmasinin da temelini olusturur [^20^], [^21^], [^26^].

**Istenen Bilesen: "Trend kanali (yukselen/dusen, ust-alt sinir)"**
Trend kanali, bir dizi swing high veya swing low noktasindan gecirilen **lineer regresyon** veya **en kucuk kareler yontemi** ile cizilen paralel cizgilerden olusur. Kanalin orta cizgisi trendin yonunu gosterirken, ust ve alt bantlari fiyatin istatistiksel olarak hareket etmesi beklenen araligi tanimlar. Algoritmik sistem, bu kanallari hesaplayarak fiyatin kanalin neresinde oldugunu belirler. Kanalin ust bandina yaklasma **asiri alim (overbought)**, alt bandina yaklasma ise **asiri satim (oversold)** olarak yorumlanabilir. Trend kanali, fiyatin mevcut trende ne kadar saptigini olcmek icin de kullanilir [^22^], [^27^], [^32^].

**Istenen Bilesen: "'Fiyat daha once buraya 3 kez geldi, oradan dondu' hafizasi"**
Bu istek, **Price Memory (Fiyat Hafizasi)** algoritmasinin ozet bir tanimidir. Bu algoritma, belirli bir fiyat bolgesine (seviyesine) fiyatin belirli bir gecmis donem icinde kac kez gelip dondugunu (veya destek/direnc olarak davrandigini) sayar. Eger bir fiyat seviyesi (ornegin 150.00) son 50 mumda 3 veya daha fazla kez test edilip her seferinde guclu bir tepki almisse, bu seviye "guclu bir hafiza bolgesi" olarak siniflandirilir. Algoritmik sistem, bu tur bolgeleri tespit ederek, fiyat bu bolgeye tekrar geldiginde **yuksek olasilikli bir tepki** beklentisiyle islem stratejisi olusturabilir. Bu, piyasanin kollektif hafizasinin bir olcusudur ve insan gozunun kolayca kacirabilecegi, ancak algoritmik olarak guclu bir istatistiki avantaj saglayan bir bilesendir [^8^], [^38^], [^41^].

Asagidaki tablo, kullanici istekleri ile sistem bilesenleri, algoritmik yontemleri ve pratik uygulamalari arasindaki iliskiyi ozetlemektedir:

| Kullanici Istegi | Sistem Bileseni | Algoritmik Yontem | Pratik Uygulama |
|---|---|---|---|
| Bugunun H/L | Gunluk Range | `df['high'].max()`, `df['low'].min()` | Volatilite olcumu, gunluk ATR hesabi [^59^] |
| Dun ve Haftanin Referanslari | PDH, PDL, PWH, PWL | Onceki period high/low kaydi | Gun acilis biasi, krilma/retest seviyeleri [^15^] |
| Pivot Noktalari (R1/R2/S1/S2) | Pivot Seviyeleri | `(H+L+C)/3` formulu | Onceden hesaplanmis gunluk destek/direncler [^1^] |
| Swing Highs/Lows | Yerel Ekstremumlar | `scipy.signal.argrelextrema` | Trend yapi tasi, dinamik S/R tespiti [^20^] |
| Trend Kanali | Regresyon Kanali | `numpy.polyfit` (Lineer Regresyon) | Trend yonu, asiri alim/satim bolgeleri [^22^] |
| Fiyat Hafizasi (3x Dokunma) | Hafiza Bolgeleri | Kumulatif dokunma sayaci + tolerans zonu | Yuksek olasilikli donus/durus noktalari [^8^] |

Yukaridaki tablo, kullanici tarafindan istenen her bir bilesenin bu Day Structure sisteminde nasil karsilandigini ve her birinin algoritmik olarak nasil tespit edilip trading kararlarina nasil entegre edildigini acikca gostermektedir. Bu butunlesik yaklasim, piyasanin farkli boyutlarini (gecmis referanslar, istatistiksel seviyeler, trend yapisi ve davranissal hafiza) tek bir analiz cercevesinde birlestirerek, **daha saglam ve yuksek olasilikli trading sinyalleri** uretmeyi hedefler.

## 2. REFERANS SEVIYE TESPITI: PDH, PDL VE HAFTALIK SEVIYELER

### 2.1 Onceki Gun En Yuksek/En Dusuk (PDH/PDL) Tespiti ve Stratejik Onemi

**Previous Day's High (PDH)** ve **Previous Day's Low (PDL)**, algoritmik Day Structure sisteminin temel taslarini olusturan ve piyasa katilimcilari tarafindan en yaygin sekilde takip edilen referans seviyelerdir. Bu seviyeler, bir onceki trading gununun fiyat kesif surecinin ust ve alt sinirlarini temsil ederler ve piyasa psikolojisi acisindan buyuk oneme sahiptirler. PDH, bir onceki gun alicilarin en yuksek fiyati odemeye razi oldugu seviye olup, yeni bir gunde bir **direnc** olarak islev gorur. Tersine, PDL, satıcıların en dusuk fiyati kabul ettigi seviye olup, yeni gunde bir **destek** olarak kabul edilir [^15^]. Algoritmik sistemler icin bu seviyelerin tespiti oldukca basittir; sadece bir onceki gunun fiyat verilerinden en yuksek ve en dusuk degerlerin cekilmesi yeterlidir. Ancak bu basit tespitin stratejik uygulamalari cok daha karmasiktir ve **coklu zaman dilimi analizi (multi-timeframe analysis)** gerektirir [^14^], [^16^].

PDH ve PDL'nin stratejik onemi, bu seviyelerin **"likidite havuzlari" (liquidity pools)** veya **"buz daglari" (icebergs)** olarak gorulmesinden kaynaklanir. Buyuk kurumsal yatirimcilar ve algoritmik sistemler, bu yaygin olarak bilinen seviyelerin hemen altina (PDH icin) veya ustune (PDL icin) buyuk hacimli emirler yerlestirebilirler. Bu durum, fiyatin bu seviyelere ulastiginda sert bir sekilde geri donmesine veya bu seviyelerin kirilmasi durumunda guclu bir momentum hareketinin baslamasina neden olabilir. Bu nedenle, algoritmik bir sistem sadece fiyatin PDH veya PDL'ye dokundugunda hareket etmez. Bunun yerine, bu seviyelerdeki **fiyat davranisini (price action)** dikkatle inceler. Ornegin, fiyat PDH'ye hizla yaklasir ve bu seviyede **uzun bir fitil (long wick)** olusturarak geri donerse, bu durum guclu bir **"reddetme" (rejection)** sinyalidir ve algoritma bir short pozisyon dusunebilir. Eger fiyat PDH'yi bir mumda guclu bir sekilde kirar ve uzerinde kapanis yaparsa, bu bir **"kirilma" (breakout)** sinyalidir ve sistem bir long pozisyon acabilir [^3^], [^28^].

Algoritmik tradingde PDH ve PDL'nin kullanimi, **"gucsuzluk" (weakness)** ve **"guc" (strength)** kavramlari uzerine kuruludur. Eger fiyat, PDH'nin uzerine cikar ancak bu seviyenin ustunde kalamaz ve hizla geri duserse, bu durum "PDH uzerinde gucsuzluk" olarak yorumlanir. Bu, yukari yonlu hareketin tukendigine ve satislarin baskin hale gelebilecegine dair erken bir uyaridir. Benzer sekilde, fiyat PDL'nin altina inse de bu seviyenin altinda tutunamazsa, bu "PDL altinda gucsuzluk" olarak degerlendirilir ve bir yukselis olasiligi dusunulebilir. Bu analizi yapmak icin algoritmik sistemler, PDH/PDL seviyelerine yaklasildiginde daha dusuk zaman dilimlerine (ornegin 5 veya 1 dakikalik) gecerek, mum yapisi (candlestick patterns), hacim ve momentum gostergeleri (ornegin RSI/MACD diverjanslari) ile birlikte bir **confluence (uyum)** ararlar [^14^]. Bu coklu dogrulama mekanizmasi, yanlis sinyalleri filtreleyerek islem basarisini artirir. Ornegin, PDH uzerinde bir gucsuzluk sinyali, gunluk grafikte yuksek zaman dilimli bir direnc bolgesiyle birlesiyorsa, bu short islemin olasiligi daha da guclenir.

### 2.2 Haftalik En Yuksek/En Dusuk (PWH/PWL) Referanslari

Gunluk referans seviyeleri (PDH/PDL) kadar yaygin olarak kullanilmamakla birlikte, **Onceki Haftanin En Yuku (Previous Week High - PWH)** ve **Onceki Haftanin En Dusugu (Previous Week Low - PWL)** degerleri, ozellikle **swing trading** ve **konum trading** stratejileri icin kritik oneme sahip referans noktalardir. Bu seviyeler, piyasanin daha genis zaman cercevesindeki (weekly timeframe) yapisini anlamak icin bir anahtar sunarlar. PWH ve PWL, bir onceki haftanin tum fiyat hareketini kapsayan ust ve alt sinirlardir ve bu nedenle, gunluk hareketlere kiyasla daha "agir" ve daha az sik kirilan seviyeler olarak kabul edilirler. Bu seviyelerin kirilmasi, genellikle daha guclu ve daha uzun soluklu bir trend degisikliginin habercisi olarak yorumlanir [^19^].

Algoritmik bir Day Structure sistemi, PWH ve PWL'yi **gunluk stratejiye baglamak (contextualize)** icin kullanir. Ornegin, eger gunun ilk yarisinda fiyat PWH'ye yaklasyorsa, bu bir **"haftalik direnc"** olarak gorulur ve piyasanin bu seviyede zorlanmasi beklenir. Bu durumda, sistem gunluk PDH seviyeleriyle birlikte PWH'yi de bir dirench bolgesi olarak tanimlayabilir. Eger fiyat PWH'yi kirarsa, bu durum "haftalik kiranin" gerceklestigi anlamina gelir ve sistem gunluk hedeflerin otesinde, daha yuksek zaman dilimli hedeflere (ornegin, aylik direncler veya Fibonacci genislemeleri) yonelmeyi dusunebilir. Bu tur bir analiz, **ic ice gecmis zaman dilimleri (nested timeframes)** prensibine dayanir; gunluk hareket, haftalik yapinin icinde, haftalik hareket ise aylik yapinin icinde gerceklesir. Bu butunluk, islem kararlarinin daha saglam bir temele oturmasini saglar [^39^], [^43^].

PWH ve PWL'nin bir diger onemli kullanim alani, **"haftalik araligin" (weekly range)** analizidir. Bir haftanin PWH ve PWL'si arasindaki mesafe, o haftanin volatilitesinin bir olcusudur. Algoritmik sistem, mevcut gunun fiyat hareketinin bu haftalik araliga gore nerede oldugunu degerlendirebilir. Ornegin, eger fiyat haftanin basindan beri PWL'ye yakin seyrediyor ve hafta ortasinda bu seviyeden bir donus sinyali gosteriyorsa, sistem bu seviyenin haftalik anlamdaki onemini goz onunde bulundurarak bir long pozisyon degerlendirebilir. Bu analiz, gunluk hareketlerin "gurultu" oldugu durumlarda, daha buyuk resmi gormeye yardimci olarak traderi gunluk dalgalanmalarin yaniltici etkisinden korur. Ozellikle **Cuma gunu kapanisi** ve **Pazartesi gunu acilisi** gibi haftalik gecis donemlerinde, PWH ve PWL seviyeleri, haftalik trendin devam edip etmeyecegine dair onemli ipuclari verir. Bir hafta PWH uzerinde kapanis yaparsa, bu sonraki hafta icin guclu bir yukari bias olusturabilir [^19^].

### 2.3 Algoritmik Tespit ve Gunluk Acilis Bias Belirleme

PDH, PDL, PWH ve PWL gibi referans seviyelerin algoritmik tespiti, veri isleme acisindan oldukca basit bir surectir. Sistem, gecmis gunluk ve haftalik verilere erisim sagladiginda, bu degerleri dogrudan `max()` ve `min()` fonksiyonlari ile hesaplayabilir. Asil zorluk, bu seviyelerden elde edilen bilginin **gunluk acilista bir "bias" (egilim)** olarak nasil yorumlanacagina karar vermektir. Gunluk bias, piyasanin o gun yukari mi yoksa asagi mi egilimli olacagina dair bir ongorudur ve algoritmik sistemlerin gun boyunca hangi yonde islem arayacagini belirler. Bu bias belirleme sureci, sadece PDH/PDL'nin kirilip kirilmamasina degil, ayni zamanda **piyasanin bu seviyelere olan mesafesine, gunluk acilis fiyatina ve acilis sonrasi ilk birkac mumun yapisina** (opening range) da baglidir [^14^], [^63^].

Gunluk bias belirleme mantiginin temelini **"PDH/PDL kiranin onaylanmasi"** olusturur. Algoritmik sistem, gunun ilk saatlerinde (ornegin, ilk 15-30 dakikalik opening range periyodu) piyasanin bu kritik seviyelere nasil davrandigini gozlemler. Eger gunun acilisi PDH'nin uzerinde gerceklesir ve ilk mumlar bu seviyenin uzerinde guclu kapanislar yaparsa, sistem otomatik olarak bir **"yukari bias"** olusturur. Bu durumda, sistem gun boyunca PDH'nin uzerindeki bolgelerde **long (alim)** firsatlari arar. Tersi durumda, acilis PDL'nin altinda ve ilk hareketler bu seviyenin altinda guclenirse, bir **"asagi bias"** olusur ve sistem short (satis) islemlerine odaklanir. Bu yaklasim, **"opening range breakout"** stratejisiyle de ortusur; yani gunun ilk belli bir dakikasindaki araligin kirilmasi, gunun genel yonu hakkinda onemli bir ipucu verir [^64^], [^66^].

Daha gelismis bir bias belirleme algoritmasi, sadece acilisi degil, ayni zamanda **"fiyatin PDH/PDL'ye olan uzakligini"** ve **"mevcut trend yapisiyla olan iliskisini"** de goz onunde bulundurur. Ornegin, bir algoritma su sekilde calisabilir:
1.  **Trend Analizi:** Gunluk grafikte mevcut trend yukari ise (ornegin, fiyat 20 gunluk hareketli ortalamanin uzerinde), sistemin baslangictaki yukari bias'i daha guclu olur.
2.  **Mesafe Analizi:** Eger gunun acilisi, PDH'nin hemen altindaysa ve piyasa hacimli bir sekilde bu seviyeyi kirarsa, bu cok guclu bir yukari bias sinyalidir.
3.  **Confluence:** Eger PDH seviyesi, ayni zamanda haftalik bir direncle (PWH) veya onemli bir psikolojik seviye ile (ornegin 150.00) cakisiyorsa, bu seviyenin kirilmasi cok daha onemli bir sinyal olarak degerlendirilir.
4.  **Gunluk Pivot:** Acilis fiyati, gunluk Pivot Point (PP) seviyesinin uzerindeyse bu yukari bias'i, altindaysa asagi bias'i guclendirir.

Bu faktorlerin hepsini birlestiren bir algoritma, gunluk bias'i bir **skorlama sistemi** ile ifade edebilir. Ornegin, yukari yondeki her bir sinyal (trend yukari, PP uzeri, PDH kirilimi vb.) belirli bir puan eklerken, asagi yondeki sinyaller puan cikarir. Sonucta pozitif bir skor, yukari bias'i; negatif bir skor ise asagi bias'i temsil eder. Bu skor, sistem gun boyunca ne tur islemler aramasi gerektigine dair bir rehber gorevi gorur ve **"long-only"**, **"short-only"** veya **"nötr/bekle"** modlarindan birine girmesini saglar. Bu tur bir sistematik yaklasim, duygusal kararlari ortadan kaldirir ve her gun icin tutarli bir analiz cercevesi saglar [^35^], [^74^].

## 3. PIVOT NOKTALARI: MATEMATIKSEL HESAPLAMA VE ALGORITMIK UYGULAMA

### 3.1 Standart (Floor Trader) Pivot Noktalari Formulleri

Pivot noktalari, ozellikle gunluk (intraday) tradingde yaygin olarak kullanilan, **onceden belirlenmis potansiyel destek ve direnc seviyeleridir**. Bu seviyelerin en klasik ve en cok bilineni **Standart (veya Floor Trader) Pivot Noktalari**dir. Bu yontem, bir onceki trading gununun **en yuksek (High)**, **en dusuk (Low)** ve **kapanis (Close)** fiyatlarini kullanarak o gun icin yedi farkli seviye hesaplar: bir ana Pivot Point (PP), uc dirench (R1, R2, R3) ve uc destek (S1, S2, S3). Bu formullerin temel mantigi, bir onceki gunun fiyat araliginin (High - Low) ve dengenin (PP) yeni gun icin bir haritasini cikarmaktir. Piyasa katilimcilari tarafindan bu kadar yaygin olarak takip edilmeleri, bu seviyeleri bir nevi **"kendini gerceklestiren kehanet" (self-fulfilling prophecy)** haline getirmistir; cunku cok sayida emir bu seviyelerin etrafinda toplanir [^1^], [^6^].

Standart pivot noktalari formulleri asagidaki gibi tanimlanir:

1.  **Ana Pivot Point (PP)**: Onceki gunun yuksek, dusuk ve kapanis fiyatlarinin aritmetik ortalamasidir. PP, o gun icin ana bir donus noktasi veya trendin belirlendigi kritik bir esik olarak gorulur. Fiyat PP'nin uzerindeyse genel egilim yukari kabul edilirken, altindaysa asagi egilim hakimdir.
    *   **Formul: PP = (Onceki Gunun High + Onceki Gunun Low + Onceki Gunun Close) / 3**

2.  **Birinci Dirench (R1)**: Ana pivot noktasi ile onceki gunun en dusuk seviyesi arasindaki mesafenin, pivot noktasina eklenmesiyle bulunur. R1, fiyatin yukselisinde karsilasabilecegi ilk onemli direnc olarak kabul edilir.
    *   **Formul: R1 = (2 x PP) - Onceki Gunun Low**

3.  **Ikinci Dirench (R2)**: Ana pivot noktasina, onceki gunun fiyat araliginin (High - Low) tamami eklenerek hesaplanir. R2, ilk direncten daha guclu bir engel olarak degerlendirilir ve fiyat burada daha sert bir tepkiyle karsilasabilir.
    *   **Formul: R2 = PP + (Onceki Gunun High - Onceki Gunun Low)**

4.  **Ucuncu Dirench (R3)**: Onceki gunun en yuksek seviyesine, ana pivot ile onceki gunun en dusuk seviyesi arasindaki mesafenin iki kati eklenerek bulunur. R3, gunluk volatilenin cok yuksek oldugu durumlarda test edilebilecek uzak bir hedeftir.
    *   **Formul: R3 = Onceki Gunun High + 2 x (PP - Onceki Gunun Low)**

5.  **Birinci Destek (S1)**: Ana pivot noktasindan, onceki gunun en yuksek seviyesi ile pivot arasindaki mesafenin cikarilmasiyla elde edilir. S1, dusus hareketinde fiyat icin ilk guvenlik agi olarak islev gorur.
    *   **Formul: S1 = (2 x PP) - Onceki Gunun High**

6.  **Ikinci Destek (S2)**: Ana pivot noktasindan, onceki gunun fiyat araliginin (High - Low) tamami cikarilarak bulunur. S2, ilk destek kirildiginda fiyat icin bir sonraki onemli zemin olarak kabul edilir.
    *   **Formul: S2 = PP - (Onceki Gunun High - Onceki Gunun Low)**

7.  **Ucuncu Destek (S3)**: Onceki gunun en dusuk seviyesinden, ana pivot ile onceki gunun en yuksek seviyesi arasindaki mesafenin iki kati cikarilarak hesaplanir. S3, cok siddetli bir satis baskisi altinda test edilebilecek son bir destektir.
    *   **Formul: S3 = Onceki Gunun Low - 2 x (Onceki Gunun High - PP)**

Bu hesaplamalarin algoritmik olarak uygulanmasi son derece basittir. Sistem, her gun trading saatleri baslamadan once, bir onceki gunun OHLC (Open, High, Low, Close) verilerini kullanarak bu yedi seviyeyi hesaplar ve bu seviyeleri o gun boyunca referans olarak kullanir. Bu seviyeler, otomatik olarak grafige yatay cizgiler olarak cizilir ve algoritmanin diger modulleri (ornegin, fiyat hafizasi veya retest algilama) bu cizgileri kendi analizlerinde kullanirlar [^1^], [^2^].

### 3.2 Fibonacci, Woodie ve Camarilla Pivot Cesitleri

Standart pivot noktalarinin yaninda, farkli trading yaklasimlarina hitap eden bazi alternatif hesaplama yontemleri de bulunmaktadir. Bu varyantlar, formullerdeki katsayilari degistirerek veya onceki gunun kapanis fiyatina daha fazla agirlik vererek farkli destek ve direnc seviyeleri uretirler. Algoritmik bir Day Structure sistemi, bu farkli pivot turlerini ayni anda hesaplayarak bir **"confluence bolgesi" (uyumlu bolge)** tespit edebilir. Eger farkli yontemler benzer bir fiyat seviyesini destek veya direnc olarak isaret ediyorsa, bu seviyenin onemi katbekat artar. Asagida en yaygin pivot varyantlari aciklanmistir [^4^], [^6^].

**Fibonacci Pivot Noktalari:**
Fibonacci pivotlari, standart PP hesaplamasini ayni sekilde yaparken, destek ve direnc seviyelerini belirlerken **Fibonacci retracement oranlarini** (%38.2, %61.8, %100) kullanir. Bu yontem, Fibonacci sayilarinin piyasada dogal olarak tekrar eden oranlari temsil ettigi dusuncesine dayanir ve bu seviyelerin de psikolojik olarak onemli referanslar oldugu kabul edilir.
*   **PP** = (H + L + C) / 3 (Standart ile ayni)
*   **R1** = PP + 0.382 * (H - L)
*   **R2** = PP + 0.618 * (H - L)
*   **R3** = PP + 1.000 * (H - L)
*   **S1** = PP - 0.382 * (H - L)
*   **S2** = PP - 0.618 * (H - L)
*   **S3** = PP - 1.000 * (H - L)
Bu hesaplama, direnc ve destek seviyelerini standart pivota gore biraz daha icsel (dar) bir araliga yayar ve **orta volatilite gunlerinde** daha etkili olabilir.

**Woodie's Pivot Noktalari:**
Woodie's formulu, standart pivottan en onemli farki, ana pivot noktasi (PP) hesaplanirken **onceki gunun kapanis fiyatina (Close) cift agirlik** vermesidir. Bu, kapanis fiyatinin piyasa katilimcilarinin gun sonundaki konsensusunu daha iyi temsil ettigi dusuncesine dayanir. Bu yontem, gunun acilis fiyatina (Open) da onem verir ve gunun acilisina gore PP'nin nerede oldugu hakkinda hizli bir yorum yapilmasini saglar.
*   **PP** = (H + L + 2 * C) / 4
*   **R1** = (2 * PP) - L
*   **R2** = PP + (H - L)
*   **S1** = (2 * PP) - H
*   **S2** = PP - (H - L)
Woodie's pivotlari, gunun acilisina gore daha "reaktif" pivot seviyeleri uretir ve gunluk trading stratejileriyle uyumlu calisir.

**Camarilla Pivot Noktalari:**
Camarilla formulu, digerlerinden cok daha farkli bir yaklasim benimser ve **daha cok sayida, birbirine daha yakin destek ve direnc seviyeleri** uretir (genellikle 4 destek ve 4 direnc). Bu yontem, ozellikle **mean reversion (ortalamaya donus)** stratejileriyle uyumludur; yani fiyatin gun icindeki asiri hareketlerinin kapanis fiyatina geri donecegi varsayimina dayanir. Formul, onceki gunun fiyat araligina (H - L) belirli sabit katsayilar uygulayarak seviyeleri hesaplar.
*   **R4** = C + (H - L) * 1.5000
*   **R3** = C + (H - L) * 1.2500
*   **R2** = C + (H - L) * 1.1666
*   **R1** = C + (H - L) * 1.0833
*   **PP** = (H + L + C) / 3
*   **S1** = C - (H - L) * 1.0833
*   **S2** = C - (H - L) * 1.1666
*   **S3** = C - (H - L) * 1.2500
*   **S4** = C - (H - L) * 1.5000
Algoritmik sistem, bu farkli pivot varyantlarini ayni anda hesaplayarak, farkli yontemlerin ayni fiyat araligini isaret ettigi **"guclu pivot bolgeleri"** tespit edebilir. Bu bolgeler, fiyatin donus yapma olasiliginin en yuksek oldugu kritik zonlardir [^4^].

### 3.3 Gunluk Pivotlarin Algoritmik Olarak Cizilmesi ve Kullanimi

Pivot noktalarinin algoritmik trading sistemine entegrasyonu, sabah saatlerinde hesaplanan bu yedi seviyenin (PP, R1-R3, S1-S3) tum gun boyunca **statik referans cizgileri** olarak kullanilmasiyla gerceklesir. Bu cizgiler, piyasanin "nerede oldugu" hakkinda hizli bir degerlendirme yapmayi saglar. Algoritmik sistem, pivot seviyelerini asagidaki sekilde stratejik kararlarina entegre eder [^1^], [^4^].

**1. Trend Belirleme ve Bias Olusturma:**
Gunun baslangicindaki ilk fiyat hareketleri, ozellikle gunun **acilis fiyati (Open)** ile Pivot Point (PP) arasindaki iliski, gunluk bias hakkinda onemli bir ipucu verir.
*   **Acilis > PP:** Bu durum, gunluk trendin yukari yonlu olabilecegine dair bir isarettir. Algoritma bu durumda R1 seviyesini ilk hedef olarak belirler ve fiyatin PP uzerinde tutunmasini bir destek olarak gormeye baslar. PP uzerindeki ilk retest, bir long giris firsati olarak degerlendirilebilir.
*   **Acilis < PP:** Bu durum, gunluk trendin asagi yonlu olabilecegine isaret eder. Algoritma S1 seviyesini ilk hedef olarak belirler ve PP'nin bir direnc olarak calismasini bekler. PP altindaki ilk retest, bir short giris firsati olabilir.
*   **Acilis ≈ PP:** Fiyatin PP civarinda acilmasi ve ilk saatlerde bu seviyenin etrafinda dolanmasi, **"belirsizlik" veya "yatay piyasa"** sinyalidir. Bu durumda algoritma, fiyatin PP'den net bir sekilde ayrilmasini bekleyerek islem yapmayabilir veya cok dar aralikli bir range trading stratejisi uygulayabilir (ornegin, PP'den S1'e kadar al, R1'e kadar sat).

**2. Otomatik Destek/Direnc ve Retest Algilama:**
Pivot seviyeleri, algoritmik retest modulu icin hazir ve onceden belirlenmis seviyeler saglar. Sistem, fiyatin R1, R2, S1 veya S2 gibi seviyelere yaklastigini veya dokundugunu otomatik olarak algilar. Bu noktada, sistem sadece fiyatin seviyeye dokunmasini degil, ayni zamanda bu seviyedeki davranisi da analiz eder:
*   **Direnc Retesti (Orn. R1):** Fiyat R1'e yukselir ve bu seviyeden geri doner (reddetme) veya R1'nin uzerinde guclu bir kapanis yapamazsa, bu bir short sinyali olarak degerlendirilebilir. Bu, "Pivot Bounce" stratejisidir.
*   **Destek Retesti (Orn. S1):** Fiyat S1'e duser ve bu seviyeden guclu bir sekilde yukselirse (fitil olusturma veya yesil mum) veya S1 altinda kapanis yapmazsa, bu bir long sinyali olarak yorumlanabilir. Bu da "Pivot Bounce" stratejisinin destek tarafidir.
*   **Kirilma ve Yeniden Test (Break & Retest):** Fiyat R1'i yukari kirir ve geri donup R1 uzerinde tutunursa, R1 artik yeni bir destek haline gelir ve bu bir long firsatidir ("Pivot Reclaim"). Ayni sey S1'in kirilmasi icin de gecerlidir; S1 altinda kalan fiyat, geri donup S1'i bir direnc olarak reddederse, bu guclu bir short sinyalidir.

**3. Hedef Belirleme ve Risk Yonetimi:**
Pivot seviyeleri, acilan bir pozisyon icin **mantikli kar hedefleri (take-profit)** ve **stop-loss** seviyeleri belirlemek icin kullanilir.
*   **Long Pozisyon:** Ornegin, PP seviyesinden bir long islem acildiginda, ilk kar hedefi R1, ikinci hedef R2 olabilir. Stop-loss ise PP'nin hemen altina, ornegin S1 seviyesine veya pivot ile S1 arasina konabilir. Bu sekilde her islem icin **Risk/Odul orani (Risk/Reward Ratio)** onceden hesaplanabilir ve sadece kabul edilebilir oranlara sahip islemlerin acilmasi saglanir.
*   **Short Pozisyon:** PP seviyesinden bir short islem acildiginda, ilk hedef S1, ikinci hedef S2 olabilir. Stop-loss PP'nin uzerine, ornegin R1'e konabilir.

Bu entegrasyon, pivot noktalarinin sadece grafik uzerindeki cizgiler olmaktan cikip, **algoritmik trading kararlarinin temelini olusturan dinamik ve etkilesimli bir yapi tasina** donusmesini saglar. Pivot seviyeleri, diger sistem bilesenleri (swing noktalari, trend kanali, VWAP) ile birlestiginde, **"coklu dogrulama" (confluence)** prensibiyle cok daha guclu ve guvenilir sinyaller uretir [^1^], [^6^].

## 4. SWING HIGH/LOW TESPITI: ARGRELEXTREMA YONTEMI

### 4.1 scipy.signal.argrelextrema ile Yerel Ekstremumlarin Bulunmasi

Algoritmik bir Day Structure sisteminin en kritik bilesenlerinden biri, fiyat grafigindeki **yerel tepe (swing high)** ve **yerel dip (swing low)** noktalarinin otomatik olarak tespit edilmesidir. Bu noktalar, fiyatin yon degistirdigi yerleri temsil eder ve trendin yapisini anlamak icin temel taslardir. Python'da bu islem icin en yaygin ve etkili yontemlerden biri, **`scipy.signal` kutuphanesinin `argrelextrema` fonksiyonunu** kullanmaktir. Bu fonksiyon, bir veri dizisindeki yerel maksimum ve minimum noktalarinin indislerini bulmak icin tasarlanmistir. Trading baglaminda, bir fiyat serisine (ornegin, 'high' veya 'low' fiyatlari) uygulandiginda, **argrelextrema bize swing high ve swing low noktalarinin hangi mumlarda (candlestick) olustugunu** soyleyebilir [^20^], [^26^].

`argrelextrema` fonksiyonunun calisma prensibi basittir: Bir veri noktasinin yerel bir ekstremum (maksimum veya minimum) olup olmadigini belirlemek icin **komsulariyla kiyaslar**. Fonksiyonun en onemli parametresi **`order`**'dir. Bu parametre, bir noktanin yerel ekstremum olarak kabul edilebilmesi icin, bu noktanin kac komsusu uzerinde (veya altinda) olmasi gerektigini belirler. Ornegin, `order=5` olarak ayarlandiginda, bir yerel maksimum (swing high) noktasi, kendinden onceki 5 mumun ve sonraki 5 mumun en yuksek fiyatindan daha yuksek bir fiyata sahip olmalidir. Bu mekanizma, **kucuk fiyat dalgalanmalarindan (noise) kaynaklanan yanlis sinyalleri filtrelemeye** yardimci olur. `order` degeri ne kadar yuksekse, tespit edilen swing noktalari o kadar "buyuk" ve onemli olur; deger dustukce daha fazla sayida ve daha kucuk swing noktasi bulunur [^20^].

Algoritmik trading sisteminde bu fonksiyonun kullanimi asagidaki gibi gerceklestirilir:
1.  **Veri Hazirlama:** Oncelikle, analiz edilecek finansal enstrumana ait **OHLCV (Open, High, Low, Close, Volume)** verileri bir `pandas.DataFrame`'e yuklenir.
2.  **Swing High Tespiti:** `argrelextrema` fonksiyonu, DataFrame'deki **'high'** kolonuna uygulanir. Karsilastirma operatoru olarak `np.greater` (buyuktur) kullanilarak yerel maksimumlarin indisleri bulunur. Bu indisler, swing high noktalarina karsilik gelir.
3.  **Swing Low Tespiti:** Benzer sekilde, fonksiyon bu kez **'low'** kolonuna uygulanir ve karsilastirma operatoru olarak `np.less` (kucuktur) kullanilarak yerel minimumlarin indisleri bulunur. Bu indisler, swing low noktalarini verir.
4.  **Sonuclarin Kaydedilmesi:** Bulunan swing high ve swing low indisleri, orijinal DataFrame'e yeni kolonlar olarak eklenir. Bu sayede, bu noktalar diger analiz modulleri (trend kanali, fiyat hafizasi vb.) tarafindan kolayca erisilebilir hale gelir.

Asagidaki tablo, `argrelextrema` fonksiyonunun farkli `order` parametreleriyle nasil calistigini gostermektedir:

| order Parametresi | Tespit Edilen Swing Noktasi Sayisi | Swing Noktasi Buyuklugu/Onemi | Kullanim Senaryosu |
|---|---|---|---|
| **2-3** | Cok Fazla | Kucuk, kisa vadeli dalgalanmalar | Mikro-yapi analizi, scalping |
| **5-8** | Orta | Orta, gun ici onemli donusler | Gunluk (intraday) swing tespiti [^20^] |
| **10+** | Az | Buyuk, ana trend yapici tepe/dipler | Haftalik/aylik trend analizi |

### 4.2 Farkli Zaman Dilimlerinde Swing Tespiti ve Onemi

Swing high ve swing low noktalarinin onemi, analiz edilen **zaman dilimine (timeframe)** bagli olarak degisir. Algoritmik bir Day Structure sistemi, sadece tek bir zaman dilimine bagli kalmamali, aksine **coklu zaman dilimi (multi-timeframe)** prensibine gore calismalidir. Bu, farkli olceklerdeki fiyat yapisini anlamak icin kritik bir yaklasimdir. Ornegin, 5 dakikalik grafikte tespit edilen bir swing high, gunluk grafikteki bir swing high'dan cok daha kucuk bir yapiyi temsil eder. Algoritmik sistem, bu farkli olcekteki swing noktalarini **hiyerarsik bir yapi** icinde organize ederek daha saglam bir analiz cercevesi olusturabilir [^21^], [^39^].

**Dusuk Zaman Dilimleri (1, 5, 15 Dakikalik):**
Bu grafikler, **gunluk trading (intraday)** icin giris ve cikis noktalarini hassas bir sekilde belirlemek icin kullanilir. Bu zaman dilimlerinde tespit edilen swing noktalari, **kis vadeli momentum degisikliklerini** ve gun ici trendinin kucuk dalgalanmalarini gosterir. Ornegin, 5 dakikalik grafikte bir dizi "daha yuksek dip" (higher low) olusturan swing low noktalari, kisa vadeli bir yukselis trendinin devam ettigini gosterir. Algoritmik sistem, bu noktalardan gecen bir trend cizgisi cizerek dinamik bir destek belirleyebilir ve fiyat bu cizgiye retest yaptiginda bir long pozisyon dusunebilir. Bu grafiklerde `order` parametresi genellikle dusuk (2-5) tutulur ki gun ici hareketlerin yapisi kacirilmasin [^43^].

**Orta Zaman Dilimleri (1, 4 Saatlik):**
Bu grafikler, **gunluk trendin yonunu ve guclu destek/direnc seviyelerini** belirlemek icin kullanilir. Burada tespit edilen swing noktalari, gun ici "gurultunun" filtrelendigi ve ana fiyat hareketinin yapici taslarini olusturan daha saglam noktalardir. Ornegin, 4 saatlik grafikte tespit edilen bir swing high ve bir swing low, gunluk trading icin onemli bir fiyat araligini tanimlar. Algoritmik sistem, bu seviyeleri PDH/PDL referanslariyla birlestirerek gunluk islem planinin ana cercevesini cizebilir. Bu grafikler icin `order` parametresi daha yuksek (8-15) olabilir [^39^].

**Yuksek Zaman Dilimleri (Gunluk, Haftalik):**
Bu grafikler, **ana trendin yonunu ve cok onemli, uzun vadeli destek/direnc seviyelerini** gosterir. Gunluk grafikteki bir swing high, bir onceki gunku PDH'yi temsil edebilir ve gunluk trading icin kritik bir direnc olarak kabul edilir. Haftalik grafikteki swing noktalari ise cok daha guclu ve daha nadir kirilan seviyelerdir ve genellikle buyuk resmi anlamak icin kullanilir. Algoritmik sistem, yuksek zaman dilimindeki trend yonunu belirleyerek gunluk islemlerin bu ana trendle uyumlu olmasini saglayabilir (trend-takip filtresi). Bu grafiklerde `order` parametresi oldukca yuksek (15+) tutulur [^43^].

**Hiyerarsik Swing Yapisi:**
Ileri duzey bir algoritmik sistem, bu farkli zaman dilimlerindeki swing noktalarini **hiyerarsik bir yapi** icinde organize edebilir. Ornegin, 1 saatlik grafikteki her bir swing high ve low noktasinin, 5 dakikalik grafikteki daha kucuk "micro-swing" noktalarini icerdigini modelleyebilir. Bu hiyerarsik yapi, piyasanin **fraktal dogasini** (yani, benzer kaliplarin farkli olceklerde tekrar ettigi dusuncesini) yakalamaya calisir. Bir swing high noktasinin altindaki kucuk dalgalanmalarin yapisi, o ana tepe noktasinin "icsel yapisini" ortaya koyabilir ve bu da potansiyel bir donus icin daha erken uyarilar saglayabilir. Bu tur bir hiyerarsik analiz, piyasanin momentumunun ne kadar guclu oldugunu ve bir swing noktasinin kirilma olasiliginin ne oldugunu degerlendirmek icin kullanilabilir [^21^].

### 4.3 Swing Noktalarindan Trend Cizgilerinin Algoritmik Olarak Cizilmesi

Swing high ve swing low noktalari tespit edildikten sonra, bu noktalar birlestirilerek **trend cizgileri (trendlines)** cizilebilir. Trend cizgileri, piyasanin yonunun ve momentumunun gorsel bir temsilidir ve dinamik destek ve dirench olarak islev gorurler. Algoritmik olarak trend cizgisi cizmek, bu noktalardan en az ikisini birlestiren bir dogrunun denklemini bulmak anlamina gelir. En basit yontem, ard arda gelen swing noktalarini birlestirmektir. Ornegin, iki ard arda swing low noktasindan gecen bir cizgi, **yukselen trendin destek cizgisi** olarak kabul edilir. Fiyat bu cizgiye yaklastiginda veya dokundugunda, trendin devam etmesi beklenerek bir long islem dusunulebilir. Benzer sekilde, iki swing high noktasindan gecen bir cizgi ise **dusen trendin direnc cizgisi** olarak islev gorur [^31^], [^41^].

Algoritmik sistem, trend cizgilerini cizmek icin su adimlari izler:
1.  **Nokta Secimi:** Tespit edilen tum swing low'lar veya swing high'lar arasindan trend cizgisi olusturmak icin uygun nokta ciftleri secilir. Ideal olarak, bir trend cizgisi en az iki noktadan gecmelidir, ancak ne kadar cok sayida noktayi birlestirirse o kadar guclu kabul edilir.
2.  **Dogru Denkleminin Hesaplanmasi:** Iki noktasi bilinen bir dogrunun denklemi (`y = mx + b`) kolayca bulunabilir. Burada `m` egimi (slope) ve `b` y-eksenini kesme noktasini (intercept) temsil eder. Algoritma, secilen her bir swing nokta cifti icin bu dengeyi hesaplar.
3.  **Gecerlilik Kontrolu:** Cizilen trend cizgisinin gecerli olup olmadigini kontrol etmek icin, diger swing noktalarinin bu cizgiye olan uzakligi olculur. Eger diger noktalar cizginin yakininda kaliyorsa (belirli bir tolerans icinde), bu cizgi gecerli bir trend cizgisi olarak kabul edilir. Eger cok sayida nokta cizgiden uzaksa, bu cizgi gecersiz sayilir.
4.  **Dinamik Guncelleme:** Trend cizgileri statik degildir. Yeni swing noktalari olustukca, algoritma mevcut trend cizgilerini gunceller veya yeni, daha guncel trend cizgileri cizer. Ornegin, yukselen bir trendde, her yeni swing low olustugunda, en son iki swing low'u birlestiren yeni bir destek cizgisi cizilebilir. Bu, trendin dinamik dogasini takip etmeyi saglar.

Bu trend cizgileri, sistem icinde bir **"yapi modulu" (structure module)** olarak calisir. Fiyat bu cizgilere yaklastiginda, sistem bir **"yapi retesti" (structure retest)** olarak degerlendirir ve bu bolgelerde islem arar. Trend cizgisinin kirilmasi (breakout) ise trendin degisebilecegine dair onemli bir uyaridir ve sistem pozisyonunu kapatma veya terse cevirme karari alabilir. Bu yontem, Price Action trading'in temelini olusturan **"Market Structure"** kavraminin algoritmik olarak uygulanmasidir [^21^], [^41^].

## 5. TREND KANALI ANALIZI: LINEER REGRESYON YONTEMI

### 5.1 En Kucuk Kareler Yontemi ile Trend Kanali Hesaplama

Trend kanali, fiyat hareketinin istatistiksel olarak en olasi yoringesini ve bu yorungenin ust ve alt sinirlarini tanimlayan guclu bir analiz aracidir. Algoritmik tradingde trend kanali olusturmak icin en yaygin ve saglam yontemlerden biri **Lineer Regresyon Kanali**dir. Bu yontem, **"En Kucuk Kareler (Least Squares)"** metodunu kullanarak verilen bir veri setine (fiyat serisine) en iyi uyan duz cizgiyi bulur. Bu cizgi, **regresyon cizgisi** olarak adlandirilir ve fiyatin "ortalama" trendini temsil eder. Regresyon cizgisinin ustune ve altina, fiyatlarin standart sapmasi kadar uzaklikta iki paralel cizgi daha cizilerek bir **kanal** olusturulur. Bu kanal, fiyatin istatistiksel olarak hareket etmesi beklenen araligi tanimlar ve dinamik bir destek/direnc bolgesi olarak islev gorur [^22^], [^32^].

Matematiksel olarak, lineer regresyon denklemi `y = a + bx` seklinde ifade edilir. Burada:
*   `y`: Tahmin edilen fiyat degeri.
*   `x`: Zaman degiskeni (ornegin, 0, 1, 2, ... N-1).
*   `b`: Regresyon cizgisinin **egimi (slope)**. Pozitif ise yukselen, negatif ise dusen trend oldugunu gosterir.
*   `a`: Regresyon cizgisinin y-eksenini kestigi nokta (intercept).

Egim (`b`) ve kesisim (`a`) katsayilari asagidaki formullerle hesaplanir:
*   **b = (n * Σ(xy) - Σx * Σy) / (n * Σ(x²) - (Σx)²)**
*   **a = (Σy - b * Σx) / n**
    Burada `n` analizde kullanilan veri noktasi (mum) sayisidir. Algoritmik sistem, belirli bir `lookback` periyodu (ornegin son 50 veya 100 mum) icin bu hesaplamayi yapar ve regresyon cizgisini bulur. Bu cizgi, secilen donem icin fiyat hareketinin "en iyi fit"'ini saglar [^22^].

Regresyon cizgisi bulunduktan sonra, kanal bantlari icin **standart sapma** hesaplanir. Her bir gercek fiyat degeri (`y_i`) ile regresyon cizgisindeki karsilik gelen tahmini degeri (`y_hat_i`) arasindaki farkin karelerinin ortalamasinin karekoku alinir.
*   **Standart Sapma (σ) = sqrt( Σ(y_i - y_hat_i)² / n )**

Kanal bantlari ise sunlardir:
*   **Ust Kanal (Upper Channel):** `y_upper = (a + bx) + k * σ`
*   **Alt Kanal (Lower Channel):** `y_lower = (a + bx) - k * σ`

Burada `k` genellikle **2** olarak secilir. Bu, fiyatlarin yaklasik **%95** olasilikla bu kanal icinde kalmasini saglar (istatistiksel normal dagilim varsayimi altinda). Algoritmik sistem, bu kanalin merkez cizgisini, ust ve alt bantlarini surekli olarak hesaplar ve gunceller. Kanalin genisligi (bantlar arasi mesafe) piyasanin **volatilitesinin** bir gostergesidir; kanal daralirsa volatilite dusuyor, genislerse volatilite artiyor demektir. Bu bilgi, **piyasa rejimi tespiti** icin de kullanilabilir [^27^], [^30^].

### 5.2 Trend Kanalinin Yorumlanmasi: Yukari, Asagi ve Yatay Trendler

Lineer regresyon kanali, trendin yonunu ve guclulugunu belirlemek icin acik ve objektif bir cerceve sunar. Algoritmik sistem, kanalin merkez cizgisinin egimine (`b` katsayisi) bakarak trendin yonunu anlik olarak tespit edebilir. Bu durum, sistem icin bir **"trend filtresi"** olarak gorev yapar ve islemlerin mevcut trend yonunde acilmasini saglayarak basari oranini artirir [^32^].

**Trend Yonlerinin Yorumlanmasi:**
*   **Yukari Trend (Uptrend):** Regresyon cizgisinin egimi (`b`) **pozitif** oldugunda, bu bir yukari trendin varligini gosterir. Kanal, yukari dogru acilan bir paralelkenar seklinde gorunur. Bu durumda, algoritmik sistem **"long-only"** moduna gecebilir ve islem ararken kanalin **alt bandini bir dinamik destek** olarak, **merkez cizgisini ise bir geri cekilme (pullback) seviyesi** olarak kullanabilir. Fiyatin alt banda dokunup donmesi, yukselis trendinin guclu oldugunu ve bir alim firsati sunabilecegini gosterir.
*   **Asagi Trend (Downtrend):** Regresyon cizgisinin egimi (`b`) **negatif** oldugunda, bu bir asagi trendin varligini gosterir. Kanal, asagi dogru acilan bir paralelkenar seklinde gorunur. Bu durumda, sistem **"short-only"** moduna gecebilir ve kanalin **ust bandini bir dinamik direnc**, **merkez cizgisini ise bir geri cekilme (pullback/rally) seviyesi** olarak kullanabilir. Fiyatin ust banda dokunup donmesi, dusus trendinin guclu oldugunu ve bir satis firsati sunabilecegini gosterir.
*   **Yatay Trend / Aralik (Sideways Trend / Range):** Regresyon cizgisinin egimi (`b`) **sifira yakin** oldugunda, bu bir yatay trendin veya fiyatin bir aralik icinde hareket ettiginin gostergesidir. Kanal, yatay bir dikdortgen seklinde gorunur. Bu durumda, sistem bir **"range trading"** stratejisi uygulayabilir; yani kanalin **alt bandindan alim**, **ust bandindan satis** yapabilir. Merkez cizgisi (PP'ye benzer sekilde) araligin ortasi olarak kabul edilir ve bu seviyenin kirilmasi, yeni bir trendin baslangic sinyali olabilir.

**R-Kare (R-Squared) ile Trend Guclulugu:**
Egimin yani sira, trendin ne kadar guclu oldugunu olcmek icin **R-Kare (R²)** istatistigi de kullanilir. R-Kare, regresyon modelinin fiyattaki degiskenligin ne kadarini acikladigini gosterir. **0 ile 1 arasinda bir deger alir**. R-Kare degeri **1'e ne kadar yakinsa**, fiyat hareketinin regresyon cizgisine o kadar iyi uydugu ve trendin o kadar guclu ve duzenli oldugu anlamina gelir. Dusuk bir R-Kare degeri (ornegin 0.3'un alti), fiyat hareketinin cok daginik ve trendsel olmadigi bir piyasa (sikisiklik/chop) oldugunu gosterir. Algoritmik sistem, R-Kare degerine gore islem agresifligini ayarlayabilir; yuksek R-Kare ile trend-takip stratejileri, dusuk R-Kare ile ise aralik stratejileri veya islem yapmama tercih edilebilir [^32^].

### 5.3 Kanal Kirilmalarinin Algoritmik Olarak Tespiti ve Sinyal Uretimi

Trend kanali, sadece trendin yonunu gostermekle kalmaz, ayni zamanda onemli **trading sinyalleri** de uretir. Algoritmik sistem, fiyatin kanal icindeki hareketini ve kanal sinirlarina olan etkilesimini surekli olarak monitorler ve bu etkilesimlere gore islem kararlari alir. Kanal sinirlarinin kirilmasi (breakout), ozellikle onemli bir sinyal olarak kabul edilir [^30^].

**Kanal Ici Islem Stratejileri:**
1.  **Mean Reversion (Ortalamaya Donus):** Fiyat, kanalin ust bandina ulastiginda (ozellikle R-Kare dusukse), fiyatin ortalamasina donmesi beklenerek bir **short** pozisyon dusunulebilir. Hedef, kanalin merkez cizgisi veya alt bandi olabilir. Benzer sekilde, fiyat alt banda ulastiginda bir **long** pozisyon acilabilir. Bu strateji, yatay piyasalarda daha etkilidir.
2.  **Trend Devami (Trend Following):** Guclu bir trend sirasinda (R-Kare yuksek), fiyat kanalin merkez cizgisine bir geri cekilme (pullback) yaptiginda, trendin devam etmesi beklenerek trend yonunde bir islem acilabilir. Ornegin, yukari trendde fiyat merkez cizgisine dokunup donerse bu bir **long** firsatidir. Bu, "dip alma" (buying the dip) stratejisinin algoritmik bir uygulamasidir.

**Kanal Kirilmasi (Breakout) Stratejileri:**
Kanal kirilmasi, mevcut trendin hizlanmasi veya yeni bir trendin baslangicinin en guclu sinyallerinden biridir.
1.  **Yukari Yonlu Kirilma:** Fiyat, ust kanalin uzerinde guclu bir mum kapanisi yaparsa (ornegin, mumun govdesi bandin uzerinde kapanir ve hacim yuksektir), bu guclu bir **yukari yonlu kirilma** olarak kabul edilir. Algoritma bu durumda bir **long** pozisyon acabilir. Hedef, kanal genisliginin kirilma noktasindan itibaren eklenmesiyle bulunur. Stop-loss ise kirilan ust bandin hemen altina veya kanalin orta cizgisine konabilir.
2.  **Asagi Yonlu Kirilma:** Fiyat, alt kanalin altinda guclu bir mum kapanisi yaparsa, bu **asagi yonlu bir kirilma** olarak kabul edilir. Algoritma bir **short** pozisyon acabilir. Hedef ve stop-loss seviyeleri yukari kirilmannin tersi seklinde ayarlanir.

**Kirilmanin Gecerliligini Dogrulama (Filtering):**
Algoritmik sistemler, **"false breakout"** (yanlis kirilma) olarak adlandirilan ve cok sik karsilasilan bir durumu filtrelemek icin ek kosullar kullanir. Bunlar:
*   **Hacim Dogrulamasi:** Gercek bir kirilma genellikle yuksek hacimle birlikte gerceklesir. Kirilma mumunun hacminin ortalama hacmin uzerinde olmasi kosulu konulabilir.
*   **Mum Kapanisi:** Kirilmanin gerceklesmesi icin fiyatin bandin otesinde bir mum kapatmis olmasi genellikle gerekir. Sadece fitilin bandi asmama yeterli gorulmez.
*   **Retest:** En guclu girislerden biri, kirilma gercelestikten sonra fiyatin kirilan banda geri donup orada destek (yukari kirilma icin) veya direnc (asagi kirilma icin) bulmasidir. Algoritma, kirilma sonrasi bir retest firsati bekleyerek islem acabilir [^5^], [^32^].

## 6. FIYAT HAFIZASI (PRICE MEMORY) ALGORITMASI

### 6.1 Belirli Seviyelere Dokunma Sayisinin Algoritmik Olarak Sayimi

**Fiyat Hafizasi (Price Memory)**, piyasanin gecmisteki fiyat seviyelerine nasil tepki verdigi bilgisinin sistematik olarak toplanmasi ve analiz edilmesi surecidir. Bu kavram, teknik analizin temelini olusturan **"piyasa hafizasi"** veya **"destek ve direnc"** fikirlerinin algoritmik bir ifadesidir. Temel mantik sudur: Eger fiyat belirli bir seviyeye (ornegin $150.00) gecmiste birden fazla kez gelip de bu seviyeden donmusse, bu seviyenin piyasa katilimcilari icin ozel bir anlami vardir. Bu seviye bir **direnc** (yukaridan) veya **destek** (asagidan) olarak algilanir ve fiyat bu seviyeye tekrar geldiginde benzer bir tepki verme olasiligi yuksektir. Algoritmik sistem, bu "dokunma" (touch) veya "test etme" (test) olaylarini otomatik olarak sayarak, **her bir fiyat seviyesinin ne kadar "guclu" bir hafizaya sahip oldugunu** puanlayabilir [^8^], [^9^].

Algoritmik olarak fiyat hafizasini olusturmak icin kullanilan temel yontem, bir **"dokunma sayaci" (touch counter)** mekanizmasidir. Bu mekanizma su sekilde calisir:
1.  **Analiz Penceresi:** Sistem, belirli bir gecmis donemi (ornegin son 500 mum veya son 30 gun) analiz kapsamina alir.
2.  **Seviye Tanilama:** Analiz edilecek fiyat seviyeleri belirlenir. Bu seviyeler, swing high/low noktalari, pivot noktalari (R1, S1 vb.), psikolojik seviyeler (yuvarlak sayilar) veya onceden tanimlanmis sabit seviyeler olabilir.
3.  **Tolerans Zonu (Tolerance Zone):** Algoritma, fiyatin tam olarak o seviyeye degmesini beklemez. Bunun yerine, her seviyenin etrafinda belirli bir **tolerans payi** olusturur. Bu tolerans payi genellikle **ATR (Average True Range)** bazli olarak tanimlanir (ornegin, seviyenin ±%10'u kadar veya ±0.2 ATR kadar). Bu, fiyatin seviyeye "yeterince yakin" olmasini saglar ve kucuk fiyat dalgalanmalarinin yanlis bir dokunma olarak sayilmasini onler.
4.  **Dokunma Sayimi:** Algoritma, analiz penceresindeki her bir mum icin, fiyatin (tipik olarak en yuksek ve en dusuk fiyatlarinin) bu tolerans zonu icine girip girmedigini kontrol eder. Her giris, bir dokunma olarak sayilir.
5.  **Guclendirme ve Zayiflatma:** Her dokunma, o seviyenin "gucluluk puanini" artirir. Ancak, eger fiyat bir seviyeye dokunur ve bu seviyeyi guclu bir sekilde kirirsa, bu seviyenin artik bir destek/direnc olarak calismadigi varsayilir ve bu seviyenin hafizasi "sifirlanir" veya gucsuzlenir.

Bu algoritma, her bir fiyat seviyesi icin bir **"dokunma skoru"** uretir. Yuksek skora sahip seviyeler, "guclu hafiza bolgeleri" olarak isaretlenir ve algoritmik sistem bu bolgelere yaklastiginda tetiklenir [^51^].

### 6.2 Guclu ve Zayif Hafiza Bolgelerinin Tespiti

Dokunma sayilarinin hesaplanmasinin ardindan, algoritmik sistem bu verileri kullanarak **"Guclu Hafiza Bolgeleri" (Strong Memory Zones)** ve **"Zayif Hafiza Bolgeleri" (Weak Memory Zones)** olarak siniflandirma yapar. Bu siniflandirma, dokunma skorlarina, dokunmalar arasindaki sureklilige ve son dokunmadan bu yana gecen zamana gore yapilir [^8^].

**Guclu Hafiza Bolgesi Kriterleri:**
Bir fiyat bolgesinin "guclu" olarak siniflandirilmasi icin genellikle su kriterlerin bir kacini karsilamasi beklenir:
*   **Yuksek Dokunma Sayisi:** Bolgeye en az 3 veya daha fazla kez dokunulmus olmasi (kullanici isteginde belirtilen "3 kez" kurali bu noktada devreye girer). Ne kadar cok dokunma varsa, o kadar cok piyasa katilimcisi bu bolgeyi onemsemiştir.
*   **Kuvvetli Reaksiyonlar:** Her dokunmada fiyatin sert ve hizli bir sekilde donmus olmasi. Eger fiyat bir bolgeye dokunup saatlerce orada oyalanmissa, bu bolgenin direnci zayif olabilir. Ancak fitil (wick) olusturup aninda donmesi, guclu bir arz/talep dengesizligi oldugunu gosterir.
*   **Yakin Zamanda Test Edilme:** Bolgenin son birkac gun/icinde tekrar test edilmis olmasi. Cok eskiden kalma bir hafiza bolgesi (ornegin 1 yil once 5 kez dokunulan bir seviye) guncel olmayabilir. Algoritma, daha yakin zamanda olusan dokunmalara daha fazla agirlik verebilir.
*   **Confluence (Uyum):** Hafiza bolgesinin, ayni zamanda bir pivot noktasi, psikolojik seviye veya trend cizgisi gibi baska bir onemli referansla cakismasi. Bu tur bir uyum, bolgenin onemini katbekat artirir.

**Zayif Hafiza Bolgesi Kriterleri:**
*   **Dusuk Dokunma Sayisi:** Bolgeye sadece 1 veya 2 kez dokunulmus olmasi.
*   **Kirilma Gecmisi:** Fiyatin bolgeye dokunduktan sonra o bolgenin ustunden veya altindan guclu bir sekilde kapanis yapmış olması. Bu, o seviyenin artik "eski bir destek/direnc" oldugunu ve rolinu degistirdigini gosterir.
*   **Uzun Sure Test Edilmeme:** Bolgenin cok uzun bir suredir (ornegin aylardir) test edilmemis olmasi. Piyasa katilimcilarinin bu seviyeyi unutmus olma olasiligi vardir.

Algoritmik sistem, bu kriterlere gore her bir fiyat bolgesini renklendirerek veya etiketleyerek (ornegin, guclu bolgeleri koyu renkte, zayif bolgeleri soluk renkte gosterebilir) tradera veya sistemin diger modullerine sunar. Bu sayede, fiyat bir bolgeye yaklastiginda, sistemin bu bolgenin "guvenilirligi" hakkinda bir onbilisi olur ve buna gore islem stratejisini ayarlar. Ornegin, guclu bir hafiza bolgesine yaklasildiginda sistem daha temkinli olabilir ve ek dogrulama sinyalleri bekleyebilirken, zayif bir bolgede daha agresif bir sekilde hareket edebilir [^38^], [^41^].

### 6.3 Hafiza Bolgelerinin Destek/Direnc Olarak Kullanimi ve Guncellenmesi

Fiyat hafizasi algoritmasi tarafindan tespit edilen guclu bolgeler, algoritmik trading sisteminde **dinamik ve istatistiksel olarak validate edilmis destek ve dirench seviyeleri** olarak gorev yaparlar. Bu seviyeler, statik pivot noktalari veya manuel olarak cizilen cizgilerin aksine, piyasanin gercek davranisindan turetilirler ve bu nedenle daha "canli" ve guvenilir kabul edilebilirler. Sistem, bu bolgeleri asagidaki sekilde stratejik kararlarina entegre eder [^9^], [^51^].

**1. Giris Noktasi (Entry) Belirleme:**
Guclu bir hafiza bolgesi, potansiyel bir donus noktasi olarak kabul edilir ve sistem bu bolgelere yaklastiginda **"uyanir"**.
*   **Direnc Bolgesinden Donus (Short Entry):** Fiyat, guclu bir hafiza direnc bolgesine (ornegin, $155.00 bolgesi, 4 kez dokunulmus) yukseldiginde, sistem bir donus beklentisiyle short pozisyon aramaya baslar. Sistem, bu bolgede retest sinyallerini bekler. Ornegin, fiyat bolgeye dokunur ve bir fitil (wick) olusturarak geri donerse veya bu bolgenin altinda bir mum kapanisi yaparsa, bu bir short giris sinyali olarak degerlendirilebilir. Stop-loss, direnc bolgesinin hemen uzerine konur.
*   **Destek Bolgesinden Donus (Long Entry):** Fiyat, guclu bir hafiza destek bolgesine dustugunde, sistem bir yukselis beklentisiyle long pozisyon arar. Bolgede fitil olusumu veya bu bolgenin uzerinde kapanis, long giris icin bir onaydir. Stop-loss, destek bolgesinin hemen altina konur.

**2. Hedef (Take-Profit) Belirleme:**
Hafiza bolgeleri, acik bir pozisyon icin **mantikli kar hedefleri** olarak da kullanilir. Ornegin, bir destek bolgesinden long isleme girildiginde, bir sonraki guclu direnc (hafiza) bolgesi birincil kar hedefi olarak belirlenebilir. Bu, risk/odul oraninin hesaplanmasini kolaylastirir.

**3. Dinamik Guncelleme ve Eski Bolgelerin Kaldirilmasi:**
Fiyat hafizasi algoritmasi statik degildir; piyasa yeni veriler urettikce surekli olarak guncellenir. Algoritma, yeni swing noktalari ve yeni dokunmalar olustukca hafiza bolgelerini yeniden hesaplar. Ayrica, eski ve artik gecerli olmayan bolgeleri kaldirmak icin su kurallari uygular:
*   **Rol Degisimi (Role Reversal):** Fiyat guclu bir destek bolgesini asagi kirarsa, bu bolge artik bir direnc bolgesi haline gelir. Algoritma bu bolgenin etiketini otomatik olarak gunceller. Ayni sey bir direncin kirilip destek haline gelmesi icin de gecerlidir [^8^].
*   **Zaman Asimi:** Belirli bir sure (ornegin 30 gun) boyunca test edilmeyen guclu bolgeler, algoritma tarafindan "eski" olarak isaretlenir ve gorselden kaldirilabilir veya daha soluk renkte gosterilebilir. Bu, grafigin kalabaliklasmasini onler ve analizi guncel tutar.
*   **Birlesme (Merging):** Iki guclu hafiza bolgesi birbirine cok yakin konumlarda olusursa (ornegin $150.00 ve $150.05), algoritma bu iki bolgeyi tek, daha genis bir **"bolge" (zone)** olarak birlestirebilir. Bu, destek/direncin tek bir fiyattan ziyade bir aralik olarak dusunulmesini saglar ve daha gercekci bir yaklasim sunar [^8^].

Bu dinamik guncelleme mekanizmasi, fiyat hafizasi algoritmasinin surekli olarak piyasanin degisen kosullarina uyum saglamasini ve trading sistemine her zaman en guncel ve en alakali destek/direnc bilgilerini saglamasini garanti eder. Bu, algoritmik trading sisteminin **adaptif ve saglam** olmasini saglayan kritik bir ozelliktir.

## 7. RETEST ALGORITMASI VE SAPMA PAYLARI (TOLERANCE)

### 7.1 Fiyatin Kritik Seviyelere Yaklasiminin Algoritmik Olarak Tespiti

**Retest**, algoritmik Day Structure sisteminin en kritik ve en karli bilesenlerinden biridir. Temel mantik sudur: Fiyat onemli bir destek veya direnc seviyesini (ornegin, PDH, bir pivot seviyesi veya bir trend cizgisi) **kirdiktan sonra**, bu seviyeye geri donup oradan **"onay" (confirmation)** almasini beklemektir. Bu geri donus hareketi, kirilan seviyenin artik yeni bir destek (yukari kirilma sonrasi) veya yeni bir direnc (asagi kirilma sonrasi) olarak calistigini dogrular. Bu onay, yanlis kiralardan (false breakouts) kaynaklanan zararlardan kacinmak icin hayati bir guvenlik mekanizmasidir [^3^], [^5^].

Algoritmik olarak retest hareketini tespit etmek icin sistem, once **bir "kirilma" (break) olayini** tanimalidir. Bu, fiyatin belirli bir seviyenin belirli bir tolerans uzerinde veya altinda kapanis yapmasiyla tanimlanir. Kirilma tespit edildikten sonra, sistem **"gozlem moduna" (watch mode)** gecer ve fiyatin kirilan seviyeye geri donup donmedigini izler. Bu izleme sureci, su kosullarin saglanmasini gerektirir:
1.  **Fiyatin Seviyeye Yaklasmasi:** Fiyatin, kirilan seviyeye belirli bir mesafe icinde olmasi gerekir. Bu mesafe, **sapma payi (tolerance)** ile tanimlanir.
2.  **Zaman Sinirlamasi:** Retest, kirilma sonrasi belirli bir zaman dilimi icinde gerceklesmelidir. Ornegin, sistem sadece kirilma sonrasi 10 mum icindeki bir retesti gecerli sayabilir. Cok uzun sure sonra gelen bir retest, artik gecerli olmayabilir.
3.  **Mum Yapisi ve Momentum:** Sistem, retest sirasindaki mum yapisini da analiz eder. Ornegin, destek seviyesinde retest sirasinda **uzun bir alt fitil (lower wick)** olmasi, o seviyede guclu bir alis baskisi oldugunu gosterir ve retestin guclulugunu artirir. Ayni sekilde, direnc seviyesinde **uzun bir ust fitil (upper wick)** olmasi, satis baskisinin guclu oldugunu gosterir.

Algoritmik sistem, bu kosullari surekli olarak degerlendirir ve tum kosullar bir araya geldiginde bir **"retest onayi" (retest confirmation)** sinyali uretir. Bu sinyal, sistemin islem acmasi icin gereken son adimdir. Bu mekanizma, trading kararlarinin sadece bir kirilmaya dayanmasindan ziyade, **kirilmanin piyasa tarafindan onaylanmasina** dayanmasini saglayarak islem basarisini onemli olcude artirir [^14^], [^64^].

### 7.2 Sapma Payi (Tolerance) Belirleme: ATR ve Yuzde Bazli Yontemler

**Sapma payi (Tolerance veya Threshold)**, algoritmik retest sisteminin en hassas ayarlarindan biridir. Bu pay, fiyatin bir referans seviyeye ne kadar "yakin" olmasi gerektigini tanimlar. Tolerans cok dar olursa, sistem cok az sayida retest yakalayabilir ve bir cok gecerli firsati kacirabilir. Tolerans cok genis olursa ise, sistem cok sayida yanlis sinyal uretir ve "gurultulu" bolgelerde gereksiz yere islem acabilir. Bu nedenle, toleransin dinamik ve piyasa kosullarina uygun bir sekilde belirlenmesi kritik oneme sahiptir. Iki temel yontem vardir: **Yuzde bazli** ve **ATR (Average True Range) bazli** [^59^], [^75^].

**Yuzde Bazli Tolerans:**
Bu yontemde, sapma payi referans seviyenin belirli bir yuzdesi olarak tanimlanir. Ornegin, **%0.1'lik bir tolerans**, $150.00'lik bir seviye icin ±$0.15'lik bir aralik (yani $149.85 ile $150.15 arasi) demektir. Bu yontem basit ve anlasilirdir, ancak **dezavantaji** dusuk ve yuksek fiyatli enstrumanlar icin esit derecede etkili olmamasidir. Ornegin, %0.1'lik bir tolerans $10'luk bir hisse icin $0.01 iken, $1000'lik bir hisse icin $1'dir. Bu durum, farkli fiyat seviyelerindeki enstrumanlar icin tutarli bir davranis saglamayabilir.

**ATR (Average True Range) Bazli Tolerans:**
Bu yontem, toleransi piyasanin guncel volatilitesine gore dinamik olarak ayarlar ve **cok daha saglam ve esnek** bir yaklasimdir. ATR, bir enstrumanin belirli bir donemdeki ortalama fiyat hareket araligini olcer. **ATR bazli tolerans**, referans seviyenin etrafinda bir "gecerlilik zonu" olusturmak icin ATR degerinin belirli bir kati (ornegi) alinmasiyla hesaplanir.
*   **Formul: Tolerans = ATR_degeri × katsayi**

Kullanilan katsayi (multiplier), trading stiline ve analiz edilen zaman dilimine gore degisir:
*   **Kucuk Katsayi (0.1 - 0.2 x ATR):** Cok hassas ve erken girisler icin kullanilir. Scalping stratejileri veya cok dusuk zaman dilimleri icin uygundur. Bu, fiyatin seviyeye "neredeyse tam olarak" dokunmasini gerektirir.
*   **Orta Katsayi (0.3 - 0.5 x ATR):** En yaygin kullanim alanidir. Gunluk trading ve swing trading icin uygundur. Bu aralik, gecerli retestleri yakalayip yanlis sinyalleri filtrelemek icin iyi bir denge saglar.
*   **Buyuk Katsayi (0.5 - 1.0 x ATR):** Daha genis bir giris bolgesi saglar. Ozellikle volatil piyasalarda veya daha yuksek zaman dilimlerinde, fiyatin seviyeye "yaklasmis olmasinin" yeterli oldugu stratejiler icin kullanilir.

Algoritmik sistem, ATR degerini surekli olarak guncelledigi icin, **tolerans da otomatik olarak piyasa volatilitesine uyum saglar**. Volatilite arttiginda (ATR yukseldiginde) tolerans genisler, volatilite dustugunde (ATR dustugunde) tolerans daralir. Bu, sistemin her piyasa kosulunda tutarli bir sekilde calismasini saglar ve **"bir olcu tum piyasalara"** yaklasimini mumkun kilar [^59^], [^82^].

### 7.3 Retest Onayi Sinyalleri: Mum Yapisi ve Hacim ile Dogrulama

Algoritmik sistem, fiyatin bir seviyeye belirli tolerans icinde geldigini (retest) tespit ettikten sonra, islem acmak icin ek **dogrulama (confirmation)** sinyalleri arar. Bu dogrulama asamasi, retestin gercekten guclu ve guvenilir bir donus mu yoksa sadece gecici bir duraksama mi oldugunu anlamak icin kritiktir. En yaygin dogrulama yontemleri, **mum yapisini (candlestick patterns)** ve **hacmi (volume)** analiz etmektir [^5^], [^78^].

**Mum Yapisi ile Dogrulama:**
Mumlar, piyasa katilimcilarinin o belirli zaman dilimindeki davranislarinin bir goruntusudur. Retest bolgesinde olusan mumlar, seviyenin tepkisini dogrudan gosterir.
*   **Destek Retesti (Long Sinyali):** Fiyat bir destek seviyesine retest yaptiginda, sistem asagidaki mum kaliplarini arar:
    *   **Fitil (Wick/Rejection):** Mumun govdesi destek seviyesinin uzerinde kalmis ancak alt fitili bu seviyeyi asmis ve geri donmusse, bu guclu bir alim baskisi isaretidir. Fitil ne kadar uzunsa, reddetme o kadar gucludur.
    *   **Bullish Engulfing:** Dusus trendindeki kucuk bir kirmizi mumu, buyuk bir yesil mumun tamamen icine almasi ("yutmasi"). Bu, alicilarin kontrolu ele gecirdiginin guclu bir isaretidir.
    *   **Hammer:** Uzun bir alt fitili ve kucuk bir govdesi olan bir mum. Bu, seviyede alicilarin guclu bir sekilde devreye girdigini gosterir.
    *   **Yesil Kapanis:** En basit onay, fiyatin destek seviyesinin uzerinde bir mum kapatmasidir.

*   **Direnc Retesti (Short Sinyali):** Fiyat bir direnc seviyesine retest yaptiginda, sistem su kaliplari arar:
    *   **Fitil (Wick/Rejection):** Mumun govdesi direnc seviyesinin altinda kalmis ancak ust fitili bu seviyeyi asmis ve geri donmusse, bu guclu bir satis baskisi isaretidir.
    *   **Bearish Engulfing:** Yukselis trendindeki kucuk bir yesil mumu, buyuk bir kirmizi mumun tamamen icine almasi. Bu, satıcıların kontrolu ele gecirdiginin isaretidir.
    *   **Shooting Star:** Uzun bir ust fitili ve kucuk bir govdesi olan bir mum. Yukaridan satis baskisinin guclu oldugunu gosterir.
    *   **Kirmizi Kapanis:** Fiyatin direnc seviyesinin altinda bir mum kapatmasi, en temel short onayidir.

**Hacim ile Dogrulama:**
Hacim, bir fiyat hareketinin "guvenilirliginin" en onemli gostergelerinden biridir. Guclu bir trend veya kirilma, genellikle yuksek hacimle desteklenir.
*   **Yukari Kirilma + Retest:** Kirilma aninda hacim yukselmisse ve retest sirasinda hacim dusuyorsa (yani satis baskisi zayiflamis), bu retestin guvenilirligini artirir. Retest sirasinda hacimin tekrar yukselmesi ve fiyatin yukari gitmesi, trendin guclu oldugunu gosterir.
*   **Asagi Kirilma + Retest:** Kirilma aninda hacim yukselmisse ve retest sirasinda hacim dusuyorsa (alis baskisi zayiflamis), bu guvenilir bir retest isaretidir.

Algoritmik sistem, bu mum kaliplarini ve hacim degisikliklerini matematiksel olarak tanimlayabilir. Ornegin, bir fitilin uzunlugunun mumun govdesinden en az 2 kat fazla olmasi, bir engulfing kalibinin olusup olusmadiginin kontrol edilmesi veya mevcut hacmin son 20 mumluk ortalama hacmin uzerinde olup olmadiginin sorgulanmasi gibi kosullar tanimlanabilir. Tum bu kosullarin (tolerans icinde olma + mum yapisi onayi + hacim onayi) ayni anda saglanmasi, algoritmik sistem icin **en yuksek olasilikli giris sinyali**ni olusturur [^41^], [^81^].

## 8. BITUNLESIK SISTEM TASARIMI VE ALGORITMIK MIMARI

### 8.1 Tum Bilesenlerin Birlestirilmesi: Sistem Akis Semasi

Day Structure algoritmik trading sistemi, yukarida ayrintili olarak ele alinan bilesenlerin (Referans Seviyeleri, Pivotlar, Swing Noktalari, Trend Kanali, Fiyat Hafizasi) tek bir butun icinde birlestirilmesiyle olusturulur. Sistemin temel prensibi **"coklu dogrulama" (confluence)** uzerine kuruludur. Yani, sistem tek bir sinyale dayanarak islem acmak yerine, **farkli analiz modullerinden gelen sinyallerin ayni yonde ve ayni bolgede uyusmasini** bekler. Bu, yanlis sinyalleri onemli olcude azaltir ve islem basarisini artirir [^35^], [^39^].

Sistemin genel akis semasi ve karar agaci asagidaki gibidir:

1.  **Veri Girisi ve On Isleme:** Sistem, gercek zamanli veya gecmis OHLCV verilerini alir. Gunun basinda PDH, PDL, PWH, PWL gibi referans seviyeleri ve tum pivot noktalari (Standart, Fibonacci vb.) hesaplanir.
2.  **Teknik Analiz Modullerinin Calistirilmasi:**
    *   **Swing Modulu:** `argrelextrema` kullanarak son swing high ve low noktalarini tespit eder.
    *   **Trend Modulu:** Lineer regresyon ile mevcut trend kanalini ve trend yonunu hesaplar.
    *   **Hafiza Modulu:** Belirli bir gecmiste guclu dokunmalari olan fiyat bolgelerini tespit eder.
    *   **VWAP Modulu:** Gunluk VWAP ve standart sapma bantlarini hesaplar.
3.  **Sinyal Uretimi ve Degerlendirmesi:** Her bir modul, fiyatin mevcut konumuna gore kendi sinyalini uretir (ornegin, "Pivot R1 direncine yaklasildi", "Trend kanali alt bandindan donus sinyali", "Guclu hafiza bolgesine girildi").
4.  **Confluence (Uyum) Motoru:** Sistemin kalbi olan bu modul, tum modullerin sinyallerini bir araya getirir ve bir **"guven skoru" (confidence score)** hesaplar. Ornegin:
    *   **Guclu Long Sinyali:** Fiyat, hem trend kanali alt bandinda, hem bir pivot destek seviyesinde (S1), hem de guclu bir hafiza bolgesinde retest yapiyor ve mum yapisi onayliyorsa -> Guven skoru: **%90+**
    *   **Zayif Long Sinyali:** Fiyat sadece pivot destek seviyesinde retest yapiyor ancak trend kanali orta cizginin uzerinde ve diger moduller sessizse -> Guven skoru: **%50**
5.  **Islem Karari:** Sistem, onceden tanimlanmis bir guven skoru esiginin (ornegin **%75**) uzerindeki sinyallere gore islem acar. Skorun altindaki sinyaller goz ardi edilir.
6.  **Risk Yonetimi:** Acilan her islem icin, ATR bazli dinamik stop-loss ve pivot/hafiza bolgelerine gore kar hedefleri otomatik olarak hesaplanir. Pozisyon buyuklugu, hesaplanan risk'e gore ayarlanir.

Bu yapi, sistemin tum bilesenlerinin birbirini tamamlayici sekilde calismasini ve her kararin saglam bir istatistiki ve teknik temele dayanmasini saglar. Sistem, tek basina PDH/PDL veya pivotlardan cok daha guclu bir cerceve sunar cunku **piyasanin farkli boyutlarindan (trend, volatilite, davranissal hafiza) gelen bilgileri sentezler** [^36^], [^37^].

### 8.2 Sinyal Uretimi: Confluence (Coklu Dogrulama) Prensibi

**Confluence (Coklu Dogrulama)**, bu Day Structure sisteminin basarisinin temelini olusturan en kritik prensiptir. Bu prensip, **farkli teknik analiz araclarinin veya analiz modullerinin ayni fiyat bolgesinde ve ayni yonde sinyal uretmesi** durumunda, o sinyalin guvenilirliginin katbekat arttigi dusuncesine dayanir. Tek bir gosterge veya seviye baz alinarak alinan kararlar, genellikle yaniltici olabilir. Ancak, bir direnc seviyesi ayni zamanda bir trend cizgisi, bir pivot noktasi ve guclu bir fiyat hafizasi bolgesiyle cakistiginda, bu seviyenin kirilmasi veya buradan donmesi cok daha onemli bir olay haline gelir. Algoritmik sistem, bu uyumu objektif olarak olcmek ve degerlendirmek icin tasarlanmistir [^35^], [^39^].

Confluence degerlendirmesi, sistem icinde bir **skorlama mekanizmasi** ile gerceklestirilir. Her bir analiz modulu, fiyatin mevcut durumunu degerlendirdiginde bir sinyal uretir ve bu sinyal belirli bir "agirlik" (weight) ile confluence skoruna eklenir. Asagida ornek bir confluence skorlama tablosu verilmistir:

| Analiz Modulu | Sinyal | Yon | Agirlik (Weight) | Kosul |
|---|---|---|---|---|
| **Trend Kanali** | Fiyat alt banda dokundu | Yukari (Long) | 25 | Kanal R-Kare > 0.7 ise |
| **Pivot Noktalari** | Fiyat S1 desteginde | Yukari (Long) | 20 | PP uzerindeyse ek +10 |
| **Fiyat Hafizasi** | Guclu destek bolgesine girildi | Yukari (Long) | 20 | 3+ dokunma varsa |
| **Swing Noktalari** | Son swing low'un uzerinde | Yukari (Long) | 15 | Yeni higher low olusuyorsa |
| **PDH/PDL** | Fiyat PDL uzerinde ve PDH'ye yakin| Yukari (Long) | 10 | Gunluk araligin ust yarisi |
| **VWAP** | Fiyat VWAP'in uzerinde | Yukari (Long) | 10 | Hacim yuksekse |

Bu tabloya gore, ornegin, fiyatin guclu bir trend kanali alt bandinda, S1 pivot desteginde ve guclu bir fiyat hafiza bolgesinde olmasi durumunda, sistem otomatik olarak 25 + 20 + 20 = **65 puanlik bir confluence skoru** hesaplar. Eger sistem, islem acmak icin 60 puanlik bir esik degeri (threshold) belirlemisse, bu durum bir long islem acmak icin yeterli confluence'un var oldugunu gosterir. Algoritma, bu skoru surekli olarak guncelleyerek fiyat hareket ettikce yeni sinyallerin eklenip cikarildigi dinamik bir degerlendirme yapar [^36^].

### 8.3 Risk Yonetimi: ATR Bazli Stop-Loss ve Pozisyon Buyuklugu

Day Structure sisteminin bir diger kritik bileseni, **saglam bir risk yonetimi protokoludur**. Sistem, islemler acilmadan once potansiyel zarar ve kazanci onceden hesaplar ve sadece kabul edilebilir risk/odul oranlarina sahip islemleri gerceklestirir. Bu sistemin temeli **ATR (Average True Range)** bazli dinamik stop-loss ve pozisyon buyuklugu belirlemedir [^59^], [^75^].

**ATR Bazli Stop-Loss Belirleme:**
Sistem, geleneksel sabit pip/puanli stop-loss kullanmak yerine, piyasanin guncel volatilitesine gore ayarlanan bir stop-loss kullanir. Bu, ozellikle farkli volatilite donemlerinde (ornegin, sabah acilisi vs. oglen seansi) tutarsiz risklerden kacinmayi saglar.
*   **Formul: Stop-Loss Mesafesi = Mevcut ATR Degeri × Katsayi**
    Katsayi genellikle **1.5 ile 3 arasinda** secilir.
    *   **1.5 x ATR:** Daha sikis ve agresif bir stop-loss. Scalping veya cok hassas girisler icin uygundur ancak yanlis kovulma (whipsaw) olasiligi daha yuksektir.
    *   **2.0 x ATR:** Dengeli bir yaklasim. Gunluk trading icin en yaygin kullanimdir.
    *   **3.0 x ATR:** Daha genis ve muhafazakar bir stop-loss. Trend takip stratejileri icin daha uygundur ve piyasa gurultusune karsi daha dayaniklidir.

Ornegin, bir long islem acildiginda, stop-loss giris fiyatinin altinda `2 × ATR` kadar bir mesafeye konur. Eger ATR degeri $0.50 ise, stop-loss $1.00 asagiya konur. Bu, islemin "nefes almasi" icin yeterli bir alan tanirken, asiri kaybi onler.

**Pozisyon Buyuklugu (Position Sizing) Belirleme:**
Sistem, her bir islem icin ne kadar sermaye risk edilecegini onceden belirler. Bu, genellikle toplam hesap bakiyesinin belirli bir yuzdesi (ornegin **%1 veya %2**) olarak tanimlanir.
*   **Formul: Pozisyon Buyuklugu = (Hesap Bakiyesi × Risk Yuzdesi) / (Giris Fiyati - Stop-Loss Fiyati)**

Bu yaklasim, her islemde sabit bir dolar miktari risk etmeyi garanti eder. Ornegin, $100,000'lik bir hesapta %1 risk ($1,000) ile islem yapiliyorsa ve bir hissenin giris fiyati $150, stop-loss'u ise $148 (yani $2'lik bir risk) ise:
*   Pozisyon Buyuklugu = $1,000 / $2 = **500 hisse**.
Bu sekilde, hissenin fiyati ne olursa olsun, her islemde maksimum $1,000 kaybetme riski vardir. Bu, risk yonetiminin disiplinli ve matematiksel olarak saglam bir sekilde yapilmasini saglar [^75^], [^82^].

## 9. PYTHON IMPLEMENTASYONU: TAM SISTEM KODU

### 9.1 DayStructureAnalyzer Sinifinin Tam ve Aciklamali Kodu

Asagida, tum yukarida ele alinan bilesenleri (Referans Seviyeleri, Pivot Noktalari, Swing Tespiti, Trend Kanali, Fiyat Hafizasi, Retest Algoritmasi) entegre eden butunsel bir Python sinifi sunulmustur. Bu sinif, `pandas` ve `scipy` kutuphanelerini kullanarak algoritmik analizi gerceklestirir.

```python
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

class DayStructureAnalyzer:
    """
    Day Structure Algoritmik Trading Sistemi
    Tum bilesenleri entegre eden butunsel analiz sinifi.
    """
    def __init__(self, df, atr_period=14, swing_order=5, tolerance_atr=0.2, 
                 memory_lookback=100, trend_lookback=50):
        self.df = df.copy()
        self.atr_period = atr_period
        self.swing_order = swing_order
        self.tolerance_atr = tolerance_atr
        self.memory_lookback = memory_lookback
        self.trend_lookback = trend_lookback
        self.levels = {}  # Referans seviyeleri
        self.memory_zones = []  # Fiyat hafizasi bolgeleri
        self.signals = []  # Uretilen sinyaller

    def calculate_atr(self):
        """ATR (Average True Range) hesaplama"""
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['ATR'] = tr.rolling(window=self.atr_period).mean()
        return self.df['ATR']

    def calculate_pivot_points(self, prev_high, prev_low, prev_close):
        """Standart Pivot Noktalari hesaplama"""
        pp = (prev_high + prev_low + prev_close) / 3
        self.levels['pivot'] = {
            'PP': pp,
            'R1': (2 * pp) - prev_low,
            'R2': pp + (prev_high - prev_low),
            'R3': prev_high + 2 * (pp - prev_low),
            'S1': (2 * pp) - prev_high,
            'S2': pp - (prev_high - prev_low),
            'S3': prev_low - 2 * (prev_high - pp)
        }
        return self.levels['pivot']

    def detect_swings(self):
        """argrelextrema ile Swing High/Low tespiti"""
        highs = self.df['high'].values
        lows = self.df['low'].values
        max_idx = argrelextrema(highs, np.greater, order=self.swing_order)[0]
        min_idx = argrelextrema(lows, np.less, order=self.swing_order)[0]
        self.df['swing_high'] = np.nan
        self.df['swing_low'] = np.nan
        self.df.loc[self.df.index[max_idx], 'swing_high'] = highs[max_idx]
        self.df.loc[self.df.index[min_idx], 'swing_low'] = lows[min_idx]
        self.levels['swings'] = {
            'highs': [(self.df.index[i], highs[i]) for i in max_idx],
            'lows': [(self.df.index[i], lows[i]) for i in min_idx]
        }
        return self.levels['swings']

    def calculate_vwap(self):
        """VWAP (Volume Weighted Average Price) hesaplama"""
        tp = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        cum_vol = self.df['volume'].cumsum()
        cum_tp_vol = (tp * self.df['volume']).cumsum()
        self.df['VWAP'] = cum_tp_vol / cum_vol
        variance = ((tp - self.df['VWAP'])**2 * self.df['volume']).cumsum() / cum_vol
        std = np.sqrt(variance)
        self.df['VWAP_upper1'] = self.df['VWAP'] + std
        self.df['VWAP_lower1'] = self.df['VWAP'] - std
        self.df['VWAP_upper2'] = self.df['VWAP'] + 2 * std
        self.df['VWAP_lower2'] = self.df['VWAP'] - 2 * std
        return self.df['VWAP']

    def detect_trend_channel(self):
        """Lineer Regresyon ile Trend Kanali tespiti"""
        recent = self.df.tail(self.trend_lookback).reset_index(drop=True)
        x = np.arange(len(recent))
        y = recent['close'].values
        n = len(x)
        b = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        a = (np.sum(y) - b * np.sum(x)) / n
        regression_line = a + b * x
        residuals = y - regression_line
        std = np.std(residuals)
        r_squared = 1 - np.sum(residuals**2) / np.sum((y - np.mean(y))**2)
        self.levels['trend'] = {
            'regression': regression_line[-1],
            'upper': regression_line[-1] + 2 * std,
            'lower': regression_line[-1] - 2 * std,
            'slope': b,
            'r_squared': r_squared,
            'strength': 'strong' if r_squared > 0.7 else 'moderate' if r_squared > 0.4 else 'weak'
        }
        return self.levels['trend']

    def price_memory(self, min_touches=2):
        """Fiyat Hafizasi Algoritmasi - Dokunma sayisi bazli bolge tespiti"""
        atr = self.df['ATR'].iloc[-1]
        zone_width = 0.25 * atr
        all_levels = []
        if 'swings' in self.levels:
            for _, price in self.levels['swings']['highs'][-self.memory_lookback:]:
                all_levels.append(price)
            for _, price in self.levels['swings']['lows'][-self.memory_lookback:]:
                all_levels.append(price)
        if 'pivot' in self.levels:
            all_levels.extend([v for k, v in self.levels['pivot'].items() if k != 'PP'])
        
        zones = []
        used = set()
        for i, level in enumerate(all_levels):
            if i in used: continue
            cluster = [level]
            used.add(i)
            for j, other in enumerate(all_levels):
                if j not in used and abs(level - other) <= zone_width:
                    cluster.append(other)
                    used.add(j)
            center = np.mean(cluster)
            touches = len(cluster)
            if touches >= min_touches:
                zones.append({
                    'center': center, 'touches': touches,
                    'lower': center - zone_width / 2, 'upper': center + zone_width / 2,
                    'strength': 'STRONG' if touches >= 3 else 'MODERATE'
                })
        self.memory_zones = sorted(zones, key=lambda x: x['touches'], reverse=True)
        return self.memory_zones

    def check_retest(self, current_price, level, direction='long'):
        """
        Retest algoritmasi - Fiyatın bir seviyeye yakın olup olmadigini kontrol et
        direction: 'long' (destek retesti) veya 'short' (direnc retesti)
        """
        atr = self.df['ATR'].iloc[-1]
        tolerance = self.tolerance_atr * atr
        distance = abs(current_price - level)
        if distance <= tolerance:
            return True, distance / atr  # Retest gecerli, ATR bazli mesafe dondur
        return False, None

    def generate_signals(self):
        """Butunsel sinyal uretimi - Confluence prensibi"""
        if self.df.empty: return []
        last = self.df.iloc[-1]
        price = last['close']
        atr = last['ATR']
        signals = []
        confluence_score = 0
        max_score = 0

        # 1. Trend Kanali Analizi
        if 'trend' in self.levels:
            trend = self.levels['trend']
            max_score += 25
            if price < trend['lower']:
                signals.append(f"TREND: Fiyat alt kanalin altinda ({trend['lower']:.2f})")
                confluence_score += 25
            elif price > trend['upper']:
                signals.append(f"TREND: Fiyat ust kanalin ustinde ({trend['upper']:.2f})")
            elif trend['slope'] > 0 and price > trend['regression']:
                signals.append("TREND: Yukselen trend, regresyon uzerinde")
                confluence_score += 15
            elif trend['slope'] < 0 and price < trend['regression']:
                signals.append("TREND: Dusen trend, regresyon altinda")

        # 2. Pivot Noktalari Analizi
        if 'pivot' in self.levels:
            pivots = self.levels['pivot']
            for name, level in pivots.items():
                is_ret, dist = self.check_retest(price, level)
                if is_ret:
                    direction = 'long' if 'S' in name else 'short'
                    signals.append(f"PIVOT: {name} retest ({level:.2f}, {dist:.2f}ATR)")
                    max_score += 20
                    if direction == 'long' and price > pivots['PP']:
                        confluence_score += 20
                    elif direction == 'short' and price < pivots['PP']:
                        confluence_score += 20

        # 3. Fiyat Hafizasi Analizi
        for zone in self.memory_zones[:4]:
            if zone['lower'] <= price <= zone['upper']:
                signals.append(f"MEMORY: {zone['strength']} bolge ({zone['touches']}x, {zone['center']:.2f})")
                max_score += 20
                confluence_score += 20

        # 4. VWAP Analizi
        if 'VWAP' in self.df.columns:
            max_score += 15
            if price > last['VWAP'] + 2 * atr:
                signals.append("VWAP: Fiyat VWAP+2σ uzerinde (asiri uzamis)")
            elif price < last['VWAP'] - 2 * atr:
                signals.append("VWAP: Fiyat VWAP-2σ altinda (asiri uzamis)")
                confluence_score += 15
            elif price > last['VWAP']:
                confluence_score += 10

        confidence = (confluence_score / max_score * 100) if max_score > 0 else 0
        signals.append(f"\nCONFLUENCE SKORU: {confluence_score}/{max_score} (%{confidence:.0f})")
        
        if confidence >= 70:
            signals.append("==> GUCLU SINYAL - Islem degerlendirilebilir")
        elif confidence >= 40:
            signals.append("==> ZAYIF SINYAL - Diger onaylar beklenmeli")
        else:
            signals.append("==> SINYAL YOK - Bekleme modu")
            
        return signals

    def run_full_analysis(self, prev_high, prev_low, prev_close):
        """Tam analiz pipeline'ini calistir"""
        self.calculate_atr()
        self.calculate_pivot_points(prev_high, prev_low, prev_close)
        self.detect_swings()
        self.calculate_vwap()
        self.detect_trend_channel()
        self.price_memory(min_touches=2)
        return self.generate_signals()
```

### 9.2 Sistem Bilesenlerinin Kullanimina Iliskin Ornekler

Yukarida tanimlanan `DayStructureAnalyzer` sinifi asagidaki sekilde kullanilabilir. Bu ornek, sistemin tum modullerinin nasil baslatilacagini ve bir sinyal uretim surecinin nasil calistirilacagini gostermektedir.

```python
import pandas as pd
import numpy as np

# 1. Ornek Veri Olusturma (Gercek veri yerine)
np.random.seed(42)
dates = pd.date_range('2024-01-15 09:30', periods=500, freq='5min')
returns = np.random.normal(0.0002, 0.001, 500)
trend = np.linspace(0, 0.05, 500)
price_changes = returns + trend/100
close = 150 * np.exp(np.cumsum(price_changes))
high = close * (1 + np.abs(np.random.normal(0, 0.001, 500)))
low = close * (1 - np.abs(np.random.normal(0, 0.001, 500)))
open_p = close + np.random.normal(0, 0.1, 500)
volume = np.random.randint(100000, 500000, 500)

df = pd.DataFrame({'open': open_p, 'high': high, 'low': low, 
                   'close': close, 'volume': volume}, index=dates)

# 2. Sistem Baslatma ve Calistirma
analyzer = DayStructureAnalyzer(df, atr_period=14, swing_order=8, 
                                tolerance_atr=0.15, memory_lookback=50)

# "Onceki gun" verileri (ornek)
prev_high = df['high'].iloc[:78].max()
prev_low = df['low'].iloc[:78].min()
prev_close = df['close'].iloc[78]

# Tam analizi calistir
signals = analyzer.run_full_analysis(prev_high, prev_low, prev_close)

# 3. Sonuclari Yazdirma
print("=== DAY STRUCTURE ANALIZ SONUCLARI ===\n")
print(f"1. Pivot Noktalari:")
for k, v in analyzer.levels['pivot'].items():
    print(f"   {k}: ${v:.2f}")

print(f"\n2. Trend Kanali:")
t = analyzer.levels['trend']
print(f"   Eğim: {t['slope']:.4f} ({'Yukari' if t['slope']>0 else 'Asagi'})")
print(f"   Guc: {t['strength']} (R²={t['r_squared']:.2f})")

print(f"\n3. Guclu Fiyat Hafizasi Bolgeleri:")
for z in analyzer.memory_zones[:3]:
    print(f"   ${z['center']:.2f} ({z['touches']} dokunma, {z['strength']})")

print(f"\n4. Sistem Sinyalleri:")
for sig in signals:
    print(f"   -> {sig}")
```

### 9.3 Gorsellestirme: Matplotlib ile Analiz Ciktisinin Cizilmesi

Sistemin urettigi analiz sonuclarini gorsellestirmek, hem backtesting hem de canli trading icin kritik oneme sahiptir. Asagida, sistemin tum bilesenlerini (fiyat, VWAP, pivotlar, swingler, trend kanali, fiyat hafizasi) bir arada gosteren bir Matplotlib grafigi olusturan kod parcasi verilmistir.

```python
import matplotlib.pyplot as plt

def plot_day_structure(analyzer):
    df_plot = analyzer.df
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), 
                             gridspec_kw={'height_ratios': [3, 1, 1]})
    fig.suptitle('Day Structure Algoritmik Analiz Grafiği', fontsize=14, fontweight='bold')

    # 1. Ana Fiyat Grafiği
    ax1 = axes[0]
    ax1.plot(df_plot.index, df_plot['close'], color='#2C3E50', lw=0.8, label='Kapanis')
    
    # VWAP ve Bantları
    ax1.plot(df_plot.index, df_plot['VWAP'], 'r--', lw=1, label='VWAP')
    ax1.fill_between(df_plot.index, df_plot['VWAP_upper2'], df_plot['VWAP_lower2'], 
                     alpha=0.08, color='red')

    # Pivot Seviyeleri
    colors_p = {'PP': 'purple', 'R1': 'green', 'R2': 'lightgreen', 
                'S1': 'orange', 'S2': 'darkorange'}
    for name, level in analyzer.levels.get('pivot', {}).items():
        if name in colors_p:
            ax1.axhline(y=level, color=colors_p[name], ls='-.', alpha=0.5, lw=1)

    # Swing Noktaları
    sh = df_plot.dropna(subset=['swing_high'])
    sl = df_plot.dropna(subset=['swing_low'])
    ax1.scatter(sh.index, sh['swing_high'], color='red', s=40, marker='v', 
                label='Swing High', zorder=5)
    ax1.scatter(sl.index, sl['swing_low'], color='green', s=40, marker='^', 
                label='Swing Low', zorder=5)

    # Trend Kanalı
    if 'trend' in analyzer.levels:
        recent = df_plot.tail(analyzer.trend_lookback)
        x_num = np.arange(len(df_plot) - analyzer.trend_lookback, len(df_plot))
        b, a = np.polyfit(x_num, df_plot['close'].tail(analyzer.trend_lookback), 1)
        trend_line = a + b * x_num
        residuals = df_plot['close'].tail(analyzer.trend_lookback) - trend_line
        std = np.std(residuals)
        ax1.plot(recent.index, trend_line, 'b-', lw=1.5, label='Trend')
        ax1.fill_between(recent.index, trend_line + 2*std, trend_line - 2*std, 
                         alpha=0.05, color='blue')

    # Fiyat Hafızası Bölgeleri
    for zone in analyzer.memory_zones[:3]:
        ax1.axhspan(zone['lower'], zone['upper'], alpha=0.1, color='gold')

    ax1.legend(loc='upper left', fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.3)

    # 2. ATR Grafiği
    ax2 = axes[1]
    ax2.fill_between(df_plot.index, df_plot['ATR'], alpha=0.3, color='purple')
    ax2.plot(df_plot.index, df_plot['ATR'], color='purple', lw=0.8)
    ax2.set_title(f'ATR (Volatilite/Sapma Payi) - Son: ${df_plot["ATR"].iloc[-1]:.4f}')
    ax2.grid(True, alpha=0.3)

    # 3. Hacim
    ax3 = axes[2]
    colors = ['green' if c >= o else 'red' for c, o in zip(df_plot['close'], df_plot['open'])]
    ax3.bar(df_plot.index, df_plot['volume'], color=colors, alpha=0.5, width=0.003)
    ax3.set_title('Hacim')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/mnt/agents/output/day_structure_full.png', dpi=150, bbox_inches='tight')
    plt.show()

# Grafiği çiz
plot_day_structure(analyzer)
```

## 10. BACKTESTING VE PERFORMANS ANALIZI

### 10.1 VectorBT Kutuphanesi ile Stratejinin Test Edilmesi

Bir algoritmik trading stratejisini canli piyasada kullanmadan once, gecmis veriler uzerinde kapsamli bir sekilde **backtest** (geri test) edilmesi hayati oneme sahiptir. Python ekosisteminde, **VectorBT** kutuphanesi, hizli ve esnek backtesting imkanlari sunan modern bir aractir. VectorBT, **vektorize islemler** sayesinde binlerce parametre kombinasyonunu saniyeler icinde test edebilir ve **look-ahead bias** (gelecege bakma yanilgisi) riskini minimize edecek sekilde tasarlanmistir [^48^], [^52^].

Day Structure stratejisini VectorBT ile test etmek icin oncelikle stratejinin sinyallerini (giris ve cikis sinyalleri) boolean (True/False) pandas Serileri olarak ifade etmek gerekir. `DayStructureAnalyzer` sinifindan elde edilen confluence skoru, bu sinyalleri olusturmak icin temel alinabilir. Ornegin, confluence skoru %70'in uzerine ciktiginda `entries` (giris) sinyali True, skor %30'un altina dustugunde ise `exits` (cikis) sinyali True olarak ayarlanabilir.

```python
# Ornek: VectorBT ile basit bir backtest yapisi
import vectorbt as vbt

# Sinyalleri olustur (Ornek mantik)
# analyzer sinifindan elde edilen confluence skorlarini bir seriye donustur
# confluence_scores = pd.Series(..., index=df.index)
# entries = confluence_scores > 70
# exits = confluence_scores < 30

# VectorBT ile backtest
# pf = vbt.Portfolio.from_signals(
#     close=df['close'],
#     entries=entries,
#     exits=exits,
#     freq='5m',
#     init_cash=100000,
#     fees=0.001 # %0.1 komisyon
# )
# print(pf.stats())
```

VectorBT'nin en guclu yanlarindan biri, **multi-timeframe analizi** desteklemesidir. Strateji, farkli zaman dilimlerindeki sinyallerin birlesimine gore calisacak sekilde ayarlanabilir. Ornegin, 1 saatlik grafikte trend yonu belirlenirken, giris ve cikis sinyalleri 5 dakikalik grafikteki confluence skorlarindan uretilebilir. Bu, stratejiyi daha saglam ve gercekci hale getirir [^48^], [^54^].

### 10.2 Performans Metrikleri: Sharpe Orani, Maksimum Dusus (Drawdown), Kazanma Orani

Bir backtestin basarisi, sadece toplam getiriye (return) bakilarak degerlendirilemez. Riskin de goz onunde bulundurulmasi gerektiginden, asagidaki temel performans metrikleri analiz edilmelidir [^52^], [^53^].

*   **Toplam Getiri (Total Return):** Stratejinin baslangic sermayesine gore ne kadar kar/zarar ettirdigini gosterir. Ancak tek basina yeterli bir olcu degildir.
*   **Sharpe Orani:** Getirinin, alinan riske (volatilite) gore ayarlanmis halidir. **Risk basina ne kadar ekstra getiri saglandigini** olcer. Yuksek bir Sharpe orani, stratejinin riski etkili bir sekilde yoneterek getiri sagladigini gosterir. Genellikle **1'in uzeri** kabul edilebilir, **2'nin uzeri** ise cok iyi olarak degerlendirilir.
*   **Maksimum Dusus (Max Drawdown - MDD):** Stratejinin, en yuksek degerinden (peak) en dusuk degerine (trough) olan en buyuk yuzdesel dususudur. Bu, **en kotu senaryoda karsilasilabilecek zarari** gosterir ve psikolojik olarak tolere edilebilecek risk sinirini belirlemeye yardimci olur. Dusuk bir MDD, stratejinin saglamliginin bir gostergesidir.
*   **Kazanma Orani (Win Rate):** Kapanan islemlerin yuzde kacinin karli oldugunu gosterir. Yuzde 50'nin uzeri, genellikle olumlu bir gostergedir. Ancak tek basina yeterli degildir; cunku kazanma orani dusuk olabilir ancak ortalama kazanc, ortalama kaybin cok ustunde olabilir (bu durumda strateji hala karli olabilir).
*   **Risk/Odul Orani (Risk/Reward Ratio):** Ortalama kazanilan miktarin, ortalama kaybedilen miktara oranidir. **1:2 veya daha yuksek** bir oran, stratejinin uzun vadede karli olmasi icin guclu bir gostergedir. Bu, her 1 dolar risk edildiginde en az 2 dolar kazanilmasi anlamina gelir.
*   **Profit Factor:** Toplam kazancin toplam zarara oranidir. **1'in uzeri**, stratejinin toplamda kar urettigini gosterir. **1.5 ve uzeri** genellikle iyi bir strateji olarak kabul edilir.

Bu metriklerin tumunun birlikte degerlendirilmesi, stratejinin guclu ve zayif yonlerinin tam bir resmini cizmeye yardimci olur. Ornegin, yuksek getiri ancak yuksek MDD ile birlikte geliyorsa, strateji cok riskli olabilir ve risk yonetimi parametreleri gozden gecirilmelidir [^52^].

### 10.3 Parametre Optimizasyonu ve Asiri-Uydurma (Overfitting) Riski

Bir stratejiyi backtest ederken, en iyi performansi veren parametreleri bulmak icin **parametre optimizasyonu** yapmak yaygin bir pratiktir. Ornegin, `DayStructureAnalyzer` icindeki `swing_order`, `tolerance_atr`, `trend_lookback` gibi parametrelerin farkli degerleri denenerek en yuksek Sharpe oranini veren kombinasyon bulunabilir. VectorBT, bu tur optimizasyonlari hizli bir sekilde gerceklestirmek icin elverislidir [^54^], [^58^].

Ancak parametre optimizasyonunda en buyuk tehlike **"asiri uydurma" (overfitting)** riskidir. Asiri uydurma, stratejinin parametrelerinin gecmis verilere o kadar iyi ayarlanmasi durumudur ki, strateji gecmisteki "gurultuyu" (noise) ve rastlantisal kalilari bir "sinyal" olarak ogrenir. Bu durumda, strateji backtestte muhtesem sonuclar verse de, gelecekte gorulmeyen yeni veriler karsisinda basarisiz olma olasiligi cok yuksektir. Asiri uydurmayi tespit etmek ve onlemek icin su yontemler kullanilir:

*   **In-Sample ve Out-of-Sample Testing:** Veri seti iki parcaya ayrilir. Parametre optimizasyonu sadece **"in-sample" (egitim)** verisi uzerinde yapilir. Bulunan en iyi parametreler daha sonra hicbir sekilde ayarlanmadan **"out-of-sample" (test)** verisi uzerinde calistirilir. Eger out-of-sample performansi, in-sample performansina gore cok duserse, bu asiri uydurmaya isaret eder.
*   **Walk-Forward Analysis:** Bu, daha gelismis bir test yontemidir. Veri seti, art arda gelen pencerelere (ornegin her biri 6 aylik) ayrilir. Her pencerede optimizasyon yapilir ve bulunan parametreler bir sonraki pencerede test edilir. Bu surec tum veri seti boyunca tekrarlanir. Bu yontem, stratejinin zaman icinde degisen piyasa kosullarina ne kadar iyi uyum sagladigini gosterir.
*   **Parametrelerin Saglamligi:** Eger stratejinin performansi, parametrelerde kucuk degisiklikler yapildiginda cok buyuk dalgalanmalar gosteriyorsa, bu stratejinin asiri uydurulmus olabilecegine isaret eder. Saglam bir strateji, parametrelerin bir araligi boyunca tutarli bir performans gostermelidir.
*   **Monte Carlo Simulasyonu:** Backtest sonuclarinin ne kadar guvenilir oldugunu test etmek icin kullanilir. Islem sirasi rastgele karistirilarak veya getiriler uzerinde rastgele degisiklikler yapilarak binlerce farkli senaryo simule edilir. Eger strateji bu simulasyonlarin buyuk cogunlugunda basarisiz oluyorsa, orijinal backtest sonucu sadece sans eseri iyi cikmis olabilir [^64^].

Bu yontemlerin dikkatli bir sekilde uygulanmasi, gelistirilen Day Structure stratejisinin gercek piyasa kosullarinda da saglam ve guvenilir bir performans sergileme olasiligini onemli olcude artirir.

## 11. Ileri DUZEY KONULAR VE SISTEM GELISTIRME

### 11.1 Piyasa Rejimi Tespiti: Trend, Aralik ve Volatil Piyasalar

Bir Day Structure sisteminin en buyuk zorluklarindan biri, **piyasa rejiminin (market regime)** surekli degismesidir. Bir strateji guclu bir trend yapan piyasada muhtesem calisabilir ancak yatay (aralik) bir piyasada surekli zarar edebilir. Bu nedenle, algoritmik sistemin mevcut piyasa kosullarini tespit ederek **stratejisini buna gore adapte etmesi** (adaptive trading) kritik oneme sahiptir. **Piyasa rejimi tespiti**, piyasanin trend mi, aralik mi yoksa yuksek volatilite mi oldugunu belirleme surecidir [^73^], [^74^].

**Rejim Tespit Yontemleri:**
1.  **Istatistiksel Modeller:**
    *   **GARCH Modelleri:** Volatilite clustering (volatilite kumelenmesi) olayini modelleyerek yuksek ve dusuk volatilite donemlerini tahmin edebilir. `arch` kutuphanesi Python'da bu modelleri uygulamak icin kullanilir [^76^].
    *   **Markov Rejim Degisim Modelleri (Markov Regime Switching):** Piyasanin iki veya daha fazla farkli rejim (ornegin dusuk volatilite-yuksek volatilite veya yukselis-dusus) arasinda gectigini varsayar ve gecis olasiliklarini hesaplar. `statsmodels` kutuphanesi bu modelleri destekler [^76^].
    *   **Hidden Markov Models (HMM):** Gozlemlenen verilerin (getiriler) arkasinda gizli rejimler oldugunu varsayar ve bu rejimleri tahmin etmeye calisir. `hmmlearn` kutuphanesi bu amacla kullanilir [^77^].

2.  **Teknik Gosterge Bazli Yontemler:**
    *   **Trend Filter:** ADX (Average Directional Index) gostergesi, trendin guclulugunu olcer. **ADX > 25** genellikle guclu bir trendin, **ADX < 20** ise zayif bir trend veya aralik piyasasinin gostergesidir.
    *   **Volatilite Filter:** ATR'nin uzun vadeli ortalamasina gore mevcut ATR'nin durumu incelenir. Mevcut ATR'nin ortalamanin uzerinde olmasi yuksek volatiliteyi, altinda olmasi dusuk volatiliteyi gosterir.
    *   **Hareketli Ortalama Agilari:** Kisa, orta ve uzun vadeli hareketli ortalamalarin birbirine gore durumu (ornegin Heikin-Ashi Smoothed veya coklu EMA'lar) trend yonu hakkinda fikir verir.

**Adaptif Strateji Uygulamasi:**
Rejim tespit edildikten sonra, Day Structure sistemi stratejisini buna gore degistirebilir:
*   **Trend Piyasasi:** Sistem, kirilma (breakout) stratejilerine agirlik verebilir. Retest girislerini daha agresif bir sekilde degerlendirebilir. Trend kanali ve VWAP takibi on plana cikar.
*   **Aralik (Range) Piyasasi:** Sistem, "mean reversion" (ortalamaya donus) stratejilerine gecer. Fiyat kanalin ust bandina ulastiginda satar, alt bandina ulastiginda alir. Guclu pivot ve fiyat hafizasi seviyeleri onem kazanir.
*   **Yuksek Volatilite:** Sistem, islem buyuklugunu (pozisyonu) kucultebilir ve stop-loss'lari genisletebilir. Cunku yuksek volatilitede fiyatlar daha sert hareket eder ve yanlis kovulma olasiligi artar. Hatta cok yuksek volatilitede (ornegin VIX > 30) sistem tamamen islem yapmayi durdurabilir.

Bu adaptif yaklasim, tek bir stratejinin tum piyasa kosullarinda basarisiz olmasi yerine, **farkli ortamlarda farkli araclari kullanan esnek bir sistem** olusturmayi hedefler [^74^], [^77^].

### 11.2 Makine Ogrenmesi ile Sinyal Guclendirme

Day Structure sisteminin sinyalleri, makine ogrenmesi (Machine Learning - ML) modelleri ile guclendirilebilir. Geleneksel teknik analiz sinyalleri (ornegin, "fiyat S1'de ve trend kanali alt bandinda"), bir ML modeline **"ozellikler" (features)** olarak beslenebilir. Model, bu ozelliklerin gecmiste basarili islemlerle ne kadar korele oldugunu ogrenerek, yeni sinyallerin basari olasiligini tahmin edebilir [^41^], [^74^].

**Makine Ogrenmesi Entegrasyon Sureci:**
1.  **Ozellik Muhendisligi (Feature Engineering):** Day Structure sisteminin urettigi tum sayisal veriler ozellik olarak tanimlanir. Bunlar sunlari icerir:
    *   Fiyatin Pivot Point'e olan uzakligi (normalize edilmis).
    *   Fiyatin trend kanali ust/alt bandina olan uzakligi.
    *   Confluence skoru.
    *   Fiyat hafizasi bolgesindeki dokunma sayisi.
    *   ATR degeri (volatilite).
    *   VWAP'tan olan sapma (standart sapma cinsinden).
    *   Hareketli ortalama agilarinin durumu (ornegin 9 EMA > 21 EMA mi?).
    *   Momentum gostergelerinin degerleri (RSI, MACD).

2.  **Etiketleme (Labeling):** Gecmis veriler, belirli bir sure sonraki fiyat hareketine gore etiketlenir. Ornegin, bir sinyal noktasindan 5 mum sonra fiyat yukseldiyse etiket "1" (basarili), dustuyse etiket "0" (basarisiz) olarak atanir.

3.  **Model Egitimi:** Etiketlenmis veriler uzerinde bir siniflandirma modeli (ornegin **Random Forest**, **XGBoost**, **Support Vector Machine** veya basit bir **Logistic Regression**) egitilir. Model, hangi ozellik kombinasyonlarinin basarili islemleri en iyi tahmin ettigini ogrenir.

4.  **Tahmin ve Sinyal Filtreleme:** Egitilen model, canli piyasada yeni bir sinyal uretildiginde, o anki ozellikleri kullanarak bu sinyalin basari olasiligini tahmin eder. Sistem, sadece modelin belirli bir esik degerinin (ornegin %65) uzerinde basari tahmin ettigi sinyallere gore islem acar. Bu, geleneksel confluence skorunun uzerine, **veri odakli bir ikinci bir dogrulama katmani** ekler.

Bu yaklasim, sistemin sadece onceden belirlenmis kurallara bagli kalmayip, **piyasanin gecmis davranislarindan surekli olarak ogrenerek ve kendini guncelleyerek** daha akilli hale gelmesini saglar. Ancak, makine ogrenmesi modellerinin de asiri uydurma (overfitting) riski tasidigi ve dikkatli bir sekilde validate edilmesi gerektigi unutulmamalidir [^74^].

### 11.3 Sistemin Farkli Enstrumanlara ve Zaman Dilimlerine Uyarlanmasi

Day Structure sisteminin mantigi, **evrensel bir cerceve** sunar ve farkli finansal enstrumanlara (hisse senetleri, forex pariteleri, emtialar, kripto paralar) ve farkli zaman dilimlerine uyarlanabilir. Ancak her enstruman ve zaman diliminin kendine ozgu karakteristikleri (volatilitesi, likiditesi, fiyat adimlari) oldugundan, sistemin parametrelerinin bu ozelliklere gore ayarlanmasi gerekir [^43^].

**Farkli Enstrumanlara Uyarlama:**
*   **Forex (EUR/USD, GBP/JPY vb.):** Cok sivi ve 5 gun 24 saat acik bir piyasadir. Gunluk kapanis saati (New York kapanisi) pivot noktalari ve gunluk referans seviyeleri icin kritiktir. Pip bazli sapma paylari yaygin olarak kullanilir. `tolerance_atr` parametresi (ornegin 0.1 - 0.2 ATR) dusuk tutulabilir cunku volatilite hisse senetlerine gore genellikle daha dusuktur.
*   **Hisse Senetleri (AAPL, TSLA vb.):** Borsa saatleri icinde (ornegin 09:30 - 16:00 EST) islem gorur. Gun acilisi (opening range) ve gun kapanisi cok onemlidir. Hisse senetleri daha sert hareket edebilir ve haber/sonuc (earnings) etkisine daha aciktir. `tolerance_atr` ve stop-loss katsayilari hissenin volatilitesine gore (ornegin TSLA icin daha yuksek) ayarlanmalidir.
*   **Emtialar (Altin, Petrol):** Guvenli liman varliklari olarak bilinir ve farkli bir dinamige sahiptirler. Ozellikle altin, forex'e benzer sekilde hareket edebilir. Ham petrol ise daha volatil olabilir ve jeo-politik olaylardan etkilenir.
*   **Kripto Paralar (BTC, ETH):** 7/24 acik, cok volatil ve "gap" (bosluk) riski olmayan bir piyasadir. Gunluk kapanis/yapisi farkli olabilir. Kripto paralarda swing tespiti icin `swing_order` daha yuksek tutulabilir cunku fiyatlar daha sert ve ani dalgalanmalar yapar. ATR bazli risk yonetimi burada cok daha kritiktir.

**Farkli Zaman Dilimlerine Uyarlama:**
Sistem, scalping (1-5 dk), gunluk trading (5-15 dk), swing trading (1-4 saat) veya pozisyon trading (gunluk) icin ayarlanabilir.

| Trading Stili | Zaman D. (Ana) | Zaman D. (Giris) | Swing Order | Tolerance ATR | Trend Lookback |
|---|---|---|---|---|---|
| **Scalping** | 1-5 dk | 1 dk | 2-3 | 0.1 - 0.15 | 10-20 |
| **Gunluk Trading** | 15-30 dk | 5 dk | 5-8 | 0.15 - 0.25 | 20-50 |
| **Swing Trading** | 4 saat | 1 saat | 8-12 | 0.2 - 0.3 | 50-100 |
| **Pozisyon Trading**| Gunluk | 4 saat | 12-20 | 0.25 - 0.4 | 100-200 |

Yukaridaki tablo, farkli trading stillerine gore sistemin temel parametrelerinin nasil ayarlanabilecegine dair bir rehber sunmaktadir. Bu ayarlamalar, her bir zaman diliminin dogal yapisina (ornegin, dusuk zaman dilimlerinde daha fazla gurultu, yuksek zaman dilimlerinde daha az sinyal) uyum saglamak icin kritiktir. Sistemin basarisi, bu parametrelerin dogru bir sekilde ayarlanmasina ve farkli enstrumanlar icin **backtesting** ile optimize edilmesine baglidir [^43^], [^64^].

## 12. SONUC VE TAVSIYELER

### 12.1 Sistemin Guclu ve Zayif Yonleri

Day Structure algoritmik trading sistemi, piyasanin yapisal ve davranissal yonlerini butunlesik bir sekilde analiz eden kapsamli bir cerceve sunmaktadir. Bu sistemin en belirgin guclu yonleri sunlardir:
*   **Butunlesik Analiz (Holistic Approach):** Sistem, tek bir gostergeye veya seviyeye bagimli kalmaz. Trend, momentum, volatilite, davranissal hafiza ve istatistiksel seviyeleri (pivotlar) bir araya getirerek **cok boyutlu bir analiz** sunar. Bu, tek bir aracin kurlganligini ortadan kaldirir.
*   **Objektif ve Tekrarlanabilir Kararlar:** Tum kurallar matematiksel olarak tanimlandigi icin sistem tamamen objektif calisir. Bu, insan psikolojisinden kaynaklanan hatalari (korku, asiri guven) elimine eder ve **tutarlilik** saglar.
*   **Dinamik Risk Yonetimi:** ATR bazli stop-loss ve pozisyon buyuklugu belirleme, sistemin **her piyasa kosulunda esnek ve adapte** bir risk yonetimi sergilemesini saglar. Bu, hesabin korunmasi acisindan kritiktir.
*   **Confluence (Coklu Dogrulama) Prensibi:** Farkli analiz modullerinin ayni yonde sinyal uretmesini bekleyerek **yanlis sinyalleri onemli olcude filtreler**. Bu, islem basari oranini artirir.
*   **Fiyat Hafizasi:** Piyasanin gecmis tepkilerini algoritmik olarak tespit ederek, insan gozunun kolayca kacirabilecegi **guclu istatistiki avantajlar** sunar.

Sistemin zayif yonleri ve dikkat edilmesi gereken noktalar ise sunlardir:
*   **Asiri Uydurma (Overfitting) Riski:** Cok sayida parametre icerdigi icin (swing_order, tolerance_atr, lookback periyotlari vb.), bu parametrelerin gecmis verilere asiri optimize edilme riski yuksektir. Bu nedenle, **Walk-Forward Analysis ve Out-of-Sample testing** gibi saglam validasyon yontemleri sarttir.
*   **Parametre Hassasiyeti:** Sistemin performansi, secilen parametrelere bagli olarak degisebilir. Farkli piyasa kosullarinda (trend vs. aralik) en iyi calisan parametreler farkli olabilir. Bu, **surekli monitorleme ve periyodik optimizasyon** gerektirir.
*   **Haber ve Beklenmedik Olaylar:** Sistem tamamen teknik analize dayalidir ve **temel analiz faktorlerini** (ekonomik veriler, sirket kar aciklamalari, jeo-politik olaylar) goz ardi eder. Bu tur olaylar, tum teknik seviyeleri gecersiz kilabilir. Bu nedenle, sistem **haber filtresi** ile birlestirilmelidir.
*   **Gecikme (Lag):** Bazi bilesenler (ornegin lineer regresyon kanali veya ATR hesaplamasi) gecmis verilere dayandigi icin dogalari geregi bir miktar gecikme icerir. Bu, cok hizli piyasa hareketlerinde sinyallerin biraz gec gelebilecegi anlamina gelir.

### 12.2 Pratik Uygulama Icin Adim Adim Baslangic Rehberi

Bu Day Structure sistemini pratikte uygulamaya baslamak icin asagidaki adimlar izlenebilir:

**Adim 1: Gelistirme Ortaminin Kurulmasi**
*   Python'in kurulu oldugundan emin olun.
*   Gerekli kutuphaneleri yukleyin: `pip install pandas numpy scipy matplotlib vectorbt yfinance`.
*   Bir Integrated Development Environment (IDE) kurun (ornegin VS Code, PyCharm veya Jupyter Notebook).

**Adim 2: Veri Edinimi ve Hazirlanmasi**
*   Uzerinde calismak istediginiz enstrumanin (hisse senedi veya forex) gecmis verilerini edinin. `yfinance` kutuphanesi hisse senetleri icin, `pandas_datareader` veya ozel bir API ise forex/ kripto icin kullanilabilir.
*   Veriyi `pandas.DataFrame` formatinda yukleyin. En azindan `open`, `high`, `low`, `close` ve `volume` kolonlarinin olmasi gerekir.

**Adim 3: Temel Sistemin Kurulmasi ve Calistirilmasi**
*   Bu raporda verilen `DayStructureAnalyzer` Python sinifini bir dosyaya kaydedin.
*   Verinizi yukleyerek sinifi baslatin ve `run_full_analysis()` metodunu calistirin.
*   Oncelikle sadece **sinyal uretimini** ve **gorsellestirmeyi** calistirarak sistemin nasil calistigini gozlemleyin. Hic islem acmadan, sadece sistemin urettigi sinyalleri ve confluence skorlarini inceleyin.

**Adim 4: Backtesting ve Parametre Optimizasyonu**
*   VectorBT kutuphanesini kullanarak, sistemin urettigi confluence skorlarina gore basit bir giris/cikis kurali olusturun (ornegin, skor > 70 ise gir, < 30 ise cik).
*   Stratejiyi en az 1-2 yillik gecmis veri uzerinde backtest edin.
*   `swing_order`, `tolerance_atr` ve `trend_lookback` gibi parametreleri degistirerek performansi (Sharpe orani, Max Drawdown) iyilestirip iyilestiremeyeceginizi arastirin. **Asiri uydurmaktan kacinmak icin In-Sample ve Out-of-Sample testlerini kullanin.**

**Adim 5: Paper Trading (Sanal Trading)**
*   Backtest sonuclarindan memnun kaldiktan sonra, sistemi canli piyasada, ancak **gercek para kullanmadan** calistirin. Bunun icin bir cok brokerin sundugu demo (paper trading) hesaplarini kullanabilirsiniz.
*   Sistemin gercek piyasa kosullarinda, slippage (kayma) ve komisyonlar dahil olmak uzere nasil calistigini gozlemleyin. Bu sure en az 1-2 ay surmelidir.

**Adim 6: Canli Tradinge Gecis ve Risk Yonetimi**
*   Paper trading basarili olduktan sonra, **cok kucuk bir sermaye ile** (hesabinizin sadece kucuk bir yuzdesiyle) canli tradinge baslayin.
*   Kesinlikle **%1-2 risk kuralina** uygun hareket edin. Hicbir islemde hesabinizin tamaminin %2'sinden fazlasini riske atmayin.
*   Sistemi surekli olarak monitorleyin ve gunluk/haftalik performansini kaydedin. Beklentiniz disinda bir performans sergilerse, tekrar optimize etmek icin backtest'e donun.

### 12.3 Gelecek Gelistirme Olanaklari

Bu Day Structure sistemi, saglam bir temel uzerine kurulmus olup, cesitli yonlerden daha da gelistirilebilir. Gelecekteki potansiyel gelistirme alanlari sunlardir:
*   **Makine Ogrenmesi Entegrasyonu:** Confluence skorunun uzerine, Random Forest veya XGBoost gibi bir siniflandirici model eklenerek sinyallerin basari olasiligi daha hassas bir sekilde tahmin edilebilir. Bu, sistemin **akilli ve adaptif** bir hale gelmesini saglar.
*   **Sentiment Analizi:** Sisteme, Twitter, Reddit gibi sosyal medya platformlarindan veya haber kaynaklarindan elde edilen **piyasa hissiyati (market sentiment)** verileri de entegre edilebilir. Bu, ozellikle haber kaynakli sert hareketlerde sistemin korunmasina yardimci olabilir.
*   **Portfoy Yonetimi:** Sistem tek bir enstrumana odaklanmak yerine, **birden fazla enstrumanin bir portfoyunu** yonetebilecek sekilde genisletilebilir. Bu, riskin cesitlendirilmesini ve daha istikrarli getiriler elde edilmesini saglar.
*   **Otomatik Islem Yurutme (API Entegrasyonu):** Sistem, Interactive Brokers, Alpaca veya Oanda gibi brokerlerin API'leri ile entegre edilerek **tamamen otomatik** bir trading botuna donusturulebilir. Bu, manuel mudahaleyi tamamen ortadan kaldirir.
*   **Rejim Tespitinin Gelistirilmesi:** Hidden Markov Models (HMM) veya Gaussian Mixture Models (GMM) gibi daha gelismis istatistiksel yontemler kullanilarak piyasa rejimi tespiti daha dogru hale getirilebilir. Bu, stratejinin farkli piyasa kosullarinda daha etkili bir sekilde adapte olmasini saglar.
*   **Order Flow Analizi:** Eger veri erisimi mumkunse, sistem **order flow** verileri (tick data, level 2 order book) ile guclendirilebilir. Bu, fiyat hareketinin arkasindaki gercek alis/satis baskisini anlamak icin cok daha derinlemesine bir analiz imkani sunar.

Bu gelistirme adimlari, sistemin sadece bir baslangic noktasi oldugunu ve **surekli ogrenme, test etme ve adapte etme** sureciyle zaman icinde cok daha guclu ve rafine bir hale getirilebilecegini gostermektedir.

---

## Kaynaklar

[^1^]: TradingSim, "Pivot Points Day Trading Guide 2026"
[^2^]: Bajaj Finserv, "Pivot Point: Definition, Formulas, Uses and Limitations"
[^3^]: TradeZella, "Vincent's Break & Retest Trading Strategy"
[^4^]: Naga, "Pivot Point Indicator: What Is It & How Does It Work?"
[^5^]: FXOpen, "What the Break and Retest Strategy Is and How It Works"
[^6^]: Edgeful, "Trading Pivot Points: Data-Backed Strategy for Futures Traders"
[^8^]: LuxAlgo, "Support & Resistance Zones Strength Classifier"
[^9^]: Heygotrade, "Support and Resistance Explained: Examples and How To Use"
[^14^]: Medium, "Using Previous Day's High/Low for Intraday Bias"
[^15^]: Capital.com, "Day trading: previous day's high (PDH) and low (PDL) explained"
[^16^]: TradingView, "Using Previous Day's High and Low to Decide Intraday Trend"
[^19^]: TradingView, "Previous Day & Week High/Low Levels"
[^20^]: Medium, "Finding local extrema in Crypto, Stocks and Forex using Python"
[^21^]: Stack Overflow, "Identifying minor swings with major swings - Price charts"
[^22^]: Devexperts, "Linear Regression Channel"
[^26^]: Medium, "Higher Highs, Lower Lows, and Calculating Price Trends in Python"
[^27^]: Medium, "Navigating Market Trends with Linear Regression Channels"
[^28^]: YouTube, "The 2 Lines That Predict Tomorrow's Trades"
[^29^]: Medium, "Comparative Analysis and Evaluation of Various Algorithmic Trading Strategies"
[^30^]: Forextester, "Linear Regression Channel: what makes a simple trend line so special?"
[^31^]: InsiderFinance, "Automatically Detect Key Levels in Python"
[^32^]: LuxAlgo, "Linear Regression: A Statistical Indicator Guide"
[^34^]: LuxAlgo, "Mean Reversion Strategies for Algorithmic Trading"
[^35^]: TradingView, "Multi-Timeframe Confluence System"
[^36^]: Ninza, "DeepStack Confluence"
[^37^]: QuantInsti, "Automated Trading Systems: Design, Architecture & Low Latency"
[^38^]: TradersPost, "Support Resistance Trading Automation"
[^39^]: Tradefundrr, "Multiple Timeframe Confluence Trading"
[^40^]: Medium, "Data Pipeline Design in an Algorithmic Trading System"
[^41^]: Stackademic, "Support Resistance and RSI: Automated Detection In Python"
[^42^]: Dev.to, "Algorithmic Trading Architecture and Quants"
[^43^]: Tradeciety, "How To Perform A Multi TimeFrame Analysis + 5 Strategies"
[^45^]: Medium, "Battle-Tested Backtesters: Comparing VectorBT, Zipline, and Backtrader"
[^46^]: Algotrading101, "Backtrader for Backtesting (Python) - A Complete Guide"
[^47^]: Bookmap, "Cumulative Volume Delta Trading Strategy"
[^48^]: PyQuantNews, "Intraday backtesting with VectorBT Pro"
[^49^]: TradeProAcademy, "Delta Profiles-The Secret Sauce of Successful Futures Trading"
[^50^]: Truedata, "Cumulative Volume Delta (CVD) & Volume Delta Trading Strategy"
[^51^]: QuantConnect, "Support & Resistance 'Touch Detection'"
[^52^]: Quantnomad, "Backtesting intraday stock strategies in Python with vectorbt"
[^53^]: PaperToProfit, "I Tested 87 Different Stop Loss Strategies"
[^54^]: Medium, "Backtesting with VectorBT: A Beginner's Guide"
[^55^]: Medium, "Auto Residual Range Calculator for TradingView"
[^56^]: OregonState, "Expansion & Contraction"
[^57^]: Sierachart, "VOLUME PROFILE Daily Session + Cumulative Delta"
[^58^]: YouTube, "Vectorbt for beginners - Full Python Course"
[^59^]: LuxAlgo, "5 ATR Stop-Loss Strategies for Risk Control"
[^60^]: AvaTrade, "Average True Range (ATR) Indicator & Strategies"
[^63^]: FXOpen, "Opening Range Breakout (ORB) Strategy Explained"
[^64^]: BuildAlpha, "Opening Range Breakout Strategy: Complete Guide"
[^65^]: PyQuantNews, "Kalman filters beat moving averages here"
[^66^]: TradersMastermind, "Opening Range Breakout Strategy: Rules & Settings"
[^67^]: LiteFinance, "Order Flow Trading with Footprint Charts"
[^68^]: QuantifiedStrategies, "Kalman Filter Trading Strategy"
[^69^]: Medium, "Order Flow Trading With NinjaTrader: Footprint Charts in Action"
[^70^]: ForexFactory, "Orderflow & Footprint Analysis: A Trader's Journey"
[^71^]: Medium, "Adaptive Kalman Filter Trading Strategy with Python"
[^72^]: OptionAlpha, "Opening Range Breakout Trading Strategy"
[^73^]: GitHub Topics, "market-regime"
[^74^]: QuantInsti, "Machine Learning for Market Regime Detection Using Random Forest"
[^75^]: TradingView, "Risk Management & Position Sizing in Trading"
[^76^]: Medium, "Volatility and Market Regimes: How Changing Risk Shapes Market Behavior"
[^77^]: QuantStart, "Market Regime Detection using Hidden Markov Models in QSTrader"
[^78^]: WrightResearch, "How to Identify and Trade the Rejection Candle Pattern?"
[^79^]: Bloomberg, "Pre- and Post-Market Trading For US Stocks"
[^80^]: Tradefundrr, "Long Wick Rejection Entry: A Comprehensive Guide"
[^81^]: Binance, "Understanding Price Action Rejection: A Comprehensive Guide"
[^82^]: InsiderFinance, "Python for Dynamic Position Sizing Based on Market Conditions"
[^83^]: Headway, "How Can You Effectively Identify and Trade Wick Rejection Patterns in Forex?"
[^84^]: TradingView, "Premarketlevels"