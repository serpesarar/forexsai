# Ön kayıt — NASDAQ 3,5 saatlik alt fitil ≥ %0,50 → dört işlem kuralı (2026-11-17)

Bu dosya sonuçlara bakılmadan yazıldı. Sonradan eklenen her şey "EK" başlığıyla ayrıca işaretlenir.

## 0. Kaynak ve gerekçe

Kullanıcı fikri ve 4 ekran görüntüsü (MT5 NAS100 H4/M30/M15, 17 Kas 2026). Doğrulama: kutunun MT5 verisinde NY 10:30–14:00 210m
mumunun alt fitili %1,14; kullanıcının 15m çizgileri (27058,3 / 26778,2, %50 = 26920,9) NY 10:30 15m mumunun gövdesi
(27060,9 → 26778,9; broker farkı ~2 puan).

Defter §2.27 (FR-01…18) fitili **mum aralığının oranı** olarak 1h/4h'de sınadı. Burada tanım yeni (fitil = **fiyatın yüzdesi**,
**210 dk**), giriş ailesi yeni (15m ana gövde seviyeleri). Yeniden açma gerekçesi: yeni tanım + yeni giriş.

## 1. Veri

- **Ana:** Dukascopy USATECHIDXUSD BID 1m, `research/nom_20261113/data/ndx_1m_v3_duka.parquet`, 2018-01-02 → 2026-11-15,
  spread modeli `spr` (ask = bid + spr).
- 15m ve 210m mumlar aynı 1m'den, işlem günü NY 17:00 çapasıyla kurulur. 210m başlangıçları 17:00, 20:30, 00:00, 03:30, 07:00,
  10:30, 14:00 ET (son mum 14:00–17:00, 180 dk). 15m = UTC 900 sn tabanı (NY ofsetleri tam saat). 210m = 14 adet 15m.
  Kontrol: bizim 210m = `research/ndx_tf_yapilandirma_20261117/out/DUKA/NDX_DUKA_210m.parquet` (ortak mumlarda OHLC farkı 0).
  O dosyada `fitil_durumu = eksik_dakika_supheli` olan mumlar olay sayılmaz.
- **Bağımsız besleme:** kutu MT5 NAS100 M15 (`out/kutu_taze/NAS100_M15.csv.gz`, 2022-08 → 2026-11-17, sunucu = NY+7 → UTC).
  15m çözünürlükte yürütülür (aynı mumda TP+SL → SL), spread = bar spread'i × 0,1.

## 2. Tanımlar

- **Olay E:** 210m mumda `(min(O,C) − L) / min(O,C) ≥ 0,50 %`. Karar anı = mumun son 1m barının kapanışı.
- **Giriş:** karar anından sonra açılan ilk 1m barın açılışı (uzun = ask, kısa = bid). Hafta sonu/günlük ara varsa ilk açılış.
- **Yol:** TP/SL 1m BID (uzun) / ask (kısa) yüksek-düşükleriyle; aynı barda ikisi → SL; boşlukla geçilirse açılış fiyatı.
  Hesap tavanı 7 takvim günü (zaman çıkışı, sayısı raporlanır). Uzun pozisyonda gecelik finansman FR-18 (−%6,41/yıl).
- **S1 (AL):** E'den sonra giriş, TP = giriş × 1,003, stop yok, giriş + 30 dk'da açılan 1m barda çık.
- **Ana mum:** E mumunun **son 6** adet 15m mumu içinde gövdesi (O − C) en büyük kırmızı mum. Kırmızı yoksa kurulum yok.
  BT = açılış, BB = kapanış, B = BT − BB; L25/L48/L50 = BB + 0,25/0,48/0,50·B; tol = fiyatın %0,03'ü.
- **Kurulum ömrü:** E kapanışından sonraki ilk 15m mumdan başlar. Bir 15m mum `C > BT·(1+tol)` veya `C < BB·(1−tol)` kapanırsa
  (bölge dışı) ya da bir sonraki E olayı kapanırsa biter. Süre sınırı yok. Açık işlemler TP/SL'ye kadar sürer.
