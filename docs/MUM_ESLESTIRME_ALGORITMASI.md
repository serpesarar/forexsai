# Mum Eşleştirme Motoru ("Geçmiş Eşleşme Radarı") — Algoritma Tasarımı

> **Sürüm:** v0.2 · 2026-10-12 · **Durum:** TASARIM — kod yok; ön-kayıt **taslak** (`research/mum_eslestirme_20261012/PROTOCOL_TASLAK.md`).
> **Geçmiş:** v0.1 (`research/mum_eslestirme_20261012/arsiv/MUM_ESLESTIRME_ALGORITMASI_v0.1.md`) → Codex incelemesi
> (`docs/MUM_ESLESTIRME_TASARIM_INCELEMESI_CODEX.md`) → v0.2 (bu belge; değişiklikler §0.2).
> **Kanıt klasörü:** `research/mum_eslestirme_20261012/` — fizibilite ölçümleri yalnız eşleşme SAYAR, gelecekteki fiyata
> bakmaz (ön-kayıt temiz). v0.2'nin sayıları `fizibilite_4_nedensel.py`'den gelir (nedensel + ortak ölçek).
> **Bağlı kurallar:** CLAUDE.md 1./2./3. KURAL · `docs/KAPI_KAYIT_DEFTERI.md` PM, PM-2, OLD-13, OLD-15, IO-18/IO-20,
> MK-01..05, GF-01, ME-00 / ME-REV / ME-01, tuzaklar E1–E25.

> ⚠️ **2026-10-12 keşif testi sonucu (ME-02, `research/mum_eslestirme_20261012/RAPOR_KALDIRMA_TESTI.md`):** 98.260 geçmiş
> karar anı, 4 sembol × 6 TF × 3 ufuk, 4 eşleştirme yöntemi × 5 eşleşme-kaldırma varyantı: **yön, büyüklük ve ±1 ATR hedefi
> tabanlardan iyi tahmin edilmedi**; eşleşmeler rastgele seçilmiş komşu kadar isabetli, büyüklükte saatin tipik hareketi
> daha iyi. Kaldırma kuralları sonucu değiştirmiyor. Bu belgenin tahmin katmanı (§8–§11) bu bulguya göre yeniden ele alınmalı.
> ⚠️ **ME-03 (2026-10-13, `RAPOR_BAGLAM_TESTI.md`):** VIX rejimi, stres, CAPREV hücresi, saat, oynaklık rejimi ve
> diğer sembollerle aynı anda eşleştirme de yönü tabanın üstüne çıkarmadı; büyüklükte hiçbiri saatin tipik hareketini geçmedi.

---

## 0. Özet

### 0.1 Tek sayfada

**İstek.** Bir tuşa basılınca sembolün son kapanmış mumları farklı zaman dilimlerinde, geçmiş 5 yıllık veride (yoksa en
eskiye kadar) her mum küçük bir payla (örn. %0,01–0,02) taransın; benzer geçmiş durumlardan sonra fiyatın hangi yöne,
ne kadar ve ne kadar sürede gittiği ekrana basılsın. Mum sayısı her sembol için araştırmayla seçilsin. Veri yerelde olsun.

**Tasarımı belirleyen olgular.**
1. **Birebir mum-mum eşleşmede örnek hızla tükenir.** Tarihsel karar anında erişilebilir bağımsız olay sayısıyla
   (`fizibilite_4`): 0,2 ATR payında medyan sorgu 5m–1h'te **2 mum**, 4h/1d'de çoğunlukla **1 mum** taşır; sorguların üst
   çeyreğinde 2–3'e, 0,3 ATR'de 3–4'e çıkar. Kullanıcı payı %0,01–0,02'de medyan sorgu 0–2 mum. Kaba beklenti N·p₁^X (bağımsızlık
   benzeri varsayım) bu ölçümle uyumlu. Yani uzun birebir dizi *yasak* değil, **çoğu sorguda yeterli örnek bulunmuyor** —
   İkiz modunda kullanıcı daha uzun X isteyebilir, sonuç ve örnek sayısı dürüstçe gösterilir.
2. **Sabit % pay semboller/TF'ler arasında farklı katılık demektir** (tek mum eşleşme olasılığı OIL 1h %0,01, NDX 5m
   %6,2). ATR-birimli pay bunu eşitler → içeride ATR, ekranda istenen % ile uygulanan pay birlikte.
3. **Uzun ufuklarda kapasite sınırı:** 1d'de 5 yılda ~1.290 mum var; 33 mumluk bağlam + 20 bar ufukla çakışmasız olay
   en fazla ~24 → K=150 gibi sabit komşu sayısı imkânsız. **K ufuk başına kapasiteyle sınırlanır**, yetersizse çekimser.
4. **Önceki kanıt yön için olumsuz** (PM, OLD-13, IO-18, MK) → yön varsayılan "bilgi amaçlı". **Büyüklük ve hedefe
   ulaşma** (kaç pips, ne sürede) hiç ölçülmedi → ayrı hedefler.
5. **Uzun bağlam temsili açık soru:** log-zaman piramidi komşuları mesafe bakımından ham 30 mumdan iyi ayırıyor (göreli
   kontrast 2,3–2,6 vs 1,5) ama bu **tahmin kanıtı değildir**. Ham 7 mum / piramit / piramit + yol özeti, sonuç
   tahminiyle yarıştırılır; ana motor seçimi araştırmaya bırakılır.

