"""
app/schemas/user.py — User request/response schemas (Pydantic v2).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email:     EmailStr
    password:  str  = Field(min_length=8)
    full_name: str  = Field(min_length=2, max_length=200)
    role:      str  = "citizen"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"citizen", "lawyer", "researcher"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v


class UserLoginRequest(BaseModel):
    email:    EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    full_name:  Optional[str] = Field(None, min_length=2, max_length=200)
    avatar_url: Optional[str] = None


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id:         uuid.UUID
    email:      str
    username:   str
    full_name:  str
    role:       str
    is_active:  bool
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class AdminRoleChange(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"citizen", "lawyer", "researcher", "admin"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v
