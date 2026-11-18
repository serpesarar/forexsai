# Ön kayıt — Bitcoin'de 16:00 NY korkusu ve NDX korku gecesinin BTC'ye taşması (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
Korku gecesi ABD hisse endekslerine özgü: Avrupa'da yok (GN-06), altında yok (GI-02). BTC 7/24 işlem görüyor ama hacmi ABD saatlerinde
yoğun ve 2024'ten beri ABD ETF akışı var. İki soru:
- **H1:** BTC'nin kendi K1'i, 16:00 NY saatinde dönüyor mu? Dönüyorsa mekanizma ABD seans akışıdır, borsa yapısı değil.
- **H2:** NDX K1 gecesinde BTC almak (risk iştahının taşması) işe yarıyor mu?

## Veri
Binance BTCUSDT 5m: `btc_indep_2017_2021/data/btc_5m.parquet` (2017-08 → 2021-05) ve `btc_5y_20261021/data/btc_5m.parquet`
(2021-06 → 2026-10). Spot, finansman yok; gidiş-dönüş maliyet 10 bp (muhafazakâr).

## Tanım
- Gün d = NYSE işlem günü; giriş d 16:00 NY 5m açılışı; çıkış sonraki NYSE işlem günü 16:00.
- **H1 K1-BTC:** P16 ≤ BTC TWAP(09:30–16:00) × (1 − e) ∧ P16 < P15; e ∈ {%0,5, %1,0} (BTC oynaklığı NDX'in ~3 katı).
- **H2:** NDX Duka K1(d) (§2.71) → BTC AL.
- 3 hücre; taban = tetiksiz NYSE günleri. ESKİ = → 2021-10, YENİ = 2021-11 →.

## Ölçüt
İki dönemde de ort > 0 ∧ > taban ∧ tüm dönem P ≥ 1 − 0,05/3 = 0,983 → B; iki dönem ama P altı → C; değilse X.
