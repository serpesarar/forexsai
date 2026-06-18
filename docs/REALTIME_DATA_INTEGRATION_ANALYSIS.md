# ForexSAI — Anlık Veri Entegrasyonu Kapsamlı Analiz Raporu

> **Tarih**: 2026-04-17  
> **Kapsam**: Tüm paneller, tüm modeller, veri akışı, sinyal karar mantıkları  
> **Amaç**: MT5 Redis WebSocket köprüsü ile gelen anlık verinin sisteme entegrasyonunu değerlendirmek

---

## 1. MEVCUT VERİ AKIŞ MİMARİSİ

### 1.1 Veri Kaynakları ve Akış

```
MT5 Terminal ──→ Redis (pub/sub) ──→ mt5_redis_client.py ──→ DataHub (bellek)
                                                                ↓
MT5 bridge + yfinance ─────────────────────────────────────────────────→ DataHub (bellek)
                                                                ↓
                                                           ┌────┴────┐
                                                      Supabase    WS Manager
                                                    (kalıcı cache)   ↓
                                                              Frontend WS
```

### 1.2 DataHub — Merkezi Veri Deposu (`data_hub.py`)

| Veri Tipi | MT5/yfinance Modu Güncelleme | MT5 Redis Modu | Mevcut Durum |
|-----------|----------------------|----------------|--------------|
| **Fiyat (tick)** | 5 saniye (poll) | Anlık (pub/sub) | ✅ MT5 aktif ise anlık |
| **5m Mum** | 5 dakika (poll) | Anlık (bar event) | ✅ MT5 aktif ise anlık |
| **1h Mum** | 5 dakika (poll) | Anlık (bar event) | ✅ MT5 aktif ise anlık |
| **30m Mum** | 30 dakika (poll, sadece XAUUSD) | Anlık | ✅ |
| **EOD Mum** | 30 dakika (poll) | Anlık (bar event) | ✅ |
| **Türetilmiş (15m, 20m, 4h)** | 5m/1h'den resample | 5m/30m/1h'den resample | ✅ Otomatik |
| **Makro (DXY, VIX, USDTRY)** | 5 dakika (poll) | — | ⚠️ Sadece MT5/yfinance |

**Sonuç**: DataHub zaten MT5 Redis üzerinden anlık fiyat ve mum verisi alabiliyor. `market_data_source = "mt5_redis"` veya `"hybrid"` ayarlandığında MT5/yfinance poll devre dışı kalıyor, tüm veri MT5'ten geliyor.

### 1.3 MT5 Redis Client (`mt5_redis_client.py`)

- **Tick kanalı**: `mt5:tick:*` → `data_hub.ingest_live_price()` → WS broadcast
- **Bar kanalları**: `mt5:bar:5m`, `mt5:bar:1h`, `mt5:bar:1d` → `data_hub.ingest_candles()`
- Otomatik sembol normalizasyonu (NASDAQ → NDX.INDX, GOLD → XAUUSD vb.)
- Her tick geldiğinde fiyat anında WS üzerinden frontend'e yayınlanıyor

---

## 2. BACKGROUND SCHEDULER ve MODEL YENİLEME DÖNGÜSÜ

### 2.1 Zamanlama Tablosu (`background_scheduler.py`)

| Görev | Aralık | Açıklama |
|-------|--------|----------|
| **Veri güncelleme + WS broadcast** | 10 saniye | `run_update_cycle()` — fiyat, TA, ML tahmini, cache |
| **ML Prediction Log** | 1800 saniye (30 dk) | `log_predictions_if_needed()` — Supabase'e kayıt |
| **Pulse/EMEL Sinyal Log** | 1800 saniye (30 dk) | `log_pulse_signals_if_needed()` |
| **SMC Sinyal Log** | 180 saniye (3 dk) | `log_smc_signals_if_needed()` |
| **Makro veri** | 300 saniye (5 dk) | Macro update |
| **Haber güncelleme** | 600 saniye (10 dk) | News update |
| **Lifecycle check** | Her döngüde | Aktif sinyallerin TP/SL kontrolü |

### 2.2 Kritik Bulgu: Scheduler Ana Döngüsü

