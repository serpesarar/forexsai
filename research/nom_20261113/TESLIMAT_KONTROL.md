# NOM — prompt ↔ teslimat kontrol listesi (2026-11-14)

Kaynak prompt: `PROMPT_NASDAQ_OLASILIK_MOTORU.md` (repo kökü, 14.541 bayt, 2026-11-13 20:14). Oturumun ilk adımında okundu; fazlar
satır 61 (Faz 0) … 240 (Faz 9), teslimatlar satır 249, DUR koşulları satır 264.

| Prompt maddesi | Durum | Kanıt |
|---|---|---|
| ÖNCE OKU: CLAUDE.md, ndx_reflex_engine, defter, raporlar | ✅ | FAZ_0_RAPOR §0 (yeniden kullanım tablosu) |
| Faz 0.1 envanter (başlangıç-bitiş, bar, boşluk, duplike, hacim, spread, TZ) | ✅ | FAZ_0 §1, `results/faz0_inventory.json` |
| Faz 0.2 kaynak karşılaştırma + hangi dönem hangi kaynak | ✅ | FAZ_0 §2, `faz0_candle_cache_weekly_lag.csv` (E4 teyidi) |
| Faz 0.3 UTC normalizasyon, NY seansı + tatil/yarım gün | ✅ | `data_layer.py`, `backend/services/nom/nyse_calendar.py` |
| Faz 0.4 Dukascopy en eski tarihten | ⚠ kısmi | 2021-11→2026-11 tam; 2026-01 dolduruldu; 2018–21 sunucu engeli (FAZ_0 EK) |
| Faz 0.4 MT5'i bugüne tamamla | ✅ | FAZ_0 EK, `results/faz0_mt5_uzatma.json` |
| Faz 0.4 makro VIX/ES/DXY/TNX/VIX9D/VIX3M/QQQ hacmi | ✅ | `src/macro_fetch.py`, `data/macro/macro_daily.parquet` |
| Faz 0.4 takvim CPI/FOMC/NFP/PCE/bilanço | ✅ (PCE hariç, gerekçeli) | `data/macro/calendar.parquet`, BLS 2026 düzeltmesi |
| Faz 0.5 temizlik kuralları | ✅ | FAZ_0 §3 (R1–R5, vade sıçraması analizi) |
| Faz 0.6 versiyonlu veri katmanı + kalite skoru | ✅ | `data/ndx_1m_v1.parquet`, FAZ_0 §1 |
| Faz 1 triple-barrier, LONG/SHORT ayrı, 5 geometri × 4 ufuk, aynı bar → SL, tick, bid/ask, taban oran | ✅ | FAZ_1, `labels.py`, `faz1_base_rates.csv`, `faz1_tick_ambiguity.csv` |
| Faz 2 özellikler (S/R, momentum, trend, oynaklık, zaman, makro, mikro), HTF kapanmış bar, leakage testi, katalog, permütasyon + SHAP | ✅ | FAZ_2, `features.py`, `faz2_feature_catalog.csv`, `faz2_importance_*.csv`, `tests/test_nom_features.py` |
| Faz 2 MiroShark meta-özellik | ✅ (dışlandı, gerekçeli) | FAZ_2: 21 gün, tamamı final dönemde |
| Faz 3 WF + purged K-fold + ambargo + kilitli final + plasebo + bootstrap | ✅ | FAZ_3, `src/validation.py` |
| Faz 4 tabanlar, LGBM, XGB, yön-koşullu, kalibrasyon, reliability | ✅ | FAZ_4, `faz4_metrics.csv`, `faz4_compare.json`, `plots/dev_reliability_*.svg` |
| Faz 4 derin modeller | ✅ (gerekçeyle bırakıldı) | FAZ_4 (ön kayıt kuralı + ortam) |
| Faz 5 sürtünmeli EV, 2×, eşikler, rejim/yıl dilimleri, bot çapraz kontrolü, final tek açılış | ✅ | FAZ_5, `faz5_dev.json`, `faz5_final.json`, `faz5_skill_slices.json`, `faz5_bot_crosscheck.json`, `FINAL_OPENED.json` |
| Faz 6 API (LONG/SHORT, bağlam, SHAP, NÖTR, sürüm, tazelik), MT5 canlı, train/serve testi, işlem açmaz | ✅ | FAZ_6, `backend/routers/nom_router.py`, `tests/test_nom_engine.py` (11/11) |
| Faz 7 panel (barlar, S/R haritası, RSI/rejim, Neden?, seçiciler, canlı kalibrasyon) | ✅ | FAZ_7, `frontend/app/olasilik-motoru/`, tarayıcı doğrulaması |
| Faz 8 `nom_predictions` (migration + RLS), gölge script, canlı kalibrasyon, mezuniyet | ✅ | FAZ_8, `supabase/migrations/20261113_nom_predictions.sql`, `scripts/nom_shadow.py`, 923 örneklem dışı satır |
| Faz 9 yeniden eğitim + terfi, sürümleme/geri alma, drift | ✅ | FAZ_9, `src/faz9_retrain.py`, `model_store.py`, `drift.py`, `faz9_retrain_dryrun.json`, `faz9_drift_20261113.json` |
| Teslimat 7 README | ✅ | `README.md` |
| Teslimat 8 DÜRÜST SONUÇ | ✅ | FAZ_5 §5 |
| Commit / push | ✅ | `753ae55d` (main) |
Tek açık madde: 2018–21 Dukascopy verisi (sunucu engeli; DUR eşiğinin üstünde 5 yıl veri mevcut).
