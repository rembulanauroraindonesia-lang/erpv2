from sqlalchemy import String, Text, ForeignKey, Column, Integer, Numeric, Date
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class DeliveryNote(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "delivery_notes"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    so_id = Column(String(36), ForeignKey("sales_orders.id"), nullable=True)
    delivery_date = Column(Date, nullable=True)
    vehicle_plate = Column(String(20), nullable=True)
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(50), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)
    delivery_address = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)


class DeliveryNoteItem(Base):
    __tablename__ = "delivery_note_items"

    id = Column(String(36), primary_key=True, default=new_id)
    delivery_note_id = Column(String(36), ForeignKey("delivery_notes.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
