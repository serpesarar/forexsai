# Sonuç — DAYCOMBO içinde SL olanları ayıran özellik / sıkışma kombosu (2026-10-20)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md). Veri: CK-03'ün birebir yeniden ürettiği 356 DAYCOMBO (2025: 195, ortR −0,030;
2026: 161, ortR +0,116) + canlı 34 DAYCOMBO / 23 REENTRY. 112 özellik (≈100 islem_otopsi + 56 gösterge + sıkışma
ölçüleri + VIX + gece getirisi + günün kaçıncı DAYCOMBO'su + önceki DAYCOMBO sonucu), 314 tertil koşulu.

## 1. Ön-kayıtlı arama (keşif 2025 → sınama 2026, 300 plasebo) — `results/rapor.md`
| aile | 2025'in en kötü 10 grubu 2026'da | ortalama kurtarılan R | plasebo yüzdeliği | hüküm |
|---|---|---|---|---|
| tek koşul | 1/10 kazandırırdı | −3,66 | %74 | GEÇMEDİ |
| **SQZ ∧ X** | 1/10 | −3,39 | %36 | GEÇMEDİ |
| herhangi iki koşul | 0/10 | −2,83 | %24 | GEÇMEDİ |
Ters yönde (2026'da bul → 2025'te sına; `ek.md`) daha iyi görünüyor (tek 9/10, SQZ∧X 8/10). Ama 2025'in tamamı
negatif (−0,03R) olduğu için orada herhangi bir grubu engellemek kolayca + çıkar; asıl testte (2025 → 2026) kombolar çöktü.
2025'te "kötü" görünen grupların çoğu 2026'da kârlı → DAYCOMBO SL'lerinin kalıcı bir ortak özelliği yok.

## 2. Dünkü SL'lerin profili — `results/ek.md`
Dün **2** DAYCOMBO SL oldu (diğer iki SL REENTRY). İkisi de diğer 32 canlı DAYCOMBO'ya göre: fiyat 1h EMA50'ye **yakın**
(%9 / %3 yüzdelik), 1h EMA50 eğimi düşük (%6 / %6), çoklu zaman dilimi uyumu düşük, 15 dk hacim yüksek (%94 / %100).
Bu dört işaret 356 tarihsel DAYCOMBO'da (dün yok) sınandı (`dunku_isaret.md`): **yalnız 2026'da** çalışıyor (EMA50'ye
yakınlık Δ −0,31), 2025'te etkisiz (+0,006).

## 3. Aday: SQZ<1 ∧ 1h EMA50 uzaklığı ≤ 1,32 ATR — `results/aday.md`
| küme | engel | ortR engel | ortR kalan | kurtarılan R | P(>0) | rastgele/saat plasebo |
|---|---|---|---|---|---|---|
| 2025 | 38 | −0,091 | −0,016 | +3,5 | %72 | %64 / %78 |
| 2026 | 31 | −0,109 | +0,169 | +3,4 | %77 | %95 / %96 |
| 2025+2026 | 69 | −0,099 | +0,068 | +6,8 | %85 | %93 / %94 · çeyrekler +5,0/−1,1/−1,5/+4,5 |
| canlı DAYCOMBO / REENTRY (10-19 hariç) | 2 / 2 | — | — | +0,3 / +0,3 | — | ölçülemez |
Hüküm: **C — zayıf aday, kapı değil.** Gün-blok güven %85 < %90; 2025'te tek başına zayıf; iki çeyrek negatif; 6 testten
biri (çoklu test düzeltmesiyle anlamlı değil); canlıda bağımsız örnek yok. Yapılabilecek: bot zaten SQZ'yi gölgede
logluyor; 1h EMA50 uzaklığını da DAYCOMBO/REENTRY gölge kaydına eklemek ileri ölçüm sağlar (kod değişikliği,
onay gerekir).
