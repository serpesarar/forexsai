-- =============================================================================
-- MEMBERSHIP SYSTEM - Complete Auth & Subscription Schema
-- =============================================================================

-- 1. USERS PROFILE TABLE (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    
    -- Membership
    membership_tier TEXT DEFAULT 'free' CHECK (membership_tier IN ('free', 'pro', 'enterprise', 'admin')),
    tier_expires_at TIMESTAMPTZ,
    
    -- Referral System
    referral_code TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(4), 'hex'),
    referred_by UUID REFERENCES user_profiles(id),
    referral_count INT DEFAULT 0,
    
    -- Status & Security
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'banned')),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,
    
    -- Spam Protection
    signup_ip TEXT,
    signup_fingerprint TEXT,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMPTZ,
    
    -- Analytics
    last_login_at TIMESTAMPTZ,
    login_count INT DEFAULT 0,
    total_claude_calls INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. EMAIL VERIFICATION TOKENS
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. PASSWORD RESET TOKENS
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '1 hour'),
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SESSIONS TABLE
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL,
    device_info JSONB,
    ip_address TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. SUBSCRIPTION PACKAGES
CREATE TABLE IF NOT EXISTS subscription_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    
    -- Features (JSON for flexibility)
    features JSONB DEFAULT '{}',
    max_claude_calls_daily INT,
    max_claude_calls_monthly INT,
    
    -- Display
    is_popular BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. USER SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    package_id UUID REFERENCES subscription_packages(id),
    
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    
    -- Payment
    stripe_subscription_id TEXT,
    stripe_customer_id TEXT,
    
    -- Auto-renew
    auto_renew BOOLEAN DEFAULT TRUE,
    cancelled_at TIMESTAMPTZ,
    cancel_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. REFERRALS TRACKING
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL REFERENCES user_profiles(id),
    referred_id UUID UNIQUE NOT NULL REFERENCES user_profiles(id),
    
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rewarded')),
    reward_type TEXT,
    reward_days INT,
    
    completed_at TIMESTAMPTZ,
    rewarded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. RATE LIMITING TABLE
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL, -- IP or user_id
    action TEXT NOT NULL, -- 'signup', 'login', 'claude_call', etc.
    count INT DEFAULT 1,
    window_start TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(identifier, action)
);

-- 9. CLAUDE USAGE TRACKING
CREATE TABLE IF NOT EXISTS claude_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. DAILY METRICS (Admin Dashboard)
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    total_signups INT DEFAULT 0,
    verified_signups INT DEFAULT 0,
    active_users INT DEFAULT 0,
    pro_upgrades INT DEFAULT 0,
    referrals_completed INT DEFAULT 0,
    claude_calls INT DEFAULT 0,
    revenue_usd DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_referral_code ON user_profiles(referral_code);
CREATE INDEX IF NOT EXISTS idx_user_profiles_status ON user_profiles(status);
CREATE INDEX IF NOT EXISTS idx_user_profiles_tier ON user_profiles(membership_tier);

CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);
CREATE INDEX IF NOT EXISTS idx_email_verifications_user ON email_verifications(user_id);

CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);

CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup ON rate_limits(identifier, action, window_start);

CREATE INDEX IF NOT EXISTS idx_claude_usage_user ON claude_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_claude_usage_date ON claude_usage(created_at);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_usage ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
DROP TRIGGER IF EXISTS trigger_user_profiles_updated ON user_profiles;
CREATE TRIGGER trigger_user_profiles_updated
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_user_subscriptions_updated ON user_subscriptions;
CREATE TRIGGER trigger_user_subscriptions_updated
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to check rate limit
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
    
    -- Clean old entries
    DELETE FROM rate_limits 
    WHERE identifier = p_identifier 
    AND action = p_action 
    AND window_start < v_window_start;
    
    -- Get current count
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
$$ LANGUAGE plpgsql;

-- Function to increment daily metric
CREATE OR REPLACE FUNCTION increment_daily_metric(p_metric TEXT, p_value INT DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_metrics (date, total_signups)
    VALUES (CURRENT_DATE, 0)
    ON CONFLICT (date) DO NOTHING;
    
    EXECUTE format('UPDATE daily_metrics SET %I = %I + $1 WHERE date = CURRENT_DATE', p_metric, p_metric)
    USING p_value;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIAL DATA - Default Packages
-- =============================================================================

INSERT INTO subscription_packages (name, slug, description, price_monthly, price_yearly, features, max_claude_calls_daily, max_claude_calls_monthly, is_popular, display_order)
VALUES 
    ('Free', 'free', 'Temel özellikler ile başla', 0, 0, 
     '{"panel_access": true, "real_time_data": true, "basic_indicators": true, "claude_analysis": false}'::jsonb,
     0, 0, FALSE, 1),
    
    ('Pro', 'pro', 'Tüm özelliklere tam erişim', 29.99, 299.99,
     '{"panel_access": true, "real_time_data": true, "basic_indicators": true, "claude_analysis": true, "priority_support": true, "advanced_patterns": true}'::jsonb,
     50, 500, TRUE, 2),
    
    ('Enterprise', 'enterprise', 'Kurumsal çözümler', 99.99, 999.99,
     '{"panel_access": true, "real_time_data": true, "basic_indicators": true, "claude_analysis": true, "priority_support": true, "advanced_patterns": true, "api_access": true, "custom_alerts": true}'::jsonb,
     NULL, NULL, FALSE, 3)
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE user_profiles IS 'Extended user profiles with membership and referral data';
COMMENT ON TABLE email_verifications IS 'Email verification tokens for new signups';
COMMENT ON TABLE user_sessions IS 'Active user sessions with device tracking';
COMMENT ON TABLE subscription_packages IS 'Available subscription tiers';
COMMENT ON TABLE user_subscriptions IS 'User subscription history and status';
COMMENT ON TABLE referrals IS 'Referral tracking between users';
COMMENT ON TABLE rate_limits IS 'Rate limiting for API endpoints';
COMMENT ON TABLE claude_usage IS 'Claude API usage tracking per user';
COMMENT ON TABLE daily_metrics IS 'Daily aggregated metrics for admin dashboard';
