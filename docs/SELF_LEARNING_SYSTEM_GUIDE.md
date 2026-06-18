# 🧠 Self-Learning Trading System - Kullanım Kılavuzu

## 📅 Son Güncelleme: Ocak 2026

---

## 🎯 Sistem Genel Bakış

Bu sistem, yapay zeka destekli bir trading sinyal sistemidir. İki ana bileşenden oluşur:

1. **ML Model (LightGBM)** - Teknik analiz verilerine dayalı tahmin
2. **Claude AI** - Hata analizi ve öğrenme feedback'i

### Sistem Akışı

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SELF-LEARNING SİSTEMİ                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   📊 ML MODEL (.pkl)              🧠 CLAUDE AI                          │
│   ┌──────────────┐               ┌──────────────┐                       │
│   │ LightGBM     │               │ Error        │                       │
│   │ Prediction   │◄──────────────│ Analysis     │                       │
│   │ Engine       │  (feedback)   │ Engine       │                       │
│   └──────────────┘               └──────────────┘                       │
│         │                              ▲                                │
│         │ Tahmin                       │ Hata                           │
│         ▼                              │                                │
│   ┌──────────────┐               ┌──────────────┐                       │
│   │ Prediction   │──────────────►│ Outcome      │                       │
│   │ Logs DB      │   sonuç       │ Results DB   │                       │
│   └──────────────┘               └──────────────┘                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Dosya Yapısı

```
backend/
├── services/
│   ├── ml_prediction_service.py      # ML tahmin servisi
│   ├── outcome_tracker.py            # Sonuç takip servisi
│   ├── error_analysis_service.py     # Hata analiz servisi (Claude)
│   ├── prediction_logger.py          # Tahmin kayıt servisi
│   ├── learning_analyzer.py          # Öğrenme analiz servisi
│   ├── background_scheduler.py       # Arka plan görevleri
│   └── target_config.py              # Hedef/pip konfigürasyonu
├── routers/
│   └── learning.py                   # Learning API endpoint'leri
├── database/
│   └── schema.sql                    # Veritabanı şeması
└── models/
    ├── lgbm_nasdaq_v2.pkl            # NASDAQ ML modeli
    └── lgbm_xauusd_v2.pkl            # XAUUSD ML modeli
```

---

## 🗄️ Veritabanı Tabloları

### 1. prediction_logs
Yapılan tüm tahminleri kaydeder.

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| symbol | VARCHAR | Sembol (NDX.INDX, XAUUSD) |
| ml_direction | VARCHAR | BUY, SELL, HOLD |
| ml_confidence | REAL | Güven yüzdesi (0-100) |
| ml_entry_price | REAL | Giriş fiyatı |
| ml_target_price | REAL | Hedef fiyat |
| ml_stop_price | REAL | Stop fiyatı |
| factors | JSONB | RSI, MACD, trend vs. |
| outcome_checked | BOOLEAN | Sonuç kontrol edildi mi? |

### 2. outcome_results
Tahminlerin sonuçlarını kaydeder.

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| prediction_id | UUID | Tahmin referansı |
| check_interval | VARCHAR | 1h, 4h, 24h |
| entry_price | REAL | Giriş fiyatı |
| exit_price | REAL | Çıkış fiyatı |
| high_price | REAL | O süredeki en yüksek |
| low_price | REAL | O süredeki en düşük |
| hit_target | BOOLEAN | Hedef ulaşıldı mı? |
| hit_stop | BOOLEAN | Stop tetiklendi mi? |
| ml_correct | BOOLEAN | Tahmin doğru muydu? |

### 3. error_analysis
Başarısız tahminlerin Claude analizi.

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| prediction_id | UUID | Tahmin referansı |
| error_type | VARCHAR | stoploss_hit, wrong_direction |
| is_fake_move | BOOLEAN | Fake pump/dump muydu? |
| fake_move_type | VARCHAR | fake_pump, stop_hunt vs. |
| ai_analysis | JSONB | Claude'un detaylı analizi |
| lesson_learned | TEXT | Öğrenilen ders |

### 4. candle_snapshots
Tahmin anındaki mum verileri.

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| prediction_id | UUID | Tahmin referansı |
| candles | JSONB | 100 mum verisi (OHLC) |
| indicators | JSONB | RSI, MACD vs. |
| levels | JSONB | Support/resistance |

### 5. learning_feedback
Öğrenilen kurallar (confidence ayarı için).

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| symbol | VARCHAR | Sembol |
| feedback_type | VARCHAR | avoid_condition, boost_condition |
| condition | JSONB | Koşul: {"rsi_above": 70} |
| action | JSONB | Aksiyon: {"reduce_confidence": 30} |
| is_active | BOOLEAN | Aktif mi? |

