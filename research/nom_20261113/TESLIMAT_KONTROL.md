# NOM — prompt ↔ teslimat kontrol listesi (2026-11-14)

Kaynak prompt: `PROMPT_NASDAQ_OLASILIK_MOTORU.md` (repo kökü, 14.541 bayt, 2026-11-13 20:14). Oturumun ilk adımında okundu; fazlar
satır 61 (Faz 0) … 240 (Faz 9), teslimatlar satır 249, DUR koşulları satır 264.

| Prompt maddesi | Durum | Kanıt |
|---|---|---|
| ÖNCE OKU: CLAUDE.md, ndx_reflex_engine, defter, raporlar | ✅ | FAZ_0_RAPOR §0 (yeniden kullanım tablosu) |
| Faz 0.1 envanter (başlangıç-bitiş, bar, boşluk, duplike, hacim, spread, TZ) | ✅ | FAZ_0 §1, `results/faz0_inventory.json` |
| Faz 0.2 kaynak karşılaştırma + hangi dönem hangi kaynak | ✅ | FAZ_0 §2, `faz0_candle_cache_weekly_lag.csv` (E4 teyidi); 1MDATA broker saatinde, −180 dk'da MT5 ile r 0,999 (FAZ_0 EK-4) |
| Faz 0.3 UTC normalizasyon, NY seansı + tatil/yarım gün (`pandas_market_calendars`) | ✅ | `data_layer.py`, `nyse_calendar.py`; XNYS kütüphanesiyle 2018–26 87 tatil + 20 yarım gün birebir (FAZ_0 EK-4, `faz0_takvim_1mdata.json`) |
| Faz 0.4 en eski tarihten çok yıllı 1m (2020 çöküşü dahil) | ✅ | Dukascopy 2021-11→2026-11 + 2026-01 dolgusu; **2018-01→2021-10 HistData** (1,31 M bar) — FAZ_0 EK-3; saat ekseni kış+yaz+geçiş haftalarında doğrulandı ve yaz kayması düzeltildi (EK-5, E135), **Dukascopy 2018-01→2021-10 de tam indi** (1.200/1.200 gün); iki besleme tüm dönemde kıyaslandı `faz0_duka_vs_histdata_2018_2021.json`, eski dönem Dukascopy ile de değerlendirildi `faz0_v3_eski_donem_duka.json` (EK-6) |
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
Açık madde yok. (Dukascopy 2018–21 indirmesi 2026-11-16'da tamamlandı; iki besleme tüm dönemde kıyaslandı ve eski dönem değerlendirmesi Dukascopy ile de koşuldu — FAZ_0 EK-6, FAZ_5 §6.)

## DUR koşulları — prompt satır 264–273, tek tek (2026-11-14)
| DUR koşulu (prompt) | Tetiklendi mi | Kanıt |
|---|---|---|
| Faz 0'da kullanılabilir NASDAQ verisi < 2 yıl **ve** Dukascopy indirmesi başarısız | **Hayır** | Dukascopy 1m 2021-11-01 → 2026-11-03 = 5,0 yıl (FAZ_0 §1 tablosu, 1,64 M bar) + MT5 ile 2026-11'e uzatıldı (EK, r 0,996); 2018-01 → 2021-10 HistData (EK-3/EK-5). Dukascopy 2018–21 de tamamlandı (EK-6) → Dukascopy toplam 8,8 yıl; durma eşiği olan "< 2 yıl" hiç oluşmadı. |
| Final test WF'den dramatik kötü (overfit) | **Hayır** | FAZ_5 §3: final Brier becerisi 15 dk +0,049 (WF +0,059), 1 s +0,022 (+0,015), 4 s +0,038 (+0,011), seans +0,082 (−0,001) → kötü değil. Kalibrasyon eğimi düşüşü (0,54–0,68) raporlandı; final setle ayar **yapılmadı** (`FINAL_OPENED.json`: tek açılış, önceki deneme yalnız çökme). |
| Canlı sistem / mevcut bot / production DB'yi **değiştiren** adım | **Hayır** | NOM commit'leri (`753ae55d`, `35d503d6`, `da0c6711`, `fba87720`, `e247c419`) `yeni deneme/`, `claude_decider/`, `remote_agent/` dosyalarına dokunmuyor (git show ile denetlendi). Backend'e yalnız yeni salt-okur router + `main.py`'de **varsayılan KAPALI** gölge döngüsü (`NOM_SHADOW_ENABLED=0`); Supabase'e yalnız yeni tablo `nom_predictions` (prompt'un izin verdiği istisna). `prediction_logs`/sinyal kapılarına bağlantı yok. |
| Ücretli veri kaynağı / API anahtarı | **Hayır** | Dukascopy, HistData, yfinance, ALFRED/FRED, BLS — hepsi ücretsiz, anahtarsız. |

