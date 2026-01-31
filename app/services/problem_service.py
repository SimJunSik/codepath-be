"""
Problem service for managing problems and submissions
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, exists, case, literal
from datetime import datetime
import math
import uuid

from app.models.problem import Problem, DifficultyLevel, ProblemCategory
from app.models.submission import Submission, SubmissionStatus
from app.schemas.problem import (
    ProblemListResponse,
    ProblemListItem,
    ProblemDetail,
    CodeRunRequest,
    CodeRunResponse,
    CodeSubmitRequest,
    CodeSubmitResponse,
    TestResult,
    SolveStatus
)
from app.core.exceptions import NotFoundError
from app.services.code_execution_service import CodeExecutionService
from app.services.explanation_eval_service import ExplanationEvalService


class ProblemService:
    """Service for problem operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.code_executor = CodeExecutionService()
        self.explanation_evaluator = ExplanationEvalService()

    def _extract_answer_payload(self, execution_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for tr in execution_result.get("test_results", []):
            actual = tr.get("actual")
            if isinstance(actual, dict):
                return actual
        return None

    def _extract_expected_schema(self, expected_outputs: List[Any]) -> List[str]:
        keys = set()
        for output in expected_outputs:
            if isinstance(output, dict):
                keys.update(output.keys())
        return sorted(keys)

    def _get_visible_expected_outputs(self, test_cases: List[Dict[str, Any]]) -> List[Any]:
        return [
            tc.get("expected_output")
            for tc in test_cases
            if not tc.get("is_hidden", False)
        ]

    async def get_problems(
        self,
        page: int = 1,
        page_size: int = 20,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        solve_status: Optional[str] = None
    ) -> ProblemListResponse:
        """
        Get paginated list of problems

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            difficulty: Filter by difficulty level
            category: Filter by category
            user_id: User ID for solve status calculation
            solve_status: Filter by solve status (solved, attempted, not_attempted)

        Returns:
            Paginated problem list
        """
        # Build base query
        query = select(Problem).where(Problem.is_active == True)

        # Apply filters
        if difficulty:
            query = query.where(Problem.difficulty == difficulty)
        if category:
            query = query.where(Problem.category == category)

        # Get total count (before solve_status filter for proper pagination)
        count_query = select(func.count()).select_from(query.subquery())

        # If user_id provided and solve_status filter requested, we need to handle it
        if user_id and solve_status:
            user_uuid = uuid.UUID(user_id)

            # Subqueries for solve status
            has_passed = exists(
                select(Submission.id).where(
                    and_(
                        Submission.problem_id == Problem.id,
                        Submission.user_id == user_uuid,
                        Submission.status == SubmissionStatus.PASSED
                    )
                )
            )
            has_any_submission = exists(
                select(Submission.id).where(
                    and_(
                        Submission.problem_id == Problem.id,
                        Submission.user_id == user_uuid
                    )
                )
            )

            if solve_status == SolveStatus.SOLVED.value:
                query = query.where(has_passed)
            elif solve_status == SolveStatus.ATTEMPTED.value:
                query = query.where(and_(has_any_submission, ~has_passed))
            elif solve_status == SolveStatus.NOT_ATTEMPTED.value:
                query = query.where(~has_any_submission)

            # Recalculate count with filter
            count_query = select(func.count()).select_from(query.subquery())

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Problem.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        problems = result.scalars().all()

        # Calculate solve status for each problem if user is authenticated
        solve_statuses: Dict[uuid.UUID, str] = {}
        if user_id and problems:
            user_uuid = uuid.UUID(user_id)
            problem_ids = [p.id for p in problems]

            # Get all submissions for these problems by this user
            submissions_query = select(
                Submission.problem_id,
                func.bool_or(Submission.status == SubmissionStatus.PASSED).label('has_passed')
            ).where(
                and_(
                    Submission.problem_id.in_(problem_ids),
                    Submission.user_id == user_uuid
                )
            ).group_by(Submission.problem_id)

            submissions_result = await self.db.execute(submissions_query)
            submissions_data = submissions_result.all()

            for row in submissions_data:
                if row.has_passed:
                    solve_statuses[row.problem_id] = SolveStatus.SOLVED.value
                else:
                    solve_statuses[row.problem_id] = SolveStatus.ATTEMPTED.value

        # Convert to response models
        problem_items = [
            ProblemListItem(
                id=p.id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty.value,
                category=p.category.value,
                total_submissions=p.total_submissions,
                successful_submissions=p.successful_submissions,
                success_rate=p.success_rate,
                solve_status=solve_statuses.get(p.id, SolveStatus.NOT_ATTEMPTED.value) if user_id else None
            )
            for p in problems
        ]

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return ProblemListResponse(
            problems=problem_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_problem_by_id(self, problem_id: str) -> ProblemDetail:
        """
        Get problem details by ID

        Args:
            problem_id: Problem UUID

        Returns:
            Problem details

        Raises:
            NotFoundError: If problem not found
        """
        result = await self.db.execute(
            select(Problem).where(
                and_(Problem.id == problem_id, Problem.is_active == True)
            )
        )
        problem = result.scalar_one_or_none()

        if not problem:
            raise NotFoundError("Problem not found")

        # Filter out hidden test cases
        visible_test_cases = [
            tc for tc in problem.test_cases
            if not tc.get("is_hidden", False)
        ]

        return ProblemDetail(
            id=problem.id,
            title=problem.title,
            slug=problem.slug,
            description=problem.description,
            difficulty=problem.difficulty.value,
            category=problem.category.value,
            starter_code=problem.starter_code,
            test_cases=visible_test_cases,
            constraints=problem.constraints,
            hints=problem.hints,
            time_complexity=problem.time_complexity,
            space_complexity=problem.space_complexity,
            total_submissions=problem.total_submissions,
            successful_submissions=problem.successful_submissions,
            success_rate=problem.success_rate,
            created_at=problem.created_at
        )

    async def list_problems_admin(
        self,
        page: int = 1,
        page_size: int = 20,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        query = select(Problem)
        if difficulty:
            query = query.where(Problem.difficulty == difficulty)
        if category:
            query = query.where(Problem.category == category)
        if is_active is not None:
            query = query.where(Problem.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Problem.created_at.desc())
        result = await self.db.execute(query)
        problems = result.scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return problems, total, total_pages

    async def get_problem_admin(self, problem_id: str) -> Problem:
        result = await self.db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()
        if not problem:
            raise NotFoundError("Problem not found")
        return problem

    async def update_problem_admin(self, problem_id: str, update_data) -> Problem:
        problem = await self.get_problem_admin(problem_id)

        data = update_data.model_dump(exclude_unset=True)
        for key, value in data.items():
            if key == "difficulty" and value is not None:
                value = DifficultyLevel(value)
            if key == "category" and value is not None:
                value = ProblemCategory(value)
            setattr(problem, key, value)

        await self.db.commit()
        await self.db.refresh(problem)
        return problem

    async def delete_problem_admin(self, problem_id: str) -> None:
        problem = await self.get_problem_admin(problem_id)
        problem.is_active = False
        await self.db.commit()

    async def import_problems_from_json(self, problems):
        created = 0
        updated = 0

        for item in problems:
            result = await self.db.execute(
                select(Problem).where(Problem.slug == item.slug)
            )
            existing = result.scalar_one_or_none()

            payload = item.model_dump(use_enum_values=True)

            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                self.db.add(Problem(**payload))
                created += 1

        await self.db.commit()
        return created, updated

    async def run_code(
        self,
        problem_id: str,
        request: CodeRunRequest
    ) -> CodeRunResponse:
        """
        Run code against visible test cases (no submission)

        Args:
            problem_id: Problem UUID
            request: Code run request

        Returns:
            Code execution results

        Raises:
            NotFoundError: If problem not found
        """
        # Get problem
        result = await self.db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()

        if not problem:
            raise NotFoundError("Problem not found")

        # Get only visible test cases for code run
        visible_test_cases = [
            tc for tc in problem.test_cases
            if not tc.get("is_hidden", False)
        ]

        if not visible_test_cases:
            raise NotFoundError("No test cases available")

        # Execute code
        try:
            execution_result = self.code_executor.execute_code(
                request.code,
                visible_test_cases
            )

            # Convert to response format
            test_results = [
                TestResult(**tr) for tr in execution_result["test_results"]
            ]

            # Determine status
            if execution_result["passed_tests"] == execution_result["total_tests"]:
                status = "passed"
            else:
                status = "failed"

            return CodeRunResponse(
                status=status,
                passed_tests=execution_result["passed_tests"],
                total_tests=execution_result["total_tests"],
                test_results=test_results,
                error_message=None,
                execution_time=execution_result["execution_time"]
            )

        except Exception as e:
            return CodeRunResponse(
                status="error",
                passed_tests=0,
                total_tests=len(visible_test_cases),
                test_results=[],
                error_message=str(e),
                execution_time=0
            )

    async def submit_code(
        self,
        problem_id: str,
        user_id: str,
        request: CodeSubmitRequest
    ) -> CodeSubmitResponse:
        """
        Submit code and run against all test cases (including hidden)

        Args:
            problem_id: Problem UUID
            user_id: User UUID
            request: Code submission request

        Returns:
            Submission results

        Raises:
            NotFoundError: If problem not found
        """
        # Get problem
        result = await self.db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()

        if not problem:
            raise NotFoundError("Problem not found")

        # Create submission record
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            code=request.code,
            language=request.language,
            status=SubmissionStatus.RUNNING
        )

        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)

        try:
            # Execute code against ALL test cases (including hidden)
            execution_result = self.code_executor.execute_code(
                request.code,
                problem.test_cases
            )

            visible_expected_outputs = self._get_visible_expected_outputs(problem.test_cases)
            expected_schema = self._extract_expected_schema(visible_expected_outputs)
            answer_payload = self._extract_answer_payload(execution_result) or {}
            explanation_result = self.explanation_evaluator.evaluate(
                problem_title=problem.title,
                problem_description=problem.description,
                constraints=problem.constraints or [],
                hints=problem.hints or [],
                expected_outputs=visible_expected_outputs,
                expected_schema=expected_schema,
                answer_payload=answer_payload
            )

            # Update submission with results
            tests_passed = execution_result["passed_tests"] == execution_result["total_tests"]
            explanation_passed = explanation_result.passed
            submission.status = (
                SubmissionStatus.PASSED
                if tests_passed and explanation_passed
                else SubmissionStatus.FAILED
            )
            submission.test_results = execution_result["test_results"]
            submission.passed_tests = execution_result["passed_tests"]
            submission.total_tests = execution_result["total_tests"]
            submission.execution_time = execution_result["execution_time"]
            submission.completed_at = datetime.utcnow()

            # Update problem statistics
            problem.total_submissions += 1
            if submission.status == SubmissionStatus.PASSED:
                problem.successful_submissions += 1

            await self.db.commit()
            await self.db.refresh(submission)

            # Prepare response (hide hidden test case details)
            test_results = []
            for tr in execution_result["test_results"]:
                test_result = TestResult(**tr)
                test_results.append(test_result)

            return CodeSubmitResponse(
                submission_id=submission.id,
                status=submission.status.value,
                passed_tests=submission.passed_tests,
                total_tests=submission.total_tests,
                test_results=test_results,
                error_message=None,
                execution_time=submission.execution_time,
                memory_used=submission.memory_used,
                submitted_at=submission.submitted_at,
                explanation_score=explanation_result.score,
                explanation_feedback=explanation_result.feedback,
                explanation_passed=explanation_result.passed
            )

        except Exception as e:
            # Update submission with error
            submission.status = SubmissionStatus.ERROR
            submission.error_message = str(e)
            submission.completed_at = datetime.utcnow()

            # Still update problem stats
            problem.total_submissions += 1

            await self.db.commit()
            await self.db.refresh(submission)

            return CodeSubmitResponse(
                submission_id=submission.id,
                status=submission.status.value,
                passed_tests=0,
                total_tests=len(problem.test_cases),
                test_results=None,
                error_message=str(e),
                execution_time=0,
                memory_used=None,
                submitted_at=submission.submitted_at,
                explanation_score=None,
                explanation_feedback=None,
                explanation_passed=None
            )