- **Bölge içi kapanış:** `BB·(1−tol) ≤ C ≤ BT·(1+tol)`. Tetikler yalnız bölge içi kapanışta.
- **S2 (AL):** her bölge içi kapanış → AL, TP = giriş × 1,0018, SL = BB. Giriş bid ≤ BB ise atla.
- **S3 (SAT):** bölge içi kapanış ve C > L48 → SAT, TP = L25, SL = BT. Giriş ask ≥ BT veya giriş bid ≤ TP ise atla.
- **S4 (SAT):** bölge içi kapanış, H > L50, C < L50, H > max(O,C) (üst fitil) → SAT, TP = BB, SL = BT. Aynı atlama kuralı.
- **Tek pozisyon:** her strateji kendi defterinde; açık işlemi varken yeni sinyal atlanır.
- **Ölçü:** S2–S4 R = net getiri / (|giriş − SL| / giriş). S1 net bp (stopu yok). Çıplak isabet tek başına raporlanmaz.

## 3. Önceden sayılmış varyantlar (dayanıklılık; sonuçtan sonra seçim yok)

| Kod | Değişen |
|---|---|
| W14 / W3 / F3 | ana mum penceresi: E'nin 14 (tüm) mumu / son 3 mumu / E'den sonraki ilk 3 mum (kurulum bu 3 mumdan sonra başlar) |
| T40 / T75 / T100 | eşik %0,40 / %0,75 / %1,00 |
| S3d | S3 TP = giriş − 0,25·B |
| S4w | S4 TP = ana mumun fitil dibi (L) |
| S4g | S4 gövde koşulu max(O,C) < L50 |
| S2f | S2 yalnız kurulumun ilk mumu |
| S1h15 / S1h60 / S1tp20 / S1tp50 | S1 tutuş 15/60 dk, TP %0,20/%0,50 |
| NOTOL | tol = 0 |

## 4. Kontroller

- **Eşli plasebo:** her E için aynı yıl × aynı 210m dilimi × aynı aralık beşlisinde (yıl içi (H−L)/C) alt fitili < %0,15 olan bir mum
  (yoksa yıl × dilim) seçilir; 10 bağımsız kopya, her kopya E ile aynı yoğunlukta aynı motorla koşar. Fark = fitilin bilgisi.
- **S1 koşulsuz taban:** her 210m kapanışında S1 (aynı dilim kırılımı).
- **Dönem:** KEŞİF 2018-01-02 → 2021-10-31, TEST 2021-11-01 → 2026-11-15; kronolojik yarılar; yıllar.
- **Bağımsız besleme:** MT5 M15 (yukarıda).
- **İstatistik:** ortalama, medyan, ay-blok bootstrap P(EV>0), **kurulum-küme** bootstrap P (bağımsız karar = kurulum),
  en iyi 5 hariç, spread × 1,5, iyimser icra (sinyal kapanışı, spread yok).

## 5. Hüküm ölçütü (önceden)

Bir strateji ancak şu hepsiyle "aday" olur: KEŞİF ve TEST ortR > 0; TEST P(EV>0) ≥ %90 (küme bootstrap); plasebodan iyi
(fark > 0, P ≥ %90); MT5 bağımsız beslemede ortR > 0; spread ×1,5 > 0. Aday olursa 2. KURAL kartı (6 ölçüt) yazılır.
Diğer durumlar: tek dönemde artı → C, hiçbir yerde → X. Varyantlar yalnız komşuluk okunur.

## EK-1 (2026-11-17, kullanıcı düzeltmesi — ana koşu sonuçları görüldükten sonra, tanım düzeltmesi olarak)

Kullanıcı grafik örneklerine baktı: 1–2. örneklerde "büyük fitil yukarıda" duruyordu; istenen yalnız **uzun fitili altta** olan mum.
4–5. örneklerde fitil kısa göründü. Kontrol: örnek 2 (alt %0,63 / üst %0,66) ve 6 (alt %0,51 / üst %0,55) gerçekten iki uçlu mumdu.
Örnek 4 (alt %0,526, 130,9 puan) ve 5 (alt %0,535) eşiği geçiyordu; 15m grafikte 210m fitili görünmüyordu. Ayrıca örnek 5 14:00 dilimindeydi;
Dukascopy'de 16:15–17:00 ET verisi olmadığı için 210m mumu eksik kuruluyordu.

Yeni tanımlar (bu ekten sonra yeniden koşulur; eski sonuçlar RAPOR'da "v1" olarak ayrı kalır):

- **Olay E (v2):** 210m mumda `alt fitil ≥ %0,50` **ve** `üst fitil ≤ alt fitil / 2` (üst fitil = (H − max(O,C)) / max(O,C)).
- **İki besleme teyidi (ana):** aynı 210m penceresinin kullanıcının broker mumunda (MT5 NAS100, `out/MT5/NDX_MT5_210m.parquet`, 2018-05 →)
  da aynı kural sağlanmalı. MT5 mumu yoksa olay ana kümeye girmez. Bu, kullanıcının grafiğinde gördüğü mumla birebir uyumu sağlar ve
  Dukascopy'nin 16:15–17:00 boşluğunu kapatır (o dilimde gerçek kapanış MT5'ten okunur).
