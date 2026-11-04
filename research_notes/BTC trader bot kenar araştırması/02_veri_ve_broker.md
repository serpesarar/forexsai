# BTC 5 yıllık veri seti + broker (Pepperstone MT5) icra parametreleri

Kapsam: 2026-10-21'de kuruldu. Ham indirmeler `research/btc_5y_20261021/data/raw/`, temiz çıktılar
`research/btc_5y_20261021/data/`, betikler `research/btc_5y_20261021/scripts/`. Kutuya hiçbir dosya
yazılmadı, emir gönderilmedi, süreç yeniden başlatılmadı (ayrıntı: "Broker spesifikasyonları" → Çıkarımlar).
Kod commit edilmedi.

Betik sırası (yeniden üretim):
1. `scripts/01_download_binance.py <raw>` — aylık/günlük zip + `.CHECKSUM` (SHA256) doğrulaması
2. `scripts/02_build_binance.py <raw> <data>` — 1m temizleme + 5m/15m/1h/4h/1d resample + kalite raporu
3. `scripts/box_01_specs.py`, `box_02_rates.py`, `box_03_ticks.py` — kutuda SALT OKUMA betikleri;
   `scripts/03_box_send.py` ile `remote.py sh` üzerinden zlib+base64 `python -c` olarak gönderilir (kutuda dosya yazılmaz)
4. `scripts/04_macro_yf.py <data>` — yfinance günlük makro
5. `scripts/05_broker_compare.py <data>` — kutu dökümlerini çöz, ofset ölç, Binance ile kıyasla
6. `scripts/06_basis_check.py <data>` — baz farkının kaynağı (Coinbase BTC-USD + USDT-USD)

Tüm Python `/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python -I` ile koşuldu (pandas 2.3.3, numpy 2.4.6, pyarrow 24.0.0, yfinance 1.2.0, Py 3.14.6).

---

## Veri kaynağı ve indirme bütünlüğü (Binance public data)

