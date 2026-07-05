from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    unit: str = "pcs"
    default_hpp: Decimal = Decimal("0")
    notes: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    default_hpp: Optional[Decimal] = None
    notes: Optional[str] = None


class ItemResponse(BaseModel):
    id: str
    name: str
    sku: Optional[str] = None
    unit: str
    default_hpp: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
