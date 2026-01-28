"""
Admin endpoints for managing users and problems
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.deps import get_current_admin_user
from app.schemas.auth import UserListResponse
from app.schemas.problem import (
    ProblemAdminListResponse,
    ProblemAdminListItem,
    ProblemAdminDetail,
    ProblemAdminUpdateRequest,
    ProblemImportRequest,
    ProblemImportResponse
)
from app.services.user_service import UserService
from app.services.problem_service import ProblemService

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = UserService(db)
    users, total = await service.list_users(page=page, page_size=page_size, role=role)
    total_pages = (total + page_size - 1) // page_size
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/problems", response_model=ProblemAdminListResponse)
async def list_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = ProblemService(db)
    problems, total, total_pages = await service.list_problems_admin(
        page=page,
        page_size=page_size,
        difficulty=difficulty,
        category=category,
        is_active=is_active
    )
    return ProblemAdminListResponse(
        problems=[ProblemAdminListItem.model_validate(p) for p in problems],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/problems/{problem_id}", response_model=ProblemAdminDetail)
async def get_problem(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = ProblemService(db)
    problem = await service.get_problem_admin(problem_id)
    return ProblemAdminDetail.model_validate(problem)


@router.put("/problems/{problem_id}", response_model=ProblemAdminDetail)
async def update_problem(
    problem_id: str,
    request: ProblemAdminUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = ProblemService(db)
    try:
        problem = await service.update_problem_admin(problem_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProblemAdminDetail.model_validate(problem)


@router.delete("/problems/{problem_id}")
async def delete_problem(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = ProblemService(db)
    await service.delete_problem_admin(problem_id)
    return {"success": True}


@router.post("/problems/import", response_model=ProblemImportResponse)
async def import_problems(
    request: ProblemImportRequest,
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    service = ProblemService(db)
    try:
        created, updated = await service.import_problems_from_json(request.problems)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProblemImportResponse(created=created, updated=updated)
