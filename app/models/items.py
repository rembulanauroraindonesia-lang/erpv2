from sqlalchemy import Column, Numeric, String, Text
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, new_id


class Item(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=new_id)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=True, unique=True)
    unit = Column(String(20), default="pcs", nullable=False)
    default_hpp = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
