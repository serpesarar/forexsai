# Yön Laboratuvarı (2026-11-14)

Soru: gün-içi NASDAQ'ta yönü şanstan ayırt edilebilir biçimde söyleyen bilgi var mı? Sonuç ve kullanım sınırları: **`FAZ_10_RAPOR.md`**.

| Dosya | İçerik |
|---|---|
| `PROTOCOL.md` (+ EK-1, EK-1b, EK-2) | ön kayıt |
| `FAZ_0…10_RAPOR.md` | faz raporları |
| `results/referans_atlasi_*.csv`, `referans_atlasi_kalibrasyon.svg` | referans atlası (gerçek / hayalet / analitik, ret–kırılım) |
| `results/durum_atlasi_tekli.csv`, `kombinasyon_taramasi.csv` | durum atlası + tarama |
| `results/faz5_*.csv`, `faz6_*.csv`, `faz7_ozet.json`, `faz89_ozet.json` | seçim, doğrulama, katmanlar, model, kör test/taşıma, işlem |
| `results/deneme_sayaci.csv` | 8.680 deneme |
| `src/` | `core` (ızgara, etiket, ilk-geçiş, martingal), `refs`, `extras`, `build_grid`, `atlas`, `faz5_validate`, `faz6_layers`, `faz7_model`, `faz89`, `tick_micro`, `kutu_export_m5` |
| `tests/test_yonlab_leak.py` | referans + durum sızıntı testi |

Yeniden üretim (veri `data/` git dışında):
```bash
cd research/yon_lab_20261114
../../.venv/bin/python src/build_data.py          # ndx_1m_v2 (NOM veri katmanı + 2026-01)
./run_builds.sh                                    # gerçek + 10 martingal ızgara (~5 dk)
for t in real mart1 mart2 mart3 mart4 mart5 mart6 mart7 mart8 mart9 mart10; do ../../.venv/bin/python src/atlas.py $t; done
../../.venv/bin/python src/faz5_validate.py
../../.venv/bin/python src/faz6_layers.py          # data/DIX.csv, data/xasset/, data/mt5/, data/tick_micro_2025.parquet gerekir
../../.venv/bin/python src/faz7_model.py
../../.venv/bin/python src/faz89.py                # KÖR — FINAL_OPENED.json kilidi; ikinci kez koşmaz
```
