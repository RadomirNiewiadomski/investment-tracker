"""
API Router for Authentication module.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.schemas import UserCreate, UserRead
from src.modules.auth.service import AuthService

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with hashed password.",
)
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    """
    Handle user registration.
    """
    service = AuthService()
    return await service.create_user(session, user_in)