## Teslimatlar 1–8 — yeniden doğrulama (2026-11-14)
1 raporlar `FAZ_0…9_RAPOR.md` (10 dosya) · 2 `data/ndx_1m_v1.parquet` + FAZ_0 kalite skoru · 3 FAZ_1 + FAZ_2 (leakage kesme/bozma testi
geçti) · 4 FAZ_4/5 (iklim + kural tabanı, `plots/*reliability*.svg`, sürtünmeli ve 2× EV, yıl/rejim dilimleri, P1/P2 plasebo, gün-blok
bootstrap, final) · 5 `/api/probability/nasdaq` + `/olasilik-motoru` + `nom_predictions` + `backend/scripts/nom_shadow.py` · 6
`pytest backend/tests/test_nom_*.py` → **11 passed** (bugün yeniden koşuldu) · 7 `README.md` (yeni betikler eklendi) · 8 FAZ_5 §5 DÜRÜST SONUÇ.

## Faz 0.4 Dukascopy "mümkün olan en eski tarihten" — durum: ✅ TAMAMLANDI (2026-11-16)
1.200/1.200 gün dosyası (2018-01-01 → 2021-10-31; eksik 0, boş 0) indi; Dukascopy 1m kapsamı artık **2018-01-01 → 2026-11 (8,8 yıl)**:
2020 çöküşü, 2022 ayı, 2023-25 boğa dahil. İki besleme tüm dönemde kıyaslandı (`results/faz0_duka_vs_histdata_2018_2021.json`,
FAZ_0 EK-6): gecikme 4 yılın 4'ünde 0; HistData 2019–21 = Dukascopy (birebir), 2018 farklı besleme (r 0,96, 12,8 bp). Eski dönem
değerlendirmesi Dukascopy ile tekrarlandı (`results/faz0_v3_eski_donem_duka.json`, FAZ_5 §6 ek tablo): beceri farkı ≤ 0,006, hüküm aynı.

## Yeniden doğrulama (2026-11-16, Dukascopy tamamlandıktan sonra) — prompt maddesi → dosyadaki kanıt
| Faz | Prompt maddesi | Bugün bakılan kanıt |
|---|---|---|
| 1 | triple-barrier ATR katı, LONG/SHORT ayrı, 5 geometri × 4 ufuk, aynı bar → SL, bid/ask giriş, taban oran | FAZ_1 §taban oranlar; `results/faz1_base_rates.csv`, `faz1_tick_ambiguity.*`; test `test_same_bar_is_sl`, `test_entry_includes_friction_and_tp` |
| 2 | kapanmış bar kuralı + otomatik sızıntı testi, katalog, permütasyon + SHAP, MiroShark kararı | `results/faz2_feature_catalog.csv`, `faz2_leak_real.json`, `faz2_importance_*.csv` (4 hedef); MiroShark: 21 gün, tamamı final dönemde → kullanılmadı (FAZ_2 §18-19); testler `test_truncation_equivalence`, `test_future_perturbation`, `test_macro_not_visible_before_1715_et` |
| 3 | WF + Purged K-Fold (ambargo ≥ en uzun ufuk), final kilit, eğitimde ölçekleyici/eşik, P1/P2 plasebo, bootstrap | FAZ_3 tablosu (`EMBARGO_S=86400`, `assert_not_final`), `results/FINAL_OPENED.json`, `faz34_ek.json` (Purged K-Fold 6 kat) |
| 4 | tabanlar, LGB/CatBoost/XGB, ayrı vs yön-koşullu, derin modeller, ensemble, isotonic, Brier/log-loss/AUC/reliability, kantil kalibrasyon | FAZ_4 + EK; `results/plots/dev_reliability_{15m,1h,4h,session}.svg`; `faz4_deep.json` (LSTM/TCN/Transformer 18/18 LGB altında → bırakıldı) |
| 5 | sürtünmeli + 2× EV, 0,55/0,60/0,65 eşik akışı (n, WR, EV, PF, maxDD, kayıp serisi), rejim/yıl dilimleri, bot çapraz kontrol, final tek kez | `results/faz5_dev.json` (40 hedef; alanlar `ev_r`, `pf`, `max_dd_r`, `max_loss_streak`, `base_ev_r_2x`); `faz5_bot_crosscheck.json` (281 işlem, AUC 0,544 < perm p95 0,571); `faz5_final.json`, `plots/final_reliability_*.svg`; eski dönem iki kaynakla (§6) |
| 6 | `GET /probability/nasdaq` LONG/SHORT P, beklenen R, bağlam (3 destek/3 direnç, RSI, rejim, seans, VIX, olay), SHAP 5 faktör Türkçe, NÖTR durumu, sürüm + tazelik, bayatsa tahmin yok, train/serve testi, emir yok | `backend/routers/nom_router.py` (`/api/probability/nasdaq` + takma ad), `services/nom/engine.py` (`STALE_S`, `VERI_BAYAT`, `NÖTR / belirsiz`, `pred_contrib` SHAP); testler `test_predict_structure`, `test_stale_and_closed`, `test_bad_inputs`, `test_router` |
| 7 | panel: LONG/SHORT barları + %95 aralık, S/R haritası, RSI/rejim, "Neden?", geometri/ufuk seçici, canlı kalibrasyon grafiği | `frontend/app/olasilik-motoru/page.tsx`, `components/nom/ProbabilityEnginePanel.tsx` (kova %95 `ci_lo–ci_hi`, WF bandı vs canlı SVG), `lib/api/nom.ts` |
| 8 | `nom_predictions` migration + RLS, outcome yazımı, gölge betiği, canlı kalibrasyon raporu, mezuniyet kriteri | `supabase/migrations/20261113_nom_predictions.sql`, `backend/scripts/nom_shadow.py`, `services/nom/{shadow,calibration}.py`, FAZ_8 §mezuniyet (≥4 hafta, tercihen 8, yüksek VIX haftası) |
| 9 | yeniden eğitim → WF → yalnız geçerse terfi, sürüm + geri alma, drift | `src/faz9_retrain.py` (terfi kuralı), `services/nom/model_store.py` (`promote`, `rollback`; test `test_promote_rollback`), `services/nom/drift.py` (PSI, destek dışı oranı) + `calibration.py` (`DRIFT_DROP`) |

