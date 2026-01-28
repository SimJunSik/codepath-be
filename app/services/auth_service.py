"""
Authentication service for user registration and login
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, request: SignupRequest) -> UserResponse:
        """
        Register a new user

        Args:
            request: Signup request data

        Returns:
            Created user data

        Raises:
            ConflictError: If email or username already exists
        """
        # Check if email already exists
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ConflictError("Email already registered")

        # Check if username already exists
        result = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise ConflictError("Username already taken")

        # Create new user
        user = User(
            email=request.email,
            username=request.username,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate user and return tokens

        Args:
            request: Login request data

        Returns:
            Access and refresh tokens

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            New access and refresh tokens

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        # Verify user exists
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def get_current_user(self, token: str) -> UserResponse:
        """
        Get current user from access token

        Args:
            token: Access token

        Returns:
            User data

        Raises:
            AuthenticationError: If token is invalid
        """
        # Decode token
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise AuthenticationError("Invalid token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token")

        # Get user from database
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        return UserResponse.model_validate(user)
