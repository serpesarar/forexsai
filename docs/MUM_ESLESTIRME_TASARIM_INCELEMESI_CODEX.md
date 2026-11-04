# Mum Eşleştirme Motoru — Tasarım İncelemesi ve Geliştirme Önerisi

**Tarih:** 2026-10-12  
**İncelenen tasarım:** `docs/MUM_ESLESTIRME_ALGORITMASI.md`, v0.1.  
**Kapsam:** Tasarım, mevcut fizibilite betikleri ve doğrudan ilgili proje kodu incelendi. Yeni yön/büyüklük deneyi veya backtest çalıştırılmadı; mevcut ölçümler yeniden üretilmedi. Aşağıdaki geliştirmeler araştırma önerisidir, kanıtlanmış tahmin gücü değildir. Ana tasarım belgesi değiştirilmedi.

## 1. Değerlendirme

Öneri sağlam bir başlangıç: kapanmış mum, kaynak tutarlılığı, ATR ölçeği, taban kıyası, kronolojik sınama, geçmişte başarısız olan çalışmaların dikkate alınması ve araştırma/servis için aynı çekirdek doğru seçimler. Kullanıcının istediği düğme, geçmiş örnekler ve olası hareket aralığı bu yapıdan üretilebilir.

Ancak v0.1 henüz uygulama sözleşmesi olarak dondurulmamalı. Eşleşme geometrisiyle tahmin başarısı birbirine karışan birkaç yerde ayrılmalı; fizibiliteyle nihai temsil aynılaştırılmalı; hedefe ulaşma, yetersiz benzerlik ve bağımsız örneklem tanımları tamamlanmalı.

Öncelikli karar: **İkiz + düşük boyutlu bağlam eşleştirmesi korunmalı; Piramit'in ana tahmin motoru seçilmesi sonuç sınamasına bırakılmalı.**

## 2. Önce düzeltilmesi gereken bulgular

### 2.1. Fizibilite sayımları tarihsel anda kullanılabilecek kütüphaneyi ölçmüyor

`fizibilite_1_birebir.py:36–37` adayın sorgudan uzak olmasını ve dosyanın son barından önce olmasını istiyor; adayın sorgudan önce olması şartı yok. `fizibilite_2_huni_kismi_knn.py` ve `fizibilite_3_piramit.py` de dosyanın sorgudan sonraki bölümünü aday havuzuna alıyor.

Bu, gelecek getiriye bakılarak bulunmuş bir yön başarısı değildir: betikler yalnız eşleşme sayısı/mesafesi ölçüyor. Fakat tarihsel anda erişilebilir eşleşme sayısını fazla gösterebilir. Nihai motor, adayın sonuç ufkunun da karar anından önce kapanmasını isteyeceği için kullanılabilir örnek sayısı ayrıca azalır.

**Düzeltme:** İki ölçüm ayrı verilsin: tüm arşivde geometrik tekrar sayısı ve tarihsel karar anında erişilebilir tekrar sayısı. Profil araştırmasının fizibilitesi ikinci ölçüme dayansın; tüm motorlarda aynı kapanış zamanı ve sonuç uygunluğu maskesi kullanılsın.

### 2.2. ATR normalizasyonu betikler arasında ve tasarımla farklı

`fizibilite_1_birebir.py:55` ve ikinci betik her mumun özelliklerini o mumun kendi önceki ATR'sine bölüyor. Bir X-mum eşleşmesinde bu, her geri adımda başka ölçek demek. Tasarım §6.1 ise pencerenin tüm mumlarını **pencere sonunun önceki ATR'sine** bölüyor. Üçüncü betikteki Piramit ve ham-pencere karşılaştırması bu ortak pencere ölçeğini kullanıyor.

İki yöntem de sorgu sonunda nedensel olabilir; fakat aynı benzerlik tanımı değildir. İlk ikisinin ölçümlerini ortak ölçekli İkiz/Hibrit'in kanıtı gibi kullanamayız.

**Düzeltme:** Tek özellik sözleşmesi ve tek ATR hesaplama tanımı oluşturulsun. Basit hareketli TR ortalaması mı, Wilder ATR mi olduğu da yazılsın; mevcut betikler basit 14-bar ortalaması kullanıyor. Nihai tanımla sayımlar yeniden yapılsın. Ortak ölçek pencere içindeki büyük/küçük mum ilişkisini koruduğu için makul başlangıçtır.

