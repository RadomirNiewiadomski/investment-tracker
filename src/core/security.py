"""
Security utilities for password hashing and token management.
Using pwdlib with Argon2 and PyJWT.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from src.core.config import settings

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain password matches the hashed password.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    return password_hash.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The principal (usually user ID or email) to identify the user.
        expires_delta: Optional custom expiration time.

    Returns:
        str: Encoded JWT token.
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
