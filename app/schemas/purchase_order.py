from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class POItemData(BaseModel):
    item_id: str
    quantity: Decimal
    unit_price: Decimal = Decimal("0")
    urutan: int = 0
    notes: Optional[str] = None


class POItemResponse(BaseModel):
    id: str
    purchase_order_id: str
    item_id: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    urutan: int
    notes: Optional[str] = None
    class Config: from_attributes = True


class PurchaseOrderCreate(BaseModel):
    supplier_id: Optional[str] = None
    order_date: Optional[date] = None
    expected_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_po_file: Optional[str] = None
    items: list[POItemData] = []


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[str] = None
    order_date: Optional[date] = None
    expected_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_po_file: Optional[str] = None
    items: Optional[list[POItemData]] = None


class PurchaseOrderResponse(BaseModel):
    id: str
    nomor: str
    supplier_id: Optional[str] = None
    status: str
    total: Decimal
    order_date: Optional[date] = None
    expected_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_po_file: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    items: list[POItemResponse] = []
