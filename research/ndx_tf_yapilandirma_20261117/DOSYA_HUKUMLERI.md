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