**Yapı.** Doğrulanmış broker kütüphanesi (kaynak, saat, mum sınırı, kapsam metadata'sı) → canlı ve araştırmada **aynı
`eligible(t)`** → temsil (İkiz, ham-7, piramit, piramit+yol, Hibrit) → **mutlak mesafe kabul sınırı + kapasite** (iyi
eşleşme yoksa çekimser) → hedefler: ham yön, anlamlı hareket, **hedefe ilk ulaşma (+T, −S'den önce, H içinde)**, büyüklük
kantilleri, **hedef–süre tablosu** → belirsizlik (ham K, Kish etkinliği, bağımsız olay, gün/hafta; ufka bağlı blok
bootstrap; nokta-bazlı koni) → dürüstlük katmanı (hedef başına ayrı durum: doğrulanmamış / iç testte geçti / ileri
gölgede kesinleşti) → panel → tekilleştirilmiş gölge kaydı + otomatik sorgu takvimi.

### 0.2 v0.1 → v0.2 değişiklikleri (Codex incelemesine yanıt)

| İnceleme | Karar | v0.2'de |
|---|---|---|
| 2.1 Sayım sorgu sonrasını da içeriyor | **Kabul** — yeniden ölçüldü | `fizibilite_4`: aday ancak j + H ≤ t ise; arşiv sayımı ayrıca. X_max değişmedi, olay sayıları düştü (§3) |
| 2.2 ATR betikler/tasarım arasında farklı | **Kabul** | Tek özellik sözleşmesi (§6.1): pencere-sonu ATR = TR'nin e−14…e−1 basit ortalaması; v0.2 sayıları bununla |
| 2.3 X formülü/RC fazla kesin | **Kabul** | "Fiziksel olarak mümkün değil" yerine "çoğu sorguda yeterli örnek yok"; üst-çeyrek X de raporlanıyor; RC yalnız ayrışma tanısı; İkiz'de uzun X serbest |
| 2.4 Temizlik sayıma dahil değil; NDX karışık kaynak | **Kabul** | Satır metadata'sı; kaynağı belirsiz satır doğrulanmış profile girmez; planlı ara ≠ eksik veri; üst-TF kapsam şartı; OIL devri takvimle (§5) |
| 2.5 Saat dönüşümü koşulsuz olamaz | **Kabul, bir notla** | Ham zaman + uygulanan dönüşüm saklanır, kaynak/dönem başına bir kez. Not: MT5 belgesi "UTC" dese de bu projede kutuda ölçülen sapma +180 dk idi (E2/E3, `yeni deneme/data_recorder.py:74`) — belgeye de varsayıma da güvenilmez, ölçülür. Birincil test bağımsız UTC beslemesiyle gecikme korelasyonu; oynaklık tepesi yardımcı (§5.3). Seans takvimleri sembole özel (§5.4) |
| 2.6 Araştırma/ürün politikası farklı | **Kabul** | Tek `eligible(t)`: kayan 5 yıl alt sınır, sonuç t'de kapanmış, ek embargo yok; 10 yıl ayrı profil; tüm t-bağımlı istatistikler ≤ t verisinden (§7.1) |
| 3.1 Piramide yol özeti | **Kabul** | P33Y adayı tanımlandı, ön-kayıtta donduruluyor (§6.3) |
| 3.2 Zorla K | **Kabul** | Mutlak kabul sınırı d_acc + asgari bağımsız olay + çekimserlik; mod değişimi açık; istenen/uygulanan pay ayrı (§7) |
| 3.3 Yön / anlamlı hareket / hedef ayrı | **Kabul** | Y1–Y5 hedefleri, dört durumlu yarış, belirsize 0,5 yok, MFE yorum düzeltmesi, hedef–süre tablosu (§8) |
| 3.4 n_eff ≠ bağımsız olay; 1d kapasitesi | **Kabul** — ölçüldü | Dört ayrı sayı; katı ve yoğun kohort; blok uzunluğu ufka bağlı; kapasite tablosu (§3.3, §9) |
| 3.5 Koni nokta-bazlı; konformal varsayımları | **Kabul** | "Her adımın tarihsel aralığı" etiketi; kronolojik, sonucu tamamlanmış kalibrasyon; gün garantisi iddiası yok (§9.4) |
| 4 Sembol sayıları sabitlenmesin; EIA takvimi | **Kabul** | Profil = sembol × TF × ufuk × hedef; bağlamlar "aday" statüsünde; EIA resmî takvimi; IO-18'in C'ye düşüşü işlendi (§12) |
| 5 Protokol eklemeleri | **Kabul + bir öneri** | `PROTOCOL_TASLAK.md`: geliştirme/kalibrasyon/iç test/**kilitli ileri gölge**, önceki bakış kaydı, tam seçim ailesi. Null için öneri: **takvim-hafta kaydırması** (seans/haftagünü hizasını korur) (§11) |
| 6 Ürün sözleşmesi | **Kabul, bir notla** | Referans fiyat, takvim, mesafe katkısı, mesafe yüzdeliği, sürümleme, tekil kayıt, POST/GET. DataHub notu: canlı artım `mt5_recorder_feed`'in broker okuma yoluyla (yeniden yazılmaz); çok yıllık arşiv DataHub'da olmadığı için parquet arşivi kalır (§4, §5.5) |
| 6 Bellek tahmini | **Kabul** | 350 bin × 21 float32 ≈ 29 MB; 48 adımlı yol ≈ 67 MB; p50/p95 ölçülecek (§5.6) |

---

## 1. Problem tanımı

| Öğe | Tanım |
|---|---|
| Sembol | NDX (MT5 `NAS100`), DAX (`GER40`), XAUUSD, USOIL (`SpotCrude`) |
| TF | 5m · 15m · 30m · 1h · 4h · 1d (1m opsiyonel) |
| Karar anı t | Sorgunun son **kapanmış** mumunun bitişi (tuşa basma anı değil; aradaki süre gösterilir) |
| Referans fiyat | C_t (son kapanmış mumun kapanışı). Güncel tick ve C_t'ye farkı ayrıca gösterilir; dağılım "tuş anındaki fiyatın tahmini" diye sunulmaz |
| Kütüphane | Aynı doğrulanmış broker kaynağı, aynı TF; `eligible(t)` (§7.1) |
| Ufuk H | İşlem barı cinsinden (TF başına 3 ön-kayıtlı değer); duvar saati bitişi takvimden hesaplanıp gösterilir |
| Pips | NDX 1,0 · DAX 1,0 · XAU 0,1 · OIL 0,01 (`meta_analysis_engine`) |

**Çıktı (TF başına, hedef başına ayrı durumla):** ham yön olasılığı + taban + fark; anlamlı hareket (yukarı/yatay/aşağı);
hedef–süre tablosu (+T'ye H içinde dokunma ve −S'den önce dokunma; aşağı ayrı); net hareket, MFE, MAE, menzil kantilleri;
her adımın tarihsel aralığı (koni); örnek sayıları (ham K, Kish etkinliği, bağımsız olay, gün/hafta); eşleşme kalitesi;
**veya** gerekçeli çekimserlik ("yeterli benzer örnek yok", "eşleşmeler uzak", "veri doğrulanmadı", "kapasite yok").

---

## 2. Önceki kanıt (3. KURAL)

| ID | Ne denendi | Sonuç | Etkisi |
|---|---|---|---|
| PM | NAS100 mum dizisi atlası (3–100 mum, mum-mum %0,005–0,20, 4 TF) | gerçek/plasebo medyan 1,0; tekrar sonrası yön taban ±2 puan | Her sayı plaseboyla |
| PM-2 | Aynı modeller ATR TP/SL işlemi | sınama −0,062R; "en iyi 20" plasebo sınırında, "en iyi 50" geçmiyor | Seçim yükü (E23/E24) |
| OLD-13 | CORTEX analog-kNN | yön yok | kNN tek başına yön vermez |
| OLD-14 | Denetimli ML + çoklu-TF çakışma | gerçek ama rejime bağlı | Bilgi rejimle kesişince çıkıyor |
| IO-18 → IO-20 | Benzer-işlem kNN; kovalama bulgusu | sonuç tekrarlamıyor (AUC 0,46–0,50); kovalama bulgusu sağlamlıkta **C'ye düştü** | `trend` bağlamı yalnız aday |
| MK-01..05 | Klasik mum formasyonları | elendi; XAU "yeni tepe BUY" gölgede (B−) | Mekanizma şekilden güçlü |
| OLD-15, GF-01 | Kısa ufuk yön; tek-özellik kapıları | taban / plasebo düzeyi | Meta-ders 1 |

Yeniden açma gerekçesi (defter §0.1): sorgu-merkezli koşullu tahmin (yeni tanım), büyüklük ve hedefe ulaşma (yeni hedef),
DAX/XAU/OIL ve 5–10 yıllık üst TF'ler (yeni veri), ATR-ortak ölçek + piramit/yol özeti (yeni temsil).
**Önceki bakış kaydı:** bu çalışmaların çoğu iç test dönemine düşen veriye zaten baktı → iç test "görülmemiş kasa" değildir;
bağlayıcı kanıt kilitli ileri gölge dönemidir (`PROTOCOL_TASLAK.md` §13).
**Yazılı ön-beklenti:** yön becerisi ≈ 0; büyüklükte "ATR + seans" tabanına karşı küçük pozitif olası; hedefe ulaşmada ≈ 0 – küçük.

---

## 3. Fizibilite ölçümü (sonuçlara bakılmadan)

### 3.1 Ne ölçüldü (v0.2 tanımı)

`fizibilite_4_nedensel.py`: her sembol × TF için son 1 yıldan 150 rastgele sorgu anı t. Aday pencere sonu j yalnız
**j + H_ref ≤ t** ise sayılır (sonucu t'de kapanmış; H_ref = TF'nin orta ufku). Mumlar **pencere-sonu ATR'siyle** ortak
ölçeklenir. Seçilen olaylar arası ≥ max(X, H_ref) bar (bağımsız olay). Ayrıca "arşiv" sayımı (her iki yön) ve uygunluk
kuralı (pay ≤ sorgu mumlarının medyan aralığı / 3) raporlanır. 4h/1d, 1h'ten broker gün sınırıyla (NY 17:00) türetildi.
v0.1 sayıları (`fizibilite_1–3`) mum-başına ATR ve nedensel olmayan aday havuzu kullanıyordu; tarihsel kayıt için klasörde
duruyor, tasarım kararları artık v0.2 sayılarına dayanıyor. Bilinen sınır: temizlik (segment/eksik veri/kaynak bayrağı)
henüz bu sayıma dahil değil — Faz 0 sonrası aynı betik temiz kütüphaneyle yeniden koşulacak.

### 3.2 Erişilebilir en uzun birebir dizi

Hücre = **medyan sorgu / üst çeyrek sorgu** için ≥ 30 bağımsız olay veren en uzun X. Son iki sütun 0,2 ATR'de X = 2 ve
X = 3 için sorgu başına medyan bağımsız olay sayısı.

| Sembol | TF | %0,01 | %0,02 | 0,1 ATR | 0,2 ATR | 0,3 ATR | X=2 olay | X=3 olay |
|---|---|---|---|---|---|---|---|---|
| NDX | 5m | 1 / 2 | 2 / 4 | 1 / 1 | 2 / 3 | 3 / 4 | 150 | 6 |
| NDX | 15m | 1 / 1 | 1 / 2 | 1 / 1 | 2 / 2 | 3 / 4 | 151 | 5 |
| NDX | 30m | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 3 / 4 | 137 | 6 |
| NDX | 1h | 0 / 1 | 1 / 1 | 1 / 1 | 2 / 3 | 3 / 4 | 74 | 4 |
| DAX | 15m | 1 / 1 | 1 / 2 | 1 / 1 | 2 / 3 | 3 / 4 | 171 | 7 |
| DAX | 30m | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 3 / 4 | 102 | 5 |
| DAX | 1h | 0 / 0 | 1 / 1 | 1 / 1 | 2 / 2 | 2 / 3 | 32 | 2 |
| XAU | 5m | 1 / 1 | 1 / 2 | 1 / 1 | 2 / 2 | 3 / 4 | 106 | 4 |
| XAU | 15m | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 3 | 3 / 4 | 117 | 4 |
| XAU | 30m | 0 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 3 / 4 | 147 | 5 |
| XAU | 1h | 0 / 0 | 0 / 1 | 1 / 1 | 2 / 2 | 2 / 3 | 51 | 1 |
| OIL | 5m | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 3 / 3 | 80 | 2 |
| OIL | 15m | 0 / 1 | 1 / 1 | 1 / 1 | 2 / 2 | 3 / 4 | 96 | 5 |
| OIL | 30m | 0 / 0 | 0 / 1 | 1 / 1 | 2 / 2 | 3 / 3 | 68 | 2 |
| OIL | 1h | 0 / 0 | 0 / 0 | 1 / 1 | 2 / 2 | 2 / 4 | 35 | 1 |

| Sembol | TF (kütüphane: 5 y · 10 y) | 0,1 ATR | 0,2 ATR | 0,3 ATR | X=2 olay (0,2 ATR) |
|---|---|---|---|---|---|
| NDX | 4h | 1/1 · 1/1 | 1/2 · 2/2 | 2/2 · 2/3 | 14 · 43 |
| NDX | 1d | 0/0 · 0/1 | 1/1 · 1/1 | 1/2 · 2/2 | 3 · 5 |
| DAX | 4h (tam ≈ 6,8 y) | 1/1 · 1/1 | 1/2 · 1/2 | 2/2 · 2/3 | 9 · 12 |
| DAX | 1d (tam ≈ 6,8 y) | 0/0 · 0/0 | 1/1 · 1/1 | 1/2 · 2/2 | 3 · 5 |
| XAU | 4h | 1/1 · 1/1 | 1/2 · 1/2 | 2/2 · 2/3 | 15 · 23 |
| XAU | 1d | 0/0 · 0/1 | 1/1 · 1/1 | 1/2 · 2/2 | 3 · 7 |
| OIL | 4h | 1/1 · 1/1 | 1/2 · 1/2 | 2/3 · 2/3 | 16 · 22 |
| OIL | 1d | 0/0 · 0/1 | 1/1 · 1/1 | 1/2 · 2/2 | 4 · 9 |

Okuma notları:
- Nedensel düzeltme X_max'ı değiştirmedi; olay sayılarını düşürdü (5m'de kütüphane sorgu anına göre yalnız 3–20 ay).
- Uygunluk kuralını geçen sorgularla NDX/DAX/OIL 1h ve tüm 4h/1d'de 0,2 ATR X_max 1'e iner; uzun eşleşmeleri büyük
  ölçüde küçük mumlu (sessiz) sorgular üretiyor.
- 0,3 ATR'de 3–4 mum mümkün görünse de pay o noktada tipik mumun büyük kısmıdır; "birebir" iddiası zayıflar.
- Ham sonuçlar: `results/fizibilite_4_nedensel.csv`, özet `results/ozet_v2.csv`.

### 3.3 Kapasite: bağımsız olay tavanı

Kütüphanenin tamamında, özellik + sonuç pencereleri çakışmayan olayların üst sınırı ≈ N / (kapsam + H):

| TF | N (5 y) | ham-7, orta H | P33: kısa / orta / uzun H | N (10 y) | P33, uzun H (10 y) |
|---|---|---|---|---|---|
| 1h | ~29.600 | ~1.950 (H=8) | 800 / 720 / 520 | ~59.000 | ~1.040 |
| 4h | ~7.700 | ~590 (H=6) | 210 / 200 / 120 | ~15.300 | ~240 |
| 1d | ~1.290 | ~110 (H=5) | 37 / 34 / **24** | ~2.580 | **~49** |

Tek bir sorgunun kabul edilen komşuları bu tavanın küçük bir alt kümesidir. Sonuç: 1d'de uzun bağlam + uzun ufuk
neredeyse kapasitesiz; 4h'te K ≤ ~50; 4h/1d için 10 yıl zorunlu aday. Kapasite her profil ve ufuk için otomatik
hesaplanır; K bunu aşamaz.

### 3.4 Uzun bağlam: mesafe ayrışması (tahmin kanıtı DEĞİL)

v0.1 ölçümü (`fizibilite_3`): göreli kontrast RC = medyan mesafe ÷ 30. komşu mesafesi. Ham 30 mum 1,47–1,64; piramit-33
2,31–2,60; ham 7 mum 2,19–2,51. Bu yalnız "komşular rastgele pencerelerden ne kadar ayrışıyor" tanısıdır; yüksek RC daha
iyi tahmin demek değildir, düşük RC de rastgele sonuç demek değildir. Piramidin değeri yalnız sonuç tahmininde ham-7'ye
karşı ölçülür (H4, `PROTOCOL_TASLAK.md`).

### 3.5 Tasarım kararlarına çevirisi

1. İkiz (kullanıcı tanımı) korunur; araştırma profilinde X = 1–3, kullanıcı modunda serbest X + dürüst sayı.
2. Pay içeride ATR, ekranda istenen % + uygulanan pay.
3. Uzun bağlam temsili (ham-7 / P33 / P33Y) sonuç sınamasıyla seçilir.
4. K ufuk başına kapasiteyle sınırlı; 4h/1d'de 10 yıl adayı; yetersizse çekimser.

---

## 4. Mimari

```
┌──────────────────────────── ÇEVRİMDIŞI ─────────────────────────────┐
│ Derin arşiv: research parquet'leri + MT5 export (+ Dukascopy, ayrı src) │
│      ▼                                                                  │
│ [§5] Kütüphane kurucu → data/candle_match/<SYM>/<tf>.parquet           │
│      (ham_ts, ts_utc, dönüşüm, src, seg, flags) + eğitim manifesti      │
│      ▼                                                                  │
│ [§6, §8] Özellik + hedef ön-hesabı (ortak sözleşme, nedensel)           │
│      ▼                                                                  │
│ [§11] PROTOCOL → geliştirme → kalibrasyon → iç test → profiles.json     │
└─────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────── ÇEVRİMİÇİ ──────────────────────────────┐
│ Kutu data_recorder → indicator_snapshots ─► mt5_recorder_feed okuma yolu │
│      (4 sembole açılır) ─► kütüphaneye artımlı ekleme + boşluk denetimi │
│      (boşluk varsa MT5'ten geri doldurma talebi)                        │
│ POST /api/candle-match/{sym}/compute  (hesapla + tekil kaydet)          │
│ GET  /api/candle-match/{sym}           (hazır sonucu oku)               │
│   → eligible(t) → temsil → kabul sınırı + kapasite → hedefler           │
│   → belirsizlik → durum/rozet → panel                                   │
│ Otomatik sorgu takvimi (ileri gölge) → aynı yol → notlayıcı             │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Sadakat:** araştırma ve canlı servis aynı çekirdeği (`backend/services/candle_match/`) çağırır; `eligible(t)`, taban,
  ölçekleyici, kabul sınırı, nadirlik ve kalibrasyon dahil tüm çıktılar için canlı ↔ tarihsel eşitlik testi (§17).
- **DataHub ile ilişki:** DataHub çok yıllık arşiv tutmuyor ve hibrit modda Yahoo'ya düşebiliyor (E21). Bu yüzden sorgu
  DataHub'ın birleşik mumundan değil, kaynak etiketi doğrulanmış broker barlarından kurulur. Yeni okuyucu yazılmaz:
  `mt5_recorder_feed`'in `indicator_snapshots` okuma ve tazelik mantığı (bugün varsayılan yalnız USOIL) dört sembole
  açılır. Kaydedici poll başına sınırlı bar çektiği için (`copy_rates_from_pos(…, 1, count)`) tablo "tam veri" garantisi
  değildir → boşluk denetimi zorunlu.

---

## 5. Veri katmanı

### 5.1 Yerel envanter (2026-10-12, yıllık bar sayısıyla doğrulandı)

| Sembol | 1m | 5m | 15m | 30m | 1h | Not |
|---|---|---|---|---|---|---|
| NDX | 2025-01→2026-10 (Dukascopy 2025 + Pepperstone 2026) | 1m'den, 21 ay | 2023-10→2026-10 | 2021-06→2026-07 | 2016-05→2026-07 (10 y) | 30m/1h bugüne uzatılmalı; 2025 kısmı ayrı `src` |
| DAX | yok | yok | 2022-11→2026-10 | 2021-03→2026-10 | 2020-01→2026-10 | 1h 2020 öncesi seyrek → dışarıda |
| XAU | yok | 2025-06→2026-09 | 2023-03→2026-09 | 2021-07→2026-09 | 2016-05→2026-09 (10 y) | 09-03+ Yahoo GC=F → broker'dan doldur |
| OIL | yok | 2025-06→2026-09 | 2023-03→2026-09 | 2021-07→2026-09 | 2016-05→2026-09 (10 y) | aynı + vade devri |

### 5.2 Satır metadata'sı ve kabul

Her satır: `ham_ts`, `ts_utc`, `donusum` (ör. "−180 dk, ölçüm 2026-07-28"), `src` (broker / dukascopy / bilinmiyor),
`enstruman` (CFD spot / vadeli tabanlı CFD), `seg`, `flags` (`planned_break` · `missing` · `roll` · `partial_htf`).
- Kaynağı `bilinmiyor` veya pencere içinde karışık olan satırlar **doğrulanmış profile girmez**; yalnız duyarlılık analizi.
- Planlı ara (günlük ara, hafta sonu, tatil) ile beklenmeyen eksik veri ayrı işaretlenir; **beklenmeyen her boşluk** (4 günden
  kısa olanlar dahil) pencereyi ve ufku geçersiz kılar.
- Üst-TF mum yalnız beklenen alt-bar kapsamı tamsa kullanılır (`partial_htf` aksi hâlde).
- Fiyat hatası denetimi: H ≥ max(O, C), L ≤ min(O, C), fiyat > 0; tek-bar sıçrama > 10 ATR → inceleme listesi.
- OIL devri: kontrat/devir takvimi metadata'sıyla işaretlenir; takvim yoksa > 3 ATR açılış boşluğu yalnız inceleme
  listesine girer (haber sıçramasından ayırmak için), otomatik devir sayılmaz.

### 5.3 Saat ekseni politikası

- Ham zaman ve uygulanan dönüşüm saklanır; dönüşüm **kaynak/dönem başına bir kez** belirlenir ve uygulanır. Daha önce
  düzeltilmiş UTC veriye tekrar uygulanamaz (dönüşüm kaydı bunu engeller).
- Birincil test: bağımsız UTC beslemesiyle (ör. Dukascopy / Yahoo saatlik) getiri gecikme korelasyonu tepe gecikmesi 0.
  Yardımcı: seans oynaklık tepesi (NY nakit açılışı 09:30 ET; Xetra 09:00 Berlin — UTC karşılıkları DST'ye göre değişir).
- Broker D1/H4 sınırının NY 17:00 ile ilişkisi broker verisinden doğrulanır (D1 mumlarının açılış saatleri).

### 5.4 Seans takvimleri

`session_context_service` NY merkezlidir (London/Berlin saat dilimlerini tanır ama seansı NY'ye göre sınıflandırır).
Yeni `symbol_sessions` modülü: borsa yerel saatinde tanımlı kovalar (zoneinfo), sembolün tatil/yarım gün takvimi, ABD ve
Avrupa DST'sinin ayrık haftaları. OIL için **EIA resmî yayın takvimi** (tatil kaymaları dahil; geçmiş araştırmada her
yılın o tarihte bilinen takvimi); "Çarşamba" sabiti kullanılmaz.

### 5.5 Depolama, güncelleme, sürümleme

- Arşiv: `data/candle_match/<SYM>/<tf>.parquet` (git dışı). Eğitim manifesti (sabit, profille eşleşir) ile canlı
  kütüphane revizyonu ayrı tutulur.
- Artımlı güncelleme `mt5_recorder_feed` yoluyla; boşlukta kutuda MT5'ten geri doldurma (`copy_rates_from_pos`, ~100 bin
  bar tavanı); geçmiş an kurgusunda `backend/research/_bars_upto.py` (E1).
- Normal artımlı ekleme profil durumunu düşürmez; eski satır düzeltmesi, kaynak veya dönüşüm değişikliği yeniden
  değerlendirme tetikler. Önbellek anahtarı = (sembol, TF, son kapanmış bar, profil sürümü, temsil sürümü, kalibrasyon
  sürümü, kütüphane revizyonu, parametreler).

### 5.6 Bellek ve gecikme

Özellik: 350 bin bar × 21 float32 ≈ 29 MB; 48 adımlı yol hedefi ≈ 67 MB; OHLC/metadata ve çok TF bunun üstünde. Bugünkü
veriyle (5m ~100 bin bar) çok daha az; 5 yıllık 5m/1m gelirse sembol başına yüzlerce MB olabilir. Hedef: arama < 10 ms,
toplama < 50 ms (TF başına); tekilleştirme, bootstrap ve plasebo dahil p50/p95 ölçülür; ağır tanılamalar ayrı aşamaya
alınabilir.

---

## 6. Temsil

### 6.1 Ortak özellik sözleşmesi

- **ATR:** A(e) = TR'nin e−14 … e−1 barları üzerinden **basit** ortalaması (Wilder değil); TR = max(H−L, |H−C₋₁|, |L−C₋₁|).
- **Mum vektörü:** pencere sonu e için penceredeki her mum i: (H_i−O_i, L_i−O_i, C_i−O_i) / A(e) — tüm mumlar aynı ölçekte;
  mumların birbirine oranı korunur.
- **Kullanıcı % modu:** mumun kendi açılışına göre %, ölçeksiz (yalnız İkiz-% görünümü).
- Tüm ölçekleyiciler (grup katsayıları, bağlam standart sapmaları) yalnız t'de bilinen veriden veya dondurulmuş geliştirme
  bölümünden.

### 6.2 İkiz ve Hibrit

- **İkiz T(X, τ):** ∀k < X, üç özelliğin hepsinde |fark| ≤ τ (L∞). Profil: X ∈ {1,2,3}, τ ∈ {0,15; 0,25}. Kullanıcı modu:
  serbest X ve %/ATR pay; uygunluk kuralı (τ ≤ sorgu medyan aralığı / 3) **uyarı** olarak gösterilir, pay sessizce
  daraltılmaz.
- **Hibrit:** T(2; 0,20) süzgeci → uzun bağlam temsiliyle sıralama. Süzgeç sonrası bağımsız olay yetersizse **çekimser**;
  saf bağlam moduna geçmek kullanıcıya açık mod değişimi olarak sunulur ve "son iki mum birebir" iddiası düşer.

### 6.3 Uzun bağlam adayları (sonuç sınamasıyla seçilir)

| Aday | Tanım | Boyut |
|---|---|---|
| R7 | ham son 7 mum, ortak ölçek | 21 |
| P33 | piramit [1,1,1,2,4,8,16]; seviye (u,d,b)/√s | 21 |
| P33Y | P33 + yol özeti: (C_{e−k} − C_e)/A(e), k ∈ {1,2,4,8,16,32} (6); birleşik seviyelerde tepe-önce-dip işareti (4); verimlilik \|C_e − C_{e−33}\| / Σ\|ΔC\| (1); yol grubu geliştirmede şekil grubuyla eşit toplam varyansa ölçeklenir | 32 |

Yeni özellik eklemek ayrı tarama değil, **tek ek temsil** olarak sınanır; kazanç yoksa basit olan seçilir.

### 6.4 Bağlam (yalnız ikincil analiz, "aday" statüsünde)

`vol_z`, `loc`, `trend` (IO-18 → IO-20'de C'ye düştüğü için zayıf gerekçe), seans kovası, kapanmış üst-TF mumu (E16),
NDX/DAX `vix_reg` (önceki günün tamamlanmış VIX'i, E20) ve `stres`. Bağlam açık her yapılandırma **"yalnız bağlam"**
tabanını ve küçük oynaklık/trend regresyonunu geçmek zorunda; geçemezse yarar şekle yazılmaz.

---

## 7. Eşleştirme

### 7.1 `eligible(t)` — canlı ve araştırma için tek fonksiyon

Aday j uygun ⇔ (1) ts(j) ≥ t − L (L = 5 yıl; 10 yıl ayrı profil), (2) j + H ≤ t, (3) özellik ve sonuç penceresi
`missing`/`roll` geçmiyor ve aynı `src` grubunda, (4) j'nin özellik penceresi sorgununkiyle çakışmıyor. Ek embargo yok.

### 7.2 Mesafe, kabul ve çekimserlik

1. Uygun adaylara mesafe (Öklid; İkiz/Hibrit'te L∞ süzgeç). BLAS ile kaba kuvvet; indeks gereksiz.
2. **Kabul sınırı:** D ≤ d_acc; d_acc = geliştirme kütüphanesindeki rastgele pencere çifti mesafelerinin %q yüzdeliği
   (q ∈ {%2, %5}, ön-kayıtlı). Sınırı aşan komşu tahmine girmez.
3. **Kapasite ve K:** K = min(K_profil, kapasite(H)); kabul edilen ve tekilleştirilmiş bağımsız olay < 20 → **çekimser**.
   Yüksek K ile "doldurma" yok.
4. Tekilleştirme iki kohortla: **katı** (özellik + sonuç aralıkları çakışmaz → bağımsız olay sayısı) ve **yoğun** (yalnız
   sonuç aralıkları çakışmaz → tahmin, blok belirsizlikle).
5. Çekimserlik türleri ayrı: "yeterli örnek yok", "eşleşmeler uzak (kabul sınırı)", "veri doğrulanmadı", "kapasite yok".

### 7.3 Eşleşmeyi açıklama

Her komşunun mesafe katkısı üç parçaya ayrılır: son mumlar / eski bağlam / (varsa) rejim. Ekranda "%81 benzerlik" yerine
**mesafe yüzdeliği** (rastgele çiftlere göre) ve kalite sınıfı (çok yakın / yakın / uzak) — olasılık ya da doğruluk değildir.

---

## 8. Hedefler (ATR birimi, referans C_t)

| ID | Tanım | Ekranda |
|---|---|---|
| Y1 ham yön | 1[C_{t+H} > C_t] | P(yukarı) + taban + fark |
| Y2 anlamlı hareket | r_H ≥ +b yukarı · ≤ −b aşağı · arası yatay; b = max(0,25·A_t, 2 × ölçülen medyan spread) | üç sınıf olasılık |
| Y3(T) hedefe ilk ulaşma | dört durum: +T önce · −T önce · H içinde hiçbiri · aynı barda ikisi (belirsiz; 1m varsa çözülür); T ∈ {0,5; 1; 1,5} | yukarı ve aşağı senaryo ayrı |
| Y4 büyüklük | net r_H, MFE_H, MAE_H, menzil kantilleri | dağılım |
| Y5 hedef–süre tablosu | T ∈ {0,5; 1; 1,5; 2} ATR × üç ufuk → P(+T'ye H içinde dokunma), P(+T, −T'den önce); aşağı ayrı; ulaşanlarda süre dağılımı | ana tablo |

- **Belirsiz durum 0,5 sayılmaz:** alt/üst sınır (belirsizlerin hepsi aleyhte / lehte) gösterilir. "Hiçbiri" paydadan çıkmaz.
- **MFE yorumu:** MFE'nin P75'i "%75 olasılıkla buraya gider" değildir; örneklerin ~%25'i bu değere ulaşır. Bu yüzden ana
  çıktı doğrudan **ulaşma oranı** (Y5).
- Ufuklar (bar): 5m {6, 12, 48} · 15m {4, 16, 32} · 30m {2, 8, 16} · 1h {4, 8, 24} · 4h {3, 6, 30} · 1d {1, 5, 20}; duvar
  saati bitişi seans/hafta sonu/tatil takviminden hesaplanır.
- İşlem/EV iddiası ayrı giriş sözleşmesi ister (sonraki M1 açılışı + gerçek spread, E7; 2. KURAL).

---

## 9. Birleştirme ve belirsizlik

### 9.1 Olasılık ve kantiller

Çekirdek ağırlık w = exp(−½(D/h)²), h = kabul edilen komşuların medyan mesafesi. Y1/Y2/Y3: ağırlıklı oran, seans-kovası
tabanına büzülme (m = 20). Y4: ağırlıklı kantiller. Taban oranları dönem × seans kovası, `eligible(t)` kümesinden
(E13, E15).

### 9.2 Örnek sayıları (dördü ayrı)

Ham K · Kish ağırlık etkinliği (Σw)²/Σw² · **bağımsız olay** (katı kohort) · farklı gün / hafta. "n_eff" adı bağımsızlık
iması taşıdığı için kullanılmaz.

### 9.3 Belirsizlik

Blok bootstrap; blok uzunluğu ≥ max(H bar, 1 işlem günü), ölçülen sonuç otokorelasyonuna göre uzatılır (1d / H = 20 → ≥ 4
hafta). Tabana karşı fark gösterilemiyorsa bu "örnek yetersiz" demek değildir — ayrı mesajlar.

### 9.4 Koni ve kalibrasyon

- Koni = **her adımın tarihsel aralığı** (nokta-bazlı P10–P90). Tüm yolun bu bantta kalma olasılığı %80 değildir; medyan
  çizgisi gerçekleşmiş bir yol değildir — ekranda yazılır. Eşzamanlı bant istenirse ayrıca sınanır.
- Aralık kalibrasyonu: kronolojik, yalnız sonucu tamamlanmış örneklerle (H gecikmeli güncelleme); uyarlamalı konformal
  yaklaşımlar (Gibbs–Candès 2021; Zaffran ve ark. 2022) aday. Ufuk/seans bazında kapsama ve genişlik raporu; belirli bir
  gün için garanti iddiası yok.

---

## 10. Dürüstlük katmanı ve durumlar

Hedef başına (Y1–Y5 ayrı) üç profil durumu:

| Durum | Anlamı | Ekranda |
|---|---|---|
| ⚪ Doğrulanmamış | iç test yapılmadı/geçilmedi veya manuel ayar | "tarihsel dağılım"; yön gri; AL/SAT dili yok |
| 🟡 İç testte geçti | `PROTOCOL` §12 iç test ölçütleri | "iç testte geçti, ileri doğrulama sürüyor" |
| 🟢 Kesinleşti | kilitli ileri gölgede ≥ 100 bağımsız tahminle teyit | renkli |

**Bugünkü sorgunun kalitesi** profil durumundan ayrı gösterilir (yakın örnek var mı, kaç bağımsız olay, kapasite).
Sorgu-başına plasebo p-değeri yalnız "tabana karşı fark gösterilebildi mi" sorusunun cevabıdır; çok TF'de sürekli
sorgulanan ham p-değerleri rozet üretmez. Hiçbir çıktı kapıya/bota/decider'a bağlanmaz (2. KURAL).

---

## 11. Araştırma protokolü (özet — ayrıntı `PROTOCOL_TASLAK.md`)

- **Hipotezler:** H1 büyüklük, H2 ham yön, H3 hedefe ulaşma — tek sabit yapılandırmayla (seçimsiz), 72 hücrede Holm;
  H4 temsil sıralaması (R7 / P33 / P33Y / İkiz / Hibrit); H5 sembole özel en iyi ayar (seçim düzeltmeli).
- **Bölümleme:** geliştirme (iç kronolojik katlar) → kalibrasyon → iç test (bir kez; önceki bakışlar nedeniyle "görülmemiş"
  sayılmaz) → **kilitli ileri gölge** (dondurmadan sonra ≥ 3 ay, otomatik sorgu takvimi; bağlayıcı kanıt).
- **Tabanlar:** seans-kovası oranları, "ATR + seans" büyüklük modeli, küçük oynaklık/trend regresyonu, R7, yalnız bağlam,
  seans + oynaklık eşli rastgele komşular.
- **Null:** takvim-hafta kaydırması (seans/haftagünü hizası ve otokorelasyon korunur, şekil→sonuç bağı kırılır) ile tüm
  seçim ailesinin yeniden yürütülmesi (maks-istatistik); büyüklükte oynaklık-eşli rastgele komşular; sentetik piyasa.
  Null'un neyi koruduğu rapora yazılır.
- **Seçim ailesi:** sembol, TF, ufuk, hedef, temsil, d_acc, K, 5/10 yıl, bağlam — tamamı sayılır (≈ 50 bin test mertebesi).
- **Pratik raporlama:** kapsam (çekimser olmayan oran), genişlik, kalibrasyon, yıl/seans dağılımı, en iyi 5 gün hariç;
  en iyi tek hücre yerine yakın ayarlarda kararlı ve basit profil.

---

## 12. Sembole özel özelleştirmeler

"NDX 33 mum, XAU 17 mum" gibi sayılar araştırmadan önce **sabitlenmez**. Profil = sembol × TF × ufuk × hedef; yön için
iyi derinlik büyüklük için iyi derinlikle aynı olmak zorunda değil. Arayüzde varsayılan tek ayar sunulabilir; hedefler
altta ayrı izlenir.

| Sembol | Aday bağlam | Özel kontroller |
|---|---|---|
| NDX | NY nakit açılışına göre zaman, oynaklık; VIX/stres ayrı varyant | R7 + yalnız bağlam tabanı; BUY/SELL ayrı rapor; aynı NDX geçmişinin tekrar kullanımı (E23) |
| DAX | Xetra ve NY açılışı ayrı kovalar; Avrupa/ABD DST farkı | NDX bağlamı aynen taşınmaz; yerel DAX seans tabanı; kısa TF geçmişi yetersiz (5m yok) |
| XAU | Asya/Londra/NY; trend ve aralık konumu | momentum/devam ↔ dönüş ayrımı; spot CFD ↔ vadeli (GC=F) ayrımı; makro veri yalnız yayın zamanından sonra |
| OIL | seans, aralık konumu, EIA yayın anı (resmî takvim), devir metadata | tatil kaynaklı EIA kaymaları; spot CFD ↔ vadeli (CL=F); haber boşluğu ↔ devir ayrımı |

Ortak: pip sabitleri (§1), spread (NDX 1,5 puan ölçülmüş; OIL 0,028; DAX/XAU Faz 0'da ölçülür), 4h/1d için 10 yıl adayı,
DAX 1h 2020 öncesi dışarıda.

---

## 13. Çalışma zamanı akışı

| Adım | İş |
|---|---|
| 1 | Kullanıcı **"Mum Eşleştir"**e basar → `POST …/compute` |
| 2 | Kütüphaneye son kapanmış broker barları eklenir; boşluk/kaynak denetimi |
| 3 | Profil + sürümler yüklenir; her TF için t, C_t, güncel tick, veri yaşı |
| 4 | `eligible(t)` → temsil → kabul sınırı + kapasite → (gerekirse) çekimserlik |
| 5 | Y1–Y5, örnek sayıları, belirsizlik, kalite, durum |
| 6 | Tekil kayıt: (sembol, TF, son kapanmış bar, profil, parametre) zaten varsa yeniden yazılmaz; her tıklama ayrı gölge olayı sayılmaz |
| 7 | `GET …` hazır sonucu döner (önbellek anahtarı §5.5) |
| 8 | Otomatik sorgu takvimi aynı yolu kullanır; notlayıcı H dolunca aynı kütüphaneden notlar |

Piyasa kapalıysa: son kapanmış mum ve sonraki açılış gösterilir; ufkun seans/hafta sonu geçişi açıkça yazılır ve tarihsel
benzer geçişlerle kıyaslanır.

---

## 14. API sözleşmesi (taslak)

| Uç nokta | Açıklama |
|---|---|
| `POST /api/candle-match/{symbol}/compute?tfs=…&mode=auto\|twin\|context&tol=auto\|<değer>` | Hesapla + tekil kaydet |
| `GET /api/candle-match/{symbol}?tfs=…` | Hazır sonucu oku |
| `GET /api/candle-match/{symbol}/neighbors?tf=…&limit=20` | Kabul edilen komşular + mesafe katkıları |
| `GET /api/candle-match/profiles` | Profil durumları + tahmin edilebilirlik haritası |

Yanıt iskeleti (**değerler örnektir**):

```json
{
  "symbol": "NDX.INDX",
  "versions": {"profile": "…", "representation": "…", "calibration": "…", "library_rev": "…"},
  "reference": {"t_utc": "2026-10-12T13:45:00Z", "t_mt5": "2026-10-12 16:45", "close_t": 30655.2,
                "tick": 30661.0, "tick_minus_close_pips": 5.8, "data_age_sec": 41},
  "timeframes": [{
    "tf": "15m",
    "mode": {"requested": "auto", "applied": "context:P33", "tolerance_requested": null, "tolerance_applied": null},
    "status": {"direction": "unverified", "move3": "unverified", "hit": "internal_pass", "magnitude": "internal_pass"},
    "query_quality": {"accepted": 64, "kish_eff": 51.2, "independent_events": 38, "days": 52, "weeks": 31,
                      "capacity": 720, "distance_pct": 3.1, "class": "yakın"},
    "abstain": null,
    "horizons": [{
      "h_bars": 16, "ends_utc": "2026-10-12T17:45:00Z",
      "direction": {"p_up": 0.54, "p0": 0.527, "lift_pp": 1.3, "ci80": [0.48, 0.60]},
      "move3": {"up": 0.31, "flat": 0.41, "down": 0.28, "band_pips": 10.3},
      "hit_table": [{"T_atr": 1.0, "T_pips": 41, "up_touch": 0.47, "up_first": 0.36, "down_first": 0.33,
                     "none": 0.29, "ambiguous": 0.02, "up_first_bounds": [0.36, 0.38]}],
      "magnitude_pips": {"net": [-88, -39, 6, 47, 96], "mfe": [12, 25, 52, 91, 140], "mae": [-150, -86, -47, -20, -8]},
      "time_to_hit_bars": {"T1_up_median": 7}
    }],
    "cone_pointwise": [{"step": 1, "p10": -18, "p50": 0, "p90": 19}],
    "neighbors_preview": [{"end_utc": "2024-03-18T13:45:00Z", "distance_pct": 0.6,
                          "contrib": {"recent": 0.55, "context": 0.45}, "net_pips_h16": 34}]
  }]
}
```

Çekimser yanıt örneği: `"abstain": {"reason": "capacity", "detail": "1d, H=20: kapasite 24 → 20 bağımsız olay şartı karşılanamadı"}`.

---

## 15. Panel (UI)

```
┌ Geçmiş Eşleşme Radarı — NDX ──────────────────────── [▶ Mum Eşleştir] [⚙] ┐
│ Referans: 13:45 kapanışı 30.655,2 · tick 30.661,0 (+5,8 p) · veri 41 sn önce │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────────────┤
│ 15m  bağlam │ 1h  ikiz    │ 4h          │ 1d          │                    │
│ ⚪ yön %54  │ ⚪ yön %49  │ çekimser:   │ çekimser:   │                    │
│ (taban %53) │ (taban %52) │ eşleşme uzak│ kapasite yok│                    │
│ 🟡 hedef    │             │             │             │                    │
│ 38 bağımsız olay · 52 gün · kalite: yakın                                     │
└─────────────┴─────────────┴─────────────┴─────────────┴────────────────────┘
Hedef–süre tablosu (15m):        4 bar     16 bar     32 bar
  +0,5 ATR (+21 p) önce            …         …          …
  +1,0 ATR (+41 p) önce            …        %36         …
  −1,0 ATR (−41 p) önce            …        %33         …
  hiçbiri / belirsiz               …      %29 / %2      …
[ Grafik: canlı mumlar + "her adımın tarihsel aralığı" konisi + soluk komşu yolları ]
[ Eşleşmeler: tarih · mesafe yüzdeliği · son mum/bağlam katkısı · sonrası ▸ yan yana grafik ]
```

- Konum: Neural sembol sayfası, Kırılım Radarı'nın yanında. Servis katmanı `frontend/lib/api/candleMatch.ts`; bileşen
  `frontend/components/neural/CandleMatchPanel.tsx`; koni `SharedChart` (lightweight-charts 4.2.1) gelecek zaman damgalı
  serilerle.
- Mod etiketi her kartta (ikiz / bağlam / hibrit); mod değişimi açıkça yazılır. Kullanıcı payında **istenen** ve
  **uygulanan** pay ayrı, uygunluk uyarısı görünür.
- Durumlar: yükleniyor, hata, boş, bayat veri, dört tür çekimserlik (§7.2).

---

## 16. Kod yerleşimi (öneri)

```
backend/services/candle_match/
    library.py        # arşiv + artımlı ekleme (mt5_recorder_feed okuma yolu), metadata, boşluk denetimi, sürümler
    eligibility.py    # eligible(t) — canlı ve araştırmanın tek kaynağı
    features.py       # ATR sözleşmesi, mum vektörü, R7/P33/P33Y, İkiz, bağlam
    targets.py        # Y1–Y5, dört durumlu yarış, yol
    engines.py        # mesafe, kabul sınırı, kapasite, kohortlar, çekimserlik
    aggregate.py      # ağırlık, büzülme, kantiller, sayılar, blok bootstrap, kalibrasyon
    profiles.py       # profil durumları + rozet mantığı
    service.py        # orkestrasyon, önbellek, tekil kayıt, otomatik takvim
backend/services/symbol_sessions.py               # sembole özel seans/tatil/EIA takvimleri
backend/routers/candle_match_router.py
backend/data/candle_match/profiles.json           # commit'lenir
data/candle_match/<SYM>/<tf>.parquet              # git dışı
research/mum_eslestirme_20261012/PROTOCOL_TASLAK.md (+ değerlendirme betikleri çekirdeği import eder)
frontend/lib/api/candleMatch.ts · frontend/components/neural/CandleMatchPanel.tsx
backend/tests/test_candle_match_*.py
```

---

## 17. Test ve doğrulama

- **Birim:** ATR sözleşmesi; ortak ölçek; piramit/yol özeti seviye sınırları; prefix testi (gelecek değişince geçmiş özellik
  değişmez); `eligible(t)` (sonuç kapanışı, çakışma, src, bayraklar); kabul sınırı ve kapasite; dört durumlu yarış ve
  belirsiz sınırları; pips dönüşümü; büzülme sınır durumları.
- **Saat ve takvim:** gecikme korelasyonu testi; broker D1/H4 sınırı; Xetra/NY açılışlarının DST haftaları; EIA takvimi.
- **Canlı ↔ tarihsel eşitlik:** 200 rastgele geçmiş anda canlı servis (kütüphane o ana kesilmiş) ile araştırma çıktısı
  **tüm alanlarda** (taban, ölçekleyici, kabul sınırı, nadirlik, kalibrasyon, Y1–Y5) birebir.
- **Sentetik null:** seans-blok bootstrap rastgele seride beceri ≈ 0.
- **Performans:** p50/p95 gecikme ve bellek, tüm tanılamalar dahil.

---

## 18. Yol haritası

| Faz | İçerik | Çıkış ölçütü |
|---|---|---|
| 0 — Veri | metadata'lı arşiv, dönüşüm kaydı, gecikme-korelasyon testi, NDX 30m/1h + XAU/OIL broker uzatması, DAX 2020 kesimi, OIL devir takvimi, `symbol_sessions`, `mt5_recorder_feed` dört sembol; `fizibilite_4` temiz kütüphaneyle yeniden | kabul testleri yeşil |
| 1 — Çekirdek | `eligibility/features/targets/engines/aggregate`; birim testleri | testler + elle doğrulanmış tek an |
| 2 — Protokol | `PROTOCOL_TASLAK` → kullanıcı kararları → dondurma (sha1 deftere) → geliştirme → kalibrasyon → iç test | rapor + `profiles.json` (olumsuz sonuç da) |
| 3 — Ürün | API (POST/GET), panel (varsayılan ⚪), tekil kayıt, otomatik sorgu takvimi, notlayıcı | uçtan uca + canlı↔tarihsel eşitlik %100 |
| 4 — İleri gölge | ≥ 3 ay kilitli dönem | hedef başına kesinleşme kararı |

---

## 19. Açık sorular

**Kullanıcı kararı**
1. Varsayılan mod: İkiz mi, bağlam (araştırmanın seçeceği temsil) mi? Araştırma öncesi geçici varsayılan önerisi: İkiz X = 2 +
   hedef–süre tablosu.
2. Pay: içeride ATR, ekranda istenen % + uygulanan — kabul mü?
3. Ufuklar sabit 3 değer mi, kullanıcı seçebilsin mi?
4. 4h/1d için 10 yıl kütüphane (kapasite için gerekli) kabul mü, yoksa "5 yıl" sabit mi?
5. 5 yıllık 5m/1m veri edinimi (Dukascopy) değer mi?

**Teknik (diğer ajanla)**
1. d_acc'yi rastgele-çift yüzdeliği yerine sorgu-yerel ölçütle (sorgunun kendi mesafe dağılımı) tanımlamak daha iyi mi?
2. Takvim-hafta kaydırması yetersizse hangi blok-permütasyon null'u seans + rejim yapısını birlikte korur?
3. Y5 hedef–süre tablosunun hücreleri için kalibrasyon: hücre başına mı, monotonluk kısıtlı ortak model mi?
4. Kısa TF'lerde (5m 15–21 ay) iddia seviyesini düşürmek yeterli mi, yoksa 5m araştırmadan tamamen mi çıkmalı?

---

## 20. Değiştirilemez kısıtlar

1. Koşan mum yok; üst-TF bağlamı yalnız kapanmış ve kapsamı tam bar (E16).
2. Tek doğrulanmış broker kaynağı; kaynağı belirsiz satır doğrulanmış profile girmez (E21).
3. Saat dönüşümü ölçülür, kaydedilir, bir kez uygulanır (E2–E5).
4. Canlı ve araştırma aynı `eligible(t)`; sonucu t'de kapanmamış komşu yok; geçmiş an kurgusunda `_bars_upto.py` (E1).
5. Taban dönem × seans kovası (E13, E15); çıplak isabet yok.
6. Dört ayrı örnek sayısı; ufka bağlı blok belirsizliği; kapasite aşılmaz (E6, E9).
7. Mutlak kabul sınırı; iyi eşleşme yoksa çekimser — zorla K yok.
8. Ön-kayıt dondurulmadan sonuç yok; iç test bir kez; bağlayıcı kanıt kilitli ileri gölge (E23).
9. Tam seçim ailesi + yapısı açıklanmış null ile maks-istatistik (E24).
10. Kapı/bot/decider bağlantısı yalnız 2. KURAL kartıyla; varsayılan ⚪.

---

## Ek A — Sözde kod

```python
def eligible(lib, t, H, L=YEARS_5, q_window=None):            # canlı ve araştırma AYNI
    m = (lib.ts >= lib.ts[t] - L) & (lib.end + H <= t)
    m &= ~lib.crosses_flag(H, flags=("missing", "roll")) & lib.same_src_group(t)
    if q_window is not None:
        m &= ~lib.overlaps(q_window)
    return m


def features_common(raw_hlc_minus_o, A, e, X):                 # ortak pencere-sonu ölçeği
    return raw_hlc_minus_o[e - X + 1:e + 1] / A[e]             # A[e] = mean(TR[e-14:e])


def search(lib, rep, t, cfg):
    m = eligible(lib, t, cfg.H, cfg.L, q_window=rep.window(t))
    d = rep.distance_to_all(t); d[~m] = inf
    if cfg.twin_filter:
        d[~twin_mask(lib, t, cfg.X_f, cfg.tau)] = inf
    acc = np.flatnonzero(d <= cfg.d_acc)                       # mutlak kabul sınırı
    dense = dedup(acc, by=d, gap=cfg.H)                         # yoğun kohort (tahmin)
    strict = dedup(acc, by=d, gap=rep.coverage + cfg.H)        # katı kohort (bağımsız olay)
    K = min(cfg.K, capacity(lib, m, rep.coverage, cfg.H))
    if len(strict) < cfg.min_events:
        return Abstain(reason="too_few" if len(acc) else "too_far")
    return dense[:K], strict


def hit_race(path_hi, path_lo, T, H, resolve_1m=None):          # dört durum
    up = first_index(path_hi[:H] >= T); dn = first_index(path_lo[:H] <= -T)
    if up is None and dn is None:
        return "none"
    if up == dn:
        return resolve_1m(up) if resolve_1m else "ambiguous"
    return "up_first" if (dn is None or (up is not None and up < dn)) else "down_first"
```

## Ek B — Yeniden üretme

```bash
python3 research/mum_eslestirme_20261012/fizibilite_4_nedensel.py   # ~10 dk → results/fizibilite_4_nedensel.csv
python3 research/mum_eslestirme_20261012/ozet_v2.py                 # → results/ozet_v2.csv (§3.2 tabloları)
# v0.1 tarihsel ölçümleri: fizibilite_1_birebir.py, fizibilite_2_huni_kismi_knn.py, fizibilite_3_piramit.py, ozet.py
```

## Ek C — Sözlük

| Terim | Anlam |
|---|---|
| ATR (bu belgede) | TR'nin önceki 14 bar basit ortalaması |
| İkiz | Son X mumu birebir pay içinde eşleşen geçmiş pencere |
| R7 / P33 / P33Y | Ham 7 mum / log-zaman piramidi / piramit + yol özeti |
| `eligible(t)` | t anında kullanılabilir komşu kümesi (canlı ve araştırmada aynı) |
| d_acc | Mutlak mesafe kabul sınırı |
| Kapasite | Kütüphanede özellik + sonuç pencereleri çakışmayan olayların üst sınırı |
| Katı / yoğun kohort | Bağımsız olay sayımı / tahmin için kullanılan komşu kümeleri |
| Kish etkinliği | (Σw)² / Σw² — ağırlık yoğunlaşması; bağımsızlık ölçüsü değil |
| Hedef–süre tablosu | +T'ye (−S'den önce) H içinde ulaşma oranları |
| Takvim-hafta kaydırması | Sonuçları k hafta kaydırarak şekil→sonuç bağını kıran, seans hizasını koruyan null |
| İç test / ileri gölge | Bir kez açılan geçmiş dönem / dondurmadan sonra toplanan bağlayıcı dönem |
