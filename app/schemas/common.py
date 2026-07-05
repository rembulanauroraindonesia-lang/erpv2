from pydantic import BaseModel
from typing import Optional


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20
    search: Optional[str] = None
    sort: str = "created_at"
    order: str = "desc"


class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    per_page: int
