"""Server-side authorization for operational and private dashboard routes."""
from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth_service import UserProfile, validate_session

_bearer = HTTPBearer(auto_error=False)
# Match the established OwnerGuard policy; require a validated server session.
_OWNER_EMAILS = "m.canodacioglu@gmail.com,m.canodaciogluabd@gmail.com"


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> UserProfile:
    """Require a real, active operator session; never trust a client-side role.

    ADMIN_EMAILS can override the existing OwnerGuard allowlist without changing
    subscriptions. An explicitly empty override permits only the admin role.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Giriş yapmanız gerekiyor", headers={"WWW-Authenticate": "Bearer"})
    user = await validate_session(credentials.credentials)
    if user is None:
        raise HTTPException(401, "Oturum geçersiz veya süresi dolmuş", headers={"WWW-Authenticate": "Bearer"})
    allowed = {email.strip().casefold() for email in os.getenv("ADMIN_EMAILS", _OWNER_EMAILS).split(",") if email.strip()}
    if (
        user.status != "active"
        or not user.email_verified
        or (user.membership_tier != "admin" and user.email.casefold() not in allowed)
    ):
        raise HTTPException(403, "Bu işlem yönetici yetkisi gerektirir")
    return user
