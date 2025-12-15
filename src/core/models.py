"""
Common model mixins for reusability across the application.
"""

import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """
    Mixin that adds a UUID column to a model.
    """

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid_pkg.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
