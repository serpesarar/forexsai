# BTC scalping veri seti: emir akışı + türev verileri (1 dakikaya hizalı)

Kapsam: 2026-10-21'de kuruldu. Kaynak yalnız Binance'in ücretsiz arşivi [data.binance.vision](https://data.binance.vision)
(S3 listesi: `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=...`). Ham dosyalar
`research/btc_scalp_20261021/data/raw/` (960 MB), çıktılar `research/btc_scalp_20261021/data/` (toplam 3,2 GB, ham dahil),
betikler `research/btc_scalp_20261021/scripts/`. Başlangıçta diskte 138 GB boş alan vardı; ham veri hiçbir anda 1,1 GB'ı geçmedi
(aggTrades zip'leri indirilip işlendikten hemen sonra silindi). Kutuya, Supabase'e ve mevcut proje dosyalarına dokunulmadı,
commit atılmadı. Tüm Python `/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python -I` ile çalıştı (numpy 2.4.6, pandas 2.3.3).
Arşiv zip'leri yalnız CSV olarak okundu; hiçbiri çalıştırılmadı.

Betik sırası (yeniden üretim, hepsi `python -I <betik> ...`):
1. `00_list_s3.py data/raw/s3_listing.json <prefix...>`: sayfalı S3 listesi (kapsam ve boyut tespiti)
2. `01_download.py data/raw/s3_listing.json data/raw`: SHA256 `.CHECKSUM` doğrulamalı paralel indirme
3. `02_build_futures.py data/raw data`: perp 1m, premium/mark/index 1m, funding
4. `01b_patch_daily.py data/raw data`: aylık dosyalardaki tam-gün boşluklarını günlük zip'lerle yamalar, ardından 3. adım yeniden çalıştırılır
5. `03_aggtrades_stream.py data/raw/s3_listing.json data/raw/aggtrades_tmp data/aggtrades_1s_days 2026-04-20 2026-10-20 4`: akış hâlinde aggTrades'ten 1 sn barlar
6. `05_consolidate_aggtrades.py data/aggtrades_1s_days data`: 1 sn birleştirme, 1m akış özellikleri, kline uzlaşması
7. `04_build_metrics.py data/raw data`: 5 dk metrics ve zaman damgası hizalama testi
8. `06_build_bookdepth.py data/raw data` ve `06b_build_cm_liq.py data/raw data`
9. `07_assemble.py data <btc_5y spot btc_1m.parquet>`: `btc_scalp_1m.parquet`
10. `08_validate.py data`: sızıntı testi, tasfiye vekili doğrulaması, funding tahmin geri-testi

---

## Kaynak kapsamı ve indirme bütünlüğü (hangi veri var, nereden nereye?)

### Takeaway
İstenen setlerin çoğu tüm dönem için mevcut: perp 1m klines, funding, 5 dk metrics, premium/mark/index 1m (2021-06-01 → 2026-10-20) ve
bookDepth (2023-01-01 → 2026-10-20). **USDT-M BTCUSDT için `liquidationSnapshot` arşivde hiç yok.** Bu yüzden bir vekil kuruldu ve
COIN-M BTCUSD_PERP tasfiyeleriyle (2023-06-25 → 2024-10-14) doğrulandı. bookTicker yalnız 2023-05-16 → 2024-03-30 arasında var ve
52,6 GB olduğu için kullanılmadı. İndirilen tüm dosyaların SHA256 değeri eşleşti; sorunlu dosya 0.

### Cited Findings
- S3 listesi (2026-10-21), `data/raw/s3_listing.json` ([data.binance.vision](https://data.binance.vision)):
  - `futures/um/monthly/klines/BTCUSDT/1m`: 81 zip, 2020-01 → 2026-09. Günlük karşılığı: 2.486 zip, 2019-12-31 → 2026-10-20.
  - `futures/um/monthly/fundingRate/BTCUSDT`: 81 zip, 2020-01 → 2026-09. **Günlük fundingRate klasörü yok.**
  - `futures/um/daily/metrics/BTCUSDT`: 2.241 zip, **2020-09-01** → 2026-10-20. 2021-06-01'den sonra eksik gün 0.
  - `premiumIndexKlines`, `markPriceKlines`, `indexPriceKlines` 1m: aylık 2020-01 → 2026-09, günlük 2019-12 → 2026-10-20.
  - `futures/um/daily/liquidationSnapshot/`: **0 dosya** (hiçbir USDT-M sembolü için yok).
  - `futures/cm/daily/liquidationSnapshot/BTCUSD_PERP`: 472 zip, 2023-06-25 → 2024-10-14, toplam 1,2 MB.
  - `futures/um/daily/bookDepth/BTCUSDT`: 1.385 zip, 2023-01-01 → 2026-10-20, 0,65 GB. Eksik günler: 2023-02-08, 2023-02-09, 2024-04-18, 2026-10-08.
  - `futures/um/daily/bookTicker/BTCUSDT`: 320 zip, 2023-05-16 → 2024-03-30, **52,58 GB**.
  - `futures/um/daily/aggTrades/BTCUSDT`: 2.486 zip, 45,1 GB toplam. Son 6 ay (184 gün) 2,84 GB, en büyük gün 65,7 MB.
- Binance README: "Each zip file has a `.CHECKSUM` file together in the same folder to verify data integrity". Mikrosaniye geçişi yalnız SPOT için belirtiliyor ("SPOT Data from January 1st 2025 onwards will be in microseconds"). Futures için böyle bir not yok — [binance-public-data README](https://github.com/binance/binance-public-data)
- Yerel doğrulama:
  - `download_log.tsv` dosyalarında 84 + 84 + 84 + 84 kline, 64 funding, 1.968 metrics, 1.385 bookDepth ve 472 cm_liq zip'inin tamamı `ok` (SHA256 eşleşti). Yama için indirilen 37 günlük premium/mark/index zip'i de `ok`.
  - aggTrades 184/184 `ok`.
  - **Futures dosyalarının hepsi milisaniye** (kline 77 başlıklı + 7 başlıksız dosya, aggTrades başlıklı). Spot'taki µs geçişi futures'ta yok. — `futures_quality_report.json`, `aggtrades_log.tsv`
- Bölge kısıtı: `fapi.binance.com/fapi/v1/fundingRate` çağrısı "Service unavailable from a restricted location according to 'b. Eligibility'..." döndü. Yani REST ile Ekim 2026 funding'i ya da güncel OI alınamıyor (bu makinede ölçüldü).

### Inferences
- Talep edilen 2021-10 başlangıcının hepsi kapsanıyor. Mevcut spot dosyasıyla hizalı olsun diye çıktılar **2021-06-01**'den başlatıldı.
- Ekim 2026 aylık dosyaları Kasım başında yayımlanınca (README: aylık dosyalar ayın ilk pazartesisi) funding tahminleri gerçek değerlerle değiştirilmeli. Bunun için `01_download.py` içindeki `M1` → `2026-10` yapılıp betikler yeniden çalıştırılır.

### Gaps
- Arşivin bookDepth, metrics ve liquidationSnapshot için resmî sütun tanımı yok (README yalnız aggTrades, klines ve trades'i belgeliyor). Anlamlar aşağıda **ampirik olarak** çıkarıldı.

---

## Spot ve perp 1m klines: taker akışı sütunları var mı?

### Takeaway
Önceki adımın spot `btc_1m.parquet` dosyası `trades`, `taker_buy_base` ve `taker_buy_quote` sütunlarını **zaten tutuyor**, bu yüzden yeniden kurulmadı.
Perp 1m kline seti eksiksiz: 2.833.920 satır, kayıp dakika 0, kopya 0, OHLC tutarsızlığı 0. 308 sıfır-hacimli perp barı var
(2023-11-10'da 99, 2024-10-28'de 89, 2022-05-28'de 35, 2022-05-01'de 29 dakika...).

### Cited Findings
- Spot şema: `ts, open, high, low, close, volume, quote_volume, trades, taker_buy_base, taker_buy_quote`. 2.833.450 satır, 470 eksik dakika (3 kesinti) — [02_veri_ve_broker.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1/02_veri_ve_broker.md)
- Perp kline CSV başlığı `open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore`. `close_time − open_time = 59,999 s` kuralına uymayan satır 0, `taker_buy > volume` olan satır 0 — `data/futures_quality_report.json`
- Perp/spot 1m hacim oranının yıllara göre medyanı: 2021 7,1×, 2022 3,8×, 2023 6,8×, 2024 7,5×, 2025 8,4×, 2026 9,5× — `data/validation_report.json`

### Inferences
- Taker satış hacmi = `volume − taker_buy_base` (sütun olarak eklendi). Binance kline'larında "taker buy" agresif alıcı hacmidir.
- Fiyat keşfi hacim bakımından perp ağırlıklı (5–9×). Akış özellikleri için perp birincil, spot ikincil kaynak olmalı.
- Sıfır-hacimli perp barları (2023-11-10 ~03:37–04:09 ve 2024-10-28) premium/mark/index boşluklarıyla aynı zamana denk geliyor. Bunlar borsa tarafı kesintiler olmalı. `perp_zero_vol=1` satırları backtest'te giriş/çıkış için dışlanmalı.

### Gaps
- 2023-11-10 ve 2024-10-28 perp kesintilerinin resmî nedeni araştırılmadı.

---

## Funding, premium, mark ve index (baz özellikleri)

### Takeaway
Funding: 5.844 uzlaşma (2021-06-01 00:00 → 2026-09-30 16:00), hepsi 8 saatlik ve 00/08/16 UTC'de; `calc_time` nominal saatten en çok 47 ms sapıyor.
Ekim 2026 için 60 uzlaşma **premium endeksinden Binance formülüyle tahmin edildi**. Formülün geri-testteki hatası çok küçük:
ortalama mutlak hata 0,027 bp, korelasyon 0,998, en kötü 2,1 bp. Premium/mark/index 1m'deki tam-gün boşluklar günlük dosyalarla yamandı.
Kalan eksik dakika: premium 66, mark 2, index 7.

### Cited Findings
- Binance funding formülü:
  - Premium endeksi "every 5 seconds" hesaplanır.
  - 8 saatlik ortalamada ağırlıklar 1, 2, …, n'dir.
  - Faiz bileşeni günde %0,03 (8 saatte %0,01).
  - "Funding Rate (F) = [Average Premium Index (P) + clamp (interest rate - Premium Index (P), 0.05%, -0.05%)] / (8 / N)".
  - Uzlaşma 00:00, 08:00 ve 16:00 UTC'de yapılır. Uzlaşmadan önce gösterilen oran bir tahmindir.
  — [Binance FAQ: funding rates](https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031)
- Premium kline'larında `count`, 1m başına 12 örnek (5 sn × 12 = 1 dk) taşıyor. 11 ve daha az olan 1m bar ~8 bin adet. Premium/mark/index kline'larında hacim hep 0 — `data/futures_quality_report.json`
- Geri-test (`08_validate.py`): 1m premium `(open+close)/2` serisi 480 dakikalık pencerede 1..480 ağırlıkla, clamp ile hesaplandı. 5.843 uzlaşmada ortalama mutlak hata 0,0273 bp, p99 0,164 bp, maks 2,09 bp, korelasyon 0,99814. Yalnız `close` kullanılınca ortalama mutlak hata 0,033 bp. — `data/validation_report.json`
- Ekim 2026 tahminleri (60 adet): ortalama %0,0031, medyan %0,0035, aralık −%0,0041…%0,0100 — `data/funding_with_oct_estimates.parquet`
- Yamalanan tam-gün boşlukları:
  - premium: 2021-07-01, 2021-07-24…27, 2022-10-02, 2023-02-24, 2026-06-29
  - mark: aynı günler + 2022-07-31
  - index: 2022-04-27, 2022-07-24/25/27/28/30/31, 2022-10-02, 2023-02-13, 2023-02-24, 2023-04-07/08, 2026-06-29
  - Kalan kısa boşluklar: 2022-07-12 13:13–14:32, 2023-11-10 03:37–04:09, 2024-08-12 10:01–10:04 UTC.
  — `01b_patch_daily.py` çıktısı, `futures_quality_report.json`
- Baz dağılımı:
  - `basis_perp_spot_bp` medyan −4,1 bp, p1 −7,5, p99 +10,5, min −235, maks +182.
  - `prem_close_bp` medyan −4,0, p1 −8,8, p99 +10,8, min −812, maks +610.
  — `validation_report.json`

### Inferences
- Medyan premium negatif (≈ −4 bp) olsa da funding çoğu zaman %0,01'e kilitli. Bunun nedeni, P değeri [−%0,04, +%0,06] aralığında kaldıkça clamp'in oranı faiz bileşenine çekmesi. Yani **funding, premium'un yalnız uç kısmını taşıyor**; scalping'de bilgi içeren seri `prem_close_bp` ve `funding_pred_running`.
- `funding_pred_running` bizim kendi nedensel tahminimiz: mevcut 8 saatlik pencerede, bu bar dahil, artan ağırlıklı premium ortalaması + clamp. Pencerenin son dakikasındaki değeri gerçekleşen orana 0,027 bp ortalama hata ile denk. Binance arayüzünde gösterilen "tahmini funding" ile birebir aynı olduğu doğrulanmadı.

### Gaps
- Ekim 2026'nın gerçek funding oranları (aylık dosya Kasım'da gelecek). REST bölgesel olarak engelli.
- 66 dakikalık premium boşluğu (yukarıdaki kesintiler) doldurulmadı. Bu dakikalarda satır NaN.

---

## Metrics 5 dk (OI, long/short oranları): zaman damgası pencerenin başı mı, sonu mu?

### Takeaway
**Damga anlamı 2024-03-04 00:00 UTC'de değişiyor.** Bu tarihten önce `create_time = T`, [T−5, T) penceresinin **sonu**; sonra
[T, T+5) penceresinin **başı**. Yani 2024-03-04'ten itibaren T damgalı satır, T'den 5 dakika sonrasının bilgisini taşıyor.
Damgayı ölçüm anı sanmak **5 dakikalık bir geleceğe bakma sızıntısı** üretir. Taker oranı ve OI değişimi aynı sonucu bağımsız olarak veriyor.
Birleşik sette `metrics_eff_ts` (gerçek pencere sonu) + **1 dk yayın payı** kullanıldı. Veri 566.368 satır (2021-06-01 → 2026-10-20 23:55),
416 eksik 5 dk dilimi var. Arşivde metrics kapsamı **2020-09-01**'de başlıyor.

### Cited Findings
- Test (`04_build_metrics.py` + ek analiz): `sum_taker_long_short_vol_ratio` ile perp 1m kline'lardan hesaplanan taker alış/satış oranı karşılaştırıldı (eşleşme ölçütü: göreli fark < %0,2).
  - [T−5, T) penceresinde eşleşme oranı: 2021-06…2024-02 aylarında %78–100. 2024-03-04'ten sonra ≈ %0.
  - [T, T+5) penceresinde eşleşme oranı: 2024-03-04'ten itibaren %55–87. Öncesinde ≈ %0.
  - Gün bazında geçiş: 2024-03-03 [T−5,T) %76 / [T,T+5) %0; 2024-03-04 %1 / %72. Son "eski" eşleşme 2024-03-03 23:55, ilk "yeni" eşleşme 2024-03-04 00:00.
  - Hizalı pencerede log-oran korelasyonu 0,997–0,999.
  — `data/metrics_quality_report.json` (`timestamp_alignment_test_taker_ratio`)
- OI ile bağımsız teyit: |OI(T) − OI(T−5)| ile 5 dk hacmin rank korelasyonu.
  - 2024-03 öncesi: hacim [T−5, T) penceresinde zirve yapıyor (0,620).
  - Sonrası: [T, T+5) penceresinde zirve (0,638).
  - Yani **OI anlık değeri de** 2024-03-04'ten sonra T+5'te alınıyor.
- REST belgeleri openInterestHist ve globalLongShortAccountRatio için `timestamp` = "End time of the period", basis için "Start time of the period" diyor. REST geçmişi yalnız son 30 gün / 1 ay. — [Binance USDⓈ-M: Open Interest Statistics](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics). **Arşiv 2024-03-04'ten sonra bu belgeyle çelişiyor** (damga pencere başında).
- Kalite:
  - Dosya içinde satırlar sırasız olabiliyor (ör. 2026-10-20 dosyası 00:25, 03:35, 04:05 diye başlıyor). Sıralandı.
  - Izgara dışı damga 0, kopya 0.
  - Eksik 5 dk dilimleri yıllara göre: 2021'de 283 (2021-06-22: 162, 06-23: 13, 11-26: 12), 2023'te 3, 2024'te 127 (2024-02-16 13:30 → 24:00), 2025'te 3.
  - OI = 0 olan satırlar 471 (2022-03-07/08, 2024-07-10…15, 2025-07-21, 2026-10-15) → NaN yapıldı.
  - NaN dağılımı: top-trader oranları 2021-12 → 2022-12 arasında çoğunlukla NaN (92 bin satır). Taker oranı 2022-01 → 2022-05 NaN (37 bin). Global L/S 5.787 NaN.
  - 2025-08 → 2026-03 aylarında [T, T+5) eşleşmesi gürültülü (medyan göreli hata %0,8–1,7, diğer aylarda %0,01–0,07). Pencere birkaç saniye kaymış olabilir.
  — `metrics_quality_report.json`
- Sızıntı testi (`08_validate.py`): satırdaki `taker_ls_vol_ratio_5m` değerinin sonraki 5 dakikanın kline taker oranıyla korelasyonu, aynı pencerenin kline oranının sonraki 5 dakikayla korelasyonuna her alt dönemde eşit. Örnek: 2026-04 → 10 için 0,057 vs 0,057; 2021-06 → 2022-12 için −0,033 vs −0,038. Yani fazladan gelecek bilgisi yok; kalan küçük korelasyon akışın kendi otokorelasyonu. `metrics_eff_ts > ts` olan satır sayısı 0.

### Inferences
- **Nedensellik kuralı:** `eff_ts = T` (T < 2024-03-04) veya `T + 5 dk` (sonrası). `avail_ts = eff_ts + 1 dk`. 1m satırı ts (kapanış ts+1m) yalnız `avail_ts ≤ ts+1m`, yani `eff_ts ≤ ts` olan metrics'i görür.
- 1 dk pay, 2025-08 → 2026-03'teki olası alt-dakika kaymasını ve yayın gecikmesini karşılamak için kondu. Canlı gecikme ölçülmediği için daha temkinli bir test `metrics_age_min ≥ 2` filtresi uygulayabilir.
- Geçişte bir kerelik 10 dakikalık sıçrama var (eff 23:55 → 00:05). Arada eff=00:00 satırı yok.
- Sütun eşlemesi (çıkarım, isimlerden ve REST uç noktalarından):
  - `count_toptrader_long_short_ratio` = top-trader **hesap** oranı
  - `sum_toptrader_long_short_ratio` = top-trader **pozisyon** oranı
  - `count_long_short_ratio` = global hesap oranı
  - `sum_taker_long_short_vol_ratio` = taker alış/satış hacmi (ampirik olarak doğrulandı)

### Gaps
- Arşiv dosyalarının canlı yayın gecikmesi (satır borsada ne zaman oluşuyor) ölçülemedi. REST engelli ve canlı kayıt yok.
- 2025-08 → 2026-03 gürültüsünün nedeni (pencere kayması mı, farklı hacim tanımı mı) çözülmedi. Bu dönemi kapsayan aggTrades (saniye çözünürlüklü) indirilmedi.

---

## Tasfiye verisi ve tasfiye VEKİLİ

### Takeaway
USDT-M BTCUSDT için arşivde tasfiye verisi **yok**. İki vekil kuruldu, eşikler doğrulamadan **önce** sabitlendi:

1. **5 dakikalık vekil:** OI düşüşü + büyük yönlü hareket + hacim patlaması + taker baskınlığı birlikte görülüyor. 1.475 long, 1.190 short pencere.
2. **1 dakikalık akış vekili:** OI kullanmıyor. 1.637 long, 1.593 short dakika.

İkisi de bağımsız COIN-M BTCUSD_PERP tasfiyeleriyle (2023-06-26 → 2024-10-13) güçlü örtüşüyor. 5 dk long vekilinin işaretli
pencerelerinde ortalama CM tasfiyesi 315.726 $; işaretsiz pencerelerde 3.649 $, rastgele plasebonun p99 değeri 11.286 $.
Ancak kapsama düşük: en büyük %0,5'lik tasfiye pencerelerinin yalnız %18'ini yakalıyor. Vekil "kesin ama seyrek" bir bayrak.

### Cited Findings
- Binance forceOrder akışı sembol başına "only the latest one liquidation order within 1000ms" iter, yani tam kayıt değil, bir örneklemdir — [USDⓈ-M Liquidation Order Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Liquidation-Order-Streams); [COIN-M aynı kural](https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-market-streams/Liquidation-Order-Streams). Arşivdeki `liquidationSnapshot` bu anlık görüntülerden oluşuyor (sütunlar: time, side, order_type, time_in_force, original_quantity, price, average_price, order_status, last_fill_quantity, accumulated_fill_quantity).
- CM ham verisi: 106.822 satır, **53.424'ü birebir kopya** (atıldı) → 53.398 olay. 2023-06-25 01:27 → 2024-10-14 05:27 UTC. SELL (long tasfiyesi) 32.826, BUY (short tasfiyesi) 20.572 — `data/cm_liq_quality_report.json`
- BTCUSD COIN-M kontrat büyüklüğü 100 USD — [CryptoPotato (2020 lansman haberi, ikincil kaynak)](https://cryptopotato.com/in-the-footsteps-of-bitmex-binance-launches-bitcoin-collateralized-125x-futures-contract/)
- **5 dk vekil tanımı** (`07_assemble.py`, ön-kayıt `P5`). Pencere W = [eff−5, eff):
  - `d_oi = OI(eff)/OI(eff−5) − 1`, yalnız ardışık satırlarda
  - `z_oi`: d_oi'nin 30 günlük (8.640 pencere) kayan ortalama/std ile z-skoru, istatistikler shift(1) (yalnız geçmiş)
  - `z_ret5`: W'deki perp log getirisinin 30 günlük std'ye bölümü
  - `z_lvol5`: log(W hacmi) z-skoru
  - `sell_share` = 1 − taker_buy/hacim
  - **long** = z_oi ≤ −2,5 ∧ z_ret5 ≤ −2,5 ∧ z_lvol5 ≥ 2 ∧ sell_share ≥ 0,55
  - **short** = z_oi ≤ −2,5 ∧ z_ret5 ≥ +2,5 ∧ z_lvol5 ≥ 2 ∧ sell_share ≤ 0,45
  - Sürekli skor `liq_proxy_score_5m = max(0, −z_oi) × z_ret5`
- **1 dk akış vekili** (ön-kayıt `P1`), perp 1m bar:
  - z_ret (log(c/o), 30 günlük std) ≤ −4 ∧ z_lvol ≥ 3 ∧ sell_share ≥ 0,65 → `liq_flow_long_1m`
  - Simetriği → `liq_flow_short_1m`
- Doğrulama (`data/validation_report.json`, 136.671 adet 5 dk pencere):

  | Vekil | İşaretli n | Ort. CM tasfiyesi (işaretli / işaretsiz) | Plasebo p50 / p99 | Pencerede CM tasfiyesi olma oranı (işaretli / işaretsiz) | Kapsama (en büyük %0,5) | İsabet (en büyük %0,5'te) | Spearman (skor) |
  |---|---|---|---|---|---|---|---|
  | long 5m | 384 | 315.726 $ / 3.649 $ | 4.112 / 11.286 $ | %95,3 / %7,7 | %17,8 | %31,8 | 0,196 |
  | short 5m | 248 | 166.418 $ / 2.102 $ | 1.759 / 7.830 $ | %93,1 / %6,0 | %12,9 | %35,5 | 0,162 |

  1m akış vekili (en büyük %0,1 dakika):

  | Vekil | İşaretli n | Ort. CM (işaretli / işaretsiz) | Kapsama | İsabet |
  |---|---|---|---|---|
  | long 1m | 374 | 199.574 $ / 796 $ | %11,7 | %21,4 |
  | short 1m | 303 | 86.649 $ / 442 $ | %8,9 | %20,1 |

### Inferences
- Vekil bayrakları tasfiye **kümelerini** güvenilir biçimde işaretliyor: işaretli pencerelerin %93–95'inde CM tarafında da tasfiye var ve ortalama hacim plasebonun ~30–90 katı. Buna karşın büyük tasfiyelerin çoğu (%82–87) eşikleri geçmiyor. Bu bayraklar "tasfiye oldu mu?" sorusunu tam yanıtlamaz, yalnız en belirgin kaskadları seçer.
- CM BTCUSD_PERP, USDT-M'den çok daha küçük bir piyasa ve kaynak bir örneklem (1 sn'de 1 olay). Dolayısıyla doğrulama yönü ve örtüşmeyi gösterir, **mutlak tasfiye miktarını** göstermez.
- 5 dk vekil, satırda **yalnız `avail_ts ≤ ts+1m` olduğunda** görünür (OI'ye bağlı olduğu için 1–6 dk gecikmeli). 1m akış vekili ise bar kapanışında bilinir ama OI teyidi yoktur.
- Isınma: z-skorları ilk ~7 gün (2021-06-01 → 06-07) NaN. Bu dönemde bayraklar 0'dır, "tasfiye yok" anlamına gelmez.

### Gaps
- USDT-M gerçek tasfiye akışı ancak canlı WebSocket kaydıyla toplanabilir (ileriye dönük). Geçmişi ücretsiz kaynaktan yok.
- Vekil eşikleri tek bir ön-kayıtla seçildi. Duyarlılık taraması yapılmadı (bilinçli olarak: sonuçlara bakıp eşik ayarlamak sızıntı olurdu).

---

## Order book derinliği (bookDepth) ve bookTicker

### Takeaway
bookDepth 2023-01-01 → 2026-10-20 arası **tamamen** işlendi (12 aylık sınır gerekmedi, ham veri 624 MB). Kayıt sıklığı ~30 sn
(p50 30 s, p90 33 s, p99 42 s), toplam 3.906.591 anlık görüntü. Seviyeler mid'den ±%1…±%5 **kümülatif** notional; **±%0,2 seviyesi 2026-01-15'ten itibaren** var.
1m dengesizlik serisi 1.964.576 dakika. Uyarı: 13.160 dakikada açıkça bozuk anlık görüntü var. Özellikle **2025-10-11…14 ve 2026-09-04…06 gün boyu**
bir tarafta %1–2 arasında hiç likidite görünmüyor. Bu satırlar `bd_suspect=1` ile işaretli.

### Cited Findings
- Ham format `timestamp,percentage,depth,notional`. Örnek (2026-10-20 00:00:01): −5…−0,2 ve +0,2…+5 olmak üzere 12 satır. Kümülatiflik ihlali 0 (`noncumulative_snaps: 0`) — `data/bookdepth_quality_report.json`
- Aylık kapsama (anlık görüntüsü olan dakika / takvim dakikası):
  - 2023-01 %85,5, 2023-02 %87,6, 2023-03 %96. Erken 2023'te her gece yarısı ~11 dk boşluk var; 2023-01-09/15/16/21/28 ve 2023-02-07'de neredeyse boş gün.
  - 2023-07 → 2025-04 arası ≈ %97–100.
  - 2025-05 → 2026-05 arası %95–99.
  - 2026-10 %89,7 (10-08 dosyası yok).
  - Aralıkta anlık görüntüsü olmayan dakika toplamı 35.578.
- Şüpheli anlık görüntü örneği (2026-09-04 12:00:04): ask_n_0p2 = ask_n_1 = ask_n_2 = 974.563 USDT, ama ask_n_3 = 141,6 M. 2025-10-12 12:00: bid_n_1…bid_n_4 = 2,14 M sabit. Bu günlerde |imb_1| > 0,95 olan dakikaların payı %96–100.
- Glassnode, Binance'in yalnız mid'e yakın seviyeleri ve ardından değişiklikleri yayımladığını, uzak seviyelerin bu yüzden "minimum" sayılması gerektiğini not ediyor (Binance'in kendi belgesi değil) — arama özeti, [Glassnode studio](https://studio.glassnode.com/charts/derivatives.PerpetualOrderbookHeatmap?a=BTC)
- bookTicker: 2023-05-16 → 2024-03-30 (320 gün), 52,58 GB, sonra kesilmiş — S3 listesi.

### Inferences
- `bd_imb_p = (bid_n_p − ask_n_p)/(bid_n_p + ask_n_p)`, kümülatif ±p% bandı. Pozitif değer alış tarafının daha derin olduğunu gösterir. Ortalama imb_1 +0,017, std 0,187.
- Şüpheli günlerdeki örüntü (bir tarafın %1–2'ye kadar düz kalması), Binance'in referans fiyatının bayatladığını ya da defter yeniden kurulumunun bozulduğunu düşündürüyor. **Gerçek likidite boşluğu olarak okunmamalı.** 2025-10-10/11 tarihi bilinen büyük kripto çöküşüne denk geliyor, ama dört gün süren tek taraflı defter gerçekçi değil.
- 30 sn kadansla bookDepth mikroyapı (saniye altı) sinyali vermez. Dakika ölçeğinde "derinlik eğimi" ve dengesizlik özelliği verir.
- bookTicker (en iyi alış/satış tick'i) yalnız ~10,5 ay için ve 52 GB. Kapsamı ana backtest dönemini karşılamadığı için atlandı.

### Gaps
- `percentage` değerinin mid'e mi yoksa en iyi fiyata mı göre hesaplandığı resmî olarak bilinmiyor.
- Anlık görüntü damgasının (`YYYY-mm-dd HH:MM:SS`) UTC olduğu varsayıldı. 00:00:01, 00:00:30… ızgarası ve dosya-gün sınırlarıyla tutarlı ama kaynakta yazılı değil.
- Şüpheli günlerin nedeni doğrulanmadı.

---

## aggTrades → 1 saniyelik akış barları (son 6 ay)

### Takeaway
2026-04-20 → 2026-10-20 arasındaki 184 günün tamamı yapıldı (3 aya düşürmek gerekmedi). 2,84 GB zip akış hâlinde indirildi;
her zip doğrulandıktan ve işlendikten hemen sonra silindi. Sonuç 14.991.587 adet 1 sn bar (saniyelerin %94,3'ünde işlem var, en uzun boşluk 16 s).
aggTrade kimliklerinde boşluk 0. 1m'ye toplanan hacim kline hacmiyle medyan %0 farkla uyuşuyor (p99 %0,6).

### Cited Findings
- Sütunlar: Aggregate tradeId, Price, Quantity, First tradeId, Last tradeId, Timestamp, "Was the buyer the maker". Kaynak `/fapi/v1/aggTrades` — [binance-public-data README](https://github.com/binance/binance-public-data)
- Yerel kalite (`data/raw/aggtrades_log.tsv`, `data/aggtrades_quality_report.json`):
  - 184/184 dosya `ok`, hepsi `ms header`
  - Günlük 0,77–2,26 M aggTrade
  - `agg_id_gaps=0` (her gün)
  - Kopya saniye 0, 60 s'den uzun boşluk yok
- Uzlaşma (264.960 dakika): hacim göreli farkı p50 0, p99 %0,60, maks %291 (birkaç düşük hacimli dakikada sınır kayması). Taker alış farkı p50 0, p99 %0,39. İşlem sayısı birebir eşit olan dakika %69,6 (|fark|/sayı p99 %0,5).

### Inferences
- `is_buyer_maker=True` olduğunda agresör satıcıdır. `buy_qty` taker alış, `sell_qty` taker satış hacmi.
- `large_*_qty` eşiği tek aggTrade ≥ 5 BTC (`LARGE_BTC`). Sabit eşik; fiyat seviyesine göre ölçeklenmiyor.
- Küçük kline/aggTrade farkları dakika sınırına düşen işlemlerin farklı dakikaya yazılmasından kaynaklanıyor olmalı (doğrulanmadı). Bilgi kaybı ihmal edilebilir.

### Gaps
- Spot aggTrades (aynı 6 ay ~2,28 GB) işlenmedi. İstenirse aynı betik spot için uyarlanabilir: spot CSV'de 8 sütun var ve 2025'ten sonra zaman birimi µs.
- 6 aydan eski dönem için saniye çözünürlüğü yok. Uzun backtest'lerde 1 sn ve agg özellikleri yalnız 2026-04-20 sonrası için var.

---

## Veri sözlüğü

### Takeaway
Tüm zamanlar UTC. 1m dosyalarda `ts` = bar AÇILIŞI ([ts, ts+60 s)). **Birleşik dosyada her satırdaki her değer bar KAPANIŞINDA (ts+60 s) bilinir.**
Bir satıra dayanan karar en erken **ts+1m açılışında** icra edilmelidir (CLAUDE.md 2. Kural, ölçüt 5).

### Cited Findings (tümü yerel dosya; satır sayıları ilgili `*_report.json` dosyalarında)

| Dosya | Satır | Kapsam (UTC) | Kadans / not |
|---|---|---|---|
| `data/btc_scalp_1m.parquet` (605 MB, 77 sütun) | 2.833.920 | 2021-06-01 00:00 → 2026-10-20 23:59 | tam dakika ızgarası; eksik kaynak = NaN |
| `data/perp_1m.parquet` | 2.833.920 | aynı | eksik dakika 0, sıfır hacim 308 |
| `data/premium_1m.parquet` / `mark_1m` / `index_1m` | 2.833.854 / 2.833.918 / 2.833.913 | aynı | eksik 66 / 2 / 7 dk; `n_samples` = kline count |
| `data/funding.parquet` | 5.844 | 2021-06-01 00:00 → 2026-09-30 16:00 | 8 saatlik; gerçek oranlar |
| `data/funding_with_oct_estimates.parquet` | 5.904 | → 2026-10-20 16:00 | `estimated=1` olan 60 satır tahmin |
| `data/metrics_5m.parquet` | 566.368 | 2021-06-01 00:00 → 2026-10-20 23:55 (ham damga) | 416 eksik dilim |
| `data/metrics_5m_effective.parquet` | 566.368 | | + `eff_ts`, `avail_ts`, vekil ara sütunları |
| `data/bookdepth_snap.parquet` (357 MB) | 3.906.591 | 2023-01-01 00:06:05 → 2026-10-20 23:59:30 | ~30 s; `bid_n_*`/`ask_n_*` USDT kümülatif |
| `data/bookdepth_1m.parquet` | 1.964.576 | 2023-01-01 → 2026-10-20 | bar içindeki son anlık görüntü |
| `data/perp_aggtrades_1s.parquet` (543 MB) | 14.991.587 | 2026-04-20 00:00:00 → 2026-10-20 23:59:59 | 1 s, işlem olmayan saniye satırsız |
| `data/perp_aggflow_1m.parquet` | 264.960 | 2026-04-20 → 2026-10-20 | 1 s'den 1m |
| `data/cm_liq_1m.parquet` / `cm_liq_5m.parquet` | 28.179 / 18.897 | 2023-06-25 → 2024-10-14 | yalnız doğrulama; COIN-M |

**`btc_scalp_1m.parquet` sütunları** (birimler; float32 olanlar hacim, oran ve z-skorları; fiyatlar ve funding float64):
- `ts`: bar açılışı (datetime64[ns, UTC]).
- `spot_open/high/low/close` (USDT), `spot_volume` (BTC), `spot_quote_volume` (USDT), `spot_trades` (adet), `spot_taker_buy_base` (BTC), `spot_taker_buy_quote` (USDT), `spot_taker_sell_base` (BTC) = volume − taker_buy. Kaynak: btc_5y spot 1m.
- `perp_*`: aynı alanlar, Binance USDT-M BTCUSDT perpetual.
- `spot_missing` (spot satırı yok, 470 dk), `spot_zero_vol` (72 dk, 2023-03-24 durdurması), `perp_zero_vol` (308 dk): int8 bayraklar.
- `prem_open/high/low/close`: Binance premium endeksi (oran; ×1e4 = bp). `prem_close_bp`.
- `mark_close`, `index_close` (USDT).
- `basis_perp_spot_bp` = (perp_close/spot_close − 1)×1e4; `basis_perp_index_bp`; `basis_mark_index_bp`. Hepsi aynı bar kapanışı, gecikme yok.
- `funding_rate_last`: uzlaşma zamanı (`funding_time`, nominal saat + ms) ≤ ts+1m olan son oran (8 saatlik kesir, ör. 0,0001 = %0,01). `funding_last_time`: nominal uzlaşma saati. `funding_last_estimated`: Ekim 2026 tahmini ise 1.
- `min_to_next_funding`: bar kapanışından sonraki 00/08/16 UTC uzlaşmasına kalan dakika (1…480).
- `funding_pred_running`: kendi canlı tahminimiz (yukarıda); bar dahil, kapanışta bilinir.
- `metrics_eff_ts`: kullanılan metrics satırının gerçek pencere sonu. `metrics_age_min` = (ts+1m − eff_ts) dakika (≥ 1).
- `oi_btc`, `oi_usd`: açık pozisyon (BTC / USDT). `top_ls_count`, `top_ls_pos`, `global_ls_count`: long/short oranları. `taker_ls_vol_ratio_5m`: 5 dk taker alış/satış hacim oranı. `oi_chg_5m`, `oi_chg_5m_z`.
  - Gecikme: `eff_ts + 1 dk ≤ ts+1m`. `metrics_age_min > 15` ise değerler NaN (1.410 satır).
- `liq_proxy_long_5m`, `liq_proxy_short_5m` (0/1), `liq_proxy_score_5m`: 5 dk vekil; gecikme metrics ile aynı.
- `perp_ret_1m_z`, `perp_lvol_1m_z`: 30 günlük geçmiş istatistikle z. `liq_flow_long_1m`, `liq_flow_short_1m` (0/1).
- `bd_imb_0p2`, `bd_imb_1`, `bd_imb_2`, `bd_imb_5`: derinlik dengesizliği. `bd_bid_n_1`, `bd_ask_n_1`, `bd_bid_n_5`, `bd_ask_n_5` (USDT, kümülatif). `bd_suspect` (0/1). `bd_snap_age_s`: kullanılan anlık görüntünün bar kapanışına göre yaşı (s).
  - Anlık görüntü bar içinde yoksa son 5 dk içindeki en yeni görüntü taşınır. 2023-01-01 öncesi NaN; ±%0,2 seviyesi 2026-01-15 öncesi NaN.
- `agg_buy_qty`, `agg_sell_qty` (BTC), `agg_n_agg`, `agg_n_trades`, `agg_max_agg_qty` (BTC), `agg_large_buy_qty`, `agg_large_sell_qty` (≥ 5 BTC aggTrade), `agg_max_1s_buy_qty`, `agg_max_1s_sell_qty`, `agg_n_active_sec` (1–60), `agg_vwap` (USDT). Yalnız 2026-04-20 sonrası.

**1 sn dosyası (`perp_aggtrades_1s`)**: `ts` (saniye başı), `open/high/low/close/vwap` (USDT), `buy_qty`, `sell_qty` (BTC), `buy_quote`, `sell_quote` (USDT), `n_agg`, `n_trades`, `max_agg_qty`, `large_buy_qty`, `large_sell_qty`.

### Inferences
- Nedensellik kararlarının özeti:

  | Kaynak | Değerin oluşma anı | Satır ts'de kullanım koşulu |
  |---|---|---|
  | Kline/premium/mark/index | bar kapanışı | aynı satır |
  | Funding | uzlaşma anı | funding_time ≤ ts+1m |
  | Metrics | eff_ts (2024-03-04 öncesi T, sonrası T+5 dk) | eff_ts + 1 dk ≤ ts+1m |
  | bookDepth | anlık görüntü zamanı | snap ∈ [ts, ts+1m) ya da daha eski (≤ 5 dk) |
  | aggTrades | saniye kapanışı | ilgili 1m bar |
  | z-skorları | | rolling(30 gün) istatistikleri `shift(1)` ile yalnız geçmişten |

- 1m spot kesintisi (2023-03-24 11:28–14:00) ve perp sıfır-hacim barları backtest'te dışlanmalı.

### Gaps
- Metrics ve funding'in canlı yayın gecikmesi ölçülmedi (1 dk pay bir varsayım).

---

## Kullanılamayan / eksik veri

### Takeaway
Ücretsiz arşivde şunlar ya hiç yok ya da kısa dönemli. **Gerçek USDT-M tasfiye akışı yok** (vekil var). **Tick düzeyinde en iyi alış/satış
(bookTicker) yalnız 2023-05 → 2024-03 arası** (kullanılmadı). bookDepth 2023 öncesi yok. aggTrades yalnız son 6 ay için işlendi.
Ekim 2026 funding'i tahmin. REST API bu bölgeden engelli.

### Cited Findings
- USDT-M `liquidationSnapshot`: 0 dosya. COIN-M BTCUSD_PERP 2023-06-25 → 2024-10-14 (yarısı kopya satır) — S3 listesi, `cm_liq_quality_report.json`
- bookTicker 2023-05-16 → 2024-03-30, 52,6 GB — S3 listesi
- bookDepth 2023-01-01 öncesi yok. Eksik günler 2023-02-08/09, 2024-04-18, 2026-10-08. 2023-01/02'de çok sayıda boş/yarım gün. Şüpheli günler 2025-10-10…15 ve 2026-09-03…07 — `bookdepth_quality_report.json`
- Metrics: 2021-06-22/23 (175 dilim), 2024-02-16 13:30–24:00 eksik. Top-trader oranları 2022'nin çoğunda NaN. Taker oranı 2022-01 → 05 NaN. OI=0 hatalı satırlar 471 — `metrics_quality_report.json`
- Funding REST: "Service unavailable from a restricted location" (bu makinede, 2026-10-21)
- Premium 66, index 7, mark 2 kayıp dakika (2022-07-12, 2023-11-10, 2024-08-12 kesintileri) — `futures_quality_report.json`

### Inferences
- Bu veri setiyle **test edilemeyecek** hipotezler:
  - saniye altı defter dinamiği (kuyruk, spoofing)
  - gerçek tasfiye büyüklüğü ve tasfiye ısı haritası
  - 2023 öncesi defter dengesizliği
  - 2026-04 öncesi saniye düzeyinde akış
- Test edilebilecek yeni hipotezler (OHLCV ile yapılamayanlar):
  - spot vs perp taker akış ayrışması
  - premium ve baz uçları
  - funding'e kalan süre etkisi
  - OI düşüşü ile kaskad
  - top-trader / global L/S konumlanması
  - dakika ölçeğinde defter dengesizliği (2023+)
  - büyük-aggTrade kümeleri (2026-04+)
- Önerilen sonraki adımlar:
  - Kasım başında Ekim aylık funding'i indirip tahminleri değiştirmek.
  - Gerekirse spot aggTrades (2,3 GB) için aynı akış betiğini çalıştırmak.
  - Canlı tasfiye ve bookTicker için ileriye dönük WebSocket kaydı başlatmak. Bu kayıt REST'in engelli olduğu bu makinede değil, başka bir konumda çalışmalı.

### Gaps
- Coinglass vb. ücretli kaynaklarda geçmiş USDT-M tasfiye verisi olabilir. Kapsam dışında bırakıldı, araştırılmadı.
