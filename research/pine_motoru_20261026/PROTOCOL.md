# Pine Motoru — TradingView topluluk scriptlerinin birebir çalıştırılması (ön kayıt)

**Kayıt:** 2026-10-26, hiçbir script sinyali yön için değerlendirilmeden önce. GÇM ön kaydının
(`../gosterge_cakisma_20261025/PROTOCOL.md`) EK-7'sidir; aşağıda yazılmayan her şey oradaki gibidir (etiket, taban,
maliyet, örtüşme bastırma, %60/20/20, ölçütler). Sonradan değişiklik "EK-P n" diye eklenir.

## 1. Kullanıcı kararı ve kapsam

Kullanıcı (2026-10-26) "tam Pine yolu"nu seçti: kaynağı açık tüm topluluk scriptleri indirilip çalıştırılabilenlerin
hepsi uygulanacak.

- **Kaynak:** `topluluk_taramasi` listesindeki 33.384 benzersiz script → `pine-facade` uç noktasından Pine kaynağı
  (`download_sources.py`). Kaynağı gelmeyen (korumalı/davetli) scriptler sayılır ve raporlanır.
- **Çalıştırma:**
  - Kendi yazdığımız Pine v1–v6 ayrıştırıcı + Python çevirmen + çalışma zamanı (`pine_parser.py`, `pine_transpile.py`, `pine_runtime.py`, `pine_ta.py`, `pine_builtins.py`, `pine_run.py`).
  - Üst-TF / alt-TF / Heikin Ashi `request.security` iki geçişli; üst-TF'de `lookahead_off` semantiği; kütüphane importları desteklenir.
- **Başarısızlık sınıfları raporlanır:** `parse_error`, `transpile_error`, `unsupported` (başka sembol verisi, olmayan alt-TF verisi, renko vb.), `runtime_error`, `timeout`. "Uygulanan" = en az bir sembolde `ok` ve ≥ 1 tepki durumu üreten script.
- **Kütüphaneler** (type=library) gösterge değildir; yalnız import çözümünde kullanılır.

## 2. Veri pencereleri

| Pencere | Kapsam | Kullanım |
|---|---|---|
| **recent** | Her sembolün 1h verisinin son 12.000 barı (~2 yıl) | Tarama |
| **past** | Ondan önceki 12.000 bar | Bağımsız geçmiş dönem — yalnız tekrarlanma kontrolü |

Diğer TF'lerde tekrar (15m/4h) yalnız aday çıkarsa yapılır.

## 3. Çıktı → tepki

Kurallar `signals.py`'de sabittir:
- Olay kanalları: `on`, long/short, up/down.
- Fiyat-ölçekli plot: fiyat üstü/altı ve eğim.
- Osilatör plot: sıfır üstü/altı, eğim, nedensel %90/%10 uçları.
- Renkli kanallar: yeşil/kırmızı.
- Elemeler: görülme oranı < %0,2 veya > %99,8; tekrarlanan dizi; script başına en çok 40 durum.

Tetik = durumun başladığı bar (GÇM §3).

## 4. Aşamalar

**A1 — her script kendi başına (L1).**
- Tüm scriptlerin tüm durum tetikleri tek bir arama sayılır.
- Seçim eşiği: etiket dizisinin keşif içinde 20 dairesel kaydırmasında **tüm durumların** max|z|'sinin %95 dilimi.
- Seçim: keşif |z| sırasıyla en çok 100 tetik (olay kümesi %80+ örtüşen atlanır).
- Doğrulama ve kasa: GÇM §7.5–7.7 ile birebir.

**A2 — çakışma.**
- A1'in keşif |z| sırasıyla ilk 300 tetiği şunlarla birleştirilir: GÇM ana kütüphanesinin 353 durumu (L2a), aynı 300 tetiğin "son 3 bar içinde" hâlleri (L2b).
- Aynı scriptten gelen çiftler atlanır.
- Aynı plasebo eşiği mantığı (L1 + L2 birlikte yeniden kurulur), aynı ölçütler.

**Ufuklar:** h ∈ {1, 2, 4, 8, 16, 32} (1h barı).

**Semboller:** NDX, DAX, XAU, USOIL ayrı ayrı (her biri kendi eşiğiyle).

## 5. Tekrarlanma ve hüküm

- **Tekrarlanan aday:** kanıtlı ve aynı tanım (script + durum [+ GÇM durumu]) **past** penceresinde yön aynı ve z ≥ 1,645.
  Ya da başka bir sembolde kanıtlı.
