import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

WIB = timezone(timedelta(hours=7))


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(WIB), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(WIB),
        onupdate=lambda: datetime.now(WIB),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)


class RevisionMixin:
    version = Column(Integer, default=1, nullable=False)
    parent_id = Column(String(36), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)


def new_id() -> str:
    return str(uuid.uuid4())
