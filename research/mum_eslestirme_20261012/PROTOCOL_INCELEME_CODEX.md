# Mum Eşleştirme — v0.2 Protokol İncelemesi

**Tarih:** 2026-10-12.  
**İncelenen:** `PROTOCOL_TASLAK.md` v0.2, güncellenmiş tasarım v0.2 ve `fizibilite_4_nedensel.py`.  
**Kapsam:** Tasarım ve yöntem incelemesi. Yeni fiyat sonucu, yön/büyüklük etiketi veya backtest hesaplanmadı; mevcut fizibilite koşusu tekrar çalıştırılmadı. Aşağıdaki sayısal örnekler yalnız formül/takvim denetimidir. Protokol değiştirilmedi veya dondurulmadı.

## 1. Karar

v0.2, önceki incelemenin ana bulgularını büyük ölçüde karşılıyor: ortak ATR, geçmişte erişilebilir adaylar, kaynak metadata'sı, çekimserlik, hedefe ilk ulaşma, belirsiz/no-touch sınıfları, ayrı örnek sayıları ve kilitli ileri gölge eklenmiş. İç testin daha önce görülmüş veri olduğunu açıklaması da doğru.

**Henüz dondurmaya hazır değil.** Özellikle hedef birimleri, gerçek veri bölümleri, kapasite hesabı, birincil ölçüt/test ailesi ve ileri doğrulamanın bitiş kuralları kesinleştirilmeli. Ayrıca mevcut uzun-bağlam ızgarası kullanıcının sembole özel mum sayısı seçimi isteğini karşılamıyor.

## 2. Öncelikli düzeltmeler

### P1 — Y2'nin birimleri tutarsız (§6, satır 86)

Hedefler ATR biriminde deniyor; `r_H` boyutsuzsa `b=max(0,25·A_t, 2·spread)` fiyat birimindedir. Bunlar doğrudan karşılaştırılamaz.

**Önerilen açık sözleşme:**

```text
r_H(t) = (C[t+H] - C[t]) / A[t]
b_ATR(t) = max(0.25, 2 * spread_price(t) / A[t])
Y2 = up if r_H >= b_ATR; down if r_H <= -b_ATR; else flat
T_price(t) = T_ATR * A[t]
```

Spread'in fiyat birimine dönüşümü, geçmiş referans aralığı ve yalnız t'de bilinen ölçümden gelmesi de yazılmalı. Eski NDX/OIL sabitleri güncel ölçüm yerine kanıtlı varsayım olarak etiketlenmeli; spread bulunamayan dönemlerin politikası önceden sabit olmalı. Y3/Y5 bariyerlerinde T'nin ATR mi fiyat mı olduğu aynı sözleşmede yer almalı.

### P2 — Veri bölümleme tablosu bütün hücreleri kapsamıyor (§2, §7)

Uzun veri sütunu ≥3,5 yıl; kısa sütun 15–21 aylık 5m için. Yaklaşık üç yıllık NDX 15m hangi dala girecek? DAX 5m mevcut envanterde yok. NDX 5m'nin 21 aylık geçmişi ise Dukascopy + broker karışımı; yalnız broker politikasından sonra bu sürenin tamamı kullanılamayabilir.

“İlk %50 + sonraki üç ay + son dört ay” bütün veri süresini tek anlamlı biçimde bölmüyor. Örneğin 18 ayda ilk dokuz + üç + son dört ay, iki ayı belirsiz bırakıyor; çok kısa broker geçmişinde bölümler çakışabilir.

**Düzeltme:** Faz 0 sonrasında her sembol/TF için açık UTC kesim tarihleri, kaynak, başlangıç/son, geçerli bar sayısı ve destek durumu tabloya yazılsın. Sabit bir kural örneği: son dört ay test; ondan önceki üç ay kalibrasyon; daha önceki tüm uygun dönem geliştirme/başlangıç kütüphanesi. Asgari geçmişi sağlamayan hücre araştırmadan çıkarılsın veya yalnız bilgi profili olsun. Gerçek hipotez listesi bu destek tablosuyla dondurulsun; eksik hücreler başarı/başarısızlık gibi sayılmasın.

