# NOM — NASDAQ Olasılık Motoru

Her an, o an açılacak varsayımsal LONG ve SHORT işlem için **P(TP önce) / P(SL önce) / P(zaman aşımı)** ve
sürtünmeli **beklenen R** veren, kalibre, açıklamalı karar destek motoru. **Emir açmaz.**
Sonuçların dürüst özeti: `FAZ_5_RAPOR.md` ve `FAZ_9_RAPOR.md` → "DÜRÜST SONUÇ".

## Dosya haritası
| Yer | İçerik |
|---|---|
| `PROTOCOL.md` | ön kayıt (etiket, özellik, doğrulama, geçme ölçütleri) |
| `FAZ_0_RAPOR.md` … `FAZ_9_RAPOR.md` | faz raporları |
| `src/` | araştırma kodu: `duka_fetch`, `macro_fetch`, `data_layer`, `faz0_build`, `faz12_build`, `faz1_tick_check`, `faz2_audit`, `validation`, `faz4_train`, `faz5_econ`, `faz9_retrain`; ekler: `histdata_layer` (2018–21, saat kuralı E135), `faz0_v3_eski_donem`, `faz0_duka_vs_histdata_2018`, `faz0_takvim_dogrula`, `faz34_ek` (Purged K-Fold, CatBoost, ensemble), `deep_nets` + `faz4_deep` (LSTM/TCN/Transformer) |
| `data/` (git dışı) | `ndx_1m_v1.parquet`, `features_v1.parquet`, `labels_*.parquet`, `macro/` |
| `results/` | metrikler, WF/final OOS tahminleri, kalibrasyon tabloları, SVG grafikler |
| `backend/services/nom/` | **tek kod yolu**: `bars`, `features`, `labels`, `nyse_calendar`, `model_store`, `live_data`, `engine`, `shadow`, `calibration`, `drift` |
| `backend/routers/nom_router.py` | API |
| `backend/models/nom/<sürüm>/` + `ACTIVE`, `HISTORY.jsonl` | model paketleri, etkin sürüm, terfi geçmişi |
| `backend/scripts/nom_shadow.py` | gölge modu koşucusu |
| `frontend/app/olasilik-motoru/` + `components/nom/` + `lib/api/nom.ts` | panel |
| `supabase/migrations/20261113_nom_predictions.sql` | gölge kayıt tablosu (uygulandı) |
| `backend/tests/test_nom_features.py`, `test_nom_engine.py` | sızıntı, train/serve eşdeğerliği, etiket, motor, API testleri |

## Çalıştırma
```bash
# API (backend çalışırken)
curl "http://localhost:8000/api/probability/nasdaq?horizon=1h&geometry=1.5x1.0"
curl "http://localhost:8000/api/probability/nasdaq/meta"
curl "http://localhost:8000/api/probability/nasdaq/calibration?horizon=1h&geometry=1x1"
curl "http://localhost:8000/api/probability/nasdaq/drift"
```
Panel: `/olasilik-motoru` (ufuk + geometri seçici, LONG/SHORT barları, S/R merdiveni, RSI/rejim, "Neden?", canlı kalibrasyon).
Canlı veri: Supabase `candle_cache` NDX.INDX 1m (kutudaki MT5 kaydedicisi), son 240 gün, disk önbelleği
`backend/data/nom_cache/`. Son bar > 5 dk eskiyse **tahmin verilmez** (`VERI_BAYAT`).

## Testler
```bash
cd backend && ../.venv/bin/python -m pytest tests/test_nom_features.py tests/test_nom_engine.py -q
```

## Yeniden üretim (sıfırdan)
```bash
cd research/nom_20261113
../../.venv/bin/python src/macro_fetch.py          # makro + takvim
../../.venv/bin/python src/faz0_build.py           # temiz veri katmanı + envanter
../../.venv/bin/python src/faz12_build.py          # özellik + etiket
../../.venv/bin/python src/faz2_audit.py           # sızıntı + önem
../../.venv/bin/python src/faz4_train.py main      # WF modelleri (~25 dk)
../../.venv/bin/python src/faz4_train.py compare   # yön-koşullu / XGBoost / P2 plasebo
.venv_ext/bin/python src/faz34_ek.py               # Purged K-Fold + CatBoost + ensemble (catboost .venv_ext'te)
.venv_ext/bin/python src/faz4_deep.py --kinds lstm,tcn,transformer   # derin modeller (torch; AYRI süreç — OpenMP)
../../.venv/bin/python src/histdata_layer.py       # 2018–21 HistData katmanı + saat ekseni denetimi
../../.venv/bin/python src/faz0_v3_eski_donem.py   # bağımsız eski dönem (FAZ_5 §6)
../../.venv/bin/python src/faz5_econ.py dev        # ekonomik test + eşik seçimi
../../.venv/bin/python src/faz5_econ.py final      # FİNAL TEST — tek kez (FINAL_OPENED.json kilidi)
../../.venv/bin/python src/faz5_econ.py bundle     # üretim paketi + ACTIVE
```

## Yeniden eğitim ve izleme
- Periyodik (önerilen: ayda bir): `../../.venv/bin/python src/faz9_retrain.py run` — yeni veri indirir, yeniden kurar,
  şampiyon (ACTIVE) ile meydan okuyanı **ikisinin de görmediği** son pencerede kıyaslar; yalnız ölçütü geçerse
  terfi eder (`FAZ_9_RAPOR.md`). Mekanizma sınaması: `... faz9_retrain.py dryrun`.
- Geri alma: `cd backend && ../.venv/bin/python -c "from services.nom import model_store as M; print(M.rollback())"`.
- Gölge modu: `NOM_SHADOW_ENABLED=1` (backend döngüsü) veya `python backend/scripts/nom_shadow.py --loop`
  → `nom_predictions`; sonuçlar ufuk dolunca aynı satıra yazılır.
- Drift: `/api/probability/nasdaq/drift` (PSI ≥ 0,25 önemli özellikte veya kalibrasyon bozulması → `alarm`).
- Mezuniyet: `FAZ_8_RAPOR.md` (≥ 4 hafta, ≥ 300 bağımsız tahmin, tüm kovalar WF bandında, Brier becerisi ≥ 0).
