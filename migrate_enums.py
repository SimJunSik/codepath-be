"""
One-time migration script to add missing enum values
Run this inside ECS container or any environment with DB access
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
import sys

async def add_enum_values():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    engine = create_async_engine(database_url)

    print('=' * 60)
    print('Adding missing enum values to database')
    print('=' * 60)

    try:
        async with engine.begin() as conn:
            # Check existing category values
            result = await conn.execute(text(
                "SELECT enumlabel FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "WHERE t.typname = 'problemcategory'"
            ))
            existing_categories = {row[0] for row in result.fetchall()}

            print('\n📝 Existing ProblemCategory values:')
            print(f'   {sorted(existing_categories)}')

            # Add missing values
            category_values = [
                'BASICS', 'COLLECTIONS', 'FUNCTION', 'CONTROL_FLOW',
                'STRING', 'BUILTIN', 'EXCEPTION', 'IO', 'MODULE',
                'UNPACKING', 'SYNTAX', 'TRUTHINESS', 'BEST_PRACTICE'
            ]

            print('\n📝 Adding missing ProblemCategory values:')
            added = 0
            for value in category_values:
                if value not in existing_categories:
                    await conn.execute(text(f"ALTER TYPE problemcategory ADD VALUE '{value}'"))
                    print(f'   ✅ Added: {value}')
                    added += 1
                else:
                    print(f'   ⏭️  Exists: {value}')

            # Check difficulty values
            result = await conn.execute(text(
                "SELECT enumlabel FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "WHERE t.typname = 'difficultylevel'"
            ))
            existing_difficulties = {row[0] for row in result.fetchall()}

            print('\n📝 Existing DifficultyLevel values:')
            print(f'   {sorted(existing_difficulties)}')

            print('\n' + '=' * 60)
            print(f'✅ Migration completed! Added {added} new enum values.')
            print('=' * 60)

    except Exception as e:
        print(f'\n❌ Error: {e}')
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_enum_values())
