"""
app/routers/auth.py — Authentication endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import bleach
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    AdminRoleChange,
    RefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
    UserUpdateRequest,
)

router = APIRouter()


def _to_username(email: str) -> str:
    return email.split("@")[0].replace(".", "_").lower()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new NyayMarg account."""
    body.full_name = bleach.clean(body.full_name)

    # Normalize email
    email_str = str(body.email).strip().lower()

    # Uniqueness check for email
    existing = await db.execute(select(User).where(User.email == email_str))
    if existing.scalar():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    base_username = _to_username(email_str)
    username = base_username
    
    # Check for username collision (common with same prefix across domains)
    counter = 1
    while True:
        existing_u = await db.execute(select(User).where(User.username == username))
        if not existing_u.scalar():
            break
        username = f"{base_username}_{counter}"
        counter += 1

    try:
        user = User(
            id=uuid.uuid4(),
            email=email_str,
            username=username,
            full_name=body.full_name,
            hashed_password=hash_password(body.password),
            role=UserRole(body.role),
        )
        db.add(user)
        await db.flush()
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Database error during registration: {exc}")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    email_str = str(body.email).strip().lower()
    result = await db.execute(select(User).where(User.email == email_str))
    user   = result.scalar_one_or_none()
    if not user or not verify_password(body.password, str(user.hashed_password)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account deactivated")

    # Update last_login
    user.last_login = datetime.utcnow()  # type: ignore[assignment]
    await db.flush()

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
async def logout():
    """Client-side token deletion. Stateless — token blacklisting via Redis can be added."""
    return {"message": "Logged out — please delete your tokens client-side"}


@router.get("/me", response_model=UserOut)
async def get_me(
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == current["id"]))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    body:    UserUpdateRequest,
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == current["id"]))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if body.full_name:
        user.full_name = bleach.clean(body.full_name)  # type: ignore[assignment]
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url  # type: ignore[assignment]
    await db.flush()
    return UserOut.model_validate(user)
