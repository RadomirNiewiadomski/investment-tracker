"""
Database models for the Authentication module.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models import TimestampMixin, UUIDMixin


class User(Base, TimestampMixin, UUIDMixin):
    """
    User model representing a registered user in the system.
    """

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), default=None)
    last_name: Mapped[str | None] = mapped_column(String(100), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    def __str__(self) -> str:
        return self.email
