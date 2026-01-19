-- Migration: Create failure_analyses table for adaptive TP/SL learning
-- This table stores analysis of why trades failed at certain price levels

CREATE TABLE IF NOT EXISTS failure_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES prediction_logs(id),
    symbol VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    failure_price DECIMAL(20, 8) NOT NULL,
    failure_reason VARCHAR(255),
    rsi_at_failure DECIMAL(5, 2),
    volume_change DECIMAL(10, 2),
    nearest_resistance DECIMAL(20, 8),
    nearest_support DECIMAL(20, 8),
    fib_level_hit VARCHAR(20),
    macd_divergence BOOLEAN DEFAULT FALSE,
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_failure_analyses_symbol ON failure_analyses(symbol);
CREATE INDEX IF NOT EXISTS idx_failure_analyses_direction ON failure_analyses(direction);
CREATE INDEX IF NOT EXISTS idx_failure_analyses_created_at ON failure_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_failure_analyses_reason ON failure_analyses(failure_reason);

-- RLS policies (if using Supabase auth)
ALTER TABLE failure_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on failure_analyses" ON failure_analyses
    FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE failure_analyses IS 'Stores analysis of why trades failed at certain price levels for ML learning';
COMMENT ON COLUMN failure_analyses.failure_reason IS 'Pipe-separated list of reasons: RSI_OVERBOUGHT, HIT_RESISTANCE, MACD_DIVERGENCE, VOLUME_DECREASE, FIB_0.618, etc.';