- **15m pencere eksiksizliği:** ana mum penceresi (son 6 mum) 210m mumun nominal bitişine kadar kesintisiz 6 adet 15m mum içermeli.
  Eksikse (Dukascopy 14:00 dilimi) o olayda S2–S4 açılmaz; S1 yine koşar. W14: son mum nominal bitişte ve aralıksız.
- **Varyantlar (ek):** U1 `üst < alt`, U3 `üst ≤ alt / 3`, G1 `alt fitil ≥ gövde`, DT Dukascopy tek (teyitsiz), MD MT5 tanımlı (olay MT5 mumuyla,
  yol Dukascopy). Diğer önceden sayılmış varyantlar aynen.
- **Doğrulama çıktıları:** tüm olayların listesi (`results/olaylar_ANA.csv`: iki beslemenin O/H/L/C, alt/üst fitil %, gövde %), 210m bağlam
  panelli grafikler, 24 rastgele olayın 210m galerisi.

## EK-2 (2026-11-17, kullanıcı düzeltmesinin ikinci adımı — sonuçlar görülmüşken, tanım düzeltmesi)

EK-1'den sonra iki gözlem kaldı:
- **Örnek 1** (2022-05-23 07:00): 3,5 sa mumunda alt %0,94 / üst %0,09. Ama kullanıcının MT5 H4 grafiğinde dibi içeren mum
  (09:00–13:00 NY) alt %0,94 / **üst %0,57**. Kullanıcı 3,5 sa göremediği için H4'e bakıyor; orada büyük üst fitil görüyor.
- **Örnek 5** (2022-07-12 14:00): alt fitil %0,54, gövde %1,08. Fitil mumun küçük parçası olduğu için "yeterince uzun görünmüyor".

Yeni ana tanım (v3):
1. **3,5 saatlik mum, hem Dukascopy hem MT5'te:** alt fitil ≥ %0,50, üst fitil ≤ alt fitil / 2, **alt fitil ≥ gövde**
   (alt fitil mumun en uzun parçası).
2. **Fitil dibini içeren MT5 H4 mumu** (kullanıcının grafiğinde gördüğü): alt fitil ≥ %0,50 ve üst fitil ≤ alt / 2.
   - H4'te gövde koşulu ilk denemede vardı (varyant H4G). Kaldırıldı, çünkü kullanıcının kendi 17 Kas örneğini eliyordu
     (H4 09:00–13:00: alt %1,15, gövde %1,6). Bu bir tanım hatasıydı; sonuçlara bakılarak değiştirilmedi.
3. Diğer her şey (S1–S4, pencere eksiksizliği, plasebo, MT5 bağımsız) aynen.

Durum: kullanıcının işaretlediği 4 örneğin 4'ü bu tanımda elenir (nedenleri `results/grafikler.html`). 17 Kas mumu geçer.

Yeni varyantlar:
- **G0:** gövde koşulu yok.
- **H0:** H4 teyidi yok.
- **H4G:** H4'te de gövde koşulu var.
- **v2:** EK-1 tanımı.

Bu, aynı veriyle denenen **üçüncü tanım** (v1 → v2 → v3). Hüküm buna göre ihtiyatlı verilir: tek tanımda görülen artı en çok C'dir.

## EK-3 (2026-11-17) — ana kural EK-1'e geri alındı

EK-2'nin iki koşulu ana kurala sonuçlar görülmüşken eklenmişti:
- alt fitil ≥ gövde,
- MT5 H4 görünüm teyidi.

İkisi de kullanıcının verdiği kuralda yok. Kullanıcının kuralı: 3,5 saatlik mumda alt fitil ≥ %0,50 ve uzun fitil yalnız altta.
Bu yüzden ana kural yeniden **EK-1** oldu:
- alt fitil ≥ %0,50,
- üst fitil ≤ alt / 2,
- Dukascopy ve MT5 3,5 saatlik mumunun ikisinde de.

MT5 teyidi veri doğruluğu için kalıyor: Dukascopy'nin 16:15–17:00 boşluğunu kapatıyor ve kullanıcının broker mumuyla uyumu sağlıyor.

