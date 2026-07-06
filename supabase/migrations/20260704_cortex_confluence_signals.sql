-- CORTEX confluence SHADOW signals — the two most-robust leak-verified edges
-- (NDX long: bull-alignment + SPX↑ ; NDX short: weak-open + S&P↓) evaluated live
-- at their decision hours, LOGGED ONLY (never executed). Forward-validates the
-- backtest edge on real data before any capital decision.

CREATE TABLE IF NOT EXISTS cortex_confluence_signals (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rule_id TEXT NOT NULL,                    -- NDX_L_spx | NDX_S_es
    symbol TEXT NOT NULL DEFAULT 'NDX.INDX',
    side TEXT NOT NULL,                       -- long | short
    decision_ts_utc TIMESTAMPTZ NOT NULL,
    horizon TEXT NOT NULL,                    -- next_1h
    -- feature snapshot at decision (audit)
    bull_score FLOAT,
    macd_hist FLOAT,
    first_hour_pct FLOAT,
    x_spx FLOAT,
    x_es FLOAT,
    price_at_decision FLOAT,
    fired BOOLEAN NOT NULL,                   -- did the rule's conditions hold
    -- outcome (filled after the horizon elapses)
    price_at_horizon FLOAT,
    actual_dir TEXT,                          -- positive | negative
    was_correct BOOLEAN,
    outcome_filled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cortex_sig_rule ON cortex_confluence_signals(rule_id);
CREATE INDEX IF NOT EXISTS idx_cortex_sig_ts ON cortex_confluence_signals(decision_ts_utc DESC);

ALTER TABLE cortex_confluence_signals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access cortex_signals" ON cortex_confluence_signals;
CREATE POLICY "Service role full access cortex_signals" ON cortex_confluence_signals
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE cortex_confluence_signals IS
  'Shadow (log-only) evaluations of the two most-robust CORTEX confluence rules
   for live forward-validation. Never executed.';
