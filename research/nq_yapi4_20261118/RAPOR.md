# PC / BT / VD — opsiyon duyarlılığı, mega-cap genişlik, fiyat–VIX ayrışması (2026-11-18)

Ön kayıt `PROTOCOL.md` + EK-1. Kod `src/yapi4.py`, `src/ek1.py`; çıktılar `results/`. Epizot + aynı yıl rastgele başlangıç plasebosu.

| ID | Yapı | Sonuç | Hüküm |
|---|---|---|---|
| PC-01 | CBOE hisse put/call 5 g üst %20 → AL, alt %20 → SAT (2006–19) | Yüksek P/C AL 2006–12 **−56 / −146 bp** (yüzdelik 0,15 / 0,13; 2008), 2013–19 artı; düşük P/C SAT 2006–12 ≈ plasebo, 2013–19 0,97 / 0,91 — yön dönemler arasında tutarsız; son 5 yıl verisi yok | X |
| BT-01 BT1 | Zweig tipi itki (≤ %25 → ≥ %75 hisse 10 g SMA üstü) → AL | Plasebo altı (KEŞİF 0,28 / 0,42, TEST 0,48 / 0,45) | X |
| BT-01 BT2 | Tükenme (≤ 1/12 hisse SMA üstü) → 5 g AL | QQQ KEŞİF +112 (1,00) / TEST +87 (0,91), SPY 0,9985 / 0,82; **EK-1:** epizotların %65'i RSI2 < 10, RSI2 ≥ 10 kısmı plaseboyu geçmiyor (0,75 / 0,78) → C3b kopyası. C3b içinde doz: QQQ +80 (P 0,999) / +46 (P 0,81), SPY TEST −6 | tek başına X · C3b dozu C |
| VD-01 VD1 | QQQ ≥ +%0,75 ∧ VIX ≥ +%3 aynı gün → SAT | 1 g KEŞİF yüzdelik 0,76, TEST 0,93 (n 12), SPY TEST 0,96 (n 7), SPY KEŞİF ters, ^NDX 1990–99 0,82; 5 g 1990'larda ters | C |
| VD-01 VD2 | QQQ ≤ −%0,75 ∧ VIX ≤ 0 (korkusuz düşüş) → 5 g AL | KEŞİF 0,87, TEST 0,79, SPY TEST 0,95, ^NDX 1990–99 0,39 | C |

Ders: genişlik/duyarlılık göstergelerinin "aşırı" uçları NASDAQ'ta mevcut korku dönüşü ailesinin (C3b, K1) başka ölçüsü; yeni bilgi
taşımıyor. Fiyat–VIX ayrışması yön değiştiriyor ve son dönemde n çok küçük. Kart yok.
