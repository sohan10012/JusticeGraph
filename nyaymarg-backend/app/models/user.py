"""
app/models/user.py — User ORM model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRole(str, enum.Enum):
    citizen    = "citizen"
    lawyer     = "lawyer"
    researcher = "researcher"
    admin      = "admin"


class User(Base):
    __tablename__ = "users"

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:           Mapped[str]       = mapped_column(String(255), unique=True, index=True, nullable=False)
    username:        Mapped[str]       = mapped_column(String(100), unique=True, index=True)
    full_name:       Mapped[str]       = mapped_column(String(200))
    hashed_password: Mapped[str]       = mapped_column(String(255), nullable=False)
    role:            Mapped[UserRole]  = mapped_column(Enum(UserRole), default=UserRole.citizen)
    is_active:       Mapped[bool]      = mapped_column(Boolean, default=True)
    avatar_url:      Mapped[str | None]= mapped_column(String(500), nullable=True)
    created_at:      Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)
    last_login:      Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
