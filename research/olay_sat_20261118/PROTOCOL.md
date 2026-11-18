# Ön kayıt — Makro olay gününde gün içi sert düşüşü SAT (2026-11-18)

Yazılış: ZA-05 ve EK-1'den sonra. Görülen: olay günü aynı ALIM NDX tüm dönem −64 bp (n 79), MT5 −66, NQ −26, US500 −75.
**Görülmeyen (kör):** NDX'in dönem ayrımı ve MT5 US30/US2000 olay grubu. Gerekçe: §3-38, FX olay günü devamı (ZA-FX EK-1 ilkesi).

## Kural
ABD olay günü (CPI/NFP/FOMC/JH; → 2026-10-02), NDX 10:00–15:30 ilk 30 dk bar ≤ −e, e ∈ {%0,6, %1,0} → sonraki açılışta **SAT** (bid),
ertesi gün 16:00'da kapat (ask); finansman takvim gecesi başına düşülür (muhafazakâr). Taban: olay günlerinde rastgele 30 dk bar
sonrası SAT.

## Ölçüt
NDX Duka'da ESKİ ve YENİ'de ikisinde de SAT ort > 0 ∧ > taban; kör US30 ve US2000'de SAT ort > taban ∧ > 0 → C+ (n küçük; B için
tüm dönem P ≥ 0,975 de gerekir). Değilse X. SAT kurallarının ayı çağına bağımlılığı (§3-37): yıl dağılımı zorunlu raporlanır.