`background_scheduler_loop_with_rss()` her **10 saniyede** bir çalışır:
1. `run_update_cycle()` çağırır → her sembol için:
   - `update_symbol_data()` → ML tahmin + TA snapshot + fiyat + makro
   - `save_to_cache()` → Supabase'e kaydet
   - `ws_manager.broadcast()` → Frontend'e yayınla
2. Pulse panel cache'i ısıtır (`_warm_pulse_panel_cache()`)
3. Sinyal loglama (interval kontrolü ile)

**ÖNEMLİ**: `update_symbol_data()` her 10 saniyede çağrılsa da, içerideki `get_ml_prediction()` kendi iç cache'ine sahip ve gereksiz yeniden hesaplama yapmaz.

---

## 3. PANEL ve MODEL ANALİZİ — Detaylı Sinyal Karar Mantıkları

### 3.1 ML Prediction Service (Ana ML Modeli)

**Dosya**: `ml_prediction_service.py`  
**Model**: LightGBM (model_lgbm_nasdaq.joblib, model_lgbm_xauusd.joblib)  
**Veri İhtiyacı**: 150+ teknik özellik (M30 ana, H1 ve H4 tamamlayıcı)

**Karar Mantığı**:
1. `get_ohlcv_data()` → DataHub'dan mum verileri al (M30 ana timeframe)
2. `_compute_technical_indicators()` → ~30 teknik indikatör hesapla (EMA20/50/200, RSI14/7, MACD, Stochastic, Bollinger, ADX, ATR, MFI, Williams %R vb.)
3. `_compute_tf_indicators()` → H1 ve H4 timeframe'ler için ayrı indikatör seti
4. `_build_feature_vector()` → 150+ özellik vektörü oluştur (M30, H1, H4 çapraz)
5. LightGBM model.predict_proba() → BUY/SELL/HOLD olasılıkları
6. `_apply_layered_confidence()` → 3 katmanlı güven hesaplaması:
   - **Kritik Katman (50%)**: Trend + Regime → Harmonik ortalama
   - **Teknik Katman (30%)**: S/R + Pattern + Candlestick → Geometrik ortalama
   - **Bağlam Katman (20%)**: Haber + COT + Session → Aritmetik ortalama
7. Signal Stability System: 15 dk cooldown, min %55 güven, min %0.15 fiyat değişimi

**Anlık Veri Etkisi**: ⭐⭐⭐ (YÜKSEK)
- ML modeli DataHub'dan mum okur → DataHub zaten anlık güncel
- AMA: Model 30m mumlar üzerinde çalışır → her tick'te yeniden hesaplamanın anlamı yok
- İYİLEŞTİRME: Mum **kapanış anında** otomatik tetikleme (şu an 10s poll)

---

### 3.2 Pulse 1 — Algoritmik Scalp

**Endpoint**: `/api/panel/pulse/{symbol}`  
**Timeframe**: 5m (varsayılan)  
**Cache TTL**: 60 saniye (Redis)  
**Frontend Poll**: 60 saniye

**Karar Mantığı (100 puan üzerinden)**:
| Faktör | Maks Puan | Açıklama |
|--------|-----------|----------|
| Son 10 mum yönü | 20 | 7+ aynı yön = tam puan |
| EMA Stack (5/10/20) | 25 | EMA5 > EMA10 > EMA20 = bullish stack |
| RSI Momentum | 20 | Yönle uyumlu RSI |
| MACD Histogram | 15 | Yönle uyumlu MACD |
| Hacim | 10 | Volume ratio >= 1.3 |
| Stochastic | 10 | K değeri yönle uyumlu |
| 4H Pattern bonus | +10 | Harmonik pattern onayı |

