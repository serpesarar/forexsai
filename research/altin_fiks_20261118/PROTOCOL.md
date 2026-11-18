# Ön kayıt — Altın LBMA fiks dönüşü (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
FX-01 (§2.53): Londra fiks akışının geri dönüşü FX'te B− (kart 5/6). Altın için defterde fiks yok. LBMA altın fiyatı günde iki kez
belirlenir: AM 10:30, PM 15:00 Londra. Fikse bağlı emirler (ETF, merkez bankası, rafineri) fiyatı fikse doğru iter; sonra geri dönmesi
beklenir.

## Veri
Dukascopy XAU 1m 2018 → 2026-11 (ana; spread 2025 ASK medyanı, sabit). Kör: MT5 XAUUSD M30 (spread puan × 0,01). M30 çözünürlükte
yalnız 30 dk'lık giriş penceresi ve +60 dk çıkış kullanılabilir.

## Tanım (Londra saati)
- Fiks F ∈ {AM 10:30, PM 15:00}. Fikse giden hareket r = P(F) / P(F − 30 dk) − 1.
- |r| ≥ e (e ∈ {%0,15, %0,30}) → F'de **ters yönde** gir (r > 0 ise SAT, r < 0 ise AL), F + h'de çık; h ∈ {30, 60} dk.
- 2 fiks × 2 eşik × 2 çıkış = 8 hücre. Ölçü: net bp (giriş/çıkış spread'i dahil).
- Taban: aynı saatte |r| < e günlerinde aynı yönlü (sign r) ters işlem, yani fiksin tetiksiz hâli.

## Ölçüt (her hücre)
ESKİ (→ 2021-10) ve YENİ'de ikisinde de ort > 0; tüm dönem bootstrap P(ort > 0) ≥ 1 − 0,05/8 = 0,994; kör MT5'te (yalnız h = 60, 30 dk
pencere) ort > 0. Hepsi → B; P hariç → C+; yalnız iki dönem → C; değilse X.
Bilgi: yukarı (coşku) ve aşağı (korku) fiks hareketleri ayrı.
