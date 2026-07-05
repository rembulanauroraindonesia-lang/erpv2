from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text, ForeignKey
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class Penawaran(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "penawaran"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    supplier_mode = Column(String(10), default="single", nullable=False)
    price_mode = Column(String(20), default="include_ppn", nullable=False)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)
    validity_days = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    total_beli = Column(Numeric(15, 2), default=0, nullable=False)
    total_jual = Column(Numeric(15, 2), default=0, nullable=False)
    ppn_amount = Column(Numeric(15, 2), default=0, nullable=False)
    grand_total = Column(Numeric(15, 2), default=0, nullable=False)
    margin = Column(Numeric(15, 2), nullable=True)
    created_by = Column(String(100), nullable=True)


class PenawaranItem(Base):
    __tablename__ = "penawaran_items"

    id = Column(String(36), primary_key=True, default=new_id)
    penawaran_id = Column(String(36), ForeignKey("penawaran.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    supplier_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    berat_beli_per_unit = Column(Numeric(10, 4), default=0, nullable=False)
    hpp_per_unit = Column(Numeric(15, 2), default=0, nullable=False)
    total_beli = Column(Numeric(15, 2), default=0, nullable=False)
    harga_jual_per_unit = Column(Numeric(15, 2), default=0, nullable=False)
    total_jual = Column(Numeric(15, 2), default=0, nullable=False)
    different_scale = Column(Boolean, default=False, nullable=False)
    berat_jual_per_unit = Column(Numeric(10, 4), nullable=True)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
