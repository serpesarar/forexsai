-- Karar dayanıklılık ısı haritası (2026-07-20): 10dk→6 saat merdiveni.
-- Uygulandı: mcp apply_migration "bias_test_log_extended_horizons"
alter table bias_test_log add column if not exists ret_90m  double precision;
alter table bias_test_log add column if not exists ret_120m double precision;
alter table bias_test_log add column if not exists ret_180m double precision;
alter table bias_test_log add column if not exists ret_300m double precision;
alter table bias_test_log add column if not exists ret_360m double precision;
