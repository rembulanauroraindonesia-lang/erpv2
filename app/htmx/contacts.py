from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact

router = APIRouter(prefix="/app/kontak", tags=["htmx-contacts"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def contacts_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)
    if type:
        query = query.where(Contact.type == type)
    if search:
        query = query.where(
            or_(Contact.name.ilike(f"%{search}%"), Contact.email.ilike(f"%{search}%"))
        )
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Contact.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return templates.TemplateResponse("contacts/index.html", {
        "request": request,
        "contacts": contacts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "search": search or "",
        "type_filter": type or "",
        "active": "kontak",
    })


@router.get("/rows")
async def contacts_rows(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)
    if type:
        query = query.where(Contact.type == type)
    if search:
        query = query.where(
            or_(Contact.name.ilike(f"%{search}%"), Contact.email.ilike(f"%{search}%"))
        )
    query = query.order_by(Contact.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return templates.TemplateResponse("contacts/_rows.html", {
        "request": request,
        "contacts": contacts,
    })


@router.get("/form")
async def contacts_create_form(request: Request):
    return templates.TemplateResponse("contacts/_form.html", {
        "request": request,
        "contact": None,
    })


@router.get("/{contact_id}/form")
async def contacts_edit_form(
    request: Request, contact_id: str, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Contact tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("contacts/_form.html", {
        "request": request,
        "contact": contact,
    })


@router.get("/{contact_id}")
async def contacts_detail(
    request: Request, contact_id: str, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Contact tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("contacts/detail.html", {
        "request": request,
        "contact": contact,
        "active": "kontak",
    })
