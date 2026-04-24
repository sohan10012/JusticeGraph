"""
app/routers/users.py — Admin user management endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.user import AdminRoleChange, UserOut

router = APIRouter()
_admin_only = require_role(UserRole.admin)


@router.get("/", response_model=PaginatedResponse[UserOut],
            dependencies=[_admin_only])
async def list_users(
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    all_u  = result.scalars().all()
    total  = len(all_u)
    start  = (page - 1) * page_size
    return PaginatedResponse.build(
        [UserOut.model_validate(u) for u in all_u[start : start + page_size]],
        total, page, page_size
    )


@router.get("/{user_id}", response_model=UserOut, dependencies=[_admin_only])
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut.model_validate(user)


@router.put("/{user_id}/role", response_model=UserOut, dependencies=[_admin_only])
async def change_role(
    user_id: UUID,
    body:    AdminRoleChange,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.role = UserRole(body.role)  # type: ignore[assignment]
    await db.flush()
    return UserOut.model_validate(user)


@router.put("/{user_id}/deactivate", status_code=204, dependencies=[_admin_only])
async def deactivate_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(update(User).where(User.id == user_id).values(is_active=False))
