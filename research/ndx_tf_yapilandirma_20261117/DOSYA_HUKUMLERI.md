# Dosya hükümleri — diskteki tüm NASDAQ mum dosyaları

Üretici: `src/s06_dosya_hukumleri.py` (`s01_envanter`, `s05_ek_kaynak` sonuçlarından). Her dosya ya bir beslemenin **ana kaynağı**, ya o beslemenin **doğrulanmış kopyası**, ya da **türetilemez / reddedildi**.

## Ana kaynaklar

| Dosya | Besleme | Kullanım |
|---|---|---|
| research/nom_20261113/data/ndx_1m_v3_duka.parquet + aynı klasörün `duka_m1/*.bi5` ham günleri (v3 sonrası 2026-11-13, 11-15; ndx_1m_v1 ile birebir) | DUKA | 1m → 2/3/90/210 |
| research/c1_turev_20261105/data/mt5/NAS100_{M1,M5,M15,M30,H1}.csv.gz | MT5 NAS100 (sunucu saati) | M1 → 2/3; M1/M5/M15/M30 → 90/210; H1 doğrulama |
| research/yon_lab_20261114/data/mt5/NAS100_{M1,M5}.csv.gz | MT5 NAS100 | birleşim (ortak barlar %100) |
| nasdaq_tam_veri_2026-08-29/1m_veri, `nasdaq_tam_veri_2026-08-29 2/1m_veri`, islem_paketi_2026-08-27/NASDAQ/1m_veri | MT5 NAS100 (UTC) | birleşim (ortak barlar %100; '…2' birebir kopya) |
| out/kutu_taze/NAS100_{M1,M5,M15,M30,H1}.csv.gz — 2026-11-17 kutudan (`calistir/arac_nas100_mum_export.py`, Pepperstone-Demo) | MT5 NAS100 | birleşim (eski dosyalarla ortak barlar %100) |
| 1MDATA/mt5_ustec_1m_bars.json, RECOVER/mt5_ustec_1m_bars.json | MT5 USTEC — önceki broker (sunucu saati) | 1m → 2/3/90/210 (iki dosya ortak 77.932 barda %100) |

## Dukascopy kopyaları (ana dosya + ham bi5 kuyruğuyla kıyas)

| Dosya | ortak bar | birebir | ana dosyada olmayan işlem günü |
|---|---|---|---|
| research/nom_20261113/data/ndx_1m_v1.parquet | 2,929,896 | %100.0 | 0 (0 bar) |
| research/nom_20261113/data/ndx_1m_v3.parquet | 2,959,922 | %90.129 (2018: %4.31) | 1 (1 bar; 2017-12-31) |
| research/yon_lab_20261114/data/ndx_1m_v2.parquet | 1,680,535 | %100.0 | 0 (0 bar) |
| research/haber_derin_20261105/data/NDX_1m.parquet | 902,747 | %100.0 | 0 (0 bar) |
| research/nom_20261113/data/histdata_ndx_1m.parquet | 1,329,571 | %78.025 (2018: %4.31) | 1 (1 bar; 2017-12-31) |
| research/fibo_altin_bolge_20261116/cache/ndx_1m.npz | 2,963,071 | satır satır aynı: False | — |

HistData ve onu içeren v3'ün 2018'i farklı besleme (%4 uyum; FAZ_0 E137) → katılmadı. Ham bi5'te ana dosyada olmayan eski günler (2018 Pazar akşamları, tatiller) temizlikten sonra boş: yalnız düz sıfır-hacim dolgu barı.

## MT5 kökenli kopyalar — gün gün MT5'in yerli barıyla birebir sınama

Kabul = o işlem gününün TÜM yerli barları kopyadan kurulan karşılığıyla birebir; tek bar farkı günü reddeder. Kabul edilen 1 dk günleri 2/3 dk'ya katıldı (terminalde olmayan barlar `kaynak_tf=M1_kopya`).

