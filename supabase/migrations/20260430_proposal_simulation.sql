-- Counterfactual simulation results for AI-ops proposals.
-- Populated by services/proposal_simulator.py after each proposal is created.
-- Frontend reads this to show "if this fix had been live, last 60 days would have looked like X".

ALTER TABLE improvement_proposals
  ADD COLUMN IF NOT EXISTS simulated_metric JSONB,
  ADD COLUMN IF NOT EXISTS simulated_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_simulated
  ON improvement_proposals (simulated_at DESC NULLS LAST);

COMMENT ON COLUMN improvement_proposals.simulated_metric IS
  'Counterfactual replay of the proposal on last N days of prediction_logs.
   Schema: {window_days, original: {n_signals, win_rate, total_pnl_pips},
            simulated: {n_blocked, n_kept, win_rate, total_pnl_pips},
            deltas: {win_rate_pp, pnl_pips}, status, fixes_evaluated, fixes_skipped}';
