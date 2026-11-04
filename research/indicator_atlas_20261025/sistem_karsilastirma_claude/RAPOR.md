# TradingView göstergeleri × ForexSAI — kaçını kullanıyoruz, hangisi yön söylüyor?

Tarih: 2026-10-25 · Claude Code oturumu · Kapsam: yerel `main` çalışma kopyası (backend, `yeni deneme/` botu, `claude_decider/`).
Railway/kutu dağıtımı ve kutunun gizli `config.py`'si sorgulanmadı → sayılar **kodda bağlı yolu** anlatır.
Tam satır satır matris: [MATRIS.md](MATRIS.md) · makine okunur: [MATRIS.json](MATRIS.json) · üretici: [build_matrix.py](build_matrix.py).

## 1. TradingView'da ne var? (bağımsız tarama)

| Kaynak | Sayı | Not |
|---|---:|---|
| Resmî "Built-in Indicators" yardım sayfası | 209 | 83'ü kripto/on-chain, temel analiz (temettü, analist hedefi) veya rehber yazısı |
| → bunlardan **teknik gösterge** | **126** (+ Open Interest = 127) | matrisin "resmi" satırları bunları kapsar |
| Resmî grafik formasyonu sayfası | 20 | 16 formasyon + Elliott + Gaps + 2 genel sayfa |
| Hacim profili / TPO | 6 / 2 | |
| Yerleşik mum formasyonu göstergeleri | ~40 | "All Candlestick Patterns" ile tek pakette |
| Pine Script v6 `ta.*` gösterge fonksiyonu | 48 | `cross`, `highest`, `valuewhen` gibi yardımcılar hariç |
| Topluluk (Public Library) | 150.000+ script | tek tek sayılamaz → en bilinen 20 aile matrise alındı (SMC, WaveTrend, QQE, Supertrend türevleri, UT Bot, Lorentzian, Nadaraya-Watson, Squeeze…) |

