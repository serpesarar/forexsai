-- News Cache Table for Claude Analysis
-- Stores fetched news for later Claude API analysis

CREATE TABLE IF NOT EXISTS news_cache (
    id SERIAL PRIMARY KEY,
    
    -- News identification
    headline TEXT NOT NULL,
    source TEXT,
    source_url TEXT,
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Content hash to avoid duplicates
    headline_hash VARCHAR(64) UNIQUE,
    
    -- Symbol relevance
    symbol VARCHAR(20) NOT NULL,  -- 'XAUUSD', 'NDX.INDX', 'GENERAL'
    
    -- V2 Keyword Analysis (automatic on insert)
    keyword_sentiment FLOAT DEFAULT 0,
    keyword_confidence FLOAT DEFAULT 0,
    keyword_impact_level VARCHAR(20) DEFAULT 'low',
    source_weight FLOAT DEFAULT 1.0,
    time_decay_factor FLOAT DEFAULT 1.0,
    
    -- Claude Analysis (filled when user clicks button)
    claude_analyzed BOOLEAN DEFAULT FALSE,
    claude_analyzed_at TIMESTAMPTZ,
    claude_sentiment FLOAT,
    claude_confidence INT,
    claude_category VARCHAR(50),
    claude_time_sensitivity VARCHAR(20),
    claude_key_entities JSONB,
    claude_rationale TEXT,
    claude_override_signal VARCHAR(20),
    claude_raw_response JSONB,
    
    -- Validation (feedback loop)
    validated BOOLEAN DEFAULT FALSE,
    validated_at TIMESTAMPTZ,
    actual_price_change FLOAT,
    validation_correct BOOLEAN,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_news_cache_symbol ON news_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_news_cache_fetched_at ON news_cache(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_cache_claude_analyzed ON news_cache(claude_analyzed);
CREATE INDEX IF NOT EXISTS idx_news_cache_headline_hash ON news_cache(headline_hash);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_news_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_news_cache_updated_at ON news_cache;
CREATE TRIGGER trigger_news_cache_updated_at
    BEFORE UPDATE ON news_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_news_cache_updated_at();

-- Comment
COMMENT ON TABLE news_cache IS 'Caches news headlines for ML and Claude analysis with validation feedback loop';
