# NDX SELL — SL Optimizasyonu (sabit + ATR-uyarlamalı)

**Tarih:** 2026-07-29 · **Soru:** SL'i genişletmek kâr oranını artırır mı?

## Veri penceresi — neden 07-16'dan başlıyor

`candle_cache` barları **2026-07-16'ya kadar** MT5 broker sunucu saatiyle
(UTC+2/+3) etiketlenmişti (`research/ndx_buy_lab/RAPOR.md §1`). Sinyaller ise
gerçek UTC. O dönemde sinyal↔bar eşlemesi 3 saat kaymış olur → **kullanılamaz**.
Bu çalışma yalnız temiz dönemi kullanır (07-16 → 07-29, 13 gün, 272 olay).
Kullanıcının istediği "son 1 hafta" zaten bu bölgenin içinde.

**Sürtünme 1.3 puan** dahil (ndx_buy_lab'ın ölçtüğü MT5 1m spread medyanı) —
girişte aleyhte kayma + hedeflerin zorlaşması olarak uygulandı.
Aynı barda TP+SL → konservatif SL, her varyantta aynı.

## 【A】 Sabit SL genişletme — TEK BAŞINA İŞE YARAMIYOR

| Geometri | n | WR | başabaş | marj | **totR** |
|---|---|---|---|---|---|
| **TP80 / SL110 (mevcut)** | 60 | %65.0 | %57.9 | +7.1pp | **+7.36** |
| TP80 / SL130 | 51 | %68.6 | %61.9 | +6.7pp | +5.54 |
| TP80 / SL150 | 51 | %72.5 | %65.2 | +7.3pp | +5.73 |
| TP80 / SL180 | 52 | %73.1 | %69.2 | +3.9pp | +2.89 |
| TP80 / SL260 | 38 | %78.9 | %76.5 | +2.4pp | +1.23 |

SL genişledikçe **kazanma oranı artıyor** (%65 → %79) ama **başabaş eşiği daha
hızlı yükseliyor** — marj daralıyor, toplam kâr düşüyor. Sabit SL'i büyütmek
NDX SELL'de kaybettiriyor. *(Not: yalnız son 7 güne bakınca SL130 daha iyi
görünüyordu — 13 günlük pencerede bu tersine döndü, yani o bulgu gürültüydü.)*

## 【C-D】 ATR-uyarlamalı SL — İŞTE BURADA KAZANÇ VAR

| Geometri | n | WR | marj | totR | avgR |
|---|---|---|---|---|---|
| MEVCUT TP80/SL110 | 60 | %65.0 | +7.1pp | +7.36 | +0.123 |
| **TP80 / SL 2.0×ATR** | 60 | %63.3 | +6.9pp | **+10.14** | +0.169 |
| TP80 / SL 3.0×ATR | 50 | %74.0 | +7.9pp | +8.35 | +0.167 |
| **TP 1.5×ATR / SL 2.5×ATR** | 48 | %75.0 | **+12.5pp** | +9.60 | **+0.200** |

Ortalama SL: 2.0×ATR ≈ **104 puan** — mevcut 110'a çok yakın. Yani kazanç
"daha geniş stop"tan değil, **stopun volatiliteye uyum sağlamasından** geliyor:
sakin piyasada daralıyor, oynak piyasada genişliyor.

## Kronolojik split doğrulaması (2×136 olay) + bootstrap

| Varyant | 1. yarı (07-16→) | 2. yarı (07-23→) | P(totR>0) |
|---|---|---|---|
| MEVCUT TP80/SL110 | %65.5 · +3.82 | %62.5 · +2.55 | %88.4 |
| TP80 / SL 2.0×ATR | %59.4 · +3.37 | %65.5 · +5.64 | %92.4 |
| TP80 / SL 3.0×ATR | %70.8 · +3.51 | %74.1 · +3.76 | **%95.4** |
| **TP 1.5×ATR / SL 2.5×ATR** | %69.6 · +2.60 | %80.8 · **+7.60** | **%98.3** |

**Her varyant iki yarıda da pozitif** — hiçbiri tek bir döneme yaslanmıyor.
En yüksek güven `TP 1.5×ATR / SL 2.5×ATR` (%98.3) ve `SL 3.0×ATR` (%95.4).

## Sonuç ve öneri

1. **"SL'i genişlet" tek başına yanlış yol** — sabit SL büyütmek toplam kârı
   düşürüyor (+7.36 → +1.23 arası). Kazanma oranı artıyor ama başabaş eşiği
   daha hızlı yükseliyor.
