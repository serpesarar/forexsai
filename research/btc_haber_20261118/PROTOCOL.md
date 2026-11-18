# Ön kayıt — Bitcoin'de ABD korkusu ve haber ayrımı (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "BTC çok hareketli, derin araştır". Defter §2.11–2.12 (36 fikir + scalping) ve YK-06 okundu.
BTC-S05 (1 s negatif şok fade, saat/haber ayrımı yok) X; BTC-X03/X04 QQQ getirisi → BTC X. Yeni olanlar: NDX korku gecesi
zaman ayrışması (YK-06'nın derinleşmesi), ABD saatlerinde haber ayrımlı şok, olay günü devamı (§3-38).

## Veri ve maliyet
Binance BTCUSDT 5m 2017-08 → 2026-10-20. CFD maliyeti (Pepperstone, §2.11): gidiş-dönüş 4 bp (muhafazakâr) + uzun swap 3,84 bp/gece
(kısa için de 3,84 kabul). NDX K1 bayrağı NDX Duka'dan (§2.71). Makro takvim CPI/NFP/FOMC/JH (→ 2026-10-02).
ESKİ 2017-08 → 2021-10, YENİ 2021-11 → 2026-10. Bonferroni: 7 hücre → P ≥ 1 − 0,05/7 = 0,993.

## H1 — NDX korku gecesi → BTC: hangi dilim? (3 hücre)
NDX K1(d) → BTC AL; (a) d 16:00 → d+1 09:30 (gece), (b) d+1 09:30 → 16:00 (ertesi seans), (c) d 16:00 → d+1 16:00 (YK-06 referansı).
Taban: K1 olmayan NYSE günleri, aynı dilim. Ölçüt: ESKİ ve YENİ'de ort > taban ∧ ort > 0, tüm dönem P(fark) ≥ 0,993 → B; P altı → C+.

## H2 — Habersiz ABD gününde sert BTC düşüşü (2 hücre)
NYSE günü, takvimde olay yok; 10:00–15:30 NY 30 dk getirisi ≤ −k·σ (σ = önceki 30 günün aynı saatlerdeki 30 dk getirilerinin std'si),
k ∈ {3, 4}; günün ilk tetiği; sonraki 5m açılışında AL → d+1 16:00. Taban: aynı gruptaki günlerde rastgele 30 dk bar sonrası giriş.
Olay günü aynı işlem bilgi olarak. Ölçüt: habersiz grupta iki dönemde ort > taban ∧ > 0, P ≥ 0,993 → B; P altı → C+.

## H3 — ABD olay günü BTC büyük hareketi devam (2 hücre)
Olay günü d: BTC 08:00 → 16:00 NY getirisi |r| ≥ k·σ_gün (σ_gün = önceki 30 günün aynı pencere std'si), k ∈ {1,5, 2,0}; 16:00'da sign(r)
yönünde gir → d+1 16:00. Kontrol: olay olmayan günlerde aynı işlem. Ölçüt: olay grubunda iki dönemde ort > 0 ∧ > kontrol, P ≥ 0,993 → B;
P altı → C+.