### Takeaway
Kaynak Binance spot BTCUSDT 1m klines (data.binance.vision): 64 aylık zip (2021-06 → 2026-09) + 20 günlük zip
(2026-10-01 → 2026-10-20), 84/84 dosya SHA256 CHECKSUM ile doğrulandı. Zaman birimi dosya başına tespit edildi:
43 dosya milisaniye, 41 dosya (2025-01'den itibaren) mikrosaniye; karışık birimli dosya yok.

### Cited Findings
- Binance public data README: kline dosyaları `/api/v3/klines` uç noktasından türetilir; sütunlar Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base, Taker buy quote, Ignore; "Each zip file has a `.CHECKSUM` file"; "The timestamp for SPOT Data from January 1st 2025 onwards will be in microseconds." — [binance-public-data README](https://github.com/binance/binance-public-data)
- Yerel doğrulama: `download_log.tsv` 84 satırın 84'ü `ok` (SHA256 eşleşti); 2024-12 dosyasının ilk open_time'ı `1733011200000` (ms), 2025-01'in `1735689600000000` (µs); CSV'lerde başlık satırı yok — [download_log.tsv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/raw/download_log.tsv), [btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_quality_report.json) (`unit_by_file`)
- Ekim 2026 aylık dosyası henüz yayımlanmadı (ay bitmedi); bu yüzden 2026-10 günlük dosyalardan alındı. Son bar `2026-10-20 23:59 UTC` — [btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_quality_report.json)

### Inferences
- `close_time − open_time = 59.999 s` kuralı 3 satırda bozuk (birim dönüşümünden kaynaklı yuvarlama veya kesinti kenarları olabilir); `close_time` parquet'e konmadı, zaman ekseni yalnız `ts` (=open_time, UTC).
- Fallback kaynak (REST API vb.) GEREKMEDİ.

### Gaps
- 2026-10-21 (bugün) verisi yok; Binance günlük dosyası ertesi gün yayımlanır. Gerekirse `01_download_binance.py`'deki `DAILY_DAYS` genişletilip yeniden koşulabilir.

---

## Temizlik, boşluklar, kopyalar, sıfır hacim, aykırı değerler

### Takeaway
2.833.450 satır, 2021-06-01 00:00 → 2026-10-20 23:59 UTC; beklenen 2.833.920 dakikadan 470 dakika eksik, hepsi
3 kesintide (2021-08-13 270 dk, 2021-09-29 120 dk, 2023-03-24 80 dk). Kopya zaman damgası 0, OHLC tutarsızlığı 0.
72 sıfır-hacimli bar var, hepsi 2023-03-24 11:28–12:39 UTC (Binance spot durdurması). Aykırı fitiller veri
hatası değil, bilinen piyasa olayları.

### Cited Findings
- Boşluklar (1m, ≥5 dk): `2021-08-13 01:59 → 06:30` (270 dk), `2021-09-29 06:59 → 09:00` (120 dk), `2023-03-24 12:39 → 14:00` (80 dk); 5 dk'dan kısa boşluk yok — [btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_quality_report.json)
- 2023-03-24: Binance tüm spot işlemleri geçici olarak durdurdu; CZ eşleştirme motorundaki trailing-stop hatasını sebep gösterdi — [TechCrunch](https://techcrunch.com/2023/03/24/crypto-giant-binance-temporarily-suspends-spot-trading); işlemlerin 14:00 UTC'de yeniden başlayacağı duyuruldu — [Forklog](https://forklog.com/en/binance-completes-maintenance-after-outage/). Bizim veride 11:28–12:39 arası 72 düz (O=H=L=C=28080, hacim 0) bar + 12:40–13:59 tamamen eksik, 14:00'te devam → duyuruyla tutarlı.
- 2021-08-13 ve 2021-09-29 kesintileri için resmi Binance duyurusu bulunamadı (arama sonuçsuz); bir TradingView kullanıcı gönderisi tarihsiz bir "UTC 02:00 planlı bakım, 6–8 saat işlem askıda" anlatıyor — [TradingView (tarihsiz, birincil değil)](https://cn.tradingview.com/chart/BTCUSDT/J7bIPAuP-Not-a-Shitcoins-dump-Just-a-scheduled-Binance-upgrade). 2021-08-13'ün 02:00'de başlaması planlı bakım desenine uyuyor ama doğrulanmadı.
- Aykırı değer taraması: |1m log getiri| > %2 olan barlar ve 1m aralığı > %3 olan 55 bar; >%5 rolling-medyan sapması olan fitiller 2021-07-26 (short squeeze), 2021-09-07 (El Salvador günü çöküşü), 2021-12-04 (hafta sonu çöküşü), 2022-11-08 (FTX), 2023-10-16 (sahte ETF haberi), 2023-10-23, 2024-03-05 tarihlerinde kümeleniyor; hepsi çok-barlı, tutarlı hareketler (tek-tick spike değil) — [btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_quality_report.json) (`abs_ret_1m_gt_2pct`, `range_1m_gt_3pct`, `wick_gt5pct_from_rolling_median`)
- 1m log getiri std = %0.0752; günlük getiriden yıllık vol ≈ %53.1 (2021-06 → 2026-10); yıllık aralıklar: 2021 (Haz–Ara) 28.805–69.000, 2022 15.476–48.190, 2023 16.499–44.700, 2024 38.555–108.353, 2025 74.508–126.200, 2026 (Eki 20'ye kadar) 57.800–97.924 USDT — yerel hesap, [btc_1d.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_1d.parquet)

### Inferences
- Temizlikte veri SİLİNMEDİ veya doldurulmadı (eksik dakika = satır yok). Backtest'ler 2023-03-24 11:28–14:00 UTC aralığını dışlamalı (sıfır hacimli düz barlar sahte "fiyat donması" üretir; bu aralıkta giriş/çıkış simülasyonu gerçekçi değildir).
- Aykırı fitiller gerçek piyasa olayıdır; bir CFD broker'ı aynı anda farklı (genelde daha geniş spread'li, bazen daha sığ) fiyat göstermiş olabilir — SL tetiklemesi açısından muhafazakâr olan Binance fitillerini kullanmaktır.

### Gaps
- 2021 kesintilerinin resmi nedeni doğrulanmadı.

---

## Veri sözlüğü

### Takeaway
Tüm BTC barları UTC, `ts` = bar AÇILIŞ zamanı (left-label, left-closed `[ts, ts+TF)`), 1d barı 00:00 UTC'de başlar.
Fiyatlar USDT cinsinden (BTCUSDT); USD ile fark ~%0.0–0.13 (aşağıda "Broker vs Binance").

### Cited Findings (tümü yerel dosyalar; satır sayıları `btc_quality_report.json` / `macro_quality_report.json` / `broker_compare_report.json`)

| Dosya | Satır | Aralık (UTC) | Not |
|---|---|---|---|
| [data/btc_1m.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_1m.parquet) (166 MB) | 2.833.450 | 2021-06-01 00:00 → 2026-10-20 23:59 | 470 dk eksik (3 kesinti) |
| [data/btc_5m.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_5m.parquet) | 566.690 | → 2026-10-20 23:55 | eksik kova 0 (kesinti kovaları satırsız) |
| [data/btc_15m.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_15m.parquet) | 188.897 | → 23:45 | 1 eksik-dakikalı kova |
| [data/btc_1h.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_1h.parquet) | 47.225 | → 23:00 | 2 eksik-dakikalı kova |
| [data/btc_4h.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_4h.parquet) | 11.808 | → 20:00 | 5 eksik-dakikalı kova |
| [data/btc_1d.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_1d.parquet) | 1.968 | 2021-06-01 → 2026-10-20 | 3 eksik gün-içi (2021-08-13 n=1170, 2021-09-29 n=1320, 2023-03-24 n=1360) |
| [data/macro_daily.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/macro_daily.parquet) | 1.378 | 2021-05-03 → 2026-10-20 (NY işlem günleri) | 4 satırda kısmi NaN |
| [data/broker_btcusd_m1.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_btcusd_m1.parquet) | 22.812 | 2026-10-05 21:49 → 2026-10-21 21:51 | Pepperstone BTCUSD M1, BID |

Sütunlar:
- **btc_1m**: `ts` (datetime64[ns, UTC], bar açılışı), `open/high/low/close` (float64, USDT), `volume` (BTC), `quote_volume` (USDT), `trades` (int64, işlem adedi), `taker_buy_base` (BTC), `taker_buy_quote` (USDT).
- **btc_5m/15m/1h/4h/1d**: `ts`, `open` (ilk), `high` (max), `low` (min), `close` (son), `volume`, `quote_volume`, `trades`, `taker_buy_base` (toplam), `n_1m` (kovadaki gerçek 1m bar sayısı; tam kova 5/15/60/240/1440). Yalnız `n_1m>0` kovalar yazıldı.
- **macro_daily**: `date` (NY yerel işlem günü, naive), `vix_close`, `vix_open` (^VIX), `dxy_close` (DX-Y.NYB), `us10y_close` (^TNX, yüzde getiri, ör. 5.117), `qqq_close`, `qqq_adj_close`, `qqq_open`, `qqq_volume` (QQQ), `ndx_close`, `ndx_open` (^NDX), `avail_utc` (= date + 22:30 UTC; değerin kesin bilinir olduğu en erken an). Son satır 2026-10-20: VIX 17.31, DXY 101.73, US10Y 5.117, QQQ 717.63, NDX 29490.28.
- **broker_btcusd_m1**: `ts_utc` (= `ts_server − 180 dk`), `ts_server` (MT5 sunucu saati, UTC gibi etiketli), `open/high/low/close` (BID, USD), `spread_pts` (MT5 bar spread'i, nokta=0.01$), `spread_usd`, `tick_volume`.
- Yan raporlar: `btc_quality_report.json`, `macro_quality_report.json`, `broker_compare_report.json`, `basis_check.json`; ham kutu çıktıları `data/broker/*.txt`.

### Inferences
- **Makro yayın zamanı (sızıntı tuzağı):** VIX/QQQ/NDX kapanışı 16:00 ET (20:00 UTC yaz / 21:00 UTC kış), DXY (ICE) 17:00 ET'ye kadar işlem görür. Bir BTC barı `t` için yalnız `avail_utc <= t` olan makro satırı kullanılmalı (`pd.merge_asof(btc, macro, left_on="ts", right_on="avail_utc")`); BTC 1d barı (00:00 UTC açılış) için bu pratikte **bir önceki ABD işlem gününün** değeridir. Hafta sonu/ABD tatilinde BTC işlem görür, makro güncellenmez → son bilinen değer ileri taşınır.
- Makro NaN satırlar: 2025-01-09 (Carter yas günü; VIX/TNX/QQQ/NDX yok, DXY var), 2025-05-26 (Memorial Day), 2026-05-25 ve 2026-09-07 (ABD tatilleri; DXY/TNX/QQQ/NDX yok ama Yahoo VIX değeri var — muhtemelen bayat/kısa seans değeri, güvenme). `ffill` + `avail_utc` ile güvenle kullanılır.
- `us10y_close` Yahoo'da zaten yüzde birimde geldi (medyan 4.087), betikteki /10 dönüşümü tetiklenmedi.

### Gaps
- Makro veride yfinance'ın ayarlama/revizyon politikası doğrulanmadı (QQQ için hem ham hem `adj_close` saklandı).

---

## Broker spesifikasyonları (Pepperstone MT5, BTCUSD)

### Takeaway
Kutudaki hesap **Pepperstone-Demo** (hedging, USD, hesap kaldıracı 1:200). BTC sembolü **`BTCUSD`** (ayrıca BTCAUD/BTCEUR/BTCGBP var);
CFD hesaplama, kontrat 1 BTC/lot, min lot 0.01, adım 0.01, maks 22 lot, 2 basamak, stops_level 0, piyasa icrası (IOC dolum).
1 lot marjin ≈ fiyatın %5'i (1:20). Swap yıllık faiz modunda: long −%14/yıl, short +%2/yıl.

### Cited Findings
- `symbol_info("BTCUSD")` (kutu, 2026-10-21): path `Markets\Cryptocurrencies\Major\BTCUSD`, `digits=2`, `point=0.01`, `spread_float=True`, `trade_contract_size=1.0`, `trade_tick_size=0.01`, `trade_tick_value=0.01`, `volume_min=0.01`, `volume_step=0.01`, `volume_max=22.0`, `swap_mode=5`, `swap_long=-14.0`, `swap_short=2.0`, `swap_rollover3days=7`, `trade_stops_level=0`, `trade_freeze_level=0`, `trade_mode=4`, `trade_calc_mode=2`, `trade_exemode=2`, `filling_mode=2`, `order_mode=127`, `margin_initial=0`; Market Watch'ta görünür DEĞİL (`visible=False`) — [box_01_specs_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_01_specs_out.txt)
- Enum sayısal değerleri kutudaki MetaTrader5 5.0.5735 paketinden okundu: `SYMBOL_SWAP_MODE_INTEREST_CURRENT=5`, `SYMBOL_CALC_MODE_CFD=2`, `SYMBOL_TRADE_EXECUTION_MARKET=2`, `SYMBOL_TRADE_MODE_FULL=4`, `ACCOUNT_MARGIN_MODE_RETAIL_HEDGING=2`, `DAY_OF_WEEK` 0=Pazar…6=Cumartesi (yani 7 aralık dışı) — kutu çıktısı (remote.py sh, bu oturum); `filling_mode=2` = IOC — [MQL5 docs](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- MQL5: INTEREST_CURRENT modunda "Swaps are charged as the specified annual interest from the instrument price", "standard bank year is 360 days" — [MQL5 docs](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- `order_calc_margin(BUY, BTCUSD, lot, ask=84772.26)`: 0.01 lot → 42.39 $, 1.0 lot → 4238.61 $ (=%5.0); `order_calc_profit(1 lot, +100$)` = 100.00 $ → 1$ fiyat hareketi = 1$/lot — [box_01_specs_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_01_specs_out.txt)
- Hesap: `company=Pepperstone Group Limited`, `server=Pepperstone-Demo`, `currency=USD`, `leverage=200`, `trade_mode=0` (demo), `margin_mode=2`; terminal build 6230, `maxbars=100000` — aynı dosya
- Pepperstone: kripto CFD'ler hafta sonu aynı sembolle işlem görür; SL/TP/bekleyen emirler hafta sonu tetiklenebilir; BTCUSD her gün 00:01–23:59 sunucu saati, Cuma 23:55'te kapanır — [Pepperstone trading hours](https://pepperstone.com/en-au/ways-to-trade/trading-hours)
- Pepperstone pazarlama/spec sayfaları: BTCUSD spread "USD$10'dan başlayan", bir (staging) spec tablosunda min 14.76 / ort. 29.86 — [Pepperstone crypto (arama özeti)](https://pepperstone.com/en-au/markets-and-symbols/cryptocurrencies); [staging spec](https://next.stg.pretrade.pepperstone.com/en-au/markets-and-symbols/cryptocurrencies) — bizim demo ölçümümüzle (ort. ~16$) çelişiyor, aşağıya bak.

### Inferences
- Swap maliyeti (INTEREST_CURRENT, 360 gün): **long 1 lot ≈ fiyat×0.14/360 ≈ 84.765×0.000389 ≈ 33 $/gece** (≈ %0.039/gece), **short ≈ +4.7 $/gece** (alacak). Long'u gece taşımak bir gecede ~2 spread'e eşdeğer maliyet. `swap_rollover3days=7` geçerli bir gün değil → üçlü swap günü yok, muhtemelen hafta sonu dahil her gece tahakkuk (kripto 7/24) — **doğrulanmadı**.
- Rollover anı sunucu gece yarısı = ABD yaz saatinde 21:00 UTC, kışın 22:00 UTC (çıkarım; swap anı ölçülmedi).
- 1:20 kripto marjin oranı → 0.01 lot ≈ 42 $ marjin; bot mevcut endeks lot büyüklüklerini (5.0 lot) BTC'ye taşırsa 5 lot ≈ 21.2 k$ marjin ve 1$ hareket = 5$ — risk boyutlandırması ayrıca yapılmalı.
- **Kutu dokunuşu:** BTCUSD Market Watch'ta gizli olduğu için tick/bar alınamıyordu (`copy_rates` → `(-2, Invalid params)`). Her okuma betiği sembolü GEÇİCİ `symbol_select(True)` ile ekleyip sonunda `symbol_select(False)` ile geri gizledi (her çıktıda `RESTORE_HIDE True`). Botun `symbols_get()` kullanımı görünürlükten bağımsız olduğu için bot davranışını etkilemez. Emir, dosya yazma, süreç yeniden başlatma yok. `remote.py ask` kullanılmadı, yalnız `sh`.

### Gaps
- Komisyon: demo hesapta BTC işlemi olmadığından gerçek komisyon/işlem ücreti görülemedi (CFD'de spread-only varsayımı doğrulanmadı).
- Gerçek swap tahakkuk günü/anı ve 360 vs 365 bölücü doğrulanmadı (BTC pozisyonu yok).
- Canlı (real) hesap spread'i demo ile aynı mı bilinmiyor; Pepperstone'un kendi sayfaları farklı rakamlar veriyor.
- MT5'te trading-session tablosu Python API'de yok (SymbolInfoSessionTrade yalnız MQL5); oturumlar bar boşluklarından çıkarıldı.

---

## Broker icra parametreleri (backtest'ler için: spread ×1.5 stresi + sonraki-M1-açılışı)

### Takeaway
BTCUSD spread'i neredeyse **sabit 15.00 $** (≈ **%0.018** fiyat; 84–85k'da). Tick-düzeyinde 14 günde medyan 15 $, p90 15 $ (hafta sonu
ve 13–16 UTC'de p90 17.25 $), p99 ~40 $; zaman-ağırlıklı ortalama 15.99 $. Volatil dakikalarda (en büyük %1 hareket) ortalama 23.7 $, p90 41.8 $.
Hafta sonu dahil 7/24 işlem; günlük 2 dk kesinti (sunucu 23:59–00:01) + Cuma 23:55–00:01; ara sıra hafta sonu bakım boşlukları.
Sunucu saati **UTC+3** (ölçüldü, ABD yaz saati); 2026-11-01'den itibaren UTC+2 olacak.

### Cited Findings
- **Tick spread (bid/ask), son 14 gün** (2026-10-07 21:52 → 10-21 21:52 UTC, 4.626.671 tick): medyan 15.0 $, p90 15.0 $, p99 40.03 $, zaman-ağırlıklı ort. 15.99 $, tw-p99 39.93 $, maks 370 $; medyan %0.0182, p90 %0.01854. Hafta içi: tw-ort 15.85 $, p99 39.9 $. Hafta sonu: tw-ort 16.33 $, tick-p90 17.25 $, p99 47.5 $, p90 %0.0208. En sık değerler: 15.00 $ (%92.5 tick), 17.25 $, 31.25 $, 32.37/32.38 $. — [box_03_ticks_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_03_ticks_out.txt)
- **Saate göre (UTC) tick spread:** 00–12 ve 17–23 UTC: medyan 15, p90 15, tw-ort 15.5–16.2 $; **13–16 UTC (ABD açılışı)**: p90 17.25 $, tw-ort 16.4–17.0 $, p99 40–64 $ (15 UTC p99 63.8 $ en kötü saat). — aynı dosya
- **Büyük hareket dakikaları** (dakikalık |mid getirisi| en üst %1): tw-ort 23.68 $, p90 41.8 $, p99 71.2 $, p90 %0.051. — aynı dosya
- **M1 bar spread'i, son 60 gün** (85.987 bar, 2026-08-23 → 10-22 sunucu): medyan 15.0 $, p90 15.0 $, maks 66.7 $, medyan %0.01845, p90 %0.01943, ort. 15.08 $; hafta içi/sonu ve 24 saatin hepsinde medyan=p90=15 $ — [box_02_stats_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_02_stats_out.txt). Bar `spread` alanının MetaQuotes'ça tanımı yok; topluluk testlerine göre barın MİNİMUM spread'i — [MQL5 forum](https://www.mql5.com/en/forum/17858/731560) → bu yüzden stres için tick ölçümü esas alınmalı.
- **Sunucu saati ofseti:** `symbol_info_tick().time − time.time()` = +3.00 saat; bağımsız olarak broker 1m getirilerinin Binance ile korelasyonu ofset +180 dk'da 0.888, ±1 dk'da ≤0.06, diğer tam saatlerde |r|<0.02 — [broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json). Pepperstone: sunucu ABD yaz saatinde GMT+3, ABD standart saatinde GMT+2 — [Pepperstone trading hours](https://pepperstone.com/en-au/ways-to-trade/trading-hours)
- **Seanslar / boşluklar (60 gün M1):** gün başına 1438 bar (her gün 23:59 ve 00:00 sunucu dakikası eksik = 20:59–21:00 UTC yaz), Cuma 1434 (Cuma 23:55–00:00 sunucu); 92 boşluk, 413 eksik dakika; >5 dk boşluklar: her Cuma 23:54→00:01 (7 dk), Pazar ~11:00 sunucu (08:00 UTC) 6–8 dk (08-30, 09-13, 10-04), Cumartesi 15:xx sunucu 6–10 dk (09-19, 09-26), **2026-10-17 Cumartesi 01:08 (44 dk) ve 09:09 (129 dk) sunucu** (=Cuma 22:08 UTC ve Cmt 06:09–08:18 UTC). Hafta sonu bar sayısı hafta içi ile aynı (Cmt/Paz ~1430–1438). — [box_02_stats_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_02_stats_out.txt), [broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json)
- **Sonraki-M1-açılışı:** broker M1 `open − önceki close` (ardışık dakikalar): |fark| medyan 0.49 $, p90 4.12 $, p99 31.18 $ — [broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json)
- **Tick hacmi:** M1 tick_volume medyan 246, p10 146, sıfır bar 0; saatlik broker tick hacmi ile Binance BTC hacmi korelasyonu 0.587 — aynı raporlar

### Inferences
- **Backtest maliyet modeli (önerilen):** Binance fiyatı ≈ mid kabul edilir; long giriş = ask = mid + S/2, çıkış = bid = mid − S/2 → gidiş-dönüş maliyeti = 1×S.
  - Taban S = **%0.0185 × fiyat** (≈15 $ @ 81–85k). Spread mutlak $ olarak sabit görünüyor; 5 yıl geriye (fiyat 16k–126k) taşırken iki varyant koş: (a) yüzde sabit %0.0185, (b) mutlak sabit 15 $ (16k'da %0.094 — 2022 dibi için çok daha pahalı). Hangisinin geçmişte geçerli olduğu bilinmiyor.
  - **Stres ×1.5 (Kart ölçüt 4):** S = **%0.028** (≈22.5 $). Ek ağır stres: volatil dakika p90'ı **~42 $ (%0.05)** — SL tetiklemeleri ve haber anları için.
  - 13–16 UTC girişlerinde tw-ort ~17 $ (×1.13); diğer saatlerde ~15.6 $ — saat-bazlı maliyet istenirse.
- **Kart ölçüt 5 (icra):** Giriş = sinyal barı kapanışı DEĞİL, Binance'te **sonraki 1m barın `open`'ı ± S/2**. Broker'da `open − önceki close` medyanı 0.49 $ olduğundan Binance sonraki-open'ı iyi bir vekil; p99 31 $ kuyruğu = spread genişlemesine denk.
- **Swap:** Gece taşıyan long'lara ~%0.039/gece (−%14/360), short'lara +%0.0056/gece ekle; rollover 21:00 UTC (yaz) / 22:00 UTC (kış) varsayımı.
- **Zaman ekseni:** Broker barlarını UTC'ye çevirirken sabit +3 KULLANMA — 2026-11-01 (ABD DST sonu) itibarıyla UTC+2; mart ortasında yeniden UTC+3. Binance verisi zaten UTC.
- **Kesintiler:** Broker günlük 20:59–21:01 UTC (yaz) 2 dk kapalı; Cuma 20:55–21:01 UTC; hafta sonu ara sıra 6–129 dk bakım boşluğu. Bu anlarda Binance'te tetiklenen SL/TP broker'da açılışta (gap) dolabilir — backtest'te bu dakikaları "dolum yok, sonraki açık dakikada dol" olarak modelle.

### Gaps
- Tick spread yalnız son 14 gün, M1 bar spread'i son 60 gün (terminal `maxbars=100000` sınırı) — 2021–2025 broker spread'i bilinmiyor.
- Kayma (slippage) ve gerçek dolum fiyatı ölçülemedi (BTC'de hiç işlem yok); demo hesap.
- 2026-10-17 hafta sonu boşluklarının nedeni (broker bakımı mı, besleme kesintisi mi) doğrulanmadı.

---

## Broker BTCUSD vs Binance BTCUSDT (örtüşen pencere 2026-10-05 → 10-21)

### Takeaway
Broker fiyatı Binance ile çok yüksek uyumlu (1m getiri korelasyonu 0.889, 5m 0.973, 15m 0.990, 1h 0.997). Broker mid'i
Binance'in ~77–105 $ (≈%0.1) ALTINDA, fakat fark tamamen USDT/USD kurundan geliyor: Coinbase BTC-USD'ye göre broker
yalnız −1…+8 $ farklı. Yani broker USD fiyatını izliyor; Binance USDT fiyatı USDT iskontosu kadar yukarıda.

### Cited Findings
- Örtüşen 21.503 dakika: baz (broker mid − Binance close) medyan −81.79 $, ort. −76.54 $, p05 −117.9 $, p95 −12.0 $, medyan %−0.099; günlük medyan 2026-10-05 −3.96 $ → 10-12 −91.3 $ → 10-17 −104.6 $ → 10-20 −92.3 $ — [broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json)
- Coinbase 1m (12:00–16:59 UTC, 300 bar/gün) ile: broker − Coinbase medyanı 10-06 −1.29 $, 10-12 +5.56 $, 10-18 +7.56 $, 10-20 +7.26 $; Binance − Coinbase 10.5 → 92.6 → 108.1 → 101.8 $; Coinbase USDT-USD medyanı 0.99983 → 0.99887 → 0.99872 → 0.99876; Binance×USDTUSD − Coinbase yalnız −3.95…+3.16 $ — [basis_check.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/basis_check.json); ham veri Coinbase Exchange public candles API (`api.exchange.coinbase.com/products/{BTC-USD,USDT-USD}/candles`), [data/raw/coinbase/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/raw/coinbase/)
- Getiri korelasyonu 1m 0.8888, 5m 0.9733, 15m 0.9900, 60m 0.9974; broker/Binance 1m getiri std oranı 1.12 — [broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json)
- Broker hafta sonu işlem görüyor: penceredeki 5.616 hafta sonu barı; UTC gün başına 1.433–1.438 bar (hafta içi ile aynı) — aynı rapor

### Inferences
- Getiri/R tabanlı backtest'lerde Binance verisi broker'ın iyi vekilidir (≥5m'de korelasyon ≥0.97). 1m'de broker %12 daha "gürültülü" (BID kotasyonu mikro-yapısı) → çok dar (birkaç $) SL/TP'li 1m stratejileri Binance'te iyimser görünebilir; böyle stratejiler broker M1 ile ayrıca doğrulanmalı.
- Seviye bazlı kurallar (yuvarlak sayı, S/R) için USDT/USD farkı ~%0.1'e kadar çıkabilir; 5 yıllık seride USDT iskontosu/primi zamanla değişti (ör. 2022 stres dönemleri) — mutlak seviye karşılaştırmasında USD kaynağı (Coinbase) düşünülmeli.
- Broker BTCUSD'nin kaynağı USD spot fiyatı gibi davranıyor (Coinbase ile ±8 $).

### Gaps
- Örtüşen broker M1 penceresi yalnız ~16 gün (çıktı limiti nedeniyle 2'şer günlük parçalar halinde çekildi; 60 günlük M1 kutuda mevcut, yalnız özet istatistiği alındı). Parça birleşim yerlerinde birkaç dakikalık yapay boşluk var (ör. 2026-10-20 21:46–21:52 UTC).
- 5 yıllık USDT/USD serisi indirilmedi (gerekirse Coinbase USDT-USD günlük ile eklenebilir).
