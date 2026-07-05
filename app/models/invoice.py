from sqlalchemy import String, Text, ForeignKey, Column, Integer, Numeric, Date
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class Invoice(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    sales_order_id = Column(String(36), ForeignKey("sales_orders.id"), nullable=True)
    delivery_note_id = Column(String(36), ForeignKey("delivery_notes.id"), nullable=True)
    status = Column(String(20), default="draft", nullable=False)  # draft, locked, paid, bad_debt
    total = Column(Numeric(15, 2), default=0, nullable=False)
    ppn_amount = Column(Numeric(15, 2), default=0, nullable=False)
    grand_total = Column(Numeric(15, 2), default=0, nullable=False)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    terms_of_payment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)
    terms_of_delivery = Column(Text, nullable=True)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, default=new_id)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_price = Column(Numeric(15, 2), default=0, nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
