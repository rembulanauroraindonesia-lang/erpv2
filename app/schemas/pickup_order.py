from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class PUItemData(BaseModel):
    item_id: str
    quantity: Decimal
    urutan: int = 0
    notes: Optional[str] = None


class PUItemResponse(BaseModel):
    id: str
    pickup_order_id: str
    item_id: str
    quantity: Decimal
    urutan: int
    notes: Optional[str] = None
    class Config: from_attributes = True


class PickupOrderCreate(BaseModel):
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    pickup_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None
    items: list[PUItemData] = []


class PickupOrderUpdate(BaseModel):
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    pickup_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[PUItemData]] = None


class PickupOrderResponse(BaseModel):
    id: str
    nomor: str
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    pickup_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    status: str
    notes: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class PickupOrderDetailResponse(PickupOrderResponse):
    items: list[PUItemResponse] = []
