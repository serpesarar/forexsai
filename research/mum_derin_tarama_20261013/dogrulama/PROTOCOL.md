# (f) "Kapanış baskısı dönüşü" ipucu — TEK SEFERLİK doğrulama ön-kaydı

Yazıldı: 2026-10-13 22:30 UTC, **sınama verisinde (NDX ≥ 2025-12-01, DAX, QQQ vekili) HİÇBİR şey hesaplanmadan önce.**
Klasör: `research/mum_derin_tarama_20261013/dogrulama/`. Canlı bot/backend/DB'ye dokunulmaz. Git commit yok.

## 0. Sınanan iddia ve kaynağı

Keşif (post-hoc, `capali/capali_ek.py` → `capali/results/ek_tanimsal.json` anahtar `F_1h`): NDX 1h 2016-05 → 2025-11,
n = 2.334 gece — son nakit saati AŞAĞI kapanınca gece (16:00 → ertesi 09:00 NY) yükseliş %60,75, ort. +13,61 puan;
YUKARI kapanınca %55,21, +0,50 puan; ortalama farkı için 5-günlük blok bootstrap P = 0,998, yükseliş oranı farkı için 0,999.
Etki 2021–2025'e yığılmış. Bu bir **ipucudur** (513 konfigürasyonluk aileden sonra, tanımsal ekte bulundu) → burada
tanım değiştirilmeden **bir kez** sınanır.

Önceden bilinen ve açıklanan temaslar (dürüstlük notu):
* Paralel çalışmalar (`research/nasdaq_derin_20261013/overnight`, `.../intraday_momentum`) aynı gün NDX 1h verisinin
  2026-06-30'a kadarını (yani bu holdout'un bir kısmını) **koşulsuz** gece getirisi (S2 CTO 16:00 → 09:30) ve son saat/yarım
  saat getirisini *hedef* olarak kullandı. Hiçbiri gece getirisini **son saatin işaretine koşullamadı**. Ben o çalışmaların
  sonuç dosyalarını okumadım ve okumayacağım (sınama bitene kadar).
* DAX'ta bu hipotez hiç sınanmadı. DAX verisi paralel çalışmalarda başka amaçlarla (CAPREV, MIM, gece sürüklenmesi) kullanıldı.
* Keşifte kullanılan `long_1h_utc.parquet`'te 2017-11-05 → 2018-02-26 arası etiket 60 dk geç (bkz.
  `nasdaq_derin_20261013/caprev_dax_recheck/results/axis_ndx_long_std.txt`); keşif sayıları bu kusurla üretildi.
  Holdout aylarında (2025-12 → 2026-07) aynı denetim kayma 0 diyor. Keşif etkisi (eşik kaynağı) **ham veriyle** hesaplanır
  (aynen yeniden üretim); düzeltilmiş sürüm yalnız bağlam olarak raporlanır.

## 1. Dondurulmuş tanım — NDX (koddan birebir; `capali_ek.py` satır "(f) tanımsal", tf = "1h")

* Takvim: `macro_daily_patched.csv`'de NDXCASH O/H/L/C dolu satırlar = NY işlem günleri (sıralı liste, indeks i).
* Erken kapanış günü (`early`): Şükran sonrası Cuma (Kasım, Cuma, gün 23–29, önceki takvim günü işlem günü değil),
  her 24 Aralık, her 3 Temmuz.
* Koşul günü i dahil ⇔ `¬early[i]` ∧ `¬early[i−1]` ∧ i > 0 ∧ i+1 < N (önceki-gün-erken dışlaması keşif kodunda MIM için
  vardı; birebir yeniden üretim için KORUNUR).
* `px(t)` = bitişi TAM t olan 1h barın kapanışı (bar başlangıcı UTC; yoksa NaN → gece düşer, doldurma yok).
  NY saati `zoneinfo America/New_York` (DST doğru).
* **Son saat** `rl = 100·(px(D 16:00)/px(D 15:00) − 1)` (15:00–16:00 NY barının kapanıştan kapanışa getirisi).
  **"Aşağı"** ⇔ `rl < 0`; **"Yukarı"** ⇔ `rl > 0`; `rl = 0` → gece düşer.
* **Gece** `on = px(D+1 09:00) − px(D 16:00)` (puan; D+1 = takvimdeki sonraki işlem günü; hafta sonu/tatil geceleri dahil;
  09:00 = 1h ızgarasında 09:30 açılışından önceki son saat sınırı). `on = 0` → düşer. Yüzde: `on% = 100·on/px(D 16:00)`.
