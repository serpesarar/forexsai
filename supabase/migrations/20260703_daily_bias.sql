-- Daily Macro Bias (MiroShark → ForexSAI bridge)
--
-- MiroShark runs a multi-agent debate once per day and emits a NASDAQ daily
-- bias (bullish / bearish / neutral / choppy) via its CIO agent. That verdict
-- is pushed to ForexSAI (webhook or manual paste) and stored here — one row per
-- (bias_date, symbol). The Precision Veto Engine reads today's row and nudges
-- NASDAQ signal confidence toward alignment with the macro bias (soft layer,
-- never a hard override — MiroShark is a once-a-day snapshot, intraday price
-- action stays authoritative).
--
-- Scope: NASDAQ only (NDX.INDX). DAX / XAUUSD / USOIL are untouched.

CREATE TABLE IF NOT EXISTS daily_bias (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    bias_date DATE NOT NULL,
    symbol TEXT NOT NULL DEFAULT 'NDX.INDX',
    nasdaq_daily_bias TEXT NOT NULL,        -- bullish | bearish | neutral | choppy
    confidence FLOAT NOT NULL,              -- 0..100
    expected_close TEXT,                    -- positive | negative | flat | uncertain
    trade_mode TEXT,                        -- buy_dips_only | sell_rallies_only | range_scalp | wait_and_see
    risk_level TEXT,                        -- low | medium | high
    main_support FLOAT,
    main_resistance FLOAT,
    invalid_if TEXT,                        -- human-readable invalidation condition
    reason_summary TEXT,
    agent_agreement TEXT,                   -- high | mixed | low
    risk_flags JSONB,
    debate_winner TEXT,                     -- bull | bear | balanced
    raw_payload JSONB,                      -- full MiroShark CIO output (audit / re-parse)
    is_invalidated BOOLEAN DEFAULT FALSE,   -- flipped intraday if invalid_if triggers
    invalidated_at TIMESTAMPTZ
);

-- One bias per day per symbol; webhook re-sends UPSERT onto this constraint.
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_bias_date_symbol
    ON daily_bias(bias_date, symbol);
-- Newest-first lookup (current-bias endpoint / veto engine).
CREATE INDEX IF NOT EXISTS idx_daily_bias_created
    ON daily_bias(created_at DESC);

ALTER TABLE daily_bias ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access daily_bias" ON daily_bias
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE daily_bias IS
  'Once-a-day NASDAQ macro bias from MiroShark''s CIO agent. Read by the
   Precision Veto Engine as a soft confidence nudge (bonus/penalty, occasional
   soft-veto on high-conviction opposition). NASDAQ-only; intraday price action
   still wins. UPSERT on (bias_date, symbol).';
