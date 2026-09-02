# Gölge takip penceresi düzeltildi → ilk gerçek kapı karnesi

**Tarih:** 2026-09-02 · **Sınıf:** ölçüm altyapısı + canlı kural değişikliği

## 1. Sorun
`shadow_log.py` gölge kararlarının sonucunu **yalnız 10 barlık MFE/MAE** ile
ölçüyordu. TP'si 80 / SL'i 110 puan olan bir işlemi 10 bar çözemez → 946
kayıtlık `POS_TIGHT` karnesi backtest ile çelişiyor, hiçbir kapı kararı
kanıtla kapanamıyordu.

## 2. Düzeltme
* `record_shadow(...)` artık scope'un **gerçek TP/SL mesafesini** kaydediyor
  (`_scope_geometry()`: VIXREG 80/uyarlamalı, CHREV sembol config'i,
  DAYCOMBO 80/110, momentum `ROBUST_SCOPES`; yüzde geometriler fiyata çevrilir).
* `resolve_pending(...)` Faz-2 dalında artık **bar-bar TP/SL yarışı** çözüyor
  (mevcut `_hypothetical_outcome` makinesi), yarış bitene kadar bekliyor
  (tavan `FOLLOWUP_MAX_MIN=480`). 10 barlık özet geriye dönük uyumluluk için duruyor.
* Fail-open korundu: geometri çözülemezse eski davranış sürer.

## 3. Birikmiş 960 kayıt geriye dönük çözüldü (yeni veri beklemeden)

**"Bloklanacak sinyal gerçek geometride ne yapardı?"**

| kural | sembol/yön | W | L | bloklanan WR | başabaş WR | fark | hüküm |
|---|---|---:|---:|---:|---:|---:|---|
| pos_tight | **GDAXI BUY** | 22 | 55 | **%28,6** | %64,0 | **−35,4** | **blokla** |
| pos_tight | NDX SELL | 31 | 19 | %62,0 | %57,9 | +4,1 | bloklama |
| pos_tight | USOIL BUY | 101 | 1 | %99,0 | %58,9 | +40,1 | kesinlikle bloklama |
| pos_tight | XAUUSD BUY | 228 | 274 | %45,4 | — | — | (işlem kapalı) |
| squeeze | NDX SELL | 3 | 0 | %100 | %57,9 | — | n=3, hükümsüz |

GDAXI binom: z=−6,47, **p≈1e-10**.

## 4. ⚠️ Backtest'im ÇÜRÜDÜ — metodolojik ders

Önceki raporda (`konum_kapisi_deneyleri`) NDX için 6s/0,60 sıkılaştırmasının
+8.401$ vs +4.290$ verdiğini bulmuştum. **Yanlıştı.** Sebep:

> Backtest, **0,40 kapısından GEÇMİŞ** işlemlere daha sıkı bir eşik uyguluyor.
> Ama sıkı kapının canlıda **BLOKLAYACAĞI popülasyon** bu değil. Gölge kaydı
> gerçek bloklanan kümeyi ölçüyor → gölge kanıtı backtest'i EZER.

Bu, "kapı backtest'i" için genel bir kural: **mevcut bir kapının arkasındaki
hayatta kalanlar üzerinde daha sıkı eşik denemek yanlı sonuç verir.**

## 5. Canlıya alınan
`POS_TIGHT_BLOCK=True` + yeni **`POS_TIGHT_SYMBOLS=("GDAXI.INDX",)`**.
Gölge ölçümü tüm sembollerde sürer; yalnız **bloklama** kanıtlanan sembolle sınırlı.
NDX ve USOIL bilerek DIŞARIDA (bloklamak para kaybettirir).
Eşikler değişmedi (SELL≥0,60 / BUY≤0,40). 2 yeni test (toplam 10, hepsi geçiyor).

## 6. Sıradaki
Gölge karnesi artık gerçek geometriyle birikiyor → `SQZ_FILTER` kararı da
(şu an n=3) birkaç hafta içinde aynı yöntemle nesnel kapanacak.