Geliştirme/kalibrasyon sınırlarını aşan sonuçlar ilgili eğitim/seçim işlemine girmemeli. İç testin F anında henüz çözülmemiş son H-bar sorguları beklemede kalmalı; bitişe kadar çözülmüş olanlarla raporlanmalı.

### P3 — “Uygun bar sayısı / (D+H)” genel kapasite formülü değil (§5.1)

Tam, kesintisiz ham bar aralığında `N/(D+H)` kaba olay yoğunluğu hesabıdır. Ancak `eligible(t)` içindeki **uygun aday bitişlerinin sayısını** bu formüle koymak hatalı olabilir. Örneğin 20 uygun adayın her biri 60 bar uzaktaysa D=33, H=20 ile 20 ayrı olay seçilebilir; `floor(20/53)` ise sıfır verir.

**Düzeltme:** Her aday için gerçek özellik/sonuç aralığını üret; maksimum çakışmasız aday sayısını aralık çizelgelemesiyle hesapla. Mesafeye göre açgözlü seçim daha az olay seçebilir; bu seçimin gerçek K'sı ayrıca tutulmalı. Genel arşiv yoğunluğu tahminiyle sorguya özgü kullanılabilir kapasite ayrı olsun. Nihai seçilmiş kohort üzerinde asgari olay kuralı denetlensin.

P33/5y/1d/H20 için toplam kapasitenin yaklaşık 24 olması ile en az 20 yakın olay istemek çok az pay bırakır. Bu profilin çoğu sorguda çalışacağı henüz ölçülmedi. Temiz veriyle **sonuçlara bakmadan**, kabul mesafesi sonrası kapsam/olay sayısı ölçülsün. Yetersiz hücreleri zorla etkinleştirmek yerine desteklenmiyor diye işaretlemek mümkündür.

### P4 — Uzun bağlamda “en iyi mum sayısı” henüz seçilmiyor (§4, H5)

R7 yedi mum; P33 ve P33Y hep 33 mum. İkiz'in 1–3 mum ızgarası var, uzun bağlamın derinlik ızgarası yok. R7/P33 kıyasında temsil türü ve mum sayısı birlikte değiştiğinden “en iyi uzun mum sayısı 33” sonucu çıkarılamaz.

**Öneri:** Birincil sabit P33 korunabilir. İkincil derinlik deneyinde yalnız Piramit D∈{9,17,33} kullanılsın; diğer ayarlar sabit olsun. Daha sonra yol özetinin katkısı sabit D'de karşılaştırılsın. Sonuç “denenen derinlikler arasında seçilen” diye sunulsun; evrensel optimum iddiası olmasın.

İkincil ızgara şu anda yaklaşık 50 bin test tarif ediyor. Birkaç yapılandırmayı değiştirmeye rağmen geniş aile içinde iyi bir hücre çıkması kolaylaşır. Önce küçük derinlik ve temsil karşılaştırmasını çalıştırmak, kapsamlı bağlam/10y/K/d_acc seçimlerini ayrı aşamaya bırakmak daha denetlenebilir. Tüm planlanan aşamalar ve bakışlar yine kayıtlı olmalı.

### P5 — Birincil başarı ölçütü ve çoklu test ailesi eksik (§1, §9, §12)

72 sembol×TF×ufuk hücresi var; H1, H2, H3'ün her biri ayrı iddia olduğu için tek scalar ölçütle bile toplam 216 aday hipotez olabilir. H1 ayrıca üç büyüklük ve beş kantil içeriyor; bunlardan hangisinin geçmesi H1'i geçirecek? H3'te hangi T ve hangi skor birincil? Her hedef için ayrı 72'lik aile kullanılacaksa aileler arası hata bütçesi açıkça bölünmeli.

