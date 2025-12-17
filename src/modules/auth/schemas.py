"""
Pydantic schemas for the Auth module.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema with common fields."""

    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for user registration.
    """

    password: str = Field(min_length=8, description="Password must be at least 8 characters long.")
    first_name: str | None = None
    last_name: str | None = None


class UserRead(UserBase):
    """
    Schema for returning user data (Response).
    """

    id: int
    uuid: UUID
    is_active: bool
    first_name: str | None
    last_name: str | None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Schema for JWT access token response.
    """

    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    """
    Schema for user login request.
    """

    email: EmailStr
    password: str
