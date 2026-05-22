-- Precision Veto Engine — blocked / penalised signal audit log.
--
-- Every signal from the 6 generators (ML, EMEL, PULSE 1/2/3, SMC) passes
-- through precision_veto_service.check_signal() BEFORE being persisted to
-- prediction_logs. A hard veto blocks the signal and writes a row here
-- with the reason + the features that triggered it; soft penalties that
-- still pass are also recorded for analysis.

CREATE TABLE IF NOT EXISTS signal_vetoes (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol TEXT NOT NULL,
    model_type TEXT NOT NULL,
    signal_direction TEXT NOT NULL,
    signal_confidence FLOAT NOT NULL,
    veto_stage INT NOT NULL,            -- 1 | 2 | 3 | 4
    veto_reason TEXT NOT NULL,          -- premium_zone_buy, wick_rejection_top, ...
    veto_details JSONB,
    -- Feature snapshot at veto time (for the analysis dashboard / Stage-4 training)
    liquidity_zone_position FLOAT,      -- 0..1, premium=1
    mtf_agreement_score FLOAT,          -- -1..+1
    wick_rejection_score FLOAT,         -- 0..1
    bb_position FLOAT,                  -- 0..1
    z_score FLOAT,
    meta_classifier_proba FLOAT,
    price_at_veto FLOAT NOT NULL,
    market_regime TEXT,
    -- 'veto' = signal blocked | 'penalty' = passed but confidence cut |
    -- 'shadow' = would-have-been-vetoed (shadow mode, not enforced)
    outcome TEXT DEFAULT 'veto'
);

CREATE INDEX IF NOT EXISTS idx_signal_vetoes_symbol_time
    ON signal_vetoes(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_vetoes_reason
    ON signal_vetoes(veto_reason);
CREATE INDEX IF NOT EXISTS idx_signal_vetoes_stage
    ON signal_vetoes(veto_stage);

ALTER TABLE signal_vetoes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access signal_vetoes" ON signal_vetoes
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Analysis view — veto counts & rates per symbol/model/reason (last 30d).
CREATE OR REPLACE VIEW signal_veto_summary AS
SELECT
    symbol,
    model_type,
    signal_direction,
    veto_stage,
    veto_reason,
    outcome,
    COUNT(*)                                  AS n,
    ROUND(AVG(signal_confidence)::numeric, 1) AS avg_confidence,
    ROUND(AVG(liquidity_zone_position)::numeric, 3) AS avg_liq_pos,
    ROUND(AVG(wick_rejection_score)::numeric, 3)    AS avg_wick_score,
    MAX(created_at)                           AS last_seen
FROM signal_vetoes
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY symbol, model_type, signal_direction, veto_stage, veto_reason, outcome
ORDER BY n DESC;

COMMENT ON TABLE signal_vetoes IS
  'Precision Veto Engine audit log — signals blocked or penalised before
   reaching prediction_logs. outcome: veto=blocked, penalty=passed with
   confidence cut, shadow=would-block (shadow mode).';
