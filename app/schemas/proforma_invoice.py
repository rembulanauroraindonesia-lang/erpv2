from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class PIItemData(BaseModel):
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal = Decimal("0")
    urutan: int = 0
    notes: Optional[str] = None


class PIItemResponse(BaseModel):
    id: str
    proforma_invoice_id: str
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    urutan: int
    notes: Optional[str] = None
    class Config: from_attributes = True


class ProformaInvoiceCreate(BaseModel):
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    due_date: Optional[date] = None
    payment_method: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    items: list[PIItemData] = []
    include_ppn: bool = True


class ProformaInvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    due_date: Optional[date] = None
    payment_method: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[PIItemData]] = None


class ProformaInvoiceResponse(BaseModel):
    id: str
    nomor: str
    customer_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    status: str
    subtotal: Decimal
    ppn_amount: Decimal
    total: Decimal
    due_date: Optional[date] = None
    payment_method: Optional[str] = None
    bukti_bayar_file: Optional[str] = None
    bukti_giro_cek_file: Optional[str] = None
    notes: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    pic_name: Optional[str] = None
    pic_phone: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class ProformaInvoiceDetailResponse(ProformaInvoiceResponse):
    items: list[PIItemResponse] = []
