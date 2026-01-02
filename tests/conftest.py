"""
Global fixtures for pytest.
Configures a separate TEST DATABASE to ensure isolation from development data.
"""

import uuid
from collections.abc import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.database import Base, get_db
from src.core.security import create_access_token, get_password_hash
from src.main import app
from src.modules.auth.models import User

TEST_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI).replace(
    f"/{settings.POSTGRES_DB}", "/investment_tracker_test"
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Creates tables in the separate TEST database at the start of the session
    and drops them at the end.
    Does NOT affect the development database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh session for each test using the TEST database.
    Rolls back changes after test execution.
    """
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Creates a Test Client where the 'get_db' dependency is overridden
    to use the test database session.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def user_factory(db_session: AsyncSession) -> Callable[[str], User]:
    """
    Fixture that returns a function to create a user with a specific email
    in the TEST database.
    """

    async def _create_user(email: str = "test_factory@example.com") -> User:
        hashed_pw = get_password_hash("secret")
        user = User(email=email, hashed_password=hashed_pw, is_active=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture(scope="function")
async def auth_headers(user_factory) -> dict[str, str]:
    """
    Helper fixture to create a user, generate a valid JWT token,
    and return authorization headers.
    """
    random_email = f"tester_{uuid.uuid4()}@example.com"
    user = await user_factory(random_email)
    token = create_access_token(subject=str(user.uuid))
    return {"Authorization": f"Bearer {token}"}
