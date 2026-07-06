-- CORTEX Phase 1 — Episodic memory (the hippocampus).
--
-- One row per NASDAQ "decision episode": the market SITUATION captured at
-- decision time + what we DECIDED + (filled after close) what actually HAPPENED.
-- Analog retrieval reads graded episodes (outcome NOT NULL) to compute real
-- base rates for the most-similar past days and feed them into the debate CIO.
--
-- Every situation field is NULLABLE on purpose: history is partial (London/QQQ
-- only exist going forward; backfill has macro+outcome but not those), and the
-- distance metric only weighs fields present on BOTH sides.
--
-- NASDAQ-only, isolated. Nothing at signal time depends on this table.

CREATE TABLE IF NOT EXISTS cortex_episodes (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    episode_ts_utc TIMESTAMPTZ NOT NULL,
    ny_date DATE NOT NULL,
    symbol TEXT NOT NULL DEFAULT 'NDX.INDX',
    run_label TEXT,                          -- links to the bias_test_log run
    source TEXT DEFAULT 'bias_run',          -- bias_run | backfill | manual

    -- ── SITUATION (all nullable) ──────────────────────────────────────────
    current_session TEXT,
    session_overlap BOOLEAN,
    is_half_day BOOLEAN,
    minutes_to_us_open INT,
    london_direction TEXT,                   -- up | down | flat
    asia_overnight_change FLOAT,
    qqq_premarket_change FLOAT,              -- % vs prior close
    vix_regime TEXT,                         -- ⭐ LOW|NORMAL|ELEVATED|HIGH|EXTREME
    vix_price FLOAT,
    vix_chg FLOAT,                           -- % / 1h
    dxy_chg FLOAT,
    us10y_chg FLOAT,
    market_regime TEXT,                      -- STRONG_TREND_UP/DOWN|RANGING|TRANSITION
    prior_day_dir TEXT,                      -- up | down
    prior_day_change_pct FLOAT,
    range_position FLOAT,                    -- 0..1 within the recent 5-day range
    day_of_week INT,                         -- 0=Mon .. 4=Fri
    high_impact_event BOOLEAN,               -- FOMC/CPI/NFP today
    situation_json JSONB,                    -- full raw snapshot (future-proof)

    -- ── DECISION ──────────────────────────────────────────────────────────
    predicted_bias TEXT,                     -- bullish|bearish|neutral|choppy
    confidence FLOAT,

    -- ── OUTCOME (filled after the cash close) ─────────────────────────────
    actual_close_direction TEXT,             -- positive | negative | flat
    actual_change_pct FLOAT,
    was_correct BOOLEAN,
    outcome_filled_at TIMESTAMPTZ
);

-- Retrieval hits this: graded episodes for a symbol.
CREATE INDEX IF NOT EXISTS idx_cortex_symbol_graded
    ON cortex_episodes(symbol, actual_close_direction);
CREATE INDEX IF NOT EXISTS idx_cortex_ny_date ON cortex_episodes(ny_date);
CREATE INDEX IF NOT EXISTS idx_cortex_created ON cortex_episodes(created_at DESC);

ALTER TABLE cortex_episodes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access cortex_episodes" ON cortex_episodes;
CREATE POLICY "Service role full access cortex_episodes" ON cortex_episodes
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE cortex_episodes IS
  'CORTEX episodic memory: NASDAQ situation + decision + outcome per day. Analog
   retrieval computes base rates from graded rows to enrich the bias debate.';