- **Sistem hükmü** (GÇM §7.9 ile aynı):
  - Kanıtlı sayısı boş beklentiyle karşılaştırılır.
  - Doğrulama ve kasada ters yönde anlamlı sayılarla simetri kontrolü yapılır.
  - past penceresindeki tekrar oranı %5 boş orana karşı okunur.
- `lookahead_on` bayrağı taşıyan scriptler ayrıca listelenir. Bunlar gelecekteki üst-TF değerini görebilir; kanıtlı çıkarlarsa kanıt sayılmaz.

## 6. Yapılmayacaklar

- Sonuçlara bakıp çıktı→tepki kurallarını, pencereleri veya ölçütleri değiştirmek.
- Çalışmayan scriptleri "kenarsız" saymak: onlar ayrıca "uygulanamadı" diye raporlanır.
- Canlıya bağlamak.

## EK-P1 (2026-10-26, değerlendirme başlamadan önce — hiçbir yön sonucu görülmedi)

1. **Zaman dilimi tekrarı genişletildi.** §2'deki "15m/4h, yalnız aday çıkarsa" yerine:
   - Kapsam: doğrulamayı geçen (`val_ok`) tüm adaylar.
   - Kendi sembollerinde **1m, 5m, 15m, 4h, 1d** verisinin son 12.000 barında yeniden çalıştırılır. 1d'de mevcut tarihin tamamı kullanılır (2.000–4.800 bar).
   - Aynı tanım tüm pencerede tek blok ölçülür; aynı ufuklar (bar sayısı), aynı maliyet.
   - Gerekçe: kullanıcı hedefi "sahip olduğumuz tüm zaman dilimi verilerinde tekrar".
   - Tekrar ölçütü: aynı yön, z ≥ 1,645 ve n ≥ N_MIN[tf]/4. Okuma %5 boş orana karşı yapılır.
2. **A2 L2b eş kodlaması** `R:<sid>|<durum>` oldu (eş scriptin kimliği). Bu bir kodlama hatası düzeltmesidir, ölçüt değişikliği değildir. Önceki kodlamada eş scriptin kimliği yoktu, tekrar ölçümü eşi bulamazdı.
3. **Motor hızlandırması:** `isna`/`T`/`DIV`/`math.max`/`math.min` sıcak yolları; bool ifadelerde `T()` atlanması.
   - Eşitlik testi: eski koşuyla 254 scriptte bayt bayt aynı tepki durumları.
   - Semantik değişiklik yok.
4. **Uygulanamayan scriptler için düzeltme turu.**
   - Tam koşu bittikten sonra en sık başarısızlık sınıflarına motor desteği eklenebilir; yalnız başarısız scriptler yeniden koşturulur.
   - Kural: yeni destek mevcut yolları değiştirmez. Önceki koşuda `ok` olan scriptlerden rastgele 500'lük örneklemde bayt bayt eşitlik testi zorunludur; tek fark bile turu geçersiz kılar.
   - Düzeltme turu, değerlendirmeden ÖNCE biter. A1/A2 son durum dosyalarıyla **bir kez** koşar.

## EK-P2 (2026-10-26 11:41, motor v2 — hiçbir yön sonucu görülmedi)

Tam koşunun ilk 3.460 scripti (part_0000–0017) v0/v1 motoruyla üretildi. Başarısızlık sınıflarının ve derleme taramasının
(`compile_scan.py`) incelenmesi iki tür kusur gösterdi. Koşu durduruldu, motor v2'ye geçildi (özet `8ecaa1997b9c`; her
kayıt `engine` alanı taşır, `data/runs/recent/engine_log.txt`).

