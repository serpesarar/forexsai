-- Add 'ml_cross_xau_nasdaq' to prediction_logs model_type CHECK constraint
-- Root cause: the NASDAQ-ML-on-XAUUSD experiment (cross_model_experiment_service)
-- logs with model_type='ml_cross_xau_nasdaq', which was missing from the allowed
-- list. Every insert silently failed the CHECK (23514) → log_prediction returned
-- None → panel showed "log_skipped" and the stats table stayed empty since setup.
-- Same class of bug as 20260328_add_meta_model_type.sql.

ALTER TABLE prediction_logs
DROP CONSTRAINT IF EXISTS prediction_logs_model_type_check;

ALTER TABLE prediction_logs
ADD CONSTRAINT prediction_logs_model_type_check
CHECK (model_type = ANY (ARRAY[
  'ml'::text, 'ml:main'::text, 'ml:ultra_safe'::text, 'ml:balanced'::text,
  'ml:full_power'::text, 'ml:aggressive'::text, 'ml:nasdaq_precision'::text,
  'ai_panel'::text, 'pulse'::text, 'pulse1'::text, 'pulse2'::text, 'pulse3'::text,
  'emel'::text, 'emel_inverse'::text, 'smc'::text, 'hybrid'::text, 'meta'::text,
  'ml_cross_xau_nasdaq'::text
]));
