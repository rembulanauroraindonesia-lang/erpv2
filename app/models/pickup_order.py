from sqlalchemy import String, Text, ForeignKey, Column, Integer, Numeric, Date
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class PickupOrder(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "pickup_orders"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    supplier_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True)
    pickup_date = Column(Date, nullable=True)
    vehicle_plate = Column(String(20), nullable=True)
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(50), nullable=True)
    expedition_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)  # expedition yg pickup
    received_date = Column(Date, nullable=True)  # kapan barang sampai
    status = Column(String(20), default="draft", nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)
    pickup_address = Column(Text, nullable=True)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)


class PickupOrderItem(Base):
    __tablename__ = "pickup_order_items"

    id = Column(String(36), primary_key=True, default=new_id)
    pickup_order_id = Column(String(36), ForeignKey("pickup_orders.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
