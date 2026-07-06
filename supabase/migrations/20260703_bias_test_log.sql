-- Bias-accuracy MEASUREMENT log (MiroShark test harness).
--
-- ISOLATED from the live daily_bias table and the Precision Veto Engine. Its
-- only job: record each MiroShark bias run with rich session context so we can
-- later answer "which run-hour produces the most accurate NASDAQ bias?" before
-- deciding whether to wire it live. Nothing reads this table at signal time.
--
-- NOTE: idempotent — safe to re-run. ny_date is a plain DATE column (computed by
-- the app from the NY timestamp) so it can be indexed. An index on
-- (ny_time::date) fails with 42P17 "must be marked IMMUTABLE" because casting a
-- timestamptz to date is timezone-session-dependent — hence a stored column.

CREATE TABLE IF NOT EXISTS bias_test_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    run_timestamp_utc TIMESTAMPTZ NOT NULL,
    ny_time TIMESTAMPTZ NOT NULL,
    ny_date DATE,                            -- NY calendar date (indexable, set by app)
    run_label TEXT,                          -- "0800_main", "0945_confirm", "manual", ...
    -- Session context at run time
    current_session TEXT,
    london_direction TEXT,
    asia_overnight_change FLOAT,
    us_premarket_change FLOAT,
    minutes_to_us_open INT,
    is_half_day BOOLEAN,
    is_holiday BOOLEAN,
    session_overlap BOOLEAN,
    -- MiroShark bias output
    predicted_bias TEXT NOT NULL,            -- bullish | bearish | neutral | choppy
    confidence FLOAT NOT NULL,
    trade_mode TEXT,
    main_support FLOAT,
    main_resistance FLOAT,
    invalid_if TEXT,
    reason_summary TEXT,
    raw_payload JSONB,
    -- Outcome (filled after the cash session closes)
    actual_close_direction TEXT,             -- positive | negative | flat (NULL = unknown yet)
    actual_change_pct FLOAT,
    was_correct BOOLEAN,                     -- predicted vs actual
    invalid_if_triggered BOOLEAN,
    outcome_filled_at TIMESTAMPTZ
);

-- Pre-existing table (created before ny_date existed) → add the column.
ALTER TABLE bias_test_log ADD COLUMN IF NOT EXISTS ny_date DATE;

-- Remove the old non-IMMUTABLE functional index if a prior run created it.
DROP INDEX IF EXISTS idx_bias_test_ny_date;

CREATE INDEX IF NOT EXISTS idx_bias_test_run_label ON bias_test_log(run_label);
CREATE INDEX IF NOT EXISTS idx_bias_test_ny_date ON bias_test_log(ny_date);
CREATE INDEX IF NOT EXISTS idx_bias_test_ny_time ON bias_test_log(ny_time);

ALTER TABLE bias_test_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access bias_test_log" ON bias_test_log;
CREATE POLICY "Service role full access bias_test_log" ON bias_test_log
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE bias_test_log IS
  'Isolated measurement log for MiroShark bias accuracy by run-hour / session
   context. Not read at signal time; drives the go-live decision.';
