-- Add bilingual AI summary/analysis fields to enriched_news

ALTER TABLE enriched_news
ADD COLUMN IF NOT EXISTS summary_en TEXT,
ADD COLUMN IF NOT EXISTS summary_tr TEXT,
ADD COLUMN IF NOT EXISTS analysis_en TEXT,
ADD COLUMN IF NOT EXISTS analysis_tr TEXT;

UPDATE enriched_news
SET
  summary_en = COALESCE(NULLIF(summary_en, ''), headline),
  summary_tr = COALESCE(NULLIF(summary_tr, ''), headline_tr, headline),
  analysis_en = COALESCE(NULLIF(analysis_en, ''), content, headline),
  analysis_tr = COALESCE(NULLIF(analysis_tr, ''), content_tr, headline_tr, content, headline)
WHERE
  summary_en IS NULL OR summary_en = '' OR
  summary_tr IS NULL OR summary_tr = '' OR
  analysis_en IS NULL OR analysis_en = '' OR
  analysis_tr IS NULL OR analysis_tr = '';

COMMENT ON COLUMN enriched_news.summary_en IS 'English AI summary generated from DeepSeek';
COMMENT ON COLUMN enriched_news.summary_tr IS 'Turkish AI summary generated from DeepSeek';
COMMENT ON COLUMN enriched_news.analysis_en IS 'English AI market analysis generated from DeepSeek';
COMMENT ON COLUMN enriched_news.analysis_tr IS 'Turkish AI market analysis generated from DeepSeek';