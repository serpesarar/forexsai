-- Post-deploy live tracking for implemented proposals.
-- After a proposal merges (status='implemented'), the monitor tracks 7-day
-- live performance vs the simulated_metric. If live < simulation × 0.5 →
-- auto-rollback alert.

ALTER TABLE improvement_proposals
  ADD COLUMN IF NOT EXISTS live_tracking_started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS live_tracking_metric JSONB,
  ADD COLUMN IF NOT EXISTS live_tracking_last_check TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rollback_recommended BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS rollback_recommendation_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_tracking
  ON improvement_proposals (live_tracking_started_at DESC NULLS LAST)
  WHERE status = 'implemented';

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_rollback_alert
  ON improvement_proposals (rollback_recommended)
  WHERE rollback_recommended = TRUE;

COMMENT ON COLUMN improvement_proposals.live_tracking_metric IS
  'Daily-updated live performance: {checked_days, daily_snapshots[],
    overall: {n_signals, win_rate, pnl_pips, max_drawdown},
    vs_simulation: {win_rate_delta, pnl_delta, divergence_factor},
    status: tracking|confirmed|degraded}';
