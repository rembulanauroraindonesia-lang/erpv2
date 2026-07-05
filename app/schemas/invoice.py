from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, computed_field


class InvItemData(BaseModel):
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal = Decimal("0")
    urutan: int = 0
    notes: Optional[str] = None


class InvItemResponse(BaseModel):
    id: str
    invoice_id: str
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    urutan: int
    notes: Optional[str] = None
    class Config: from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_bayar_file: Optional[str] = None
    items: list[InvItemData] = []
    include_ppn: bool = True  # True = harga exclude PPN


class InvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_bayar_file: Optional[str] = None
    items: Optional[list[InvItemData]] = None


class InvoiceResponse(BaseModel):
    id: str
    nomor: str
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    status: str
    total: Decimal
    ppn_amount: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    bukti_bayar_file: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

    @computed_field
    @property
    def remaining(self) -> Decimal:
        return self.grand_total - self.paid_amount


class InvoiceDetailResponse(InvoiceResponse):
    items: list[InvItemResponse] = []