**Sadakat düzeltmeleri** (eski motor TradingView'den farklı davranıyordu):

- **Broker emülatörü** (`pine_broker.py`): `strategy.exit` boş geçiliyordu. 3.118 strateji scriptinin 1.495'i bunu kullanıyor; "pozisyon yoksa gir" koşullu ~1.000'i ilk girişten sonra hiç işlem açmıyordu. Örneklem farkları: 1→69, 1→80, 0→275 giriş.
  - Piyasa emri bir sonraki açılışta dolar.
  - Limit/stop emirleri ve çıkış braketleri OHLC yolu varsayımıyla işlenir.
  - Piramitleme uygulanır; `opentrades.*`/`closedtrades.*` desteklenir.
- `request.security_lower_tf` demet ifadesi dizi demeti döner. Eskiden demet dizisi dönüyordu.
- Yerleşik ad alanı, aynı adlı kullanıcı değişkenine baskındır (`str.tostring`, `str` değişkeni varken).
- Jenerik çağrı ileri bakışı anahtar kelimeleri reddeder. `low < a or high > (b)` artık `low<…>(…)` sanılmıyor.
- Çizim getter/setter'ları na kimlikte na döner veya yok sayılır.
- Fonksiyon aşırı yüklemesi parametre sayısıyla seçilir. Eskiden son tanım hepsini eziyordu.

**Kapsam eklemeleri:**

- Dil ve çağrı biçimi:
  - Metodun fonksiyon biçiminde çağrılması.
  - Varsayılanlıdan sonra gelen parametre.
  - Operatörle biten satırın devamı.
  - v3/v4 adları: `isintraday`, gün sabitleri, `ticker`, `tickerid()`, `heikenashi()`, `round_to_mintick`.
  - `security(resolution=…)`.
  - `"240.0"` TF yazımı.
- Veri:
  - `request.earnings/financial/dividends/splits` → na. Sembollerimiz hisse değil; TradingView de na döner.
  - `request.currency_rate` aynı para biriminde 1.
  - Alt TF'ler 1m'den türetilir (2/3/10/30 dk…).
  - Arama yoluyla 218 eksik kütüphane eklendi (`fetch_libs.py`); yayıncı adı değişmişse ad eşleşmesi kullanılır.
- Yerleşikler:
  - `line.all`/`box.all`/`label.all` (üst sınır 500).
  - Matris işlemleri: mult/inv/pinv/det/rank/trace/sort/submatrix/sum/diff…
  - Kullanıcı metotları renk/string/sayı tiplerinde.

Derleme: 31.317 → 32.243 script (+926).

**Eşitlik testi** (`equiv_check.py`, 150 rastgele; kodu aynı, strateji dışı, 4 sembolde ok):

- İlk denemede **15 fark**: dizi `shift/pop/first/last/remove` gerilemesi. Toplu bir metin değişikliği çizim getter'ı yerine dizi fonksiyonlarına da uygulanmıştı.
- Gerileme düzeltildi. Yeni örneklemde 2 fark kaldı, ikisi de yük altında zaman aşımı; tek başına koşulduklarında 8/8 sembol bayt bayt aynı.

**Düzeltme turu kuralı:**

- v2'den önceki motorla üretilmiş TÜM kayıtlar (`engine` alanı yok) tam koşu bitince v2 ile yeniden koşar: `batch.py retry recent 7 stale`.
- v2'den sonra motor yine değişirse yeniden koşacak scriptler:
  - başarısızlar,
  - iki derleme taramasında kod özeti değişenler,
  - değişikliğin dokunduğu çalışma zamanı sınıfları (regex ile yazılır).

  Eşitlik testi her seferinde yinelenir.

**Zaman aşımı notu:** 60 sn sınırı yüke bağlıdır; batch'le eşzamanlı ağır işler sınırdaki scriptleri aşıma itebilir. Son raporda zaman aşımı sayısı ayrıca verilir.

## EK-P3 (2026-10-26, değerlendirme başlamadan önce — hiçbir yön sonucu görülmedi)

**Tüm tarih tekrarı.** Tarama, maliyet nedeniyle her sembolün son 12.000 1h barında yapılır (§2). Kullanıcı hedefi ise
"sahip olduğumuz veri tarihinin tamamı". Bu yüzden doğrulamayı geçen adaylar ek olarak **old** penceresinde de
çalıştırılır ve ölçülür: son pencereden önceki 1h tarihinin tamamı (NDX ~47.800, DAX ~26.500, XAU/USOIL ~48.600 bar).
`past` (önceki 12.000 bar) bunun alt kümesidir; ikisi de raporlanır.

- Tekrar ölçütü aynıdır: aynı yön, z ≥ 1,645 ve n ≥ N_MIN/4.
- Tüm tarihin tamamında A1/A2 araması yapılmaz. 33 bin script × ~4 kat bar ≈ 40 saat; bu sınır raporda açıkça yazılır.

## EK-P4 (2026-10-26 ~13:00, motor v3 — hiçbir yön sonucu görülmedi)

**Neden:** v2'nin ilk 1.600 scriptinde, NDX'te çalışanların %21'i (281) hiç tepki üretmedi. Bunların 194'ü sinyalini
yalnız çizimle veriyor: `label.new` ("BUY/SELL", "BOS", "CHoCH" etiketleri) ya da `box.new` (order block / FVG
bölgeleri). §3'ün çıktı kanalları çizimleri okumuyordu. Bu sinyal biçimi atlanırsa topluluk scriptlerinin ~%13'ü
"çalışıyor ama tepkisiz" kalır.

**§3'e eklenen kanal — çizim oluşturma olayları** (`label.new`, `box.new`, `line.new`):

- **Olay barı:** nesnenin oluşturulduğu bar. Nesne geçmiş bir bara yerleştirilse de bu nedenseldir; script o anda bildi.
- **`on`:** o barda o çağrı yeri en az bir nesne oluşturdu.
- **Etiket yönü (`up`/`dn`):**
  - Önce stile bakılır: `label_up`, `arrowup`, `triangleup`, `label_lower_*` → yukarı; `label_down`, `arrowdown`, `triangledown`, `label_upper_*` → aşağı.
  - Stil yoksa metin kullanılır: buy/long/bull/bullish → yukarı; sell/short/bear/bearish → aşağı. İkisi birden varsa nötr.
- **Renk sınıfı (`col+`/`col-`):** önce dolgu rengi (etiket `color`, kutu `bgcolor`, çizgi `color`). Dolgu nötrse yazı rengi (etiket) ya da kenar rengi (kutu). Mevcut %1 kuralı geçerli.
- **Değişmeyenler:** görülme oranı eleme kuralları (%0,2–%99,8) ve script başına 40 durum sınırı. Her barda ya da yalnız son barda çizen scriptler bu kurallarla zaten elenir.
- **Kayıt anahtarı:** çizim olayları ayrı bir sayaçla anahtarlanır (`draw<n>`). Mevcut plot/şekil durum adları değişmez.

**v3'teki diğer düzeltmeler:**

- **Kütüphane üst düzey kodu:** her deyim ayrı ayrı korunur. Pine'da import edilen kütüphanenin demo/üst düzey kodu çalışmaz; eskiden bunun hatası importu düşürüyordu. `TradingView/ta` → `relativevalue` zinciri bu yüzden kırıktı.
- **Kütüphane enum üyesi:** `ut.Theme.DARK` doğru çözülür. Enum değerleri üzerinde enum tipli metotlar çağrılabilir.
- **Kütüphane fonksiyon seçimi:**
  - Yerleşik ad alanı adıyla import edilen kütüphanede (`import TradingView/ta/9 as ta`) kütüphanenin dışa aktarmadığı adlar yerleşiğe düşer (`ta.atr`, `ta.ema`).
  - Kütüphane aşırı yüklemeleri argüman sayısıyla seçilir.
- **`input(1, defval=1, …)`** çakışması giderildi.

**Düzeltme turu:** v3'ten önceki motorlarla (v0/v1/v2) üretilmiş TÜM kayıtlar tam koşu bitince v3 ile yeniden koşar
(`batch.py retry recent 7 stale`). Eşitlik testi v3 için yinelenir (kodu değişmeyen, strateji dışı örneklem).

## EK-P5 (2026-10-28 ~01:30) — `lookahead_on` scriptleri aramadan çıkarılır

**Gözlem (ilk değerlendirme, yalnız sızıntı denetimi için okundu):** dört sembolde aday listesinin %83–96'sı
`lookahead_on` bayraklı scriptlerden oluştu. Kanıtlıların tamamı bu scriptlerden ya da onlarla kurulan çiftlerden
geliyordu (NDX 419, DAX 386, XAU 411, USOIL 406); temiz scriptlerden kanıtlı 0. Örnekler: MTF Ichimoku, "HTF
candles" Fibonacci, Equinox Timed Extremes; kasa z ≈ 10–12, isabet %73–92. Bunlar üst zaman diliminin henüz
kapanmamış barını gören scriptlerdir. §6'daki "kanıt sayılmaz" kuralı doğruydu ama yetersizdi: sızıntılı tetikler en
iyi 100 aday ve A2'nin 300 tetiklik havuzunu doldurup temiz adayların sıralamaya girmesini engelliyordu. Plasebo
eşiği de bu güçlü tetiklerle şişmişti.

**Değişiklik:** herhangi bir sembolde `lookahead_on` bayrağı taşıyan script (1.386 script; 1.095'i tepki üretiyor)
A1/A2 aramasından, A2 eş havuzundan ve plasebodan tamamen çıkarılır. Temiz scriptlerin tanımı, ölçütleri, eşikleri
ve ufukları değişmez. İlk değerlendirmenin çıktısı `results_lookahead_kontrol/` altında **pozitif kontrol** olarak
saklanır: hat gerçek bir bilgi sızıntısını z ≈ 10 ile buluyor, yani güç sorunu yok.

**Neden sonuca bakmadan sayılır:** değişiklik yalnız sızıntılı kümeyi çıkarır. Temiz scriptlerin hiçbir sonucu bu
karardan önce görülmedi; ilk koşuda temiz adaylardan kanıtlı çıkmadığı bilgisi dışında.

## EK-P6 (2026-10-28 ~03:00, motor v4) — alt zaman dilimi eşlemesi kapanışa göre

**Bulgu:** tekrar sınamasında "MTF VWAP" (NDX h=1 SELL) adayı aynı dönemde DAX/XAU/USOIL'de z 2,3–3,8 ve
+10–20 puanlık ek isabetle tuttu, ama NDX'in diğer zaman dilimlerinde tutmadı. Kaynağı incelendi: script 1h grafikte
`security(..., "45", …)` ile 45 dakikalık veri istiyor. Motor alt zaman dilimi barlarını **açılış** zamanına göre
grafik barına bağlıyordu. 10:00–11:00 mumuna 10:30–11:15 barı düşüyor, yani mum kapandıktan sonraki 15 dakika
görülüyordu. Grafik zaman dilimini tam bölmeyen her alt zaman diliminde (45m, 7m, 25m…) aynı sızıntı var. Bayrak
taşımadığı için EK-P5'in dışında kaldı.

**Düzeltme (motor v4):** alt zaman dilimi barı, **kapanışı** grafik barının (açılış, kapanış] aralığına düşen grafik
barına bağlanır. Tam bölen alt zaman dilimlerinde sonuç değişmez; tam bölmeyenlerde sınırı aşan bar bir sonraki
grafik barına geçer.

**Yeniden koşu:** kaynağında `security`/`security_lower_tf` çağrısı olan ya da bu çağrıyı içeren 85 kütüphaneden
birini import eden ve çalışmış (ok/timeout/runtime_error) 8.059 script v4 ile yeniden koşar (`batch.py retry recent 7
data/sids_ekp6.txt`). Diğer scriptler alt zaman dilimi yoluna hiç girmediği için çıktıları değişemez; v3 etiketiyle
kalır. Ardından değerlendirme ve tekrar sınaması baştan koşar. Ölçütler ve eşikler değişmez. Önceki temiz koşunun
çıktısı `results_v3_ltf_sizinti/` altında saklanır.

## EK-P7 (2026-10-28, sonuçlara bakılmadan) — tüm-script konsensüs çizgisinin sınaması

İnceleme sayfalarındaki konsensüs çizgisi şimdiye dek yalnız betimleyiciydi. Tanım (değişmez):
C_t = (etkin boğa tepkisi − etkin ayı tepkisi) / tepki üreten script sayısı; boğa = `long/up/px+/z+/col+`, ayı =
`short/dn/px-/z-/col-` son ekli durumlar; `lookahead_on` scriptler hariç (EK-P5); motor v4 kayıtları.
Kurallar: C'nin KEŞİF dilimindeki %90 kantilini yukarı kesmesi → AL, %10 kantilini aşağı kesmesi → SAT (yalnız geçiş
barı; ufuk h kadar susturma). 4 sembol × 2 kural × ufuk {1,2,4,8,16,32} = 48 hücre, 1h son 12.000 bar, aynı etiket/
taban/maliyet. Geçme = kanıtlı ölçütü (doğrulama z ≥ 1,645, kasa z ≥ 1,645, lift ≥ 2 p, getiri > maliyet).
Plasebo: C dizisinin 20 dairesel kaydırması, kanıtlı sayısının boş dağılımı. Geçen hücre olursa 5m/15m/4h'te aynı tanımla tekrar.

**EK-P7 sonucu (aynı gün):** kanıtlı 1/48 (plasebo ort 0,05, max 1, p 0,05). Tek hücre DAX h=16 AL; doğrulama n=3,
kasa n=10, keşif z −1,7 → E75 küçük-n artefaktı. Ön kayıttaki çok-TF tekrarı bu hücre için yapılmadı: konsensüs tüm
scriptlerin o TF'de koşmasını gerektiriyor ve n=3 bunu haklı çıkarmıyor (sapma olarak kayıtlı).

## EK-P8 (2026-10-28, sonuçlara bakılmadan) — Kombinasyon Madencisi (kullanıcı isteği)

**İstek:** scriptlerin "AL/SAT" anlamına bakmadan HER türlü tepki karışımının (ör. 2 script AL + 3 script SAT
derken fiyatın yukarı gitmesi) ve yüksek dereceli çakışmaların taranması; ufuk 1, 2, 3 … 15 mumun HER BİRİ ayrı;
bir kombinasyonun bütün örnekleri her ufukta birlikte değerlendirilir.

**Özellik evreni** (sembol × pencere; `lookahead_on` scriptler hariç, EK-P5):
1. Her script durumu iki biçimde: *aktif* (durum o barda doğru) ve *taze* (durumun başlangıcı son 3 bar içinde).
2. Karışım özellikleri: her barda taze boğa tepkisi veren script sayısı ve taze ayı tepkisi veren script sayısı
   (EK-P7 son ek sınıflaması), tepki üreten script sayısına bölünmüş; her biri keşif dilimi kantillerine göre 5 kovaya
   ayrılır → "boğa kova k", "ayı kova k" ikili özellikleri. Bunların çakışması (ör. boğa kova 2 ∧ ayı kova 4)
   "kaç AL, kaç SAT" karışımını temsil eder.
3. Keşifte sıklığı %1–%60 dışında kalan ve bit dizisi birebir aynı olan özellikler elenir (yalnız ilk kopya kalır).

**Kombinasyon ve olay:** kombinasyon = 1–4 özelliğin VE'si. Olay = kombinasyonun doğru olmaya başladığı bar
(önceki barda değil, bu barda doğru); ufuk h için h bar susturma. Yön verinin işaretinden okunur (AL/SAT etiketine
bakılmaz): keşifte z > 0 → AL, z < 0 → SAT.

**Arama (yalnız keşif dilimi, her h = 1…15 ayrı):**
- Tekli: tüm özellikler. Havuz = keşif |z| sırasında ilk 1.000 özellik + 10 karışım kovası özelliği.
- Işın araması: ilk 100 tekli × havuz → ikili; ilk 100 ikili × havuz → üçlü; ilk 100 üçlü × havuz → dörtlü.
  Seçim ölçütü keşif |z|, keşif olayı ≥ N_MIN (1h ve 15m: 200).
- Eşik (çoklu sınama): değerlendirilen TÜM kombinasyonların keşif istatistikleri etiketin 10 dairesel kaydırmasıyla da
  hesaplanır; eşik = kaydırmalarda max|z|'nin %95 kantili. Sınırlılık: ışın gerçek etiketle yönlendirildiğinden bu,
  aynı sayıda sınamanın boş maksimumudur (tam yeniden arama değil); asıl koruma dokunulmamış doğrulama + kasadır.
- Aday listesi: her h'de keşif |z| sırasıyla ilk 100 kombinasyon (%80 olay örtüşmesi ayıklaması).

**Geçme (değişmez, PN-01 ile aynı):** doğrulama z ≥ 1,645 ve n ≥ N_MIN/4; kasa z ≥ 1,645, n ≥ N_MIN/4, lift ≥ 2 p,
getiri > maliyet → kanıtlı. Kanıtlı sayısı, aynı aday sayısında boş beklenti (%5 × %5 × aday sayısı ≈ 0,25/100) ile
kıyaslanır; doğrulama/kasa aynı-yön ve ters-yön sayıları simetri için raporlanır.

**Ufuk profili:** seçilen her kombinasyon için h = 1…15'in HER BİRİNDE (bütün örnekleri birlikte) keşif/doğrulama/kasa
n, isabet, taban, lift, z tablosu.

**Tüm-özellik modeli (keyfi derece çakışma):** her h için LightGBM (keşifte eğitilir, doğrulamada erken durdurma,
kasada okunur; özellikler = keşif |z| ilk 3.000 + karışım sayıları). Ölçüt: kasada AUC − 0,5 ve en emin %10 olayda
isabet − taban; h = 1…15 için 15 sonuç, işaret simetrisi raporlanır.

**Pencereler:** 1h son 12.000 bar (mevcut koşu, motor v4) ve 15m son 12.000 bar (kullanıcı kararı; tüm scriptler
koşulduktan sonra). Kanıtlı kombinasyonlar diğer pencerede ve diğer 3 sembolde aynı tanımla tekrar ölçülür.

**EK-P8 sonuç notu (2026-10-29):** 1h ve 15m, 6.000'er aday: kanıtlı 8 / 4 (boş ≈15), model kasa AUC ≤ 0,571 → X
(RAPOR §Kombinasyon Madencisi). **Sapma (E82):** `lookahead_on` dışlaması yalnız 1h koşu bayraklarından alınıyordu;
1h'te hata veren 187 HTF scripti 15m'de sızdırdı. Dışlama tüm pencerelerin bayrakları ∪ kaynak taramasına çevrildi
(2.750), iki madenci + tekrar + 15m konsensüs bu listeyle yeniden koşuldu; sızıntılı koşu arşivlendi.

## EK-P9 (2026-10-29, sonuçlara bakılmadan) — Kombinasyon Madencisi v2 (kullanıcı isteği)

**Gerekçe:** EK-P8 enjeksiyon sınaması (`kombo_enjeksiyon.py`, NDX 1h, h=4): bilinen güçte 16 tek sinyalden yalnız
+12 p / ~760 olay olan kanıtlı çıktı; tek başına zayıf A, B'nin A∧B kenarı (%8) hiç aday olamadı. Üç neden:
(1) yalnız son 12k bar, (2) z getiri büyüklüğünden (yön sorusu için ~%35 güç kaybı), (3) ışın araması saf etkileşimi
yapısal olarak göremez.

**Değişiklikler:**
1. **Pencere:** sembolün TÜM 1h tarihi (`full_1h_<SYM>`; ilk NDX, 2016-05 → 2026-07, ~60k bar); %60/20/20 kronolojik.
   Script evreni: recent koşusunda o sembolde çalışıp benzersiz durum katan scriptler (NDX 17.628), lookahead hariç (E82).
2. **Puan = yön isabeti:** e = 1[r>0] − p_up(bölme × UTC saati); z = t(e) (≈ ikiterimli z). Getiri ve maliyet yalnız
   kasa ölçütünde (getiri > maliyet) kalır.
3. **İkili etkileşim taraması:** popülerlik (boost) sırasıyla, keşif sıklığı %8–50 ve aralarında |korelasyon| < 0,9 olan
   K = 3.000 özellik; TÜM K·(K−1)/2 çift. Olay = A∧B'nin h-adımlı ızgara barlarında aktif olması (ızgara örtüşmeyen
   etiket verir). Eşik: 10 dairesel kaydırmada tüm çift aramasının max|z|'sinin %95'i. Her h için ilk 100 çift
   (%80 olay örtüşme ayıklaması) doğrulama/kasaya.
