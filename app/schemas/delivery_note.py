from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class DNItemData(BaseModel):
    item_id: str
    quantity: Decimal
    urutan: int = 0
    notes: Optional[str] = None


class DNItemResponse(BaseModel):
    id: str
    delivery_note_id: str
    item_id: str
    quantity: Decimal
    urutan: int
    notes: Optional[str] = None
    class Config: from_attributes = True


class DeliveryNoteCreate(BaseModel):
    customer_id: Optional[str] = None
    so_id: Optional[str] = None
    delivery_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None
    bukti_kirim_file: Optional[str] = None
    items: list[DNItemData] = []


class DeliveryNoteUpdate(BaseModel):
    customer_id: Optional[str] = None
    so_id: Optional[str] = None
    delivery_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None
    bukti_kirim_file: Optional[str] = None
    items: Optional[list[DNItemData]] = None


class DeliveryNoteResponse(BaseModel):
    id: str
    nomor: str
    customer_id: Optional[str] = None
    so_id: Optional[str] = None
    delivery_date: Optional[date] = None
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    status: str
    notes: Optional[str] = None
    bukti_kirim_file: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    items: list[DNItemResponse] = []
