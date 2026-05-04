-- Persistent history of pattern mining runs.
-- Backend writes here weekly so:
--   1. Rules survive Railway redeploys (file system is ephemeral)
--   2. We can compare rule sets over time
--   3. Frontend can display "last run X days ago, Y rules active"

CREATE TABLE IF NOT EXISTS pattern_mining_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    window_days INT NOT NULL,
    total_signals INT NOT NULL,
    rules_count INT NOT NULL,
    winning_count INT,
    avoid_count INT,
    segments_count INT,
    rules JSONB NOT NULL,                 -- full rules array (the same shape as pattern_rules.json)
    triggered_by VARCHAR(30) DEFAULT 'cron',  -- cron / manual
    status VARCHAR(30) DEFAULT 'completed',
    error TEXT,
    duration_seconds NUMERIC(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pattern_mining_runs_recent
  ON pattern_mining_runs (generated_at DESC);

ALTER TABLE pattern_mining_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access pattern_mining_runs" ON pattern_mining_runs
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE pattern_mining_runs IS 'Weekly self-feeding pattern mining runs. The rules JSONB matches pattern_rules.json schema.';
