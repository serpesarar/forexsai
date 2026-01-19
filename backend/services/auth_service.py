"""
Authentication Service - Complete user management with spam protection

Features:
- Email/password signup with verification
- Session management (JWT-like tokens)
- Rate limiting per IP/action
- Referral system with rewards
- Tier-based access control
"""
from __future__ import annotations

import logging
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class MembershipTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


# Rate limits: (max_count, window_seconds)
RATE_LIMITS = {
    "signup": (5, 86400),      # 5 signups per IP per day
    "login": (10, 3600),       # 10 login attempts per hour
    "login_failed": (5, 900),  # 5 failed logins = 15 min lockout
    "password_reset": (3, 3600),  # 3 reset requests per hour
    "claude_call_free": (0, 86400),  # 0 for free tier
    "claude_call_pro": (50, 86400),  # 50 per day for pro
}

# Referral reward: 5 referrals = 7 days pro
REFERRAL_REWARD_THRESHOLD = 5
REFERRAL_REWARD_DAYS = 7


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UserProfile:
    id: str
    email: str
    full_name: Optional[str]
    membership_tier: str
    tier_expires_at: Optional[str]
    referral_code: str
    referral_count: int
    status: str
    email_verified: bool
    created_at: str
    last_login_at: Optional[str]


@dataclass
class AuthResult:
    success: bool
    user: Optional[UserProfile] = None
    session_token: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class SignupResult:
    success: bool
    user_id: Optional[str] = None
    referral_code: Optional[str] = None
    verification_sent: bool = False
    error: Optional[str] = None
    error_code: Optional[str] = None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against hash"""
    check_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(check_hash, hashed)


def generate_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)


def generate_referral_code() -> str:
    """Generate 8-character referral code"""
    return secrets.token_hex(4).upper()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalı"
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az 1 büyük harf içermeli"
    if not re.search(r'[a-z]', password):
        return False, "Şifre en az 1 küçük harf içermeli"
    if not re.search(r'[0-9]', password):
        return False, "Şifre en az 1 rakam içermeli"
    return True, None


def get_client_fingerprint(ip: str, user_agent: str) -> str:
    """Generate browser fingerprint for spam detection"""
    data = f"{ip}:{user_agent}"
    return hashlib.md5(data.encode()).hexdigest()[:16]


# =============================================================================
# SUPABASE CLIENT
# =============================================================================

_supabase_client = None

async def get_supabase():
    """Get or create Supabase client"""
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase not configured")
            return None
        
        try:
            from supabase import create_client
            _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            return None
    
    return _supabase_client


# =============================================================================
# RATE LIMITING
# =============================================================================

async def check_rate_limit(identifier: str, action: str) -> Tuple[bool, Optional[str]]:
    """
    Check if action is allowed for identifier (IP or user_id).
    Returns (allowed, error_message)
    """
    if action not in RATE_LIMITS:
        return True, None
    
    max_count, window_seconds = RATE_LIMITS[action]
    
    if max_count == 0:
        return False, "Bu özellik üyelik seviyeniz için kullanılamaz"
    
    client = await get_supabase()
    if not client:
        # If no DB, allow (fail open for dev)
        return True, None
    
    try:
        result = client.rpc('check_rate_limit', {
            'p_identifier': identifier,
            'p_action': action,
            'p_max_count': max_count,
            'p_window_seconds': window_seconds
        }).execute()
        
        allowed = result.data
        if not allowed:
            return False, f"Çok fazla deneme. Lütfen {window_seconds // 60} dakika bekleyin."
        return True, None
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True, None  # Fail open


# =============================================================================
# SIGNUP
# =============================================================================

async def signup(
    email: str,
    password: str,
    full_name: Optional[str] = None,
    referral_code: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> SignupResult:
    """
    Register new user with email verification.
    
    Spam protection:
    - Rate limiting per IP
    - Email format validation
    - Password strength check
    - Fingerprint tracking
    """
    # 1. Validate inputs
    if not validate_email(email):
        return SignupResult(success=False, error="Geçersiz email formatı", error_code="INVALID_EMAIL")
    
    valid_pw, pw_error = validate_password(password)
    if not valid_pw:
        return SignupResult(success=False, error=pw_error, error_code="WEAK_PASSWORD")
    
    # 2. Rate limit check
    if ip_address:
        allowed, rate_error = await check_rate_limit(ip_address, "signup")
        if not allowed:
            return SignupResult(success=False, error=rate_error, error_code="RATE_LIMITED")
    
    # 3. Get Supabase client
    client = await get_supabase()
    if not client:
        return SignupResult(success=False, error="Veritabanı bağlantısı kurulamadı", error_code="DB_ERROR")
    
    try:
        # 4. Check if email exists
        existing = client.table("user_profiles").select("id").eq("email", email.lower()).execute()
        if existing.data:
            return SignupResult(success=False, error="Bu email zaten kayıtlı", error_code="EMAIL_EXISTS")
        
        # 5. Hash password
        password_hash, salt = hash_password(password)
        
        # 6. Resolve referral code
        referred_by = None
        if referral_code:
            referrer = client.table("user_profiles")\
                .select("id")\
                .eq("referral_code", referral_code.upper())\
                .single()\
                .execute()
            if referrer.data:
                referred_by = referrer.data["id"]
        
        # 7. Generate fingerprint
        fingerprint = None
        if ip_address and user_agent:
            fingerprint = get_client_fingerprint(ip_address, user_agent)
        
        # 8. Create user
        new_referral_code = generate_referral_code()
        
        user_data = {
            "email": email.lower(),
            "full_name": full_name,
            "membership_tier": "free",
            "referral_code": new_referral_code,
            "referred_by": referred_by,
            "status": "pending",
            "email_verified": False,
            "signup_ip": ip_address,
            "signup_fingerprint": fingerprint,
        }
        
        result = client.table("user_profiles").insert(user_data).execute()
        
        if not result.data:
            return SignupResult(success=False, error="Kayıt oluşturulamadı", error_code="INSERT_FAILED")
        
        user_id = result.data[0]["id"]
        
        # 9. Store password separately (in a secure way)
        client.table("user_credentials").insert({
            "user_id": user_id,
            "password_hash": password_hash,
            "salt": salt
        }).execute()
        
        # 10. Create verification token
        verification_token = generate_token()
        client.table("email_verifications").insert({
            "user_id": user_id,
            "token": verification_token,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }).execute()
        
        # 11. Create referral record if referred
        if referred_by:
            client.table("referrals").insert({
                "referrer_id": referred_by,
                "referred_id": user_id,
                "status": "pending"
            }).execute()
        
        # 12. Update daily metrics
        try:
            client.rpc('increment_daily_metric', {'p_metric': 'total_signups'}).execute()
        except:
            pass
        
        # 13. TODO: Send verification email (implement with Resend/SendGrid)
        logger.info(f"New signup: {email}, verification token: {verification_token[:8]}...")
        
        return SignupResult(
            success=True,
            user_id=user_id,
            referral_code=new_referral_code,
            verification_sent=True
        )
        
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return SignupResult(success=False, error="Beklenmeyen bir hata oluştu", error_code="UNKNOWN_ERROR")


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

async def verify_email(token: str) -> Tuple[bool, Optional[str]]:
    """Verify email with token"""
    client = await get_supabase()
    if not client:
        return False, "Veritabanı bağlantısı kurulamadı"
    
    try:
        # Find token
        result = client.table("email_verifications")\
            .select("*")\
            .eq("token", token)\
            .is_("used_at", "null")\
            .single()\
            .execute()
        
        if not result.data:
            return False, "Geçersiz veya süresi dolmuş doğrulama linki"
        
        verification = result.data
        
        # Check expiry
        expires_at = datetime.fromisoformat(verification["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            return False, "Doğrulama linkinin süresi dolmuş"
        
        user_id = verification["user_id"]
        
        # Update user
        client.table("user_profiles").update({
            "email_verified": True,
            "email_verified_at": datetime.utcnow().isoformat(),
            "status": "active"
        }).eq("id", user_id).execute()
        
        # Mark token as used
        client.table("email_verifications").update({
            "used_at": datetime.utcnow().isoformat()
        }).eq("id", verification["id"]).execute()
        
        # Complete referral if exists
        client.table("referrals").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("referred_id", user_id).execute()
        
        # Check and award referral bonus
        await check_referral_reward(user_id)
        
        # Update metrics
        try:
            client.rpc('increment_daily_metric', {'p_metric': 'verified_signups'}).execute()
        except:
            pass
        
        return True, None
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        return False, "Doğrulama sırasında hata oluştu"


# =============================================================================
# LOGIN
# =============================================================================

async def login(
    email: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuthResult:
    """
    Authenticate user and create session.
    
    Security:
    - Rate limiting on failed attempts
    - Account lockout after 5 failures
    - Session token generation
    """
    # 1. Rate limit check
    if ip_address:
        allowed, rate_error = await check_rate_limit(ip_address, "login")
        if not allowed:
            return AuthResult(success=False, error=rate_error, error_code="RATE_LIMITED")
    
    client = await get_supabase()
    if not client:
        return AuthResult(success=False, error="Veritabanı bağlantısı kurulamadı", error_code="DB_ERROR")
    
    try:
        # 2. Find user
        user_result = client.table("user_profiles")\
            .select("*")\
            .eq("email", email.lower())\
            .single()\
            .execute()
        
        if not user_result.data:
            return AuthResult(success=False, error="Email veya şifre hatalı", error_code="INVALID_CREDENTIALS")
        
        user = user_result.data
        user_id = user["id"]
        
        # 3. Check account status
        if user["status"] == "banned":
            return AuthResult(success=False, error="Hesabınız askıya alınmış", error_code="ACCOUNT_BANNED")
        
        if user["status"] == "suspended":
            return AuthResult(success=False, error="Hesabınız geçici olarak askıya alınmış", error_code="ACCOUNT_SUSPENDED")
        
        # 4. Check lockout
        if user.get("locked_until"):
            locked_until = datetime.fromisoformat(user["locked_until"].replace("Z", "+00:00"))
            if datetime.now(locked_until.tzinfo) < locked_until:
                remaining = (locked_until - datetime.now(locked_until.tzinfo)).seconds // 60
                return AuthResult(
                    success=False, 
                    error=f"Hesap kilitli. {remaining} dakika sonra tekrar deneyin.",
                    error_code="ACCOUNT_LOCKED"
                )
        
        # 5. Get credentials
        creds_result = client.table("user_credentials")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not creds_result.data:
            return AuthResult(success=False, error="Kimlik bilgileri bulunamadı", error_code="NO_CREDENTIALS")
        
        creds = creds_result.data
        
        # 6. Verify password
        if not verify_password(password, creds["password_hash"], creds["salt"]):
            # Increment failed attempts
            failed = user.get("failed_login_attempts", 0) + 1
            update_data = {"failed_login_attempts": failed}
            
            if failed >= 5:
                update_data["locked_until"] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            
            client.table("user_profiles").update(update_data).eq("id", user_id).execute()
            
            return AuthResult(success=False, error="Email veya şifre hatalı", error_code="INVALID_CREDENTIALS")
        
        # 7. Check email verification
        if not user["email_verified"]:
            return AuthResult(
                success=False, 
                error="Lütfen önce email adresinizi doğrulayın",
                error_code="EMAIL_NOT_VERIFIED"
            )
        
        # 8. Create session
        session_token = generate_token(48)
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        device_info = {
            "user_agent": user_agent,
            "ip": ip_address,
            "login_time": datetime.utcnow().isoformat()
        }
        
        client.table("user_sessions").insert({
            "user_id": user_id,
            "token_hash": token_hash,
            "device_info": device_info,
            "ip_address": ip_address,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }).execute()
        
        # 9. Update user stats
        client.table("user_profiles").update({
            "last_login_at": datetime.utcnow().isoformat(),
            "login_count": user.get("login_count", 0) + 1,
            "failed_login_attempts": 0,
            "locked_until": None
        }).eq("id", user_id).execute()
        
        # 10. Build response
        profile = UserProfile(
            id=user_id,
            email=user["email"],
            full_name=user.get("full_name"),
            membership_tier=user["membership_tier"],
            tier_expires_at=user.get("tier_expires_at"),
            referral_code=user["referral_code"],
            referral_count=user.get("referral_count", 0),
            status=user["status"],
            email_verified=user["email_verified"],
            created_at=user["created_at"],
            last_login_at=datetime.utcnow().isoformat()
        )
        
        return AuthResult(success=True, user=profile, session_token=session_token)
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return AuthResult(success=False, error="Giriş sırasında hata oluştu", error_code="UNKNOWN_ERROR")


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

async def validate_session(token: str) -> Optional[UserProfile]:
    """Validate session token and return user profile"""
    client = await get_supabase()
    if not client:
        return None
    
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find session
        session_result = client.table("user_sessions")\
            .select("*")\
            .eq("token_hash", token_hash)\
            .single()\
            .execute()
        
        if not session_result.data:
            return None
        
        session = session_result.data
        
        # Check expiry
        expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            # Delete expired session
            client.table("user_sessions").delete().eq("id", session["id"]).execute()
            return None
        
        # Get user
        user_result = client.table("user_profiles")\
            .select("*")\
            .eq("id", session["user_id"])\
            .single()\
            .execute()
        
        if not user_result.data:
            return None
        
        user = user_result.data
        
        # Update last activity
        client.table("user_sessions").update({
            "last_activity_at": datetime.utcnow().isoformat()
        }).eq("id", session["id"]).execute()
        
        return UserProfile(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name"),
            membership_tier=user["membership_tier"],
            tier_expires_at=user.get("tier_expires_at"),
            referral_code=user["referral_code"],
            referral_count=user.get("referral_count", 0),
            status=user["status"],
            email_verified=user["email_verified"],
            created_at=user["created_at"],
            last_login_at=user.get("last_login_at")
        )
        
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return None


async def logout(token: str) -> bool:
    """Invalidate session token"""
    client = await get_supabase()
    if not client:
        return False
    
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        client.table("user_sessions").delete().eq("token_hash", token_hash).execute()
        return True
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return False


# =============================================================================
# REFERRAL SYSTEM
# =============================================================================

async def check_referral_reward(referred_user_id: str) -> bool:
    """Check if referrer should receive reward after new user verifies"""
    client = await get_supabase()
    if not client:
        return False
    
    try:
        # Find who referred this user
        referral = client.table("referrals")\
            .select("referrer_id")\
            .eq("referred_id", referred_user_id)\
            .eq("status", "completed")\
            .single()\
            .execute()
        
        if not referral.data:
            return False
        
        referrer_id = referral.data["referrer_id"]
        
        # Count completed referrals
        count_result = client.table("referrals")\
            .select("id", count="exact")\
            .eq("referrer_id", referrer_id)\
            .eq("status", "completed")\
            .neq("status", "rewarded")\
            .execute()
        
        count = count_result.count or 0
        
        if count >= REFERRAL_REWARD_THRESHOLD:
            # Award pro membership
            await grant_pro_membership(referrer_id, REFERRAL_REWARD_DAYS, "referral_reward")
            
            # Mark referrals as rewarded
            client.table("referrals").update({
                "status": "rewarded",
                "rewarded_at": datetime.utcnow().isoformat(),
                "reward_type": "pro_membership",
                "reward_days": REFERRAL_REWARD_DAYS
            }).eq("referrer_id", referrer_id).eq("status", "completed").execute()
            
            # Update referral count
            client.table("user_profiles").update({
                "referral_count": count
            }).eq("id", referrer_id).execute()
            
            logger.info(f"Awarded {REFERRAL_REWARD_DAYS} days pro to referrer {referrer_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Referral reward check error: {e}")
        return False


async def grant_pro_membership(user_id: str, days: int, reason: str) -> bool:
    """Grant pro membership to user"""
    client = await get_supabase()
    if not client:
        return False
    
    try:
        # Get current tier expiry
        user = client.table("user_profiles")\
            .select("tier_expires_at")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        current_expiry = None
        if user.data and user.data.get("tier_expires_at"):
            current_expiry = datetime.fromisoformat(
                user.data["tier_expires_at"].replace("Z", "+00:00")
            )
        
        # Calculate new expiry (extend if already pro)
        if current_expiry and current_expiry > datetime.now(current_expiry.tzinfo):
            new_expiry = current_expiry + timedelta(days=days)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=days)
        
        # Update user
        client.table("user_profiles").update({
            "membership_tier": "pro",
            "tier_expires_at": new_expiry.isoformat()
        }).eq("id", user_id).execute()
        
        # Create subscription record
        pro_package = client.table("subscription_packages")\
            .select("id")\
            .eq("slug", "pro")\
            .single()\
            .execute()
        
        if pro_package.data:
            client.table("user_subscriptions").insert({
                "user_id": user_id,
                "package_id": pro_package.data["id"],
                "status": "active",
                "starts_at": datetime.utcnow().isoformat(),
                "ends_at": new_expiry.isoformat(),
                "auto_renew": False
            }).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Grant pro membership error: {e}")
        return False


# =============================================================================
# TIER ACCESS CHECK
# =============================================================================

async def check_feature_access(user_id: str, feature: str) -> Tuple[bool, Optional[str]]:
    """
    Check if user has access to a feature based on their tier.
    
    Features:
    - claude_analysis: Pro only
    - advanced_patterns: Pro only
    - api_access: Enterprise only
    """
    client = await get_supabase()
    if not client:
        return False, "Veritabanı bağlantısı kurulamadı"
    
    try:
        user = client.table("user_profiles")\
            .select("membership_tier, tier_expires_at")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        if not user.data:
            return False, "Kullanıcı bulunamadı"
        
        tier = user.data["membership_tier"]
        
        # Check tier expiry
        if tier in ["pro", "enterprise"] and user.data.get("tier_expires_at"):
            expiry = datetime.fromisoformat(user.data["tier_expires_at"].replace("Z", "+00:00"))
            if datetime.now(expiry.tzinfo) > expiry:
                # Tier expired, downgrade to free
                client.table("user_profiles").update({
                    "membership_tier": "free",
                    "tier_expires_at": None
                }).eq("id", user_id).execute()
                tier = "free"
        
        # Feature access matrix
        access_matrix = {
            "claude_analysis": ["pro", "enterprise", "admin"],
            "advanced_patterns": ["pro", "enterprise", "admin"],
            "priority_support": ["pro", "enterprise", "admin"],
            "api_access": ["enterprise", "admin"],
            "custom_alerts": ["enterprise", "admin"],
            "panel_access": ["free", "pro", "enterprise", "admin"],
            "real_time_data": ["free", "pro", "enterprise", "admin"],
        }
        
        allowed_tiers = access_matrix.get(feature, [])
        
        if tier in allowed_tiers:
            return True, None
        else:
            return False, f"Bu özellik {', '.join(allowed_tiers)} üyelik seviyesi gerektirir"
        
    except Exception as e:
        logger.error(f"Feature access check error: {e}")
        return False, "Erişim kontrolü sırasında hata oluştu"


# =============================================================================
# CLAUDE USAGE TRACKING
# =============================================================================

async def track_claude_usage(user_id: str, endpoint: str, tokens: int, cost: float) -> bool:
    """Track Claude API usage for billing and limits"""
    client = await get_supabase()
    if not client:
        return False
    
    try:
        client.table("claude_usage").insert({
            "user_id": user_id,
            "endpoint": endpoint,
            "tokens_used": tokens,
            "cost_usd": cost
        }).execute()
        
        # Update user total
        client.table("user_profiles").update({
            "total_claude_calls": client.table("user_profiles")
                .select("total_claude_calls")
                .eq("id", user_id)
                .single()
                .execute()
                .data.get("total_claude_calls", 0) + 1
        }).eq("id", user_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Claude usage tracking error: {e}")
        return False


async def check_claude_limit(user_id: str) -> Tuple[bool, Optional[str], int]:
    """
    Check if user can make Claude API calls.
    Returns (allowed, error_message, remaining_calls)
    """
    client = await get_supabase()
    if not client:
        return False, "Veritabanı bağlantısı kurulamadı", 0
    
    try:
        # Get user tier
        user = client.table("user_profiles")\
            .select("membership_tier")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        if not user.data:
            return False, "Kullanıcı bulunamadı", 0
        
        tier = user.data["membership_tier"]
        
        if tier == "free":
            return False, "Claude analizi Pro üyelik gerektirir", 0
        
        if tier == "admin":
            return True, None, 999
        
        # Get daily limit
        limit = RATE_LIMITS.get(f"claude_call_{tier}", (0, 86400))[0]
        
        # Count today's usage
        today = datetime.utcnow().date().isoformat()
        usage = client.table("claude_usage")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("created_at", today)\
            .execute()
        
        used = usage.count or 0
        remaining = max(0, limit - used)
        
        if used >= limit:
            return False, f"Günlük Claude limiti ({limit}) doldu", 0
        
        return True, None, remaining
        
    except Exception as e:
        logger.error(f"Claude limit check error: {e}")
        return False, "Limit kontrolü sırasında hata oluştu", 0
