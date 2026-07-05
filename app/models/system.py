import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from app.models.base import Base, TimestampMixin, new_id

WIB = timezone(timedelta(hours=7))


class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=new_id)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)


class Counter(Base):
    __tablename__ = "counters"
    __table_args__ = (UniqueConstraint("type", "year"),)

    id = Column(String(36), primary_key=True, default=new_id)
    type = Column(String(30), nullable=False)
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=new_id)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(36), nullable=False)
    action = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    user_info = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(WIB), nullable=False)
