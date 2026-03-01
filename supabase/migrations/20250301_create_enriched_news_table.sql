-- Create enriched_news table for News-Chart Correlation System
-- Stores AI-analyzed news with market impact data

CREATE TABLE IF NOT EXISTS enriched_news (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL,
    headline TEXT NOT NULL,
    content TEXT,
    category TEXT,
    url TEXT,
    image_url TEXT,
    
    -- AI Analysis Results
    impacts JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Example: [{"symbol": "XAUUSD", "direction": "bullish", "score": 8, "confidence": 0.85, "reasoning": "Safe haven demand"}]
    
    sentiment TEXT CHECK (sentiment IN ('risk_on', 'risk_off', 'neutral')),
    volatility_expectation TEXT CHECK (volatility_expectation IN ('high', 'medium', 'low')),
    key_levels JSONB,
    -- Example: {"support": [2900.50, 2880.00], "resistance": [2950.00, 2980.00]}
    
    event_duration TEXT CHECK (event_duration IN ('immediate', 'short_term', 'long_term')),
    ai_confidence NUMERIC(5,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 100),
    
    -- Metadata
    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_enriched_news_timestamp 
    ON enriched_news(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_enriched_news_sentiment 
    ON enriched_news(sentiment);

CREATE INDEX IF NOT EXISTS idx_enriched_news_analysis_timestamp 
    ON enriched_news(analysis_timestamp DESC);

-- GIN index for JSONB queries on impacts
CREATE INDEX IF NOT EXISTS idx_enriched_news_impacts 
    ON enriched_news USING GIN(impacts);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_enriched_news_updated_at ON enriched_news;
CREATE TRIGGER update_enriched_news_updated_at
    BEFORE UPDATE ON enriched_news
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS)
ALTER TABLE enriched_news ENABLE ROW LEVEL SECURITY;

-- Allow read access to all authenticated users
CREATE POLICY "Allow read access to enriched_news" 
    ON enriched_news FOR SELECT 
    TO authenticated 
    USING (true);

-- Allow insert/update only to service role
CREATE POLICY "Allow service role full access to enriched_news" 
    ON enriched_news FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE enriched_news IS 'AI-enriched financial news with market impact analysis';
COMMENT ON COLUMN enriched_news.impacts IS 'Array of symbol impacts with direction, score, confidence, and reasoning';
COMMENT ON COLUMN enriched_news.sentiment IS 'Overall market sentiment: risk_on, risk_off, or neutral';
COMMENT ON COLUMN enriched_news.key_levels IS 'Support and resistance levels mentioned in the news';
