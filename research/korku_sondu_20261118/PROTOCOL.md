# Ön kayıt — "Korku söndü": VIX sıçramasından hızlı iniş → çok günlü AL (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe / mekanizma
Oynaklık hedefleyen fonlar ve risk paritesi, oynaklık düşünce kaldıracı geri artırır (zorunlu alım, gecikmeli ve günlere yayılı).
Defter: VE-01 ters VIX eğrisi (korkunun zirvesi) C+, VE-02 VIX sıçraması sonrası 5 gün −41 bp. **Korkunun sönmesi** (VIX'in zirvesinden
hızla geri gelmesi) hiç sınanmadı.

## Veri (günlük kapanış)
VIX (1990 →) ve QQQ (1999-03 →), `qs03_akis_takvim_20261111/data/`; kör tekrar SPY. NDX CFD maliyeti: 2 bp gidiş-dönüş + finansman
`lib.FIN_BP_PER_DAY` × takvim günü (taban da aynı maliyeti öder).

## Tanım
- Sinyal günü d: VIX(d) ≤ (1 − k) × max(VIX, d−9…d) ∧ o max ≥ L; k ∈ {%20, %30}, L ∈ {25, 30}.
- Epizod: bir sinyalden sonra 20 işlem günü yeni sinyal yok (bağımsızlık; E102).
- Giriş d+1 kapanışı (VIX 16:15'te kapanır, bir gün gecikme), çıkış H işlem günü sonra kapanış; H ∈ {5, 10, 20}.
- 12 hücre. Taban: aynı H ile her günden giriş (koşulsuz sürüklenme).

## Dönemler ve seçim
KEŞİF 1999-03 → 2011-12 (QQQ): fark (sinyal − taban) en yüksek t'li ≤ 2 hücre dondurulur (n ≥ 8 epizod, fark > 0).
TEST 2012-01 → 2021-10 ve YENİ 2021-11 → (QQQ): ikisinde de fark > 0; TEST+YENİ birleşik epizod bootstrap P(fark > 0) ≥ 0,975.
Kör: aynı hücre SPY'da tüm dönem fark > 0.
Hepsi → B; P hariç → C+; tek dönem → C; değilse X. Bilgi: epizod başına en kötü, "VIX hâlâ yüksek ama inmedi" günleri.
