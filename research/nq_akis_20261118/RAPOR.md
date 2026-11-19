# NA-01…04 — NASDAQ'ta mekanik akış ve dış bilgi (2026-11-18)

Ön kayıt `PROTOCOL.md` (+ EK-1 VP1 kopya kontrolü, EK-2 ihale × faiz rejimi). Kod `src/`, çıktılar `results/*.json`.
Veri: ^NDX günlük 1985+, QQQ 1999+, ^VXN 2001+ (yfinance); Hazine ihaleleri FiscalData `auctions_query` (10/30 yıl nominal,
1979–2026-10); Dukascopy NDX 1m 2018-04+; MT5 NAS100 2m (bağımsız); Binance BTC 5m.

## Özet
| ID | Yapı | Sonuç | Hüküm |
|---|---|---|---|
| NA-01 | Oynaklık hedefli fon akışı (ΔE5 vekil pozisyon) | Kaldıraç azaltma sonrası SAT **ters**: 5 gün +98 bp vs taban +42 (KEŞİF 2012–21, P 0,007 ters yönde) — korku dönüşünün kopyası. Kaldıraç artırma AL KEŞİF −13, TEST +58 (tutarsız) | X |
| NA-02 | Varyans primi (VXN − RV20) yüksek → AL | VP1 h20 KEŞİF 2001–21 fark +121 bp (P 0,98, 16/19 yıl), TEST +95 (P 0,90, 5/6 yıl), QQQ aynı; iki yarı da artı (2001–10 +207, 2011–21 +47). EK-1: VXN düzeyi düşükken bile KEŞİF +132 (P 0,99), TEST +67 (P 0,85) → korku düzeyi kopyası değil. TEST P eşiği (0,983) geçilmedi | **C+** |
| NA-02 | Düşük prim SAT / negatif prim AL | yön dönemler arasında dönüyor | X |
| NA-03 | Hazine 10/30 yıl ihale günü 13:00→16:00 | ESKİ 2018–21 −15 bp, KEŞİF 2021–24 −21 bp (P 0,99); zayıf ihale (bid-to-cover < son 6 medyanı) 13:02 SAT +26/+28 bp P 0,996–0,998, **MT5 bağımsızda birebir**. TEST 2024-07 → **yön döndü**: ihale günü +21/+26, zayıf SAT −5, güçlü AL +40/+51. EK-2: faiz yükselen rejimde de TEST eksi → faiz rejimi açıklamıyor | X (rejim dönüşü) |
| NA-03 | Günlük (^NDX 1990+): ihale günü / ertesi gün | taban farkı yok (KEŞİF +5 vs +7) | X |
| NA-04 | BTC hafta sonu → NDX Pazar açılışı | Açılış boşluğu BTC'yi giderek fiyatlıyor (korelasyon ESKİ 0,10 → KEŞİF 0,43 → TEST 0,55; eğim 0,02 → 0,16). Sonrasında devam ya da eksik tepki yok; KEŞİF'te P ≥ 0,90 hücre yok, TEST en iyi KEŞİF hücresi −133 bp | X |

## Ana dersler
1. **Zorunlu akışın işareti çağa bağlı.** Hazine ihalesi 2018–2024'te iki bağımsız beslemede güçlü ve tutarlı bir satış
   baskısıydı; 2024 ortasından itibaren tersine döndü. Ne faiz yönü ne ihale gücü dönüşü açıklıyor. Yayınlanmış, herkesin
   takviminde olan bir olay; §3-41 ile tutarlı: izlenen akış fiyatlanır, sonra aşırı fiyatlanıp ters döner.
2. **Mekanik kaldıraç azaltma satış baskısı değil.** Oynaklık sıçraması sonrası NASDAQ yükseliyor (korku ailesinin bir yüzü).
   Fon akışı gerçekse bile fiyatı ortalamada aşağı itmiyor; dönüşü satın alanlar baskın.
3. **Varyans primi bilgi taşıyor ama yavaş ve seyrek.** Primin yüksek olduğu günlerin %20'sinde 20 günlük tutuş tabanın
   ~+100 bp üstünde. 20 günlük örtüşen pencereler yüzünden etkin bağımsız gözlem az (yılda ~2–4 epizot); TEST P 0,90.
   Rejim etiketi / doz aday, tek başına kural değil.
4. **BTC hafta sonu bilgisi Pazar 18:00 açılışında fiyatlanıyor.** BTC–NDX bağının artışı açılış boşluğuna geçiyor, sonrasında
   kenar kalmıyor.

## Kart
B yok → 2. KURAL kartı çıkarılmadı. VP1 C+ için öneri: ileri gölge etiketi (`vrp_pct ≥ 0,80`) ve mevcut uzun kurallarda
(C3b, KSG, korku gecesi) doz boyutu olarak ön kayıtlı sınama.
