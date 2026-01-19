-- =============================================================================
-- OPTIMIZED MEMBERSHIP SYSTEM - Supabase Production Ready v2
-- =============================================================================
-- Bu şema Supabase Auth ile tam entegre çalışır
-- Gereksiz tablolar kaldırıldı (email_verifications, password_resets, user_sessions)
-- Tüm tablolarda RLS aktif
-- =============================================================================

-- 1. USER PROFILES (Supabase Auth ile entegre)
CREATE TABLE IF NOT EXISTS user_profiles (
    -- Supabase Auth ile doğrudan bağlantı
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Temel Bilgiler
    full_name TEXT,
    avatar_url TEXT,
    
    -- Membership (Beta döneminde herkes free ama tüm özelliklere erişebilir)
    membership_tier TEXT DEFAULT 'free' CHECK (membership_tier IN ('free', 'pro', 'enterprise', 'admin')),
    tier_expires_at TIMESTAMPTZ,
    is_beta_user BOOLEAN DEFAULT TRUE, -- Beta kullanıcıları tüm özelliklere erişir
    
    -- Referral System
    referral_code TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(4), 'hex'),
    referred_by UUID REFERENCES user_profiles(id),
    
    -- Analytics
    last_login_at TIMESTAMPTZ,
    login_count INT DEFAULT 0,
    
    -- Security (GDPR uyumlu - IP hash'lenmiş)
    signup_ip_hash TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_user_profiles_referral ON user_profiles(referral_code);
CREATE INDEX IF NOT EXISTS idx_user_profiles_tier ON user_profiles(membership_tier);
CREATE INDEX IF NOT EXISTS idx_user_profiles_beta ON user_profiles(is_beta_user);

-- RLS Policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Public can view referral codes" ON user_profiles;
CREATE POLICY "Public can view referral codes" ON user_profiles
  FOR SELECT USING (true);

-- =============================================================================

-- 2. SUBSCRIPTION PACKAGES
CREATE TABLE IF NOT EXISTS subscription_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    
    -- Pricing (Yakında belirlenecek)
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    
    -- Limits
    max_claude_calls_daily INT,
    max_claude_calls_monthly INT,
    
    -- Features (JSONB)
    features JSONB DEFAULT '{}',
    
    -- Display
    is_popular BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Herkes paketleri görebilir
ALTER TABLE subscription_packages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can view packages" ON subscription_packages;
CREATE POLICY "Anyone can view packages" ON subscription_packages
  FOR SELECT USING (is_active = TRUE);

-- =============================================================================

-- 3. USER SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    package_id UUID REFERENCES subscription_packages(id),
    
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'trial', 'beta')),
    
    -- Tarihler
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    
    -- Stripe (İleride kullanılacak)
    stripe_subscription_id TEXT,
    stripe_customer_id TEXT,
    
    -- Cancellation
    auto_renew BOOLEAN DEFAULT TRUE,
    cancelled_at TIMESTAMPTZ,
    cancel_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_user_subs_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subs_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subs_ends_at ON user_subscriptions(ends_at);

-- RLS
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own subscription" ON user_subscriptions;
CREATE POLICY "Users can view own subscription" ON user_subscriptions
  FOR SELECT USING (auth.uid() = user_id);

-- =============================================================================

-- 4. REFERRALS (Sadeleştirilmiş)
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL REFERENCES user_profiles(id),
    referred_id UUID UNIQUE NOT NULL REFERENCES user_profiles(id),
    
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rewarded')),
    reward_days INT DEFAULT 7, -- 1 hafta bonus
    
    completed_at TIMESTAMPTZ,
    rewarded_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);

-- RLS
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own referrals" ON referrals;
CREATE POLICY "Users can view own referrals" ON referrals
  FOR SELECT USING (auth.uid() = referrer_id OR auth.uid() = referred_id);

-- =============================================================================

-- 5. CLAUDE USAGE (Detaylı Maliyet Takibi)
CREATE TABLE IF NOT EXISTS claude_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Request detayları
    request_id TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(16), 'hex'),
    endpoint TEXT NOT NULL, -- "analyze_news", "generate_signal"
    model TEXT DEFAULT 'claude-3-5-sonnet-20241022',
    
    -- Token & Maliyet
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
    
    -- Cache
    is_cached BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_claude_usage_user ON claude_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_claude_usage_date ON claude_usage(created_at);

