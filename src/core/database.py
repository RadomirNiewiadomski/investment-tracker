"""
Database connection and session management using SQLAlchemy 2.0 (Async).
"""

import re
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

from src.core.config import settings

# Create Async Engine (for managing Connection Pool)
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,  # Set to False in production
    future=True,
)

# Create Session Factory (new AsyncSession instances for each request)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate snake_case table name from CamelCase class name.
        Example: 'UserPortfolio' -> 'user_portfolio'
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    def __repr__(self) -> str:
        """
        String representation of the model showing Primary Key(s).
        Example: <User(id=1)>
        """
        pk_cols = [c.name for c in self.__table__.primary_key]

        params = ", ".join(f"{key}={getattr(self, key)}" for key in pk_cols)

        return f"<{self.__class__.__name__}({params})>"


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    Dependency to provide a database session for a request.
    Ensures the session is closed after the request is finished.

    Yields:
        AsyncSession: The database session.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from src.modules.auth.models import User  # noqa: F401, E402
from src.modules.portfolio.models import Asset, Portfolio  # noqa: F401, E402
