-- Add 'meta' to prediction_logs model_type CHECK constraint
-- Root cause: meta engine signals were silently failing because 'meta' was not in the allowed list

ALTER TABLE prediction_logs
DROP CONSTRAINT IF EXISTS prediction_logs_model_type_check;

ALTER TABLE prediction_logs
ADD CONSTRAINT prediction_logs_model_type_check
CHECK (model_type = ANY (ARRAY[
  'ml'::text, 'ml:main'::text, 'ml:ultra_safe'::text, 'ml:balanced'::text,
  'ml:full_power'::text, 'ml:aggressive'::text, 'ml:nasdaq_precision'::text,
  'ai_panel'::text, 'pulse'::text, 'pulse1'::text, 'pulse2'::text, 'pulse3'::text,
  'emel'::text, 'emel_inverse'::text, 'smc'::text, 'hybrid'::text, 'meta'::text
]));
