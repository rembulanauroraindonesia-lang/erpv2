from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class SOItemData(BaseModel):
    item_id: str
    quantity: Decimal
    unit_price: Decimal = Decimal("0")
    urutan: int = 0
    notes: Optional[str] = None


class SOItemResponse(BaseModel):
    id: str
    sales_order_id: str
    item_id: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    urutan: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SalesOrderCreate(BaseModel):
    penawaran_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    items: list[SOItemData] = []


class SalesOrderUpdate(BaseModel):
    customer_id: Optional[str] = None
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[SOItemData]] = None


class SalesOrderResponse(BaseModel):
    id: str
    nomor: str
    penawaran_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: str
    total: Decimal
    ppn_amount: Decimal
    grand_total: Decimal
    margin: Optional[Decimal] = None
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesOrderDetailResponse(SalesOrderResponse):
    items: list[SOItemResponse] = []
