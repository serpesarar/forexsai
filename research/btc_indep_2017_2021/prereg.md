# Ön kayıt — Dondurulmuş BTC gölge portföyünün bağımsız dönem sınavı (2017-08 → 2021-05)

Yazılış: **2026-10-22 12:17 UTC**. Bu dosya yazılırken bağımsız dönemin hiçbir fiyat/akış verisi İNDİRİLMEDİ ve hiçbir sonuç
hesaplanmadı. Önceden yapılan tek şey: data.binance.vision S3 **dosya listesi** (yalnız hangi ayların mevcut olduğu;
`logs/00_list.log`) ve dondurulmuş kayma eşiğinin ESKİ veriden (2021-06→2023-12 DISC) yeniden okunması (aşağıda §4).
Sonradan yapılan her ek "EK-n (sonuç SONRASI)" etiketiyle dosyanın sonuna yazılır ve verdikti değiştiremez.

## 0. Amaç ve dürüstlük çerçevesi
- 08 notundaki (`research_notes/BTC scalping strateji araştırması/08_strateji_insasi.md`) **dondurulmuş** "BTC-ST GÖLGE PORTFÖYÜ v1"
  (P-PRE) ve iki geniş portföyün (P-ALL−DV = P-PRE + CAPREV-RV + OF02; P-ALL = yedi kol) **hiç görülmemiş** 2017-08-17 → 2021-05-31
  Binance verisinde **tek seferlik** sınavı. Parametre ayarı YOK, kol ekleme/çıkarma YOK, veto YOK (dondurulmuş portföy vetosuz).
- Bu dönem 2021-06 öncesidir; önceki iki turun hiçbir aşaması (keşif, seçim, POST, BLIND) bu veriyi görmedi. Dolayısıyla burada
  post-hoc kollar (CAPREV-RV, OF02, DV04c) da **ilk kez bağımsız** sınanır.
- Bilinçli zorluk: 2017 köpüğü (BTC $4k→$20k), 2018 ayı piyasası (−%75), 2019 toparlanma, 2020-03-12 COVID çöküşü, 2020-10→2021-04 boğa,
  2021-05 çöküşü. Fiyat düzeyi $3k–$64k. Testin amacı tam olarak bu farklı rejimde kenarın işaretinin korunup korunmadığı.
- Önceden yazılan beklenti (dürüst): P-PRE'nin POST kenarı +0,026R ve son 12 ayı ≈0 olduğu için, bağımsız dönemde gerçek kenar sıfırsa
  ortR'nin ±0,03R bandında herhangi bir işaret çıkması olasıdır; P(EV>0) ≥ %90 eşiği bu yüzden şarttır.

## 1. Veri (indirilecek; data.binance.vision, SHA256 .CHECKSUM doğrulamalı)
- Spot BTCUSDT 1m aylık: **2017-08 → 2021-05** (46 dosya). İlk bar 2017-08-17 04:00 UTC (Binance listelemesi).
- USDT-M perp BTCUSDT 1m klines aylık: **2020-01 → 2021-05** (17 dosya). S3 listesi: perp arşivi **2020-01'de başlıyor**
  (görevde varsayılan ~2019-09 DEĞİL; günlük arşivde tek ek gün 2019-12-31). premiumIndex/mark/index 1m + fundingRate aynı aylar
  (yalnız veri kalitesi/baz çapraz kontrolü; hiçbir dondurulmuş kolun girdisi değil).
