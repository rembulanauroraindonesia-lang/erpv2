from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class PenawaranItemData(BaseModel):
    item_id: str
    supplier_id: Optional[str] = None
    quantity: Decimal
    berat_beli_per_unit: Decimal = Decimal("0")
    hpp_per_unit: Decimal = Decimal("0")
    harga_jual_per_unit: Decimal = Decimal("0")
    different_scale: bool = False
    berat_jual_per_unit: Optional[Decimal] = None
    urutan: int = 0
    notes: Optional[str] = None


class PenawaranItemResponse(BaseModel):
    id: str
    penawaran_id: str
    item_id: str
    supplier_id: Optional[str] = None
    quantity: Decimal
    berat_beli_per_unit: Decimal
    hpp_per_unit: Decimal
    total_beli: Decimal
    harga_jual_per_unit: Decimal
    total_jual: Decimal
    different_scale: bool
    berat_jual_per_unit: Optional[Decimal] = None
    urutan: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PenawaranCreate(BaseModel):
    customer_id: Optional[str] = None
    supplier_mode: str = "single"
    price_mode: str = "include_ppn"
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    customer_po_number: Optional[str] = None
    notes: Optional[str] = None
    items: list[PenawaranItemData] = []


class PenawaranUpdate(BaseModel):
    customer_id: Optional[str] = None
    supplier_mode: Optional[str] = None
    price_mode: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    customer_po_number: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[PenawaranItemData]] = None


class PenawaranResponse(BaseModel):
    id: str
    nomor: str
    customer_id: Optional[str] = None
    supplier_mode: str
    price_mode: str
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    customer_po_number: Optional[str] = None
    notes: Optional[str] = None
    status: str
    total_beli: Decimal
    total_jual: Decimal
    ppn_amount: Decimal
    grand_total: Decimal
    margin: Optional[Decimal] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PenawaranDetailResponse(PenawaranResponse):
    items: list[PenawaranItemResponse] = []