-- RLS
ALTER TABLE claude_usage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own usage" ON claude_usage;
CREATE POLICY "Users can view own usage" ON claude_usage
  FOR SELECT USING (auth.uid() = user_id);

-- =============================================================================

-- 6. DAILY METRICS (Admin Dashboard)
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    
    -- Kullanıcılar
    total_signups INT DEFAULT 0,
    active_users INT DEFAULT 0,
    
    -- Subscription
    pro_upgrades INT DEFAULT 0,
    
    -- Referral
    referrals_completed INT DEFAULT 0,
    
    -- Usage
    claude_calls_total INT DEFAULT 0,
    claude_cost_total DECIMAL(10,2) DEFAULT 0,
    
    -- Revenue (İleride)
    revenue_usd DECIMAL(12,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Sadece admin görebilir
ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Only admin can view metrics" ON daily_metrics;
CREATE POLICY "Only admin can view metrics" ON daily_metrics
  FOR SELECT USING (
    auth.uid() IN (SELECT id FROM user_profiles WHERE membership_tier = 'admin')
  );

-- =============================================================================

-- 7. RATE LIMITS (Basit, DB-based - küçük ölçek için yeterli)
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL, -- IP hash veya user_id
    action TEXT NOT NULL, -- 'signup', 'login', 'claude_call'
    count INT DEFAULT 1,
    window_start TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(identifier, action)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup ON rate_limits(identifier, action, window_start);

-- =============================================================================
-- TRIGGERS & FUNCTIONS
-- =============================================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_user_profiles_updated ON user_profiles;
CREATE TRIGGER trigger_user_profiles_updated
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_user_subscriptions_updated ON user_subscriptions;
CREATE TRIGGER trigger_user_subscriptions_updated
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================

-- Yeni kullanıcı oluşturulunca profile oluştur (Auth Hook)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, membership_tier, is_beta_user)
  VALUES (NEW.id, 'free', TRUE)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Auth trigger (eğer yoksa oluştur)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================

-- 5 Referral tamamlanınca reward ver
CREATE OR REPLACE FUNCTION check_referral_reward()
RETURNS TRIGGER AS $$
DECLARE
  v_completed_count INT;
BEGIN
  IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status = 'pending') THEN
    -- Kaç tane tamamlanmış ve ödüllendirilmemiş referral var?
    SELECT COUNT(*) INTO v_completed_count
    FROM referrals
    WHERE referrer_id = NEW.referrer_id
      AND status = 'completed'
      AND rewarded_at IS NULL;
    
    -- 5 veya daha fazla ise reward ver
    IF v_completed_count >= 5 THEN
      -- User'ın tier_expires_at'ını 7 gün uzat
      UPDATE user_profiles 
      SET tier_expires_at = COALESCE(tier_expires_at, NOW()) + INTERVAL '7 days',
          membership_tier = CASE WHEN membership_tier = 'free' THEN 'pro' ELSE membership_tier END
      WHERE id = NEW.referrer_id;
      
      -- İlk 5 referral'ı rewarded olarak işaretle
      UPDATE referrals 
      SET rewarded_at = NOW(), status = 'rewarded'
      WHERE referrer_id = NEW.referrer_id 
        AND status = 'completed' 
        AND rewarded_at IS NULL
      ORDER BY created_at
      LIMIT 5;
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS referral_reward_checker ON referrals;
CREATE TRIGGER referral_reward_checker
  AFTER INSERT OR UPDATE ON referrals
  FOR EACH ROW EXECUTE FUNCTION check_referral_reward();

-- =============================================================================

-- Rate limit kontrolü (basit versiyon)
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_identifier TEXT,
    p_action TEXT,
    p_max_count INT,
    p_window_seconds INT
) RETURNS BOOLEAN AS $$
DECLARE
    v_count INT;
    v_window_start TIMESTAMPTZ;