### 2.3. X sınırı ve RC yorumları fazla kesin

`N·p₁^X` bağımsızlık benzeri varsayımlar altında kaba beklentidir. Mumların seans ve oynaklık bağımlılığı, sorgunun yapısı ve çakışmaları bu beklentiyi değiştirir. Medyan sorguda 0 eşleşme bulunması her sorguda 0 bulunacağı anlamına gelmez.

Bu nedenle “10–20 mum fiziksel olarak mümkün değil” yerine “ölçülen toleranslarda çoğu sorguda yeterli örnek bulunması beklenmiyor” denmeli. İkiz modunda kullanıcı daha uzun X arayabilsin; sonuç yoksa veya örnek azsa bu gösterilsin. Araştırma profilleri için X=1–3 başlangıç aralığı korunabilir.

RC=2,6 komşuların mesafe bakımından daha iyi ayrıldığını gösterir; yön veya büyüklük tahmininin iyileştiğini göstermez. RC=1,5 de tek başına rastgele seçimle aynı sonuç verdiğinin kanıtı değildir. **Piramit'in ham 7 mum üzerine katkısı, gelecekteki sonuçları tahmin ederken ayrıca sınanmalı.**

### 2.4. Kütüphane temizliği henüz mevcut sayımın parçası değil

`_common.py:42–47` kaynağı varsa filtreliyor, sıralıyor ve son beş yılı kesiyor. Burada boşluk/segment, çakışan timestamp, eksik üst-TF kova ve fiyat hatası denetimleri bulunmuyor. Bunlar tasarımda gelecekte yapılacak işler; mevcut sayımlara uygulanmış kabul edilmemeli.

NDX 5m/15m için `_common.py` açıklamasında Dukascopy 2025 + Pepperstone 2026 yazıyor. `src` kolonu olmayan dosya da yükleniyor. Dolayısıyla mevcut fizibilitenin tamamı “tek broker kaynağı” standardında yapılmış sayılmaz.

**Düzeltme:** Kaynak, broker, enstrüman türü, saat dönüşümü ve mum hizası açık metadata olsun. Kaynağı bilinmeyen satırlar doğrulanmış profile girmesin. Planlı piyasa arası ile eksik veri ayrı işaretlensin; dört günden kısa gerçek veri kesintileri de pencereleri geçersiz kılabilsin. Üst-TF mum yalnız beklenen alt-bar kapsamı tamamlandıysa kullanılsın. Petrol boşluğunu yalnız >3 ATR diye devir saymayalım: gerçek haber sıçramasıyla ayırmak için kontrat/devir kaydı gerekli.

### 2.5. Saat dönüşümü her kaynakta otomatik −2/−3 saat olamaz

Projede kaymış broker kayıtları yaşanmış ve mevcut kaydedici offset ölçüyor. Bu geçmiş kanıt korunmalı. Ancak [resmî MT5 Python belgesi](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py), alınan zamanları UTC olarak tanımlıyor. Bu fark, her dosyanın gerçekten nasıl üretildiğinin doğrulanmasını gerektiriyor; tüm veriye koşulsuz offset uygulamak daha önce düzeltilmiş UTC veriyi yeniden bozabilir.

