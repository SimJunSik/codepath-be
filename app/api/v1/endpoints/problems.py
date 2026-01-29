"""
Problem API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.schemas.problem import (
    ProblemListResponse,
    ProblemDetail,
    CodeRunRequest,
    CodeRunResponse,
    CodeSubmitRequest,
    CodeSubmitResponse
)
from app.schemas.auth import UserResponse
from app.services.problem_service import ProblemService
from app.services.rate_limiter import RateLimiter, RateLimitExceeded
from app.api.v1.deps import get_current_active_user
from app.core.exceptions import NotFoundError


router = APIRouter()


@router.get("", response_model=ProblemListResponse)
async def get_problems(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of problems

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **difficulty**: Filter by difficulty (beginner, easy, medium, hard, expert)
    - **category**: Filter by category

    Public endpoint - No authentication required
    """
    try:
        problem_service = ProblemService(db)
        problems = await problem_service.get_problems(
            page=page,
            page_size=page_size,
            difficulty=difficulty,
            category=category
        )
        return problems
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch problems"
        )


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get problem details by ID

    - **problem_id**: Problem UUID

    Requires: Authentication
    """
    try:
        problem_service = ProblemService(db)
        problem = await problem_service.get_problem_by_id(problem_id)
        return problem
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch problem details"
        )


@router.post("/{problem_id}/run", response_model=CodeRunResponse)
async def run_code(
    problem_id: str,
    request: CodeRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Run code against visible test cases (no submission)

    - **problem_id**: Problem UUID
    - **code**: Python code to execute
    - **language**: Programming language (default: python)

    This endpoint runs code against visible test cases only.
    Use the submit endpoint to test against all test cases.

    Requires: Authentication
    """
    try:
        problem_service = ProblemService(db)
        result = await problem_service.run_code(problem_id, request)
        return result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution failed: {str(e)}"
        )


@router.post("/{problem_id}/submit", response_model=CodeSubmitResponse)
async def submit_code(
    problem_id: str,
    request: CodeSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Submit code and run against all test cases (including hidden)

    - **problem_id**: Problem UUID
    - **code**: Python code to submit
    - **language**: Programming language (default: python)

    This endpoint creates a submission record and runs code against
    all test cases including hidden ones.

    Rate limit: 10 seconds between submissions (LLM evaluation)

    Requires: Authentication
    """
    try:
        # Check rate limit for LLM usage
        await RateLimiter.check_and_record_llm_request(str(current_user.id))

        problem_service = ProblemService(db)
        result = await problem_service.submit_code(
            problem_id=problem_id,
            user_id=str(current_user.id),
            request=request
        )
        return result
    except RateLimitExceeded as e:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": e.message,
                "retry_after": e.retry_after
            },
            headers={"Retry-After": str(e.retry_after)}
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code submission failed: {str(e)}"
        )