BEGIN
    v_window_start := NOW() - (p_window_seconds || ' seconds')::INTERVAL;
    
    -- Eski kayıtları temizle
    DELETE FROM rate_limits 
    WHERE identifier = p_identifier 
    AND action = p_action 
    AND window_start < v_window_start;
    
    -- Mevcut sayıyı al
    SELECT count INTO v_count 
    FROM rate_limits 
    WHERE identifier = p_identifier 
    AND action = p_action 
    AND window_start >= v_window_start;
    
    IF v_count IS NULL THEN
        INSERT INTO rate_limits (identifier, action, count, window_start)
        VALUES (p_identifier, p_action, 1, NOW());
        RETURN TRUE;
    ELSIF v_count >= p_max_count THEN
        RETURN FALSE;
    ELSE
        UPDATE rate_limits 
        SET count = count + 1 
        WHERE identifier = p_identifier 
        AND action = p_action;
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================

-- Günlük Claude kullanımını kontrol et (Beta'da sınırsız, sonra limit olacak)
CREATE OR REPLACE FUNCTION get_user_claude_usage_today(p_user_id UUID)
RETURNS INT AS $$
DECLARE
    v_count INT;
    v_is_beta BOOLEAN;
BEGIN
    -- Beta kullanıcısı mı kontrol et
    SELECT is_beta_user INTO v_is_beta FROM user_profiles WHERE id = p_user_id;
    
    -- Beta kullanıcıları için sınırsız (9999 döndür - limit yok gibi)
    IF v_is_beta = TRUE THEN
        RETURN 0;
    END IF;
    
    -- Normal kullanıcılar için bugünkü kullanımı say
    SELECT COUNT(*) INTO v_count
    FROM claude_usage
    WHERE user_id = p_user_id
    AND created_at >= CURRENT_DATE;
    
    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Paketler (Fiyatlar yakında belirlenecek)
INSERT INTO subscription_packages (name, slug, description, price_monthly, price_yearly, max_claude_calls_daily, features, is_popular, display_order)
VALUES 
  ('Free', 'free', 'Temel özellikler', NULL, NULL, 5, 
   '{"panel_access": true, "basic_indicators": true}'::jsonb, FALSE, 1),
  ('Pro', 'pro', 'Tüm özelliklere erişim', NULL, NULL, 50, 
   '{"panel_access": true, "basic_indicators": true, "claude_analysis": true, "advanced_patterns": true}'::jsonb, TRUE, 2),
  ('Enterprise', 'enterprise', 'Kurumsal çözümler', NULL, NULL, NULL, 
   '{"panel_access": true, "basic_indicators": true, "claude_analysis": true, "advanced_patterns": true, "api_access": true, "priority_support": true}'::jsonb, FALSE, 3)
ON CONFLICT (slug) DO UPDATE SET
  description = EXCLUDED.description,
  features = EXCLUDED.features,
  max_claude_calls_daily = EXCLUDED.max_claude_calls_daily;

-- =============================================================================
-- ADMIN VIEW (İstatistikler için)
-- =============================================================================

CREATE OR REPLACE VIEW admin_dashboard AS
SELECT
  (SELECT COUNT(*) FROM user_profiles) as total_users,
  (SELECT COUNT(*) FROM user_profiles WHERE is_beta_user = TRUE) as beta_users,
  (SELECT COUNT(*) FROM user_profiles WHERE created_at >= CURRENT_DATE) as today_signups,
  (SELECT COUNT(*) FROM referrals WHERE status = 'completed') as total_referrals,
  (SELECT COALESCE(SUM(cost_usd), 0) FROM claude_usage WHERE created_at >= NOW() - INTERVAL '30 days') as monthly_claude_cost,
  (SELECT COUNT(*) FROM claude_usage WHERE created_at >= CURRENT_DATE) as today_claude_calls;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE user_profiles IS 'User profiles linked to Supabase Auth - Beta users have full access';
COMMENT ON TABLE subscription_packages IS 'Subscription tiers - prices TBD';
COMMENT ON TABLE user_subscriptions IS 'User subscription history';
COMMENT ON TABLE referrals IS 'Referral tracking - 5 referrals = 7 days bonus';
COMMENT ON TABLE claude_usage IS 'Claude API usage tracking with cost';
COMMENT ON TABLE daily_metrics IS 'Daily aggregated metrics for admin';
COMMENT ON TABLE rate_limits IS 'Simple rate limiting';

-- =============================================================================
-- DONE! 
-- Beta döneminde tüm kullanıcılar is_beta_user=TRUE ile oluşturulur
-- Bu sayede herkes tüm özelliklere erişebilir
-- Fiyatlandırma başladığında is_beta_user=FALSE yapılır
-- =============================================================================