| Dosya | TF | damga | aralık (UTC) | referans | sınanan gün | NAS100 kabul | red | red günlerden USTEC'le birebir |
|---|---|---|---|---|---|---|---|---|
| nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv | 1m | utc | 2026-02-10 → 2026-08-28 | yerli M5 | 143 | 60 | 83 | 43 |
| backend/data/nom_cache/ndx_1m.parquet | 1m | utc | 2026-03-22 → 2026-11-16 | yerli M5 | 171 | 112 | 59 | 33 |
| ndx_reflex_engine/data/ustec_1m_2026.parquet | 1m | sunucu(NY+7) | 2026-02-10 → 2026-07-03 | yerli M5 | 103 | 4 | 99 | 84 |
| research/fcr_ilk_mum_20261027/data/cache_NDX_1m.parquet | 1m | utc | 2026-02-10 → 2026-11-16 | yerli M5 | 199 | 107 | 92 | 43 |
| output/islem_otopsi/_cache/NDX_INDX_1m_raw.parquet | 1m | utc | 2026-06-17 → 2026-11-13 | yerli M5 | 106 | 39 | 67 | 0 |
| research/tp_sonrasi_ters_20261109/data/ndx_1m.parquet | 1m | utc | 2026-06-16 → 2026-11-09 | yerli M5 | 102 | 32 | 70 | 0 |
| research/next_candidates/bars_NDX_INDX_1m.csv | 1m | sunucu(NY+7) | 2026-06-21 → 2026-07-23 | yerli M5 | 24 | 9 | 15 | 0 |
| research/sim_bot/bars_NDX_INDX_1m.json | 1m | sunucu(NY+7) | 2026-05-31 → 2026-07-28 | yerli M5 | 42 | 13 | 29 | 6 |
| research/trade_mgmt_ndx/bars_NAS100.csv | 1m | sunucu(NY+7) | 2026-06-14 → 2026-07-21 | yerli M5 | 27 | 10 | 17 | 0 |
| sr_rejection_research/data/NDX.INDX_1m.json | 1m | sunucu(NY+7) | 2026-02-10 → 2026-06-25 | yerli M5 | 97 | 0 | 97 | 87 |
| 1MDATA/mt5_islem_analizi/nasdaq_1m.csv | 1m | utc | 2026-07-12 → 2026-08-14 | yerli M5 | 25 | 17 | 8 | 0 |
| analiz_paketi_2026-07-09/prices/NDX_INDX_1m_son_14gun.csv | 1m | sunucu(NY+7) | 2026-06-25 → 2026-07-09 | yerli M5 | 11 | 9 | 2 | 0 |
| bot_live_audit/bars/NDX.INDX_5m.json | 5m | sunucu(NY+7) | 2026-06-09 → 2026-06-22 | yerli M5 | 9 | 0 | 9 | 1 |
| research/sim_bot/bars_NDX_INDX_5m.json | 5m | sunucu(NY+7) | 2026-05-31 → 2026-07-28 | yerli M5 | 42 | 25 | 17 | 0 |
| research/dts_uyarlama_20261104/data/cc_NDX_5m.csv | 5m | utc | 2026-07-20 → 2026-11-05 | yerli M5 | 79 | 49 | 30 | 0 |
| sr_rejection_research/data/NDX.INDX_5m.json | 5m | sunucu(NY+7) | 2026-03-17 → 2026-06-25 | yerli M5 | 72 | 0 | 72 | 45 |
| backend/data/candle_history/NDX_5m.npz | 5m | utc | 2025-01-01 → 2026-10-02 | yerli M5 | 312 | 95 | 217 | 61 |
| research/dts_uyarlama_20261104/data/cc_NDX_15m.csv | 15m | utc | 2026-07-20 → 2026-11-05 | yerli M15 | 79 | 39 | 40 | 0 |
| backend/data/candle_history/NDX_15m.npz | 15m | utc | 2023-03-08 → 2026-10-02 | yerli M15 | 925 | 923 | 2 | 0 |
| sr_rejection_research/data/NDX.INDX_30m.json | 30m | sunucu(NY+7) | 2026-03-20 → 2026-06-25 | yerli M30 | 70 | 0 | 70 | 59 |
| backend/data/candle_history/NDX_30m.npz | 30m | utc | 2021-06-29 → 2026-10-02 | yerli M30 | 1362 | 1360 | 2 | 0 |

Birleşime giren kabul günleri: 125 gün, 171,334 bar (2026-05-07 → 2026-11-12); terminalle çakışan her bar birebir (s03 birleşimi dayatır).

Red nedenleri: (1) **USTEC beslemesinin kopyası** — 2026-05-06 öncesi candle_cache ve ondan türeyenler, `sr_rejection_research`, `bot_live_audit` (bazıları `time_utc` etiketli ama sunucu saatinde); NAS100 ile hiçbir kaydırmada eşleşmez, seviye farkı 10–35 puan. USTEC ana kaynağı (json) 2026-06-12'de bittiği için sonraki USTEC günleri tek kopyada kalır ve doğrulanamadığından katılmadı (aşağıdaki sayı). (2) Kaymış dönem: candle_cache 2026-02 → 03-08 +60 dk (E4), 07-08/09 ~12 dk. (3) Yarım gün / eksik dakika kopyaları — tek bar farkı günü reddeder; bu günlerin hepsi terminal M1'inde zaten var. Panel `candle_history` npz'lerinin 15m/30m'si NAS100 yerli barlarının kopyası (yeni gün eklemiyor), 5m'nin 2025'i karışık besleme.

