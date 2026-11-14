# NOM — prompt ↔ teslimat kontrol listesi (2026-11-14)

Kaynak prompt: `PROMPT_NASDAQ_OLASILIK_MOTORU.md` (repo kökü, 14.541 bayt, 2026-11-13 20:14). Oturumun ilk adımında okundu; fazlar
satır 61 (Faz 0) … 240 (Faz 9), teslimatlar satır 249, DUR koşulları satır 264.

| Prompt maddesi | Durum | Kanıt |
|---|---|---|
| ÖNCE OKU: CLAUDE.md, ndx_reflex_engine, defter, raporlar | ✅ | FAZ_0_RAPOR §0 (yeniden kullanım tablosu) |
| Faz 0.1 envanter (başlangıç-bitiş, bar, boşluk, duplike, hacim, spread, TZ) | ✅ | FAZ_0 §1, `results/faz0_inventory.json` |
| Faz 0.2 kaynak karşılaştırma + hangi dönem hangi kaynak | ✅ | FAZ_0 §2, `faz0_candle_cache_weekly_lag.csv` (E4 teyidi); 1MDATA broker saatinde, −180 dk'da MT5 ile r 0,999 (FAZ_0 EK-4) |
| Faz 0.3 UTC normalizasyon, NY seansı + tatil/yarım gün (`pandas_market_calendars`) | ✅ | `data_layer.py`, `nyse_calendar.py`; XNYS kütüphanesiyle 2018–26 87 tatil + 20 yarım gün birebir (FAZ_0 EK-4, `faz0_takvim_1mdata.json`) |
| Faz 0.4 en eski tarihten çok yıllı 1m (2020 çöküşü dahil) | ✅ | Dukascopy 2021-11→2026-11 + 2026-01 dolgusu; **2018-01→2021-10 HistData** (1,31 M bar) — FAZ_0 EK-3; saat ekseni kış+yaz+geçiş haftalarında doğrulandı ve yaz kayması düzeltildi (EK-5, E135), Dukascopy 2018 Oca–May ile iki beslemeli kıyas `faz0_duka_vs_histdata_2018.json` |
| Faz 0.4 MT5'i bugüne tamamla | ✅ | FAZ_0 EK, `results/faz0_mt5_uzatma.json` |
| Faz 0.4 makro VIX/ES/DXY/TNX/VIX9D/VIX3M/QQQ hacmi | ✅ | `src/macro_fetch.py`, `data/macro/macro_daily.parquet` |
| Faz 0.4 takvim CPI/FOMC/NFP/PCE/bilanço | ✅ | `data/macro/calendar.parquet`, BLS 2026 düzeltmesi; PCE 105 tarih ALFRED'den (FAZ_0 EK-4; model olay özellikleri FOMC/CPI/NFP/EARN, PCE canlı bağlamda) |
| Faz 0.5 temizlik kuralları | ✅ | FAZ_0 §3 (R1–R5, vade sıçraması analizi) |
| Faz 0.6 versiyonlu veri katmanı + kalite skoru | ✅ | `data/ndx_1m_v1.parquet`, FAZ_0 §1 |
| Faz 1 triple-barrier, LONG/SHORT ayrı, 5 geometri × 4 ufuk, aynı bar → SL, tick, bid/ask, taban oran | ✅ | FAZ_1, `labels.py`, `faz1_base_rates.csv`, `faz1_tick_ambiguity.csv` |
| Faz 2 özellikler (S/R, momentum, trend, oynaklık, zaman, makro, mikro), HTF kapanmış bar, leakage testi, katalog, permütasyon + SHAP | ✅ | FAZ_2, `features.py`, `faz2_feature_catalog.csv`, `faz2_importance_*.csv`, `tests/test_nom_features.py` |
| Faz 2 MiroShark meta-özellik | ✅ (dışlandı, gerekçeli) | FAZ_2: 21 gün, tamamı final dönemde |
| Faz 3 WF + purged K-fold + ambargo + kilitli final + plasebo + bootstrap | ✅ | FAZ_3, `src/validation.py`; Purged K-Fold KOŞULDU 6/6 kat + (1 s +0,013, 4 s +0,021 ≈ WF) — FAZ_3 EK, `faz34_ek.json` |
| Faz 4 tabanlar, LGBM, XGB, yön-koşullu, kalibrasyon, reliability | ✅ | FAZ_4, `faz4_metrics.csv`, `faz4_compare.json`, `plots/dev_reliability_*.svg` |
| Faz 4 CatBoost + ensemble | ✅ | FAZ_4 EK, `faz34_ek.json`: CatBoost ≈ LGB, LGB+Cat ortalaması +0,002/+0,004 (üretime alınmadı, gerekçe FAZ_4 EK) |
| Faz 4 derin modeller (TCN/LSTM/Transformer) | ✅ (DENENDİ, boosting'i geçemedi → bırakıldı) | FAZ_4 EK, `src/deep_nets.py`, `src/faz4_deep.py`, `faz4_deep.json` |
| Faz 5 sürtünmeli EV, 2×, eşikler, rejim/yıl dilimleri, bot çapraz kontrolü, final tek açılış, 2020 çöküşü dahil bağımsız eski dönem (düzeltilmiş eksenle yeniden koşuldu) | ✅ | FAZ_5, `faz5_dev.json`, `faz5_final.json`, `faz5_skill_slices.json`, `faz5_bot_crosscheck.json`, `FINAL_OPENED.json` |
| Faz 6 API (LONG/SHORT, bağlam, SHAP, NÖTR, sürüm, tazelik), MT5 canlı, train/serve testi, işlem açmaz | ✅ | FAZ_6, `backend/routers/nom_router.py`, `tests/test_nom_engine.py` (11/11) |
| Faz 7 panel (barlar, S/R haritası, RSI/rejim, Neden?, seçiciler, canlı kalibrasyon) | ✅ | FAZ_7, `frontend/app/olasilik-motoru/`, tarayıcı doğrulaması |
| Faz 8 `nom_predictions` (migration + RLS), gölge script, canlı kalibrasyon, mezuniyet | ✅ | FAZ_8, `supabase/migrations/20261113_nom_predictions.sql`, `scripts/nom_shadow.py`, 923 örneklem dışı satır |
| Faz 9 yeniden eğitim + terfi, sürümleme/geri alma, drift | ✅ | FAZ_9, `src/faz9_retrain.py`, `model_store.py`, `drift.py`, `faz9_retrain_dryrun.json`, `faz9_drift_20261113.json` |
| Teslimat 7 README | ✅ | `README.md` |
| Teslimat 8 DÜRÜST SONUÇ | ✅ | FAZ_5 §5 |
| Commit / push | ✅ | `753ae55d` (main) + 2026-11-14 tamamlama commit'leri (`git log -- research/nom_20261113`) |
Açık madde yok. (2018–21 Dukascopy sunucu engeline takıldı: 2018-05-23'e kadar indirildi, kalan ~33 saatlik indirme durduruldu; dönem kullanıcı onayıyla HistData'dan tamamlandı ve iki besleme çakışan 123 günde kıyaslandı, FAZ_0 EK-3/EK-5.)

## DUR koşulları — prompt satır 264–273, tek tek (2026-11-14)
| DUR koşulu (prompt) | Tetiklendi mi | Kanıt |
|---|---|---|
| Faz 0'da kullanılabilir NASDAQ verisi < 2 yıl **ve** Dukascopy indirmesi başarısız | **Hayır** | Dukascopy 1m 2021-11-01 → 2026-11-03 = 5,0 yıl (FAZ_0 §1 tablosu, 1,64 M bar) + MT5 ile 2026-11'e uzatıldı (EK, r 0,996); 2018-01 → 2021-10 HistData (EK-3/EK-5). Dukascopy 2018–21 indirmesi engelli ama yavaş ilerliyor (aşağıda) — durma eşiği olan "< 2 yıl" hiç oluşmadı. |
| Final test WF'den dramatik kötü (overfit) | **Hayır** | FAZ_5 §3: final Brier becerisi 15 dk +0,049 (WF +0,059), 1 s +0,022 (+0,015), 4 s +0,038 (+0,011), seans +0,082 (−0,001) → kötü değil. Kalibrasyon eğimi düşüşü (0,54–0,68) raporlandı; final setle ayar **yapılmadı** (`FINAL_OPENED.json`: tek açılış, önceki deneme yalnız çökme). |
| Canlı sistem / mevcut bot / production DB'yi **değiştiren** adım | **Hayır** | NOM commit'leri (`753ae55d`, `35d503d6`, `da0c6711`, `fba87720`, `e247c419`) `yeni deneme/`, `claude_decider/`, `remote_agent/` dosyalarına dokunmuyor (git show ile denetlendi). Backend'e yalnız yeni salt-okur router + `main.py`'de **varsayılan KAPALI** gölge döngüsü (`NOM_SHADOW_ENABLED=0`); Supabase'e yalnız yeni tablo `nom_predictions` (prompt'un izin verdiği istisna). `prediction_logs`/sinyal kapılarına bağlantı yok. |
| Ücretli veri kaynağı / API anahtarı | **Hayır** | Dukascopy, HistData, yfinance, ALFRED/FRED, BLS — hepsi ücretsiz, anahtarsız. |

