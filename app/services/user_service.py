"""
User service for admin operations
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User


class UserService:
    """Service for user admin operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None
    ) -> Tuple[List[User], int]:
        query = select(User)
        if role:
            query = query.where(User.role == role)

        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        users = result.scalars().all()
        return users, total