USTEC json bitişinden (06-12) sonra NAS100 ile tutmayan gün: `nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv` 21, `ndx_1m.parquet` 25, `ustec_1m_2026.parquet` 11, `cache_NDX_1m.parquet` 30, `NDX_INDX_1m_raw.parquet` 67, `ndx_1m.parquet` 70, `bars_NDX_INDX_1m.csv` 15, `bars_NDX_INDX_1m.json` 19, `bars_NAS100.csv` 17, `NDX.INDX_1m.json` 9, `nasdaq_1m.csv` 8, `NDX_INDX_1m_son_14gun.csv` 2, `NDX.INDX_5m.json` 6, `bars_NDX_INDX_5m.json` 15, `cc_NDX_5m.csv` 30, `NDX.INDX_5m.json` 9, `NDX_5m.npz` 10, `cc_NDX_15m.csv` 40, `NDX_15m.npz` 1, `NDX.INDX_30m.json` 9, `NDX_30m.npz` 1 — bunlar USTEC'in tek kopyası ya da eksik dakikalı NAS100 kopyası; ikisi de bağımsız referansla sınanamadığı için katılmadı.

## Türetilemez / mum değil

| Dosya | Neden |
|---|---|
| research/fitil_ret_20261106/data_d1_NDX.parquet | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/ndx_kapi_20261110/data/NDX.parquet | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/pythia_20261111/data/NDX.parquet | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/kasa_trend_20261028/data/NDX.csv | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/geri_cekilme_20261106/data/now_NDX.csv | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/yon_lab_20261114/data/xasset/NDX_1d.parquet | günlük (Yahoo ^NDX) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/yon_lab_20261114/data/xasset/NDXF_1h.parquet | 1 sa (NQ vadeli, Yahoo) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/cortex_confluence/data/NQ_1h.csv | 1 sa (NQ vadeli) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/cortex_confluence/intraday/NQ.csv | 1 sa yalnız kapanış (NQ vadeli) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/ndx_long_1h_fixa.parquet | 1 sa (panel) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/ndx_long_1h_fixb.parquet | 1 sa (panel) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| backend/data/candle_history/NDX_1h.npz | 1 sa (panel candle_history) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| backend/data/candle_history/NDX_4h.npz | 4 sa (panel candle_history) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| sr_rejection_research/data/NDX.INDX_1h.json | 1 sa (panel) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |
| research/sim_bot/sig_NDX_INDX.json | mum değil (sinyal listesi) — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |

## Reddedilen her kopya gününün çözümü (`s09`)

Toplam 1097 reddedilen gün; her biri son çıktılardan birinde kapsanıyor:

| Çözüm | Gün |
|---|---|
| MT5_1dk_birlesiminde_tam (2/3/90/210 o günden) | 678 |
| USTEC_beslemesinde (json birebir) | 360 |
| USTEC_beslemesinde + MT5_90/210 (kopya kaymış/eksikti) | 56 |
| MT5_90/210_yerli_barlardan (2/3 dk yok: o gün NAS100 1 dk yok) | 3 |

Kapsanmayan gün: **0**. Gün gün liste: `results/s09_red_gun_cozumu.csv`.

## Ev dizinindeki ek beslemeler — haftalık saat kalibrasyonu (`s08`)

| Besleme | Dosya | TF | hafta kabul | bar kabul | kural(lar) |
|---|---|---|---|---|---|
| EET30 | ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv | 30m | 425/463 | %92.09 | Europe/Athens 425 |
| NQ | ~/Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv | 5m | 245/259 | %94.64 | Europe/Berlin kapanış 111, America/New_York kapanış 98, UTC+1 kapanış 36 |

Reddedilen haftaların tamamında en iyi gecikme 0 (saat doğru) ama r < 0,90 (ince veri / iki ürün farkı); ölçüt gevşetilmedi. Hafta hafta liste: `results/s08_ek_besleme.json`.

## Kutudaki MT5 geçmiş dosyaları `history/NAS100/<YIL>.hcc` (`s12`, salt okuma)

