# ForexSAI Trading Portal - Sistem Dokümantasyonu

> **Proje:** ForexSAI AI Trading Dashboard  
> **Oluşturulma Tarihi:** 14 Nisan 2026  
> **Son Güncelleme:** 2026-07-01 (Gösterge Denetimi — detay: `UYGULAMA_NOTLARI_2026-07-01.md`)  
> **Doküman Tipi:** Teknik Sistem Dokümantasyonu (Haber Analiz Sistemi Hariç)  

> ⚠️ **2026-07-01 Gösterge Denetimi değişiklikleri:** Merkezi sinyal kapıları (`services/signal_gates.py`: XAU trend-SELL, seans, takvim, GDAXI pulse1 askısı), TP1→breakeven semantiği (`direction_flip_after_tp`), pulse1'de Stochastic→H4 Trend Uyumu, PULSE 3 rejime duyarlı TF ağırlıkları, endekslerde ATR-taban TP/SL, EMEL 10. kontrol (Makro Uyum), XAUUSD gerçek 1h bar tercihi, ml_cross deneyi kapalı. Bu dokümanın ilgili bölümleri güncellenmiştir.

---

## 1. PROJE ÖZETİ

ForexSAI, yapay zeka destekli, gerçek zamanlı piyasa analizi ve trading sinyalleri sunan uçtan uca (end-to-end) bir trading dashboard sistemidir. NASDAQ (NDX.INDX), Altın (XAUUSD), DAX (GDAXI.INDX) ve Ham Petrol (USOIL.FOREX) için ML tabanlı tahminler, pattern analizi, sentiment analizi ve Smart Money Concepts (SMC) sinyalleri sağlar.

### Ana Özellikler
- **Gerçek Zamanlı Piyasa Verisi:** MT5/yfinance WebSocket entegrasyonu ile canlı fiyatlar
- **ML Tahmin Pipeline:** 150+ teknik özellik ile LightGBM modelleri
- **Çoklu Zaman Dilimi Analizi:** 5m, 15m, 30m, 1h, 4h, 1d
- **AI Destekli Analiz:** DeepSeek, Anthropic, Groq, xAI entegrasyonları
- **Sinyal Yaşam Döngüsü Takibi:** Otomatik TP/SL izleme ve başarısızlık otopsisi
- **Kendi Kendine Öğrenen Sistem:** Tahmin doğruluğu takibi ve hatalardan öğrenme
- **Smart Money Concepts:** Order block, Fair Value Gaps (FVG), COT raporları

---

## 2. MİMARİ YAPI

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                         [Railway/Netlify] │
│  ├─ page.tsx (ana SPA dashboard, ~64KB)                         │
│  ├─ 28+ Panel bileşeni (lazy-loaded)                            │
│  ├─ WebSocketContext → gerçek zamanlı veri                     │
│  ├─ Zustand stores (dashboard, chart, news, ML strategy)       │
│  ├─ React Query HTTP fallback                                   │
│  └─ Çoklu dil desteği (next-intl)                               │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI)                             [Railway]        │
│  ├─ main.py (31 router, lifespan yönetimi)                    │
│  ├─ DataHub (merkezi MT5/yfinance veri pompası)                        │
│  ├─ BackgroundScheduler (periyodik güncellemeler)             │
│  ├─ ML Prediction Service (LightGBM modeller)                   │
│  ├─ Signal Lifecycle (aktif sinyal takibi)                    │
│  ├─ Trading Engine (16 alt-modül)                               │
│  └─ WebSocket broadcast (/ws/all)                               │
├─────────────────────────────────────────────────────────────────┤
│  DATABASE (Supabase PostgreSQL)                                 │
│  ├─ candle_cache (kalıcı OHLCV)                                 │
│  ├─ prediction_logs (sinyal takibi)                             │
│  ├─ signal_checks (yaşam döngüsü pingleri)                      │
│  ├─ failure_autopsies (ölüm sonrası analiz)                    │
│  ├─ outcome_results (öğrenme sistemi)                           │
│  ├─ users / pro_users (kimlik doğrulama)                        │
│  └─ meta_combination_stats (model kombinasyon performansı)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. TEKNOLOJİ STACK

### Frontend
| Kategori | Teknoloji |
|----------|-----------|
| Framework | Next.js 14 (App Router) |
| Dil | TypeScript 5.5 |
| Styling | Tailwind CSS 3.4 |
| State Management | Zustand 4.5 + React Query 5.51 |
| Grafikler | Recharts 2.12, Lightweight Charts 4.2 |
| Animasyon | Framer Motion |
| Test | Vitest 2.0 + jsdom |
| UI Bileşenleri | Custom (shadcn/ui kullanılmıyor) |

