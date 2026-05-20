-- MT5 deals (ground truth from the broker terminal).
-- Used to reconcile our prediction_logs against the actual filled trades.
-- Populated via /api/mt5/upload-deals (CSV/HTML/JSON upload).

CREATE TABLE IF NOT EXISTS mt5_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- MT5 identifiers
    ticket BIGINT NOT NULL,
    order_id BIGINT,
    position_id BIGINT,
    -- Trade
    symbol VARCHAR(50) NOT NULL,         -- MT5 form (XAUUSD, USTEC, DE40, XTIUSD)
    normalized_symbol VARCHAR(50),       -- ForexSAI canonical (NDX.INDX, GDAXI.INDX, USOIL.FOREX, XAUUSD)
    direction VARCHAR(10) NOT NULL,      -- BUY | SELL
    entry_type VARCHAR(10),              -- in (open) | out (close) | inout | out_by
    -- Financials
    volume NUMERIC(10, 4),
    price NUMERIC(14, 5),
    profit NUMERIC(14, 2),               -- account currency
    commission NUMERIC(10, 2),
    swap NUMERIC(10, 2),
    -- Time
    deal_time TIMESTAMPTZ NOT NULL,
    -- Context
    comment TEXT,
    account_login BIGINT,
    broker VARCHAR(120),
    currency VARCHAR(10),
    -- Reconciliation
    matched_prediction_id UUID REFERENCES prediction_logs(id) ON DELETE SET NULL,
    matched_at TIMESTAMPTZ,
    match_confidence NUMERIC(5, 2),      -- 0-100, how confident the match is
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (ticket, entry_type)
);

CREATE INDEX IF NOT EXISTS idx_mt5_trades_symbol_time ON mt5_trades(normalized_symbol, deal_time DESC);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_position ON mt5_trades(position_id);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_matched ON mt5_trades(matched_prediction_id)
    WHERE matched_prediction_id IS NOT NULL;

ALTER TABLE mt5_trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access mt5_trades" ON mt5_trades
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE mt5_trades IS
  'MT5 broker terminal deal history. Ground truth for reconciliation
   with prediction_logs — exposes the gap between our lifecycle outcomes
   and actual broker fills (spread, slippage, premature lifecycle hits).';
