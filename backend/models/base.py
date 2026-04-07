"""SQLAlchemy declarative base and common mixins."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


class TimestampMixin:
    """Mixin for created_at timestamp."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key."""
    pass  # Each model defines its own PK with specific column name
