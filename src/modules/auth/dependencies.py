"""
FastAPI dependencies for Authentication module.
Handles JWT token verification and user retrieval.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.modules.auth.models import User

security = HTTPBearer()


async def get_current_user(
    token_creds: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency that validates the JWT token and returns the current user.

    Args:
        token: JWT token extracted from the Authorization header.
        session: Database session.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If token is invalid, expired, or user not found.
    """
    token = token_creds.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_uuid: str | None = payload.get("sub")

        if user_uuid is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception from None

    stmt = select(User).where(User.uuid == user_uuid)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user
