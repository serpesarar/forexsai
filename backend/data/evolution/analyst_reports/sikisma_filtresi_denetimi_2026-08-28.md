# ATR Sıkışma Filtresi denetimi — dış AI'ın "SL adli tıp" raporu

**Tarih:** 2026-08-28 · **Denetlenen:** `NASDAQ_SL_ADLI_TIP.md` (n=28, tek pencere)
**Motor:** 120 gün gerçek MT5 geçmişi (282 NAS100 işlemi), 100.000 adet 1m bar
**Bölünme:** DIŞ 29 Haz–12 Ağu (n=254) · İÇ 13–27 Ağu (n=28, raporun penceresi)

## VERDİKT: GEÇTİ (gölge seviyesinde) — testi geçen ilk dış öneri

Kural: `ATR14(1m) / ATR100(1m) < 1.00 → giriş elenir`

| | filtresiz | kalan (sqz≥1.00) | **elenen (sqz<1.00)** |
|---|---|---|---|
| DIŞ (n=254) | WR %58.3 · ortR +0.024 · +2.403$ | n=132 · WR %63.6 · **+0.111** · +6.802$ | n=122 · WR %52.5 · **−0.070** · **−4.399$** |
| İÇ (n=28) | WR %60.7 · +0.129 · +1.886$ | n=17 · WR %70.6 · +0.401 · +2.914$ | n=11 · WR %45.5 · −0.292 · −1.028$ |

**Aile bazında yön tutarlı (DIŞ, elenen küme ortR):** CHREV −0.216 · MOM/SR −0.150 ·
VIXREG −0.058 · DAYCOMBO +0.080 (n=8, tek istisna ve zayıf). 4 ailenin 3'ünde net negatif.

**Eşik platosu:** 0.95→+0.058 · 1.00→+0.111 · 1.05→+0.107 · 1.10→+0.095 (kalan küme ortR).
Raporun iddia ettiği 0.95–1.05 platosu dış-örneklemde de duruyor.

## ⚠️ SIZINTI DÜZELTMESİ — bu denetimin en önemli teknik notu

İlk turda özellikler `bisect_left(bt, ts)` ile alınmıştı; bu, **giriş anını içeren
KOŞAN barı** özelliklere sokuyordu. Etkisi devasa:

| | sızıntılı | **sızıntısız (open+60 ≤ giriş)** |
|---|---|---|
| sıkışma filtresi plasebo | p=0.20 GEÇEMEDİ | **p=0.043 GEÇTİ** |
| elenen küme (DIŞ) | ortR −0.025 | **−0.070** |
| "kovalama streak≥2" | +0.146 / +3.966$ (sahte kenar) | +0.023 / −745$ (kenar yok) |

Yani sızıntı hem gerçek kuralı gizlemiş hem de olmayan bir kural (streak
kovalama) uydurmuştu. **1m özellik üreten her analizde koşan bar elenmeli.**

## Neden yine de GÖLGE (canlı blok değil)

1. **Koşullu plasebo yalnız 1.00'da geçiyor:** p=0.043; komşular 0.95→p=0.217,
   1.05→p=0.073. Gerçek bir kenar plato boyunca dayanmalıydı — sınırda etki imzası.
2. **Kronolojik çeyrekler:** filtre 4 çeyreğin 3'ünü iyileştiriyor ama Ç3 negatif
   kalıyor (−0.093 → −0.065). Canlıya alma kartı ölçüt-3 geçilmedi.
3. n=282 tek hesap, tek broker, 2 aylık rejim.

## Raporun DİĞER iddiaları

| İddia | Dış-örneklem |
|---|---|
| SL'ler sıkışmada açılmış (medyan 0.94 vs 1.19) | ✅ yön doğru ama zayıf: 1.005 vs 1.060 |
| SL'lerde gövde oranı yüksek (0.69 vs 0.50) | ❌ ayrışmıyor (0.50 vs 0.46) |
| TP'ler geri çekilmede, SL'ler streak'te girmiş | ⚠️ sızıntısız hâlde streak ayrıştırmıyor (plasebo p=0.23) |
| İki arketip (sıkışma-kovalama / genişleme-tuzak) | test edilmedi — n yetersiz |

## TP büyütme ile etkileşim (önceki denetimin yan bulgusu)

Kronolojik çeyrekler (ortR), TP=5×ATR14 ile:
`filtresiz+sabit` +0.091/+0.020/**−0.107**/+0.079 (4/4 değil) →
`filtresiz+5×ATR` +0.145/+0.034/+0.095/+0.136 (**4/4**) →
`sqz≥1.0+5×ATR` +0.248/+0.130/+0.332/+0.244 (**4/4, en güçlü**, plasebo p=0.029)

İki bulgu bağımsız ve toplanıyor. Ama TP değişikliği hâlâ ayrı bir gölge işi
(sim slot işgalini/BE-trail'i/swap'ı modellemiyor) — birlikte canlıya alınmaz.

## Uygulama

`phase_rules.py` → `SQZ_FILTER_ENABLED=True` (ölç+logla), **`SQZ_FILTER_BLOCK=False`**,
`SQZ_FILTER_MIN=1.00`, `SQZ_FILTER_SYMBOLS=("NDX.INDX",)`.
Saf çekirdek `squeeze_ratio` / `squeeze_blocks` (MT5'siz test edilebilir, 6 test).
Bot: `_squeeze_ratio` (pozisyon 1 → koşan bar hariç) + `_squeeze_blocks`,
`open_trade` ve `open_trade_sr` içine bağlı. Gölgede `shadow_log`'a
`would_block` yazar; blok açılırsa `gate_skip` + `SQUEEZE_GATE` satırı.

**Sonraki adım:** 2 hafta gölge → elenen kümenin gerçek sonuçları 1m replay ile
ölçülür → Ç3 pozitife dönüyor ve plasebo platoda dayanıyorsa `SQZ_FILTER_BLOCK=True`.