* İstatistik: grup ortalaması (aşağı) − (yukarı); yükseliş oranı (`on > 0`) farkı.
* Bootstrap (keşifle aynı yöntem): blok = ⌊i/5⌋ (5 ardışık işlem günü), bloklar iadeli yeniden örneklenir (blok sayısı kadar),
  grup ortalamaları blok toplamlarının oranı; **B = 10.000** (keşifte 2.000; yöntem aynı, Monte Carlo hatası küçük),
  tohum 20261013. P = pay(fark > 0). Tek yönlü, yön keşifteki gibi (aşağı − yukarı > 0).

## 2. Sınama setleri (her biri BİR kez açılır; tek betik `dv_1_test.py`, tek koşum)

| Set | Veri | Koşul günleri | Rol |
|---|---|---|---|
| **N-H** holdout | `ndx_gate_forge/data/long_1h_utc.parquet`, ts ≥ 2025-12-01 | 2025-12-01 → 2026-07-13 (gece sonu ≤ 07-14) | birincil (bileşen) |
| **N-X** uzatma | `ndx_pattern_motifs/data/bars_15m.parquet` → 1h'e toplanmış | 2026-07-14 → takvim sonu (2026-09-30'un gecesi takvimde sonraki gün olmadığı için düşer) | birincil (bileşen) |
| **N-HX** birleşik | N-H ∪ N-X | | **NDX birincil karar seti** |
| **D-30** DAX | `dax_30m.parquet`, eksen düzeltilmiş (§4) | 2021-03-17 → veri sonu | **bağımsız piyasa birincil** |
| D-1h DAX vekili | `dax_1h.parquet`, eksen düzeltilmiş | 2020-01-01 → veri sonu | ikincil, etiketli vekil |
| Q-D QQQ günlük vekili | `macro_daily_patched.csv` QQQ O/H/L/C | 2015-01 → 2026-09, üç döneme bölünmüş | ikincil, etiketli vekil, karar YOK |