**Sinyal Eşikleri**: CONFIRM ≥ 56, SCOUT ≥ 35, HOLD < 35  
**Filtreler**: Regime (STRONG_TREND'de devre dışı), R/R minimum, RSI aşırı bölge, yön filtresi

**Fiyat Kaynağı**: `fetch_latest_price(symbol)` → DataHub'dan canlı fiyat (30s max gecikme)

**Anlık Veri Etkisi**: ⭐⭐⭐⭐ (ÇOK YÜKSEK)
- 5m scalp modeli → fiyat hassasiyeti yüksek
- Mevcut durum: Cache 60s + poll 60s = **120 saniyeye kadar gecikme**
- İYİLEŞTİRME: Anlık veri ile her 5m mum kapanışında otomatik recalculate

---

### 3.3 Pulse 2 — ML + TA Hibrit

**Endpoint**: `/api/panel/pulse-ml/{symbol}`  
**Timeframe**: 15m (varsayılan)  
**Cache TTL**: 60 saniye  
**Frontend Poll**: Yok (sadece dashboard-refresh event'i)

**Karar Mantığı (100 puan üzerinden)**:
| Faktör | Maks Puan | Açıklama |
|--------|-----------|----------|
| ML Güven | 40 | ML model + TA fallback |
| EMA Trend Onayı | 25 | Fiyat > EMA20 > EMA50 |
| MACD Momentum | 15 | Yönle uyumlu histogram |
| RSI Filtresi | 10 | Regime-aware RSI |
| Hacim Onayı | 10 | Volume ratio kontrolü |
| 4H Pattern bonus | +10 | Harmonik pattern onayı |

**TA Fallback**: ML HOLD verdiğinde TA yönü (EMA + MACD + RSI oylaması) devreye girer  
**Anlık Veri Etkisi**: ⭐⭐⭐ (YÜKSEK) — ML modeli 15m mum bazlı, TA kısmı anlık fayda görür

---

### 3.4 Pulse 3 — 3 Zamanlı Hibrit

**Endpoint**: `/api/panel/pulse-v3/{symbol}`  
**Timeframe**: 5m(%50) + 1H(%30) + 4H(%20)  
**Cache TTL**: 60 saniye  
**Frontend Poll**: Yok (sadece dashboard-refresh event'i)

**Karar Mantığı**:
- `_analyze_5m()`: Son 10 mum yönü (15p) + EMA stack (15p) + Hacim (10p) + RSI (10p) = max 50
- `_analyze_1h()`: Değişim (20p) + EMA onayı (10p) = max 30
- `_analyze_4h()`: Değişim (15p) + EMA onayı (5p) = max 20
- Toplam: max 100 + pattern bonus (+10)
- Order Block entegrasyonu (4H OB tespiti → SCOUT → CONFIRM yükseltme)

**5m veri cache**: 30 saniye, 1H veri cache: 300 saniye (5 dk), 4H veri cache: 600 saniye (10 dk)

**Anlık Veri Etkisi**: ⭐⭐⭐⭐ (ÇOK YÜKSEK) — 5m ağırlığı %50, anlık veri en çok burayı etkiler

---

### 3.5 EMEL — 9 Kontrol Noktalı Analiz

**Endpoint**: `/api/panel/emel/{symbol}`  
**Timeframe**: 1H  
**Cache**: Yok (doğrudan hesaplama)  
**Frontend**: WS üzerinden `panels.emel` key'i ile alır

**9 Kontrol Noktası**:
1. Trend Analizi (EMA 20/50/200)
2. Rejim Tespiti (ADX + Yapı)
3. Multi-Timeframe Uyumu (1D/4H/1H/15m)
4. RSI Momentum
5. MACD Trend
6. Hacim Profili
7. ML Tahmin Onayı
8. Formasyon Tespiti (Harmonic patterns)
9. Nihai Karar (Rebound filtresi dahil)

**Sinyal Eşiği**: 5/9 yeşil → BUY/SELL, 4/9 + ML uyumu → BUY/SELL, aksi halde HOLD

**Anlık Veri Etkisi**: ⭐⭐⭐ (YÜKSEK) — 1H bazlı ama canlı fiyat kritik (EMA/RSI/destek-direnç hesapları)

---

### 3.6 SMC — Smart Money Concepts

**Endpoint**: `/api/deepseek/smc/{symbol}`  
**Veri**: Günlük (EOD) mumlar, 50 barlık  
**Cache**: Yok  
**Frontend Poll**: 5 dakika

**Mantık**: `calculate_smc_with_gaps()` — Kural tabanlı geometrik hesaplama
- FVG (Fair Value Gap) tespiti
- Likidite alanları
- Order flow analizi
- Swing structure

**Anlık Veri Etkisi**: ⭐ (DÜŞÜK)
- Günlük mum bazlı → anlık tick verisi minimal fayda
- Gün içi FVG tespiti eklenmesi: potansiyel iyileştirme

---

### 3.7 Meta Engine — Konsensüs Sistemi

**Endpoint**: `/api/meta/dashboard`  
**Cache**: Yok  
**Frontend Poll**: 60 saniye

**Mantık**: Tüm model sinyallerini bir araya getirip konsensüs oluşturur  
**Anlık Veri Etkisi**: ⭐⭐ (ORTA) — Alt modeller ne kadar taze ise meta sinyal de o kadar taze

---

### 3.8 Market Regime Service

**Dosya**: `market_regime_service.py`  
**Cache**: 30 dakika  
**Veri**: DataHub'dan 1H ve 4H mumlar

**Mantık**: ADX + ATR + Swing Structure → STRONG_TREND_UP / STRONG_TREND_DOWN / RANGING / TRANSITION  
**Anlık Veri Etkisi**: ⭐⭐ (ORTA) — Regime 30 dk'da bir değişir, daha sık yenilemenin anlamı sınırlı

---

## 4. GRAFİK PANELLER — Veri Tüketim Analizi

### 4.1 Clear Trend Panel (V3)

**Backend**: `/api/clear-trend/{timeframe}/{symbol}`  
**Veri**: `fetch_ohlc_data()` → DataHub + `fetch_latest_price()` → canlı fiyat  
**Frontend**: WS üzerinden `panels.clear_trend` key'i ile alır (NO HTTP poll)

**Hesaplama**: 
- Swing high/low fractal (3-bar) → Cluster → S/R seviyeleri
- EMA alignment (20/50/200) → Trend yönü/gücü
- ATR normalizasyon → Güç yüzdesi

**Anlık Veri Etkisi**: ⭐⭐⭐⭐⭐ (KRİTİK)
- S/R seviyelerine mesafe anlık fiyata göre hesaplanır
- Trend gücü EMA-fiyat mesafesiyle ölçülür
- **Mevcut güncelleme**: WS broadcast her 10 saniye (scheduler döngüsü)
- İYİLEŞTİRME: Fiyat WS update geldiğinde S/R mesafeleri frontend'de anlık yenilenebilir

---

### 4.2 Harmonic Visualizer Panel

**Backend**: `/api/panel/harmonic/{symbol}`  
**Frontend**: `useQuery` ile HTTP fetch (refetchInterval var)  
**Veri**: DataHub'dan 4H mum verileri

**Anlık Veri Etkisi**: ⭐⭐ (ORTA) — 4H pattern tespiti, anlık veri etkisi düşük

---

### 4.3 MTF Matrix Panel

**Frontend**: WS üzerinden `panels.mtf` key'i ile alır  
**Anlık Veri Etkisi**: ⭐⭐⭐ (YÜKSEK) — Birden fazla timeframe trend gösterimi, anlık güncelleme değerli

---

### 4.4 Order Block Chart Panel

**Backend**: `/api/order-blocks/detect`  
**Frontend**: `useQuery` (refetchInterval)  
**Veri**: DataHub mumları  
**Anlık Veri Etkisi**: ⭐⭐ (ORTA) — OB tespiti tarihi veri bazlı, ama fiyat-OB mesafesi anlık değerli

---

## 5. FRONTEND → BACKEND VERİ TÜKETİM PATERNLERİ

### 5.1 WebSocket Kanal Yapısı

```
Frontend ←──── /ws/all ←──── ws_manager.broadcast()
                                    ↑
                             background_scheduler (10s)
                                    ↑
                             DataHub (anlık MT5 veya 5s MT5/yfinance poll)
```

**Mesaj Tipleri**:
- `type: "update"` — Tam sembol verisi (ML, TA, fiyat, makro, paneller)
- `type: "price_update"` — Sadece fiyat güncellemesi (anlık tick)

### 5.2 Panel Veri Kaynağı Özeti

| Panel | Veri Kaynağı | Güncelleme | Anlık Veri Kullanır? |
|-------|-------------|------------|---------------------|
| **Clear Trend V3** | WS `panels.clear_trend` | 10s (scheduler) | ⚠️ Kısmen (fiyat WS'den) |
| **Clear Trend (Cyberpunk)** | WS `panels.clear_trend` | 10s (scheduler) | ⚠️ Kısmen |
| **EMEL Panel** | WS `panels.emel` | 10s (scheduler) | ⚠️ Kısmen |
| **MTF Matrix** | WS `panels.mtf` | 10s (scheduler) | ⚠️ Kısmen |
| **Pulse 1** | HTTP poll | 60s | ❌ Cache 60s |
| **Pulse 2** | HTTP (refresh event) | Manuel | ❌ Cache 60s |
| **Pulse 3** | HTTP (refresh event) | Manuel | ❌ Cache 60s |
| **SMC** | HTTP poll | 5 dakika | ❌ |
| **Meta Engine** | HTTP poll | 60s | ❌ |
| **Harmonic** | HTTP poll (useQuery) | refetchInterval | ❌ |
| **Order Blocks** | HTTP poll (useQuery) | refetchInterval | ❌ |
| **Strategy Performance** | HTTP poll (useQuery) | refetchInterval | ❌ |
| **Fiyat Ticker (Header)** | WS `price_update` | Anlık | ✅ TAM ANLIK |
| **Model Analysis** | HTTP poll (useQuery) | refetchInterval | ❌ |

---

## 6. SONUÇ ve ÖNERİLER

### 6.1 Mevcut Durumun Değerlendirmesi

**İyi olan**:
- ✅ DataHub zaten MT5 Redis'ten anlık veri alabiliyor
- ✅ Fiyat ticker'ı (header) tam anlık çalışıyor
- ✅ WS altyapısı sağlam (`price_update` + `update` mesaj tipleri)
- ✅ DataHub türetilmiş timeframe'leri otomatik resample ediyor

**İyileştirme gereken**:
- ⚠️ Background scheduler 10 saniyede bir TÜM modelleri yeniden hesaplıyor → CPU israfı
- ⚠️ Panel cache'leri (60s Redis) anlık veri avantajını ortadan kaldırıyor
- ⚠️ Frontend panellerin çoğu HTTP poll → WS stream'den faydalanmıyor
- ⚠️ Model yeniden hesaplama mum kapanışına bağlı değil, zamana bağlı

---

### 6.2 KATMANLI İYİLEŞTİRME ÖNERİLERİ

#### 🟢 Katman 1: Düşük Risk, Yüksek Etki (Hemen Yapılabilir)

**1A. Fiyat-duyarlı frontend güncellemesi**
- Clear Trend, EMEL gibi panellerde `price_update` WS mesajı geldiğinde sadece **fiyata bağlı hesaplamaları** (S/R mesafesi, yüzde değişimi) frontend'de anlık güncelle
- Backend yeniden hesaplamaya gerek yok
- Tahmini etki: Kullanıcı deneyiminde **anlık hissiyat**, sıfır ek maliyet

**1B. WS üzerinden panel verisi aktif tüketimi**
- Pulse 1/2/3 panellerini HTTP poll → WS stream'e çevir
- Zaten scheduler her 10s'de `_warm_pulse_panel_cache()` çalıştırıyor ve WS üzerinden yayınlıyor
- Frontend'de `useWSPanelData(symbol, "pulse_v3")` kullanımı
- Tahmini etki: **50s gecikme azalması** (60s poll → 10s WS)

#### 🟡 Katman 2: Orta Risk, Yüksek Etki (1-2 Haftalık Çalışma)

**2A. Mum Kapanışı Tetiklemeli Model Yenileme (Event-Driven)**
```
DataHub: 5m mum kapandı → Event yayınla
  → Pulse 1/3: 5m bazlı → Hemen yeniden hesapla
  → Clear Trend: → S/R seviyelerini güncelle
  
DataHub: 1H mum kapandı → Event yayınla
  → EMEL: 1H bazlı → Hemen yeniden hesapla
  → Pulse 2: 15m bazlı → Yeniden hesapla
  
DataHub: 30m mum kapandı → Event yayınla
  → ML Model: M30 bazlı → Yeniden hesapla
```

Bu yaklaşım:
- 10s blind polling yerine **akıllı tetikleme**
- Gereksiz hesaplamaları ortadan kaldırır
- Mum kapanış anında anında yeni sinyal üretir
- **CPU kullanımı %70 azalır** (çoğu 10s döngüde mum kapanmamış)

**2B. Anlık Fiyat ile TA Mikroguncellemesi**
- Her tick'te TÜM indikatörleri yeniden hesaplamak yerine, sadece fiyat-bağımlı olanları güncelle:
  - `current_price > EMA_20` → Trend yönü değişti mi?
  - `current_price - support_level` → S/R mesafesi
  - RSI approximate (son bar verisiyle hızlı hesap)
- Ağır hesaplamalar (bollinger, ADX, ATR) mum kapanışına bırakılır

**2C. Regime Cache Süresini Azaltma**
- 30 dakikadan → **15 dakikaya** düşür
- Sadece gerçek rejim değişikliklerinde (ADX eşik geçişi) broadcast yap
- Anlık veri ile ADX'in eşik geçişini tespit edip erken uyarı ver

#### 🔴 Katman 3: Yüksek Risk, Çok Yüksek Etki (Uzun Vadeli Proje)

**3A. Tick-Level Micro Signal Engine**
- Mevcut modellerin üzerine, sadece anlık tick akışına dayalı bir "micro signal" katmanı:
  - **Hızlı momentum**: Son 30 tick'in yönü
  - **Spread değişimi**: Bid-Ask genişleme → volatilite uyarısı
  - **Tick hızı**: Saniyedeki tick sayısı → aktivite seviyesi
  - **Volume spike**: Anlık hacim patlaması tespiti
- Bu, mevcut 5m/1H modellerinin "erken uyarı" katmanı olur

**3B. ML Modeline Tick Özellikleri Ekleme**
- Feature vector'e tick bazlı özellikler ekle:
  - `tick_momentum_30s`: Son 30s tick yön ortalaması
  - `tick_rate_per_minute`: Dakikadaki tick sayısı
  - `bid_ask_spread_ratio`: Spread / ATR oranı
  - `volume_acceleration`: Hacim ivmesi
- Bu özellikler LightGBM modeline ekstra bilgi verir

**3C. Adaptive Signal Threshold**
- Anlık volatiliteye göre sinyal eşiklerini dinamik ayarla:
  - Yüksek volatilite → Eşikleri yükselt (gürültü filtresi)
  - Düşük volatilite → Eşikleri düşür (fırsatları kaçırma)

---

### 6.3 PANEL BAZLI DETAYLI ÖNERİ MATRİSİ

| Panel | Mevcut | Öneri | Beklenen İyileşme |
|-------|--------|-------|-------------------|
| **Pulse 1** | 60s HTTP poll, 60s cache | WS stream + mum kapanış tetikleme | Gecikme: 120s → <5s |
| **Pulse 2** | Manuel refresh | WS stream + 15m mum kapanış tetikleme | Gecikme: dakikalar → <15s |
| **Pulse 3** | Manuel refresh | WS stream + 5m mum kapanış tetikleme | Gecikme: dakikalar → <5s |
| **EMEL** | WS 10s | 1H mum kapanış tetikleme + anlık fiyat güncelleme | Gecikme: 10s → anlık fiyat, 1H mum → sinyal |
| **Clear Trend** | WS 10s | Anlık fiyat → frontend S/R mesafe güncelleme | Gecikme: 10s → anlık |
| **SMC** | 5dk HTTP poll | Günlük mum bazlı → değişiklik yok | — (zaten yeterli) |
| **ML Model** | 10s scheduler | 30m mum kapanış tetikleme | CPU: %70 azalma |
| **Regime** | 30dk cache | 15dk + ADX eşik tetikleme | Daha hızlı regime değişikliği |
| **Meta Engine** | 60s HTTP poll | Alt model değişikliğinde tetikleme | Daha taze konsensüs |
| **Harmonic** | HTTP poll | 4H mum kapanış tetikleme | CPU azalma |
| **Order Blocks** | HTTP poll | 4H mum kapanış tetikleme | Daha taze OB |

---

### 6.4 TEKNİK UYGULAMA PLANI (Event-Driven Mimariye Geçiş)

```python
# data_hub.py — Mum kapanış event sistemi
_candle_close_callbacks = defaultdict(list)  # timeframe -> [callback_fn]

def on_candle_close(timeframe: str, callback: Callable):
    """Register callback for candle close events."""
    _candle_close_callbacks[timeframe].append(callback)

async def _notify_candle_close(symbol: str, timeframe: str, candle: dict):
    """Notify all registered callbacks when a candle closes."""
    for callback in _candle_close_callbacks.get(timeframe, []):
        try:
            await callback(symbol, timeframe, candle)
        except Exception as e:
            logger.warning(f"Candle close callback error: {e}")
```

```python
# background_scheduler.py — Event-driven model refresh
async def on_5m_candle_close(symbol: str, timeframe: str, candle: dict):
    """Triggered when a 5m candle closes."""
    await recalculate_pulse1(symbol)
    await recalculate_pulse3(symbol)
    await broadcast_updated_panels(symbol, ["pulse_v3", "clear_trend"])

async def on_1h_candle_close(symbol: str, timeframe: str, candle: dict):
    """Triggered when a 1H candle closes."""
    await recalculate_emel(symbol)
    await recalculate_pulse2(symbol)
    await broadcast_updated_panels(symbol, ["emel", "mtf"])

async def on_30m_candle_close(symbol: str, timeframe: str, candle: dict):
    """Triggered when a 30m candle closes."""
    await recalculate_ml_prediction(symbol)
    await broadcast_updated_panels(symbol, ["ml_prediction"])
```

---

### 6.5 YAPILMAMASI GEREKENLER (Riskler)

1. **❌ Her tick'te tüm modelleri yeniden hesaplamayın** — CPU patlaması, aynı sonuç
2. **❌ Signal stability (cooldown) sistemini devre dışı bırakmayın** — Sinyal churn problemi geri döner
3. **❌ Scheduler'ı tamamen kaldırmayın** — Bazı görevler (news, macro, lifecycle check) hâlâ zamana bağlı olmalı
4. **❌ Redis cache TTL'ini 0'a düşürmeyin** — Yoğun istek dönemlerinde backend çöker
5. **❌ Prediction Log interval'ını azaltmayın** — 30dk cooldown ile uyumlu olmalı (signal churn riski)

---

## 7. ÖNCELİK SIRASI

| # | İyileştirme | Zorluk | Etki | Öncelik |
|---|-------------|--------|------|---------|
| 1 | Frontend anlık fiyat S/R mesafe güncelleme | Kolay | Yüksek | 🔥 Hemen |
| 2 | Pulse panellerini WS stream'e çevir | Kolay | Yüksek | 🔥 Hemen |
| 3 | 5m mum kapanış tetiklemeli Pulse 1/3 yenileme | Orta | Çok Yüksek | ⭐ 1. Sprint |
| 4 | 1H mum kapanış tetiklemeli EMEL yenileme | Orta | Yüksek | ⭐ 1. Sprint |
| 5 | 30m mum kapanış tetiklemeli ML yenileme | Orta | Yüksek | ⭐ 1. Sprint |
| 6 | Regime cache süresini 15dk'ya düşür | Kolay | Orta | 2. Sprint |
| 7 | Tick-level micro signal katmanı | Zor | Çok Yüksek | 3. Sprint |
| 8 | ML modeline tick özellikleri ekleme | Zor | Yüksek | 4. Sprint |

---

## 8. ÖZET

**Mevcut sistem anlık veri ALABILIYOR** (MT5 Redis köprüsü sağlam çalışıyor), fakat **anlık veriyi TÜKETİM** tarafında yeterince verimli kullanamıyor. Ana darboğazlar:

1. **Zamana bağlı polling** yerine **event-driven (mum kapanışı) tetikleme** gerekiyor
2. **Frontend panellerin çoğu** hâlâ HTTP poll kullanıyor, WS stream'den faydalanmıyor
3. **Cache TTL'leri** (60s Redis) anlık verinin faydalarını geciktiriyor
4. **CPU israfı**: 10s'de bir tüm modelleri yeniden hesaplamak yerine, sadece yeni mum kapandığında hesapla

Bu iyileştirmeler yapıldığında:
- **Sinyal gecikmesi**: 60-120s → <5s (5m bazlı modeller)
- **CPU kullanımı**: %60-70 azalma
- **Kullanıcı deneyimi**: Anlık fiyat hareketlerinde paneller canlı tepki verir
- **Model doğruluğu**: Daha taze veri ile hesaplanan sinyaller → daha isabetli kararlar
