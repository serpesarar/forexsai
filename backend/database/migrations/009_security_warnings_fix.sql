-- Security Warnings Fix Migration
-- Fixes function search_path and overly permissive RLS policies

-- ============================================
-- 1. FIX FUNCTION SEARCH_PATH ISSUES
-- Set explicit search_path for security
-- ============================================

-- Fix update_updated_at_column function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Fix handle_new_user function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, created_at)
    VALUES (NEW.id, NEW.email, NOW())
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

-- Fix check_referral_reward function
CREATE OR REPLACE FUNCTION public.check_referral_reward()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
    -- Check if referrer exists and reward them
    IF NEW.referred_by IS NOT NULL THEN
        UPDATE public.profiles
        SET referral_credits = COALESCE(referral_credits, 0) + 1
        WHERE id = NEW.referred_by;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================
-- 2. FIX OVERLY PERMISSIVE RLS POLICY
-- Replace "allow all" with proper policies
-- ============================================

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "Allow all operations on failure_analyses" ON public.failure_analyses;

-- Enable RLS if not already enabled
ALTER TABLE public.failure_analyses ENABLE ROW LEVEL SECURITY;

-- Create proper policies: public read, service write
CREATE POLICY "Allow public read on failure_analyses" 
    ON public.failure_analyses 
    FOR SELECT 
    USING (true);

CREATE POLICY "Allow service write on failure_analyses" 
    ON public.failure_analyses 
    FOR INSERT 
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service update on failure_analyses" 
    ON public.failure_analyses 
    FOR UPDATE 
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service delete on failure_analyses" 
    ON public.failure_analyses 
    FOR DELETE 
    USING (auth.role() = 'service_role');

-- ============================================
-- DONE: All warnings fixed
-- ============================================