Testler bugün yeniden koşuldu: `pytest backend/tests/test_nom_engine.py backend/tests/test_nom_features.py` → **11 passed**.

### Çalıştırarak doğrulama (2026-11-16, ~20:40 UTC) — dosya taraması değil, koşu
- **Faz 1 (yeniden hesap):** `data/labels_15m.parquet` → 15m long 1/1: n 320.402, P(TP) 0,1833, P(SL) 0,5121, P(zaman) 0,3046, EV −0,418R
  = `results/faz1_base_rates.csv` ALL satırı **birebir**.
- **Faz 5 final (yeniden hesap, yeniden AÇILMADAN):** `results/final/*.parquet` (40 hedef) kayıtlı tahminlerinden ufuk başına 10 hedef
  ortalaması: Brier becerisi 15 dk +0,049 · 1 s +0,022 · 4 s +0,038 · seans +0,082; AUC TP model/iklim 0,609/0,597 · 0,625/0,624 ·
  0,662/0,650 · 0,725/0,721 → FAZ_5 §3 tablosu **birebir**. Final kilidi tek kez açıldı; yeniden eğitim/ayar yapılmadı.
- **Faz 6 (canlı API):** `backend-nom-test` (port 8081) ayağa kaldırıldı; `GET /api/probability/nasdaq` 1h/1.5x1, 15m/1x1, 4h/1x1 →
  200; son bar 20:40 UTC (gecikme 67–80 sn), durum **NÖTR / belirsiz**, LONG/SHORT P(TP/SL/zaman) + beklenen R + %95 kova bandı,
  bağlam (3 destek/3 direnç ATR uzaklık + test sayısı, RSI M5–D1 ve 70/30 uzaklığı, rejim, seans, VIX 19,3, yaklaşan olay
  EARN_NVDA), SHAP 5 faktör Türkçe, sürüm `nom_v1b_20261113`; takma ad `/probability/nasdaq` → 200.
- **Faz 7 (panel render):** `frontend-nom-test` (3013) `/olasilik-motoru` tarayıcıda açıldı: LONG/SHORT barları, %95 aralık,
  "Neden?" 5 faktör, S/R haritası, RSI/rejim, VIX, olay, canlı kalibrasyon grafiği (WF bandı vs canlı). Ufuk seçici "4 saat"
  tıklandı → ATR birimi M15→H1, olasılıklar yenilendi, NOM istekleri 200. Konsol hataları yalnız test arka ucunda olmayan
  genel düzen uçları (`/api/data/cached`, `/ws/all`); NOM'a ait hata yok.