15m → 1h toplama: saat başı UTC kovası (NY saatleri tam saat ofsetli → NY saat sınırı); O = ilk, H = maks, L = min,
C = son 15m kapanışı; bar geçerli ⇔ kovanın son 15m barı (başlangıç :45) mevcut (böylece `px(t)` = t'deki gerçek fiyat).
N-X ayrıca tam aynı `px` tanımıyla kurulur.

**Hizalama denetimi (sınamadan önce, `dv_0_hazirlik.py`; getiri/hipotez istatistiği HESAPLAMAZ):**
1. 15m→1h toplamı vs `long_1h` bire bir OHLC: 2025-11-17 → 11-21 (holdout öncesi) ve 2026-07-06 → 07-10 (eklem haftası).
   Kabul: ≥ %95 barda |ΔH|, |ΔL|, |ΔC| ≤ 0,5 puan.
2. 2026-07-15 sonrası 15m (candle_cache kaynağı, `long_1h` ile örtüşmesi YOK): (a) bağımsız kaynak `bars_1m.parquet`
   (MT5 M1 / indicator_snapshots) 15m'e toplanıp kıyas, kabul ≥ %90 barda |ΔC| ≤ 2 puan ve en iyi kayma 0;
   (b) ay bazında 16:00 NY kapanışı vs NDXCASH_close farkının std'si kayma −60/0/+60 dk için — en küçük std kayma 0 olmalı;
   (c) her ay en geniş medyan aralıklı 15m dilim 09:30 NY.
3. `long_1h` holdout ayları için 2(b) aynısı.
Herhangi biri tutmazsa ilgili set **kullanılmaz** (gerekçe §8'e yazılır), sonuç "veri yok" olur — düzeltip yeniden denemek
sınamayı keşfe çevirir.

## 3. Karar ölçütleri (tek yönlü, yön: aşağı − yukarı > 0)

Keşif etkileri `dv_0_hazirlik.py` ile keşif verisinden (ham `long_1h`, ts < 2025-12-01) **aynı kodla** yeniden üretilir
(kod önce keşif sayılarını n = 2.334, %60,75 / %55,21, +13,61 / +0,50 birebir vermeli; vermezse durulur):
* E_pct = ort. on% farkı (yüzde puanı), E_up = yükseliş oranı farkı (puan), E_pts = 13,11 puan (yalnız rapor),
  d_E = E_pct / SD(on%, tüm keşif geceleri) (standartlaştırılmış etki, DAX eşiği için).

**Birincil ölçüt (her sette):** ortalama on% farkı.
* **GEÇER** ⇔ P(fark > 0) ≥ 0,95 **ve** fark ≥ 0,5 × E_pct (NDX) / fark ≥ 0,5 × d_E × SD(on%, o setin tüm geceleri) (DAX).
* **ÇÜRÜTÜLDÜ** (negatif) ⇔ GEÇMEZ ve bootstrap farkının %95'lik üst değeri < yarı-etki eşiği (veri keşif etkisinin
  yarısını bile dışlıyor).
* **SONUÇSUZ** ⇔ ikisi de değil (güç yetersiz). MDE₈₀ = (1,645 + 0,842) × SD_boot raporlanır.

**Eş-birincil (aynı kural):** yükseliş oranı farkı, eşik 0,5 × E_up (iki piyasada da puan cinsinden; birimsiz).
Puan cinsinden fark yalnız raporlanır (fiyat düzeyi 2016'da ~4.500, 2026'da ~25.000 → puan eşiği karşılaştırılamaz).

**Hipotez düzeyi verdikt:** "TEKRARLANDI" ⇔ N-HX **ve** D-30 birincil ölçütte GEÇER. "KISMİ" ⇔ yalnız biri GEÇER.
"TEKRARLANMADI" ⇔ hiçbiri geçmez ve en az biri ÇÜRÜTÜLDÜ. Aksi "SONUÇSUZ". Bileşenler (N-H, N-X), vekiller (D-1h, Q-D) ve
eş-birincil yalnız betimsel/destekleyici; verdikti yükseltemez.

**Zorunlu ek raporlar (her set):**
* Koşulsuz gece yükseliş oranı ve ortalaması (aynı geceler) vs aşağı-son-saat sonrası mutlak yükseliş oranı → "yalnız
  zamanlama bilgisi mi (iki koşullu oran da > %50), yoksa yönde işlenebilir bilgi mi (yukarı-son-saat sonrası < %50)?".
* Ortalama gece hareketi (puan) vs 1,5 puan spread; "yalnız aşağı-son-saat gecesi AL" vs "her gece AL" gecelik ortalama
  net puan (spread düşülmüş). Gecelik finansman (swap) ayrıca not edilir (hesaplanmaz; kaynak: `nasdaq_derin_20261013/overnight/PROTOCOL.md` §3).
* Gece sayısı, grup büyüklükleri, MDE₈₀.

## 4. DAX — mekanizma-eşdeğer tanım (sonuçlara bakmadan sabit)

* **Eksen düzeltmesi zorunlu:** `caprev_dax_recheck/fix_data.py` + `axis_dax.py` kanıtı — DAX dosyalarında NY standart
  saatindeyken etiket 60 dk ERKEN (broker saati NY+7 sabit −3 s ile çevrilmiş). Düzeltme: T = etiket + 60 dk, eğer
  NY(etiket + 60 dk) standart saatteyse; aksi T = etiket. `dv_0` doğrular: düzeltme sonrası her yıl × (iki-kış / iki-yaz /
  omuz) sınıfında en geniş medyan aralıklı 30m dilim 09:00 Berlin olmalı; 1h dosyası 30m toplamıyla eşleşmeli.
* **Brief'ten sapma (gerekçeli):** brief `dax_1h` 2020+ diyor, ama 1h barlar UTC saat başında başlar ve Berlin ofseti tam
  saattir → 16:30–17:30 Berlin 1h ızgarasında **kurulamaz**. Bu yüzden birincil DAX seti `dax_30m` (2021-03-17'den,
  verinin başı); 1h ikincil vekil olarak tutulur.
* Xetra günleri: Berlin Pzt–Cum, şu tatiller hariç: 1 Ocak, Kutsal Cuma, Paskalya Pazartesi, 1 Mayıs, 24/25/26/31 Aralık
  (Paskalya: anonim Gregoryen algoritma). Pfingstmontag ve 3 Ekim işlem günü sayılır. (Takvim kitaplığı yüklü değil, web
  araması bu oturumda kapalı → kural tabanlı; sınırlılık olarak yazılır.) Xetra'da yarım gün yok (24/31 Aralık zaten dışarıda).
* `px(t)` = bitişi TAM t (Berlin, `zoneinfo Europe/Berlin`) olan düzeltilmiş barın kapanışı.
* **D-30:** son saat `rl = px(D 17:30)/px(D 16:30) − 1` (16:30–17:00 ve 17:00–17:30 barları; 17:30 kapanış müzayedesi
  öncesi son fiyat). Gece `on = px(D+1 09:00) − px(D 17:30)`, D+1 = sonraki Xetra günü. `rl = 0` / `on = 0` düşer.
* **D-1h vekil:** 1h ızgarasında kapanışı İÇEREN saat 17:00–18:00 Berlin: `rl = px(D 18:00)/px(D 17:00) − 1`;
  gece `on = px(D+1 09:00) − px(D 18:00)`. 2020-01-01 → 2021-03-16 alt dönemi (30m'nin kapsamadığı) ayrıca raporlanır.
* Blok = Xetra takvim indeksi ⌊i/5⌋.
* Eşik: §3'teki standartlaştırılmış kural (DAX gece oynaklığı NDX'ten farklı).

## 5. Plasebo — kapanış olmayan saat

* NDX: `rp = px(D 12:00)/px(D 11:00) − 1` (bitişi 12:00 NY olan saat) işaretine göre **aynı gece** (16:00 → 09:00) getirisi;
  aynı geceler (§1 örneği) + `rp = 0` düşer. DAX: `px(12:00)/px(11:00)` Berlin → aynı gece (17:30 → 09:00; vekilde 18:00 → 09:00).
* Kapanışa özgüllük: aynı bootstrap çekilişlerinde P(fark_son-saat − fark_plasebo > 0). "Kapanışa özgü" ⇔ bu P ≥ 0,90
  **ve** plasebo kendisi §3 GEÇER ölçütünü geçmiyor.
* Plasebo keşif verisinde de (bağlam, eşik değil) `dv_0`'da hesaplanır.

## 6. QQQ günlük vekil (ikincil, karar yok)

Günlük veride son saat tanımlanamaz → açıkça etiketli vekil: kapanış konumu `CLV = (C − L)/(H − L)`; "aşağı kapanış vekili"
⇔ CLV < 0,5 (H = L → düşer). Gece % = 100·(O_{sonraki satır}/C − 1). Dışlama §1 ile aynı (`early`, önceki-gün-erken).
Dönemler: Q-pre 2015-01-02 → 2016-05-27 (keşif 1h'inden ÖNCE — zaman olarak bağımsız ama küçük), Q-ovl 2016-05-30 →
2025-11-28 (keşifle ÇAKIŞIK, bağımsız değil), Q-hold 2025-12-01 → 2026-09-29 (holdout dönemi; N-HX ile aynı piyasa).
QQQ temettü günleri (yılda ~4) olası ayarlanmamış veri yanlılığı olarak not edilir.

## 7. Hesap kuralları

* `nice`, tek süreç, python3.13 (pandas/pyarrow). Bütün sınama setleri `dv_1_test.py` içinde tek koşumda, çıktı
  `results/test_sonuc.json` + `results/test_stdout.txt`. Koşum çökerse (sonuç basılmadan) hata düzeltilip yeniden koşulabilir;
  sonuç görüldükten sonra hiçbir tanım/eşik/dönem değişmez. Değişirse §8'e yazılır, sonuç "doğrulayıcı değil" etiketlenir.

## 8. Sapmalar ve sınama öncesi sayılar (dv_0 sonrası doldurulur; sınama verisine bakılmadan)

Yazıldı 2026-10-14, `dv_0_hazirlik.py` sonrası, `dv_1_test.py` koşulmadan önce. Çıktı: `results/hazirlik.json`,
`results/hazirlik_stdout.txt`. Sınama setlerinde yalnız eksen denetimi + gece SAYILARI hesaplandı.

**8.1 Keşif yeniden üretimi — birebir.** n = 2.334 (aşağı 1.144), yükseliş %60,752 / %55,210, ort. +13,612 / +0,498 puan
(ek_tanimsal.json ile 1e-6 içinde aynı). B = 10.000 ile P(puan) 0,9987, P(%) 0,9963, P(yükseliş) 0,9959.

**8.2 Dondurulmuş eşikler (keşiften):**
| büyüklük | keşif etkisi | eşik (½) |
|---|---|---|
| ort. gece % farkı E_pct | 0,0859 yüzde puanı (aşağı +0,1026 % vs yukarı +0,0168 %) | **≥ 0,0429** (NDX) |
| yükseliş oranı farkı E_up | 5,54 puan | **≥ 2,77 puan** (NDX ve DAX) |
| puan farkı E_pts | 13,11 puan | yalnız rapor |
| standartlaştırılmış d_E = E_pct / SD(on%) | 0,1082 (SD 0,794 %) | **d ≥ 0,0541** → DAX eşiği = 0,0541 × SD(DAX on%) |

Bağlam (eşik değil): çağlar 2016–2020 fark +0,026 % / +3,6 puan; 2021–2025 +0,145 % / +7,6 puan. Keşif plasebosu
(11→12 NY saati → aynı gece): fark −0,034 %, P 0,14; eşli P(son saat − plasebo > 0) = 0,994 → keşifte etki kapanışa özgü.
2017-11/2018-02 eksen düzeltmeli keşif: +0,0862 % / +5,24 puan (kusur sonucu değiştirmiyor).

**8.3 Hizalama — hepsi geçti.** 15m→1h vs `long_1h`: 2025-11-17..21 (114 bar) ve 2026-07-06..10 (113 bar) %100 eşleşme,
maks |ΔC| 0. 07-15 sonrası 15m vs bağımsız 1m→15m: kayma 0'da %99,3 barda |ΔC| ≤ 2 (medyan 0), ±15/±60 dk'da ≤ %8.
16:00 NY kapanışı vs NDXCASH_close std: `long_1h` 2025-12 → 2026-07 ve 15m 2026-07 → 09 her ayda en iyi kayma 0.
Açılış tepe dilimi: 15m 2026-07/08/09 = 09:30 NY; `long_1h` holdout ayları 09:00 veya 10:00 barı (beklenen).
DAX eksen düzeltmesi: tepe = 09:00 Berlin payı 30m ham %61 → düzeltilmiş %94 (17/18 yıl×sınıf grubu); tek istisna 2026 omuz
(15 gün; 09:00 ikinci, 130 vs 136). 1h düzeltilmiş %86 (istisnalar omuz grupları, ABD oturumu baskın). 1h_fix vs 30m_fix
toplamı %99,5 eşleşme. Omuz döneminde (NY yaz/Berlin kış) düzeltme uygulanmıyor ve 30m'de 09:00 her yıl ilk ya da ikinci.

**8.4 Değişiklikler (sınama ÖNCESİ, sonuç görülmeden — doğrulayıcı niteliği korunur):**
1. Takvim = `NDXCASH_close` dolu günler (§1'de "O/H/L/C dolu" yazıyordu). Neden: O/H/L 2026-07-28'de bitiyor, kapanış
   2026-09-30'a kadar var; eski tanımla uzatma yalnız 10 gece olurdu. 2026-07-28'e kadar iki tanım birebir aynı gün
   kümesi (denetlendi); keşif yeniden üretimi değişmedi. (f) O/H/L kullanmaz.
2. QQQ verisi 2026-07-28'de bitiyor → Q-hold fiilen 2025-12-01 → 2026-07-27.
3. DAX Xetra tatilleri kural tabanlı; CFD 2021 Kutsal Cuma/Paskalya Pzt'de işlem görmüş (bar var) → bar varlığı Xetra
   açık demek değil; kural takvimi esas. Pfingstmontag her yıl bar var ve işlem günü sayılıyor.

**8.5 Gece sayıları ve a-priori güç (MDE₈₀, keşif bootstrap sd'sinden ölçekli):**
N-H 150 gece (2025-12-02 → 2026-07-13), N-X 55 (2026-07-14 → 09-29), **N-HX 205**; D-30 1.403 (2021-03-18 → 2026-09-30;
1.415 adaydan 12'si eksik bar); D-1h 1.712; Q-D 2.845 (2015-01-05 → 2026-07-27).
* N-HX: MDE₈₀ ≈ **0,27 yüzde puanı** = keşif etkisinin 3,2 katı, eşiğin 6,3 katı; yükseliş oranında ≈ 17,7 puan.
  → NDX holdout'u yapısal olarak düşük güçlü: etki keşifteki kadarsa bile büyük olasılıkla **SONUÇSUZ** çıkar;
  ÇÜRÜTÜLDÜ ancak gözlenen fark belirgin negatifse mümkün. Bu, sınamadan önce bilinen bir sınırlılıktır.
* D-30: MDE₈₀ ≈ d 0,130 = d_E'nin 1,2 katı → tam keşif etkisi için güç ≈ %65, yarı etki için düşük. DAX bağımsız piyasa
  sınamasının asıl gücü budur.

## 9. Koşum kaydı (sınama sonrası; tanım/eşik değişmedi)

`dv_1_test.py` 2026-10-14'te **bir kez** koşuldu (çökme/yeniden koşum yok). Sonuç: `results/test_sonuc.json`,
`results/test_stdout.txt`. Hipotez verdikti: N-HX SONUÇSUZ (Δ% +0,127, P 0,906), D-30 SONUÇSUZ (Δ% +0,001, P 0,506) →
**SONUÇSUZ**. Yorum: `research_notes/Nasdaq mum eşleştirme derin tarama/dogrulama.md`; defter ME-07.
