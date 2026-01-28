"""
Problem related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class ProblemListItem(BaseModel):
    """Problem list item response"""
    id: uuid.UUID
    title: str
    slug: str
    difficulty: str
    category: str
    total_submissions: int
    successful_submissions: int
    success_rate: float

    class Config:
        from_attributes = True


class ProblemListResponse(BaseModel):
    """Paginated problem list response"""
    problems: List[ProblemListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestCase(BaseModel):
    """Test case schema"""
    input: Dict[str, Any]
    expected_output: Any
    is_hidden: bool = False


class ProblemDetail(BaseModel):
    """Problem detail response"""
    id: uuid.UUID
    title: str
    slug: str
    description: str
    difficulty: str
    category: str
    starter_code: str
    test_cases: List[Dict[str, Any]]  # Only non-hidden test cases
    constraints: Optional[List[str]]
    hints: Optional[List[str]]
    time_complexity: Optional[str]
    space_complexity: Optional[str]
    total_submissions: int
    successful_submissions: int
    success_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class CodeRunRequest(BaseModel):
    """Code run request"""
    code: str = Field(..., description="Python code to run")
    language: str = Field(default="python", description="Programming language")


class TestResult(BaseModel):
    """Individual test result"""
    test_id: int
    passed: bool
    input: Dict[str, Any]
    expected: Any
    actual: Optional[Any]
    error: Optional[str]
    execution_time: Optional[int]  # milliseconds


class CodeRunResponse(BaseModel):
    """Code run response"""
    status: str
    passed_tests: int
    total_tests: int
    test_results: List[TestResult]
    error_message: Optional[str]
    execution_time: Optional[int]


class CodeSubmitRequest(BaseModel):
    """Code submission request"""
    code: str = Field(..., description="Python code to submit")
    language: str = Field(default="python", description="Programming language")


class CodeSubmitResponse(BaseModel):
    """Code submission response"""
    submission_id: uuid.UUID
    status: str
    passed_tests: int
    total_tests: int
    test_results: Optional[List[TestResult]]
    error_message: Optional[str]
    execution_time: Optional[int]
    memory_used: Optional[int]
    submitted_at: datetime
    explanation_score: Optional[int]
    explanation_feedback: Optional[str]
    explanation_passed: Optional[bool]

    class Config:
        from_attributes = True
