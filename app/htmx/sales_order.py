from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.sales_order import SalesOrder, SalesOrderItem
from app.models.contacts import Contact
from app.models.items import Item
from app.models.penawaran import Penawaran

router = APIRouter(prefix="/app/sales-order", tags=["htmx-sales-order"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def so_index(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(SalesOrder).where(
        SalesOrder.is_deleted == False,
        SalesOrder.is_current == True,
    )
    if search:
        query = query.where(SalesOrder.nomor.ilike(f"%{search}%"))
    if status:
        query = query.where(SalesOrder.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(SalesOrder.created_at.desc())
    query = query.offset((page - 1) * 20).limit(20)
    result = await db.execute(query)
    docs = result.scalars().all()

    # Resolve customer names
    customer_ids = [d.customer_id for d in docs if d.customer_id]
    customers = {}
    if customer_ids:
        c_result = await db.execute(select(Contact).where(Contact.id.in_(customer_ids)))
        customers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("sales_order/index.html", {
        "request": request,
        "docs": docs,
        "customers": customers,
        "total": total,
        "page": page,
        "search": search or "",
        "status_filter": status or "",
        "active": "sales_order",
    })


@router.get("/new")
async def so_new(request: Request, penawaran_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    customers_result = await db.execute(
        select(Contact).where(Contact.type == "customer", Contact.is_deleted == False)
    )
    customers = customers_result.scalars().all()

    items_result = await db.execute(select(Item).where(Item.is_deleted == False))
    items = items_result.scalars().all()

    # If creating from penawaran, pre-fill
    penawaran = None
    if penawaran_id:
        penawaran = await db.get(Penawaran, penawaran_id)

    return templates.TemplateResponse("sales_order/new.html", {
        "request": request,
        "customers": customers,
        "items": items,
        "penawaran": penawaran,
        "active": "sales_order",
    })


@router.get("/{doc_id}")
async def so_detail(request: Request, doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        return templates.TemplateResponse("shared/404.html", {"request": request}, status_code=404)

    result = await db.execute(
        select(SalesOrderItem)
        .where(SalesOrderItem.sales_order_id == doc_id)
        .order_by(SalesOrderItem.urutan)
    )
    items = result.scalars().all()

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [pi.item_id for pi in items]
    item_names = {}
    if item_ids:
        i_result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in i_result.scalars().all()}

    from app.services.settings import get_all_settings
    company = await get_all_settings(db)

    return templates.TemplateResponse("sales_order/detail.html", {
        "request": request,
        "doc": doc,
        "items": items,
        "customer": customer,
        "item_names": item_names,
        "company": company,
        "active": "sales_order",
    })