## Teslimatlar 1–8 — yeniden doğrulama (2026-11-14)
1 raporlar `FAZ_0…9_RAPOR.md` (10 dosya) · 2 `data/ndx_1m_v1.parquet` + FAZ_0 kalite skoru · 3 FAZ_1 + FAZ_2 (leakage kesme/bozma testi
geçti) · 4 FAZ_4/5 (iklim + kural tabanı, `plots/*reliability*.svg`, sürtünmeli ve 2× EV, yıl/rejim dilimleri, P1/P2 plasebo, gün-blok
bootstrap, final) · 5 `/api/probability/nasdaq` + `/olasilik-motoru` + `nom_predictions` + `backend/scripts/nom_shadow.py` · 6
`pytest backend/tests/test_nom_*.py` → **11 passed** (bugün yeniden koşuldu) · 7 `README.md` (yeni betikler eklendi) · 8 FAZ_5 §5 DÜRÜST SONUÇ.

## Faz 0.4 Dukascopy "mümkün olan en eski tarihten" — durum
Dukascopy sunucusu bu IP'ye 503/URLError ile hız sınırı uyguluyor (saatte ~34–60 dosya). 2018-01-01 → 2018-05-23 indi (123 gün);
indirici kaldığı yerden yeniden başlatıldı (`logs/duka_fetch_bid5.log`, `src/duka_fetch.py`, 50 sn aralık). Tamamlanınca
`src/faz0_duka_vs_histdata_2018.py` tüm 2018-01 → 2021-10 için yeniden koşulacak ve eski dönem değerlendirmesi Dukascopy ile de
tekrarlanacak. O zamana kadar aynı dönem, saat ekseni üç pencerede doğrulanmış HistData ile kapsanıyor (FAZ_0 EK-5).
