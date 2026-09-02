# İşlem export'unda +1230 dk zaman kayması — kök neden, kapsam, düzeltme

**Tarih:** 2026-08-30 · **Sınıf:** KRİTİK (veri bütünlüğü)
**Bulan:** dış AI (`DUZELTME_RAPORU_2026-08-30`) · **Doğrulayan + düzelten:** panel Claude

## 1. İddia DOĞRULANDI

Dış AI, `nasdaq_tam_veri_2026-08-29` paketindeki işlem CSV'sinin +1230 dk
(20s30dk) ileri kayık olduğunu bildirdi. Bağımsız olarak iki testle doğrulandı:

**Test A — ticket eşleştirmesi (95 ortak LIVE emri):**
CSV − karar defteri = **+1229,99 dk** (min +1229,98 / max +1230,00) → sabit kayma.

**Test B — lag-grid (fiyat/bar uyumu, 284 işlem):**

| lag | ort. hata | bar içinde |
|---|---|---|
| −1230 dk | **0,0 pt** | **%99,6** |
| 0 dk | 253,6 pt | %1,3 |
| +1230 dk | 383,8 pt | %0,0 |

## 2. Kök neden — dış AI'ın teşhisi YANLIŞ, mekanizma farklı

Rapor "script zaman damgasına +1230 dk ekliyor" diyor. Öyle değil; script
**aralıklı olarak** hatalı offset ölçüyor:

```python
# box_export_trades_30d.py::detect_offset() — ESKİ (hatalı)
for sym in syms:
    tk = mt5.symbol_info_tick(sym)
    if tk and tk.time:
        return int(round((tk.time - _time.time()) / 900.0) * 900)   # İLK tick'i kullan
```
İlk tick veren sembol kapalı/likit değilse tick **bayat** olur → offset
−63.000 sn ölçülür (doğrusu +10.800 sn). Fark = 73.800 sn = **tam 1230 dk**.

**Kanıt — aynı script, aynı gün, iki koşum:**
| koşum | rapor ettiği offset | sonuç |
|---|---|---|
| 120 günlük çekim | `broker_offset_dk=+180` | ✅ doğru |
| 130 günlük çekim | `broker_offset_dk=-1050` | ❌ kayık (paket bundan üretildi) |

Yani hata sistematik değil, **kırılgan**: koşuma göre bazen doğru bazen yanlış.
Bu, "script hep +1230 ekliyor" teşhisiyle düzeltilseydi, doğru koşumlar
yanlışlıkla −1230 kaydırılıp bozulacaktı.

## 3. Kapsam — hangi çıktı etkilendi, hangisi etkilenmedi

| Çıktı | Durum |
|---|---|
| `nasdaq_tam_veri_2026-08-29/islemler/*.csv` | ❌ kayıktı → **düzeltildi** (−1230 dk, lag=0'da %99,6 doğrulandı) |
| `nasdaq_tam_veri_2026-08-29/1m_veri/` | ✅ baştan doğru (ayrı script, offset 10.800) |
| `nasdaq_tam_veri_2026-08-29/karar_gunlukleri/` | ✅ doğru (botun kendi yazdığı, kaymasız) |
| `islem_paketi_2026-08-27` (NASDAQ+DAX paketi) | ✅ doğru — teslim öncesi 72 fiyatın 71'i bar aralığında doğrulanmıştı |
| **Dış AI kural paketi elemesi (K1-K5)** | ✅ etkilenmedi — +180 dk'lık export + kutuda taze offset |
| **Sıkışma filtresi denetimi** | ✅ etkilenmedi — aynı şekilde |

Denetimlerin verisi lag taramasında **lag=0'da %99,6 uyum** veriyor; hükümleri geçerli.

## 4. Kaymanın ürettiği sahte bulgu

Kayık veride "**Cumartesi anomalisi**: 33 işlem, −2.600$" görünüyordu. Piyasa
Cumartesi kapalı — imkânsız. 20,5 saatlik kayma Cuma işlemlerini Cumartesi'ye
taşımıştı. Doğru eksende gün dağılımı:

| gün | n | SL% | USD |
|---|---:|---:|---:|
| Pzt | 38 | %34 | +3.276 |
| Sal | 58 | %40 | −78 |
| Çar | 76 | %41 | +1.925 |
| Per | 69 | %36 | +3.656 |
| **Cum** | **40** | **%60** | **−4.002** |

**Cuma bulgusu doğru eksende de duruyor** (dış AI −4.043$ demişti, bağımsız
ölçümüm −4.002$). ⚠️ Ama bu YENİ değil: bot zaten `TQ_FRIDAY_COOL=True` ile
Cuma'da çıta yükseltiyor ve CLAUDE.md'deki gerekçesi aynı sayı ("Cuma bot %46
WR / −3,9k$"). Karar "yeni kural eklemek" değil, mevcut **soğutmayı bloğa
yükseltmek mi** sorusudur — ve o ölçüm henüz yapılmadı.

## 5. Düzeltme

`detect_offset()` yeniden yazıldı: birden fazla sembolden ölçer, bayat tick'i
ve ±5 saat dışını **eler**, **medyan** alır, hiçbiri geçerli değilse
`sys.exit` ile **durur** (eskisi sessizce `return 0` yapıyordu — daha da kötü).

## 6. Ders

Dış AI'ın kalıcı önlemi ("Kapı 0 — çapraz-dosya zaman hizalaması") doğru ve
benimsenmeli. Bu projede aynı sınıf hata üçüncü kez çıkıyor:
`candle_cache` 3 saat kayması (2026-08-12), `mt5.copy_rates_from` ileri-bar
tuzağı, şimdi bu. Ortak kök: **MT5 zaman ekseni broker saatinde ve ölçüm
kırılgan.** Kural: bir zaman ekseni, üretildiği yerde değil, **bağımsız bir
referansa karşı** (fiyat↔bar uyumu / ticket↔defter farkı) doğrulanmalı.
