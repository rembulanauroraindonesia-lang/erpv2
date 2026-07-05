from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.items import Item

router = APIRouter(prefix="/app/items", tags=["htmx-items"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def items_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Item).where(Item.is_deleted == False)
    if search:
        query = query.where(
            or_(Item.name.ilike(f"%{search}%"), Item.sku.ilike(f"%{search}%"))
        )
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Item.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return templates.TemplateResponse("items/index.html", {
        "request": request,
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "search": search or "",
        "active": "items",
    })


@router.get("/rows")
async def items_rows(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Item).where(Item.is_deleted == False)
    if search:
        query = query.where(
            or_(Item.name.ilike(f"%{search}%"), Item.sku.ilike(f"%{search}%"))
        )
    query = query.order_by(Item.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return templates.TemplateResponse("items/_rows.html", {
        "request": request,
        "items": items,
    })


@router.get("/form")
async def items_create_form(request: Request):
    return templates.TemplateResponse("items/_form.html", {
        "request": request,
        "item": None,
    })


@router.get("/{item_id}/form")
async def items_edit_form(
    request: Request, item_id: str, db: AsyncSession = Depends(get_db)
):
    item = await db.get(Item, item_id)
    if not item or item.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Item tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("items/_form.html", {
        "request": request,
        "item": item,
    })


@router.get("/{item_id}")
async def items_detail(
    request: Request, item_id: str, db: AsyncSession = Depends(get_db)
):
    item = await db.get(Item, item_id)
    if not item or item.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Item tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("items/detail.html", {
        "request": request,
        "item": item,
        "active": "items",
    })
