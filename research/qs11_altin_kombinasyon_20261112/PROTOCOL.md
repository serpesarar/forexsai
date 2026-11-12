# QS-11 — Altında kombinasyon taktikleri (XAUUSD) — ön kayıt (2026-11-12)

Kullanıcı: "Altında farklı bir taktikle, farklı kombinasyonlarla, farklı şeyleri birleştirerek tekrar dene." Sonuçlar görülmeden yazıldı.

## Defter taraması (3. Kural)
Altında ayakta kalanlar: XS-01 günlük 55 gün tepesi + EMA200 uzun (B, gölge), MK-06 R0B_G1 1h yeni 20 bar tepesi AL (B+, gölge), MK-13 "önceki gün
altın > +%1 ise kırılımı ATLA" (A, kural içi filtre — kovalama cezası). Hep aynı mekanizma: altın trend taşır, uzun taraf, ama kısa vadede kovalamak ceza.
X olanlar: gün içi scalp, makro yön (reel faiz/dolar işareti dönmüş), RSI2 (C3 endeks etkisi), saat/seans (QS-09, TR-X18), varlıklar arası şok ertesi
gün (TR-T13; X2 VIX düşüşü C), GPR (PY-01), ay sonu ailesi (QS-10), SMC, fitil, formasyon, DBG ızgarası. **Hiç sınanmamış:** trend İÇİNDE düşüş
günü alımı (MK-13'ün aynası), altın/gümüş göreli değeri, COMEX opsiyon vadesi takvimi, hisseyle birlikte satılan altın (likidasyon) günü.

## Veri
GLD günlük düzeltilmiş (2004-11 → 2026-11, birincil), SLV (2006-04 →), SPY; broker XAUUSD M30 2018-06 → (maliyet `ortak.py`: spread × 1,5, swap
1,8 bp/gece); destek GC=F + SI=F 2000-08 → 2004-11 (karar dışı; vade geçişi sıçramalı). Giriş/çıkış günlük kapanış; broker'da 16:00 ET barının açılışı.

## Hipotezler (her biri TEK, donmuş hücre; seçim yok)
- **H1 trend içi düşüş günü (MK-13 aynası):** GLD kapanış > SMA200 ve SMA50 > SMA200; o günün getirisi ≤ −%1 → D kapanış AL, D+3 kapanış SAT.
  Taban: aynı trend durumundaki TÜM günlerde D→D+3 uzun.
- **H2 altın/gümüş göreli değer:** rel = r20(GLD) − r20(SLV); z = rel / (son 252 günün rel std'si). z ≤ −1 → altın AL, z ≥ +1 → altın SAT,
  D kapanış → D+5 kapanış; örtüşme yok (pozisyon kapanmadan yeni sinyal alınmaz). Taban: uzun bacak için tüm günlerde D→D+5 uzun, kısa için kısa.
- **H3 COMEX opsiyon vadesi:** E = ayın son işlem gününden 4 işlem günü önce (NYSE takvimi yaklaşımı). H3a vade sonrası rahatlama: E kapanış AL →
  E+3 kapanış. H3b vade öncesi baskı: E−3 kapanış SAT → E kapanış. Taban: tüm günlerde 3 gün uzun / kısa.
- **H4 likidasyon günü ("korku döner" altında):** SPY getirisi ≤ −%2 ve GLD getirisi ≤ −%1 aynı gün → D kapanış AL → D+5 kapanış. Taban: 5 gün uzun.

## Karar (her hipotez ayrı; 5 hücre Holm)
Ölçüm birimi işlem başı net bp (GLD'de 2 bp maliyet) ve **taban üstü fark** (aynı yönlü koşulsuz pozisyon; altının 2004-26 sürüklenmesi E13).
- (a) 2004-12 → 2026-10 taban üstü fark > 0, ay-blok bootstrap P ≥ %90; (b) iki kronolojik yarıda (2004-15 / 2015-26) fark ≥ 0;
  (c) broker XAUUSD 2018-06 → 2026-10 net (maliyet × 1,5 + swap) > 0; (d) Holm düzeltilmiş p ≤ 0,10.
- (a)(b)(c)(d) → **B−** (kart sonra) · (a)(b) → **C** · diğer → **X**. GC/SI 2000-04 destek olarak raporlanır.
- Sıklık raporlanır; 15–20/ay hedefi bu turun ölçütü değildir (ölçüt kenar).
