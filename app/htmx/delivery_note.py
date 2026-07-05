from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.delivery_note import DeliveryNote, DeliveryNoteItem
from app.models.contacts import Contact
from app.models.items import Item

router = APIRouter(prefix="/app/surat-jalan", tags=["htmx-delivery-note"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def dn_index(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DeliveryNote).where(
        DeliveryNote.is_deleted == False,
        DeliveryNote.is_current == True,
    )
    if search:
        query = query.where(DeliveryNote.nomor.ilike(f"%{search}%"))
    if status:
        query = query.where(DeliveryNote.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(DeliveryNote.created_at.desc())
    query = query.offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    docs = result.scalars().all()

    # Resolve customer names
    customer_ids = [d.customer_id for d in docs if d.customer_id]
    customers = {}
    if customer_ids:
        c_result = await db.execute(select(Contact).where(Contact.id.in_(customer_ids)))
        customers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("delivery_note/index.html", {
        "request": request,
        "docs": docs,
        "customers": customers,
        "total": total,
        "page": page,
        "search": search or "",
        "status_filter": status or "",
        "active": "delivery_note",
    })


@router.get("/new")
async def dn_new(request: Request, db: AsyncSession = Depends(get_db)):
    customers_result = await db.execute(
        select(Contact).where(Contact.type == "customer", Contact.is_deleted == False)
    )
    customers = customers_result.scalars().all()

    items_result = await db.execute(select(Item).where(Item.is_deleted == False))
    items = [{"id": i.id, "name": i.name, "unit": i.unit, "default_hpp": float(i.default_hpp or 0)} for i in items_result.scalars().all()]

    expeditions_result = await db.execute(
        select(Contact).where(Contact.type == "expedition", Contact.is_deleted == False)
    )
    expeditions = expeditions_result.scalars().all()

    return templates.TemplateResponse("delivery_note/new.html", {
        "request": request,
        "customers": customers,
        "items": items,
        "expeditions": expeditions,
        "active": "delivery_note",
    })


@router.get("/{doc_id}")
async def dn_detail(request: Request, doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc or doc.is_deleted:
        return templates.TemplateResponse("shared/404.html", {"request": request}, status_code=404)

    result = await db.execute(
        select(DeliveryNoteItem)
        .where(DeliveryNoteItem.delivery_note_id == doc_id)
        .order_by(DeliveryNoteItem.urutan)
    )
    items = result.scalars().all()

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [di.item_id for di in items]
    item_names = {}
    if item_ids:
        i_result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in i_result.scalars().all()}

    from app.services.settings import get_all_settings
    company = await get_all_settings(db)

    expedition = None
    if doc.expedition_id:
        expedition = await db.get(Contact, doc.expedition_id)

    return templates.TemplateResponse("delivery_note/detail.html", {
        "request": request,
        "doc": doc,
        "items": items,
        "customer": customer,
        "expedition": expedition,
        "item_names": item_names,
        "company": company,
        "active": "delivery_note",
    })
