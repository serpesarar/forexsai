-- Macro daily-bias columns on the veto audit log.
--
-- precision_veto_service now applies a NASDAQ macro-bias nudge (from the
-- daily_bias table) inside Stage 1. These two columns record what it did so the
-- veto dashboard and Stage-4 training can see the bias effect per signal:
--   macro_bias_adjustment  signed confidence delta (+bonus / -penalty), NULL if n/a
--   macro_bias_state       bullish | bearish | neutral | choppy | no_bias | ...

ALTER TABLE signal_vetoes ADD COLUMN IF NOT EXISTS macro_bias_adjustment FLOAT;
ALTER TABLE signal_vetoes ADD COLUMN IF NOT EXISTS macro_bias_state TEXT;
