from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class ContactCreate(BaseModel):
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: str
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopHistoryCreate(BaseModel):
    top_type: str
    tempo_days: Optional[int] = None
    effective_date: date
    notes: Optional[str] = None


class TopHistoryResponse(BaseModel):
    id: str
    contact_id: str
    top_type: str
    tempo_days: Optional[int] = None
    effective_date: date
    notes: Optional[str] = None
    created_at: Optional[date] = None

    class Config:
        from_attributes = True
