-- TP/SL Optimization Recommendations
-- Each row = one analysis pass for (symbol, model, direction, timeframe).
-- Compares current static config (target_config.py) with optimal TP/SL
-- found by grid-searching the historical MFE/MAE distribution.

CREATE TABLE IF NOT EXISTS tp_sl_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Scope
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),                -- nullable = aggregate across all models
    direction VARCHAR(10),                  -- BUY / SELL / null=combined
    timeframe VARCHAR(10),                  -- 5m / 30m / 1h / null=any
    -- Sample
    sample_size INT NOT NULL,
    analysis_window_days INT NOT NULL,
    -- Current config snapshot (from services/target_config.py)
    current_tp_pips NUMERIC(8, 2),
    current_sl_pips NUMERIC(8, 2),
    current_net_pnl_pips NUMERIC(10, 2),
    current_win_rate NUMERIC(5, 2),
    -- Optimal recommendation
    recommended_tp_pips NUMERIC(8, 2) NOT NULL,
    recommended_sl_pips NUMERIC(8, 2) NOT NULL,
    recommended_net_pnl_pips NUMERIC(10, 2),
    recommended_win_rate NUMERIC(5, 2),
    -- Improvement
    expected_pnl_delta_pips NUMERIC(10, 2),
    expected_winrate_delta_pp NUMERIC(6, 2),
    -- Distribution diagnostics (jsonb to avoid schema bloat)
    mfe_distribution JSONB,                -- {p10, p25, p50, p70, p80, p90, p95}
    mae_distribution JSONB,
    grid_top5 JSONB,                        -- top 5 (tp, sl, net_pnl) for inspection
    -- Workflow
    status VARCHAR(30) DEFAULT 'pending',  -- pending | reviewed | applied | rejected
    severity VARCHAR(20),                  -- critical | high | medium | low | none
    reasoning TEXT,                        -- human-readable why
    reviewed_by VARCHAR(120),
    reviewed_at TIMESTAMPTZ,
    applied_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tp_sl_recommendations_symbol ON tp_sl_recommendations(symbol);
CREATE INDEX IF NOT EXISTS idx_tp_sl_recommendations_status ON tp_sl_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_tp_sl_recommendations_created ON tp_sl_recommendations(created_at DESC);

ALTER TABLE tp_sl_recommendations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access tp_sl_recommendations" ON tp_sl_recommendations
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE tp_sl_recommendations IS
  'Optimal TP/SL pairs derived from historical MFE/MAE grid search. Each row
   pairs current static config with a data-driven recommendation, plus the
   distribution stats used to derive it.';
