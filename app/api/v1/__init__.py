"""
API v1 router configuration
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, problems, dashboard

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(problems.router, prefix="/problems", tags=["Problems"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
