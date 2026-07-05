from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.invoice import Invoice, InvoiceItem
from app.models.contacts import Contact
from app.models.items import Item
from app.services.settings import get_all_settings

router = APIRouter(prefix="/app/invoice", tags=["htmx-invoice"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def invoice_index(
    request: Request, page: int = Query(1, ge=1), search: str = None, status: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Invoice).where(Invoice.is_deleted == False, Invoice.is_current == True)
    if search: query = query.where(Invoice.nomor.ilike(f"%{search}%"))
    if status: query = query.where(Invoice.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    per_page = 20
    total_pages = max(1, (total + per_page - 1) // per_page)

    query = query.order_by(Invoice.created_at.desc()).offset((page-1)*per_page).limit(per_page)
    result = await db.execute(query)
    docs = result.scalars().all()

    customer_ids = [d.customer_id for d in docs if d.customer_id]
    customer_names = {}
    if customer_ids:
        r = await db.execute(select(Contact).where(Contact.id.in_(customer_ids)))
        customer_names = {c.id: c.name for c in r.scalars().all()}

    return templates.TemplateResponse("invoice/index.html", {
        "request": request, "active": "invoice",
        "docs": docs, "customer_names": customer_names,
        "page": page, "total": total, "per_page": per_page,
        "total_pages": total_pages, "search": search or "", "status_filter": status or "",
    })


@router.get("/new")
async def invoice_create_form(request: Request, db: AsyncSession = Depends(get_db)):
    customers = (await db.execute(
        select(Contact).where(Contact.type == "customer", Contact.is_deleted == False).order_by(Contact.name)
    )).scalars().all()
    items = (await db.execute(
        select(Item).where(Item.is_deleted == False).order_by(Item.name)
    )).scalars().all()
    return templates.TemplateResponse("invoice/new.html", {
        "request": request, "active": "invoice",
        "customers": customers, "items": items, "today": __import__("datetime").date.today(),
    })


@router.get("/{doc_id}")
async def invoice_detail(doc_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/app/invoice", 302)

    items = (await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == doc_id).order_by(InvoiceItem.urutan)
    )).scalars().all()

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [pi.item_id for pi in items if pi.item_id]
    item_names = {}
    if item_ids:
        r = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in r.scalars().all()}

    company = await get_all_settings(db)
    return templates.TemplateResponse("invoice/detail.html", {
        "request": request, "active": "invoice",
        "doc": doc, "items": items, "customer": customer,
        "item_names": item_names, "company": company,
    })
