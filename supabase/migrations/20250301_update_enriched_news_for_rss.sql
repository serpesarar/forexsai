-- Update enriched_news table for RSS aggregation support
-- Adds RSS-specific fields and improves indexing

-- Add new columns for RSS support
ALTER TABLE enriched_news 
ADD COLUMN IF NOT EXISTS url TEXT,
ADD COLUMN IF NOT EXISTS urgency TEXT CHECK (urgency IN ('breaking', 'high', 'medium', 'low')) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS duplicate_of TEXT REFERENCES enriched_news(id),
ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general';

-- Create index for urgency filtering
CREATE INDEX IF NOT EXISTS idx_enriched_news_urgency 
    ON enriched_news(urgency);

-- Create index for category filtering
CREATE INDEX IF NOT EXISTS idx_enriched_news_category 
    ON enriched_news(category);

-- Create index for duplicate detection
CREATE INDEX IF NOT EXISTS idx_enriched_news_duplicate 
    ON enriched_news(duplicate_of) 
    WHERE duplicate_of IS NOT NULL;

-- Create partial index for non-duplicate items (main query optimization)
CREATE INDEX IF NOT EXISTS idx_enriched_news_main 
    ON enriched_news(timestamp DESC, urgency, category) 
    WHERE duplicate_of IS NULL;

-- Create index for URL lookups (deduplication)
CREATE INDEX IF NOT EXISTS idx_enriched_news_url 
    ON enriched_news(url) 
    WHERE url IS NOT NULL;

-- Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_enriched_news_symbol_time 
    ON enriched_news(timestamp DESC) 
    INCLUDE (impacts, urgency, sentiment);

-- Update RLS policies for RSS data
-- Allow service role to insert RSS data
CREATE POLICY "Allow RSS service to insert news" 
    ON enriched_news FOR INSERT 
    TO service_role 
    WITH CHECK (true);

-- Function to clean old RSS data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_rss_news()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM enriched_news 
    WHERE timestamp < NOW() - INTERVAL '30 days'
    AND urgency IN ('low', 'medium'); -- Keep high and breaking news longer
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON COLUMN enriched_news.urgency IS 'News urgency level: breaking, high, medium, low';
COMMENT ON COLUMN enriched_news.duplicate_of IS 'Reference to original news item if this is a duplicate';
COMMENT ON COLUMN enriched_news.sources IS 'Array of RSS sources that reported this news';
COMMENT ON COLUMN enriched_news.category IS 'News category: forex, markets, business, commodities, crypto';
