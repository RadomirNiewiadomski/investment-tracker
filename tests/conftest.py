"""
Global fixtures for pytest.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, async_session_maker, engine
from src.main import app


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
