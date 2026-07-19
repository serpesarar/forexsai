-- Çok-ufuklu notlama: tartışma kararının +10/30/60/240 dk gerçekleşmesi.
-- Gerekçe (backend/data/agent_debate_analysis_report.md): gün-kapanışı metriği
-- ajan isabetini gizliyor (NDX bearish gün 0/4 ama 60dk 4/6, 240dk 4/5).
-- ret_* = karar fiyatından (price_at_decision) itibaren % değişim (yönsüz, ham).
-- mfe/mae_60m = ilk 60 dk'da TAHMİN YÖNÜNE göre lehte/aleyhte maksimum hareket %
-- (nötr/choppy tahminlerde lehte=yukarı kabul edilir; okuma tarafı belgeli).
ALTER TABLE bias_test_log
  ADD COLUMN IF NOT EXISTS ret_10m  double precision,
  ADD COLUMN IF NOT EXISTS ret_30m  double precision,
  ADD COLUMN IF NOT EXISTS ret_60m  double precision,
  ADD COLUMN IF NOT EXISTS ret_240m double precision,
  ADD COLUMN IF NOT EXISTS mfe_60m  double precision,
  ADD COLUMN IF NOT EXISTS mae_60m  double precision,
  ADD COLUMN IF NOT EXISTS horizon_filled_at timestamp with time zone;

COMMENT ON COLUMN bias_test_log.ret_60m IS
  'Karar fiyatından +60dk ham % değişim (5m mum kapanışı; yön uygulanmamış)';
COMMENT ON COLUMN bias_test_log.mfe_60m IS
  'İlk 60dk tahmin yönünde lehte maksimum hareket % (nötr tahminde yukarı)';
COMMENT ON COLUMN bias_test_log.mae_60m IS
  'İlk 60dk tahmin yönüne karşı aleyhte maksimum hareket %';

-- Çift-yazar teşhisi/idempotensi sorguları için (tablo küçük ama kalıcı doğru):
CREATE INDEX IF NOT EXISTS idx_bias_test_log_date_label
  ON bias_test_log (ny_date, run_label);
