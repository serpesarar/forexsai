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
    password: str = Field(..., min_length=8, max_length=128)
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
    - Password must be at least 8 characters with uppercase, lowercase, and number
    - Optional referral code for bonus rewards
    - Verification email will be sent
    """
    result = await signup(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        referral_code=body.referral_code,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
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
    
    total = len(referrals.data) if referrals.data else 0
    completed = sum(1 for r in (referrals.data or []) if r["status"] in ["completed", "rewarded"])
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
    
    return {"packages": packages.data or []}


@router.get("/validate-referral/{code}")
async def validate_referral_code(code: str):
    """Check if a referral code is valid"""
    from services.auth_service import get_supabase
    
    client = await get_supabase()
    if not client:
        return {"valid": False, "message": "Doğrulama yapılamadı"}
    
    result = client.table("user_profiles")\
        .select("id, full_name")\
        .eq("referral_code", code.upper())\
        .single()\
        .execute()
    
    if result.data:
        name = result.data.get("full_name", "Bir kullanıcı")
        return {
            "valid": True,
            "message": f"{name} sizi davet etti!",
            "referrer_name": name
        }
    
    return {"valid": False, "message": "Geçersiz referans kodu"}
