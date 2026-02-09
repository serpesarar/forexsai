"""
Authentication Router - User signup, login, and session management

Endpoints:
- POST /api/auth/signup - Register new user
- POST /api/auth/login - Authenticate user
- POST /api/auth/logout - End session
- GET /api/auth/me - Get current user profile
- POST /api/auth/verify-email - Verify email with token
- POST /api/auth/resend-verification - Resend verification email
- GET /api/auth/check-feature/{feature} - Check feature access
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from services.auth_service import (
    signup, login, logout, validate_session, verify_email,
    check_feature_access, check_claude_limit, UserProfile,
    MembershipTier
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=5, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    referral_code: Optional[str] = Field(None, max_length=20)


class SignupResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    referral_code: Optional[str] = None
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


class UserProfileResponse(BaseModel):
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
    
    # Computed fields
    is_pro: bool
    can_use_claude: bool


class VerifyEmailRequest(BaseModel):
    token: str


class FeatureAccessResponse(BaseModel):
    feature: str
    allowed: bool
    message: Optional[str] = None
    tier_required: Optional[List[str]] = None


class ClaudeLimitResponse(BaseModel):
    allowed: bool
    remaining_calls: int
    message: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("user-agent", "unknown")


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[UserProfile]:
    """Dependency to get current user from token"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]
    return await validate_session(token)


async def require_auth(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> UserProfile:
    """Dependency that requires authentication"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor")
    return user


async def require_pro(
    user: UserProfile = Depends(require_auth)
) -> UserProfile:
    """Dependency that requires Pro membership"""
    if user.membership_tier not in ["pro", "enterprise", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Bu özellik Pro üyelik gerektirir"
        )
    return user


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/signup", response_model=SignupResponse)
async def signup_user(request: Request, body: SignupRequest):
    """
    Register a new user account.
    
    - Email must be unique
    - Password must be at least 5 characters
    - Optional referral code for bonus rewards
    """
    import traceback
    try:
        result = await signup(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            referral_code=body.referral_code,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        if not result.success:
            # Log detailed error
            print(f"Signup failed: {result.error} | Code: {result.error_code}")
            raise HTTPException(status_code=400, detail=result.error)
    except HTTPException:
        raise
    except Exception as e:
        # Log full traceback
        print(f"Signup exception: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")
    
    return SignupResponse(
        success=True,
        user_id=result.user_id,
        referral_code=result.referral_code,
        message="Kayıt başarılı! Lütfen email adresinizi doğrulayın."
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(request: Request, body: LoginRequest):
    """
    Authenticate user and return session token.
    
    - Account must be verified
    - Returns JWT-like token valid for 7 days
    - Token should be sent in Authorization header as "Bearer {token}"
    """
    result = await login(
        email=body.email,
        password=body.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    if not result.success:
        status_code = 401
        if result.error_code == "RATE_LIMITED":
            status_code = 429
        elif result.error_code == "ACCOUNT_LOCKED":
            status_code = 423
        elif result.error_code == "EMAIL_NOT_VERIFIED":
            status_code = 403
        
        raise HTTPException(status_code=status_code, detail=result.error)
    
    user_dict = {
        "id": result.user.id,
        "email": result.user.email,
        "full_name": result.user.full_name,
        "membership_tier": result.user.membership_tier,
        "referral_code": result.user.referral_code,
        "referral_count": result.user.referral_count,
        "email_verified": result.user.email_verified,
    }
    
    return LoginResponse(
        success=True,
        token=result.session_token,
        user=user_dict,
        message="Giriş başarılı!"
    )


@router.post("/logout")
async def logout_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """End current session"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        await logout(token)
    
    return {"success": True, "message": "Çıkış yapıldı"}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: UserProfile = Depends(require_auth)):
    """Get current user's profile"""
    is_pro = user.membership_tier in ["pro", "enterprise", "admin"]
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        membership_tier=user.membership_tier,
        tier_expires_at=user.tier_expires_at,
        referral_code=user.referral_code,
        referral_count=user.referral_count,
        status=user.status,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        is_pro=is_pro,
        can_use_claude=is_pro
    )


@router.post("/verify-email")
async def verify_email_endpoint(body: VerifyEmailRequest):
    """Verify email address with token from email link"""
    success, error = await verify_email(body.token)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"success": True, "message": "Email adresiniz doğrulandı!"}


@router.get("/check-feature/{feature}", response_model=FeatureAccessResponse)
async def check_feature(
    feature: str,
    user: UserProfile = Depends(require_auth)
):
    """Check if user has access to a specific feature"""
    allowed, message = await check_feature_access(user.id, feature)
    
    tier_required = None
    if not allowed:
        tier_map = {
            "claude_analysis": ["pro", "enterprise"],
            "advanced_patterns": ["pro", "enterprise"],
            "api_access": ["enterprise"],
        }
        tier_required = tier_map.get(feature)
    
    return FeatureAccessResponse(
        feature=feature,
        allowed=allowed,
        message=message,
        tier_required=tier_required
    )


@router.get("/claude-limit", response_model=ClaudeLimitResponse)
async def get_claude_limit(user: UserProfile = Depends(require_auth)):
    """Check remaining Claude API calls for today"""
    allowed, message, remaining = await check_claude_limit(user.id)
    
    return ClaudeLimitResponse(
        allowed=allowed,
        remaining_calls=remaining,
        message=message
    )


