from sqlalchemy import String, Text, ForeignKey, Column, Integer, Numeric, Date, DateTime, func
from app.models.base import Base, TimestampMixin, new_id


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=new_id)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    proforma_invoice_id = Column(String(36), ForeignKey("proforma_invoices.id"), nullable=True)
    payment_number = Column(String(20), nullable=False, unique=True)
    amount = Column(Numeric(15, 2), default=0, nullable=False)
    payment_method = Column(String(20), nullable=True)  # transfer, giro, cek, cash
    status = Column(String(20), default="pending", nullable=False)  # pending, cleared, extended, bad_debt, cancelled
    payment_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    cleared_date = Column(Date, nullable=True)
    bukti_bayar_file = Column(String(500), nullable=True)
    bukti_giro_cek_file = Column(String(500), nullable=True)
    giro_bank = Column(String(100), nullable=True)
    giro_number = Column(String(50), nullable=True)
    extension_count = Column(Integer, default=0, nullable=False)
    bad_debt_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id = Column(String(36), primary_key=True, default=new_id)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    action = Column(String(30), nullable=False)  # created, cleared, extended, bad_debt_declared, cancelled
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    amount_before = Column(Numeric(15, 2), nullable=True)
    amount_after = Column(Numeric(15, 2), nullable=True)
    due_date_before = Column(Date, nullable=True)
    due_date_after = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    user_info = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
