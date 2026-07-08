"""Shared-passcode authentication.

The whole family shares one passcode. On login we verify it (constant-time)
and issue a long-lived JWT so members log in once and stay in. Protected
endpoints depend on `require_auth`.
"""
from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .models import TokenResponse

_ALGO = "HS256"
_bearer = HTTPBearer(auto_error=False)


def verify_passcode(passcode: str) -> bool:
    expected = get_settings().family_passcode
    return hmac.compare_digest(passcode.strip(), expected.strip())


def issue_token() -> TokenResponse:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    token = jwt.encode(
        {"scope": "family", "exp": expires_at},
        settings.jwt_secret,
        algorithm=_ALGO,
    )
    return TokenResponse(token=token, expires_at=expires_at)


def require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """FastAPI dependency: reject requests without a valid family token."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="مطلوب تسجيل الدخول",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        jwt.decode(creds.credentials, get_settings().jwt_secret, algorithms=[_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="انتهت الجلسة، الرجاء تسجيل الدخول من جديد",
            headers={"WWW-Authenticate": "Bearer"},
        )