@router.get("/referral-stats")
async def get_referral_stats(user: UserProfile = Depends(require_auth)):
    """Get user's referral statistics"""
    from services.auth_service import get_supabase
    
    client = await get_supabase()
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    # Get referral count
    referrals = client.table("referrals")\
        .select("*")\
        .eq("referrer_id", user.id)\
        .execute()
    
    total = len(referrals.get("data", [])) if referrals.get("data") else 0
    completed = sum(1 for r in (referrals.get("data") or []) if r["status"] in ["completed", "rewarded"])
    pending = total - completed
    
    # Calculate progress to reward
    progress = min(completed, 5)
    reward_unlocked = completed >= 5
    
    return {
        "referral_code": user.referral_code,
        "referral_link": f"https://xauusd-panel.com/signup?ref={user.referral_code}",
        "total_referrals": total,
        "completed_referrals": completed,
        "pending_referrals": pending,
        "progress_to_reward": f"{progress}/5",
        "reward_unlocked": reward_unlocked,
        "reward_description": "5 arkadaş davet et, 1 hafta Pro üyelik kazan!"
    }


# =============================================================================
# Public Endpoints (No Auth Required)
# =============================================================================

@router.get("/packages")
async def get_packages():
    """Get available subscription packages"""
    from services.auth_service import get_supabase
    
    client = await get_supabase()
    if not client:
        # Return static packages if DB unavailable
        return {
            "packages": [
                {
                    "slug": "free",
                    "name": "Free",
                    "price_monthly": 0,
                    "features": ["Panel erişimi", "Gerçek zamanlı veri", "Temel göstergeler"],
                    "limitations": ["Claude analizi yok", "Gelişmiş pattern yok"]
                },
                {
                    "slug": "pro",
                    "name": "Pro",
                    "price_monthly": 29.99,
                    "features": ["Tüm Free özellikleri", "Claude AI analizi", "Gelişmiş patternler", "Öncelikli destek"],
                    "is_popular": True
                }
            ]
        }
    
    packages = client.table("subscription_packages")\
        .select("*")\
        .eq("is_active", True)\
        .order("display_order")\
        .execute()
    
    return {"packages": packages.get("data") or []}


@router.get("/validate-referral/{code}")
async def validate_referral_code(code: str):
    """Check if a referral code is valid"""
    from services.auth_service import get_supabase
    
    client = await get_supabase()
    if not client:
        return {"valid": False, "message": "Doğrulama yapılamadı"}
    
    result = client.table("user_profiles")\
        .select("id,full_name")\
        .eq("referral_code", code.upper())\
        .execute()
    
    if result.get("data") and len(result["data"]) > 0:
        name = result["data"][0].get("full_name", "Bir kullanıcı")
        return {
            "valid": True,
            "message": f"{name} sizi davet etti!",
            "referrer_name": name
        }
    
    return {"valid": False, "message": "Geçersiz referans kodu"}


# =============================================================================
# Password Reset Endpoints
# =============================================================================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=5, max_length=128)


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Send password reset email"""
    import traceback
    try:
        from services.auth_service import get_supabase, generate_token
        from services.email_service import send_password_reset_email
        import hashlib
        from datetime import datetime, timedelta
        
        client = await get_supabase()
        if not client:
            return {"success": True, "message": "Eğer email kayıtlıysa, şifre sıfırlama linki gönderildi."}
        
        # Find user
        user = client.table("user_profiles")\
            .select("id,full_name,email")\
            .eq("email", body.email.lower())\
            .execute()
        
        if not user.get("data") or len(user["data"]) == 0:
            # Don't reveal if email exists
            return {"success": True, "message": "Eğer email kayıtlıysa, şifre sıfırlama linki gönderildi."}
        
        user_data = user["data"][0]
        
        # Generate reset token
        token = generate_token()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store token (reuse email_verifications table)
        try:
            client.table("email_verifications").insert({
                "user_id": user_data["id"],
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
                "verification_type": "password_reset"
            })
        except:
            # Update existing
            client.table("email_verifications").eq("user_id", user_data["id"]).update({
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
                "verification_type": "password_reset"
            })
        
        # Send email
        await send_password_reset_email(
            to=body.email.lower(),
            token=token,
            full_name=user_data.get("full_name")
        )
        
        return {"success": True, "message": "Şifre sıfırlama linki email adresinize gönderildi."}
    except Exception as e:
        print(f"Forgot password error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Hata: {str(e)}")


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """Reset password with token"""
    from services.auth_service import get_supabase, hash_password, validate_password
    import hashlib
    from datetime import datetime
    
    # Validate new password
    is_valid, error = validate_password(body.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    client = await get_supabase()
    if not client:
        raise HTTPException(status_code=500, detail="Veritabanı bağlantısı kurulamadı")
    
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    
    # Find token
    verification = client.table("email_verifications")\
        .select("user_id,expires_at")\
        .eq("token_hash", token_hash)\
        .eq("verification_type", "password_reset")\
        .execute()
    
    if not verification.get("data") or len(verification["data"]) == 0:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş token")
    
    # Check expiry
    v_data = verification["data"][0]
    expires_at = datetime.fromisoformat(v_data["expires_at"].replace("Z", "+00:00"))
    if datetime.now(expires_at.tzinfo) > expires_at:
        raise HTTPException(status_code=400, detail="Token süresi dolmuş. Lütfen yeni bir link isteyin.")
    
    user_id = v_data["user_id"]
    
    # Update password
    password_hash = hash_password(body.new_password)
    client.table("user_credentials").eq("user_id", user_id).update({
        "password_hash": password_hash,
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Delete used token
    client.table("email_verifications")\
        .eq("token_hash", token_hash)\
        .delete()
    
    # Invalidate all sessions
    client.table("user_sessions")\
        .eq("user_id", user_id)\
        .delete()
    
    return {"success": True, "message": "Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş yapabilirsiniz."}
