# RAPOR — "Büyük kırmızı mum + destek yok → SELL" ve botun 2026-07-28 NASDAQ SELL'i

**Tarih:** 2026-07-28 · **Sembol:** NAS100 (IC Markets, kutu) · **Veri:** 99.000 × 5m bar,
2025-03-05 → 2026-07-28 (~17 ay), broker sunucu saati (UTC+3) · **Lab:** `research/sell_after_red_lab.py`
· **Friksiyon:** spread 1,5 puan (canlı ölçüm: ask−bid = 1,5) · **Lot referansı:** 5,0 (1 puan = 1 $/lot)

---

## 1. Ekran görüntüsündeki işlem — birincil kanıt

Kullanıcının çemberlediği işlem MT5 geçmişinden ve bot logundan **birebir** bulundu:

```
2026-07-28 10:43:50 (kutu saati)  NDX.INDX:SELL:VIXREG — VIX=18.4 favored=SELL,
                                  2 model onaylıyor → market giriş
2026-07-28 10:43:51  [CANLI] ✅ Açıldı ticket=348877894 → NDX.INDX:SELL:VIXREG |
                     NAS100 SELL @ 27623.8  TP=27543.8  SL=27733.8  lot=5.0  (oy: pulse1,pulse2)
```

| | |
|---|---|
| Sunucu saati | 2026-07-28 **17:43:51** (kutu UTC−4, MT5 sunucusu UTC+3 — üç ayrı saat dilimi var) |
| Scope | **VIXREG** (magic 52890971 = `MAGIC_NUMBER+2`) — momentum scope'u DEĞİL |
| Geometri | sabit TP 80 / SL 110 puan (`config.VIX_REGIME_TP/SL`) |
| Sonuç | 18:18:15'te **SL 27733.8 → −549,00 $** |

**Aynı gün aynı scope'un diğer işlemleri:** 16:31 SELL → TP **+330,50** · 17:43 SELL → SL **−549,00**
· 20:19 SELL → TP **+400,00** · 23:26 SELL → hâlâ açık (+79). Yani gün net **+181,50 $** realize.
Ekranda görülen tek kayıptı.

### Karar zinciri — hangi bileşen hangi zaman dilimine bakıyor?

| Adım | Karar | Zaman dilimi | Mumlara bakıyor mu? |
|---|---|---|---|
| 1 | VIX 18,4 eşiğinin **altında** → NDX için SELL "favored" | **günlük** (makro) | hayır |
| 2 | `pulse1` + `pulse2` SELL CONFIRM verdi (2 oy) | backend panel modelleri (5m/15m/1h karışık) | dolaylı |
| 3 | Trend kapısı: fiyat **1h EMA50**'nin altında → SELL hizalı ✓ | **1 saat** | hayır |
| 4 | Konum kapısı: son 48×5m = **4 saatlik dalga** 27443,6–27871,5; fiyat 27623,8 → konum **0,42** ≥ 0,40 ✓ | 5m ama yalnız **dip/tepe** olarak | hayır |
| 5 | Backend Precision Veto → **gölge** (`VIXREG_BACKEND_VETO=0`), bloklamaz | — | — |
| 6 | Geometri: sabit 80/110 puan | — | hayır |

> **Sorunun cevabı:** Evet, sistem başka zaman dilimlerine bakıyor (günlük VIX + 1h EMA50 + 4 saatlik
> dalga). Ama asıl önemli olan şu: **hiçbir adım son mumların rengine, gövdesine veya hacmine
> bakmıyor.** Gözünün gördüğü "iki büyük yeşil mum" bilgisi bu karar zincirinde hiç yok. 5m grafiği
> yalnızca 4 saatlik dalganın dip/tepesini bulmak için kullanılıyor.

### Log'un ortaya çıkardığı asıl mekanizma: kapı bir "çekim noktası" yaratmış

Girişten önceki dakikaların logu:

```
10:36  KONUM KAPISI: konum 0.34 → SELL açılmadı
10:37  KONUM KAPISI: konum 0.34 → SELL açılmadı
10:39  KONUM KAPISI: konum 0.26 → SELL açılmadı
10:41  KONUM KAPISI: konum 0.35 → SELL açılmadı
10:42  KONUM KAPISI: konum 0.38 → SELL açılmadı
10:43  VIX=18.4 favored=SELL, 2 model onaylıyor → market giriş     ← konum 0.42'ye çıktığı ilk tarama
```

Sinyal (VIX + pulse oyları) saatlerdir açıktı; **girişin zamanını sinyal değil, konum kapısının
0,40 eşiği belirledi.** Fiyat dipten toparlanıp eşiği geçtiği ilk dakikada emir gitti — yani bot
yapısal olarak "tepkinin/yükselişin içine" satıyor. Kullanıcının gözlemi mekanik olarak DOĞRU.

