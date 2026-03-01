-- News-Chart Correlation System - Full Migration
-- Run this in Supabase SQL Editor (NOT psql \i command)

-- =====================================================
-- 1. CREATE ENRICHED_NEWS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS enriched_news (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL,
    headline TEXT NOT NULL,
    content TEXT,
    category TEXT DEFAULT 'general',
    url TEXT,
    image_url TEXT,
    
    -- AI Analysis Results
    impacts JSONB NOT NULL DEFAULT '[]'::jsonb,
    sentiment TEXT CHECK (sentiment IN ('risk_on', 'risk_off', 'neutral')),
    volatility_expectation TEXT CHECK (volatility_expectation IN ('high', 'medium', 'low')),
    key_levels JSONB,
    event_duration TEXT CHECK (event_duration IN ('immediate', 'short_term', 'long_term')),
    ai_confidence NUMERIC(5,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 100),
    
    -- RSS-specific fields
    urgency TEXT CHECK (urgency IN ('breaking', 'high', 'medium', 'low')) DEFAULT 'medium',
    duplicate_of TEXT REFERENCES enriched_news(id),
    sources JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_enriched_news_timestamp 
    ON enriched_news(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_enriched_news_sentiment 
    ON enriched_news(sentiment);

CREATE INDEX IF NOT EXISTS idx_enriched_news_analysis_timestamp 
    ON enriched_news(analysis_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_enriched_news_impacts 
    ON enriched_news USING GIN(impacts);

CREATE INDEX IF NOT EXISTS idx_enriched_news_urgency 
    ON enriched_news(urgency);

CREATE INDEX IF NOT EXISTS idx_enriched_news_category 
    ON enriched_news(category);

CREATE INDEX IF NOT EXISTS idx_enriched_news_duplicate 
    ON enriched_news(duplicate_of) 
    WHERE duplicate_of IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_enriched_news_main 
    ON enriched_news(timestamp DESC, urgency, category) 
    WHERE duplicate_of IS NULL;

CREATE INDEX IF NOT EXISTS idx_enriched_news_url 
    ON enriched_news(url) 
    WHERE url IS NOT NULL;

-- =====================================================
-- 3. CREATE FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to clean old RSS data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_rss_news()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM enriched_news 
    WHERE timestamp < NOW() - INTERVAL '30 days'
    AND urgency IN ('low', 'medium');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. CREATE TRIGGERS
-- =====================================================

DROP TRIGGER IF EXISTS update_enriched_news_updated_at ON enriched_news;
CREATE TRIGGER update_enriched_news_updated_at
    BEFORE UPDATE ON enriched_news
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 5. ENABLE RLS AND CREATE POLICIES
-- =====================================================

ALTER TABLE enriched_news ENABLE ROW LEVEL SECURITY;

-- Allow read access to all authenticated users
DROP POLICY IF EXISTS "Allow read access to enriched_news" ON enriched_news;
CREATE POLICY "Allow read access to enriched_news" 
    ON enriched_news FOR SELECT 
    TO authenticated 
    USING (true);

-- Allow service role full access
DROP POLICY IF EXISTS "Allow service role full access to enriched_news" ON enriched_news;
CREATE POLICY "Allow service role full access to enriched_news" 
    ON enriched_news FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

-- Allow RSS service to insert news
DROP POLICY IF EXISTS "Allow RSS service to insert news" ON enriched_news;
CREATE POLICY "Allow RSS service to insert news" 
    ON enriched_news FOR INSERT 
    TO service_role 
    WITH CHECK (true);

-- =====================================================
-- 6. ADD COMMENTS
-- =====================================================

COMMENT ON TABLE enriched_news IS 'AI-enriched financial news with market impact analysis from RSS feeds';
COMMENT ON COLUMN enriched_news.impacts IS 'Array of symbol impacts with direction, score, confidence, and reasoning';
COMMENT ON COLUMN enriched_news.sentiment IS 'Overall market sentiment: risk_on, risk_off, or neutral';
COMMENT ON COLUMN enriched_news.key_levels IS 'Support and resistance levels mentioned in the news';
COMMENT ON COLUMN enriched_news.urgency IS 'News urgency level: breaking, high, medium, low';
COMMENT ON COLUMN enriched_news.duplicate_of IS 'Reference to original news item if this is a duplicate from another source';
COMMENT ON COLUMN enriched_news.sources IS 'Array of RSS sources that reported this news';
COMMENT ON COLUMN enriched_news.category IS 'News category: forex, markets, business, commodities, crypto';
