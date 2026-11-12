# QS-06 — Ay sonu akışının anatomisi (S&P 500 + Nasdaq) ve ABD'ye özgü ikinci zorunlu akış — ön kayıt (2026-11-11)

Kullanıcı: "bu mantıkla S&P 500 ve Nasdaq üzerinde yeni denemeler, yolları genişlet". Bilinen: R1 (D−3→D ters yön, B), E2 uzun (D→D+3, B),
döngü kart 6/6, F1 son gün 15:30→16:00 (B−, kör 3/3), S&P 500'de döngü en temiz (US500 Sharpe 1,03).
**Çoklu bakış uyarısı (E23):** aynı ABD geçmişine QS-03…05'te 11 hipotezle bakıldı. Bu turda seçim yalnız KEŞİF'te / tek sembolde yapılır,
karar yalnız seçimde kullanılmamış veride verilir. Defter: OPEX (GF-02 H15) X olduğu için açılmadı. Sonuçlar görülmeden yazıldı.

## A1 — Gün × seans akış haritası (ileri yürüme)
- İşaret s = R1 yönü (D−3 kapanışında Δ = SPY − TLT ay içi; Δ ≥ +%2 → s = −1, ≤ −%2 → s = +1; arada atla).
- Hücreler: gün k ∈ {D−2, D−1, D, D+1, D+2, D+3} × seans {GECE: önceki kapanış → açılış, GÜN: açılış → kapanış} = 12 hücre.
  Hücre getirisi = s × seans getirisi (brüt, ETF açılış/kapanış; QQQ+SPY ortalaması).
- **Seçim (yalnız KEŞİF 2002-08→2013-12):** |t| ≥ 2,0 olan hücreler; işlem yönü = işaret(ort)·s.
- **Karar (seçilen her hücre):** (1) TEST 2014-26 QQQ+SPY aynı işaret, net (−2 bp) ort > 0, P ≥ %90; (2) SPY 1993-2002 (sentetik tahvil
  sinyali) aynı işaret > 0; (3) broker NAS100 ve US500 2018-26 (GECE 16:00 → 09:30, GÜN 09:30 → 16:00, maliyet + swap) ikisi de > 0.
  1–3 → **B−** · 1 ∧ (2 ∨ 3) → **C+** · diğer **X**. Hiç hücre seçilmezse A1 = "harita düz".

## A2 — F1'in kardeş yarım saatleri (MOC akışı kaç güne yayılıyor, ertesi sabah dönüyor mu?)
Öncüller: dengeleme emirleri son 2-3 günün kapanışlarına yayılır (R1 gün gün: gün1 +24, gün3 +19); kapanış baskısı ertesi açılışta geri döner.
- **A2a:** D−1 günü 15:30→16:00, s yönünde. **A2b:** D−2 günü 15:30→16:00, s yönünde.
- **A2c:** D+1 günü 09:30→10:00, E2 yönünde (Δ_D ≥ +%2 → UZUN; yalnız uzun bacak, QS-04).
- Seçim/keşif sembolü: yok (öncül önceden yazıldı). Kör: broker NAS100, US500, US30, US2000 (2018/2020→) + Dukascopy NDX 1m (2021→).
- Ölçüt (hücre başına): broker dört sembolün ≥ 3'ü artı ∧ en az ikisinde P ≥ %90 ∧ Dukascopy > 0 → **B−**; dört sembolden ≥ 3 artı → **C**;
  diğer **X**. Kontrol: aynı yarım saat, tüm günler.

## C — Şirket hisse geri alım yasağı (ABD'ye özgü zorunlu talep kesintisi)
Mekanizma: S&P 500 şirketleri çeyrek sonuna ~2 hafta kala geri alımı durdurur, bilanço açıklanınca (~çeyrek sonrası 3-4. hafta) yeniden başlar.
ABD geri alımları yılda ~1 trilyon $ (2004 sonrası büyüdü); yasak döneminde endeksin "taban alıcısı" yoktur.
- Q = çeyrek ayının son işlem günü. **YASAK** = [Q−10, Q+15] işlem günü; **AÇIK** = diğer günler. Ay dönümü karıştırıcısını atmak için her ayın
  son 1 ve ilk 3 işlem günü iki gruptan da çıkarılır; ayrıca R1 pencereleri (D−3…D) çıkarılır.
- Ölçü: günlük kapanış → kapanış ortalaması, AÇIK − YASAK (bp/gün), ay-blok bootstrap.
- Dönemler: ABD SPY+QQQ 2004-2014 / 2015-2026 (geri alım büyük); 1993-2003 SPY (geri alım küçük → fark küçük beklenir).
  **Plasebo:** 12 yabancı endeks + GDAXI/STOXX50E/N225/FTSE, aynı takvim (geri alım küçük → fark ≈ 0 beklenir).
- Ölçüt: (1) ABD iki dönemde AÇIK − YASAK > 0, ikisinde P ≥ %90; (2) yabancı havuz farkı ABD farkının yarısından küçük; (3) 1993-2003 farkı
  2004-26'dan küçük (doz). Üçü → **B−** (gün kapısı/boyut adayı) · (1) → **C** · diğer **X**.

## Deneme sayacı
QS-03…05: 11 · QS-06: A1 (seçilen hücre sayısı kadar) + A2 (3) + C (1).
