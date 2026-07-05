from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class PaymentCreate(BaseModel):
    invoice_id: Optional[str] = None
    proforma_invoice_id: Optional[str] = None
    amount: Decimal
    payment_method: Optional[str] = None  # transfer, giro, cek, cash
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    giro_bank: Optional[str] = None
    giro_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    invoice_id: Optional[str] = None
    proforma_invoice_id: Optional[str] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    giro_bank: Optional[str] = None
    giro_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentStatusUpdate(BaseModel):
    """For status transitions: clear, extend, bad_debt, cancel"""
    action: str  # cleared, extended, bad_debt_declared, cancelled
    cleared_date: Optional[date] = None
    due_date_new: Optional[date] = None  # for extension
    bad_debt_reason: Optional[str] = None
    notes: Optional[str] = None
    user_info: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    invoice_id: Optional[str] = None
    proforma_invoice_id: Optional[str] = None
    payment_number: str
    amount: Decimal
    payment_method: Optional[str] = None
    status: str
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    cleared_date: Optional[date] = None
    bukti_bayar_file: Optional[str] = None
    bukti_giro_cek_file: Optional[str] = None
    giro_bank: Optional[str] = None
    giro_number: Optional[str] = None
    extension_count: int
    bad_debt_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class PaymentHistoryResponse(BaseModel):
    id: str
    payment_id: str
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    amount_before: Optional[Decimal] = None
    amount_after: Optional[Decimal] = None
    due_date_before: Optional[date] = None
    due_date_after: Optional[date] = None
    notes: Optional[str] = None
    user_info: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True
