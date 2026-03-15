alter table public.prediction_logs
  drop constraint if exists prediction_logs_model_type_check;

alter table public.prediction_logs
  add constraint prediction_logs_model_type_check
  check (
    model_type = any (
      array[
        'ml',
        'ml:main',
        'ml:ultra_safe',
        'ml:balanced',
        'ml:full_power',
        'ml:aggressive',
        'ml:nasdaq_precision',
        'pulse',
        'pulse1',
        'pulse2',
        'pulse3',
        'emel',
        'emel_inverse',
        'hybrid'
      ]
    )
  );