Kaynaklar: [Built-in Indicators](https://www.tradingview.com/support/folders/43000587405-built-in-indicators/) ·
[Chart Patterns](https://www.tradingview.com/support/folders/43000587407-chart-patterns/) ·
[Volume Profiles](https://www.tradingview.com/support/folders/43000587408-volume-profiles/) ·
[TPO](https://www.tradingview.com/support/folders/43000592009-tpo/) ·
[Pine v6 reference](https://www.tradingview.com/pine-script-reference/v6/) ·
[Public Library](https://www.tradingview.com/scripts/) ·
[Editors' picks](https://www.tradingview.com/scripts/editors-picks/) ·
[Candlestick patterns blog](https://www.tradingview.com/blog/en/new-candlestick-patterns-20461).

## 2. Sistemimiz bunların kaçını kullanıyor?

**127 resmî teknik sayfanın 26'sı (%20) bir karar yolunda** (sinyal yönü, puan, veto, emir, ML girdisi veya SL/TP ölçeği).

| Seviye (resmî sayfa) | Sayfa |
|---|---:|
| Karar yolunda (K/M/R) | **26** |
| Dokunuyor ama karar değil (bağlam, gölge, kayıt, araç) | 8 |
| Yalnız benzeri var / yer tutucu | 16 |
| Hiç yok | **77** |

Bileşen bazında (132 matris satırı, resmî + formasyon + profil + topluluk):

| Bileşen | Karar (K/M/R) | Dokunuyor | Benzeri/yer tutucu | Yok |
|---|---:|---:|---:|---:|
| Backend (panel modelleri, kapılar, ML) | 32 | 9 | 17 | 74 |
| Bot (`yeni deneme/`, backend `bot_router` vetosu dahil) | 14 | 8 | 5 | 105 |
| Claude Decider | 4 | 15 | 2 | 111 |

Pine `ta.*` açısından: 48 fonksiyonun **24'ü bizde var** (MACD'si kusurlu dahil), 3'ünün benzeri var, 1'i yalnız araştırma aracında, **20'si hiç yok**.

### Karar yolundaki 26 resmî gösterge

| Rol | Göstergeler |
|---|---|
| **Yön/puan formülü** (Pulse, EMEL, meta, kural-ML) | EMA, RSI, MACD, Stochastic, Momentum, Bollinger Bands, OBV, Volume, ADX/DMI, Parabolic SAR (XAU) |
| **Yapı/seviye** | Linear Regression kanalı, Williams fractal, Pivot High/Low |
| **Kapı/veto** | EMA50 trend kapısı, Trading Sessions, VWAP (CHREV), bot_router momentum filtresi (Stoch + EMA20 + SAR), RSI diverjansı (rebound) |
| **Yalnız ML girdisi** | SMA, Williams %R, MFI, BB %b, BB Width, Correlation Coefficient, ROC, Historical Volatility |
| **Risk/geometri** | ATR (TP/SL merdiveni, sıkışma, erken kesme) |

Topluluk tarafında karar yolunda olanlar: **SMC** (BOS/CHoCH/OB/FVG), **harmonik + klasik formasyonlar**, **sahte kırılım dedektörü** (kendi modelimiz) ve **VIX rejimi**.

### Hiç olmayan popüler göstergeler

Supertrend, Ichimoku (yalnız boş sütun adı), Keltner, Hull/KAMA/ALMA/DEMA/TEMA/WMA/VWMA/McGinley, Stoch RSI, CCI (yalnız araştırma endpoint'inde), Awesome, TSI, TRIX, Fisher, Aroon (yalnız çekirdek ölçüsü XAU ML'de), Vortex, Chaikin/CMF/ADL/PVT, Zigzag, Pitchfork, Auto trendlines, TPO, gerçek CVD/footprint. Topluluktan WaveTrend, QQE, HalfTrend, UT Bot, SSL, Range Filter, Nadaraya-Watson, Schaff, Ehlers, Kalman ve Wyckoff da yok.

## 3. Yön tahmini açısından: hangisi işe yaradı?

Göstergeleri Kapı Kayıt Defteri'ndeki sızıntısız sınamalarla eşleştirdim (`docs/KAPI_KAYIT_DEFTERI.md`). 132 satırın **35'inin defterde bir sınaması var, 97'si hiç sınanmadı.**

**Ayakta kalanlar (A/B):** bunların hiçbiri klasik osilatör değil; hepsi **rejim, bağlam veya geometri**.

| Kanıt | Ne |
|---|---|
| A | VIX rejimi → NDX yönü (OLD-10: +24,9pp, OOS +17pp, plasebo p=0). Ama genel girişlerde işlem başına ≈0,01R (GF-05) |
| A− | 1h EMA50 trend hizası (B4: hizalı %63,3 vs karşı %43,4, 332 işlem) |
| A | Momentum-devam girişi; filtresi gerçek (+0,054R) ama **yalnız uzak (2×ATR) hedefte** paraya dönüyor (OLD-20) |
| A/B | Seans/gün kapıları (B2 NDX Cuma, B3 ASIA, B6 TQ) |
| A (yalnız NDX) | Sahte kırılım dedektörü (OLD-17, CK-04) |
| B | XAU günlük Golden Donchian (XS-01; bağımsız dönemde tuttu, n küçük → gölge) · CAPREV stres-günü (GF-21) |

**Sınanıp çöken (X):**
- MACD kesişimi (OLD-12)
- EMA10/25/50 kesişimi (HK-01)
- RSI diverjansı giriş olarak (HK-04)
- S/R reaksiyonu ve dokunuş sayısı (OLD-05, HK-03)
- Klasik formasyon SELL'leri (%22,6, n=115)
- Mum formasyonları (MK-01/02/05)
- Hacim ölçüleri (IO-03)
- VWAP dönüşü (OLD-15, BTC-SC-VS06/07)
- Açılış aralığı kırılımı (FG)
- Değer alanı / TPO %80 kuralı (HK-02)
- Analog kNN (OLD-13, ME-02/03)
- ATR sıkışma ileri dönemde (IO-22)
- USOIL Donchian kırılımı (P(EV>0) %0,3)
- ATR-TP genişletme (M8)

**Okuma:** Sistemimizin kullandığı klasik osilatörlerin (RSI, MACD, Stoch, BB) **hiçbirinin tek başına sızıntısız yön kenarı yok**. Bunlar Pulse/EMEL'in puanına giriyor, ama defterdeki her doğrudan sınamada ya taban düzeyinde kaldılar ya da düştüler. Yön bilgisi taşıyan şeyler bağlam: VIX rejimi, büyük zaman diliminde trend hizası, seans, NDX'te kırılım teyidi ve uzak hedefli momentum. Bu, defterin "geometri > filtre" ve "korku döner, coşku dönmez" meta-dersleriyle aynı yöne işaret ediyor.

**Sınanmamış 97 satır** (Supertrend, Keltner/Squeeze, WaveTrend, QQE, KAMA/Hull, Ichimoku vb.) için hüküm yok. Bunlar kenarsız oldukları için değil, hiç ölçülmedikleri için listede. Defterdeki örüntü, klasik fiyat-türevi osilatörlerin bu dört piyasada tek başına kenar vermediği yönünde. Bu yüzden yeni bir göstergeyi eklemeden önce, ön kayıtlı aynı protokolle (taban + plasebo + bağımsız dönem + gerçek icra) ölçmek gerekiyor.

## 4. Kodda bulunan hesap/sözleşme sorunları (kendi doğrulamam)

Codex'in raporundaki dört iddiayı kaynaktan doğruladım; birini düzelttim.

1. **NDX/DAX ML + Pulse/EMEL'in ortak hesaplayıcısı sadeleştirilmiş** (`backend/services/ml_prediction_service.py:603` `_compute_technical_indicators`):
   - MACD'nin `signal=0`, `histogram=MACD çizgisi`, `hist_diff=0` olarak dönüyor (satır ~661). Pulse/EMEL'deki `macd_hist > 0` puanı (`backend/routers/emel_pulse.py:1712`, `:2392`, `:2800`) bu yüzden fiilen **EMA12 > EMA26** demek. Yani MACD puanı EMA trend puanının kopyası ve aynı bilgiyi iki kez sayıyor.
   - `abs(macd_hist) < 0.01` eşiği fiyat ölçeğine bağlı. NDX'te (~20.000) bu eşik neredeyse hiç tutmaz.
   - Stochastic'te `%D = %K`, yani yumuşatma yok.
   - RSI ve ATR Wilder değil, son 14 değerin düz ortalaması.
   - Aynı göstergenin projede **üç farklı uygulaması** var: bu hesaplayıcı, `signal_feature_snapshot.py` (gerçek MACD/%D/SAR) ve botun `indicators.py`'si (Wilder). Hangisinin hangi kararı beslediği sinyal yoluna göre değişiyor.
   - ⚠ Formülü düzeltmek NDX modelinin eğitim sözleşmesini bozabilir. Önce modelin hangi formülle eğitildiğinin bulunması gerekiyor.
2. **USOIL ML gerçek model çalıştırmıyor.** `ML_MODEL_FAMILY_BY_SYMBOL` USOIL'i `model_xauusd_v2.joblib`'e yönlendiriyor. Bu dosya bir dict (`buy_model`, `sell_model`, `feature_columns`, …), `feature_names_in_` alanı yok. Bu yüzden `_build_feature_vector` `None` dönüyor ve her çağrı `_rule_based_prediction`'a düşüyor (`ml_prediction_service.py:1295`, `:2454`). Bu yedek formül 4 kural: RSI eşikleri + EMA20/50/200 dizilimi + MACD işareti + BB z-skoru. Bunu yerel modelle taze yükleme yaparak doğruladım. Railway'deki dosyanın aynı olduğunu doğrulamadım.
3. **NDX/DAX modeli 810 girdi bekliyor.** Kodun açık eşlemesi bunların ~103'ünü dolduruyor, kalanlar adına göre varsayılan değer alıyor (Codex ölçümü; `feature_names_in_` = 810'u doğruladım). "Ichimoku" ve "CMF" sütunları bu varsayılan gruba giriyor.
4. **COT eşlemesi:** `cot_report_service._normalize_symbol` GDAXI ve USOIL'i varsayılan olarak `XAUUSD`'ye düşürüyor (`backend/services/cot_report_service.py:352-363`). DAX ve petrol panellerinin COT bağlamı **altın kontratından** geliyor.
5. **Codex'e düzeltme:** Codex Stoch/MACD/SAR'ı botta "yalnız kayıt" saymıştı. Oysa backend `routers/bot_router.py:78` `MOMENTUM_FILTER`, botun her `/api/bot/trade-signal` çağrısında NDX BUY, DAX BUY ve USOIL BUY için şu üç koşulu zorunlu tutuyor: **M15/M30 Stoch %K > 70, EMA20 mesafesi > 0,8 ATR, H1 SAR fiyatın altında**. Koşullar tutmazsa `should_trade=false` dönüyor ve bot emir açmıyor (`yeni deneme/forexsai_demo_bot.py:2001`). Bu hesap `signal_feature_snapshot.py`'den geliyor (gerçek %D ve SAR). Yani Stochastic ve SAR botun canlı kararında **aktif kapı**.
6. **Diğer isim/kapsam notları:**
   - EMEL/Pulse'taki "pivot" son 20 barın H/L/C'sinden hesaplanıyor; TradingView'daki günlük Pivot Points Standard değil.
   - Botun "SQZ"si ATR14/ATR100 oranı; TTM'in Bollinger-Keltner sıkışması değil.
   - Petrol servisindeki "CVD", mum rengiyle ±0,6×hacim alan sentetik bir değer; gerçek delta değil.
   - Botta "formasyon" kelimesi geçen 110 satırın hepsi config "flag"i. Bot grafik formasyonu kullanmıyor.

## 5. Önerilen sıradaki adımlar (backlog'a yazıldı)

1. **USOIL ML yönlendirmesini düzelt veya dürüstçe etiketle** (wiring, high). Ya USOIL için gerçek bir model bağlanmalı, ya da sinyal `rule_based` diye etiketlenip karnesi ayrı tutulmalı.
2. **Pulse/EMEL MACD puanının EMA'yı ikinci kez sayması** (decision). Önce NDX modelinin eğitim formülü bulunmalı, sonra karar verilmeli: MACD puanı kaldırılabilir, gerçek MACD'ye geçilebilir veya gölgede kıyaslanabilir.
3. **COT eşlemesi DAX→Eurex/DAX vadelisi, USOIL→WTI** (wiring).
4. **Sınanmamış popüler TradingView göstergeleri için ön-kayıtlı yön sınaması** (experiment, medium). Aday seti: Supertrend, Keltner/TTM Squeeze, WaveTrend, QQE, KAMA, Ichimoku bulut kırılımı, Donchian (endeksler). Protokol: 4 sembol, taban + plasebo + bağımsız dönem + sonraki M1 açılış icrası (2. KURAL). Önceki X'lerin tekrarı olmaması için tanımlar defterle karşılaştırılarak donduruluyor.

## 6. Yöntem ve sınırlar

- **Kod taraması:** [`scan_indicators.py`](scan_indicators.py) (`python3 scan_indicators.py <repo> out.json`) 122 imza regex'iyle backend `services/routers`, `yeni deneme/` ve `claude_decider/` üretim dosyalarını taradı (testler, adli/araştırma scriptleri hariç). Türkçe kelimelerden gelen sahte eşleşmeler ("alma"→ALMA, "kama"→KAMA, "mesafe"→MESA, "flag"→formasyon) tek tek elendi. Her karar sınıflandırması dosya okumasıyla doğrulandı.
- **Erişilebilirlik:** `main.py`'den import grafiği çıkarıldı (258 modülün 131'i statik olarak erişilebilir). Yalnız araç endpoint'lerinde kullanılanlar (strategy_optimizer CHOP, permutation CCI/Force Index) "A" olarak işaretlendi.
- **Sınırlar:**
  - Canlı env bayrakları (ör. kutuda kapatılmış bir kapı) ve Railway'deki model hash'leri görülmedi.
  - "Yok", yalnız incelenen üretim yollarında yok demek.
  - Topluluk kütüphanesi örneklem; eksiksiz değil.
  - Bu çalışmada **yeni backtest yapılmadı**; yön sütunu yalnız defterdeki mevcut sınamaları aktarıyor.
