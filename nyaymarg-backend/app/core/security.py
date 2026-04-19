"""
app/core/security.py — JWT, bcrypt, PII detection, role-based access.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# ── PII Patterns ──────────────────────────────────────────────────────────────
_PII_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),    # Aadhaar
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),        # PAN
    re.compile(r"\b[6-9]\d{9}\b"),                 # Indian mobile
]


def detect_pii(text: str) -> bool:
    """Return True if text contains Aadhaar, PAN, or Indian phone number."""
    return any(p.search(text) for p in _PII_PATTERNS)


# ── Password helpers ──────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_access_token(data: dict[str, Any]) -> str:
    payload = {
        **data,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = {
        **data,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Role hierarchy ────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    citizen    = "citizen"
    lawyer     = "lawyer"
    researcher = "researcher"
    admin      = "admin"


_ROLE_RANK: dict[UserRole, int] = {
    UserRole.citizen:    0,
    UserRole.lawyer:     1,
    UserRole.researcher: 2,
    UserRole.admin:      3,
}


# ── Current user dependency ───────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Dependency that extracts + validates the Bearer JWT and returns a minimal
    user dict. Routers that need DB-loaded user objects should further query.
    """
    from app.core.exceptions import AuthenticationError

    if credentials is None:
        raise AuthenticationError()

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise AuthenticationError()

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthenticationError()

    return {
        "id":    UUID(user_id),
        "email": payload.get("email", ""),
        "role":  UserRole(payload.get("role", UserRole.citizen)),
    }


def require_role(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.

    Usage::
        router.get("/admin", dependencies=[require_role(UserRole.admin)])
    """
    async def _checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError()
        return current_user
    return Depends(_checker)
