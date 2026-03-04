-- Add chart marker columns to enriched_news table
-- Run this in Supabase SQL Editor

-- Add missing columns for chart markers
ALTER TABLE enriched_news 
ADD COLUMN IF NOT EXISTS marker_type TEXT DEFAULT 'news',
ADD COLUMN IF NOT EXISTS marker_color TEXT DEFAULT '#3B82F6',
ADD COLUMN IF NOT EXISTS show_on_chart BOOLEAN DEFAULT false;

-- Add index for faster chart marker queries
CREATE INDEX IF NOT EXISTS idx_enriched_news_show_on_chart 
    ON enriched_news(show_on_chart, timestamp DESC) 
    WHERE show_on_chart = true;

-- Add comment for documentation
COMMENT ON COLUMN enriched_news.marker_type IS 'Chart marker type: news, breaking_news, high_impact, economic_event';
COMMENT ON COLUMN enriched_news.marker_color IS 'Hex color code for chart marker';
COMMENT ON COLUMN enriched_news.show_on_chart IS 'Whether to show this news as marker on chart';

-- Verify columns added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'enriched_news' 
AND column_name IN ('marker_type', 'marker_color', 'show_on_chart')
ORDER BY ordinal_position;
