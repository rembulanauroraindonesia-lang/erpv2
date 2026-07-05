from sqlalchemy import String, Text, ForeignKey, Column, Integer, Numeric, Date
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class ProformaInvoice(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "proforma_invoices"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    sales_order_id = Column(String(36), ForeignKey("sales_orders.id"), nullable=True)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    status = Column(String(20), default="draft", nullable=False)  # draft, sent, paid, cancelled, revised, obsolete
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    ppn_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    due_date = Column(Date, nullable=True)
    payment_method = Column(String(20), nullable=True)  # transfer, giro, cek
    bukti_bayar_file = Column(String(500), nullable=True)
    bukti_giro_cek_file = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    pic_name = Column(String(100), nullable=True)
    pic_phone = Column(String(50), nullable=True)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)


class ProformaInvoiceItem(Base):
    __tablename__ = "proforma_invoice_items"

    id = Column(String(36), primary_key=True, default=new_id)
    proforma_invoice_id = Column(String(36), ForeignKey("proforma_invoices.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_price = Column(Numeric(15, 2), default=0, nullable=False)
    total = Column(Numeric(15, 2), default=0, nullable=False)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
