"""
Submission database model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"


class Submission(Base):
    """Submission model"""
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)

    # Submission data
    code = Column(Text, nullable=False)
    language = Column(String(20), default="python", nullable=False)

    # Execution results
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False, index=True)

    # Test results stored as JSON
    # Format: [{"test_id": int, "passed": bool, "input": {...}, "expected": {...}, "actual": {...}, "error": str}]
    test_results = Column(JSON, nullable=True)

    passed_tests = Column(Integer, default=0, nullable=False)
    total_tests = Column(Integer, default=0, nullable=False)

    # Execution metrics
    execution_time = Column(Integer, nullable=True)  # milliseconds
    memory_used = Column(Integer, nullable=True)  # bytes

    # Error information
    error_message = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")

    @property
    def is_successful(self) -> bool:
        """Check if submission passed all tests"""
        return self.status == SubmissionStatus.PASSED and self.passed_tests == self.total_tests

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this submission"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def __repr__(self):
        return f"<Submission {self.id} - {self.status.value}>"