Terminal 100.000 bar sınırı yüzünden copy_rates son ~100 günü veriyordu; diskteki yıl dosyaları ayrıştırıldı (MqlRates, 60 bayt). Gün kabulü: o gün için en ince yerli MT5 barıyla (M5 → M15 → M30 → H1) birebir **ve** gerçekten M1 (medyan aralık 60 sn, dakika ≥ yerli kapsamın %80'i). 2026.hcc terminal kilidinde, okunamadı.

| Yıl | ayrıştırılan bar | sınanan gün | kabul gün | M1 olmayan (H1/D1 kaydı) | referans |
|---|---|---|---|---|---|
| 2009 | 209 | 209 | 0 | 209 | {'60': 209} |
| 2010 | 84 | 84 | 0 | 84 | {'60': 84} |
| 2016 | 4,943 | 216 | 0 | 216 | {'60': 216} |
| 2017 | 193,639 | 257 | 131 | 112 | {'60': 257} |
| 2018 | 345,595 | 257 | 249 | 0 | {'30': 164, '60': 93} |
| 2019 | 347,791 | 257 | 257 | 0 | {'30': 257} |
| 2020 | 348,123 | 259 | 258 | 1 | {'30': 259} |
| 2021 | 352,536 | 259 | 259 | 0 | {'30': 259} |
| 2022 | 353,562 | 258 | 257 | 0 | {'30': 156, '15': 102} |
| 2023 | 352,754 | 258 | 258 | 0 | {'15': 258} |
| 2024 | 354,295 | 259 | 259 | 0 | {'15': 259} |
| 2025 | 352,033 | 258 | 257 | 0 | {'5': 147, '15': 111} |

Toplam kabul edilen M1: 2,964,439 bar.

## Proje dışı (ev dizini) NASDAQ adlı dosyalar (`s10`)

304 dosya. Özet:

| Hüküm | Dosya |
|---|---|
| mum değil (ad: model/sinyal/olay/rapor/temel veri) | 145 |
| türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) | 54 |
| DUKA kopya | 40 |
| mum değil (OHLC sütunu/zaman yok) | 27 |
| türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) | 10 |
| türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA | 9 |
| NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) | 4 |
| arşiv/biçim dışı | 3 |
| çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 100072, DUKA ile eşit %100.0) | 2 |
| çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 70, DUKA ile eşit %92.9) | 2 |
| projedeki backend/models/%80nasdaq_meta_lgb_v2.pkl dosyasının birebir kopyası (md5) | 1 |
| projedeki analiz_paketi_2026-07-09/prices/NDX_INDX_1m_son_14gun.csv dosyasının birebir kopyası (md5) | 1 |
| ANA KAYNAK: NQ beslemesi (haftalık kalibre, reddedilen haftalar s08'de) | 1 |
| ANA KAYNAK: EET30 beslemesi (haftalık kalibre, reddedilen haftalar s08'de) | 1 |
| türetilemez (10080 dk: 2/3/90/210 bundan kurulamaz) | 1 |
| türetilemez (44640 dk: 2/3/90/210 bundan kurulamaz) | 1 |
| çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 70, DUKA ile eşit %100.0) | 1 |
| projedeki nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv dosyasının birebir kopyası (md5) | 1 |

| Dosya | MB | TF | aralık | besleme · saat · r · eşit% | hüküm |
|---|---|---|---|---|---|
| ~/Desktop/Trading Projeleri/HEsaplanmis/HAZIR AILER/%80nasdaq_meta_lgb_v2.pkl | 17.8 |  |  |  | projedeki backend/models/%80nasdaq_meta_lgb_v2.pkl dosyasının birebir kopyası (md5) — orada sınandı |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/NAS100_USD_1D_analyzed.csv | 2.7 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/NAS100_USD_1D_multi_analyzed.csv | 1.9 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD1440_analyzed.csv | 1.8 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD1440_multi_analyzed.csv | 1.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD15_analyzed.csv | 56.9 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD15_multi_analyzed.csv | 38.4 | 1440m | 2021-04-27 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD1_analyzed.csv | 57.0 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD1_multi_analyzed.csv | 38.4 | 1440m | 2025-06-19 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD240_analyzed.csv | 10.2 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD240_multi_analyzed.csv | 6.9 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD30_analyzed.csv | 56.5 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD30_multi_analyzed.csv | 38.1 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD5_analyzed.csv | 56.5 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD5_multi_analyzed.csv | 38.2 | 1440m | 2024-04-10 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD60_analyzed.csv | 37.0 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD60_multi_analyzed.csv | 24.9 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/analyzed/USATECHIDXUSD_multi_analyzed.csv | 6.4 | 1m |  | DUKA · nan · nan · 100.0 | çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 70, DUKA ile eşit %100.0) — yeni veri yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/NAS100_USD_1D.csv | 0.2 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD1.csv | 5.7 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD1440.csv | 0.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD15.csv | 5.8 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD240.csv | 1.0 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD30.csv | 5.7 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD5.csv | 5.7 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/cleaned_data/USATECHIDXUSD60.csv | 3.7 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/NAS100_USD_1D.csv | 0.2 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/NAS100_USD_FULL.csv | 0.0 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD1.csv | 5.5 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD1440.csv | 0.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD15.csv | 5.6 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD240.csv | 1.0 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD30.csv | 5.4 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD5.csv | 5.5 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/data/USATECHIDXUSD60.csv | 3.5 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/fundamentals/USATECHIDXUSD_H1.csv | 2.9 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/fundamentals/USATECHIDXUSD_M1-2.csv | 6.7 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/fundamentals/USATECHIDXUSD_M1.csv | 5.9 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/fundamentals/USEPUFEARINDX.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/merged/USATECHIDXUSD1_multi_timeframe.csv | 5.8 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/merged/USATECHIDXUSD_multi_timeframe.csv | 79.4 | 1m |  | DUKA · nan · nan · 100.0 | çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 100072, DUKA ile eşit %100.0) — yeni veri yok |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/NAS100_USD_1D_analyzed_model.pkl | 3.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/NAS100_USD_1D_model.pkl | 13.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/NAS100_USD_1D_multi_analyzed_model.pkl | 8.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/NAS100_USD_1D_multi_model.pkl | 15.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1440_analyzed_model.pkl | 2.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1440_model.pkl | 9.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1440_multi_analyzed_model.pkl | 6.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1440_multi_model.pkl | 12.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD15_analyzed_model.pkl | 0.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD15_multi_analyzed_model.pkl | 27.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD15_multi_model.pkl | 61.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1_mtf_model.pkl | 1.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1_multi_analyzed_model.pkl | 28.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD1_multi_model.pkl | 64.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD240_analyzed_model.pkl | 2.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD240_multi_analyzed_model.pkl | 13.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD240_multi_model.pkl | 27.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD30_analyzed_model.pkl | 1.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD30_multi_analyzed_model.pkl | 31.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD30_multi_model.pkl | 75.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD5_analyzed_model.pkl | 0.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD5_multi_analyzed_model.pkl | 29.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD5_multi_model.pkl | 67.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD60_analyzed_model.pkl | 2.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD60_multi_analyzed_model.pkl | 26.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/USATECHIDXUSD60_multi_model.pkl | 58.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/models/nasdaq_model.pkl | 10.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/melih2/trading_ai/reports/USATECHIDXUSD1_report.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv | 17.3 | 5m | 2019-08-11 → 2024-08-09 |  | ANA KAYNAK: NQ beslemesi (haftalık kalibre, reddedilen haftalar s08'de) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_backtest_unified_regime_analysis_v1.txt | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_encoders_v1.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_features_v1.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_features_v2.json | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_label_encoders_v2.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_scaler_v1.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_scaler_v2.pkl | 0.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_xgb_v1.pkl | 6.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_event_outcome_xgb_v2.pkl | 4.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_encoders_v2_robust.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_features.pkl | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_features_v2_robust.pkl | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_scaler.pkl | 0.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_scaler_v2_robust.pkl | 0.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_xgb.pkl | 1.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_master_wave_xgb_v2_robust.pkl | 5.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_meta_optuna_cv_v2.pkl | 15.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_news_impact_dir_mid_xgb.pkl | 5.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_news_impact_dir_xgb.pkl | 4.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_news_impact_features.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_news_impact_meta.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_news_impact_scaler.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_playbook_signals_bt_report_v1.txt | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_dir_v3_xgb.pkl | 2.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_dir_xgb.pkl | 1.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_features.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_scaler.pkl | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_v3_features.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/models/nasdaq_wave_v3_scaler.pkl | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq.csv | 231.7 | 1440m | 2016-03-31 → 2021-07-13 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_2010_2024_daily.csv | 0.3 | 1440m | 2010-01-04 → 2024-12-30 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_2010_2024_monthly.csv | 0.0 | 44640m | 2010-01-01 → 2024-12-01 |  | türetilemez (44640 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_2010_2024_weekly.csv | 0.1 | 10080m | 2010-01-01 → 2024-12-27 |  | türetilemez (10080 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv | 5.9 | 30m | 2016-11-15 → 2025-10-01 |  | ANA KAYNAK: EET30 beslemesi (haftalık kalibre, reddedilen haftalar s08'de) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq240.csv | 81.7 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq240_merged.csv | 17.1 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq240_sample300.csv | 1.3 | 1440m | 2013-05-22 → 2013-08-01 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq60.csv | 291.6 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq60_merged.csv | 25.3 | 60m | 2013-05-22 → 2025-10-06 | NQ(ham duvar saati) · nan · nan · 95.67 | NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) — yeni veri yok |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq60_sample300.csv | 1.3 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_30m_ULTIMATE_v1.pkl | 13.6 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_30m_ULTIMATE_v2.pkl | 328.2 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_5m_H1_part.csv | 1.7 | 60m | 2019-08-11 → 2024-08-09 | NQ(ham duvar saati) · nan · nan · 100.0 | NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) — yeni veri yok |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_5m_H4_part.csv | 0.5 | 240m | 2019-08-11 → 2024-08-09 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_5m_M30_part.csv | 3.4 | 30m | 2019-08-11 → 2024-08-09 | NQ(ham duvar saati) · nan · nan · 100.0 | NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) — yeni veri yok |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_M30_merged.csv | 27.9 | 30m | 2016-03-31 → 2024-08-09 | NQ(ham duvar saati) · nan · nan · 99.13 | NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) — yeni veri yok |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_daily.csv | 0.2 | 1440m | 2010-01-04 → 2025-11-20 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_daily_features.parquet | 0.4 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_base_M30_H1_H4.parquet | 8.5 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_base_M30_H1_H4_SYN.parquet | 4.1 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_clean.parquet | 206.7 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_data_TECHNICAL.csv | 67.2 | 1440m | 2016-03-31 → 2016-11-30 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_from5m_clean.parquet | 40.1 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_full_with_daily.parquet | 40.4 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_kernel_full_data.csv | 0.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_kernel_original_data.csv | 0.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_kernel_train_data.csv | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_kernel_valid_data.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/nasdaq_training_dataset_v2.parquet | 107.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_event_outcomes_v1.parquet | 9.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_event_outcomes_with_preds_v1.csv | 126.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_event_outcomes_with_preds_v1.parquet | 22.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_event_outcomes_with_preds_v2.csv | 23337.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_event_outcomes_with_preds_v2.parquet | 1087.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_short_signals_with_model_v1.csv | 4.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_short_signals_with_model_v1.parquet | 0.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_signals_with_model_v1.csv | 20.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_signals_with_model_v1.parquet | 1.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_unified_backtest_regimes_v1.parquet | 0.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_unified_signals_with_model_v1.csv | 37.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_fake_live_unified_signals_with_model_v1.parquet | 2.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_full_wave.parquet | 8.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_full_wave_patterns_sr_v1.parquet | 45.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_full_wave_patterns_v1.parquet | 44.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_full_wave_strength.parquet | 8.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_full_wave_v3.parquet | 40.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_master_features_v1.parquet | 929.5 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_news_impact_events.parquet | 30.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_news_impact_events_FULL.parquet | 56.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_news_short_mid.parquet | 1.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_panel_signals_feed_v1.csv | 6.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_panel_signals_feed_v1.parquet | 0.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_short_signals_from_master_v1.csv | 3.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_short_signals_from_master_v1.parquet | 0.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_signals_bt_v1.csv | 14.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_signals_bt_v1.parquet | 1.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_signals_from_master_v1.csv | 13.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/nasdaq/staging/nasdaq_playbook_signals_from_master_v1.parquet | 0.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_summary_m30.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_summary_m30_h10.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_summary_m30_h20.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_summary_m30_v2_h20.csv | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_trades_m30.parquet | 4.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_trades_m30_h10.parquet | 2.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_trades_m30_h20.parquet | 2.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_backtest_trades_m30_v2_h20.parquet | 5.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_metrics_ywin.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_ml_dataset_m30_h20.parquet | 7.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_ml_scored_m30_h20_time.parquet | 8.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_ml_scored_m30_h20_time_NOLEAK.parquet | 8.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_patterns_out_m30.parquet | 206.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_policy.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_policy.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_policy_metrics_m30_v2_h20.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_policy_trades_m30_v2_h20.csv | 0.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_policy_trades_m30_v2_h20.parquet | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Trading Projeleri/video/nasdaq_scored_FINAL.parquet | 8.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/EKSIKLER/USATECHIDXUSD_H1.csv | 2.9 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/EKSIKLER/USATECHIDXUSD_M1-2.csv | 6.7 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/EKSIKLER/USATECHIDXUSD_M1.csv | 5.9 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/EKSIKLER/USEPUFEARINDX.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/fundamental_data/USATECHIDXUSD_H1.csv | 2.9 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/fundamental_data/USATECHIDXUSD_M1-2.csv | 6.7 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/fundamental_data/USATECHIDXUSD_M1.csv | 5.9 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/fundamental_data/USEPUFEARINDX.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD1440_multi_analyzed.csv | 14.4 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD15_multi_analyzed.csv | 425.7 | 1440m | 2021-04-27 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD1_multi_analyzed.csv | 422.3 | 1440m | 2025-06-19 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD30_RECALCULATED.csv | 431.0 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD30_multi_analyzed.csv | 430.5 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD30_multi_analyzed_BACKUP.csv | 428.1 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ/price_data/USATECHIDXUSD5_multi_analyzed.csv | 421.7 | 1440m | 2024-04-10 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/NASDAQ.zip | 4373.3 |  |  |  | arşiv/biçim dışı — içeriği diskte açık kopya olarak ayrıca sınandı |
| ~/Desktop/Uygulama Projeleri/PROJELER/nasdaq.txt | 0.0 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/NAS100_USD_1D_analyzed.csv | 23.3 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/NAS100_USD_1D_multi_analyzed.csv | 22.4 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD1440_analyzed.csv | 14.9 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD1440_multi_analyzed.csv | 14.4 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD15_analyzed.csv | 449.2 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9975 · 99.77 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD15_multi_analyzed.csv | 425.7 | 1440m | 2021-04-27 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD1_analyzed.csv | 445.3 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 0.9984 · 99.8 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD1_multi_analyzed.csv | 422.3 | 1440m | 2025-06-19 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD240_analyzed.csv | 85.9 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD240_multi_analyzed.csv | 81.7 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD30_analyzed.csv | 454.0 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9992 · 99.77 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD30_multi_analyzed.csv | 430.5 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD5_analyzed.csv | 445.3 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 0.9925 · 99.78 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD5_multi_analyzed.csv | 421.7 | 1440m | 2024-04-10 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD60_analyzed.csv | 306.9 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.8 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD60_multi_analyzed.csv | 291.6 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed/USATECHIDXUSD_multi_analyzed.csv | 9.1 | 1m |  | DUKA · nan · nan · 92.86 | çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 70, DUKA ile eşit %92.9) — yeni veri yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/NAS100_USD_1D_analyzed.csv | 23.3 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/NAS100_USD_1D_multi_analyzed.csv | 22.4 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD1440_analyzed.csv | 14.9 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD1440_multi_analyzed.csv | 14.4 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD15_analyzed.csv | 449.2 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9975 · 99.77 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD15_multi_analyzed.csv | 425.7 | 1440m | 2021-04-27 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD1_analyzed.csv | 445.3 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 0.9984 · 99.8 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD1_multi_analyzed.csv | 422.3 | 1440m | 2025-06-19 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD240_analyzed.csv | 85.9 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD240_multi_analyzed.csv | 81.7 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD30_analyzed.csv | 454.0 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9992 · 99.77 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD30_multi_analyzed.csv | 430.5 | 1440m | 2016-03-31 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD5_analyzed.csv | 445.3 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 0.9925 · 99.78 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD5_multi_analyzed.csv | 421.7 | 1440m | 2024-04-10 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD60_analyzed.csv | 306.9 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.8 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD60_multi_analyzed.csv | 291.6 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/analyzed 2/USATECHIDXUSD_multi_analyzed.csv | 9.1 | 1m |  | DUKA · nan · nan · 92.86 | çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 70, DUKA ile eşit %92.9) — yeni veri yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/NAS100_USD_1D.csv | 0.2 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD1.csv | 5.7 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD1440.csv | 0.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD15.csv | 5.8 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD240.csv | 1.0 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD30.csv | 5.7 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD5.csv | 5.7 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/cleaned_data/USATECHIDXUSD60.csv | 3.7 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/NAS100_USD_1D.csv | 0.2 | 1440m | 2006-08-01 → 2025-10-05 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/NAS100_USD_FULL.csv | 0.0 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD1.csv | 5.5 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD1440.csv | 0.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD15.csv | 5.6 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD240.csv | 1.0 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD30.csv | 5.4 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD5.csv | 5.5 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/data/USATECHIDXUSD60.csv | 3.5 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/fundamentals/USATECHIDXUSD_H1.csv | 2.9 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/fundamentals/USATECHIDXUSD_M1-2.csv | 6.7 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/fundamentals/USATECHIDXUSD_M1.csv | 5.9 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/fundamentals/USEPUFEARINDX.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/merged/USATECHIDXUSD1_multi_timeframe.csv | 5.8 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/merged/USATECHIDXUSD_multi_timeframe.csv | 79.4 | 1m |  | DUKA · nan · nan · 100.0 | çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı 100072, DUKA ile eşit %100.0) — yeni veri yok |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/NAS100_USD_1D_analyzed_model.pkl | 3.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/NAS100_USD_1D_model.pkl | 13.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/NAS100_USD_1D_multi_analyzed_model.pkl | 8.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/NAS100_USD_1D_multi_model.pkl | 15.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1440_analyzed_model.pkl | 2.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1440_model.pkl | 9.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1440_multi_analyzed_model.pkl | 6.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1440_multi_model.pkl | 12.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD15_analyzed_model.pkl | 0.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD15_multi_analyzed_model.pkl | 27.2 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD15_multi_model.pkl | 61.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1_mtf_model.pkl | 1.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1_multi_analyzed_model.pkl | 28.4 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD1_multi_model.pkl | 64.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD240_analyzed_model.pkl | 2.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD240_multi_analyzed_model.pkl | 13.7 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD240_multi_model.pkl | 27.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD30_analyzed_model.pkl | 1.9 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD30_multi_analyzed_model.pkl | 31.8 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD30_multi_model.pkl | 75.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD5_analyzed_model.pkl | 0.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD5_multi_analyzed_model.pkl | 29.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD5_multi_model.pkl | 67.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD60_analyzed_model.pkl | 2.3 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD60_multi_analyzed_model.pkl | 26.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/USATECHIDXUSD60_multi_model.pkl | 58.5 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/models/nasdaq_model.pkl | 10.6 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/trading_ai/reports/USATECHIDXUSD1_report.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Desktop/Uygulama Projeleri/PROJELER/yedektradingai/reports/USATECHIDXUSD1_report.json | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Downloads/INDX_LIST_OF_SYMBOLS.csv | 0.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Downloads/USATECHIDXUSD1.csv | 5.6 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Downloads/USATECHIDXUSD1440.csv | 0.2 | 1440m | 2013-05-22 → 2025-10-06 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Downloads/USATECHIDXUSD15.csv | 5.7 | 15m | 2021-04-27 → 2025-10-06 | DUKA · UTC · 0.9997 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Downloads/USATECHIDXUSD240.csv | 1.0 | 240m | 2013-05-22 → 2025-10-06 |  | türetilemez (240 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Downloads/USATECHIDXUSD30.csv | 5.5 | 30m | 2016-03-31 → 2025-10-06 | DUKA · UTC · 0.9999 · 99.97 | DUKA kopya — yeni gün yok |
| ~/Downloads/USATECHIDXUSD30_FIXED_V2.csv | 231.7 | 1440m | 2016-03-31 → 2021-07-13 |  | türetilemez (1440 dk: 2/3/90/210 bundan kurulamaz) |
| ~/Downloads/USATECHIDXUSD5.csv | 5.6 | 5m | 2024-04-10 → 2025-10-06 | DUKA · UTC · 1.0 · 99.98 | DUKA kopya — yeni gün yok |
| ~/Downloads/USATECHIDXUSD60.csv | 3.6 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Downloads/USATECHIDXUSD_H1.csv | 4.3 | 60m | 2013-05-22 → 2025-10-06 | DUKA · UTC · 1.0 · 99.95 | türetilemez (60 dk: 90/210 bunun katı değil) · kimlik DUKA |
| ~/Downloads/USATECHIDXUSD_M1-2.csv | 6.8 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Downloads/USATECHIDXUSD_M1.csv | 6.0 | 1m | 2025-06-19 → 2025-10-06 | DUKA · UTC · 1.0 · 100.0 | DUKA kopya — yeni gün yok |
| ~/Downloads/USEPUFEARINDX.csv | 0.0 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/Downloads/analiz_paketi_2026-07-09/prices/NDX_INDX_1m_son_14gun.csv | 0.9 |  |  |  | projedeki analiz_paketi_2026-07-09/prices/NDX_INDX_1m_son_14gun.csv dosyasının birebir kopyası (md5) — orada sınandı |
| ~/Downloads/data/5 min/us/nasdaq etfs/bndx.us.txt | 0.5 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Downloads/data/5 min/us/nasdaq stocks/2/sndx.us.txt | 0.5 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Downloads/data/5 min/us/nyse etfs/1/fndx.us.txt | 0.5 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Downloads/data/5 min/us/nyse stocks/2/nqp.us.txt | 0.2 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Downloads/nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv | 12.4 |  |  |  | projedeki nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv dosyasının birebir kopyası (md5) — orada sınandı |
| ~/Downloads/nasdaq_1m_candle_cache_20260210_20260829.zip | 2.8 |  |  |  | arşiv/biçim dışı — içeriği diskte açık kopya olarak ayrıca sınandı |
| ~/Downloads/nasdaq_30m_ULTIMATE/nasdaq_30m_ULTIMATE_v1.pkl | 13.6 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
| ~/Downloads/nasdaq_30m_ULTIMATE.zip | 4.5 |  |  |  | arşiv/biçim dışı — içeriği diskte açık kopya olarak ayrıca sınandı |
| ~/Downloads/nasdaq_trades_history.csv | 7.1 |  |  |  | mum değil (ad: model/sinyal/olay/rapor/temel veri) |
| ~/download/usatechidxusd-tick-2025-01-01-2025-12-31.csv | 482.3 |  |  |  | mum değil (OHLC sütunu/zaman yok) |