### Backend
| Kategori | Teknoloji |
|----------|-----------|
| Framework | FastAPI 0.111 |
| Dil | Python 3.11+ |
| ML/AI | LightGBM 4.3, XGBoost 2.0, scikit-learn 1.5 |
| Veri | Pandas 2.2, NumPy 1.26 |
| Database | Supabase (PostgreSQL) |
| Cache | Redis (opsiyonel, bellek fallback) |
| AI APIs | DeepSeek (birincil), Anthropic, Groq, xAI, OpenAI |
| WebSocket | Native websockets library |

### Altyapı
| Kategori | Teknoloji |
|----------|-----------|
| Deployment | Railway (Nixpacks) + Netlify |
| Frontend URL | https://upbeat-flow-production.up.railway.app |
| API/WebSocket | Aynı domain (wss:// için WebSocket) |

---

## 4. VERİ AKIŞI (DATA FLOW)

### 4.1 DataHub - Merkezi Veri Yönetimi

**Dosya:** `backend/services/data_hub.py` (~1458 satır)

```
Başlangıç:  Supabase (candle_cache) → DataHub (bellek)
Çalışma:    MT5 bridge + yfinance (delta sadece) → DataHub (bellek) → persist Supabase
Restart:   Supabase'ten yükle (0 API çağrısı) → sadece yeni mumları çek
```

**Fetch Planı (başlangıç sonrası):**
- Gerçek zamanlı fiyat: her 30s sembol başına
- 5m mumlar: her 5dk, DELTA sadece (24 mum = ~2sa)
- 1h mumlar: her 5dk, DELTA sadece (6 mum = ~6sa)
- EOD mumlar: her 30dk, DELTA sadece (5 mum = ~5gün)

**Türetilmiş (hesaplanan, 0 API çağrısı):**
- 15m mumlar: 5m'den resample (3x)
- 30m mumlar: 5m'den resample (6x)
- 4h mumlar: 1h'den resample (4x)

**Günlük API Bütçesi (ilk seed sonrası):**
- Price: 3 sembol × 1 çağrı × 2/dk × 60dk × 24sa = ~8,640 çağrı
- 5m: 3 sembol × 12/saat × 24sa = 864 çağrı
- 1h: 3 sembol × 12/saat × 24sa = 864 çağrı
- EOD: 3 sembol × 2/saat × 24sa = 144 çağrı
- TOPLAM: ~11,950 / 100,000 limit (~12% kullanım)

### 4.2 Mum Kapama Event Sistemi

```python
@on_candle_close("5m")
async def handle_5m_close(symbol: str, timeframe: str):
    # Model refresh, sinyal kontrolü, vs.
    
# Callback'ler:
# - Meta-Intelligence Engine sinyal üretimi
# - Signal Lifecycle otomatik kontrol
# - WebSocket broadcast
```

### 4.3 Sembol Normalizasyonu

```python
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

# Alias mapping:
# NDX, NASDAQ → NDX.INDX
# XAUUSD.FOREX, GOLD → XAUUSD
# GDAXI, DAX → GDAXI.INDX
# USOIL, CL, WTI → USOIL.FOREX
```

### 4.4 Veri Kaynakları

**MT5 bridge + yfinance (Birincil):**
- Gerçek zamanlı fiyatlar
- Intraday mumlar (5m, 1h)
- EOD günlük mumlar

**Yahoo Finance (Fallback):**
- XAUUSD (GC=F) - emtia
- USOIL (CL=F) - emtia
- ABD saatleri dışında kullanılır

**MT5 Redis (Opsiyonel):**
- `MARKET_DATA_SOURCE=mt5_redis|hybrid`
- Redis pub/sub kanalları: `mt5:tick`, `mt5:bar`
- MT5_redis_client.py ile DataHub'a besleme

---

## 5. MODEL MANTIĞI ve ALGORİTMALAR

### 5.1 ML Prediction Service

**Dosya:** `backend/services/ml_prediction_service.py` (~2568 satır)

**Model Ailesi:**
```python
ML_MODEL_FAMILY_BY_SYMBOL = {
    "NDX.INDX": "NDX.INDX",      # NASDAQ modeli
    "GDAXI.INDX": "NDX.INDX",    # NASDAQ modeli (aile paylaşımı)
    "XAUUSD": "XAUUSD",          # Altın modeli
    "USOIL.FOREX": "XAUUSD",     # Altın modeli (aile paylaşımı)
}

ML_MODEL_FILES = {
    "NDX.INDX": "model_lgbm_nasdaq.joblib",
    "XAUUSD": "model_lgbm_xauusd.joblib",
}
```

**Strateji Presetleri:**
| Preset | Threshold | Açıklama |
|--------|-----------|----------|
| ultra_safe | 58% | Yüksek win rate, az trade |
| balanced | 55% | Optimal win rate/trade sayısı |
| full_power | 52% | Tüm faktörler aktif |
| aggressive | 50% | Çok trade, düşük filtre |
| nasdaq_precision | 60% | NASDAQ için optimize |

**Confidence Katmanları:**
```python
CONFIDENCE_LAYERS = {
    "critical": {      # 50% ağırlık
        "factors": ["trend", "regime"],
        "logic": "harmonic"  # Küçük değerleri yumuşatır
    },
    "technical": {     # 30% ağırlık
        "factors": ["sr", "pattern", "candle"],
        "logic": "geometric"  # Dengeli etki
    },
    "context": {       # 20% ağırlık
        "factors": ["news", "cot", "session", "confluence"],
        "logic": "arithmetic"  # Basit ortalama
    }
}
```

**Sinyal Stabilite Sistemi:**
- Soğuma süresi: 15 dakika
- Min reversal confidence: 55%
- Min fiyat değişimi: 0.15%
- Aynı yön sinyalleri her zaman izin verilir

### 5.2 PULSE Modelleri (3 Adet)

**Dosya:** `backend/routers/emel_pulse.py` (~2955 satır)

#### PULSE 1 (Algo) - `/api/panel/pulse/{symbol}`
```python
# 6-bileşenli puanlama (100 puan) — 2026-07-01 revizyonu
components = {
    "candle_10": 20,      # Son 10 mum yönü
    "ema_stack": 25,      # EMA 5/10/20 stack
    "rsi": 20,            # RSI momentum (trend-aware: yönle uyumlu aşırı RSI ceza YEMEZ)
    "macd": 15,           # MACD histogram
    "volume": 10,         # Hacim onayı
    "h4_alignment": 10    # H4 trend uyumu (Stochastic'in yerini aldı — RSI ile mükerrerdi)
}
# Stochastic artık yalnızca görüntü amaçlı (skor katkısı 0)
# SCOUT(35-55)/CONFIRM(56+), R/R min regime.min_rr (dinamik)
# GDAXI'de pulse1 ASKIDA (60g WR %25) — GDAXI_PULSE1_ENABLED=1 ile açılır
# Sinyal sonrası merkezi kapılar: signal_gates.apply_signal_gates()
```

#### PULSE 2 (ML+TA) - `/api/panel/pulse-ml/{symbol}`
```python
# ML confidence + EMA20+EMA50+MACD triple onay
# ML threshold: 45% (SCOUT için düşürülmüş)
# Regime-aware RSI
# Trend EMA pullback puanlaması
# Dinamik ATR hedefleri (3x trend modu)
```

#### PULSE 3 (Hybrid) - `/api/panel/pulse-v3/{symbol}`
```python
# Çoklu zaman dilimi — REGIME-AWARE ağırlıklar (2026-07-01):
#   RANGING:            5m %50 / 1H %30 / 4H %20 (eski dağılım)
#   TRANSITION:         5m %30 / 1H %35 / 4H %35
#   STRONG_TREND / ATH: 5m %25 / 1H %35 / 4H %40  (5m gürültüsü 4H trendini ezemez)
# 1H/4H mutlak % eşikleri ATR-normalize edildi (PULSE3_REGIME_WEIGHTS=1)
# Paralel veri fetch
# Entry zone hesaplama
# Order Block tespiti
```

### 5.3 EMEL (10 Kontrol Noktalı Strateji) — 2026-07-01: Makro Uyum eklendi

**Dosya:** `backend/routers/emel_pulse.py` - `get_emel_analysis()`

```python
# 10 kontrol noktası:
checks = [
    "Trend Analizi",        # EMA20/50/200 stack + slope
    "Rejim Tespiti",        # ADX + yapı
    "Multi-Timeframe",      # 1D/4H/1H/15m konfluans
    "Formasyon",            # Harmonik pattern (4H)
    "Destek/Direnç",        # Pivot S/R
    "Momentum",             # RSI/MACD/Stochastic
    "Hacim Onayı",          # Volume z-score
    "Learning",             # Geçmiş performans (win rate)
    "Portföy Riski",        # Günlük risk limiti (hard gate)
    "Makro Uyum"            # YENİ (2026-07-01): DXY/US10Y (emtia), VIX (endeks)
]

# Konfluans ağırlıkları sembol-spesifik (bkz. CLAUDE.md "Enstrüman-Spesifik
# EMEL Ağırlıkları"): macro ağırlığı XAU=15, USOIL=10, endeksler=5.
# GDAXI revizyonu: volume 15→8, sr 15→12, trend 20→25.
# XAUUSD EMEL 60g WR: %84.8 — ATH SELL bloğu diğer modellere de genellendi
# (signal_gates.xau_trend_sell_gate).
```

### 5.4 Meta-Intelligence Engine

**Dosya:** `backend/services/meta_analysis_engine.py` (~1053 satır)

**6 Model Kombinasyonu:**
```python
MODEL_IDS = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]

DEFAULT_MODEL_WEIGHTS = {
    "ml": 0.25, "pulse1": 0.15, "pulse2": 0.15,
    "pulse3": 0.15, "emel": 0.20, "smc": 0.10
}
```

**Rejim Bazlı Ağırlık Çarpanları:**
```python
REGIME_WEIGHT_MULTIPLIERS = {
    "STRONG_TREND_UP":   {"ml": 1.2, "pulse1": 0.8, "pulse3": 1.3, ...},
    "STRONG_TREND_DOWN": {"ml": 1.2, "pulse1": 0.8, "pulse3": 1.3, ...},
    "RANGING":           {"ml": 0.8, "pulse1": 1.3, "smc": 1.3, ...},
    "VOLATILE":          {"ml": 0.7, "emel": 1.0, "smc": 1.4, ...},
    "TRANSITION":        {tüm modeller: 1.0}
}
```

**Teknik Doğrulama (8 Koşul):**
1. EMA Stack (20 > 50 > 200 için BUY)
2. Price vs EMA200
3. RSI Momentum (BUY: 40-75, SELL: 25-60)
4. MACD Alignment
5. ADX Strength (>20 = trending)
6. Volume Confirmation (>0.8x average)
7. Bollinger Band Position
8. ATR Validity

**Meta Sinyal Yaşam Döngüsü:**
- Her 60 saniyede kontrol
- Her 20 dakikada loglama (prediction_logs, model_type='meta')
- Canonical hedef/SL hesaplamaları (target_config.py)
- TP/SL çözünürlüğü signal_lifecycle.py tarafından yönetilir

### 5.5 Smart Money Zones (SMC)

**Dosya:** `backend/services/order_block_service.py` (~43824 satır)

**Bileşenler:**
- Order Block (OB) tespiti - ICT tarzı
- Fair Value Gaps (FVG)
- CHoCH (Change of Character)
- BOS (Break of Structure)
- Premium/Discount bölgeleri

**Sinyal Mantığı:**
```python
# Asimetrik threshold'lar:
bull_threshold = 75   # BUY için çok yüksek conviction
bear_threshold = 50  # SELL için daha düşük

# TP/SL: 1.0*ATR TP, 2.0*ATR SL
# 30 future candles (honest scalping R:R 0.5:1)
```

**SMC Sinyalleri için Özel Loglama:**
- `model_type='smc'`
- Timeframe-aware active signal handling
- Aynı sembol+farklı timeframe = ayrı sinyaller açık kalabilir

### 5.6 Market Regime Detection

**Dosya:** `backend/services/market_regime_service.py` (~33790 satır)

**4 Rejim:**
```python
REGIMES = [
    "STRONG_TREND_UP",   # Güçlü yükseliş trendi
    "STRONG_TREND_DOWN", # Güçlü düşüş trendi
    "RANGING",           # Yatay bant
    "TRANSITION"         # Geçiş/belirsizlik
]
```

**ADX Hesaplama:**
- Wilder smoothing (14 period)
- 4H veri kullanılır
- ADX > 25 = trending, ADX < 20 = ranging

**ATH (All-Time High) Protocol:**
- ATH bölgesinde (1.5% içinde) SELL bloklanır
- ML threshold 55%'e yükseltilir (normalde 52%)
- Hedefler genişletilir (1.3x), SL daraltılır (0.85x)

**Model Ağırlık Matrisi:**
- STRONG_TREND: Pulse 1 devre dışı (0.0 ağırlık)
- RANGING: Pulse 1 ve SMC güçlendirilir
- TRANSITION: Tüm modeller eşit ağırlık

---

## 6. SİNYAL YAŞAM DÖNGÜSÜ (SIGNAL LIFECYCLE)

**Dosya:** `backend/services/signal_lifecycle.py` (~1687 satır)

### 6.1 Yaşam Döngüsü Aşamaları

```
CREATED → ACTIVE → [COMPLETED|STOPPED|EXPIRED]
              ↓
         CHECK LOOP (her 60s)
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
TP HIT    SL HIT    TIMEOUT
```

### 6.2 Zaman Dilimi Bazlı Değerlendirme

```python
TIMEFRAME_EVALUATION_WINDOWS = {
    "1m": 2,       # 2 dakika
    "5m": 10,      # 10 dakika
    "15m": 15,     # 15 dakika (varsayılan)
    "30m": 60,     # 60 dakika
    "1h": 120,     # 2 saat
    "4h": 480,     # 8 saat
    "1d": 2880,    # 2 gün
}
```

### 6.3 Hedef/SL Çözünürlüğü

**Dosya:** `backend/services/target_config.py`

```python
SYMBOL_CONFIGS = {
    "NDX.INDX": {
        "pip_value": 1.0,
        "targets": [TP1=15, TP2=25, TP3=35, TP4=50],
        "stoploss_pips": 50
    },
    "XAUUSD": {
        "pip_value": 1.0,  # 1 pip = $1.00
        "targets": [TP1=8, TP2=15, TP3=25, TP4=40],
        "stoploss_pips": 15  # Önceki: 8 (çok dar idi)
    },
    "USOIL.FOREX": {
        "is_percentage": True,
        "targets": [TP1=0.02%, TP2=0.04%, TP3=0.06%, TP4=0.1%],
        "stoploss_pips": 0.05%
    }
}
```

### 6.4 Durum Makinesi

```python
STATUS_TRANSITIONS = {
    "active": ["completed", "stopped", "expired"],
    "completed": [],  # Terminal
    "stopped": [],    # Terminal
    "expired": []     # Terminal
}

RESOLUTION_REASONS = {
    "completed": ["tp1_hit", "tp2_hit", "tp3_hit", "tp4_hit", 
                   "all_targets_hit", "partial_then_sl", "target_hit"],
    "stopped": ["sl_hit", "stop_loss_triggered"],
    "expired": ["timeout", "timeframe_expired", "max_duration_reached"]
}
```

### 6.5 Ölçüm ve Metrikler

```python
class LifecycleMetrics:
    total_checks: int           # Toplam kontrol sayısı
    total_signals_processed: int
    total_errors: int
    total_completed: int      # TP'ye ulaşan
    total_stopped: int         # SL tetiklenen
    total_expired: int         # Süre dolan
    last_check_duration_ms: float
    consecutive_failures: int
```

---

## 7. VERİTABANI ŞEMASI

### 7.1 Ana Tablolar

#### prediction_logs
```sql
CREATE TABLE prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(16) DEFAULT '15m',
    
    -- ML Model çıktıları
    ml_direction VARCHAR(8) NOT NULL,  -- BUY, SELL, HOLD
    ml_confidence REAL NOT NULL,
    ml_probability_up REAL,
    ml_probability_down REAL,
    
    -- Hedef ve SL
    ml_target_price REAL,
    ml_stop_price REAL,
    ml_entry_price REAL,
    
    -- Faktörler (JSONB)
    factors JSONB NOT NULL DEFAULT '{}',
    
    -- Model tipi (CHECK constraint)
    model_type VARCHAR(16) CHECK (
        model_type IN ('ml', 'pulse', 'pulse1', 'pulse2', 'pulse3', 
                      'emel', 'hybrid', 'smc', 'meta')
    ),
    
    -- Yaşam döngüsü
    status VARCHAR(16) DEFAULT 'active',
    targets_hit JSONB DEFAULT '{}',
    exit_price REAL,
    
    -- Strateji
    strategy VARCHAR(32),
    strategy_scope VARCHAR(16)
);
```

#### signal_checks
```sql
CREATE TABLE signal_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES prediction_logs(id),
    check_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- Fiyat snapshot
    current_price REAL,
    session_high REAL,
    session_low REAL,
    
    -- Hedef durumu
    targets_hit JSONB,
    highest_profit_pips REAL,
    lowest_drawdown_pips REAL,
    
    -- İşlem sonucu
    would_complete BOOLEAN,
    would_stop BOOLEAN,
    
    -- Metadata
    duration_minutes INT,
    market_open BOOLEAN
);
```

#### outcome_results
```sql
CREATE TABLE outcome_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES prediction_logs(id),
    
    check_interval VARCHAR(16),  -- '1h', '4h', '24h', '7d'
    
    entry_price REAL,
    exit_price REAL,
    high_price REAL,
    low_price REAL,
    price_change_pct REAL,
    
    actual_direction VARCHAR(8),  -- UP, DOWN, FLAT
    hit_target BOOLEAN,
    hit_stop BOOLEAN,
    
    ml_correct BOOLEAN,
    pips_profit REAL,
    pips_loss REAL
);
```

#### meta_combination_stats
```sql
CREATE TABLE meta_combination_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(32),
    regime VARCHAR(32),
    combo_key VARCHAR(64),  -- "ml+pulse2+emel"
    
    total_signals INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    win_rate REAL,
    profit_factor REAL,
    expectancy REAL,
    
    avg_profit_pips REAL,
    avg_loss_pips REAL,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
```

### 7.2 Kalıcı Cache Tabloları

#### candle_cache
```sql
CREATE TABLE candle_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,  -- '5m', '1h', '4h', 'eod'
    candle_time TIMESTAMPTZ NOT NULL,
    
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    
    UNIQUE(symbol, timeframe, candle_time)
);
```

#### candle_cache_meta
```sql
CREATE TABLE candle_cache_meta (
    symbol VARCHAR(32),
    timeframe VARCHAR(8),
    last_update TIMESTAMPTZ,
    candle_count INT,
    source VARCHAR(16),  -- 'mt5_redis', 'derived'
    PRIMARY KEY (symbol, timeframe)
);
```

---

## 8. API ENDPOINT YAPISI

### 8.1 Router Listesi (31 Adet)

| Router | Dosya | Açıklama |
|--------|-------|----------|
| `/api/panel` | emel_pulse.py | EMEL + PULSE 1/2/3 |
| `/api/ml` | prediction.py | ML tahminleri |
| `/api/mtf` | mtf_analysis.py | Çoklu zaman dilimi |
| `/api/learning` | learning.py | Sinyal performansı |
| `/api/signals` | signal_lifecycle_router.py | Yaşam döngüsü |
| `/api/meta` | meta_engine_router.py | Meta-Intelligence |
| `/api/order-blocks` | order_blocks.py | SMC/OB tespiti |
| `/api/data` | data.py | OHLCV verisi |
| `/api/datahub` | data.py | DataHub durumu |
| `/api/run` | nasdaq.py, xauusd.py, dax.py, usoil.py | Sembol çalıştırma |
| `/api/whale` | (main.py) | COT/Whale takibi |
| `/api/optimizer` | strategy_optimizer.py | Strateji optimizasyonu |
| `/api/permutation-analysis` | permutation_router.py | Kombinasyon analizi |
| `/ws` | websocket.py | WebSocket bağlantısı |

### 8.2 WebSocket Yapısı

```python
# Endpoint: /ws/{symbol} veya /ws/all

# Giden mesaj tipleri:
{
    "type": "price_update",
    "symbol": "NDX.INDX",
    "price": 19500.50,
    "timestamp": 1713001200.000
}

{
    "type": "signal_update",
    "symbol": "NDX.INDX",
    "model": "ml",
    "direction": "BUY",
    "confidence": 67.5
}
```

---

## 9. FRONTEND YAPISI

### 9.1 Sayfa ve Panel Yapısı

**Ana Sayfa:** `frontend/app/page.tsx` (~1525 satır)

**Görünümler (Views):**
- TradingView (varsayılan) - Ana dashboard
- AnalysisView - Detaylı teknik analiz
- SignalsView - Sinyal geçmişi ve performans

**Panel Düzeni (2 Sütunlu Grid):**
```
Sol Sütun:              Sağ Sütun:
- ClearTrendPanel       - MTFMatrixPanel
- PulseV3Panel          - SMCPanel
- PulseMLPanel          - RiskRewardPanel
- PulsePanel            - PatternEngineV2
- EmelPanel             - SentimentPanel
- EmelInversePanel      - COMEX News
- ClaudeAnalysisPanel   - WhaleTrackerPanel
- NewsPanel             - CandlestickPatternPanel
- LearningDashboardV2   - StrategyPerformancePanel
- COTWhalePanel         - SeasonalityPanel
                        - MetaEnginePanel
                        - PermutationPanel
```

### 9.2 Panel Bileşenleri (28 Adet)

| Panel | Dosya | Açıklama |
|-------|-------|----------|
| EmelPanel | panels/EmelPanel.tsx | 10 kontrol noktalı analiz (2026-07-01: Makro Uyum eklendi) |
| PulsePanel | panels/PulsePanel.tsx | PULSE 1 (Algo) |
| PulseMLPanel | panels/PulseMLPanel.tsx | PULSE 2 (ML+TA) |
| PulseV3Panel | panels/PulseV3Panel.tsx | PULSE 3 (Hybrid MTF) |
| MLPredictionPanel | MLPredictionPanel.tsx | ML tahmin paneli |
| MetaEnginePanel | panels/MetaEnginePanel.tsx | Meta-Intelligence |
| MTFMatrixPanel | panels/MTFMatrixPanel.tsx | Çoklu zaman dilimi matrisi |
| SMCPanel | panels/SMCPanel.tsx | Smart Money Concepts |
| OrderBlockPanelUnified | OrderBlockPanelUnified.tsx | Order Block analizi |
| LearningDashboardV2 | panels/LearningDashboardV2.tsx | Sinyal performansı |
| WhaleTrackerPanel | WhaleTrackerPanel.tsx | COT/Whale takibi |
| StrategyOptimizerPanel | panels/StrategyOptimizerPanel.tsx | Strateji optimizasyonu |
| PermutationPanel | panels/PermutationPanel.tsx | Kombinasyon analizi |
| HarmonicVisualizerPanel | panels/HarmonicVisualizerPanel.tsx | Harmonik pattern'ler |
| OilBalticPanel | panels/OilBalticPanel.tsx | Petrol/Baltic intel |

### 9.3 State Management

```typescript
// Zustand Stores:
- useDashboardStore      // Dashboard durumu
- useDetailPanelStore    // Detay panel durumu
- useAuthStore          // Kimlik doğrulama
- useI18nStore          // Çoklu dil
- useNavigationStore    // Navigasyon

// React Query:
- useLivePrices()       // Canlı fiyatlar
- useCachedDashboardData() // Önbellekli veri
- useMTFAnalysis()      // MTF analizi
- useWebSocket()        // WebSocket bağlantısı
```

---

## 10. ARKAPLAN SERVİSLERİ (BACKGROUND SERVICES)

### 10.1 Lifespan Servisleri

**Dosya:** `backend/main.py` - `lifespan()` fonksiyonu

Başlangıç sırası:
```python
1. Redis (opsiyonel)
2. DataHub başlat
3. Candle event handler'ları kaydet
4. MT5 Redis listener (opsiyonel)
5. Pulse/EMEL scheduler (15dk)
6. Lifecycle checker (2dk)
7. Meta-Intelligence Engine (60sn)
8. Background scheduler
9. Oil Baltic sync (3600sn)
10. AIS oil collector (opsiyonel)
```

### 10.2 Zamanlayıcılar (Schedulers)

#### background_scheduler.py
```python
# Çalışma döngüsü:
- run_update_cycle(): Her 60 saniye
  - DataHub'dan veri çek
  - WebSocket broadcast
  - Redis cache
  - Supabase kaydet
```

#### Signal Lifecycle Loop
```python
async def lifecycle_loop():
    while True:
        await check_lifecycle_if_needed()  # Aktif sinyalleri kontrol et
        await asyncio.sleep(120)  # 2 dakika
```

#### Meta-Engine Loop
```python
async def meta_engine_loop():
    await asyncio.sleep(15)  # Başlangıç gecikmesi
    while True:
        for sym in SUPPORTED_SYMBOLS:
            await get_meta_signal(sym)  # Sinyal üret ve logla
        await asyncio.sleep(60)  # 60 saniye
```

### 10.3 Candle Event Handler'ları

**Dosya:** `backend/services/candle_event_handlers.py`

```python
@on_candle_close("5m")
async def on_5m_close(symbol: str, timeframe: str):
    # Meta-Engine sinyal kontrolü
    # Signal Lifecycle otomatik check
    # WebSocket broadcast
```

---

## 11. GÜVENLİK ve ÜRETİM SERTLEŞTİRME

### 11.1 Signal Lifecycle Hardening

1. **parse_json_field() helper** - Supabase REST API'den gelen JSON'u normalize eder
2. **Structured error logging** - signal_id, symbol, model_type, direction loglanır
3. **LifecycleMetrics** - In-process sayaçlar (/api/signals/metrics)
4. **DB-level dedup** - Partial unique index ile aktif sinyal çakışması önlenir
5. **Concurrency safety** - asyncio.Lock() ile aynı process'te çakışma önlenir
6. **Scheduler resilience** - scheduler_state tablosu ile job takibi
7. **DataHub circuit breaker** - 5 ardışık hata sonrası sembol atlanır

### 11.2 Sinyal Doğrulama Katmanları

```python
# 1. DB-level CHECK constraint:
CHECK (model_type IN ('ml', 'pulse1', 'pulse2', 'pulse3', 'emel', 'hybrid', 'smc', 'meta'))

# 2. Code-level cooldown:
SIGNAL_COOLDOWN_MINUTES = 15

# 3. Confidence threshold:
MIN_CONFIDENCE_FOR_REVERSAL = 55

# 4. Price movement validation:
MIN_PRICE_CHANGE_PCT = 0.15
```

---

## 12. ÇEVRE DEĞİŞKENLERİ (ENVIRONMENT VARIABLES)

### Kritik (Uygulama çalışmadan önce gerekli)
| Değişken | Kaynak | Açıklama |
|----------|--------|----------|
| `SUPABASE_URL` | Supabase | Database URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase | Service role key |

### AI/ML Özellikleri (Graceful degradation)
| Değişken | Kaynak | Açıklama |
|----------|--------|----------|
| `DEEP_SEEKR1` | DeepSeek | Birincil AI analizi |
| `ANTHROPIC_API_KEY` | Anthropic | Claude (yedek) |
| `GROQ_API_KEY` | Groq | Groq LLM |
| `XAI_API_KEY` | xAI | xAI analizi |

### Opsiyonel Özellikler
| Değişken | Açıklama |
|----------|----------|
| `REDIS_URL` | WebSocket broadcast cache |
| `MARKET_DATA_SOURCE` | `mt5_redis` veya `hybrid` |
| `MT5_REDIS_TICK_CHANNEL` | MT5 tick kanalı (varsayılan: mt5:tick) |
| `MT5_REDIS_BAR_CHANNEL` | MT5 bar kanalı (varsayılan: mt5:bar) |
| `TELEGRAM_BOT_TOKEN` | Telegram bildirimleri |

### Order Block Konfigürasyonu
| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `OB_FRACTAL_PERIOD` | 2 | Fractal periyodu |
| `OB_MIN_DISPLACEMENT_ATR` | 1.0 | Min displacement (ATR çarpanı) |
| `OB_MIN_SCORE` | 50.0 | Min OB skoru |
| `OB_ZONE_TYPE` | wick | Zone hesaplama tipi |
| `OB_MAX_TESTS` | 2 | Max test sayısı |

---

## 13. KOD STİLİ ve STANDARTLAR

### Python (Backend)
- PEP 8 kuralları
- Type hints kullanımı
- Async/await I/O operasyonları için
- Pydantic modeller request/response validasyonu
- `logging` modülü ile loglama (print değil)
- Import sırası: stdlib → third-party → local

### TypeScript (Frontend)
- **Strict mode KAPALI** (`"strict": false` tsconfig.json'da)
- Path alias: `@/*` → `./*`
- Functional components + hooks
- Zustand global state için
- React Query server state için
- `"use client"` direktifi client bileşenleri için

---

## 14. YAPIM ve ÇALIŞTIRMA KOMUTLARI

### Backend
```bash
# Geliştirme (auto-reload ile)
uvicorn backend.main:app --reload

# Üretim
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app
```

### Frontend
```bash
cd frontend

# Geliştirme
npm run dev

# Üretim build
npm run build

# Test
npm run test

# TypeScript kontrolü (Railway deploy öncesi ZORUNLU)
npx tsc --noEmit
```

---

## 15. ÖNEMLİ NOTLAR ve SINIRLILIKLAR

### XAUUSD Intraday Verisi
- MT5/yfinance XAUUSD.FOREX için sadece `1m` interval destekler
- 5m ve 1h boş array döndürür
- Çözüm: 1m'den 5m'ye resample, sonra türet

### MT5/yfinance WebSocket
- Kullanıcının API tier'ı forex/indices WebSocket'ine izin vermiyor
- ETF proxy'ler yanlış fiyat gösteriyor
- Çözüm: DataHub 5s REST polling kullanılıyor

### DataHub Persist Cache
- Supabase `candle_cache` ve `candle_cache_meta` tabloları
- 15 dakikada bir persist (throttled)
- Restart sonrası 0 API çağrısı ile warm start

### Model Aile Paylaşımı
- NASDAQ modeli: NDX.INDX + GDAXI.INDX
- XAUUSD modeli: XAUUSD + USOIL.FOREX
- Sembol bazlı özelleştirme feature engineering'de yapılır

---

## 16. ÖZET ve BAĞLANTILAR

### Temel Dosyalar
| Dosya | Satır | Açıklama |
|-------|-------|----------|
| `backend/main.py` | ~890 | App entry point |
| `backend/services/data_hub.py` | ~1458 | Merkezi veri yönetimi |
| `backend/services/ml_prediction_service.py` | ~2568 | ML pipeline |
| `backend/services/signal_lifecycle.py` | ~1687 | Sinyal yaşam döngüsü |
| `backend/services/meta_analysis_engine.py` | ~1053 | Meta-Intelligence |
| `backend/routers/emel_pulse.py` | ~2955 | PULSE + EMEL |
| `backend/services/order_block_service.py` | ~43824 | SMC/Order Blocks |
| `frontend/app/page.tsx` | ~1525 | Ana dashboard |

### Önemli Servisler
- **DataHub:** Tüm piyasa verisinin merkezi kaynağı
- **ML Prediction:** LightGBM tabanlı tahminler
- **Signal Lifecycle:** TP/SL izleme ve sinyal yönetimi
- **Meta-Engine:** 6 model kombinasyonu ve ağırlıklı karar
- **Market Regime:** ADX bazlı piyasa rejimi tespiti

### Veritabanı Tabloları
- **prediction_logs:** Tüm sinyaller
- **signal_checks:** Yaşam döngüsü anlık görüntüleri
- **outcome_results:** Sonuç takibi
- **meta_combination_stats:** Kombinasyon performansı
- **candle_cache:** Kalıcı OHLCV verisi

---

**Hazırlayan:** Cascade AI  
**Tarih:** 14 Nisan 2026  
**Proje:** ForexSAI Trading Portal  
**Versiyon:** v2026.04.14
