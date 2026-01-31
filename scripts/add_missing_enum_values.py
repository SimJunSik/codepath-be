"""
Add missing enum values to PostgreSQL
Run this script to update production database
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def add_enum_values():
    """Add missing enum values to PostgreSQL"""

    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        print("=" * 60)
        print("Adding missing enum values to PostgreSQL")
        print("=" * 60)

        # ProblemCategory enum values
        category_values = [
            'BASICS', 'COLLECTIONS', 'FUNCTION', 'CONTROL_FLOW',
            'STRING', 'BUILTIN', 'EXCEPTION', 'IO', 'MODULE',
            'UNPACKING', 'SYNTAX', 'TRUTHINESS', 'BEST_PRACTICE'
        ]

        # Check existing category values first
        result = await conn.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = 'problemcategory'"
        ))
        existing_categories = {row[0] for row in result.fetchall()}

        print("\n📝 Adding ProblemCategory enum values...")
        for value in category_values:
            if value in existing_categories:
                print(f"  ⏭️  {value} (already exists)")
            else:
                try:
                    await conn.execute(text(f"ALTER TYPE problemcategory ADD VALUE '{value}'"))
                    print(f"  ✅ {value}")
                except Exception as e:
                    print(f"  ❌ Error adding {value}: {e}")

        # Check existing difficulty values
        result = await conn.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = 'difficultylevel'"
        ))
        existing_difficulties = {row[0] for row in result.fetchall()}

        difficulty_values = ['BEGINNER', 'EASY', 'MEDIUM', 'HARD', 'EXPERT']

        print("\n📝 Checking DifficultyLevel enum values...")
        for value in difficulty_values:
            if value in existing_difficulties:
                print(f"  ⏭️  {value} (already exists)")
            else:
                try:
                    await conn.execute(text(f"ALTER TYPE difficultylevel ADD VALUE '{value}'"))
                    print(f"  ✅ {value}")
                except Exception as e:
                    print(f"  ❌ Error adding {value}: {e}")

        print("\n" + "=" * 60)
        print("✅ Enum values update completed!")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify the database schema!")
    print("Make sure you're running this on the correct database.\n")
    print(f"Database URL: {settings.DATABASE_URL[:50]}...")

    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        asyncio.run(add_enum_values())
    else:
        print("Aborted.")
