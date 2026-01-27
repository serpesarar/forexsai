-- Live Data Cache Table
-- Stores pre-computed market data for instant page loads

CREATE TABLE IF NOT EXISTS live_data_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ML Prediction data (JSON)
    ml_prediction JSONB DEFAULT '{}',
    
    -- Technical Analysis snapshot (JSON)
    ta_snapshot JSONB DEFAULT '{}',
    
    -- Macro indicators (JSON)
    macro JSONB DEFAULT '{}',
    
    -- Trading session info (JSON)
    session JSONB DEFAULT '{}',
    
    -- Volume data (JSON)
    volume JSONB DEFAULT '{}',
    
    -- Volatility assessment (JSON)
    volatility JSONB DEFAULT '{}',
    
    -- News data (JSON)
    news JSONB DEFAULT '{}',
    news_updated_at TIMESTAMPTZ,
    
    -- Full context pack for detailed analysis (JSON)
    context_pack JSONB DEFAULT '{}',
    
    -- Current price for quick access
    current_price DECIMAL(20, 6),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast symbol lookups
CREATE INDEX IF NOT EXISTS idx_live_data_cache_symbol ON live_data_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_live_data_cache_updated ON live_data_cache(updated_at DESC);

-- Enable RLS
ALTER TABLE live_data_cache ENABLE ROW LEVEL SECURITY;

-- Public read policy (no auth needed for reading cache)
CREATE POLICY "Allow public read access to cache" ON live_data_cache
    FOR SELECT USING (true);

-- Service role can update
CREATE POLICY "Allow service role full access" ON live_data_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Insert initial rows for tracked symbols
INSERT INTO live_data_cache (symbol, ml_prediction, ta_snapshot, macro, session, volume, volatility, news, context_pack)
VALUES 
    ('NDX.INDX', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'),
    ('XAUUSD', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
ON CONFLICT (symbol) DO NOTHING;
