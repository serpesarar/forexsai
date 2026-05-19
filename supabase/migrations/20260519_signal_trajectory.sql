-- Post-Entry Trajectory Learner (PETL)
-- Captures feature snapshots at every lifecycle check for active signals.
-- Used to learn which feature evolution patterns predict SL-hits — the
-- model can then abort live trades before they reach SL.
--
-- v1 (rule-based): compares current vs entry snapshot, fires "deterioration"
-- alerts on configurable thresholds.
-- v2 (ML, future): trains a classifier on completed trajectories to predict
-- P(SL_hit) given the trajectory so far.

CREATE TABLE IF NOT EXISTS signal_trajectory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),
    direction VARCHAR(10),
    age_minutes NUMERIC(8, 2) NOT NULL,        -- minutes since signal creation
    current_price NUMERIC(14, 4),
    current_profit_pips NUMERIC(10, 2),
    current_drawdown_pips NUMERIC(10, 2),       -- negative magnitude
    distance_to_tp1_pct NUMERIC(8, 3),         -- % distance remaining to TP1
    distance_to_sl_pct NUMERIC(8, 3),          -- % distance remaining to SL
    features JSONB NOT NULL DEFAULT '{}',       -- lightweight snapshot: rsi, ema, macd, atr, sar, regime
    deteriorating BOOLEAN DEFAULT FALSE,        -- v1 rule-based flag
    deterioration_score NUMERIC(4, 2),         -- v1 score 0..1
    deterioration_reasons TEXT[],              -- which rules fired
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lookup signal trajectory by signal_id (most common query)
CREATE INDEX IF NOT EXISTS idx_trajectory_signal ON signal_trajectory_snapshots(signal_id);
-- Time-window query for training (last N days of finished signals)
CREATE INDEX IF NOT EXISTS idx_trajectory_captured ON signal_trajectory_snapshots(captured_at DESC);
-- Symbol-specific training cohorts
CREATE INDEX IF NOT EXISTS idx_trajectory_symbol ON signal_trajectory_snapshots(symbol, captured_at DESC);
-- Find which signals had deterioration alerts (for offline analysis)
CREATE INDEX IF NOT EXISTS idx_trajectory_deterior ON signal_trajectory_snapshots(deteriorating)
    WHERE deteriorating = TRUE;

ALTER TABLE signal_trajectory_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access trajectory" ON signal_trajectory_snapshots
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE signal_trajectory_snapshots IS
  'Periodic feature snapshots for active signals. Powers the trajectory-aware
   exit predictor: v1 rule-based deterioration detection, v2 ML model.';

-- Per-symbol abort decisions (audit trail of v1+v2 actions)
CREATE TABLE IF NOT EXISTS signal_aborts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),
    direction VARCHAR(10),
    abort_reason TEXT NOT NULL,                -- "deterioration_score>0.7", "ml_predict_sl=0.85", etc
    abort_source VARCHAR(20) NOT NULL,         -- "rule_v1" | "ml_v2"
    pnl_at_abort_pips NUMERIC(10, 2),          -- what we locked in (positive=profit, negative=loss)
    saved_pips_estimate NUMERIC(10, 2),        -- if SL would have fired, this is what we saved
    factors JSONB,                              -- snapshot at abort moment
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aborts_signal ON signal_aborts(signal_id);
CREATE INDEX IF NOT EXISTS idx_aborts_created ON signal_aborts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_aborts_symbol ON signal_aborts(symbol, created_at DESC);

ALTER TABLE signal_aborts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access aborts" ON signal_aborts
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
