# HB-03 — Haber neden etkilemiyor gibi görünüyordu, kâr eden yapı var mı? (2026-11-05)

Ön kayıt: `PROTOCOL.md` + EK-1…9. Makro sürpriz aileleri (S1–S6, S8, S11) FinancialJuice arşivi inince eklenecek; bu sürüm ara rapordur.

## 1. Haber fiyatı etkiliyor mu?
Evet, gerçek olaylar güçlü etkiliyor; eski test hepsini tek "haber" türü saydığı için göremedi.

| Olay (NDX, 2024-25) | t=0 dakikası, olağana oran | t=+5 dk |
|---|---|---|
| CPI | 11,1× | 2,8× |
| FOMC | 5,8× | 3,1× |
| NFP | 4,4× | 2,2× |
| Trump Truth "Çin" (5 dk |getiri|) | 2,08× | |
| Trump Truth "tarife" (5 dk) | 1,49× | |

Genel başlık akışında (23.782 başlık, 10 hafta) başlık anında sıçrama YOK: plasebo oranı t=−30'dan t=+30'a düz, ≈1,1–1,3 (başlıklar zaten hareketli saatlere yığılıyor). Tekrar eden başlıklar yenilerden daha hareketli anlara denk geliyor (≈1,3 vs ≈1,15): tekrar, olayın sonucudur.
Ters sorgu (büyük hareketlerde en yakın ilgili başlık): dağılım plaseboya yakın, başlık akışı olayı işaret edemeyecek kadar yoğun. NDX'te +1…5 dk payı %29 vs plasebo %20: başlık çoğu kez hareketi izliyor.

**Üç neden:** (1) Başlıkların çoğu bilgi taşımıyor; yorum, tekrar, açıklama. (2) Gerçek olayda hareket ilk dakikada; 1 dk sonra girene yön bilgisi kalmıyor (CPI/NFP 5 dk tepkisine uy: 15/60/240 dk hepsi negatif). (3) Metinden yön çıkmıyor: Truth metin yönü P<%95, 240 dk'da işaret dönüyor. Oynaklık bilgisi var, yön bilgisi yok.

## 2. Haber ailelerinin hükmü (KEŞİF 2024-25, NDX)
| Aile | Sonuç | Hüküm |
|---|---|---|
| S7 FOMC öncesi uzun, sonrası ters | n=15, P %78; maxT yok | X |
| S3k/S15 CPI/NFP/FOMC tepkisine uy / ters | en iyi P %93, maxT ≥0,75 | X |
| S9 Truth tepkisine uy (4 konu × 3 ufuk) | en iyi petrol 240 dk +10 bp P %96, maxT 0,41 | X |
| S9b Truth metin yönü | en iyi 15 dk +4,1 bp P %94, 240 dk −12 bp | X |
| S16 Çift yönlü emir | P < %85 | X |
| S14 Hafta sonu boşluğu | keşif +29 bp, 2016-23 −14 bp | X |
| S18/S19 Bilanço tepkisi | S19 yarılar +18/−73 | X |
| **S13b Bilanço gecesi** | 2012-25 +16,7 bp vs komşu +3,9, plasebo p 0,0016, 12/14 yıl +; **2026 −14 / −30 bp (17 gece)** | **C** |

## 3. Bulunan kenar: NDX açılış aralığı kırılımı × VIX (C1)
**Kural:** önceki gün VIX ≥ 18,4 → 09:30 ET ilk 15 dk aralığı → 5m kapanış tepenin üstünde → sonraki bar açılışı BUY · stop aralık ortası · hedef 2R · 15:55 çıkış · 15:30 sonrası yeni giriş yok · günde ≤1. Kısa yok.
Parametre seçilmedi: aralık/stop/hedef DTS-02 repo varsayılanı; VIX eşiği Defter K1.

| Dönem | n | ort R | bp/işlem | Not |
|---|---|---|---|---|
| 1h 2016-06→2021-06 (görülmemiş) | 226 | +0,096 | +4,9 | P %99,4; VIX altı −0,049 |
| 30m 2021-07→2023 (görülmemiş, 2022 ayı) | 227 | +0,199 | +9,4 | P %99,8; 2022 +0,094 |
| 5m 2024 | 33 | +0,297 | +10,6 | |
| 5m 2025 | 62 | +0,474 | +24,5 | |
| 5m 2026 | 57 | +0,098 | +3,5 | P %68,5 |
| **Havuz 10 yıl** | **605** | **+0,185** | **+8,8** | **10/10 yıl +** · VIX<18,4 n=859 +0,004 · etiket permütasyon p 0,0004 |

Kart `go_live_cards/ndx_orb_vix.json`: **6/6** (n=152, +0,295R, P %99,7, yarılar +0,399/+0,190, spread×1,5 +0,292, 3,4 pt +0,267, icra farkı 0,028). En iyi 5 hariç +34,8R. En büyük düşüş −10R, en uzun kayıp 10 işlem.

### Uyarılar (kartı geçmesi bunları silmez)
- **2026 zayıf:** 5m +0,098; 15m −0,064; 30m 2024-26 ≈0. Beklenti için +0,295 değil **+0,10…+0,18R** kullanılmalı.
- **Eşleşik gün tabanı +0,057R, P %85: ön-kayıtlı ölçüt tutmadı.** Bu taban gelecek bilgisi taşır (E96); bilgisi temiz tabanlar p 0,0012 ve +0,159R P %99,8.
- 2024-26 birleşik VIX kırılımını görüp kombinasyonu öyle ön-kaydettim; temiz sınama 2016-23 ve 2026'dır.
- DAX'a aktarılmıyor (−0,055R); XAU/USOIL arşiv ekseni bozuk, sınanmadı.
- Saf MT5 2026-05→08 n=13 −0,172R (küçük örnek); broker+önbellek 2026 n=55 +0,083R.
- Yılda ~30-60 işlem; VIX düşükken hiç sinyal yok (2026 Q3-Q4: 9 işlem).
