"""
Service layer for Authentication module.
Handles business logic for user registration and management.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.modules.auth.models import User
from src.modules.auth.schemas import UserCreate


class AuthService:
    """
    Service responsible for user authentication logic.
    """

    async def create_user(self, session: AsyncSession, user_in: UserCreate) -> User:
        """
        Creates a new user in the database.

        Args:
            session: Database session.
            user_in: User creation data (DTO).

        Returns:
            User: The created user model instance.

        Raises:
            HTTPException: If the email is already registered.
        """
        stmt = select(User).where(User.email == user_in.email)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            first_name=user_in.first_name,
            last_name=user_in.last_name,
        )

        session.add(db_user)
        await session.commit()

        await session.refresh(db_user)

        return db_user
