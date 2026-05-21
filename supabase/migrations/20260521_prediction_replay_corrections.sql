-- Replay-derived corrected outcomes for historical signals.
--
-- Built for the 2026-05-20 recovery operation: re-walk every signal
-- created since 2026-02-10 against 1m MT5 bars and re-decide the
-- TP/SL outcome using the EXACT same rule logic as signal_lifecycle.py.
-- This recovers honest win/loss/timeout buckets that the pre-entry wick
-- leak (fixed 2026-05-19) polluted on prediction_logs.
--
-- IMPORTANT: this table is AUDIT-SAFE — prediction_logs is never
-- overwritten. Panels can opt into "corrected mode" by joining here.

CREATE TABLE IF NOT EXISTS prediction_replay_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Source signal
    prediction_id UUID NOT NULL REFERENCES prediction_logs(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),
    direction VARCHAR(10),
    timeframe VARCHAR(10),
    entry_price NUMERIC(14, 5),
    signal_created_at TIMESTAMPTZ NOT NULL,

    -- ORIGINAL outcome (snapshotted at replay time for delta comparison)
    original_status VARCHAR(30),
    original_resolution_reason VARCHAR(60),
    original_exit_price NUMERIC(14, 5),
    original_highest_profit_pips NUMERIC(14, 3),
    original_lowest_drawdown_pips NUMERIC(14, 3),

    -- CORRECTED outcome (computed by 1m walk-forward replay)
    corrected_status VARCHAR(30),               -- completed | stopped | expired
    corrected_resolution_reason VARCHAR(60),    -- tp1_hit | tp2_hit | tp3_hit | tp4_hit |
                                                -- tp1_3_hit_then_sl | all_targets_hit |
                                                -- sl_hit | window_expired | no_candles
    corrected_target_hit VARCHAR(10),           -- TP1 | TP2 | TP3 | TP4 | null
    corrected_exit_price NUMERIC(14, 5),
    corrected_exit_at TIMESTAMPTZ,              -- 1m bar timestamp where resolution fired
    corrected_time_to_resolution_minutes INTEGER,

    -- True MFE/MAE from 1m bars during the active window
    corrected_mfe_pips NUMERIC(14, 3),
    corrected_mae_pips NUMERIC(14, 3),

    -- Diagnostics
    bars_walked INTEGER,                         -- how many 1m bars consumed
    replay_status VARCHAR(30) NOT NULL,          -- ok | no_entry | no_candles | exception
    replay_notes TEXT,

    -- Diff convenience flags (computed by service, not generated columns —
    -- keeps Supabase migrations portable)
    outcome_flipped BOOLEAN,                     -- original != corrected status
    pnl_delta_pips NUMERIC(14, 3),               -- corrected - original profit_pips

    -- Audit
    replayed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    replay_batch_id UUID,                        -- groups a single /api/replay/run pass
    rule_version VARCHAR(20) DEFAULT 'v1',       -- bump if TP/SL ladder logic changes

    UNIQUE (prediction_id, replay_batch_id)
);

CREATE INDEX IF NOT EXISTS idx_replay_prediction_id
    ON prediction_replay_corrections(prediction_id);
CREATE INDEX IF NOT EXISTS idx_replay_symbol_model
    ON prediction_replay_corrections(symbol, model_type, replayed_at DESC);
CREATE INDEX IF NOT EXISTS idx_replay_batch
    ON prediction_replay_corrections(replay_batch_id);
CREATE INDEX IF NOT EXISTS idx_replay_flipped
    ON prediction_replay_corrections(outcome_flipped)
    WHERE outcome_flipped = TRUE;

ALTER TABLE prediction_replay_corrections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access prediction_replay_corrections"
    ON prediction_replay_corrections
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE prediction_replay_corrections IS
  'Audit-safe replay corrections — walks each historical signal against
   1m MT5 bars and re-decides TP/SL outcome using current signal_lifecycle
   rules. Used to recover honest win/loss attribution polluted by the
   pre-entry wick leak (lifecycle fix commit 32033c6, 2026-05-19).';
