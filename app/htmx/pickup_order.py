from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.pickup_order import PickupOrder, PickupOrderItem
from app.models.contacts import Contact
from app.models.items import Item

router = APIRouter(prefix="/app/pickup-order", tags=["htmx-pickup-order"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def pu_index(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PickupOrder).where(
        PickupOrder.is_deleted == False,
        PickupOrder.is_current == True,
    )
    if search:
        query = query.where(PickupOrder.nomor.ilike(f"%{search}%"))
    if status:
        query = query.where(PickupOrder.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(PickupOrder.created_at.desc())
    query = query.offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    docs = result.scalars().all()

    # Resolve supplier names
    supplier_ids = [d.supplier_id for d in docs if d.supplier_id]
    suppliers = {}
    if supplier_ids:
        c_result = await db.execute(select(Contact).where(Contact.id.in_(supplier_ids)))
        suppliers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("pickup_order/index.html", {
        "request": request,
        "docs": docs,
        "suppliers": suppliers,
        "total": total,
        "page": page,
        "search": search or "",
        "status_filter": status or "",
        "active": "pickup_order",
    })


@router.get("/new")
async def pu_new(request: Request, db: AsyncSession = Depends(get_db)):
    suppliers_result = await db.execute(
        select(Contact).where(Contact.type == "supplier", Contact.is_deleted == False)
    )
    suppliers = suppliers_result.scalars().all()

    items_result = await db.execute(select(Item).where(Item.is_deleted == False))
    items = items_result.scalars().all()

    return templates.TemplateResponse("pickup_order/new.html", {
        "request": request,
        "suppliers": suppliers,
        "items": items,
        "active": "pickup_order",
    })


@router.get("/{doc_id}")
async def pu_detail(request: Request, doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted:
        return templates.TemplateResponse("shared/404.html", {"request": request}, status_code=404)

    result = await db.execute(
        select(PickupOrderItem)
        .where(PickupOrderItem.pickup_order_id == doc_id)
        .order_by(PickupOrderItem.urutan)
    )
    items = result.scalars().all()

    supplier = None
    if doc.supplier_id:
        supplier = await db.get(Contact, doc.supplier_id)

    item_ids = [pi.item_id for pi in items]
    item_names = {}
    if item_ids:
        i_result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in i_result.scalars().all()}

    from app.services.settings import get_all_settings
    company = await get_all_settings(db)

    return templates.TemplateResponse("pickup_order/detail.html", {
        "request": request,
        "doc": doc,
        "items": items,
        "supplier": supplier,
        "item_names": item_names,
        "company": company,
        "active": "pickup_order",
    })
