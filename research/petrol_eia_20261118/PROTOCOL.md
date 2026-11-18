# Ön kayıt — Petrol EIA haftalık envanter tepkisi: devam mı, dönüş mü? (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
HB-03 makro sürpriz sınaması NDX/XAU/USOIL için CPI/NFP/FOMC takvimini kullandı; EIA envanter raporu ayrı sınanmadı. Petrolde
haftanın en büyük planlı haberi EIA'dır (Çarşamba 10:30 ET; Pazartesi tatilse Perşembe 11:00).

## Veri
MT5 SpotCrude M30 (2018-05 → 2026-11; spread puan × 0,001). Tek besleme → en fazla C+.

## Tanım
- Olay günü: Çarşamba (Pazartesi NYSE tatiliyse Perşembe, saat 11:00). Olay saati E (10:30 / 11:00).
- Tepki R = P(E + 30 dk) / P(E) − 1. |R| ≥ e, e ∈ {%0,5, %1,0}.
- **Devam:** E + 30 dk'da R yönünde gir; çıkış 14:30 aynı gün (uzlaşma) veya ertesi işlem günü 14:30. **Dönüş** bunun tersidir.
- 2 eşik × 2 çıkış = 4 hücre (dönüş = devamın aynası).
- **Kontrol:** EIA olmayan günlerde (Pzt, Salı, Cuma) aynı saatte aynı büyüklükteki hareketler.

## Ölçüt
Devam getirisinin işareti ESKİ (→ 2021-10) ve YENİ'de aynı ∧ tüm dönem bootstrap P(işaret) ≥ 1 − 0,05/4 = 0,9875 ∧ kontrolden aynı
yönde farklı → C+ (o yönde kural). Aynı işaret, P altı → C. Değilse X.
