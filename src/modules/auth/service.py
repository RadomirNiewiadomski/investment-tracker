"""
Service layer for Authentication module.
Handles business logic for user registration and management.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash, verify_password
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

    async def authenticate_user(self, session: AsyncSession, email: str, password: str) -> User | None:
        """
        Authenticate a user by email and password.

        Args:
            session: Database session.
            email: User's email.
            password: Plain text password to verify.

        Returns:
            User | None: User object if credentials are valid, otherwise None.
        """
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
