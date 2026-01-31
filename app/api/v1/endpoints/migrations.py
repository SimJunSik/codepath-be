"""
Migration endpoints for admin
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.api.v1.deps import get_current_admin_user

router = APIRouter()


@router.post("/enum-values")
async def add_missing_enum_values(
    db: AsyncSession = Depends(get_db),
    _admin_user=Depends(get_current_admin_user)
):
    """Add missing enum values to database"""

    results = {
        "added_categories": [],
        "existing_categories": [],
        "added_difficulties": [],
        "existing_difficulties": []
    }

    # Check and add ProblemCategory values
    result = await db.execute(text(
        "SELECT enumlabel FROM pg_enum e "
        "JOIN pg_type t ON e.enumtypid = t.oid "
        "WHERE t.typname = 'problemcategory'"
    ))
    existing_categories = {row[0] for row in result.fetchall()}

    category_values = [
        'BASICS', 'COLLECTIONS', 'FUNCTION', 'CONTROL_FLOW',
        'STRING', 'BUILTIN', 'EXCEPTION', 'IO', 'MODULE',
        'UNPACKING', 'SYNTAX', 'TRUTHINESS', 'BEST_PRACTICE'
    ]

    for value in category_values:
        if value not in existing_categories:
            await db.execute(text(f"ALTER TYPE problemcategory ADD VALUE '{value}'"))
            results["added_categories"].append(value)
        else:
            results["existing_categories"].append(value)

    # Check and add DifficultyLevel values (should already exist)
    result = await db.execute(text(
        "SELECT enumlabel FROM pg_enum e "
        "JOIN pg_type t ON e.enumtypid = t.oid "
        "WHERE t.typname = 'difficultylevel'"
    ))
    existing_difficulties = {row[0] for row in result.fetchall()}

    difficulty_values = ['BEGINNER', 'EASY', 'MEDIUM', 'HARD', 'EXPERT']

    for value in difficulty_values:
        if value not in existing_difficulties:
            await db.execute(text(f"ALTER TYPE difficultylevel ADD VALUE '{value}'"))
            results["added_difficulties"].append(value)
        else:
            results["existing_difficulties"].append(value)

    await db.commit()

    return {
        "success": True,
        "message": f"Added {len(results['added_categories'])} category values and {len(results['added_difficulties'])} difficulty values",
        "details": results
    }