EK-2 koşulları yalnız yan varyant olarak raporlanır ve hükme girmez:
- G1: alt fitil ≥ gövde.
- H4: MT5 H4 teyidi.
- V3: G1 + H4.
- H4G: V3 + H4'te gövde koşulu.

Hüküm §5 ölçütüyle ana kural üzerinden verilir. Varyantlardaki artılar "önceden kayıtsız hipotez" olarak backlog'a gider.

## EK-4 (2026-11-17) — ana kural kullanıcının etiketlerine göre (son tanım)

Kullanıcının hedef talimatı eşik sayısı değil, mumun grafikte nasıl göründüğü:
- "büyük fitil yukarıda olanları sayma, yalnız uzun fitil aşağıda olsun" (örnek 1, 2),
- "fitili yeterince uzun görünmüyor, kuralımın dışında" (örnek 4, 5).

Kullanıcı 3,5 saatlik mumu MT5'te göremez; H4'e bakar. Bu yüzden ana kural, kullanıcının **5 etiketli örneğini** doğru sınıflandıran
tanımdır (EK-2'deki V3):
- 4 örnek dışarıda: 1, 2, 4, 5.
- 17 Kas örneği içeride.

**Ana kural:**
1. 3,5 saatlik mum, Dukascopy ve MT5'te: alt fitil ≥ %0,50, üst fitil ≤ alt / 2, alt fitil ≥ gövde.
2. Fitil dibini içeren MT5 H4 mumu: alt fitil ≥ %0,50, üst fitil ≤ alt / 2.

Etiket uyumu:

| Örnek | Elenme nedeni |
|---|---|
| 1 | H4 üst %0,57 > alt / 2 |
| 2 | 3,5 sa üst %0,66 > alt / 2 |
| 4 | MT5 alt %0,49 |
| 5 | gövde %1,08 > alt fitil %0,54 |
| 17 Kas | geçer |

E1 (EK-1, yalnız eşik + üst fitil) 1 ve 5'i tutuyordu; kullanıcı etiketleriyle çelişir. Varyant olarak raporlanır.

**Dürüstlük notu:** bu tanım, aynı veride v1 (1.136) ve E1 (820) sonuçları görüldükten sonra kesinleşti. Tanımın kaynağı kullanıcının
etiketleri ve kendi 17 Kas örneğidir; P&L'ye göre ayarlanmadı (H4'te gövde koşulu, 17 Kas örneğini elediği için konmadı). Yine de
aynı veride dördüncü tanım olduğu için hüküm §5 ölçütüyle ve ihtiyatla verilir. Artı hücreler önceden kayıtsız hipotezdir.

**Kullanıcı onayı (2026-11-17):** Seçenekler kullanıcıya soruldu:
- yalnız 3,5 sa eşiği (820 olay; 1 ve 5 kurala uyar),
- eşik + gövde (625 olay; 1 kalır),
- görünüşe göre (232 olay; 1, 2, 4, 5 elenir).

Kullanıcı açıkça **"görünüşe göre"** tanımını seçti. EK-4 ana kuralı kullanıcı kararıdır.

## EK-5 (2026-11-17) — "canlı mum" varyantı (kullanıcı sorusu: 11:00–13:45 neden işlem yok?)

Ana kuralda kurulum 3,5 saatlik mum **kapanınca** başlıyordu, çünkü tespit (fitil boyu, üst fitil, gövde) mum kapanınca kesinleşir.
Kullanıcı ana mumdan hemen sonraki mumlarda işlem bekledi. Bunu gerçek zamanlı yapmanın sızıntısız yolu şu varyant:
- 3,5 sa mumu oluşurken her 15m kapanışında, o ana kadarki mum (açılış, şimdiye kadarki tepe/dip, son kapanış) aynı şekil kuralını
  (alt ≥ %0,50, üst ≤ alt/2, alt ≥ gövde) sağlarsa kurulum o anda kurulur.
- Ana mum, o ana kadar kapanmış 15m mumlar içinde gövdesi en büyük kırmızı mumdur.
- Tespit mumu ana mumdan sonraysa ilk tarama mumu tespit mumunun kendisidir.

Canlıda yapılamayanlar:
- H4 ve broker teyidi (o mumlar da oluşuyor).
- S1 (mum kapanışında AL; değişmedi).

Bu varyant bugünkü örnek görüldükten sonra tanımlandı: önceden kayıtsız, hükme girmez. Ölçülerek raporlandı.
