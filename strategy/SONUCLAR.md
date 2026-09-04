# NASDAQ karnesi (2026-05-19 → 09-02, 284 işlem, baz +5.023$)

| # | strateji | tarihsel | **dış-örneklem** | hüküm |
|---|---|---:|---|---|
| **S08** | **geri çekilmede daha iyi fiyattan limit** | **+19.606** | **+105 → +970 ✅** | **EN İYİ ADAY — gölge** |
| S02 | Cuma ≥12 UTC bloğu | +8.340 | doğrulandı ✅ | doğru ama **zaten canlıydı** |
| S01 | ATR sıkışma filtresi | +9.717 | yapılmadı | gölge (permütasyon sınırda) |
| S03 | TP büyütme (k×ATR) | 2×: −2.458 · 5×: +5.588 | — | açık soru, simülatöre duyarlı |
| S06 | konum kapısı sıkılaştırma | +8.401 | **gölge karnesi çürüttü ❌** | NDX'te bloklama; **GDAXI'de canlı** |
| S05 | HTF seviye filtresi | +8.298 | **ters döndü ❌** | çürüdü |
| S07 | teyit bekleme | +8.898 | **+105 → −2.020 ❌** | çürüdü |
| S04 | kâr takipli stop | −1.681 | — | çürüdü (kozmetik WR) |

## Canlıya alınanlar (bu oturumda)
* `NDX_FRIDAY_BLOCK=True` — repo varsayılanı düzeltildi (kutuda zaten açıktı)
* `POS_TIGHT_BLOCK=True` + `POS_TIGHT_SYMBOLS=("GDAXI.INDX",)` — gölge karnesi:
  GDAXI'de bloklananlar %28,6 kazanıyor (başabaş %64), z=−6,47
* `SQZ_FILTER_*` — gölgede ölçülüyor
* `shadow_log` takip penceresi 10 bar → gerçek TP/SL yarışı (karneyi bu düzeltme mümkün kıldı)
* `box_export_trades_30d.detect_offset()` — bayat tick koruması

## Sıradaki
1. S08'i gölge bayrağı olarak bağla, 2 hafta ölç (X monoton olduğu için
   canlı doluluk oranı kritik).
2. Aynı bataryayı **XAUUSD / USOIL / GDAXI**'de koştur — `kosu.py` hazır.
3. Gölge karnesi biriktikçe S01 (sıkışma) kararını nesnel kapat.
