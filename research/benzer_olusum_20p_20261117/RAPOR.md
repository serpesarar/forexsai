# Benzer oluşum taraması — 20 puan TP/SL, rastgele giriş (2026-11-17)

Ön kayıt `PROTOCOL.md`. Kod `src/build.py` (giriş + 20 puan BUY/SELL sonuçları + 30×1m oluşum), `src/knn.py` (yalnız geçmişte benzer arama, S1/S2,
plasebo), `src/ornek.py` (görsel örnek, `results/ornek_2025-08-13.png`). Veri Dukascopy NDX 1m 2018-01 → 2026-11.

## Kurulum
Her gün 10 rastgele giriş → **19.099 giriş**, her biri BUY ve SELL olarak ayrı: TP = SL = 20 puan (ask/bid, spread dahil), en çok 240 dk.
Rastgele girişte BUY_TP ≈ SELL_TP (yıl başına %30–47), beklenti tam spread kadar eksi (2018 ≈ −1 puan → 2026 ≈ −3,5 puan / işlem).
Oluşum = girişten önceki son 30 adet 1m mumun açılış/tepe/dip/kapanışı (son kapanışa göre puan, 120 boyut). Benzerler YALNIZ geçmişten
(≥ 1 gün önce), K = 20 (ikincil 50), ay ay genişleyen arşiv.

## Sonuçlar
**S1 — benzerler aynı TP'ye gidiyor mu?** (benzerlerin aynı yön TP oranı − geçmiş taban oranı; K = 20)
| dönem | BUY_TP sorgularının benzerleri | diğer sorguların benzerleri | SELL_TP sorgularının benzerleri | diğer |
|---|---|---|---|---|
| BAĞIMSIZ 2018–21 | +0,001 | −0,035 | +0,005 | −0,019 |
| KEŞİF 2022–23 | +0,013 | +0,005 | +0,007 | −0,007 |
| TEST 2024–26 | +0,019 | +0,016 | +0,025 | +0,014 |
Fark (TP olanın benzerleri − olmayanın benzerleri) 0,3–3,6 puan; K = 50'de de aynı → **benzer oluşum aynı TP'yi taşımıyor.**

**S2 — işlem kuralı** (benzerlerin BUY_TP − SELL_TP ≥ +0,30 → BUY, ≤ −0,30 → SELL)
| dönem | n | net puan / işlem | isabet | P | rastgele komşu plasebo ort. (%95) |
|---|---|---|---|---|---|
| BAĞIMSIZ | 1.098 | −1,87 | %45,8 | 0,00 | −1,22 (−0,22) |
| KEŞİF | 698 | −2,02 | %44,8 | 0,00 | −1,67 (−0,66) |
| TEST | 1.120 | −3,66 | %40,7 | 0,00 | −3,03 (−2,03) |
K = 50: BAĞIMSIZ +0,69 (n 136, P 0,71) / KEŞİF −4,54 / TEST −3,48. Yıllar 9'un 1'inde artı (2019, n 4). **BZ-01/02 X.**

## Görsel örnek
`results/ornek_2025-08-13.png`: BUY_TP olmuş bir sorgu ve en benzer 5 geçmiş oluşum — görsel olarak gerçekten benzer, 5'in 4'ü BUY_TP.
Tek örnek "yapı tekrar ediyor" dedirtir; 19.099 girişte bu oran taban oranından ayrılmıyor (E140: gözle seçilen örnek).

## Hüküm
20 puanlık sabit braketle rastgele girişte "kazanan oluşumun geçmişteki benzerleri de aynı TP'ye gider" iddiası tutmuyor; benzerlik araması
görsel olarak benzer oluşumları buluyor ama bunların sonucu yazı-tura + spread. ME-02 (mum eşleştirme) sonucunun sabit 20 puan braketle tekrarı.
