"""
CodePath Backend - Main Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import CodePathException
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")

    async def ensure_admin_user() -> None:
        admin_email = settings.ADMIN_EMAIL.strip()
        admin_username = settings.ADMIN_USERNAME.strip()
        admin_password = settings.ADMIN_PASSWORD.strip()
        admin_full_name = settings.ADMIN_FULL_NAME.strip() or "Admin User"

        if not (admin_email and admin_username and admin_password):
            print("ADMIN_* not set; skipping admin bootstrap.")
            return

        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
            if result.scalars().first():
                print("Admin user already exists; skipping bootstrap.")
                return

            existing_result = await session.execute(
                select(User).where(or_(User.email == admin_email, User.username == admin_username))
            )
            existing_user = existing_result.scalars().first()
            if existing_user:
                existing_user.role = UserRole.ADMIN
                existing_user.is_verified = True
                existing_user.hashed_password = get_password_hash(admin_password)
                if admin_full_name and not existing_user.full_name:
                    existing_user.full_name = admin_full_name
                await session.commit()
                print("Promoted existing user to admin.")
                return

            session.add(
                User(
                    email=admin_email,
                    username=admin_username,
                    hashed_password=get_password_hash(admin_password),
                    full_name=admin_full_name,
                    role=UserRole.ADMIN,
                    is_verified=True
                )
            )
            await session.commit()
            print("Admin user created from ADMIN_* settings.")

    # Create database tables (disabled in production by default)
    # Note: In production, use Alembic migrations instead
    if settings.AUTO_CREATE_DB:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        print("AUTO_CREATE_DB is disabled; skipping metadata.create_all()")

    try:
        await ensure_admin_user()
    except Exception as exc:
        print(f"Admin bootstrap failed: {exc}")

    yield

    # Shutdown
    print("Shutting down application")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CodePath Backend API - 개발자 학습 플랫폼",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(CodePathException)
async def codepath_exception_handler(request: Request, exc: CodePathException):
    """Handle custom CodePath exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    # In production, log the exception
    print(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CodePath API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
