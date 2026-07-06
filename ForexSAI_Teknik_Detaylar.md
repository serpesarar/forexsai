# ForexSAI - Detaylı Teknik Özellikler

> Bu doküman, meta-engine entegrasyonu için gerekli teknik detayları içerir.
> **Son Güncelleme:** 2026-07-01 — Gösterge Denetimi değişiklikleri işlendi
> (merkezi kapılar `signal_gates.py`, pulse1 Stoch→H4, PULSE 3 rejim ağırlıkları,
> endeks ATR TP/SL, EMEL 10. kontrol). Detay: `UYGULAMA_NOTLARI_2026-07-01.md`

---

## 1. VERİ ERİŞİMİ

### 1.1 prediction_logs Tablo Şeması

```sql
CREATE TABLE prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Temel bilgiler
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(16) DEFAULT '1d',
    
    -- ML Model çıktıları
    ml_direction VARCHAR(8) NOT NULL,  -- BUY, SELL, HOLD
    ml_confidence REAL NOT NULL,       -- 0-100 arası (yüzde)
    ml_probability_up REAL,
    ml_probability_down REAL,
    ml_target_price REAL,
    ml_stop_price REAL,
    ml_entry_price REAL,
    
    -- Claude çıktıları (opsiyonel)
    claude_direction VARCHAR(8),
    claude_confidence REAL,
    claude_model VARCHAR(64),
    
    -- Analizde kullanılan faktörler (JSONB)
    factors JSONB NOT NULL DEFAULT '{}',
    -- Örnek: {"rsi_14": 65.2, "ema20_distance_pct": 1.27, "volume_ratio": 0.08}
    
    -- Strateji adı
    strategy VARCHAR(32),  -- EMEL, PULSE, PULSE_V3, balanced, smc
    
    -- Takip durumu
    outcome_checked BOOLEAN DEFAULT FALSE
);
```

**Önemli Index'ler:**
- `idx_prediction_logs_symbol` - Sembol bazlı sorgular
- `idx_prediction_logs_created_at` - Tarih sıralaması
- `idx_prediction_logs_outcome_checked` - Açık sinyaller

### 1.2 TP/SL Hit Verileri Nerede?

**Ana Tablo:** `prediction_logs` (sinyal kaydı)

