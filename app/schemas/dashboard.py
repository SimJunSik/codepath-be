"""
Dashboard related Pydantic schemas
"""
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import uuid


class RecentSubmission(BaseModel):
    """Recent submission for dashboard"""
    id: uuid.UUID
    problem_id: uuid.UUID
    problem_title: str
    status: str
    passed_tests: int
    total_tests: int
    submitted_at: datetime


class ProblemProgress(BaseModel):
    """Problem solving progress"""
    total_problems: int
    solved_problems: int
    attempted_problems: int
    success_rate: float


class DifficultyStats(BaseModel):
    """Statistics by difficulty level"""
    beginner: int = 0
    easy: int = 0
    medium: int = 0
    hard: int = 0
    expert: int = 0


class DashboardResponse(BaseModel):
    """Dashboard data response"""
    user_id: uuid.UUID
    username: str
    progress: ProblemProgress
    solved_by_difficulty: DifficultyStats
    recent_submissions: List[RecentSubmission]
    current_streak: int
    total_submission_count: int
