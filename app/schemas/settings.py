from typing import Optional
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_npwp: Optional[str] = None
    company_city: Optional[str] = None
    default_supplier_mode: Optional[str] = None
    default_price_mode: Optional[str] = None
    default_ppn_rate: Optional[float] = None
    default_validity_days: Optional[int] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_holder: Optional[str] = None
    pdf_header_text: Optional[str] = None
