-- ============================================================
-- SQL UPDATE SCRIPT - Pulse Integration & User Reports
-- Bu komutları Supabase SQL Editor üzerinden çalıştırın.
-- ============================================================

-- 1. Pulse ve EMEL sinyallerini ayırt etmek için 'strategy' kolonu ekleyin
ALTER TABLE prediction_logs 
ADD COLUMN IF NOT EXISTS strategy VARCHAR(32);

-- İndeks ekleyelim (sorgulama performansı için)
CREATE INDEX IF NOT EXISTS idx_prediction_logs_strategy ON prediction_logs(strategy);

-- 2. Kullanıcı geri bildirimleri için tablo oluşturun
CREATE TABLE IF NOT EXISTS user_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Kullanıcı bilgisi (opsiyonel)
    user_id UUID,
    email VARCHAR(255),
    
    -- Rapor detayları
    type VARCHAR(32) NOT NULL, -- 'bug', 'feature', 'other'
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Ek teknik detaylar (browser, os vb.)
    
    -- Durum takibi
    status VARCHAR(32) DEFAULT 'pending', -- 'pending', 'in_progress', 'resolved', 'closed'
    admin_notes TEXT,
    
    CONSTRAINT valid_report_type CHECK (type IN ('bug', 'feature', 'other')),
    CONSTRAINT valid_report_status CHECK (status IN ('pending', 'in_progress', 'resolved', 'closed'))
);

CREATE INDEX IF NOT EXISTS idx_user_reports_status ON user_reports(status);
CREATE INDEX IF NOT EXISTS idx_user_reports_created_at ON user_reports(created_at DESC);

-- 3. (Opsiyonel) Signal Source kolonu - İleride farklı kaynaklar için
ALTER TABLE prediction_logs 
ADD COLUMN IF NOT EXISTS signal_source VARCHAR(64);
