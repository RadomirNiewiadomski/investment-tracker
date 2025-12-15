from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password
from src.modules.auth.schemas import UserCreate
from src.modules.auth.service import AuthService


@pytest.mark.asyncio
async def test_create_user_success():
    """
    Ensure a user can be successfully created with a hashed password.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    user_in = UserCreate(email="new@example.com", password="secret_password", first_name="John", last_name="Doe")
    service = AuthService()

    user = await service.create_user(mock_session, user_in)

    assert user.email == "new@example.com"
    assert user.hashed_password != "secret_password"
    assert verify_password("secret_password", user.hashed_password)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_already_exists():
    """
    Ensure registration fails with 400 Bad Request when the email is already taken.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    existing_user = MagicMock()
    existing_user.email = "exists@example.com"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_user
    mock_session.execute.return_value = mock_result

    user_in = UserCreate(email="exists@example.com", password="password")
    service = AuthService()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_user(mock_session, user_in)

    assert exc_info.value.status_code == 400
    assert "Email already registered" in exc_info.value.detail

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
