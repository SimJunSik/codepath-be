"""
Authentication related Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


class SignupRequest(BaseModel):
    """User signup request"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    full_name: Optional[str] = Field(None, max_length=100, description="User full name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseModel):
    """User response"""
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """Admin user list item"""
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: list[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class SendVerificationCodeRequest(BaseModel):
    """Send verification code request (before signup)"""
    email: EmailStr = Field(..., description="Email address to verify")


class VerifyCodeRequest(BaseModel):
    """Verify code request (before signup)"""
    email: EmailStr = Field(..., description="Email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class VerifyCodeResponse(BaseModel):
    """Verify code response"""
    message: str = Field(..., description="Response message")
    verified: bool = Field(..., description="Whether email is verified")