2. **Doğru cevap ATR-uyarlamalı stop.** İki güçlü aday:
   - `TP80 / SL 2.0×ATR` — en yüksek toplam (+10.14, mevcuda göre **+%38**),
     işlem sayısı aynı (60), mevcut TP'ye dokunmaz → **en az müdahaleli**
   - `TP 1.5×ATR / SL 2.5×ATR` — en yüksek verim (avgR +0.200, mevcudun
     **1.6 katı**) ve en yüksek güven (%98.3), ama işlem sayısı düşük (48)
3. **Uyarı:** 13 günlük pencere, 24 varyant tarandı → in-sample seçim baskısı
   var. Split ve bootstrap bunu bir miktar dengeliyor ama **ileriye dönük
   doğrulama şart**. Bu yüzden önerim: kazananı **gölge modda** ölç, canlı
   geometriye hemen dokunma.

**Dosya:** `ndx_sell_sl.py`

---

# DERİN TEST — 5.5 AY (2026-02-18 → 07-29, 8.129 sinyal)

## Zaman kayması düzeltildi ve KANITLANDI
Bar damgalarına dönem-bazlı düzeltme (`<03-08: −120dk`, `03-08→07-16: −180dk`,
`≥07-16: 0`). **Doğrulama:** 07-16 sonrası dilimde bu script `n=60, WR %65.0,
totR +7.36` üretti — bağımsız yazılmış önceki scriptle **birebir aynı**.

## 1. ÖNCEKİ BULGUM ÇÜRÜDÜ — 13 gün gürültüymüş

| Geometri | 13 gün (önceki) | **5.5 ay (kapısız)** |
|---|---|---|
| TP80 / SL 2.0×ATR | +10.14R | **−13.57R** |
| TP 1.5×ATR / SL 2.5×ATR | +9.60R | **−20.60R** |
| TP80/SL110 (canlı) | +7.36R | **−7.82R** |

36 kombinasyonun 35'i negatif; en iyisi +1.00R, P(kâr>0)=%50.9 (yazı tura).
Dönem kırılımı: `02-18→03-08` +1.9R · `03-08→07-16` **−16.4R** · `07-16→` +7.4R.

## 2. ASIL BULGU: kapılar belirleyici, geometri ikincil

| Geometri | Kapısız | **trend+konum KAPILI** | P(kâr>0) |
|---|---|---|---|
| TP80/SL110 (canlı) | −7.82 | **+37.18** (WR %73.4) | %100 |
| TP80 / SL150 | +4.73 | +31.80 (WR %82.5) | %100 |
| **TP80 / SL 2.0×ATR** | −13.57 | **+73.53** | %100 |
| **TP 2.0×ATR / SL 2.0×ATR** | −14.00 | **+75.00** | %100 |
| TP 1.5×ATR / SL 2.5×ATR | −20.60 | +55.60 | %100 |

## 3. TP'yi de ATR'ye bağlamak — evet kârlı, ama SL kadar dayanıklı değil

| | Aylık pozitif | Mart hariç | IN (%60) | OUT (%40) | P(OUT>0) |
|---|---|---|---|---|---|
| TP80/SL110 (canlı) | 4/6 | +14.0 | +27.73 | +10.18 | %93.6 |
| **TP80 / SL 2.0×ATR** | **6/6** | **+36.2** | +51.34 | **+23.61** | %99.5 |
| TP 2.0×ATR / SL 2.0×ATR | 5/6 | +28.0 | +57.00 | +19.00 | %99.5 |
| TP 1.5×ATR / SL 2.5×ATR | **6/6** | +23.0 | +39.80 | +16.40 | %100 |

## Öneri
1. **Kapılar doğrulandı** (5.5 ayda −7.8R → +37.2R) — canlıda kalsın.
2. **SL = 2.0×ATR(14, 5m), TP 80 sabit** — 6/6 ay pozitif, Mart'sız +36.2R
   (canlının 2.6 katı), OUT +23.61R, P=%99.5, işlem sayısı korunuyor (175/139).
   Ortalama SL ≈104p ≈ mevcut 110 → kazanç genişlikten değil, uyumdan.
3. TP'yi de ATR'ye bağlamak +75R veriyor ama aylık dayanıklılığı düşük (5/6)
   ve Mart'a bağımlı → önce yalnız SL'i uyarlamalı yapmak daha az riskli.
4. 36 varyant tarandı; aylık+split+blok-bootstrap dengeliyor ama ileriye
   dönük teyit yine de şart.