- **Faz 8 (gölge):** `nom_shadow.py --once` → **5 tahmin yazıldı** (`source='shadow'`, t_dec 2026-11-16 20:41; seans ufku
  kapanışa <30 dk olduğundan atlandı). `--backfill 2026-11-13T21:00 2026-11-16T16:00` → 92 örneklem dışı satır, **90 sonuç yazıldı**.
  `/calibration` (1 s 1,5/1, 56 gün): n 193, LONG Brier becerisi **−0,027**, eğim **0,35**, 5 kova WF bandı dışında, `drift_uyarisi`
  açık; SHORT +0,021 → **mezun değil (12,7 gün < 28)**. `/drift`: 918 karar, birkaç hızlı özellikte PSI KAYMA (yuvarlak seviye
  yakınlığı, H1 ATR oranı — NDX 27k düzeyi ve yüksek VIX haftası). Bu, FAZ_5'in final eğim bulgusuyla (0,54–0,68) tutarlı:
  sıralama var, olasılık düzeyi yeni rejimde kayıyor → gölge izlemeye devam, güvenilir sayılmaz (mezuniyet kuralı işliyor).
- **Faz 9:** `test_promote_rollback` geçti; `/drift` ucu canlı yanıt verdi.
- Testler: **11 passed** (leakage 3, eşdeğerlik 1, etiket 3, API/engine 4).

### Ek koşular (2026-11-16, hook sonrası)
- **Faz 9 tam döngü:** `faz9_retrain.py run` (indir → yeniden kur → W'de şampiyon/meydan okuyan) → **şampiyon kalır** (%56,7 < %60,
  ort. +0,0004); `results/faz9_retrain_20261116.json`, FAZ_9 EK.
- **Gölge mod testi:** `backend/tests/test_nom_shadow.py` → **4 passed** (her hedefe bir satır + idempotent upsert, sonuç tahminle
  yazılmaz; bayatta yazım yok; `fill_outcomes` yalnız ufku dolanı çözer ve **eğitimdeki `label_batch` ile birebir**; update filtresi
  önce (E128); DB yoksa fail-open).
- **Panel render testi:** `frontend/tests/nomPanel.test.tsx` (vitest, canlı API'den alınmış gerçek yanıt fixture'ları) → **5 passed**
  (LONG/SHORT + %95, NÖTR + yön uyarısı, 5 SHAP faktörü, S/R haritası, RSI/rejim/VIX, model sürümü, canlı kalibrasyon SVG +
  "mezun değil", ufuk/geometri seçicisi hook'u yeni hedefle çağırır, veri bayatsa tahmin gizlenir).
- **Canlı eşdeğerlik:** canlı gölge satırları vs aynı anın Dukascopy tahmini r 0,995, sonuç etiketi %93,8 aynı (FAZ_5 §5).
- Toplam NOM testleri: backend **15 passed** (11 + 4), frontend **5 passed**.
- **Mezuniyet:** karşılanmıyor (12,7 gün < 28; takvim gerektirir). Prompt "yaz" diyor — yazıldı ve uygulanıyor; motor
  mezun olana kadar "güvenilir değil" etiketiyle gölgede kalır (DÜRÜST SONUÇ, FAZ_5 §5).


### Gölge döngüsü canlıda AÇIK (2026-11-16, kullanıcı onayıyla)
- Railway `upbeat-flow`: `NOM_SHADOW_ENABLED=1` (tek yazar; kutu/yerel betik kapalı). Önce `pyarrow` eksikliği giderildi
  (commit 6ab64192; canlı `/api/probability/nasdaq` 500 → 200).
- İlk canlı kayıt: t_dec 2026-11-16 21:12 UTC, 5 hedef (`source='shadow'`), 15 dk aralıkla sürüyor.
- Mezuniyet ölçümü: 28 gün dolunca (≈ 2026-12-14, canlı-gölge başlangıcından) `GET /api/probability/nasdaq/calibration?source=shadow`.
  O tarihe kadar motor "güvenilir değil" etiketiyle gölgede.

### Mezuniyet ölçütü geçmişte yeniden oynatıldı (2026-11-16)
`src/faz8_eski_donem_mezuniyet.py`: sayaçta iki ölçüm hatası bulundu ve düzeltildi (E138; eşikler aynı). Düzeltilmiş ölçüt
2018–21 Dukascopy'de gerçek modeli 29 günlük pencerelerin %26–62'sinde mezun ediyor, bozuk modelleri ≤%13 / %0 → ölçüt
ayırt edici. Test `test_graduation_independence_and_band` (backend NOM testleri **16 passed**). Canlı mezuniyet ≈ 2026-12-14.