---

## 🔌 API Endpoint'leri

### Tahmin ve Sonuç Takibi

```bash
# Son tahminleri listele
GET /api/learning/predictions?symbol=NDX.INDX&limit=20

# Doğruluk özeti
GET /api/learning/accuracy-summary?symbol=NDX.INDX&days=7

# Hedef bazlı doğruluk (1h interval)
GET /api/learning/multi-target-accuracy?symbol=NDX.INDX&check_interval=1h

# Hedef bazlı doğruluk (24h interval)
GET /api/learning/multi-target-accuracy?symbol=NDX.INDX&check_interval=24h
```

### Self-Learning Sistemi

```bash
# Sistem durumu
GET /api/learning/self-learning-status

# Hata analizleri
GET /api/learning/error-analyses?symbol=NDX.INDX&limit=20

# Aktif feedback kuralları
GET /api/learning/learning-feedback?active_only=true

# Manuel hata analizi tetikle
POST /api/learning/trigger-error-analysis?hours_ago=4&limit=5
```

### Dashboard

```bash
# Tam dashboard verisi
GET /api/learning/dashboard?symbol=NDX.INDX&days=7
```

---

## ⏰ Otomatik Arka Plan Görevleri

| Görev | Sıklık | Açıklama |
|-------|--------|----------|
| **Data Update** | 5 saniye | Fiyat ve TA verilerini günceller |
| **Outcome Check** | 5 dakika | Tahminlerin sonuçlarını kontrol eder |
| **Error Analysis** | 1 saat | Başarısız tahminleri Claude ile analiz eder |
| **News Update** | 5 dakika | Haber verilerini günceller |

---

## 🔄 Öğrenme Mekanizmaları

### 1. Soft Learning (Aktif)
ML modelini değiştirmeden confidence ayarı yapar.

```
HATA OLDU → Claude Analiz → Feedback Kaydedildi
                                   │
                                   ▼
                         Sonraki tahminlerde:
                         ML: %75 BUY
                         Feedback: -%30 (RSI yüksek)
                         SONUÇ: %45 BUY
```

**Örnek Feedback Kuralları:**
- RSI > 70 + BUY → Confidence -%30
- RSI < 30 + SELL → Confidence -%30
- Against Trend → Confidence -%25
- Low Volume → Confidence -%15

### 2. Hard Learning (Gelecekte)
ML modelini yeniden eğitir.

```bash
# Manuel çalıştırılır
python scripts/retrain_model.py --symbol NDX.INDX --min_samples 200
```

---

## 🧠 Claude Hata Analizi Detayları

### Analiz Süreci

1. **Başarısız tahmin tespit edilir** (stoploss, wrong direction)
2. **Veriler toplanır:**
   - Tahmin anındaki 100 mum
   - Sonraki 20 mum
   - Teknik göstergeler
   - Fiyat hareketleri (high/low)
3. **Fake move tespiti yapılır:**
   - fake_pump: Fiyat yukarı gidip geri döndü
   - fake_dump: Fiyat aşağı gidip geri döndü
   - stop_hunt: Stop seviyelerine dokunup döndü
   - liquidity_grab: Likidite toplama hareketi
4. **Claude'a gönderilir**
5. **Analiz sonucu kaydedilir:**
   - root_cause: Hatanın kök nedeni
   - missed_signals: Gözden kaçan sinyaller
   - lesson_learned: Öğrenilen ders

### Root Cause Tipleri

| Tip | Açıklama |
|-----|----------|
| overbought_buy | RSI yüksekken BUY |
| oversold_sell | RSI düşükken SELL |
| against_trend | Trende karşı işlem |
| divergence_ignored | Diverjans göz ardı edildi |
| fake_move | Sahte hareket |
| low_volume | Düşük hacim onayı |
| bad_timing | Kötü zamanlama |

---

## 📊 Hedef Konfigürasyonu

### NASDAQ (NDX.INDX)
```python
pip_value = 1.0  # 1 index point = 1 pip
targets:
  - TP1: 20 pips
  - TP2: 30 pips
  - TP3: 50 pips
stoploss: 50 pips
```

### Altın (XAUUSD)
```python
pip_value = 0.1  # $0.10 = 1 pip
targets:
  - TP1: 5 pips ($0.50)
  - TP2: 10 pips ($1.00)
  - TP3: 20 pips ($2.00)
stoploss: 10 pips
```

---

## 🛠️ Supabase Migration SQL

Yeni kurulum veya güncelleme için çalıştırılması gereken SQL:

