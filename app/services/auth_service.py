"""
Authentication service for user registration and login
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import secrets
import redis.asyncio as redis

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.core.redis import get_redis
from app.services.email_service import email_service

# Constants for verification code
VERIFICATION_CODE_TTL = 300  # 5 minutes
VERIFIED_EMAIL_TTL = 600  # 10 minutes (time to complete signup after verification)
VERIFICATION_CODE_PREFIX = "email_verification:"
VERIFIED_EMAIL_PREFIX = "email_verified:"


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_verification_code() -> str:
        """Generate a 6-digit random verification code"""
        return "".join(secrets.choice("0123456789") for _ in range(6))

    @staticmethod
    async def store_verification_code(email: str, code: str) -> None:
        """Store verification code in Redis with 5 minute TTL"""
        redis_client = await get_redis()
        key = f"{VERIFICATION_CODE_PREFIX}{email}"
        await redis_client.setex(key, VERIFICATION_CODE_TTL, code)

    @staticmethod
    async def get_verification_code(email: str) -> Optional[str]:
        """Get verification code from Redis"""
        redis_client = await get_redis()
        key = f"{VERIFICATION_CODE_PREFIX}{email}"
        return await redis_client.get(key)

    @staticmethod
    async def delete_verification_code(email: str) -> None:
        """Delete verification code from Redis"""
        redis_client = await get_redis()
        key = f"{VERIFICATION_CODE_PREFIX}{email}"
        await redis_client.delete(key)

    @staticmethod
    async def mark_email_verified(email: str) -> None:
        """Mark email as verified in Redis with 10 minute TTL"""
        redis_client = await get_redis()
        key = f"{VERIFIED_EMAIL_PREFIX}{email}"
        await redis_client.setex(key, VERIFIED_EMAIL_TTL, "true")

    @staticmethod
    async def is_email_verified(email: str) -> bool:
        """Check if email is verified in Redis"""
        redis_client = await get_redis()
        key = f"{VERIFIED_EMAIL_PREFIX}{email}"
        result = await redis_client.get(key)
        return result == "true"

    @staticmethod
    async def delete_email_verified(email: str) -> None:
        """Delete email verified status from Redis"""
        redis_client = await get_redis()
        key = f"{VERIFIED_EMAIL_PREFIX}{email}"
        await redis_client.delete(key)

    async def send_verification_code(self, email: str) -> dict:
        """
        Send verification code to email (before signup)

        Args:
            email: Email address to verify

        Returns:
            Success message

        Raises:
            ConflictError: If email is already registered
        """
        # Check if email already exists in DB
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            raise ConflictError("이미 가입된 이메일입니다.")

        # Generate and send verification code
        code = self.generate_verification_code()
        await self.store_verification_code(email, code)
        await email_service.send_verification_code(email, code)

        return {"message": "인증 코드가 이메일로 발송되었습니다."}

    async def verify_code(self, email: str, code: str) -> dict:
        """
        Verify the code sent to email (before signup)

        Args:
            email: Email address
            code: 6-digit verification code

        Returns:
            Success message with verified status

        Raises:
            AuthenticationError: If code is invalid or expired
        """
        # Get stored code from Redis
        stored_code = await self.get_verification_code(email)

        if not stored_code:
            raise AuthenticationError("인증 코드가 만료되었습니다. 새 코드를 요청해 주세요.")

        if stored_code != code:
            raise AuthenticationError("잘못된 인증 코드입니다.")

        # Mark email as verified
        await self.mark_email_verified(email)
        await self.delete_verification_code(email)

        return {"message": "이메일 인증이 완료되었습니다.", "verified": True}

    async def signup(self, request: SignupRequest) -> TokenResponse:
        """
        Register a new user (email must be verified first)

        Args:
            request: Signup request data

        Returns:
            Access and refresh tokens

        Raises:
            AuthenticationError: If email is not verified
            ConflictError: If email or username already exists
        """
        # Check if email is verified
        if not await self.is_email_verified(request.email):
            raise AuthenticationError("이메일 인증이 필요합니다.")

        # Check if email already exists
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ConflictError("이미 가입된 이메일입니다.")

        # Check if username already exists
        result = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise ConflictError("이미 사용 중인 사용자명입니다.")

        # Create new user (already verified)
        user = User(
            email=request.email,
            username=request.username,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            is_verified=True,  # Already verified via email
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Delete verified email status from Redis
        await self.delete_email_verified(request.email)

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

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
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다.")

        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다.")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("비활성화된 계정입니다.")

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