### Yan bulgular (kayda değer)

* **VIX = 18,4, eşik = 18,4.** Kod `vix >= 18.4 → BUY`. Yani gerçek değer 18,35–18,399 aralığındaydı;
  yüzde birlik bir VIX farkı bütün günün NDX yönünü ters çevirebilirdi. Bıçak sırtı.
* **Kayma (slippage):** 16:31'deki SELL, TP'si 27703,9 olacak şekilde ~27783,9 teklifinden
  hesaplanmış ama **27770,0'dan** dolmuş → hızlı düşen piyasada ~14 puan kötü fiyat.
* **Repo ile kutu ayrışması:** repo `config.SYMBOL_MAP` NASDAQ için `USTEC`, petrol için `XTIUSD`
  diyor; kutunun kendi (gitignore'lu) config'i **`NAS100` / `SpotCrude`** kullanıyor ve lot 5,0
  (repodaki `LOT_SIZE = 0.10` değil). Analiz yapan herkes bu tuzağa düşer.
* **Kutuda `research/` sparse-checkout dışı** — `git pull` dosyayı indexe alıyor, diske yazmıyor.
  Lab dosyası kutuya doğrudan aktarıldı (`lab_sell_after_red.py`, sha1 doğrulandı).

---

## 2. Kullanıcı kurgusunun ölçümü

**Kurgu:** 5m'de büyük kırmızı mum (gövde ≥ 1,0×ATR14 **ve** gövde/menzil ≥ 0,55) kapanınca,
kapanış son 400 barın güçlü desteklerinden birine denk gelmiyorsa → altı boş → SELL.

Güçlü destek = son 400 barın onaylı fraktal dip pivotları, 0,35×ATR toleransıyla kümelenmiş,
**≥2 dokunuş**. Sızıntı yok: pivot ancak sağındaki 2 bar kapandıktan sonra "onaylı" sayılıyor,
giriş sinyal barının kapanışı, sonuç yalnız sonraki barların high/low'u, aynı barda TP+SL → KAYIP.

**Olay sayısı: 5.574 büyük kırmızı mum** (tüm barların %10,8'i büyük mum).

### 2.1 Filtresiz — "her SELL mumunun ardından aç"

| Geometri | n | WR | EV/işlem | Toplam | 5 lot ile | P(EV>0) |
|---|---|---|---|---|---|---|
| Bot 80/110 | 5.574 | 53,5 % | −1,14 p (−0,010R) | −57,9R | **−31.828 $** | %15 |
| ATR 1,0:1,0 | 5.574 | 44,1 % | −2,05 p (−0,118R) | −658R | −57.216 $ | %0 |
| ATR 1,5:1,0 | 5.574 | 36,1 % | −1,83 p (−0,099R) | −550R | −50.926 $ | %0 |
| ATR 0,75:1,0 (yüksek WR) | 5.574 | 50,3 % | −2,08 p (−0,120R) | −667R | −57.874 $ | %0 |
| TP = alttaki destek / SL 1ATR | 3.466 | 35,5 % | −1,28 p (−0,094R) | −325R | −22.168 $ | %0 |

Sonuç dağılımı (80/110): TP %45,1 · SL %29,5 · zaman-stopu %25,4 · **ortalama tutuş 36 bar (3 saat)**.

### 2.2 Destek sınıfına göre — hipotez TERSİNE çıktı

| Sınıf | Tanım | Bot 80/110 EV | ATR 1:1 EV |
|---|---|---|---|
| **BOŞLUKTA** (kullanıcının aldığı taraf) | alttaki en yakın destek ≥0,75 ATR uzak | −0,011R (−19.281 $) | −0,136R |
| ARADA | 0,25–0,75 ATR | −0,026R (−16.128 $) | −0,090R |
| **DESTEKTE** (kullanıcının elediği taraf) | kapanış bir seviyeye ≤0,25 ATR | **+0,005R (+3.581 $)** | −0,097R |

Yani "kapanış desteğe değmiyorsa sat" kuralı, üç sınıfın **en kötüsünü** seçiyor. Fark küçük
(hepsi ≈0), ama işaret hipotezin tersine.

### 2.3 Kırılma olasılığı tablosu (istenen hesap) — raporun en kullanışlı çıktısı

Büyük kırmızı mum kapanışından sonra, **alttaki en yakın desteğin 2 saat (24 bar) içinde
0,25×ATR aşılarak kırılma oranı**:

| Desteğin uzaklığı | n | kırıldı | hacim ≥1,3× iken | ABD seansında |
|---|---|---|---|---|
| 0,00–0,25 ATR | 653 | **%89,7** | %94,6 | %91,6 |
| 0,25–0,50 ATR | 600 | %86,0 | %91,0 | %82,9 |
| 0,50–0,75 ATR | 618 | %78,5 | %79,8 | %73,3 |
| 0,75–1,25 ATR | 852 | %69,4 | %72,8 | %67,4 |
| 1,25–2,00 ATR | 753 | %61,1 | %64,5 | %60,5 |
| ≥ 2,00 ATR | 1.243 | **%29,9** | %35,5 | %30,0 |
| **tümü** | 4.719 | %63,8 | | |

**Okunuşu — ve hipotezin kırıldığı yer:** seviye en çok **YAKIN olduğunda** kırılıyor (%90),
uzak olduğunda değil (%30). "Altında destek yok" demek "kırılacak" demek değil; tam tersine
o mesafenin kendisi seviyeyi koruyor. Ayrıca **kırılma ≠ para**: %90 ihtimalle 0,25 ATR delinmesi,
80 puanlık bir TP'yi ödemiyor. Yüksek olasılık ile kârlılık aynı şey değil — 2.1'deki tablo bunun
faturası.

### 2.4 Dayanıklılık bataryası

* **Çeyreklik:** 7 çeyreğin 6'sında negatif (2025Ç1 −0,245R … 2026Ç2 −0,046R); tek pozitif
  2026Ç3 (+0,025R, n=162 — henüz 1 ay).
* **Kronolojik kör test:** eğitim (%70) −0,009R → TEST (%30) −0,017R (80/110). Üç geometride de
  hem eğitimde hem testte negatif.
* **Seans:** hepsi negatif; en az kötü ABD (−0,060R), en kötü AVRUPA (−0,164R).
* **Plasebo/taban:** koşulsuz SELL (her 6. bar, n=16.421) 80/110 ile −2,27 p. Büyük kırmızı mum
  koşullusu −1,14 p. → **Kırmızı mum GERÇEKTEN ~+1,1 puanlık bir aşağı eğilim taşıyor** ama
  spread 1,5 puan. Sinyal var, eşiğin altında.
* **Ayna kontrolü:** büyük yeşil mum → BUY da negatif (−0,45 p / −0,004R). Sorun SELL tarafına
  özgü değil; 5m'de "büyük mumun yönüne devam" ailesi bu geometrilerde ölü.
* **Filtre taraması + kör test:** 15 aday filtre, tekli+ikili tüm kombinasyonlar, 3 geometri;
  eğitimde en iyi 12 aday seçildi → **kör testte +EV kalan 6/12**. Şans beklentisi 6/12.
  Yani kurtaran filtre yok. (2026-07-28'deki NDX BUY çalışmasında 82 filtre adayının kör testte
  çökmesiyle aynı sonuç.)

### 2.5 Verdikt

> Bu kurgu, kendi başına canlıya alınacak bir scope **değil**. 17 ayda 5.574 olayla,
> beş geometride, yedi çeyrekte, kör testte ve plasebo karşısında +EV üretmiyor.
> Destek filtresi kurguyu iyileştirmiyor, kötüleştiriyor. Sezgideki gerçek pay (kırmızı mumun
> taşıdığı ~1,1 puanlık aşağı eğilim) spread'in altında kalıyor.

---

## 3. Botun konum kapısının tarihsel karnesi (asıl aksiyon burada)

Popülasyon: H1 EMA50 altı (SELL hizalı) tüm anlar, ≥24 bar arayla örneklenmiş, geometri 80/110.
*(Uyarı: işlemler örtüşüyor, ufuk 72 bar → n şişkin, güven aralıkları dar okunmalı.)*

| 4 saatlik dalgadaki konum | n | WR | EV | 5 lot | P(EV>0) |
|---|---|---|---|---|---|
| 0,00–0,40 — **kapının BLOKLADIĞI bölge** | 1.347 | 56,1 % | **+0,019R** | +14.336 $ | %83 |
| 0,40–0,50 — **girişlerin yığıldığı bant** | 872 | 54,2 % | **−0,000R** | −165 $ | %50 |
| 0,50–0,65 | 882 | 55,6 % | +0,019R | +9.382 $ | %77 |
| 0,65–0,80 | 769 | 49,7 % | −0,062R | −26.142 $ | %2 |
| 0,80–1,00 (dalga tepesi) | 611 | 47,5 % | **−0,083R** | −27.772 $ | %0 |

Eşik geçiş anında girmek (botun bugün yaptığı): 0,40 geçişi +0,017R · 0,50 geçişi +0,003R
· 0,60 geçişi +0,006R · 0,70 geçişi **−0,039R**.

**İki ölçüm çelişiyor:**

| | dip bölge (0–0,40) | tepe bölge (0,65+) |
|---|---|---|
| Canlı 30 gün, 175 VIXREG SELL (kapının gerekçesi) | WR %53, −3.738 $ | WR %66, +2.860 $ |
| Bu çalışma, 17 ay, H1-trend altı | WR %56, +0,019R | WR %48–50, −0,062…−0,083R |

Bu bir rejim farkı olabilir (son 30 gün NDX toparlanma rejimindeydi; dipten satmak cezalandırıldı)
ya da 175 işlemlik örneklem gürültüsü. **Tek bir teste dayanarak kapı ters çevrilmemeli.**
Ama iki şey ölçümden bağımsız olarak doğru:

1. **Kapı bir tetikleyiciye dönüşmüş.** Sinyal saatlerce açıkken girişin zamanını eşik belirliyor
   ve girişler tam olarak **0,40–0,50 bandında** (EV = 0,000R, P = %50) yığılıyor. Bugünkü işlem
   konum 0,421 ile açıldı; bir önceki taramada 0,38'di. Bu bir strateji değil, bir sınır artefaktı.
2. **En güçlü ve en tutarlı negatif işaret üst bantta:** 0,65+ konumda SELL, P(EV>0) = %0–2.
   Kapı bugün ALT sınır koyuyor, ÜST sınır koymuyor.

---

## 4. Kullanıcının asıl gözlemi: "yükselen mumların içine satıyor" — ölçüldü

Popülasyon: botun **bugünkü** kapılarını geçen anlar (H1 EMA50 altı + konum ≥0,40), n=1.320,
geometri 80/110.

| Giriş anındaki son 2 mumun net hareketi | n | WR | EV | P(EV>0) |
|---|---|---|---|---|
| **GÜÇLÜ YUKARI (≥ +1,0 ATR)** ← bugünkü vaka | 420 | 55,0 % | **+0,001R** | %51 |
| yukarı (0 … +1,0 ATR) | 460 | 53,7 % | −0,009R | %39 |
| aşağı (−1,0 … 0) | 347 | 51,6 % | **−0,038R** | %18 |
| GÜÇLÜ AŞAĞI (≤ −1,0 ATR) | 93 | 58,1 % | +0,047R | %71 |

Son mum yeşil: −0,008R · son mum kırmızı: −0,013R → **fark yok.**

Önerilen ek kapı ("yukarı momentumun içine SELL açma", mom2 < +0,75 ATR):
kapısız −0,010R → kapılı **−0,015R** (daha kötü). Kör testte de aynı yön:
TEST kapısız +0,011R (n=407) → kapılı +0,003R (n=240).

> **Dürüst cevap:** Bugünkü kayıp acı verici ama sistematik bir hata değil. 17 ayda, iki büyük
> yeşil mumun ardından açılan SELL'ler **en kötü grup değil, en nötr grup**. "Yeşil mumların
> içine satma" filtresi eklenseydi kazananları da elerdi — hem eğitimde hem kör testte.
> Gözlemin mekanik kısmı doğru (bot mumlara bakmıyor), tahmin kısmı veriyle desteklenmiyor.

---

## 5. Öneriler (hiçbiri uygulanmadı — karar kullanıcının)

1. **Hiçbir şeyi bugün değiştirme.** Ne kullanıcı kurgusu canlıya alınmalı, ne konum kapısı
   ters çevrilmeli.
2. **Gölge ölçüm (bedava, riski sıfır):** bot zaten `gate_skipped.jsonl`'e konum kapısının elediği
   her sinyali `pos` ile yazıyor. `research/gate_audit.py` bunları 1m barlarla replay ediyor.
   2 hafta boyunca **0–0,40 elenenler** ile **0,65+ geçenler** aynı geometriyle karşılaştırılsın;
   çelişkiyi canlı veri çözer.
3. **En savunulabilir tek değişiklik:** konum kapısına **üst sınır** (0,65) eklemek — hem bu
   çalışmanın en güçlü negatif sinyali (P(EV>0) = %0–2), hem de kapının bugünkü tek yönlü
   yapısındaki asimetriyi giderir. Yine de canlı kanıt tersini söylediği için önce gölgede.
4. **Yapısal:** eşik geçişini tetikleyici olmaktan çıkar — girişi ya fiyat olayına bağla
   (taze 5m alt-dip / bearish kapanış) ya da konumun N tarama boyunca eşiğin üstünde kalmasını
   şart koş. Bugünkü hâlde giriş zamanını sinyal değil sınır belirliyor.
5. **Kırılma olasılığı tablosu (2.3)** panele/decider'a bağlam olarak verilebilir — kendi başına
   işlem açtırmaz ama "bu seviye tutar mı?" sorusuna kalibre bir cevap üretir.

## 6. Kısıtlar

* Örneklem MT5'in 99.000 bar tavanı yüzünden 2025-03-05'te başlıyor; tek broker, tek sembol.
* Aynı-bar TP+SL belirsizliği %0,1 (80/110) – %2,9 (ATR 0,75) → 1m çözünürlüklü doğrulama
  yapılmadı, etkisi ihmal edilebilir.
* Bölüm 3–4 popülasyonu VIX rejimi ve pulse oylarını İÇERMİYOR (canlı VIXREG'in tam kopyası değil);
  işlemler örtüşüyor.
* Friksiyon yalnız spread (1,5 p); komisyon/swap yok, kayma modellenmedi (bugün ~14 puan görüldü).

---

# EK — HACİM × TP/SL GRID TARAMASI (kullanıcı isteği, 2026-07-28 gece)

**Soru:** "hacimleri ve TP/SL seviyelerini oynayarak en yüksek başarı oranına sahip,
büyük düşüş mumundan sonraki mumda işlem açma kurgusunu bulabilir misin?"

**Kurulum:** giriş HER ZAMAN 2. mumun (teyit mumu) kapanışında. 6 hacim kovası ×
11 TP × 11 SL (ATR katı) = **726 hücre**, ayrı olarak 64 sabit-puan hücresi,
3 teyit varyantı (yok / 2.mum kırmızı / 2.mum 1.'in dibini kırdı).
Sıralama YALNIZ eğitimde (%70), sonuç kör testte (%30).
Labs: `research/vol_tpsl_grid.py`, `research/tight_stop_probe.py`, `research/horizon_probe.py`.

## E1. Grid gerçekten bir şey buluyor mu? (çoklu-test kontrolü)

| ölçüm | değer |
|---|---|
| eğitimde +EV olan hücre | 70 / 726 |
| eğitim EV ↔ test EV korelasyonu | r = +0,597 |
| TÜM hücrelerde testte +EV oranı (şans çıtası) | %11 |
| eğitimde +EV olanların testte +EV kalma oranı | %11 |
| **seçimin sağladığı avantaj** | **+0 puan** |

"Her çeyrekte tutan hücre" (istikrar seçimi) denendi: 726 hücreden 8'i eğitim
çeyreklerinin ≥%75'inde pozitifti; **kör testte 8'den yalnız 1'i pozitif kaldı**
(+0,002R ≈ sıfır). Yani klasik "en iyi hücreyi seç" de, "istikrarlı hücreyi seç" de
işe yaramıyor.

## E2. Hacme dayalı TP/SL — her kovanın kendi optimumu

| hacim kovası | eğitimde en iyi TP/SL | eğitim EV | KÖR TEST EV |
|---|---|---|---|
| hepsi | 2,00/3,00 ATR | +0,001R | −0,036R |
| <0,9× (sakin) | eğitimde +EV hücre yok | — | — |
| 0,9–1,2× | 3,00/3,00 ATR | +0,030R | +0,001R |
| 1,2–1,5× | eğitimde +EV hücre yok | — | — |
| 1,5–2,0× | 2,50/2,50 ATR | **+0,176R** | **−0,183R** |
| ≥2,0× (patlama) | eğitimde +EV hücre yok | — | — |

En parlak eğitim sonucu (hacim 1,5–2,0×, +0,176R) kör testte tam tersine döndü.
**Hacme dayalı TP/SL diye tutarlı bir yapı yok.**

Hacim deseni boyutu (geometri sabit): teyit mumunun hacmi ≥1,2× → ±0,00R;
hacim ARTIYOR → −0,019/−0,025R (iki dönemde de eksi); hacim DÜŞÜYOR → +0,001/+0,006R.
Tek tutarlı işaret bu ve büyüklüğü ihmal edilebilir.

## E3. Tek hayatta kalan aile: SIKI STOP + UZAK HEDEF

Sabit-puan gridinde bir aile hem eğitimde hem kör testte pozitif çıktı ve tabanı
(koşulsuz SELL) iki dönemde de yendi:

| geometri | eğitim EV | kör test EV | tümü | taban farkı (tümü) |
|---|---|---|---|---|
| TP 80 / SL 30 | +0,016R | +0,079R | +0,035R (+1,06 p/işlem) | **+0,069R** |
| TP 120 / SL 25 | +0,046R | +0,150R | +0,078R (+1,95 p/işlem) | — |
| TP 80 / SL 110 (canlı) | +0,013R | −0,014R | +0,004R | +0,028R |

Knife-edge değil: SL 20→50 arası **tüm** komşu hücreler pozitif (+0,004…+0,051R),
TP 80→150 arası aynı. Üç teyit varyantında da aynı aile tepede. Çeyreklik:
7 çeyreğin 5'i pozitif.

## E4. …ama kenar girişten DEĞİL, zaman-stopundan geliyor

TP 80 / SL 30, ufuk 72 bar, n=2.147 sonuç anatomisi:

| sonuç | oran | ortalama |
|---|---|---|
| TP | %25,7 | +80,0 p |
| SL | %68,9 | −30,0 p |
| zaman-stopu | %5,4 | +21,9 p (bunların %79'u kârda) |

Hesap: 0,257×80 + 0,689×(−30) = **−0,11 p** → TP/SL kısmı tam başabaş.
Zaman çıkışları: +1,18 p → **toplam +1,06 p'nin tamamı, işlemlerin %5,4'ünden geliyor.**
Ufuk taraması bunu doğruluyor: EV ufukla birlikte monoton büyüyor
(12 bar −0,018R → 24 −0,006 → 48 +0,017 → 72 +0,035 → 96 +0,044).
Yani sinyalin kendisi değil, "6 saat tut" kuralı para kazandırıyor — 116 işlemlik
ince bir dilim.

## E5. "En yüksek başarı oranı" sorusunun doğrudan cevabı

| TP/SL (puan) | isabet% | başabaş% | fark | EV | sonuç |
|---|---|---|---|---|---|
| 20/80 | **%77,4** | %80,0 | −2,6 | −0,009R | **zarar** |
| 25/60 | %68,3 | %70,6 | −2,3 | −0,013R | zarar |
| 30/50 | %59,8 | %62,5 | −2,7 | −0,026R | zarar |
| 50/50 | %46,9 | %50,0 | −3,1 | −0,008R | zarar |
| 80/30 | %25,7 | %27,3 | −1,6 | +0,035R | ≈başabaş (zaman-stopu sayesinde) |
| 120/25 | %15,7 | %17,2 | −1,5 | +0,078R | ≈başabaş (zaman-stopu sayesinde) |

**Yapısal bulgu:** "fark" sütunu her geometride −1,5 … −3,4 puan. Yani isabet oranı
her zaman başabaşın ALTINDA ve TP/SL oynatarak bu açık kapanmıyor — bu, friksiyon +
yukarı sürüklenmenin sabit vergisi. **Yüksek başarı oranı isteyen her ayar zarar
ediyor;** artıya geçen tek profil %15–26 isabetli, 2,7–4,8:1 risk-getirili olan.

## E6. Kayma (slippage) testi — asıl öldürücü

| spread/kayma | TP 80/SL 30 EV (tümü) |
|---|---|
| 1,5 p (canlı ölçüm) | +0,035R |
| 3,0 p | −0,015R |
| 5,0 p | −0,068R |
| 8,0 p | −0,180R |

30 puanlık stop ile kenar ~2,5 puanlık friksiyonda ölüyor. **Bugün canlıda 14 puanlık
kayma gözlendi** (16:31'deki hızlı piyasa emri). Bu kurgu tam da hızlı piyasada
tetiklendiği için kaymaya en açık kurgu.

## E7. Verdikt

> Hacim koşulu veya TP/SL ayarı ile **güvenilir yüksek başarı oranı bulunamadı**.
> Grid'in seçim gücü sıfır (şansla aynı), hacme dayalı TP/SL kör testte çöküyor,
> yüksek-isabet geometrilerinin hepsi zararda. Artıya geçen tek aile (sıkı stop +
> uzak hedef) kenarını girişten değil zaman-stopundan alıyor ve 3 puanlık kaymada
> ölüyor. **Canlıya bağlanacak bir şey yok.**
>
> Kayda değer tek pozitif: büyük kırmızı mum + teyit girişi, koşulsuz SELL'e göre
> tutarlı biçimde ~+2 puan/işlem daha iyi (her iki dönemde de). Bu gerçek ama
> spread kadar; ancak icra maliyeti sıfıra yakın bir kurgu (limit emirle giriş)
> üzerine inşa edilirse anlam kazanır.

---

# EK-2 — LİMİT EMİRLE GİRİŞ (2026-07-29)

**Neden:** market girişinin kenarı spread + kaymaya eşit. SELL LİMİT emri (a) daha iyi
fiyattan doldurur, (b) girişte kayma yemez — karşılığında (c) her zaman dolmaz,
(d) hemen kaçan işlemleri ıskalar. Lab: `research/limit_entry_lab.py`,
`limit_deep_probe.py`, `limit_baseline_control.py`.

Model: barlar BID; SELL LİMİT L'de high ≥ L olunca **tam L'den** dolar (kayma yok);
çıkışta spread ödenir (market versiyonuyla aynı); dolum barında SL mümkünse KAYIP
(konservatif). Sinyal: büyük kırmızı mum + teyit (2. mum 1.'in dibini kırdı),
limit teyit mumunun kapanışının X×ATR ÜSTÜNE konur.

## L1. Küçük geri çekilme limitleri ÖLDÜRÜCÜ — ters seçilim

| giriş | dolum% | EV/işlem | EV/sinyal |
|---|---|---|---|
| MARKET (teyit mumu kapanışı) | %100 | +1,03 p | **+1,03 p** |
| +0,20×ATR / 3 bar | %87,6 | −0,25 | −0,22 |
| +0,30×ATR / 6 bar | %86,9 | −0,47 | −0,41 |
| +0,50×ATR / 6 bar | %78,8 | −0,06 | −0,05 |

**Sebep — ters seçilim ölçüldü:** +0,30×ATR/6 bar kurgusunda limitin **dolmadığı**
282 sinyalin market'teki beklentisi **+43,08 puan**; dolan 1.863 sinyalin ise **−5,33 puan**.
Yani market versiyonunun tüm kârı, hemen kaçan (%13) işlemlerden geliyor ve küçük
limit tam olarak onları eliyor.

## L2. BÜYÜK geri çekilme limitleri farklı bir işlem — ve çalışıyor

+0,75 … +1,00×ATR'de limit, "kırılımı satmak"tan çıkıp **"gerilmiş tepkiyi satmak"**
oluyor (mean-reversion). TP 80 / SL 30:

| konfig | dolum% | EĞİTİM EV/sinyal | KÖR TEST EV/sinyal | TÜMÜ |
|---|---|---|---|---|
| +0,75×ATR / 12 bar | %77,5 | +0,51 | +1,54 | +0,82 |
| +0,75×ATR / 24 bar | %83,9 | +0,37 | +2,19 | +0,93 |
| +1,00×ATR / 6 bar | %58,1 | +0,47 | +2,06 | +0,96 |
| **+1,00×ATR / 12 bar** | %69,4 | **+0,97** | **+2,15** | **+1,33** |
| +1,00×ATR / 24 bar | %78,4 | +0,89 | +2,55 | +1,40 |
| +1,50×ATR / 6 bar | %41,7 | +0,86 | −0,42 | +0,47 |

9 konfigürasyonun 8'i hem eğitimde hem kör testte pozitif (yalnız +1,50/6 bar çöküyor).
Market karşılaştırması: +1,03 → **+1,33** (ve limit girişte kayma yemez, market yer).

## L3. TABAN KONTROLÜ — koşul gerçekten bilgi taşıyor mu? (asıl kanıt)

Aynı limit mekaniği (+1,00×ATR / 12 bar / TP80 SL30) üç popülasyonda:

| popülasyon | sinyal | EĞİTİM EV/sinyal | KÖR TEST EV/sinyal | TÜMÜ |
|---|---|---|---|---|
| **büyük kırmızı mum + teyit** | 2.145 | **+0,97** | **+2,15** | **+1,33** |
| yalnız büyük kırmızı mum (teyitsiz) | 5.589 | −0,27 | +1,48 | +0,25 |
| **KOŞULSUZ her 6. bar (taban)** | 16.479 | **−1,15** | **−0,91** | **−1,07** |

**Monoton merdiven:** koşul eklendikçe sonuç düzeliyor ve taban her iki dönemde de
belirgin negatif. Yani "her tepkiyi sat" çalışmıyor; kırmızı mum + teyit koşulu
**+2,41 puan/sinyal** taşıyor. Offset taramasında fark 0,25→1,50 ATR arasında her
noktada pozitif (tepe +1,00'de, +2,41).

## L4. Zayıflıklar (dürüstlük)

* **Çeyreklik istikrarsız:** +6,56 / −0,75 / −1,69 / +1,02 / +6,44 / −0,98 / +4,39
  → 7 çeyreğin 3'ü negatif; ortalamayı iki çeyrek (2025Ç1, 2026Ç1) taşıyor.
* **Friksiyon payı ince:** spread 1,5 → +1,33 · 3,0 → +0,10 · 5,0 → −1,51.
  (Market aynı seviyelerde +1,03 / −0,48 / −2,07 → limit her seviyede daha iyi,
  ayrıca girişte kayma yemiyor.)
* **Mutlak büyüklük küçük:** +1,33 p/sinyal ≈ 6,65 $/sinyal (5 lot), ~126 sinyal/ay,
  %69 dolum → ~87 işlem/ay, ~840 $/ay. Tek sembol, tek broker, 17 ay.
* **Çoklu test riski:** bu sonuç, bugün taranan yüzlerce konfigürasyonun içinden çıktı.
  Onu ayakta tutan şey grid sıralaması değil, **eşleştirilmiş taban kontrolü + monoton
  koşul merdiveni + komşu parametrelerin de pozitif olması**.

## L5. Verdikt

> Limit girişli versiyon, bu soruşturmada **eğitim + kör test + eşleştirilmiş taban +
> parametre komşuluğu** dördünü birden geçen ilk konfigürasyon. Ama çeyreklik
> istikrarsızlığı ve ince friksiyon payı nedeniyle doğrudan canlıya alınmamalı.
> Doğru adım: **gölge ölçüm** (sanal emir, gerçek fiyatla çözüm, 3-4 hafta) — proje
> zaten `shadow_trade_tracker` altyapısına sahip. Riski sıfır, kanıtı gerçek.
>
> Konfigürasyon: NAS100 5m · büyük kırmızı mum (gövde ≥1×ATR14, gövde/menzil ≥0,55)
> · teyit: sonraki mum 1. mumun dibinin altında kapanır · SELL LİMİT = teyit mumu
> kapanışı + 1,00×ATR · 12 bar geçerli (dolmazsa iptal) · TP 80 / SL 30 puan
> · 72 bar (6 saat) zaman-stopu.

---

# EK-2 — LİMİT EMİRLE GİRİŞ TESTİ + GÖLGE BAĞLANTISI (2026-07-29)

## L1. Limit emir kurguyu kurtarmıyor — BOZUYOR

Karar teyit mumunun kapanışında; market yerine kapanışın ÜSTÜNE SELL LIMIT
(daha iyi fiyat), X bar içinde dolmazsa iptal. Lab: `research/limit_entry_lab.py`.
Karşılaştırma "sinyal başına EV" ile (dolmayan = 0; market %100 dolduğu için tek adil ölçü).

Kazanan geometri **TP 120 / SL 25** üzerinde:

| giriş türü | doluş% | sinyal başına EV | kör test EV |
|---|---|---|---|
| **MARKET (referans)** | %100 | **+1,99 p** | +3,88 p |
| limit +0,10 ATR (exp 6 bar) | %94,8 | +0,88 p | +2,71 p |
| limit +0,20 ATR | %91,2 | +0,36 p | +2,74 p |
| limit +0,30 ATR | %86,9 | −0,04 p | +2,08 p |
| kırmızı mumun %50'si (exp 12) | %57,4 | +0,36 p | +0,41 p |
| kırmızı mumun açılışı (exp 12) | %40,5 | +0,98 p | +1,14 p |

**Neden:** ters seçilim. Limit yalnız fiyat GERİ GELİRSE dolar; kırılım gerçekten
işleyecekse (en kârlı senaryolar) fiyat geri gelmez ve tam o işlemler kaçar.
Dolan işlemler bile daha kötü — "dolan başına EV" market'in altında. Birkaç puanlık
fiyat iyileştirmesi, kaçan kazananları ödemiyor. Eski 80/110 geometrisinde derin
limitler (+0,50 ATR, %50 seviyesi) marjinal iyileşme veriyor ama o geometri
kör testte zaten negatifti.

**Karar:** limit-emir varyantı reddedildi; gölge MARKET girişini ölçer. Yine de
her gölge işleminin `details`'ine iki limit fiyatı yazılıyor
(`limit_px_010atr`, `limit_px_confirm_high`) — 2-3 hafta sonra gerçek verili
karşı-olgusal replay yapılabilsin diye.

## L2. Gölge bağlantısı (canlı emir YOK)

`shadow_trade_tracker`'a 4. kaynak: **`redcandle`** (commit 41fed6a).

| | |
|---|---|
| Tetik | büyük kırmızı 5m mum (gövde ≥1×ATR14, gövde/menzil ≥0,55) + teyit mumu kapanışı önceki dibin altında |
| Giriş | teyit mumunun kapanışı (son KAPANMIŞ bar — koşan bar asla) |
| Geometri | **tp120_sl25** ve **tp80_sl30** paralel (iki ayrı gölge işlem) |
| Zaman-stopu | 6 saat (72×5m — kenarın kaynağı, kısaltma!) |
| Sembol | NDX.INDX (kanıt NAS100 puanlarında; env `REDCANDLE_SHADOW_SYMBOLS`) |
| Kapatma | `REDCANDLE_SHADOW_ENABLED=0` |
| İzolasyon | `shadow_pattern_trades` tablosu; prediction_logs/lifecycle'a dokunmaz |

Doğrulama: saf çekirdek `detect_redcandle_setup` birim testli — 2026-07-28'in
gerçek barlarında 16:35 mumunu yakalıyor (gövde 1,82 ATR, teyit 27588,8 < 27628,0);
fitilli/yeşil/küçük/teyitsiz mumları eliyor. Uçtan uca test: tespit → insert →
çözümleme (win R=4,8 / 2,67) geçti.

⚠️ **Migration bekliyor:** `shadow_pattern_trades.source` CHECK kısıtına
`redcandle` ekleyen `supabase/migrations/20260729_shadow_redcandle_source.sql`
DB erişimi salt-okunur olduğu için UYGULANAMADI. Bu yüzden satırlar şimdilik
disk yedeğine düşüyor (`backend/data/shadow_fallback_trades.jsonl` — yeni eklendi;
önceden bellekteydi ve her restart'ta siliniyordu). Migration uygulanınca DB'ye
akmaya kendiliğinden başlar.

**Değerlendirme kriteri (2-3 hafta sonra):** n≥30 çözülmüş işlemde sinyal başına
EV > 0 VE gerçek doluş fiyatlarıyla kayma ölçümü < 3 puan değilse aile çöpe.
