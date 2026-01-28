"""
Dashboard API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.schemas.auth import UserResponse
from app.services.dashboard_service import DashboardService
from app.api.v1.deps import get_current_active_user
from app.core.exceptions import NotFoundError


router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get dashboard data for current user

    Returns:
    - **user_id**: Current user ID
    - **username**: Current username
    - **progress**: Problem solving progress statistics
    - **solved_by_difficulty**: Count of solved problems by difficulty level
    - **recent_submissions**: Last 10 submissions
    - **current_streak**: Current daily submission streak
    - **total_submission_count**: Total number of submissions

    Requires: Authentication
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard = await dashboard_service.get_dashboard(str(current_user.id))
        return dashboard
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )
