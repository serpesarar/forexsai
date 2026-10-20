# Ön-kayıt — DAYCOMBO içinde SL olanları ayıran özellik / sıkışma kombosu (2026-10-20)

Kullanıcı: tüm DAYCOMBO'lar için değil; SL olan DAYCOMBO'ların diğerlerinden farklı bir özelliği olmalı — belki
sıkışma ile birlikte bir kombo. Defter: CK-03 (kural birebir, 2025 −0,030R), IO-09 (20 p düşüş limiti elendi),
IO-18 (NDX BUY genel alt-grup araması geçmedi), IO-22 (SQZ dönemlik; DAYCOMBO+REENTRY'de SQZ engeli −6,1R), E24
(çok özellikten seçim → plasebo/sınama zorunlu). Yeni olan: aile-içi (yalnız DAYCOMBO) arama, kuralın yeniden üretilmiş
356 işlemi, SQZ × X kombolarının açıkça sınanması.

## Veri
`research/canli_kart_20261009/results/daycombo_trades.parquet` (CK-03, kural birebir, sabit TP 80 / SL 110, spread 1,5):
**keşif = 2025 (OOS-A)**, **sınama = 2026 (IS + OOS-B)**. Canlı 34 DAYCOMBO (07-30 → 10-20) sınama dönemiyle örtüşür →
ayrı bağımsız kanıt sayılmaz, yalnız sadakat/yorum. Özellikler giriş anında yalnız KAPANMIŞ barlarla:
islem_otopsi `pre_*`/`geo_*`/zaman + 56 gösterge (sl_ortak `entry_features`, ≈100) + sıkışma ölçüleri (IO-22 `core`)
+ VIX önceki gün + gece getirisi büyüklüğü + günün kaçıncı DAYCOMBO'su + aynı gün önceki DAYCOMBO sonucu.

## Arama (keşifte)
Koşullar: sayısal özellik keşif tertilleri (alt/orta/üst) + kategoriler. Üç aile:
(a) tek koşul, (b) **SQZ ∧ X** (atr_14_100 < 1 veya ≥ 1, VE bir X koşulu), (c) herhangi iki koşul VE.
Destek ≥ 15 keşif işlemi. Sıralama: alt grubun ortR'si (en düşük = engel adayı). Her aileden en kötü 10.

## Sınama ve geçme
Sınamada (2026) her aday için: engellenen n, ortR(engel) vs ortR(kalan), kurtarılan R. Plasebo: keşifte sonuçlar
karıştırılıp aynı arama 300 kez yapılır → seçilen 10'un sınama kurtarılan R ortalaması dağılımı.
**Geçme (aile başına):** 10 adayın ≥6'sında sınama kurtarılan R > 0 VE 10'un ortalaması plaseboların %90'ını aşar.
Geçen tek aday bile olsa yalnız GÖLGE adayıdır (2. KURAL). Ek: 10-19'un 3 SL'sinin özellik yüzdelikleri (keşif+sınama
dağılımında) ve k=10 komşu SL oranı — yorum, kanıt değil.
