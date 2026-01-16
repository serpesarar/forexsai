-- ============================================================
-- SELF-IMPROVING TRADING AI - DATABASE SCHEMA
-- Supabase (PostgreSQL) için tasarlandı
-- ============================================================

-- 1) PREDICTION LOGS
-- Her ML + Claude analizi yapıldığında buraya kayıt atılır
CREATE TABLE IF NOT EXISTS prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Temel bilgiler
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(16) DEFAULT '1d',
    
    -- ML Model çıktıları
    ml_direction VARCHAR(8) NOT NULL,  -- BUY, SELL, HOLD
    ml_confidence REAL NOT NULL,
    ml_probability_up REAL,
    ml_probability_down REAL,
    ml_target_price REAL,
    ml_stop_price REAL,
    ml_entry_price REAL,
    
    -- Claude çıktıları
    claude_direction VARCHAR(8),
    claude_confidence REAL,
    claude_model VARCHAR(64),
    
    -- Analizde kullanılan faktörler (JSON olarak saklayalım - esneklik için)
    factors JSONB NOT NULL DEFAULT '{}',
    -- Örnek: {
    --   "rsi_14": 65.2,
    --   "ema20_distance_pct": 1.27,
    --   "volume_ratio": 0.08,
    --   "vix": 15.1,
    --   "dxy": 99.13,
    --   "news_count": 3,
    --   "news_tone": "NEUTRAL",
    --   "trend": "BULLISH",
    --   "volatility": "LOW"
    -- }
    
    -- Takip durumu
    outcome_checked BOOLEAN DEFAULT FALSE,
    
    -- İndeksler için
    CONSTRAINT valid_ml_direction CHECK (ml_direction IN ('BUY', 'SELL', 'HOLD')),
    CONSTRAINT valid_claude_direction CHECK (claude_direction IS NULL OR claude_direction IN ('BUY', 'SELL', 'HOLD'))
);

CREATE INDEX idx_prediction_logs_symbol ON prediction_logs(symbol);
CREATE INDEX idx_prediction_logs_created_at ON prediction_logs(created_at DESC);
CREATE INDEX idx_prediction_logs_outcome_checked ON prediction_logs(outcome_checked) WHERE outcome_checked = FALSE;


-- 2) OUTCOME RESULTS
-- Tahmin yapıldıktan belirli süre sonra fiyatın ne yaptığını kaydeder
CREATE TABLE IF NOT EXISTS outcome_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Hangi zaman diliminde kontrol edildi
    check_interval VARCHAR(16) NOT NULL,  -- '1h', '4h', '24h', '48h'
    
    -- Fiyat değişimi
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    high_price REAL,  -- Highest price since prediction (for BUY target check)
    low_price REAL,   -- Lowest price since prediction (for SELL target check)
    price_change_pct REAL NOT NULL,  -- (exit - entry) / entry * 100
    
    -- Gerçek yön
    actual_direction VARCHAR(8) NOT NULL,  -- UP, DOWN, FLAT
    
    -- Hedef/Stop durumu
    hit_target BOOLEAN DEFAULT FALSE,
    hit_stop BOOLEAN DEFAULT FALSE,
    
    -- ML tahmini doğru muydu?
    ml_correct BOOLEAN NOT NULL,
    
    -- Claude tahmini doğru muydu?
    claude_correct BOOLEAN,
    
    CONSTRAINT valid_check_interval CHECK (check_interval IN ('1h', '4h', '24h', '48h', '7d')),
    CONSTRAINT valid_actual_direction CHECK (actual_direction IN ('UP', 'DOWN', 'FLAT'))
);

CREATE INDEX idx_outcome_results_prediction_id ON outcome_results(prediction_id);
CREATE INDEX idx_outcome_results_check_interval ON outcome_results(check_interval);


-- 3) LEARNING INSIGHTS
-- Öğrenme döngüsünden çıkan içgörüler
CREATE TABLE IF NOT EXISTS learning_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Hangi sembol için
    symbol VARCHAR(32),  -- NULL = genel
    
    -- İçgörü tipi
    insight_type VARCHAR(32) NOT NULL,  -- 'accuracy', 'factor_correlation', 'condition_performance', 'warning'
    
    -- Zaman aralığı
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    sample_size INT NOT NULL DEFAULT 0,
    
    -- İçgörü verisi (JSON)
    data JSONB NOT NULL DEFAULT '{}',
    -- Örnek accuracy: {"ml_accuracy": 0.62, "claude_accuracy": 0.58, "combined_accuracy": 0.71}
    -- Örnek factor_correlation: {"low_volume_ratio_error_rate": 0.45, "high_vix_error_rate": 0.38}
    -- Örnek condition_performance: {"bullish_trend_ml_accuracy": 0.72, "high_volatility_claude_accuracy": 0.51}
    
    -- Aktif mi? (eski insight'lar deaktif edilebilir)
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT valid_insight_type CHECK (insight_type IN ('accuracy', 'factor_correlation', 'condition_performance', 'warning', 'recommendation'))
);

