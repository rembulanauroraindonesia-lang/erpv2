from sqlalchemy import Boolean, Column, Date, Integer, String, Text, ForeignKey
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, new_id


class Contact(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=new_id)
    type = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    npwp = Column(String(50), nullable=True)
    tax_info = Column(Text, nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(50), nullable=True)  # PIC mobile number
    terms_of_payment = Column(Text, nullable=True)  # default payment terms
    terms_of_delivery = Column(Text, nullable=True)  # default delivery terms
    notes = Column(Text, nullable=True)


class ContactTopHistory(Base):
    __tablename__ = "contact_top_history"

    id = Column(String(36), primary_key=True, default=new_id)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False)
    top_type = Column(String(20), nullable=False)
    tempo_days = Column(Integer, nullable=True)
    effective_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(Date, nullable=True)
