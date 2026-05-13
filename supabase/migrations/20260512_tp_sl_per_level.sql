-- Per-TP-level simulation breakdown for TP/SL recommendations.
-- Stores how each existing TP level (TP1..TP4) performs against the current SL,
-- so the dashboard can show an honest "what if you keep current ladder" view
-- alongside the optimizer's single-point recommendation.

ALTER TABLE tp_sl_recommendations
    ADD COLUMN IF NOT EXISTS per_tp_level_simulated JSONB,
    ADD COLUMN IF NOT EXISTS grid_dim JSONB;

COMMENT ON COLUMN tp_sl_recommendations.per_tp_level_simulated IS
  'Array of {name, tp_pips, sl_pips, net_pnl, win_rate, wins, losses, timeouts}
   for each existing TP level vs current SL. Lets reviewers see whether the
   issue is TP placement or SL placement.';

COMMENT ON COLUMN tp_sl_recommendations.grid_dim IS
  'Grid search resolution {tp_candidates, sl_candidates, tp_range, sl_range}.
   Helps verify the recommendation was made with a sufficiently fine grid.';