4. Işın araması (EK-P8) ve LightGBM (girdi: tekli ilk 3.000 ∪ çift kümesi K) yeni puanla aynen koşar; h = 1…15.

**Geçme (değişmez):** doğrulama z ≥ 1,645, n ≥ N_MIN/4; kasa z ≥ 1,645, n ≥ N_MIN/4, lift ≥ 2 p, getiri > maliyet.
Kanıtlı sayısı boş beklentiyle (aday × %0,25) kıyaslanır.

**Önce duyarlılık (zorunlu):** gerçek veriden önce enjeksiyon sınaması v2 ile koşar — tek sinyaller (lift 3/5/8/12 p ×
sıklık %4/8/16/30) ve saf etkileşim çiftleri (A, B tek başına kenarsız; A∧B'de lift 5/8/12 p). Rapor: hangi
güç/sıklıkta kanıtlı yakalanıyor (tespit sınırı). Hüküm bu sınırla birlikte yazılır ("şu büyüklükte kenar yok").

**EK-P9 sonuç notu (2026-10-30):** enjeksiyon önce koşuldu (tespit sınırı RAPOR'da); gerçek NDX tüm 1h: çift kanıtlı 3
(boş ≈ 3,75, doğrulama 46/82), ışın kanıtlı 11 = ~5 aile (h=2 tek çekirdek 6 satır), ışın SAT doğrulama 97/27 → kasa
35/27 (dönem sürüklenmesi); model kasa AUC 0,494–0,530 → **X**. Sapma yok; ara 5.000-script koşusu tam koşu erken
bittiği için iptal edildi.

