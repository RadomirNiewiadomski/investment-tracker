"""
Global fixtures for pytest.
"""

from collections.abc import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, async_session_maker, engine
from src.core.security import get_password_hash
from src.main import app
from src.modules.auth.models import User


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Create tables before tests and drop them after.
    This fixture runs automatically for the whole session.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for a test function.
    Rolls back transaction after test to keep DB clean.
    """
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an asynchronous HTTP client for testing.

    Yields:
        AsyncClient: An httpx client configured to communicate with the FastAPI app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def user_factory(get_db: AsyncSession) -> Callable[[str], User]:
    """
    Fixture that returns a function to create a user with a specific email.

    Args:
        get_db: The database session fixture.

    Returns:
        Callable: An async function that takes an email and returns a created User.
    """

    async def _create_user(email: str = "test_factory@example.com") -> User:
        hashed_pw = get_password_hash("secret")
        user = User(email=email, hashed_password=hashed_pw, is_active=True)
        get_db.add(user)
        await get_db.commit()
        await get_db.refresh(user)
        return user

    return _create_user