**Düzeltme:** H1 için tek sabit birleşik kayıp veya tek ana hedef/kantil; H2 için Brier; H3 için sabit T=1 ve açık sonuç/skor tanımı seçilsin. Diğer hedefler ikincil/tanımlayıcı olabilir. Loss ortalamasının oranı ile skill oranlarının ortalaması aynı değildir; birleşim formülü yazılsın. Düzeltilmiş p-değerini üreten null testi ve bootstrap tekrar sayısı önceden sabitlensin. `P_bootstrap(skill>0)` ifadesi kendiliğinden Holm'e verilecek null p-değeri değildir.

Monte Carlo p-değeri `(1 + en az gözlenen kadar uç tekrar)/(B+1)` ile hesaplanırsa B=200 için en küçük değer ~0,00498'dir. Holm'ün 72'lik ailede ilk eşiği ~0,000694; 216'lık ailede ~0,000231'dir. Dolayısıyla **aynı 200 tekrarı hücre p-değeri için kullanmak yeterli değildir**. Bu çözünürlüğe erişmek için sırasıyla en az 1.439 ve 4.319 tekrar gerekir; bunlar yalnız matematiksel alt sınırlardır, hassasiyet garantisi değildir. Tek global maks-istatistik testinde α=0,05 için 200 tekrar başka bir kullanım olabilir; iki amacı karıştırmamak gerekir. İlgili p-değeri hesabı için [Romano–Wolf'un birincil çalışması](https://www.econ.uzh.ch/apps/workingpapers/wp/econwp219.pdf) referanstır.

### P6 — Çekimserlik ve taban karşılaştırması aynı sorgu kümesinde olmalı (§8–9)

Her motorun çekimser kaldığı sorgular farklı olabilir. Yalnız tahmin üreten sorguların ortalama becerisini kıyaslamak, farklı piyasa anlarını karşılaştırabilir. Çok küçük bir kapsama sahip model yüksek beceriyle “en iyi” seçilebilir.

**Düzeltme:** Birincil değerlendirme takvimi sabit olsun; çekimser sorguda ürünün verdiği taban dağılımı tam takvim skoruna girsin. Ek olarak yalnız tahmin üretilen aynı sorgularda model–taban eşli kayıp farkı ve kapsam raporlansın. Motorlar arası karşılaştırmanın ortak sorgu kümesi de ayrıca gösterilsin. Kalibrasyon ve iç test için asgari çözümlenmiş sorgu/blok sayıları önceden tanımlansın.

Her taban yalnız kendisi için anlamlı hedeflerde kullanılmalı. Küçük doğrusal/lojistik regresyon, büyüklük kantillerini nasıl verecek? Y3/Y5 için hangi çıktısı var? Tabanda bulunmayan çıktı için “hepsini geçer” şartı uygulanamaz. Hedef→taban→skor tablosu yazılsın. Rastgele komşular aynı uygunluk, kaynak, olay tekilleştirme ve K kurallarına tabi olsun. R7/P33 karşılaştırması yalnız geometriye farklı tarihsel bilgi hakkı vererek yapılmasın.

### P7 — Y3/Y5'in skorları ve belirsiz etiketler ayrılmalı (§6, §9)

Y5'te “H içinde +T'ye dokundu mu?” ikili olaydır; çok sınıflı log-loss diye tarif edilmesi net değil. Y3 dört gözlenen sınıf olarak skorlanabilir, fakat “sırası belirsiz” piyasanın bir yönü değil, veri çözünürlüğü durumudur. H3'ün gerçek ilk ulaşma olasılığı ile dört gözlenen sınıfın başarısı aynı iddia değildir.

**Düzeltme:** Y3'ün dört-sınıf gözlem skoru ve gerçek ilk-ulaşma olasılığının belirsizlik sınırları ayrı olsun. H3 için hangisinin birincil olduğu yazılsın. Y5'in dokunma olayı ikili Brier/log-loss, bariyer yarışı ise açık çok-sınıflı veya sınırlandırılmış skor kullansın. 1m bar bile aynı dakikada iki bariyere dokunursa sıra hâlâ bilinmeyebilir. Çözüm hiyerarşisi, 1m kaynak/kapsam kuralı ve çözülmeyenlerin skoru bütün dönemlerde sabit olsun. Sıfır olasılıkların log-loss'u için yumuşatma/clipping kuralı da dondurulsun.

Y5 burada 0,5/1/1,5/2 ATR hedeflerle hesaplanıyor; seçime katılıp katılmadığı ve rozetinin hangi kanıttan geldiği açık değil. Daha fazla hedef ve ufku inceleyip yalnız iyi olanı göstermek seçim ailesini büyütür. Net hareket kantilleri de ürün için gerekli: protokol Y4 yalnız `|r_H|` diyor, tasarım imzalı `r_H` bekliyor. İmzalı/işaretsiz çıktılar ayrı tanımlansın. MFE/MAE'nin sıfırdan başlayan ve pozitif/negatif işaret sözleşmeleri yazılsın.

### P8 — Takvim-hafta kaydırması tek başına geçerli null garantisi değil (§10)

Haftagünü/saat eşleştirme önceki rastgele bar kaydırmasından daha açıklayıcı. Fakat aynı UTC saati, DST geçişleri arasında aynı yerel seans değildir; yerel saat kullanılsa bile Avrupa/ABD seans kesişimi değişebilir. Rejim ve oynaklık devirleri korunmaz. Eksik eşleşen barların atılması sorgu kümesini ve skor dağılımını tekrarlar arasında değiştirebilir. Her sorguya ayrı k seçilirse otokorelasyon da korunmaz.

**Düzeltme:** Her tekrarda ortak mı ayrı mı k kullanılacağı, zaman ekseni, dairesel sınır, tatil/eksik bar davranışı, sonuç paketinin birlikte kaydırılması ve sabit destek kümesi açıkça yazılsın. Haftalık kaydırma önce duyarlılık/null denetimi olarak kalsın; doğrulama testi eşli kayıp farklarına uygun, zaman bağımlılığını taşıyan blok yaklaşımıyla tanımlansın. Ortak maks-istatistikte TF/semboller arası bağımlılık için eşzamanlı takvim blokları gerektiği değerlendirilsin. [Romano–Shaikh–Wolf'un yöntem açıklaması](https://www.econ.uzh.ch/dam/jcr:e2d4e460-63dd-4908-8502-7357c570c5a0/palgrave_2010.pdf), bağımlı zaman verisinde uygun zaman serisi bootstrap'ının gereğini açıklar.

Gerçek getiri bloklarını tekrar örneklemek sıfır tahmin gücü yaratmaz: bloklarda momentum ve büyüklük bilgisi kalabilir. Oynaklık kümelenmeli sentetik seride uzun şekil ATR+saat tabanına gerçekten katkı verebilir. Bu nedenle “sentetikte skill mutlaka ≈0” sızıntı kanıtı olarak kullanılmasın. Sızıntı için prefix/kapanış-zamanı testleri; yanlış pozitif oranı için koşullu veri üretimi bilinen null simülasyonu ayrı tasarlansın.

### P9 — İleri gölge için tek örnek eşiği ve bitiş kuralı uygun değil (§7, §11–12)

Her günlük kapanışta tahmin toplamak H=20-bar sonuçları bağımsız yapmaz. Sorguları H aralıklı tutma kuralıyla 100 adet günlük H=20 tahminin sonuçlarının tamamlanması yaklaşık 2.000 işlem günü, yılda ~252 işlem günü varsayımıyla yaklaşık sekiz yıl ister. H=5 için yaklaşık iki yıl, H=1 için en az 100 işlem günü gerekir. Bunlar sadece sonuç çakışmasını kaldıran yaklaşık alt sınırlardır; tam istatistiksel bağımsızlık garantisi değildir. “≥3 ay” mantıksal olarak sekiz yılı dışlamaz ama ürün doğrulamasının pratik beklentisini açıklamıyor.

**Öneri:** Her profilde gerçek sorgu sayısı, çakışma/blok yapısı, asgari blok sayısı ve planlanan karar tarihi ayrı olsun. Örtüşen tahminler kaydedilebilir; belirsizlik uygun bloklarla hesaplanır, bunlar 100 bağımsız olay diye adlandırılmaz. Uzun ufukta üç ay yeterli blok sağlamazsa profil bilgi düzeyinde kalır. Günlük/uzun ufuk için kısa sürede “kesinleşti” vaadi verilmesin.

İleri dönemde her yeni veriyle aralığa bakıp ilk sıfırı dışladığı gün rozet vermek tekrarlı sınamadır. Tek planlı değerlendirme veya önceden tanımlanmış sıralı-test/hata bütçesi, aile düzeltmesi ve sürüm değiştirme kuralı yazılsın. “100 olunca” tek belirli değerlendirme de seçilebilir; örnek sayısı her sonuç görüldükten sonra değiştirilmesin. Kullanıcı tıklamalarıyla otomatik sorgular ayrılmaya devam etsin.

## 3. Tekrarlanabilirlik için tamamlanacak teknik ayrıntılar

- **Katı/yoğun kohort:** Protokol §5.1 katı kohortla tahmin diyor; tasarım §7.2/Ek A yoğun kohortla tahmin, katı kohortla yeterlilik denetimi yapıyor. Birincil yöntem tek olmalı. Birincil/ikincil kohort farkı ayrı yapılandırma olarak sayılabilir.
- **Asıl bilgi aralığı:** İkiz/R7'nin ATR'si görünür X'in öncesine bakıyor; TR önceki kapanışı da ister. P33Y'deki `C[e−33]` mevcut pencerenin 33 mumundan bir mum daha eski. Bağlamın EMA/100-bar/1-yıllık istatistikleri de daha uzun geçmişe bağımlı. Çakışmazlık yalnız ana şekil penceresi içinse buna “tam bağımsız” denmesin; veri yeterliliği ve blok tasarımı bütün bağımlılıkları dikkate alsın.
- **P33Y sınır durumları:** Tepe ve dip aynı mumdaysa işaretin değeri; eşit uçlarda hangi bar seçildiği; sıfır verimlilik paydası; sıfır grup varyansı davranışı tanımlansın. D=33 için e−32/e−33 tercihi ve beklenen boyut testle sabitlensin.
- **Dondurulanlar/uyarlananlar:** d_acc ve ölçekler geliştirmede sabit mi, `eligible(t)` ile her t'de yeniden mi hesaplanıyor? Kalibrasyon testi sırasında güncelleniyor mu? İki seçenek de koşullu olarak nedensel olabilir; güncelleme takvimi ve yalnız çözülmüş sonuç kullanımı önceden belirlenmeli.
- **Zaman sözleşmesi:** `j+H≤t` indeks-zaman karışımını önlemek için `close_ts[j+H] <= as_of_utc` ve uygun bar dizisiyle yazılsın. Üst-TF kova bitişi, mum başlangıcı ve sorgu karar anı ayrı alanlar olsun.
- **UTC kabul:** Bağımsız referansın sembol/enstrüman/zaman dilimi, karşılaştırma dönemi, gecikme tarama aralığı, tepe ayrışması toleransı ve referans yoksa davranış tanımlansın. Gürültülü/sığ veride tek korelasyon tepesinin sıfır olması tek başına saat kanıtı değildir.
- **Son sayımın sınırı:** `fizibilite_4` ortak ölçek ve geçmiş uygunluğunu gerçekten ekliyor. Ancak satır 83'te olay aralığı `max(X,H)`; protokoldeki X+H ayrılığı değil. Satır 37'de 4h için üç, günlük için 12 alt-bar kabulü tam kova denetimi değil. Satır 38 kaydırılmış yerel kova zamanını yaklaşık UTC diye etiketliyor. Temizlik henüz koşuya dahil olmadığı tasarımda açıklanmış; bu sayımlar nihai protokolün veri/kohort kabul testi yerine geçmemeli.
- **Dondurma kaydı:** Son belge hash'i yanında kabul edilmiş veri manifesti, kod sürümü, somut hipotez/yapılandırma listesi, seed ve ortam kaydı bulunsun. Belge hash'inin kaydını belge içine yeniden yazarak kendini değiştiren hash döngüsü oluşturulmasın.

## 4. Dondurmadan önce asgari teslim paketi

1. Gerçek broker geçmişine göre destek/bölümleme tablosu; açık UTC sınırları.
2. Tek hedef/birim, temsil/information-lookback ve kohort sözleşmesi.
3. Ana scalar ölçütler, desteklenen hipotez listesi ve hata bütçesi.
4. Kapasite aralık seçimi, kabul sonrası örnek/kapsam fizibilitesi; sonuç etiketi gerektirmez.
5. Çekimserlik dahil sabit takvim skoru, eşli kıyas ve hedefe uygun tabanlar.
6. Uygulanabilir null, bootstrap blok/tekrar sayıları ve p-değeri yöntemi.
7. Sembole özel küçük derinlik deneyi; ileri değerlendirme tarihi/blok sayısı/tekrarlı bakış politikası.

Bu paket tamamlanınca yöntem dondurulabilir; sonuç hesapları daha sonra başlar. Kod geliştirmeye geçmek için ön-kayıttaki her hedefin önceden başarılı olmasını beklemek gerekmez, fakat başarı rozetleri protokolün kanıt seviyesine bağlı kalmalıdır.

## 5. Diğer agente iletilebilecek kısa revizyon isteği

> Protokol v0.2 önceki incelemeyi büyük ölçüde karşılıyor; henüz dondurma. Y2'yi ATR biriminde tutarlı yaz. Broker-only veri kabulünden sonra her sembol/TF için gerçek UTC bölümleme ve destek tablosunu çıkar; üç yıllık NDX 15m ve bulunmayan DAX 5m'yi açıkça ele al. Kapasiteyi eligible aday sayısını D+H'ye bölerek değil gerçek aralık seçimiyle hesapla. H5'e sabit diğer ayarlarla D=9/17/33 küçük Piramit derinlik deneyi ekle. H1/H3 ana scalar skorunu, H3 T'sini, tüm test ailesini ve Holm p-değerinin üretim yöntemini sabitle; 200 tekrarlık global null ile küçük hücre p-değeri hesabını ayır. Çekimserlik dahil sabit takvim ve aynı sorgularda eşli kıyas kullan. Y3 belirsiz gözlem sınıfı ile gerçek ilk-ulaşma sınırlarını, Y5 ikili olay skorlarını, imzalı net hareketi ayrı tanımla. Haftalık kaydırmanın DST/rejim/eksik bar/ortak k varsayımlarını yaz; bilinen null simülasyonunu gerçek getiri blok-bootstrap'ından ayır. İleri gölgede günlük H20 için 100 bağımsız tahminin yaklaşık sekiz yıl gerektirdiğini açıkla; profile göre blok/karar zamanı ve tekrarlı bakış politikasını dondur. Katı/yoğun kohort, gerçek özellik geçmişi ve online güncelleme kuralları tasarım ve protokolde aynı olsun. Sonuç etiketi hesaplamadan v0.3 taslağını hazırla.