```sql
-- 1) outcome_results tablosuna high/low sütunları ekle
ALTER TABLE outcome_results 
ADD COLUMN IF NOT EXISTS high_price REAL,
ADD COLUMN IF NOT EXISTS low_price REAL;

-- 2) ERROR ANALYSIS tablosu
CREATE TABLE IF NOT EXISTS error_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    outcome_id UUID REFERENCES outcome_results(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    error_type VARCHAR(32) NOT NULL,
    prediction_direction VARCHAR(8) NOT NULL,
    confidence_pct REAL,
    entry_price REAL NOT NULL,
    target_price REAL,
    stop_price REAL,
    actual_high REAL,
    actual_low REAL,
    exit_price REAL,
    pips_against REAL,
    pips_favor REAL,
    is_fake_move BOOLEAN DEFAULT FALSE,
    fake_move_type VARCHAR(32),
    analysis_status VARCHAR(16) DEFAULT 'pending',
    ai_analysis JSONB,
    lesson_learned TEXT,
    improvement_suggestion TEXT,
    applied_to_model BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_error_type CHECK (error_type IN ('stoploss_hit', 'wrong_direction', 'missed_target', 'early_exit'))
);

CREATE INDEX idx_error_analysis_prediction_id ON error_analysis(prediction_id);
CREATE INDEX idx_error_analysis_status ON error_analysis(analysis_status);
CREATE INDEX idx_error_analysis_error_type ON error_analysis(error_type);

-- 3) CANDLE SNAPSHOTS tablosu
CREATE TABLE IF NOT EXISTS candle_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,
    snapshot_type VARCHAR(16) NOT NULL,
    candles JSONB NOT NULL,
    indicators JSONB,
    levels JSONB,
    candle_count INT NOT NULL
);

CREATE INDEX idx_candle_snapshots_prediction_id ON candle_snapshots(prediction_id);
CREATE INDEX idx_candle_snapshots_type ON candle_snapshots(snapshot_type);

-- 4) LEARNING FEEDBACK tablosu
CREATE TABLE IF NOT EXISTS learning_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol VARCHAR(32),
    feedback_type VARCHAR(32) NOT NULL,
    condition JSONB NOT NULL,
    action JSONB NOT NULL,
    source_error_ids UUID[],
    strength REAL DEFAULT 0.5,
    sample_count INT DEFAULT 1,
    success_rate REAL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    CONSTRAINT valid_feedback_type CHECK (feedback_type IN ('avoid_condition', 'boost_condition', 'pattern_warning', 'timing_adjustment'))
);

CREATE INDEX idx_learning_feedback_symbol ON learning_feedback(symbol);
CREATE INDEX idx_learning_feedback_active ON learning_feedback(is_active) WHERE is_active = TRUE;
```

---

## 📈 Performans Metrikleri

### Self-Learning Status Endpoint Yanıtı

```json
{
  "system_active": true,
  "total_predictions": 150,
  "total_outcomes": 120,
  "total_error_analyses": 45,
  "active_feedback_rules": 8,
  "recent_error_distribution": {
    "stoploss_hit": 25,
    "wrong_direction": 15,
    "missed_target": 5
  },
  "fake_move_rate": 0.35,
  "learning_coverage": 37.5
}
```

### Metrik Açıklamaları

| Metrik | Açıklama |
|--------|----------|
| total_predictions | Toplam tahmin sayısı |
| total_outcomes | Sonucu kontrol edilen tahmin sayısı |
| total_error_analyses | Claude ile analiz edilen hata sayısı |
| active_feedback_rules | Aktif öğrenme kuralı sayısı |
| fake_move_rate | Son 50 hatanın kaçı fake move? |
| learning_coverage | Hataların yüzde kaçı analiz edildi? |

---

## 🚀 Gelecek Geliştirmeler

1. **Model Retraining Script** - Otomatik model güncelleme
2. **A/B Testing** - Farklı feedback kurallarını karşılaştırma
3. **Pattern Recognition** - Tekrarlayan hata pattern'leri tespit
4. **Real-time Alerts** - Yanlış sinyal uyarıları
5. **Performance Dashboard** - Frontend'de görsel takip

---

## 📞 Troubleshooting

### Hata: "Database not available"
- Supabase bağlantısını kontrol et
- `.env` dosyasında `SUPABASE_URL` ve `SUPABASE_KEY` var mı?

### Hata: "No candle data"
- MT5 bridge + yfinance key'i kontrol et
- Sembol formatını kontrol et (NDX.INDX)

### Hata: "Claude analysis failed"
- Anthropic API key'i kontrol et
- Rate limit'e takılmış olabilir

### Outcome'lar güncellenmiyor
- Background scheduler çalışıyor mu?
- `GET /api/data/scheduler-status` ile kontrol et

---

**Bu doküman, trading panel projesinin self-learning sistemini açıklar.**
