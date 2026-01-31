"""
Problem database model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class DifficultyLevel(str, enum.Enum):
    """Problem difficulty levels"""
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ProblemCategory(str, enum.Enum):
    """Problem categories - Python Deep Dive"""
    # Beginner basics
    BASICS = "basics"

    # Core Python internals
    GIL = "gil"
    CPYTHON = "cpython"
    MEMORY = "memory"

    # Data structures
    DATA_STRUCTURE = "data_structure"
    COPY = "copy"
    COLLECTIONS = "collections"

    # Functions and control flow
    GENERATOR = "generator"
    DECORATOR = "decorator"
    CLOSURE = "closure"
    FUNCTION = "function"
    CONTROL_FLOW = "control_flow"

    # OOP and concurrency
    CONCURRENCY = "concurrency"
    OOP = "oop"

    # Basic Python concepts
    STRING = "string"
    BUILTIN = "builtin"
    EXCEPTION = "exception"
    IO = "io"
    MODULE = "module"
    UNPACKING = "unpacking"
    SYNTAX = "syntax"
    TRUTHINESS = "truthiness"
    BEST_PRACTICE = "best_practice"


class Problem(Base):
    """Problem model"""
    __tablename__ = "problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)

    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, index=True)
    category = Column(SQLEnum(ProblemCategory), nullable=False, index=True)

    # Starter code and solution
    starter_code = Column(Text, nullable=False)
    solution_code = Column(Text, nullable=True)

    # Test cases stored as JSON
    # Format: [{"input": {...}, "expected_output": {...}, "is_hidden": bool}]
    test_cases = Column(JSON, nullable=False)

    # Constraints and hints
    constraints = Column(JSON, nullable=True)  # ["constraint1", "constraint2"]
    hints = Column(JSON, nullable=True)  # ["hint1", "hint2"]

    # Time/Space complexity for solution
    time_complexity = Column(String(50), nullable=True)
    space_complexity = Column(String(50), nullable=True)

    # Problem stats
    total_submissions = Column(Integer, default=0, nullable=False)
    successful_submissions = Column(Integer, default=0, nullable=False)

    # Visibility
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_submissions == 0:
            return 0.0
        return (self.successful_submissions / self.total_submissions) * 100

    def __repr__(self):
        return f"<Problem {self.title} ({self.difficulty.value})>"
