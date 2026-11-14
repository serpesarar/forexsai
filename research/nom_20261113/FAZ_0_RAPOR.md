# FAZ 0 — Veri envanteri ve denetim (NOM, 2026-11-13)

Kod: `src/data_layer.py`, `src/faz0_build.py`, `src/duka_fetch.py`, `src/macro_fetch.py`.
Çıktı: `data/ndx_1m_v1.parquet` (temiz katman), `data/macro/macro_daily.parquet`, `data/macro/calendar.parquet`,
`results/faz0_inventory.json`, `results/faz0_candle_cache_weekly_lag.csv`.

## 0. Neyi yeniden kullanıyorum, neyi neden değiştiriyorum

| Kaynak | Kullanım | Değişiklik / neden |
|---|---|---|
| `ndx_reflex_engine/labels/triple_barrier.py`, DESIGN §6 | Triple-barrier fikri, **aynı bar → SL**, bid/ask içinde spread, ATR geometrisi, SL-önce belirsizliği | Yeniden yazıldı (`backend/services/nom/labels.py`): reflex etiketi **olay** tabanlı ve tek ufuk; NOM her anda (5/15 dk ızgara), 4 ufuk × 5 geometri × 2 yön, boşluk dolumu ve hafta sonu kuralıyla. Canlı sonuç notlaması da aynı fonksiyonu kullanır. |
| reflex `features/pack.py` | Özellik fikirleri (ATR yüzdeliği, VWAP z, yuvarlak sayı, önceki gün H/L, VIX 18,4) | Yeniden yazıldı (`backend/services/nom/features.py`): **tek kod yolu** (eğitim = canlı), tüm HTF'ler `end ≤ t` kilidiyle (E16 dersi: mom_cont sol-etiket sızıntısı) + otomatik kesme/bozma testleri. |
| reflex isotonic kalibrasyon + doğrulama bataryası | Kalibrasyon yaklaşımı, plasebo, bootstrap, 1,5–2× sürtünme stresi | Purged WF + ambargo + kilitli final test eklendi (reflex 60/40 kronolojik bölmeydi). |
| `research/trend_kanal_20261108/data.py`, `geri_cekilme_limit/data_y.py` | Dukascopy bi5 ayrıştırıcı, kapalı-saat maskesi, NY 18:00 hizalı 4h/1d | Aynı mantık `data_layer.py`/`bars.py`'ye taşındı; 15m dolgu günleri KULLANILMIYOR (E104: kaba yolla çözülen dönem 1m dönemle karıştırılmaz). |
| `research/ndx_seans_tasima_20261103/denetim/duka_slow.py` | Seri, nazik indirme kalıbı | `src/duka_fetch.py`: öncelikli aralık listesi. |
| `research/xau_best_days_20261015/makro/03_calendar.py` (FOMC/CPI/NFP/JH) | Olay takvimi | 2026 FOMC Tem/Eyl/Eki/Ara eklendi; mega-cap bilanço tarihleri yfinance'tan. PCE **eklenmedi** (güvenilir tarih kaynağı yok; uydurma tarih yok). |
| `yeni deneme/broker_time.py` | MT5 sunucu saati = NY+7 kuralı | Eğitim verisi Dukascopy (UTC) → gerekmedi; canlıda candle_cache (kaydedici zaten UTC'ye çeviriyor). RECOVER json'u (broker saati) kullanılmadı. |
| Defter E1–E127 | Kontrol listesi | Özellikle E4 (candle_cache −60 dk), E16, E58 (1m ilk dokunuş yanlılığı), E62/E63 (kalibre olmayan eşik), E90 (Brier'i iklim tabanıyla sına), E99 (makro kapanış saati), E51 (maliyetli plaseboyu yenmek kenar değildir). |
| Önceki hükümler | GC-02 (tüm göstergeler modeli: AUC +0,0065), TM-01 (Monte Carlo "hedef önce" iklim tabanından kötü), DTS-03 (oynaklık bandı **A**, yön değil), PN-05 | **Ön beklenti:** P(TP önce) simetrik geometride ≈ yön tahmini → iklim tabanına yakın; P(zaman aşımı) oynaklıktan → öngörülebilir. Yeni gerekçe: aynı soru ilk kez ATR-ölçekli çok-ufuklu bariyer etiketiyle, 5 yıl 1m + makro + seviye bağlamıyla, kalibrasyon ve ekonomik değerle birlikte soruluyor. |

## 1. Envanter (kaynak başına)

| Kaynak | Başlangıç → bitiş (UTC) | 1m bar | Eksik işlem günü | İnce gün (<600 bar) | Spread | Kalite skoru |
|---|---|---|---|---|---|---|
| Dukascopy bi5 2021-11→2023 | 2021-11-01 → 2023-12-29 | 741.943 | 0 / 544 | 115 (tatil/yarım gün) | yok → model | 93,3 |
| Dukascopy 2024 (haber_derin) | 2024-01-01 → 2024-12-31 | 342.269 | 0 / 252 | 54 | 2025 modelinden | 93,2 |
| Dukascopy 2025 (gerçek bid/ask) | 2025-01-01 → 2025-12-30 | 306.635 | 1 / 249 | 66 | **gözlenen**, medyan 1,52 | 92,0 |
| Dukascopy 2026 (haber_derin) | 2026-02-08 → 2026-11-03 | 253.843 | 0 / 186 | 39 | 2025 modelinden | 93,3 |
| **MT5 NAS100 (altın standart)** | 2026-05-19 → 2026-08-28 | 100.000 | 0 / 71 | 15 | medyan 1,3 | 95,8 |
| candle_cache CSV | 2026-02-10 → 2026-08-28 | 195.285 | 0 / 139 | 30 | yok | 94,3 (ama bkz. §2) |
| RECOVER/mt5_ustec json | 2026-03-03 → 2026-06-12 | 99.820 | 0 | 15 | yok | **kullanılmaz** (bkz. §2) |
| 2018-01 → 2021-10 Dukascopy | indirme denendi | — | — | — | — | **eksik** (aşağıda) |
| 2026-01-01 → 02-07 | indirme denendi | — | — | — | — | **eksik** |

Hacim: Dukascopy bi5'te var, 2024+ parquet'te yok; MT5 tick hacmi farklı tanım → **hacim özelliği kullanılmıyor**.
Saat dilimi: hepsi UTC epoch, bar açılışı. Seans hesapları `America/New_York` (zoneinfo, DST doğru) + statik NYSE
tatil/yarım gün takvimi (`backend/services/nom/nyse_calendar.py`, 2018–2026; `pandas_market_calendars` ortamda yok).

## 2. Kaynaklar arası karşılaştırma

| Çift | Çakışma | En iyi gecikme | Getiri korelasyonu | Seviye farkı (medyan / IQR) | ±3 puan uyum | Uyum <%80 gün |
|---|---|---|---|---|---|---|
| Dukascopy vs **MT5 altın** | 96.771 bar | **0 dk** | 0,978 | −1,0 / 29,1 puan | %91,7 | 15/88 |
| candle_cache vs MT5 altın | 99.611 | 0 dk | 0,994 | 0 / 0 | %95,5 | 8/88 |
| Dukascopy vs candle_cache | 187.576 | 0 dk (tümü) | 0,839 | −0,5 / 22,6 | %80,4 | 48/171 |
| RECOVER json vs MT5 altın | 22.102 | ±90 dk içinde yok | ≈0 | −35,8 / 140 | %2,9 | 19/19 |

Haftalık gecikme taraması (`faz0_candle_cache_weekly_lag.csv`): candle_cache **2026-02-10 → 03-05 haftaları +60 dk**
kayık (E4 teyit), 03-05 haftası karışık (r=0,64), sonrası 0 dk. RECOVER json korelasyonu ±90 dk içinde sıfır → alan
broker saatinde (+180 dk, E93). Dukascopy ile Pepperstone arasında sabit olmayan seviye farkı (IQR 29 puan, CFD
fiyatlama farkı) var → **tüm özellikler ATR-normalize, fiyat seviyesi kullanılmaz**.

**Karar:** Eğitim/etiket = Dukascopy (tek tutarlı besleme, MT5 altın standartla gecikme 0, r=0,978).
candle_cache yalnız 2026-03-08 sonrası canlı servis beslemesi olarak (MT5 kaydedicisinin yazdığı broker verisi)
kullanılır; MT5 altın standart dönemde onunla r=0,994 uyumlu.

## 3. Temizlik kuralları ve sayaçlar
- R1 kapalı saat (NY 17:00 saati, hafta sonu): 2021-23 bi5'ten 196.680 satır.
- R2 OHLC tutarsızlığı: 0. R3 düz sıfır-hacim dolgu barı: 37.691 (2021-23 bi5). Duplike: 0.
- R4 tek-bar sıçrama (|getiri| > 25× gün medyanı ve ≥%80 geri dönüş): 8 bar silindi.
- Rollover: günlük aradan sonraki açılış boşluğu çeyrek vade penceresinde ortalama −0,10 puan, diğer günlerde
  +0,85 (|medyan| 14,2 vs 14,0) → **sistematik vade sıçraması yok** (Dukascopy endeks CFD'si nakit-benzeri). En büyük
  boşluklar gerçek olaylar: 2025-04-02 −997 (gümrük vergisi), 2025-04-06 −845.
- Spread modeli (NY saati, puan): 09–17 → 1,40–1,50; gece/Asya → 3,41. MT5 Pepperstone medyanı 1,3 → koruyucu
  maksimum alındı. 2025 dışındaki yıllarda spread **model**dir; 2020/2022 gibi stresli dönemlerde gerçek spread daha
  geniş olabilir → Faz 5'te 2× sürtünme stresi bu yüzden zorunlu.

## 4. Veri eksiği kapatma
- **Dukascopy 2018-01 → 2021-10 (2020 çöküşü)**: `src/duka_fetch.py` seri indirme başlatıldı; sunucu 503 /
  "connection reset" ile sürekli blokluyor (önceki oturumlarda da saatte ~40 dosya, defter notu). Bu rapor anında
  yalnız 10 gün indi → **bu sürümde yok**. Arka plan indirici devam ediyor; tamamlanırsa `data_layer` onları otomatik
  alır (v2). 2020 çöküşü rejimi bu nedenle eğitimde YOK; 2022 ayı piyasası ve 2025 Nisan çöküşü VAR.
- 2026-01-01 → 02-07 (5 hafta) aynı nedenle eksik (geliştirme döneminde delik; etiketler deliği geçemez).
- MT5'i bugüne tamamlama: Mac'te MT5 terminali yok; kutudaki terminal 1m'yi ~100 gün tutar (E126) ve canlı
  kaydedici zaten candle_cache'e yazıyor → eğitim için gerekmedi, **atlandı**.
- Makro (yfinance, günlük, 2012-01 → 2026-11-13): VIX, VIX9D, VIX3M, SPX, ES=F, NDX, QQQ (+hacim), DXY, TNX.
- Takvim: FOMC 151, CPI 224, NFP 225, Jackson Hole 17, mega-cap bilanço 615 (AAPL/MSFT/NVDA/AMZN/GOOGL/META/TSLA).
  CPI listesi 2026-09-11'de bitiyor (sonrası kapsam dışı — özellik NaN değil "uzak" olur; sınırlılık).

## 5. Kullanılabilir veri hükmü
Çekirdek: **2021-11-01 → 2026-11-03, 1m, 1.645k bar, ~5 yıl** (2022 ayı, 2023-25 boğa, 2025 Nisan çöküşü).
DUR koşulu (<2 yıl) oluşmadı. Hedeflenen "≥5 yıl" karşılandı; "2020 çöküşü" karşılanamadı (indirme engeli).

## EK (2026-11-14) — MT5'i bugüne tamamlama ve 2018–2021 indirme girişimleri
- **MT5 bugüne tamamlandı** (§4 madde 2'nin kapanışı): kutudaki Pepperstone terminalinden salt okunur NAS100 **M1 2026-08-05 → 2026-11-13**
  ve **M5 2025-06-18 → 2026-11-13** çekildi (`research/yon_lab_20261114/src/kutu_export_m5.py`, terminal tavanı 100.000 bar, E126).
  Dukascopy ile karşılaştırma (`results/faz0_mt5_uzatma.json`): M1 87.590 ortak bar, **gecikme 0 dk, getiri korelasyonu 0,996,
  ±3 puan uyum %95,0**; M5 89.899 ortak bar, gecikme 0, korelasyon 0,968. Önceki altın standart (05-19 → 08-28, r 0,978, %91,7) ile
  tutarlı → Dukascopy ana seri olarak kalır, MT5 ile 2026-11'e kadar doğrulanmış olur.
- **2026-01-01 → 02-07 boşluğu dolduruldu** (32 gün dosyası indi; Yön Lab v2 veri katmanında kullanıldı).
- **2018-01 → 2021-10 (2020 çöküşü) tamamlanamadı:** Dukascopy seri indirici (1,5 sn aralık + 60→600 sn geri çekilme) ~3 saatte
  yalnız 57 gün indirebildi; günlükte 36 "503 / connection reset" engeli (`logs/duka_fetch_bid*.log`). Kalan ~1.100 gün bu hızla
  > 50 saat → indirici durduruldu (yeniden başlatılabilir, inen günleri atlar). Alternatif ücretsiz 1m kaynak HistData.com
  (NSXUSD M1) denendi: indirme belirteci yalnız tarayıcı JavaScript'iyle üretiliyor, komut satırından alınamıyor; ayrıca farklı
  besleme (E88/E104) olurdu. **DUR koşulu tetiklenmedi:** kullanılabilir veri 5 yıl 1m (2021-11 → 2026-11), eşik 2 yıl.
  Rejim kapsamı: 2022 ayı piyasası, 2023–25 boğa, 2025 Nisan çöküşü var; 2020 çöküşü yok (sınırlılık, FAZ_5 ve README'de).

## EK-2 (2026-11-14) — spread modelinin birimi (bulgu) ve 2018–21 tamamlama planı
- Faz 0'ın spread modeli **puan** cinsindendi (2025 fiyat düzeyinde 1,4–3,4 p). Fiyat düzeyi farklı dönemlere aynen taşınınca sürtünme
  ATR'ye göre bozuluyor: 2018'de (fiyat ≈ 6.800) ≈ 3× şişiyor (15 dk'da gözlenen TP %16 → bp ölçekli %23); NOM eğitiminin 2021–23 kısmında
  (fiyat 11–16 bin) ≈ %30–60 fazla → NOM v1 etiketleri o yıllarda **muhafazakâr** (olasılık tarafında TP biraz az, SL biraz çok).
  Canlı fiyat (≈ 27–31 bin) 2025 düzeyinin üstünde olduğundan servis tarafında sürtünme gerçeğe yakın/hafif fazla.
- Düzeltme: `src/faz0_v3_eski_donem.py` → `data/ndx_1m_v3.parquet`, spread = max(Dukascopy 2025, Pepperstone) NY-saati **bp × fiyat**.
  v1 (NOM paketinin veri sürümü) değiştirilmedi; v2 paket adayı backlog'da (bp etiketleriyle yeniden eğitim, Faz 9 terfi kuralıyla).
- 2018–21 indirmesi sabit beklemeli (6 sn aralık, 503'te 45 sn) indiriciyle sürüyor (`logs/duka_fetch_bid3.log`); tamamlanınca aynı
  betik etkin NOM paketini 2018-01 → 2021-10'da (2020 çöküşü dilimi dahil) hiç görmediği veri olarak değerlendirir
  (`results/faz0_v3_eski_donem.json`) ve bu ek güncellenir.

## EK-3 (2026-11-14) — 2018-01 → 2021-10 TAMAMLANDI (HistData NSXUSD, kullanıcı onayıyla)
- Kaynak: HistData.com NASDAQ 100 (NSXUSD) 1m "Generic ASCII" tam yıl arşivleri 2018/2019/2020/2021 (3,6 / 3,9 / 4,8 / 4,9 MB;
  kullanıcının Chrome oturumundan, sitenin kendi gezinme akışıyla — doğrudan adresle girilince indirme belirteci boş geliyor).
  `data/histdata/` (git dışı), ayrıştırıcı `src/histdata_layer.py`, katman `data/histdata_ndx_1m.parquet`.
- Saat: ~~belge "yaz saatsiz EST" → UTC = EST + 5 s~~ **YANLIŞTI — EK-5 (E135): yaz aylarında 60 dk kayıktı; düzeltildi.** İlk ölçüm (`results/faz0_histdata_denetim.json`):
  2021-11/12'de Dukascopy ile 58.194 ortak bar, **en iyi gecikme 0 dk, getiri korelasyonu 1,000, seviye farkı 0** (2021 HistData =
  Dukascopy); 2018 başında 52.801 ortak bar, gecikme 0 ama korelasyon 0,72, seviye farkı ~8 p → HistData'nın erken yılları farklı besleme.
- Temizlik (ilk eksen): 1.372.850 satır, R1 kapalı saat 14.176 (düzeltilmiş eksende 131), R2 0, R4 sıçrama 7. Eski dönem: **1.300.473 bar (düzeltilmiş 1.314.518), 1.194 gün, eksik hafta içi 5**
  (207 ince gün = HistData'nın 16:15–18:00 ET boşluğu ve tatiller).
- Kullanım: **tek beslemeli bağımsız eski dönem** (eğitim dışı, E88/E104) → `src/faz0_v3_eski_donem.py`, `data/ndx_1m_v3.parquet`
  (spread bp × fiyat), sonuç `results/faz0_v3_eski_donem.json` (FAZ_5 §6). Dukascopy indiricisi gereksizleşti, durduruldu.
- **Faz 0 madde 4 kapandı:** veri 2018-01 → 2026-11 (8,8 yıl, 1m), rejimler: 2018 Şubat şoku, 2018 Q4 düşüşü, **2020 çöküşü**,
  2021 boğası, 2022 ayı piyasası, 2023–25 boğa, 2025 Nisan çöküşü.

## EK-4 (2026-11-14) — prompt satır satır kapanış: takvim kütüphanesi, PCE, 1MDATA
- **Faz 0.3 `pandas_market_calendars`:** ayrı araştırma ortamı `.venv_ext` (py3.14; ana `.venv`'in numpy/sklearn kısıtları korunmak için)
  kuruldu, XNYS takvimiyle statik takvim karşılaştırıldı (`src/faz0_takvim_dogrula.py`, `results/faz0_takvim_1mdata.json`):
  2018–2026 **87 tatil ve 20 yarım gün, iki tarafta da birebir aynı, fark 0**. Servis statik modülü kullanmaya devam eder (Railway'de ek
  bağımlılık yok); eşdeğerlik kanıtlı.
- **Faz 0.4 PCE:** BEA Personal Income and Outlays açıklama günleri ALFRED PCEPI sürüm tarihlerinden alındı (2018-01 → 2026-10, 105
  tarih; ALFRED listesinde 2019-02 ve 2025-10/11 yok — o aylarda revizyon/kapanma) → takvime 08:30 ET olarak eklendi
  (`data/macro/pce_dates_alfred.txt`, `calendar.parquet`, `backend/data/nom/calendar.csv`). PCE prompt Faz 2'nin olay-özelliği listesinde
  yok; model özellikleri değişmedi, canlı "yaklaşan olay" bağlamında görünür.
- **Faz 0.2 `1MDATA/mt5_ustec_1m_bars.json`:** 2026-02-11 → 05-21, 97.252 bar. Alan broker saatinde (E93): kaydırmasız MT5 altın standartla
  r −0,03; **−180 dk kaydırmada r 0,999, uyum %99,8**; Dukascopy ile −180'de r 0,69 (dönemin Şubat–Mart kış kısmında offset +120 —
  tek sabit kaydırma oturmaz; broker_time kuralı gerekir). Eğitimde kullanılmadı (RECOVER json'uyla aynı karar).
- **Faz 0.4 MT5 betikleri:** prompt `RECOVER/mt5_export_1m_bars.py` / `research/mt5_pull_missing_1m.py` diyor; kutu terminali 100.000 bar
  tavanlı (E126) olduğundan aynı işi gören salt-okunur dışa aktarım (`yon_lab_20261114/src/kutu_export_m5.py`) kullanıldı → EK.
- **Dukascopy 2018–21:** HistData ile dönem kapandı (EK-3); Dukascopy indiricisi 2018-05-23'te durduruldu; eldeki
  123 günle iki beslemeli kıyas yapıldı → EK-5.

## EK-5 (2026-11-14) — HistData saat ekseni düzeltmesi (E135) + iki beslemeli eski dönem kıyası
Dukascopy 2018 indirmesi saatte ~34 gün hızla (503/URLError sabit beklemeleri) 2018-01-01 → 05-23'e ulaştı (123 gün); kalan 1.121 gün
~33 saat sürecekti ve dönem HistData ile zaten kapalı olduğundan durduruldu (`src/duka_fetch.py` kaldığı yerden sürer). Eldeki
123 günle iki besleme kıyaslandı (`src/faz0_duka_vs_histdata_2018.py`, `results/faz0_duka_vs_histdata_2018.json`):
- **Hata bulundu:** kışta gecikme 0 (r 0,97), **yazda −60 dk** (r 0,993; gecikme 0'da 0,14). İlk HistData denetimi yalnız kış
  pencerelerinde (2021 Kasım–Aralık, 2018 başı) yapılmıştı; 2018 başı r 0,72 bir işaretti ama gözden kaçtı.
- **Kural yıla göre farklı:** ham etiket ET'dir; yaz saati 2018 dosyasında **ABD** takvimiyle, 2019–2021 dosyalarında **AB**
  takvimiyle değişir. Kanıt: ABD–AB geçiş pencerelerindeki FOMC/NFP anları (2018-03-21 FOMC etiket 14:00; 2019-03-20, 2019-10-30,
  2021-03-17, 2021-11-03 FOMC 13:00; 2019-11-01, 2021-11-05 NFP 07:30; yaz ortası FOMC'ler her yıl 14:00).
- **Doğrulama (düzeltme sonrası):** gecikme 0 üç pencerede — 2018 kış r 0,969, 2018 yaz r 0,993, 2021 Kasım–Aralık r 1,000; olay
  anları UTC'de 9/11 ilk-2 dakikada, kalan 2 (sakin kış FOMC'leri) ve ek 3 kış FOMC'sinde 19:00 UTC hareketi 18:00'ten büyük (5/5);
  **kapalı saatte kalan bar (R1) 14.176 → 131** (referanstan bağımsız teyit).
- Düzeltilmiş eksende 123 günün tamamı: en iyi gecikme 0, 1m getiri r 0,92 (98.123 ortak bar); kapanış düzey farkı medyan 10,8 bp
  (|fark| p95 24 bp; HistData yukarıda — spot endeks vs CFD), günlük aralık oranı medyan 1,01, 1m |getiri| oranı 0,99 → oynaklık
  ölçüsü bakımından eşdeğer beslemeler.
- Etki: FAZ_5 §6 yeniden koşuldu (15 dk becerisi +0,012/+0,019 → +0,025/+0,034); yön kenarı hükmü değişmedi.
