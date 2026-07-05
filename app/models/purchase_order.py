from sqlalchemy import String, Text, ForeignKey, Boolean, Column, Integer, Numeric, Date
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class PurchaseOrder(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    supplier_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    order_date = Column(Date, nullable=True)
    expected_date = Column(Date, nullable=True)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(String(36), primary_key=True, default=new_id)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_price = Column(Numeric(15, 2), default=0, nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
