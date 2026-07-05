from sqlalchemy import Boolean, Column, Date, Integer, Numeric, String, Text, ForeignKey
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class SalesOrder(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "sales_orders"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    penawaran_id = Column(String(36), ForeignKey("penawaran.id"), nullable=True)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    ppn_amount = Column(Numeric(15, 2), default=0, nullable=False)
    grand_total = Column(Numeric(15, 2), default=0, nullable=False)
    margin = Column(Numeric(15, 2), nullable=True)
    order_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)
    delivery_address = Column(Text, nullable=True)


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(String(36), primary_key=True, default=new_id)
    sales_order_id = Column(String(36), ForeignKey("sales_orders.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_price = Column(Numeric(15, 2), default=0, nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