**Lifecycle Takip:** `signal_checks` tablosu (her 3dk'da bir ping):
```sql
CREATE TABLE signal_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES prediction_logs(id),
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    current_price REAL,
    highest_profit_pips REAL,    -- Peak excursion
    lowest_drawdown_pips REAL,   -- Max drawdown
    targets_hit TEXT[],          -- ['TP1', 'TP2'] vs
    status VARCHAR(16)           -- active, completed, stopped, expired
);
```

**Sonuç Tablosu:** `outcome_results` (1h/4h/24h/48h/7d sonrası kontrol):
```sql
CREATE TABLE outcome_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES prediction_logs(id),
    check_interval VARCHAR(16),  -- '1h', '4h', '24h'
    entry_price REAL,
    exit_price REAL,
    high_price REAL,       -- Tahmin sonrası max
    low_price REAL,        -- Tahmin sonrası min
    hit_target BOOLEAN,
    hit_stop BOOLEAN,
    ml_correct BOOLEAN,    -- Tahmin doğru muydu?
    price_change_pct REAL
);
```

**Query Örneği (Son sinyaller ve durumları):**
```sql
SELECT 
    p.symbol,
    p.ml_direction,
    p.ml_confidence,
    p.created_at,
    sc.status,
    sc.targets_hit,
    sc.lowest_drawdown_pips
FROM prediction_logs p
LEFT JOIN signal_checks sc ON sc.prediction_id = p.id
WHERE p.symbol = 'NDX.INDX'
  AND p.created_at > NOW() - INTERVAL '24 hours'
ORDER BY p.created_at DESC;
```

---

## 2. MODEL ÇIKTILARI

### 2.1 API Endpoint'ler ve Dönüş Formatları

#### ML Prediction API
```
GET /api/ml/predict/{symbol}?scope=balanced
```

**Response (PredictionResult dataclass):**
```json
{
  "symbol": "NDX.INDX",
  "direction": "BUY",
  "confidence": 68.5,           // 0-100 arası
  "probability_up": 0.685,
  "probability_down": 0.315,
  
  "target_pips": 15.0,
  "stop_pips": 50.0,
  "risk_reward": 0.3,
  
  "entry_price": 25000.50,
  "target_price": 25015.50,
  "stop_price": 24950.50,
  
  "technical_score": 0.72,
  "momentum_score": 0.65,
  "trend_score": 0.80,
  "volatility_regime": "NORMAL",
  
  "reasoning": ["EMA20 > EMA50", "RSI 62", "ADX 28 güçlü trend"],
  "key_levels": [
    {"type": "support", "price": 24950, "strength": 0.85}
  ],
  
  "timestamp": "2026-03-27T12:00:00Z",
  "model_version": "lgbm_nasdaq_v2"
}
```

#### PULSE 1 API (Algo)
```
GET /api/panel/pulse/{symbol}
```

**Response (PulseResponse):**
```json
{
  "symbol": "NDX.INDX",
  "signal": "BUY",
  "signal_type": "CONFIRM",     // SCOUT, CONFIRM, HOLD
  "pulse_score": 72.0,          // 0-100 arası
  
  "trend": {
    "direction": "up",
    "strength": 0.85,
    "last_5_candles": ["up", "up", "down", "up", "up"]
  },
  
  "price": {
    "current": 25000.50,
    "change_5": 0.12
  },
  
  "levels": {
    "r1": 25050.0,
    "pivot": 25000.0,
    "s1": 24950.0,
    "target": 25020.0,
    "stop": 24988.0
  },
  
  "momentum": {
    "rsi": {"value": 62.0, "trend": "rising"},
    "macd": {"value": 12.5, "trend": "bullish"},
    "stochastic": {"value": 68.0, "trend": "rising"}
  },
  
  "regime": {
    "type": "STRONG_TREND_UP",
    "adx": 32.5,
    "session": "newyork",
    "allowed_directions": ["BUY", "HOLD"],
    "min_rr": 1.3
  },
  
  "score_breakdown": {
    "candles": 20,
    "ema_stack": 25,
    "rsi": 20,
    "macd": 15,
    "volume": 10,
    "stochastic": 0,
    "h4_alignment": 10
  }
  // 2026-07-01: Stochastic skor dışı (display_only:true, RSI ile mükerrerdi);
  // 10 puan yeni h4_alignment bileşenine taşındı (H4 close vs EMA20 uyumu)
}
```

#### PULSE 2 API (ML+TA)
```
GET /api/panel/pulse-ml/{symbol}
```

**Response (PulseMLResponse):**
```json
{
  "symbol": "NDX.INDX",
  "signal": "BUY",
  "signal_type": "CONFIRM",
  "pulse_score": 68.0,
  "confidence": 68.0,
  "model_type": "PULSE_ML_HYBRID",
  
  "score_breakdown": {
    "ml": {"pts": 35, "confidence": 52.0, "direction": "BUY"},
    "ema": {"pts": 25, "status": "above", "ema20": 24980.0, "ema50": 24950.0},
    "macd": {"pts": 15, "hist": 12.5},
    "rsi": {"pts": 10, "value": 58.0},
    "volume": {"pts": 10}
  },
  
  "details": {
    "ml_direction": "BUY",
    "ema_20": 24980.0,
    "ema_50": 24950.0,
    "rsi_14": 58.0,
    "macd_hist": 12.5,
    "notes": ["ML + EMA onaylı", "RSI nötr bölge"]
  },
  
  "target": 25015.0,
  "stop": 24950.0,
  "rr_ratio": 1.23
}
```

#### PULSE 3 API (Multi-Timeframe)
```
GET /api/panel/pulse-v3/{symbol}
```

**Response (PulseV3Response):**
```json
{
  "symbol": "NDX.INDX",
  "pulse_score": 78,            // 0-100 (5m+1H+4H ağırlıklı)
  "signal_type": "CONFIRM",
  "direction": "BUY",
  "confidence": 78.0,
  
  "timeframes": {
    "5m": {"raw_score": 45, "max": 50, "trend": "up", "details": {...}},
    "1h": {"raw_score": 25, "max": 30, "trend": "up", "details": {...}},
    "4h": {"raw_score": 18, "max": 20, "trend": "up", "details": {...}}
  },
  
  "entry_zones": [
    {"price": 25000.50, "share": 40, "label": "Instant"},
    {"price": 24995.50, "share": 30, "label": "On Dip"},
    {"price": 24990.50, "share": 30, "label": "Support"}
  ],
  
  "order_blocks": [
    {"type": "bullish", "low": 24980, "high": 25000, "strength": 0.85, "is_nearby": true}
  ],
  
  "levels": {
    "r2": 25050, "r1": 25025, "pivot": 25000,
    "s1": 24975, "s2": 24950,
    "target": 25020, "stop": 24988
  },
  
  "rr_ratio": 1.67
}
```

#### EMEL API (10-Check — 2026-07-01: Makro Uyum eklendi)
```
GET /api/panel/emel/{symbol}
```

**Response (EMELResponse):**
```json
{
  "symbol": "NDX.INDX",
  "signal": "BUY",
  "signal_type": "CONFIRM",     // STRONG_BUY, BUY, SELL, STRONG_SELL, HOLD
  "confidence": 72.0,
  "final_score": 72,            // 0-100 arası
  
  "checks": [
    {
      "id": 1,
      "name": "Trend Analizi",
      "subtitle": "EMA 20/50/200",
      "status": "pass",           // pass, warning, fail
      "direction": "up",
      "color": "green",
      "label": "YUKARI YÖN",
      "details": {"ema20": 24980, "ema50": 24950, "ema200": 24800},
      "comment": "Kısa ve orta vadeli trend yukarı."
    },
    // ... 9 more checks (id:10 = "Makro Uyum" — DXY/US10Y emtia, VIX endeks)
  ],
  
  "confluence": {
    "green": 6,                   // 6/10 kontrol geçti
    "yellow": 2,
    "red": 1,
    "direction": "bullish"
  },
  
  "recommendation": {
    "action": "BUY",
    "entry": 25000.50,
    "target": 25050.00,
    "stop": 24950.00,
    "confidence": 72,
    "timeframe": "15m-1h"
  }
}
```

### 2.2 ML Confidence Değeri Formatı

**Önemli:** Confidence her zaman **0-100 arası yüzde** olarak döner.

```python
# ml_prediction_service.py
@dataclass
class PredictionResult:
    confidence: float  # 0-100 (yüzde)
    probability_up: float   # 0-1 (ondalık)
    probability_down: float # 0-1 (ondalık)
```

**Dönüşüm Mantığı:**
```python
# Model çıktısı: probability_up = 0.685
# Confidence: 0.685 * 100 = 68.5

# Katmanlı confidence uygulaması:
final_confidence = base_confidence * layer_multipliers  # 30-95 arası clamp
```

---

## 3. TEKNİK GÖSTERGELER

### 3.1 Hesaplanan İndikatörler

**Dosya:** `backend/services/ml_prediction_service.py` → `_compute_technical_indicators()`

| İndikatör | Periyot | Formül | Kullanım |
|-----------|---------|--------|----------|
| **EMA** | 5, 10, 20, 50, 200 | TradingView standard: `alpha = 2/(period+1)` | Trend yönü |
| **SMA** | 5, 10, 20, 50, 200 | Basit ortalama | PULSE 3 hızlı analiz |
| **RSI** | 7, 14 | Wilder smoothing | Momentum |
| **MACD** | 12, 26, 9 | EMA12 - EMA26 | Trend gücü |
| **ATR** | 14 | Average True Range | Volatilite, TP/SL |
| **ADX** | 14 | Wilder DMI | Trend gücü (Regime) |
| **Stochastic** | 14, 3 | %K = (C-L14)/(H14-L14)*100 | PULSE 1 görüntü (2026-07-01: skor dışı, yerine H4 uyumu) |
| **Bollinger** | 20, 2 | SMA ± 2σ | EMEL S/R |
| **Williams %R** | 14 | -100*(H14-C)/(H14-L14) | Aşırı alım/satım |
| **MFI** | 14 | Money Flow Index | Hacimli RSI |
| **Momentum** | 3, 10 | (C - C_n)/C_n * 100 | Kısa trend |

### 3.2 EMA Hesaplama (TradingView Uyumlu)

**DataHub'dan çekilmiyor** - Manuel hesaplanıyor:

```python
def _calc_ema(values, period):
    """TradingView ile aynı EMA hesabı."""
    if len(values) < period:
        return float(values[-1])
    
    alpha = 2.0 / (period + 1.0)
    
    # İlk değer = SMA
    ema = float(np.mean(values[:period]))
    
    # Sonraki değerler = EMA formülü
    for v in values[period:]:
        ema = alpha * float(v) + (1 - alpha) * ema
    
    return ema

# Kullanım:
ema_20 = _calc_ema(closes, 20)
ema_50 = _calc_ema(closes, 50)
ema_200 = _calc_ema(closes, 200)
```

**Önemli:** EMA değerleri her API çağrısında OHLCV verisinden **real-time hesaplanır**. DataHub sadece ham OHLCV sağlar.

---

## 4. RİSK PARAMETRELERİ

### 4.1 Sembol Başına TP/SL Mesafeleri

**Dosya:** `backend/services/target_config.py`

| Sembol | TP1 | TP2 | TP3 | TP4 | SL | Tip |
|--------|-----|-----|-----|-----|-----|-----|
| **NDX.INDX** | 15 | 25 | 35 | 50 | 50 | Pip/Point |
| **GDAXI.INDX** | 15 | 25 | 35 | 50 | 50 | Pip/Point |
| **XAUUSD** | 8 | 15 | 25 | 40 | 15 | $ (1 pip = $1) |
| **USOIL.FOREX** | 0.02% | 0.04% | 0.06% | 0.10% | 0.05% | Yüzde |

**Timeframe Genişletmesi:**
```python
# 15m üzeri timeframe'lerde +0.2% genişleme
steps = {
    "5m": 0.0, "15m": 0.0,
    "30m": 0.2, "1h": 0.4, "4h": 0.6, "1d": 0.8
}
```

### 4.2 Scalping TP/SL (PULSE modelleri için)

**Dosya:** `backend/routers/emel_pulse.py` → `_scalp_tp_sl()`

```python
SCALP_DISTANCES = {
    "NDX.INDX":    {"tp": 20, "sl": 12},    # points
    "XAUUSD":      {"tp": 7,  "sl": 4},    # dollars
    "GDAXI.INDX":  {"tp": 20, "sl": 12},   # points
    "USOIL.FOREX": {"tp": 0.50, "sl": 0.30} # dollars
}

# ── 2026-07-01: ENDEKSLER (GDAXI/NDX) için ATR-TABAN geometri ──
# Sabit mesafeler artık TABAN, ATR tavan belirler (PULSE_ATR_GEOMETRY=1):
#   tp_dist = max(fixed_tp, ATR × 1.5)
#   sl_dist = max(fixed_sl, ATR × 1.0)   → RR ≥ 1.5 garanti
# Gerekçe: GDAXI'de TP20/SL12 5m gürültüsünün içindeydi (stopped MFE 7p vs SL 65p).
# Emtialar (XAUUSD/USOIL) eski davranışta kalır:
atr_tp = atr_val * 1.0
atr_sl = atr_val * 0.6
tp_dist = min(tp_dist, max(atr_tp, tp_dist * 0.3))  # Min %30 sabit
sl_dist = min(sl_dist, max(atr_sl, sl_dist * 0.3))
```

**Sonuç:** Hybrid sistem - **Fixed pip + ATR sınırlandırması**

### 4.3 Portföy Risk Limitleri (EMEL)

```python
# Günlük maksimum risk: %3
# Anlık açık risk: %1.5

# EMEL Check #9:
if anlik_risk > 3.0:
    return "OVERRIDE"  # Sinyal bloklu
elif anlik_risk > 1.5:
    return "DİKKAT"    # Sarı uyarı
else:
    return "UYGUN"     # Yeşil
```

---

## 5. META-ENGINE ENTEGRASYON TERCİHLERİ

### 5.1 Önerilen Mimari: FastAPI Entegre

```
┌─────────────────────────────────────────┐
│  Mevcut FastAPI Backend               │
│  ├─ /api/panel/* (mevcut)              │
│  ├─ /api/ml/* (mevcut)                 │
│  └─ /api/meta/* (YENİ)                 │
│      ├─ /ensemble (tüm modeller)       │
│      ├─ /vote (oylama)                 │
│      └─ /meta-signal (birleştirilmiş)  │
└─────────────────────────────────────────┘
```

**Neden FastAPI Entegre?**
- Aynı veri erişimi (prediction_logs, DataHub)
- Aynı Python ortamı (pandas, numpy, scikit-learn)
- Aynı cache/Redis erişimi
- Daha düşük latency (ekstra HTTP hop yok)
- Kolay test/debug

### 5.2 Önerilen Çalışma Modu: Poll-Based

```
Zamanlayıcı: Her 1 dakikada bir (veya 30sn)
├── Tüm semboller için: [NDX.INDX, XAUUSD, GDAXI.INDX, USOIL.FOREX]
├── Her sembol için:
│   ├── Tüm modelleri çağır (parallel)
│   ├── Meta-engine ensemble hesapla
│   └── Sonucu Redis'e yaz + WebSocket broadcast
└── Dinleyiciler: Frontend WebSocket subscriber
```

**Neden Poll-Based?**
- Daha basit implementasyon
- Hata durumunda retry kolay
- Model cache ile zaten hızlı (60sn TTL)
- Regime detection 30dk cache - çok sık çağrıya gerek yok

**Alternatif WebSocket:**
```python
# Eğer sub-saniye latency gerekirse:
# WebSocket üzerinden stream (zaten mevcut altyapı var)
# /ws/all endpoint'i mevcut
```

### 5.3 Meta-Engine Input/Output Önerisi

**Input:**
```json
{
  "symbol": "NDX.INDX",
  "timeframe": "15m",
  "models": ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"],
  "weights": {              // Opsiyonel, override
    "ml": 0.30,
    "pulse1": 0.15,
    "pulse2": 0.20,
    "pulse3": 0.15,
    "emel": 0.15,
    "smc": 0.05
  },
  "min_agreement": 0.60,    // %60 model uyumu gerekli
  "confidence_threshold": 55  // Min confidence
}
```

**Output:**
```json
{
  "symbol": "NDX.INDX",
  "meta_signal": "BUY",     // BUY, SELL, HOLD
  "meta_confidence": 72.5,   // Ağırlıklı ortalama
  "agreement_ratio": 0.83,   // 5/6 model aynı yönde
  
  "model_votes": {
    "ml": {"direction": "BUY", "confidence": 68, "raw": {...}},
    "pulse1": {"direction": "HOLD", "confidence": 35, "raw": {...}},
    "pulse2": {"direction": "BUY", "confidence": 72, "raw": {...}},
    "pulse3": {"direction": "BUY", "confidence": 78, "raw": {...}},
    "emel": {"direction": "BUY", "confidence": 70, "raw": {...}},
    "smc": {"direction": "NEUTRAL", "confidence": 50, "raw": {...}}
  },
  
  "divergence_warning": false,  // Modeller çelişkili mi?
  "recommended_action": "SCALP_BUY",  // Sinyal tipi
  
  "risk_params": {
    "suggested_tp": 25020,
    "suggested_sl": 24950,
    "position_size_pct": 2.0  // Portföy % kaç
  }
}
```

---

## 6. ÖZET - KRİTİK BİLGİLER

| Konu | Detay |
|------|-------|
| **Confidence Formatı** | 0-100 yüzde (probability_up/down = 0-1) |
| **EMA Hesaplama** | Manuel, TradingView formülü (alpha = 2/(period+1)) |
| **TP/SL Sistemi** | Fixed pip + ATR clamping hybrid |
| **Cache Stratejisi** | Redis 60sn (panel), 30sn (5m), 30dk (regime) |
| **Veri Kaynağı** | MT5 bridge + yfinance → DataHub (30sn polling) |
| **Sinyal Ömrü** | 15 dakika (lifecycle), 30dk cooldown |
| **En Çok Kullanılan Kolonlar** | symbol, ml_direction, ml_confidence, created_at, status |
