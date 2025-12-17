"""
API Router for Authentication module.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token
from src.modules.auth.schemas import Token, UserCreate, UserLogin, UserRead
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


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return JWT access token.",
)
async def login(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_db),
) -> Token:
    """
    Handle user login and token generation.
    """
    service = AuthService()

    user = await service.authenticate_user(session, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.uuid)

    return Token(access_token=access_token, token_type="bearer")
