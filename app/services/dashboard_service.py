"""
Dashboard service for user statistics and progress
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from datetime import datetime, timedelta

from app.models.user import User
from app.models.problem import Problem, DifficultyLevel
from app.models.submission import Submission, SubmissionStatus
from app.schemas.dashboard import (
    DashboardResponse,
    ProblemProgress,
    DifficultyStats,
    RecentSubmission
)
from app.core.exceptions import NotFoundError


class DashboardService:
    """Service for dashboard operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(self, user_id: str) -> DashboardResponse:
        """
        Get dashboard data for user

        Args:
            user_id: User UUID

        Returns:
            Dashboard data with progress and statistics

        Raises:
            NotFoundError: If user not found
        """
        # Verify user exists
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Get problem progress
        progress = await self._get_problem_progress(user_id)

        # Get solved problems by difficulty
        solved_by_difficulty = await self._get_solved_by_difficulty(user_id)

        # Get recent submissions
        recent_submissions = await self._get_recent_submissions(user_id)

        # Get current streak
        current_streak = await self._get_current_streak(user_id)

        # Get total submission count
        result = await self.db.execute(
            select(func.count(Submission.id)).where(Submission.user_id == user_id)
        )
        total_submission_count = result.scalar() or 0

        return DashboardResponse(
            user_id=user.id,
            username=user.username,
            progress=progress,
            solved_by_difficulty=solved_by_difficulty,
            recent_submissions=recent_submissions,
            current_streak=current_streak,
            total_submission_count=total_submission_count
        )

    async def _get_problem_progress(self, user_id: str) -> ProblemProgress:
        """Get problem solving progress"""

        # Total active problems
        result = await self.db.execute(
            select(func.count(Problem.id)).where(Problem.is_active == True)
        )
        total_problems = result.scalar() or 0

        # Solved problems (distinct problems with successful submissions)
        result = await self.db.execute(
            select(func.count(distinct(Submission.problem_id))).where(
                and_(
                    Submission.user_id == user_id,
                    Submission.status == SubmissionStatus.PASSED
                )
            )
        )
        solved_problems = result.scalar() or 0

        # Attempted problems (distinct problems with any submission)
        result = await self.db.execute(
            select(func.count(distinct(Submission.problem_id))).where(
                Submission.user_id == user_id
            )
        )
        attempted_problems = result.scalar() or 0

        # Calculate success rate
        if attempted_problems > 0:
            success_rate = (solved_problems / attempted_problems) * 100
        else:
            success_rate = 0.0

        return ProblemProgress(
            total_problems=total_problems,
            solved_problems=solved_problems,
            attempted_problems=attempted_problems,
            success_rate=round(success_rate, 2)
        )

    async def _get_solved_by_difficulty(self, user_id: str) -> DifficultyStats:
        """Get count of solved problems by difficulty"""

        # Get all successful submissions with problem info
        query = select(Problem.difficulty, func.count(distinct(Problem.id))).join(
            Submission, Submission.problem_id == Problem.id
        ).where(
            and_(
                Submission.user_id == user_id,
                Submission.status == SubmissionStatus.PASSED
            )
        ).group_by(Problem.difficulty)

        result = await self.db.execute(query)
        difficulty_counts = dict(result.all())

        return DifficultyStats(
            beginner=difficulty_counts.get(DifficultyLevel.BEGINNER, 0),
            easy=difficulty_counts.get(DifficultyLevel.EASY, 0),
            medium=difficulty_counts.get(DifficultyLevel.MEDIUM, 0),
            hard=difficulty_counts.get(DifficultyLevel.HARD, 0),
            expert=difficulty_counts.get(DifficultyLevel.EXPERT, 0)
        )

    async def _get_recent_submissions(self, user_id: str, limit: int = 10) -> List[RecentSubmission]:
        """Get recent submissions"""

        query = select(Submission, Problem).join(
            Problem, Problem.id == Submission.problem_id
        ).where(
            Submission.user_id == user_id
        ).order_by(
            Submission.submitted_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        recent_submissions = []
        for submission, problem in rows:
            recent_submissions.append(
                RecentSubmission(
                    id=submission.id,
                    problem_id=problem.id,
                    problem_title=problem.title,
                    status=submission.status.value,
                    passed_tests=submission.passed_tests,
                    total_tests=submission.total_tests,
                    submitted_at=submission.submitted_at
                )
            )

        return recent_submissions

    async def _get_current_streak(self, user_id: str) -> int:
        """Calculate current daily submission streak"""

        # Get submissions ordered by date
        query = select(
            func.date(Submission.submitted_at).label('submission_date')
        ).where(
            Submission.user_id == user_id
        ).group_by(
            func.date(Submission.submitted_at)
        ).order_by(
            func.date(Submission.submitted_at).desc()
        )

        result = await self.db.execute(query)
        submission_dates = [row[0] for row in result.all()]

        if not submission_dates:
            return 0

        # Check if today or yesterday has a submission
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        if submission_dates[0] not in [today, yesterday]:
            return 0

        # Count consecutive days
        streak = 1
        current_date = submission_dates[0]

        for i in range(1, len(submission_dates)):
            expected_date = current_date - timedelta(days=1)
            if submission_dates[i] == expected_date:
                streak += 1
                current_date = submission_dates[i]
            else:
                break

        return streak
