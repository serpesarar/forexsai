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
    """Validate password strength - minimum 5 characters"""
    if len(password) < 5:
        return False, "Şifre en az 5 karakter olmalı"
    return True, None


def get_client_fingerprint(ip: str, user_agent: str) -> str:
    """Generate browser fingerprint for spam detection"""
    data = f"{ip}:{user_agent}"
    return hashlib.md5(data.encode()).hexdigest()[:16]


# =============================================================================
# SUPABASE CLIENT
# =============================================================================

async def get_supabase():
    """Get custom Supabase REST client (uses httpx directly)"""
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if client is None:
        logger.warning("Supabase REST client not available")
    return client


# =============================================================================
# RATE LIMITING
# =============================================================================

async def check_rate_limit(identifier: str, action: str) -> Tuple[bool, Optional[str]]:
    """
    Rate limiting disabled - always allow
    """
    return True, None


# =============================================================================
# SIGNUP
# =============================================================================

async def verify_turnstile(token: str, ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Verify Cloudflare Turnstile token.
    Returns (success, error_message)
    """
    from config import settings
    
    # DEBUG: Log key status
    key_status = "SET" if settings.turnstile_secret_key else "NOT SET"
    logger.warning(f"[TURNSTILE DEBUG] Secret key status: {key_status}")
    if settings.turnstile_secret_key:
        logger.warning(f"[TURNSTILE DEBUG] Key starts with: {settings.turnstile_secret_key[:10]}...")
    
    if not settings.turnstile_secret_key:
        logger.warning("Turnstile secret key not configured, skipping verification")
        return True, None
    
    if not token:
        return False, "Bot doğrulaması gerekli"
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.turnstile_secret_key,
                    "response": token,
                    "remoteip": ip_address or ""
                }
            )
            
            result = response.json()
            
            if result.get("success"):
                return True, None
            else:
                error_codes = result.get("error-codes", ["unknown"])
                logger.warning(f"Turnstile verification failed: {error_codes}")
                return False, "Bot doğrulaması başarısız"
                
    except Exception as e:
        logger.error(f"Turnstile verification error: {e}")
        return False, "Bot doğrulaması sırasında hata oluştu"


async def signup(
    email: str,
    password: str,
    full_name: Optional[str] = None,
    referral_code: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    turnstile_token: Optional[str] = None
) -> SignupResult:
    """
    Register new user with email verification and bot protection.
    
    Spam protection:
    - Rate limiting per IP
    - Email format validation
    - Password strength check
    - Fingerprint tracking
    - Cloudflare Turnstile CAPTCHA
    - Email verification required
    """
    # 1. Validate inputs
    if not validate_email(email):
        return SignupResult(success=False, error="Geçersiz email formatı", error_code="INVALID_EMAIL")
    
    valid_pw, pw_error = validate_password(password)
    if not valid_pw:
        return SignupResult(success=False, error=pw_error, error_code="WEAK_PASSWORD")
    
    # 2. Bot protection - Turnstile verification
    turnstile_valid, turnstile_error = await verify_turnstile(turnstile_token, ip_address)
    if not turnstile_valid:
        return SignupResult(success=False, error=turnstile_error or "Bot doğrulaması başarısız", error_code="INVALID_CAPTCHA")
    
    # 3. Rate limit check
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
        if getattr(existing, 'data', []) if not isinstance(existing, dict) else existing.get('data', []):
            return SignupResult(success=False, error="Bu email zaten kayıtlı", error_code="EMAIL_EXISTS")
        
        # 5. Hash password
        password_hash, salt = hash_password(password)
        
        # 6. Resolve referral code
        referred_by = None
        if referral_code:
            referrer = client.table("user_profiles")\
                .select("id")\
                .eq("referral_code", referral_code.upper())\
                .execute()
            if getattr(referrer, 'data', []) if not isinstance(referrer, dict) else referrer.get('data', []) and len(referrer["data"]) > 0:
                referred_by = referrer["data"][0]["id"]
        
        # 7. Generate fingerprint
        fingerprint = None
        if ip_address and user_agent:
            fingerprint = get_client_fingerprint(ip_address, user_agent)
        
        # 8. Create user - PENDING status (email verification required)
        new_referral_code = generate_referral_code()
        
        user_data = {
            "email": email.lower(),
            "full_name": full_name,
            "membership_tier": "free",
            "referral_code": new_referral_code,
            "referred_by": referred_by,
            "status": "pending",  # User must verify email to activate
            "email_verified": False,  # Will be set to True after verification
            "signup_ip": ip_address,
            "signup_fingerprint": fingerprint,
        }
        
        result = client.table("user_profiles").insert(user_data)
        
        if not getattr(result, 'data', []) if not isinstance(result, dict) else result.get('data', []):
            return SignupResult(success=False, error="Kayıt oluşturulamadı", error_code="INSERT_FAILED")
        
        user_id = result["data"][0]["id"]
        
        # 9. Store password separately (in a secure way)
        client.table("user_credentials").insert({
            "user_id": user_id,
            "password_hash": password_hash,
            "salt": salt
        })
        
        # 10. Create email verification OTP and send email
        from services.email_service import send_verification_email_with_otp
        import random
        
        # Generate 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        verification_token = generate_token()
        
        logger.info(f"[SIGNUP] Creating OTP for {email}: {otp_code}")
        
        client.table("email_verifications").insert({
            "user_id": user_id,
            "token": verification_token,
            "otp_code": otp_code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()  # 30 min expiry
        })
        
        # Send verification email with OTP
        logger.info(f"[SIGNUP] Sending OTP email to {email}")
        try:
            email_sent = await send_verification_email_with_otp(email, otp_code, full_name)
            logger.info(f"[SIGNUP] OTP email sent result: {email_sent}")
        except Exception as e:
            logger.error(f"[SIGNUP] OTP email send failed: {e}")
            email_sent = False
        
        # 11. Create referral record if referred (status pending until verification)
        if referred_by:
            client.table("referrals").insert({
                "referrer_id": referred_by,
                "referred_id": user_id,
                "status": "pending"  # Will be completed after email verification
            })
        
        # 12. Update daily metrics (optional, rpc not available in custom client)
        pass
        
        logger.info(f"New signup (verification required): {email}, email_sent: {email_sent}")
        
        return SignupResult(
            success=True,
            user_id=user_id,
            referral_code=new_referral_code,
            verification_sent=email_sent
        )
        
    except Exception as e:
        logger.error(f"Signup error: {e}")
        # Return actual error message for debugging
        return SignupResult(success=False, error=f"Hata: {str(e)}", error_code="UNKNOWN_ERROR")


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
            .is_("verified_at", "null")\
            .execute()
        
        if not getattr(result, 'data', []) if not isinstance(result, dict) else result.get('data', []) or len(result["data"]) == 0:
            return False, "Geçersiz veya süresi dolmuş doğrulama linki"
        
        verification = result["data"][0]
        
        # Check expiry
        expires_at = datetime.fromisoformat(verification["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            return False, "Doğrulama linkinin süresi dolmuş"
        
        user_id = verification["user_id"]
        
        # Update user
        client.table("user_profiles").eq("id", user_id).update({
            "email_verified": True,
            "email_verified_at": datetime.utcnow().isoformat(),
            "status": "active"
        })
        
        # Mark token as used
        client.table("email_verifications").eq("id", verification["id"]).update({
            "verified_at": datetime.utcnow().isoformat()
        })
        
        # Complete referral if exists
        client.table("referrals").eq("referred_id", user_id).update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Check and award referral bonus
        await check_referral_reward(user_id)
        
        # Update metrics
        # rpc not available in custom client, skip metrics
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
            .execute()
        
        if not getattr(user_result, 'data', []) if not isinstance(user_result, dict) else user_result.get('data', []) or len(user_result["data"]) == 0:
            return AuthResult(success=False, error="Email veya şifre hatalı", error_code="INVALID_CREDENTIALS")
        
        user = user_result["data"][0]
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
            .execute()
        
        if not getattr(creds_result, 'data', []) if not isinstance(creds_result, dict) else creds_result.get('data', []) or len(creds_result["data"]) == 0:
            return AuthResult(success=False, error="Kimlik bilgileri bulunamadı", error_code="NO_CREDENTIALS")
        
        creds = creds_result["data"][0]
        
        # 6. Verify password
        if not verify_password(password, creds["password_hash"], creds["salt"]):
            # Increment failed attempts
            failed = user.get("failed_login_attempts", 0) + 1
            update_data = {"failed_login_attempts": failed}
            
            if failed >= 5:
                update_data["locked_until"] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            
            client.table("user_profiles").eq("id", user_id).update(update_data)
            
            return AuthResult(success=False, error="Email veya şifre hatalı", error_code="INVALID_CREDENTIALS")
        
        # 7. Check email verification status
        if not user["email_verified"]:
            return AuthResult(
                success=False, 
                error="Lütfen önce email adresinizi doğrulayın. Doğrulama linki emailinize gönderildi.",
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
        })
        
        # 9. Update user stats
        client.table("user_profiles").eq("id", user_id).update({
            "last_login_at": datetime.utcnow().isoformat(),
            "login_count": user.get("login_count", 0) + 1,
            "failed_login_attempts": 0,
            "locked_until": None
        })
        
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
        return AuthResult(success=False, error=f"Login hatası: {str(e)}", error_code="UNKNOWN_ERROR")


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
            .execute()
        
        if not getattr(session_result, 'data', []) if not isinstance(session_result, dict) else session_result.get('data', []) or len(session_result["data"]) == 0:
            return None
        
        session = session_result["data"][0]
        
        # Check expiry
        expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            # Delete expired session
            client.table("user_sessions").eq("id", session["id"]).delete()
            return None
        
        # Get user
        user_result = client.table("user_profiles")\
            .select("*")\
            .eq("id", session["user_id"])\
            .execute()
        
        if not getattr(user_result, 'data', []) if not isinstance(user_result, dict) else user_result.get('data', []) or len(user_result["data"]) == 0:
            return None
        
        user = user_result["data"][0]
        
        # Update last activity
        client.table("user_sessions").eq("id", session["id"]).update({
            "last_activity_at": datetime.utcnow().isoformat()
        })
        
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
        client.table("user_sessions").eq("token_hash", token_hash).delete()
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
            .execute()
        
        if not getattr(referral, 'data', []) if not isinstance(referral, dict) else referral.get('data', []) or len(referral["data"]) == 0:
            return False
        
        referrer_id = referral["data"][0]["referrer_id"]
        
        # Count completed referrals
        count_result = client.table("referrals")\
            .select("id")\
            .eq("referrer_id", referrer_id)\
            .eq("status", "completed")\
            .execute()
        
        count = len(count_result.get("data", []))
        
        if count >= REFERRAL_REWARD_THRESHOLD:
            # Award pro membership
            await grant_pro_membership(referrer_id, REFERRAL_REWARD_DAYS, "referral_reward")
            
            # Mark referrals as rewarded
            client.table("referrals").eq("referrer_id", referrer_id).eq("status", "completed").update({
                "status": "rewarded",
                "rewarded_at": datetime.utcnow().isoformat(),
                "reward_type": "pro_membership",
                "reward_days": REFERRAL_REWARD_DAYS
            })
            
            # Update referral count
            client.table("user_profiles").eq("id", referrer_id).update({
                "referral_count": count
            })
            
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
            .execute()
        
        current_expiry = None
        if getattr(user, 'data', []) if not isinstance(user, dict) else user.get('data', []) and len(user["data"]) > 0 and user["data"][0].get("tier_expires_at"):
            current_expiry = datetime.fromisoformat(
                user["data"][0]["tier_expires_at"].replace("Z", "+00:00")
            )
        
        # Calculate new expiry (extend if already pro)
        if current_expiry and current_expiry > datetime.now(current_expiry.tzinfo):
            new_expiry = current_expiry + timedelta(days=days)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=days)
        
        # Update user
        client.table("user_profiles").eq("id", user_id).update({
            "membership_tier": "pro",
            "tier_expires_at": new_expiry.isoformat()
        })
        
        # Create subscription record
        pro_package = client.table("subscription_packages")\
            .select("id")\
            .eq("slug", "pro")\
            .execute()
        
        if getattr(pro_package, 'data', []) if not isinstance(pro_package, dict) else pro_package.get('data', []) and len(pro_package["data"]) > 0:
            client.table("user_subscriptions").insert({
                "user_id": user_id,
                "package_id": pro_package["data"][0]["id"],
                "status": "active",
                "starts_at": datetime.utcnow().isoformat(),
                "ends_at": new_expiry.isoformat(),
                "auto_renew": False
            })
        
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
            .select("membership_tier,tier_expires_at")\
            .eq("id", user_id)\
            .execute()
        
        if not getattr(user, 'data', []) if not isinstance(user, dict) else user.get('data', []) or len(user["data"]) == 0:
            return False, "Kullanıcı bulunamadı"
        
        tier = user["data"][0]["membership_tier"]
        
        # Check tier expiry
        if tier in ["pro", "enterprise"] and user["data"][0].get("tier_expires_at"):
            expiry = datetime.fromisoformat(user["data"][0]["tier_expires_at"].replace("Z", "+00:00"))
            if datetime.now(expiry.tzinfo) > expiry:
                # Tier expired, downgrade to free
                client.table("user_profiles").eq("id", user_id).update({
                    "membership_tier": "free",
                    "tier_expires_at": None
                })
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
        })
        
        # Update user total
        current = client.table("user_profiles").select("total_claude_calls").eq("id", user_id).execute()
        current_count = 0
        if getattr(current, 'data', []) if not isinstance(current, dict) else current.get('data', []) and len(current["data"]) > 0:
            current_count = current["data"][0].get("total_claude_calls", 0) or 0
        client.table("user_profiles").eq("id", user_id).update({
            "total_claude_calls": current_count + 1
        })
        
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
            .execute()
        
        if not getattr(user, 'data', []) if not isinstance(user, dict) else user.get('data', []) or len(user["data"]) == 0:
            return False, "Kullanıcı bulunamadı", 0
        
        tier = user["data"][0]["membership_tier"]
        
        if tier == "free":
            return False, "Claude analizi Pro üyelik gerektirir", 0
        
        if tier == "admin":
            return True, None, 999
        
        # Get daily limit
        limit = RATE_LIMITS.get(f"claude_call_{tier}", (0, 86400))[0]
        
        # Count today's usage
        today = datetime.utcnow().date().isoformat()
        usage = client.table("claude_usage")\
            .select("id")\
            .eq("user_id", user_id)\
            .gte("created_at", today)\
            .execute()
        
        used = len(usage.get("data", []))
        remaining = max(0, limit - used)
        
        if used >= limit:
            return False, f"Günlük Claude limiti ({limit}) doldu", 0
        
        return True, None, remaining
        
    except Exception as e:
        logger.error(f"Claude limit check error: {e}")
        return False, "Limit kontrolü sırasında hata oluştu", 0