- **metrics (OI/LS) İNDİRİLMEZ:** yedi kolun hiçbiri OI/LS/funding/premium kullanmıyor (OF02 = perp taker deltası + spot getiri;
  DV04c = spot z5 + perp/spot baz değişimi, ikisi de klines'tan). Arşiv zaten 2020-09'da başlıyor. Sapma olarak not edildi, etkisi yok.
- Makro günlük (yfinance, `04_macro_yf.py` mantığı, aynı 5 sembol): 2017-01-01 → 2021-06-30. X04 yalnız QQQ açılış/kapanış kullanır.
- Ham dosyalar `data/raw/` (güvenilmez; yalnız CSV olarak okunur, `python -I`), inşa edilen parquet `data/`.
- İnşa: `btc_5y_20261021/scripts/02_build_binance.py` (ms/µs dosya-başı birim tespiti, başlık atlama, boşluk DOLDURMA YOK, UTC
  left-closed/left-label 5m/15m/1h/4h/1d) ve `btc_scalp_20261021/scripts/02_build_futures.py` + `07_assemble.py`'nin kolların
  ihtiyaç duyduğu sütunları üreten kısmı (spot_*, perp_*, spot_missing, spot_zero_vol, perp_zero_vol, basis_perp_spot_bp) —
  yalnız tarih sabitleri değişir.

## 2. Dönem, pencereler ve kolların etkin başlangıçları
- **IND** = giriş zamanı ∈ [2017-08-17, 2021-06-01). Çıkışı veri sonunu (2021-05-31 23:59) aşan işlemler sansürlenip atılır
  (motorun mevcut kuralı; 2021-06 verisi kullanılmaz). Sayısı raporlanır.
- **PERP** = giriş ∈ [2020-01-11, 2021-06-01): tüm yedi kolun etkin olduğu ortak alt pencere (bilgi + P-ALL−DV/P-ALL için ikincil).
- Kolların etkin başlangıcı (dondurulmuş kodun KENDİ ısınma kurallarından; ek kısıt eklenmez):
  | kol | girdi | ısınma (kodda) | beklenen ilk olası giriş |
  |---|---|---|---|
  | S1 CORE | UTC H4 + D1 | EMA200(D1) ilk 199 bar NaN (`lt.ema`) | ~2018-03-05 |
  | S2 MAX10 | D1 | ATR14 Wilder (13 bar NaN), 10 D1 maksimum | ~2017-08-31 |
  | S3 QB | 1h | ATR14(1h) basit ortalama | ~2017-08-18 |
  | S4 X04 | QQQ + D1 | karar > T0+30 gün; dvol20 | ~2017-09-18 |
  | S5 CAPREV-RV | D1 + 1h | σ30'un 365 g medyanı min_periods=120 | ~2018-01-14 |
  | S6 OF02 | perp + spot 1m | z penceresi 30 g, min 14.400 dk (10 g) | ~2020-01-11 |
  | S7 DV04c | spot z5 + perp/spot baz | z5 min 10.000 dk; baz perp'ten | ~2020-01-01 |
  (2021-06 öncesi orijinal verilerde de aynı ısınma kuralları veri başından itibaren işletilmişti; kural aynı.)
- Dışlama: yeni dışlama YOK. Motorun yerleşik boşluk kuralları aynen: trend motoru (giriş ≤10 dk gecikme, boşluk-duyarlı SL dolumu),
  scalp ızgarası (≥5 dk Binance kesintisi BAD; [e, e+60) BAD ile kesişmemeli). 2023-03-24 sabit dışlaması bu dönemde etkisiz.

## 3. Dondurulmuş tanımlar (kopya ile referans)
Tanımlar = 08 notu "Önerilen strateji (dondurulmuş tanım)" tablosu + `btc_scalp_20261021/strateji/prereg.md` §2–§7. Kod, aşağıdaki
SHA256'lı dosyalardan **birebir kopyalanır**; yalnız veri yolları, ızgara başlangıç/bitiş sabitleri, bölme (split) sabitleri ve
rollover/plasebo tarih aralıkları değiştirilir. Kopyalama `scripts/00_port.py` ile, her değişiklik tam-eşleşmeli (tam bir kez)
dizge değişimi olarak yapılır; fark dosyası `scripts/port/PORT_DIFF.txt`. Mantık satırı değişmez.

| dosya (research/ altında) | SHA256 |
|---|---|
| btc_scalp_20261021/strateji/lib_st.py | 61e76c3e8f79c994aeac94d83f71adc489996e0ea790f7e14881d0741abb9362 |
| btc_scalp_20261021/strateji/sleeves.py | dee37f9eb36099bbcf424a0d1e9b5ceac1cce2035bb5a3c5aadf753b27e12e4e |
| btc_scalp_20261021/strateji/03_portfolio.py | 50f08e2343165924a7231329a12dda28aa8a79a46e5168b54919f3340be7110b |
| btc_scalp_20261021/strateji/01_events.py | c95a81c89b4fc266a74ec28b0e7f9032ddd1055b5e1e0499e70b4265ca9ba966 |
| btc_scalp_20261021/strateji/00_selftest.py | a2127938d0f6e47940e40f8b19ae4a4232cbc45e719cf0874cbb4c240959f2c7 |
| btc_scalp_20261021/strateji/prereg.md | 788cafef6d8b0d0446528d3802c576da27664ee50d5973fb963c8685727ad74f |
| btc_5y_20261021/fam_trend/lib_trend.py | 178dd033e4b7f44ac97ea34445d4db913a69d0dba50d1c9486cd2494d3d21018 |
| btc_scalp_20261021/fam_orderflow/ofl.py | e59b9378fc4bf40ac285f20bf773efcfabdddc065f0ced0ed55587c5422d3b37 |
| btc_scalp_20261021/fam_orderflow/01_build.py | 6952cddaf77b870dff6e8027872ec00a5ceef05d6f6ae6daa993cb7a33515273 |
| btc_scalp_20261021/feasibility/lib.py | 4bc6354bc1de272fb9b7273969deb4215c49c164a09d2747c21fd8bf72ea1a7f |
| btc_scalp_20261021/fam_turev/scripts/01_prep.py / 02_outcomes.py / 03_events.py / common.py | 2a7885b7… / 7add1127… / 30d14cbc… / cffac3ca… |
| btc_5y_20261021/scripts/02_build_binance.py / 04_macro_yf.py | 2c59bba4… / 062bd345… |
| research_notes/…/08_strateji_insasi.md | 8d7c98e76cb3fbe7ec8f5175a7d14b5d7a57a145e207b7adcb03a051baadbdc3 |

Kollar (özet; tam tanım yukarıdaki kaynakta): S1 CORE H4D20-T-L (UTC H4 kapanışı ≥ önceki 20 H4 en yükseği ∧ D1 kapanış > EMA200(D1);
BUY piyasa; SL 2×ATR14(H4), TP 4×ATR14, 30 H4 bar) · S2 MAX10 (D1 kapanış = 10 günün en yükseği → 00:00 BUY, SL 2×ATR14(D1), 24 s) ·
S3 QB (RO+1 BUY → 23:00 UTC; bot biçimi 2×ATR14(1h) felaket SL, R paydası 2×ATR1h) · S4 X04 (QQQ |gz|>0,5 → 10:00 ET boşluğun tersi,
SL 1×dvol20, 16:58 ET çıkış) · S5 CAPREV-RV D0 · S6 OF02 W15 θ5 · S7 DV04c-U b3. OF02 ve DV04c olay üretimi `fam_orderflow/01_build.py`
(yalnız OF02_W15_th5 hücresi) ve `fam_turev/scripts/01_prep.py`+`02_outcomes.py`(H60 `valid`)+`03_events.py` (yalnız DV04c-U b3.0)
kodunun ilgili satırlarıyla yeniden üretilir.

## 4. İcra/maliyet modeli (dondurulmuş, değişmez)
- Giriş = sonraki 1m açılışı ± yarım spread; **birincil maliyet % modeli RT 1,85 bp**; stres ×1,5 (2,775 bp); sabit **15 $ RT** varyantı
  (2017–2021 fiyatlarında 15 $ = ~2,3 bp ($64k) … ~50 bp ($3,1k) — 2018–2019'da çok büyür; yalnız rapor); iyimser varyant (ölçüt 5).
- SL bid/ask tetik, boşluk-duyarlı dolum, kayma 1 bp / sıcak dakikada 5 bp. **Sıcak dakika eşiği = dondurulmuş sayı 29,298 bp**
  (orijinal DISC p99 |1m log getiri|, eski veriden yeniden okundu: 29.298164936615546). Bağımsız dönemin kendi p99'u YALNIZ
  duyarlılık olarak raporlanır (2018 oynaklığı daha yüksek → dondurulmuş eşik daha çok dakikayı "sıcak" sayar → muhafazakâr).
- TP limit, aynı barda TP+SL → SL. Swap: her NY 17:00 rollover'ında long −%14/365, short +%2/365 (dondurulmuş Pepperstone; o yılların
  gerçek BTC CFD swap'ı farklıydı — model varsayımı olarak not edilir). Rollover = `America/New_York` 17:00 → UTC (zoneinfo/pandas tz;
  2017–2021 ABD DST kuralları 2007 kuralıyla aynı: Mart 2. Pazar → Kasım 1. Pazar; yaz 21:00, kış 22:00 UTC). Gün-içi kollar RO−2'de
  kapanır, [RO−2, RO+3) girişsiz, QB RO+1 girer.

## 5. Portföyler ve kart
- P-PRE = S1+S2+S3+S4 (**birincil**); P-ALL−DV = S1…S6; P-ALL = S1…S7; P-CORE = S1 (bilgi). Kol başı tek pozisyon, eşit risk/işlem,
  vetosuz, kollar arası serbest; küresel tek-poz ölçüt 6 için (03_portfolio.py `card(glob_single=True)` aynen).
- Kart = 03_portfolio.py `card()` birebir: 1 n ≥ 150 · 2 ortR > 0 ∧ gün-bloklu bootstrap P(EV>0) ≥ %90 (B=5000, tohum 7) · 3 iki
  kronolojik yarı ≥ 0 · 4 stres ortR > 0 · 5 |iyimser − gerçek| ≤ ortR/2 · 6 kol-içi tek-poz (portföyde küresel tek-poz) > 0.
  Ek: plasebo yüzdeliği (200 tekrar, 03_portfolio.py yöntemi ve tohumu 20261022; yıl sınırları bağımsız döneme kırpılır), en iyi 5/20
  gün hariç ortR, maxDD(R), yıl bazında n/ortR, sabit 15 $ ortR, bp.

## 6. Geçme kuralı (ŞİMDİ donduruldu)
**H1 (birincil, tek karar):** P-PRE, IND penceresinde:
- **TUTUYOR** ⇔ ortR > 0 **∧** gün-bloklu P(EV>0) ≥ %90 **∧** kart ≥ 4/6.
- **ZAYIF / TEYİT YOK** ⇔ ortR > 0 ama P < %90 veya kart < 4/6.
- **TUTMUYOR** ⇔ ortR ≤ 0.
**H2 (kol bazında, betimsel + işaret):** her kol IND'de kendi etkin penceresinde: işaret (ortR > 0?), P(EV>0), kart. "Kol tutuyor" ⇔
ortR > 0 ∧ P ≥ %90. Önceden beklenen işaretler: POST'ta yedisi de pozitifti; bağımsız dönemde kaç tanesinin pozitif kaldığı raporlanır.
**H3 (ikincil):** P-ALL−DV ve P-ALL için H1 kuralı IND'de (kollar etkin oldukları sürece katkı verir) ve PERP alt penceresinde.
Post-hoc kollar burada ilk kez bağımsızdır; yine de portföy kararını H1 belirler.
**Sağlamlık raporu (verdikti değiştirmez, önceden ilan):** yıl bazında işaret (2017k, 2018, 2019, 2020, 2021k), en iyi 20 gün hariç,
plasebo %, stres, sabit 15 $, sıcak-eşik duyarlılığı, >%5 fitil içeren günler hariç duyarlılığı (veri kalitesi raporunda işaretlenen
günler; yalnız duyarlılık).
**08 notuyla tutarlılık okuması (önceden):** bağımsız ortR, POST'un +0,026R'sinin %95 GA'sı [−0,004; +0,057] içindeyse "tutarlı",
altındaysa "POST kenarı bağımsız dönemde küçülüyor/yok" olarak yazılır.

## 7. Motor doğrulama (sonuçtan ÖNCE koşulur; geçmezse sonuç üretilmez)
- (a) kayma 0 iken CORE olaylarında port edilmiş Engine = port edilmiş `lib_trend.M1.simulate` (|ΔR| < 1e-9).
- (b) ≥3.000 rastgele olay (piyasa/limit-skip/limit-market, iki yön, TP'li/TP'siz, base/stress/abs, kaymalı) dakika dakika kaba döngü
  (`lib_st.brute`) ile 0 uyuşmazlık — yeni veri üzerinde.
- (c) OF02 özellikleri için önek (sızıntı) testi (`01_build.py` yöntemi, kesim 2020-09-15 12:00).
- (d) Port farkının yalnız sabit/yol değişikliği olduğunu gösteren `PORT_DIFF.txt`.

## 8. Yazma/erişim kısıtları
Yalnız `research/btc_indep_2017_2021/` altına yazılır; başka repo dosyası, kutu, Supabase'e dokunulmaz; commit yok.
Python `.venv` (numpy 2.4.6), `python -I -B`.

---
## EK-1 (sonuç ÖNCESİ, veri; 2026-10-22 ~12:25 UTC — tanım/kural değiştirmez)
- Binance spot arşivinde iki blok dakika-dışı açılış damgası: 2017-12-04 06:00:20.799 → 2017-12-18 10:00:20.799 (20.401 bar, +20,799 s)
  ve 2018-02-09 09:59:14.789 → 2018-02-10 05:59:14.789 (1.201 bar, +14,789 s). `scripts/02b_floor_offgrid.py` damgaları dakikaya
  tabanladı (lt.tmin ve resample zaten böyle yapıyordu); tek çakışmada (2017-12-04 06:00) hacimli dakika-hizalı bar tutuldu.
  Üst TF OHLC'leri tabanlanmamış hâliyle birebir aynı çıktı (`logs/02b_floor.log`). Etki: yalnız 1m ızgara birleştirmesi (scalp kolları
  2020+ kullanır → sonuca etkisi yok).
- Perp arşivi 2020-01-01'de başlıyor (§1'de zaten yazılı). OF02 ilk geçerli olay 2020-02-26, DV04c ilk epizod 2020-01-03.
- `scripts/port/events.py` tablosundaki "POST_*" sütun adları dondurulmuş koddan kalmadır; burada anlamı IND (A ∪ PERP) penceresidir.

## EK-2 (sonuç SONRASI, 2026-10-22 ~12:40 UTC — verdikti DEĞİŞTİRMEZ)
- `scripts/05_sensitivity.py`: ön-kayıtlı duyarlılıklar (dönem p99 sıcak eşiği, fitil günleri hariç, sabit 15 $ yıl bazında, swap −%22,5)
  + ön-kayıtlı OLMAYAN maliyet taraması (% RT 1,85…20 bp; başabaş spread'i bulmak için; seçim için kullanılmadı) + bağlam (BTC al-tut
  yıl getirisi, P-PRE uzun payı, QB'siz P-PRE).