CREATE INDEX idx_learning_insights_symbol ON learning_insights(symbol);
CREATE INDEX idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX idx_learning_insights_active ON learning_insights(is_active) WHERE is_active = TRUE;


-- 4) FACTOR IMPORTANCE (Opsiyonel - ML model feedback için)
-- Hangi faktörler doğru tahminlerde daha önemli?
CREATE TABLE IF NOT EXISTS factor_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    symbol VARCHAR(32),  -- NULL = genel
    factor_name VARCHAR(64) NOT NULL,
    
    -- Korelasyon metrikleri
    correlation_with_correct REAL,  -- Faktör değeri ile doğru tahmin arasındaki korelasyon
    importance_score REAL DEFAULT 0.5,  -- 0-1 arası, yüksek = daha önemli
    
    -- İstatistikler
    sample_size INT DEFAULT 0,
    avg_value_when_correct REAL,
    avg_value_when_wrong REAL,
    
    UNIQUE(symbol, factor_name)
);

CREATE INDEX idx_factor_importance_symbol ON factor_importance(symbol);


-- 5) VIEWS (Kolay sorgulama için)

-- Son 7 günlük accuracy özeti
CREATE OR REPLACE VIEW v_recent_accuracy AS
SELECT 
    p.symbol,
    COUNT(*) as total_predictions,
    COUNT(o.id) as checked_predictions,
    ROUND(AVG(CASE WHEN o.ml_correct THEN 1.0 ELSE 0.0 END)::numeric, 3) as ml_accuracy,
    ROUND(AVG(CASE WHEN o.claude_correct THEN 1.0 ELSE 0.0 END)::numeric, 3) as claude_accuracy,
    ROUND(AVG(CASE WHEN o.ml_correct AND o.claude_correct THEN 1.0 ELSE 0.0 END)::numeric, 3) as both_correct_rate
FROM prediction_logs p
LEFT JOIN outcome_results o ON o.prediction_id = p.id AND o.check_interval = '24h'
WHERE p.created_at > NOW() - INTERVAL '7 days'
GROUP BY p.symbol;


-- Faktör bazlı hata analizi (son 30 gün)
CREATE OR REPLACE VIEW v_factor_error_analysis AS
SELECT 
    p.symbol,
    (p.factors->>'trend')::text as trend,
    (p.factors->>'volatility')::text as volatility,
    COUNT(*) as sample_count,
    ROUND(AVG(CASE WHEN o.ml_correct THEN 1.0 ELSE 0.0 END)::numeric, 3) as ml_accuracy,
    ROUND(AVG((p.factors->>'volume_ratio')::numeric), 3) as avg_volume_ratio,
    ROUND(AVG((p.factors->>'rsi_14')::numeric), 1) as avg_rsi
FROM prediction_logs p
JOIN outcome_results o ON o.prediction_id = p.id AND o.check_interval = '24h'
WHERE p.created_at > NOW() - INTERVAL '30 days'
GROUP BY p.symbol, (p.factors->>'trend')::text, (p.factors->>'volatility')::text
HAVING COUNT(*) >= 5;


-- ============================================================
-- 6) LIVE DATA CACHE
-- Arka planda sürekli güncellenen canlı veriler
-- ============================================================

CREATE TABLE IF NOT EXISTS live_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(32) NOT NULL UNIQUE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ML Prediction cache
    ml_prediction JSONB,
    
    -- Technical Analysis cache
    ta_data JSONB,
    ta_snapshot JSONB,
    
    -- Levels cache
    levels JSONB,
    
    -- Volume data
    volume JSONB,
    
    -- Volatility data
    volatility JSONB,
    
    -- Macro data (DXY, VIX, USDTRY)
    macro JSONB,
    
    -- News cache (ayrı güncellenir)
    news JSONB,
    news_updated_at TIMESTAMPTZ,
    
    -- Session info
    session JSONB,
    
    -- Full context pack for Claude
    context_pack JSONB,
    
    -- Trend channel
    trend_channel JSONB
);

CREATE INDEX idx_live_data_cache_symbol ON live_data_cache(symbol);
CREATE INDEX idx_live_data_cache_updated_at ON live_data_cache(updated_at DESC);


-- ============================================================
-- ROW LEVEL SECURITY (Opsiyonel - Supabase için)
-- ============================================================
-- Eğer public erişim istemiyorsan bunları aktif et:
-- ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE outcome_results ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE learning_insights ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE factor_importance ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE live_data_cache ENABLE ROW LEVEL SECURITY;
