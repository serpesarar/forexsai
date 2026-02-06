-- Eski ve beklemedeki test verilerini temizleme scripti
-- 1 Şubat 2026 öncesindeki tüm kayıtları siler

BEGIN;

-- 1. Eski Logları Sil
DELETE FROM prediction_logs 
WHERE created_at < '2026-02-01 00:00:00';

-- 2. Sonuçları Görüntüle
SELECT COUNT(*) as remaining_logs FROM prediction_logs;

COMMIT;