**Düzeltme:** Ham zaman ve uygulanan dönüşüm saklansın; kaynak/dönem bazında doğrulanan dönüşüm yalnız bir kez uygulansın. Oynaklık tepesi yardımcı kontrol olsun, tek başına UTC kanıtı veya kesin durdurma kuralı olmasın. [Xetra ana seansının](https://www.xetra.com/xetra-en/trading/trading-calendar-and-trading-hours) 09:00 yerel saat referansının UTC karşılığı yaz/kış değişir; genişletilmiş saatler ayrıca sınıflandırılmalıdır. Broker D1/H4 sınırının NY 17:00 ile ilişkisi de gerçek broker takviminden doğrulansın.

`session_context_service.py` mevcut haliyle ağırlıkla ABD/NYSE bağlamı sunuyor; tasarımdaki tüm DAX/XAU/OIL seans kovaları hazırmış gibi kullanılmamalı. Sembolün takvimi, tatiller ve ABD/Avrupa DST geçişlerinin farklı haftaları kapsanmalı.

### 2.6. Araştırma ve ürün aynı geçmiş politikasını kullanmalı

Tasarım canlı aramada son beş yılı, araştırmada genişleyen kütüphaneyi tarif ediyor; araştırmaya ayrıca bir gün embargo ekliyor. Bunlar aynı davranış değildir. On yıllık alternatif de seçilecekse ayrı profil/deneme olarak sayılmalı.

**Düzeltme:** Her t için alt sınır, sonuç kapanış şartı ve varsa embargo aynı fonksiyondan gelsin. Taban, ölçekleyici, bağlam standart sapmaları, nadirlik dağılımı ve kalibrasyon da yalnız t'de bilinen veriden üretilsin. Canlı servis ile tarihsel tekrarın eşitlik testi bu tüm çıktıları kapsasın.

## 3. Tahmin katmanını geliştiren öneriler

### 3.1. Piramit'e fiyat yolunu koruyan küçük bir temsil ekle

Birleştirilmiş mumun OHLC'si, grup içinde önce tepeye mi dibe mi gidildiğini ve kaç kez yön değiştiğini kaybeder. Aynı süper-mum çok farklı yollardan oluşabilir. Ayrıca boşluklar dışarıda bırakılırsa ardışık mumların fiyat bağlantısı eksik kalır.

İlk deneyde temsil sayısını büyütmeden şu üç aday yeterli:

1. **Ham son 7 mum:** basit kıyas.
2. **Piramit:** mevcut aday.
3. **Piramit + küçük yol özeti:** 4–8 sabit noktada `(C_i−C_sorgu)/A_sorgu`, gruptaki tepe/dip sırası ve tek bir yönlülük ölçüsü `|C_son−C_ilk|/Σ|ΔC|`.

Hangi alanların kullanılacağı sonuç görülmeden dondurulsun. Özellik grupları geçmiş eğitim bölümündeki ölçekle dengelensin; her yeni özelliği ayrı taramak yerine tek ek temsil sınansın. Kazanç yoksa daha basit temsil seçilsin.

### 3.2. En yakın K eşleşmeyi zorla tahmin üretmekten kurtar

kNN her zaman en yakın örnekleri bulur; bunlar yine de kötü eşleşmeler olabilir. Mesafe büyüyünce bant genişliğini aynı komşuların medyanına göre büyütmek bu sorunu çözmez.

**Öneri:** Geliştirme döneminde dondurulan kabul mesafesi + örnek yeterlilik kuralı kullanılsın. Kabul sınırını aşan komşular tahmine girmesin. Yetersiz durumda sonuç “tarihsel dağılım”, “yeterli benzer örnek yok” veya yalnız taban olarak sunulsun; otomatik olarak yüksek K ile doldurulmasın. Sınırın katılığı ve tahmin üretme kapsamı birlikte ölçülsün.

İkiz/Hibrit yetersiz kalınca Piramit'e geçmek kullanıcıya açık bir mod değişimi olarak gösterilsin. “Son iki mum birebir” iddiası fallback sonucunda korunmasın. Kullanıcının yüzde toleransı da sessizce daraltılmasın; istenen ve uygulanan pay ayrı gösterilsin.

### 3.3. Yön, anlamlı hareket ve hedefe ulaşmayı ayrı cevapla

Kapanışın 1 pip yukarıda olmasıyla maliyet sonrası kullanılabilir hareket farklıdır. Ayrı çıktılar öneriyorum:

- Ham yön: `P(C_H > C_0)`; mevcut tanımla karşılaştırılabilir.
- Anlamlı hareket: yukarı / yatay / aşağı; nötr bant önceden tanımlanmış asgari hareket ve ölçülen maliyete dayanır. Bu ayrı hedef olarak kalibre edilir.
- Hedef: `P(+T'ye H içinde, −S'den önce dokunma)`; yukarı ve aşağı senaryolar ayrı.
- Zaman: hedefe ulaşan örneklerde süre dağılımı ve tüm örneklerde H'ye kadar ulaşma oranı; ulaşmayanlar gizlenmez.

En faydalı yeni ürün parçası **hedef–süre tablosudur**: satırda hedef mesafesi, sütunda zaman ufku; her hücrede hedefe ulaşma oranı ve ters hareket koşulu. Önce ATR biriminde hesaplanır, kullanıcının sembolünde pips ve fiyat seviyesi gösterilir. Rastgele oynaklık/seans tabanına göre farkı da bulunur.

Önemli yorum: MFE'nin P75 değeri, “%75 ihtimalle buraya gider” demek değildir. Sürekli dağılımda örneklerin yaklaşık %25'i bu değere ulaşır/aşar. Doğrudan ulaşma oranı bu karışıklığı önler.

`race` sonucu dört durum içersin: yukarı önce / aşağı önce / H içinde ikisine de dokunmadı / sırası belirsiz. “Dokunmadı” örnekleri paydadan çıkarılmasın. Aynı mumda iki bariyerin görülmesine yön analizinde otomatik 0,5 vermek gerçek sıra bilgisi üretmez; belirsiz oran ve olasılık alt/üst sınırları raporlansın.

### 3.4. n_eff bağımsız olay sayısı olarak adlandırılmasın

Kish formülü ağırlık yoğunlaşmasını ölçer, zaman bağımlılığını ortadan kaldırmaz. Komşu bitişlerinin `max(H, D/2)` kadar ayrılması D-mum özellik pencerelerinin çakışmasını da tamamen önlemez. Çakışmayan olaylar bile aynı piyasa dönemini paylaşabilir.

Ham K, ağırlık etkinliği, bağımsız olay/küme sayısı ve gün/hafta sayısı ayrı verilsin. Katı çakışmasız kohort için özellik+sonuç aralıklarının gerçekten ayrılması kullanılabilir; daha yoğun kohort ayrı raporlanıp uygun bloklarla belirsizlik hesaplanabilir. Blok uzunluğu H ve ölçülen bağımlılıkla ilişkili olmalı: 1d/20-bar sonuçta tek gün bootstrap yeterli değildir.

Günlük beş yıllık yaklaşık 1.300 barda, yalnız 20-bar sonuçları çakışmasız tutmak bile en fazla yaklaşık 65 olay bırakır; geçmiş uygunluğu ve uzun özellik pencereleri bunu daha da azaltır. **Günlük/4h profil için K=150 zorunlu tutulamaz.** Ufuk başına kapasite denetimi yapılsın; gerektiğinde daha az örnek ve daha geniş belirsizlik gösterilsin.

### 3.5. Tahmin konisi ile olasılık güven aralığı ayrı kalibre edilsin

P10–P90 her adım için %80 noktasal kapsama sağlasa bile tüm yolun koni içinde kalma olasılığı %80 olmaz. Grafik açıkça “her adımın tarihsel aralığı” desin; tüm yol için kapsama isteniyorsa ayrıca eşzamanlı bant sınansın. Adım medyanlarının oluşturduğu çizgi de gerçekleşmiş bir komşunun yolu olmak zorunda değildir.

Standart konformal yöntemlerin varsayımları bağımlı zaman serisinde kendiliğinden sağlanmaz. Bu konuda [Zaffran ve arkadaşlarının zaman serisi çalışması](https://proceedings.mlr.press/v162/zaffran22a.html) ve [Gibbs–Candès'in uyarlamalı yaklaşımı](https://papers.nips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html) uygun birincil referanslardır. Buradaki öneri: kronolojik, sonuçları tamamlanmış kalibrasyon; ufuk/seans bazında kapsama ve genişlik raporu. H gecikmeli hedeflerde güncelleme yalnız hedef çözüldükten sonra yapılmalı. Belirli bir gün için garanti iddiası kurulmasın.

## 4. Sembole özel seçim nasıl yapılmalı?

“NDX 33, XAU 17 mum” gibi sayıları şimdi sabitlemek için sonuç kanıtı yok. Doğru araştırma çıktısı **sembol × TF × ufuk × hedef** profilidir. Yön için iyi derinlik, büyüklük için iyi derinlikle aynı olmak zorunda değil. Kullanıcıya varsayılan tek ayar sunulabilir; altında hedefler ayrı izlenir.

| Sembol | Öncelikli bağlam | Özel araştırma kontrolü |
|---|---|---|
| NDX.INDX | ABD açılışına göre zaman, trend, oynaklık; VIX/stres ayrı varyant | Son 7 mum + yalnız bağlam tabanları; BUY/SELL ayrı; aynı NDX geçmişinin tekrar kullanılması |
| GDAXI.INDX | Xetra ve ABD açılışı ayrı, Avrupa/ABD DST farkı | NDX bağlamını aynen taşımama; yerel DAX seans tabanı; yetersiz kısa-TF geçmişi |
| XAUUSD | Asya/Londra/NY, trend ve aralık konumu | Momentum/devam ve dönüş ayrımı; spot broker/vadeli altın ayrımı; bilinen makro verinin yayın zamanı |
| USOIL.FOREX | Seans, aralık konumu, gerçek stok açıklaması zamanı, devir metadata | Tatil nedeniyle kaymış EIA günleri; spot CFD/vadeli petrol ayrımı; haber boşluğu/devir ayrımı |

Bunlar aday bağlamlardır; her birine doğrulanmış özellik statüsü verilmemeli. Özellikle mevcut kayıt defterinde IO-18'in sağlamlık sınamasından sonra zayıflaması bağlam gerekçesine yansıtılmalı. `vol_z` ve ATR+saat kıyasına ek olarak küçük bir geçmiş-oynaklık/trend tabanı kullanılmalı; getirilen ek bilginin yalnız kolay bir oynaklık tahmini olmadığı anlaşılmalı.

Petrolde “Çarşamba” sabiti yerine [EIA'nın gerçek yayın takvimi](https://www.eia.gov/petroleum/supply/weekly/schedule.php) kullanılmalı; resmî takvim tatil kaynaklı farklı gün ve saatleri listeliyor. Geçmiş araştırmada her yılın o tarihte bilinen takvimi gerekir.

## 5. Araştırma protokolüne eklenmesi gerekenler

1. **Keşif, seçim ve kalibrasyon ayrımı:** Geliştirme döneminde yürüyen iç katlar; seçim dondurulduktan sonra ayrı kronolojik kalibrasyon; ardından son sınama. Az verili TF'ler daha düşük iddia seviyesinde kalır.
2. **Eski veriye tekrar bakma kaydı:** Önceki PM/CORTEX/mum çalışmaları bazı dönemleri zaten değerlendirdi. Son 12 aya “hiç görülmemiş kasa” demek otomatik doğru değil. Mevcut dönem için iç OOS ve araştırma geçmişi açıklansın; kilitli yeni ileri gölge dönemi ayrıca toplansın.
3. **Tam seçim ailesi:** D/K yanında sembol, TF, H, hedef, kaynak, 5/10 yıl, bağlam ve ek temsillerin tümü sayılsın. Sabit topluluk her sembol/TF/hedefte çalıştırılıyorsa aile çapında tek test değildir.
4. **Dairesel kaydırma varsayımı:** Tüm sonuç serisini rastgele bar sayısı kaydırmak saat/seans, rejim ve ATR–sonuç ilişkisini korumaz. Null tasarımı neyi koruyacağını açıkça yazmalı; yerel dönem/seans eşli blok kontrolleriyle desteklenmeli. Geçerli blok yapısıyla seçim prosedürünün tamamını yeniden yürütmek esas olsun; Hansen SPA/Romano–Wolf adı tek başına bu sorunu çözmez.
5. **Sorgu p-değeri ayrı amaçta:** p>0,10 “örneklem yetersiz” demek değildir; tabana karşı fark gösterilemedi demektir. Az örnek, uzak eşleşme ve ek bilgi bulunamaması ayrı durumlar olsun. Sürekli sorgulanan çoklu TF'lerde ham p-değerleri yeni doğrulanmış profil rozeti üretmesin.
6. **Daha güçlü kıyas:** Son 7 mum, yalnız bağlam, ATR+saat, küçük oynaklık/trend tabanı ve seans/oynaklık eşli rastgele komşular. Şekil+bağlam yalnız bağlamı geçemiyorsa yararı şekle yazılmasın.
7. **Pratik katkı:** BSS/pinball pozitifliğine ek olarak örnek kapsamı, bant genişliği, kalibrasyon, yıl/seans dağılımı ve uç gün bağımlılığı raporlansın. En iyi tek hücre yerine yakın ayarlarda kararlı ve daha basit profil seçilsin. İleri gölge değerlendirmesi için sabit otomatik sorgu takvimi de olsun; yalnız kullanıcının ilginç bulup tıkladığı anlara dayanılmasın.

## 6. Ürün ve servis sözleşmesine eklemeler

- **Tahmin referansı:** Son kapanmış mumun kapanışı, güncel tick ve aralarındaki fark gösterilsin. Kapanış tabanlı dağılım düğmeye basılan fiyatın tahmini gibi sunulmasın; işlem çıktısı ayrı giriş sözleşmesi gerektirir.
- **Takvim:** H işlem barı ile duvar saati farklıdır. Seans sonu, hafta sonu ve tatil geçişi açık gösterilsin; olası bitiş takvimden hesaplansın. Mevcut seans-sonu sorgular geçmişte benzer geçiş örnekleriyle kıyaslansın.
- **Eşleşmeleri açıklama:** Son mum / eski bağlam / rejim mesafe katkısı ve yan yana grafik. Mesafeden türetilen “%81 benzerlik” olasılık veya objektif doğruluk değildir; tercihen mesafe yüzdeliği/kalite sınıfı kullanılsın.
- **Hedef–süre tablosu:** Ulaşma olasılığı, ters hareket, belirsiz/dokunmayan oranı ve bugünkü fiyat seviyesi.
- **Profil durumu:** Yön/büyüklük/ulaşma ayrı doğrulama; veri ve kalibrasyon bozulunca geçerli durum düşsün. Araştırmada doğrulama ile bugün sorguda yakın örnek bulunması ayrı gösterilsin.
- **Sürümler:** Sabit eğitim manifesti, kaynak/temsil/kalibrasyon sürümü ve değişen kütüphane revizyonu ayrı olsun. Dosya hash'i her yeni mumda değişir; normal artımlı ekleme tek başına tüm rozeti silmemeli. Eski satır düzeltmesi ve kaynak değişimi yeniden değerlendirme tetikleyebilir. Önbellek bu sürümleri de anahtara alsın.
- **Kayıt:** Sembol/TF/son kapanmış mum/profil/parametre kimliğiyle aynı tahmin tek kez kaydedilsin; her tıklama bağımsız gölge olay sayılmasın. Veri güncellemesi ve kayıt için POST; hazır sonucu okuma için GET tasarlanabilir.
- **Veri katmanını tekrar kullanma:** Mevcut DataHub yalnız Yahoo değildir; MT5 Redis ve `mt5_recorder` yolları da var. `data_hub.py` ve `mt5_recorder_feed.py` kaynak/freshness altyapısı incelenerek broker-only bir erişim sözleşmesi kurulmalı. Yeni paralel veri sahipliği ancak mevcut sözleşme gereksinimi karşılamıyorsa eklenmeli. `indicator_snapshots` için kaydedicide poll başına sınır var; OHLC kapsamı da doğrulanmalı, tablo adı tam veri garantisi değildir.
- **Performans:** <10 ms arama / <50 ms toplama ve tüm araştırmanın dakikalarda bitmesi hedef olarak kalsın. 350 bin ×21 float32 özellik tek başına yaklaşık 29 MB; aynı barlar için 48-adımlı float32 yol yaklaşık 67 MB daha ister. OHLC/metadata ve çok TF bunun üstündedir. Gerçek bellek, tekilleştirme, bootstrap ve plasebo dahil p50/p95 gecikme ölçülsün; gerekirse ağır tanılamalar ayrı aşamada gelsin.

## 7. Önerilen nihai akış

1. **Veriyi kabul et:** Sembolün kaynak/saat/mum sınırı/kapsam denetiminden geçmiş kütüphanesini kullan; son kapanmış sorguyu sabitle.
2. **Adayları sınırla:** Karar anında hem özellik hem sonuç biliniyor; kaynak ve segment uygun; aynı kütüphane politikası araştırma ve üründe geçerli.
3. **Temsili üret:** Sıkı İkiz veya araştırmanın seçtiği küçük temsil; son mumlar, uzun bağlam ve varsa rejim ayrı katkılarla.
4. **Benzerleri kabul et:** Mesafe sınırı, olay tekilleştirmesi ve ufuk başına kapasite; iyi eşleşme yoksa açıkça çekimser çıktı.
5. **Senaryoları hesapla:** Ham yön, anlamlı hareket, net hareket dağılımı, MFE/MAE, hedefe ilk ulaşma ve süre; ölçeği mevcut ATR ile pips/fiyata taşı.
6. **Belirsizliği ölç:** Ağırlık etkinliği ve olay kümeleri ayrı; uygun uzunlukta bloklar; geçmiş kalibrasyon ve tabana göre ek beceri.
7. **Ekranda açıklama:** Varsayılan sonuç + farklı TF'ler + hedef–süre tablosu + geçmiş örnekler; referans fiyat, veri yaşı ve doğrulama seviyesi görünür.
8. **İleri karneyi topla:** Aynı tahmini tekilleştir; tamamlanan sonuçla notla; kilitli ileri dönemde katkıyı izle. Bot bağlantısı ayrı go-live sürecine tabidir.

## 8. Açık teknik sorulara görüş

| Soru | Öneri |
|---|---|
| Piramit / Haar / PAA-SAX? | Önce ham7, Piramit ve tek küçük yol-özeti varyantı; daha çok temsil ilk araştırmayı gereksiz büyütür. |
| K ve bant genişliği? | İç kronolojik geliştirmede seç; mutlak benzerlik kabul sınırı ve bağımsız kapasite olmadan K optimizasyonu yeterli değil. |
| Kantil kNN / kantil regresyonu? | kNN açıklanabilir başlangıç; küçük regresyon güçlü kıyas olabilir. Kalibrasyon ikisinin de üstünde ayrı katman olsun. |
| Seçim düzeltmesi? | Önce geçerli null/blok yapısı ve tüm seçim ailesi; ardından uygun maks-istatistik veya başka çoklu-test yöntemi. |
| Mahalanobis? | Eğitim bölümünde grup ölçekleme/robust standartlaştırma önce; kovaryans terslemesi az veride ek oynaklık yaratabilir. |
| Siamese/contrastive / DTW? | Basit motor gelecekte katkı göstermeden ilk sürüme ekleme. DTW zaman yapısını değiştirdiği için ayrı hipotez olsun. |
| Eski komşulara yaş ağırlığı? | Sonuçlara bakmadan en fazla tek alternatif politikayı tanımla; son5y ile zaman ağırlıklı aynı pencereyi kıyasla. Daha az etkin örnek ve rejim körlüğü birlikte raporlansın. |

## 9. Diğer agente iletilebilecek revizyon isteği

> v0.1'i v0.2'ye yükseltirken mevcut çekirdek fikri koru. Önce fizibilite betiklerinin sorgudan sonraki adayları ve farklı ATR normalizasyonunu düzelt; temiz kaynak/segment ve sonuç uygunluğu maskelerini ortaklaştır. X≤3'ü evrensel fiziksel sınır, RC üstünlüğünü tahmin kanıtı olarak sunma. Ham7/Piramit/tek küçük yol-özeti kıyasını ön-kayıtla. kNN'ye mutlak mesafe kabul sınırı ve çekimserlik ekle; günlük/4h'te K'yi ufuk başına bağımsız kapasiteyle sınırla. Ham yön, anlamlı hareket ve +T'ye −S'den önce H içinde ulaşmayı ayrı hedef yap; no-touch/belirsiz sınıflarını koru. Kish n_eff ile bağımsız olay sayısını ayır; uzun ufukta uygun uzun bloklarla belirsizlik ve noktasal/eşzamanlı bant ayrımı kullan. Son5y/embargo/kalibrasyon politikası canlı ve araştırmada aynı olsun. Önceki araştırmalarda kullanılan dönemi yeni bağımsız kasa diye adlandırma; ileri gölge dönemini kilitle. Null testinde seans/rejim yapısının korunmasını ve bütün seçim ailesini açıkla. DataHub'ın broker yollarını değerlendirmeden paralel veri katmanı kurma. Sürüm/hash/cache ve referans fiyat sözleşmesini tamamla. Sonuç iddiası üretmeden v0.2 tasarımı ve PROTOCOL.md taslağını hazırla.
