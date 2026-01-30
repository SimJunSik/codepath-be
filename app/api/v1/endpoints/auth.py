"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse, RefreshTokenRequest,
    UserResponse, SendVerificationCodeRequest, VerifyCodeRequest, VerifyCodeResponse
)
from app.services.auth_service import AuthService
from app.api.v1.deps import get_current_active_user
from app.core.exceptions import AuthenticationError, ConflictError


router = APIRouter()


@router.post("/send-verification-code")
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send verification code to email (before signup)

    - **email**: Email address to verify

    A 6-digit verification code will be sent to the email address.
    The code expires in 5 minutes.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.send_verification_code(request.email)
        return result
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 코드 발송 중 오류가 발생했습니다."
        )


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify the code sent to email (before signup)

    - **email**: Email address
    - **code**: 6-digit verification code

    Returns verification status. Once verified, you have 10 minutes to complete signup.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.verify_code(request.email, request.code)
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 코드 검증 중 오류가 발생했습니다."
        )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user (email must be verified first)

    - **email**: Verified email address
    - **username**: Unique username (3-50 characters, alphanumeric + underscore)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **full_name**: Optional full name

    Note: Email must be verified via /auth/verify-code before signup.
    Returns access and refresh tokens upon successful registration.
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.signup(request)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 중 오류가 발생했습니다."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access/refresh tokens

    - **email**: User email address
    - **password**: User password
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.login(request)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.refresh_token(request.refresh_token)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    Requires: Bearer token in Authorization header
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Logout current user

    Note: In this MVP version, logout is handled client-side by removing tokens.
    In production, implement token blacklisting with Redis.

    Requires: Bearer token in Authorization header
    """
    # TODO: Implement token blacklisting with Redis
    # For MVP, client will simply discard the tokens
    return None
