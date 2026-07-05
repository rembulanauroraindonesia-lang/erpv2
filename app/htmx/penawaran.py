import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact
from app.models.penawaran import Penawaran, PenawaranItem

router = APIRouter(prefix="/app/penawaran", tags=["htmx-penawaran"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def penawaran_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Penawaran).where(
        Penawaran.is_deleted == False,
        Penawaran.is_current == True,
    )
    if search:
        query = query.where(Penawaran.nomor.ilike(f"%{search}%"))
    if status:
        query = query.where(Penawaran.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Penawaran.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    penawarans = result.scalars().all()

    # Get customer names for display
    customer_ids = [p.customer_id for p in penawarans if p.customer_id]
    customers = {}
    if customer_ids:
        c_result = await db.execute(
            select(Contact).where(Contact.id.in_(customer_ids))
        )
        customers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("penawaran/index.html", {
        "request": request,
        "penawarans": penawarans,
        "customers": customers,
        "total": total,
        "page": page,
        "per_page": per_page,
        "search": search or "",
        "status_filter": status or "",
        "active": "penawaran",
    })


@router.get("/rows")
async def penawaran_rows(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Penawaran).where(
        Penawaran.is_deleted == False,
        Penawaran.is_current == True,
    )
    if search:
        query = query.where(Penawaran.nomor.ilike(f"%{search}%"))
    if status:
        query = query.where(Penawaran.status == status)

    query = query.order_by(Penawaran.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    penawarans = result.scalars().all()

    customer_ids = [p.customer_id for p in penawarans if p.customer_id]
    customers = {}
    if customer_ids:
        c_result = await db.execute(
            select(Contact).where(Contact.id.in_(customer_ids))
        )
        customers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("penawaran/_rows.html", {
        "request": request,
        "penawarans": penawarans,
        "customers": customers,
    })


@router.get("/new")
async def penawaran_new(request: Request):
    return templates.TemplateResponse("penawaran/new.html", {
        "request": request,
        "active": "penawaran",
        "edit_mode": False,
        "existing_data": None,
    })


@router.get("/{doc_id}")
async def penawaran_detail(
    request: Request, doc_id: str, db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        return HTMLResponse("<p>Penawaran tidak ditemukan</p>", status_code=404)

    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc_id)
        .order_by(PenawaranItem.urutan)
    )
    items = result.scalars().all()

    # Get related names
    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    from app.models.items import Item
    item_ids = [pi.item_id for pi in items]
    item_names = {}
    supplier_ids = [pi.supplier_id for pi in items if pi.supplier_id]
    supplier_names = {}

    if item_ids:
        i_result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in i_result.scalars().all()}
    if supplier_ids:
        s_result = await db.execute(select(Contact).where(Contact.id.in_(supplier_ids)))
        supplier_names = {c.id: c.name for c in s_result.scalars().all()}

    return templates.TemplateResponse("penawaran/detail.html", {
        "request": request,
        "doc": doc,
        "items": items,
        "customer": customer,
        "item_names": item_names,
        "supplier_names": supplier_names,
        "active": "penawaran",
    })


@router.get("/{doc_id}/edit")
async def penawaran_edit(
    request: Request, doc_id: str, db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        return HTMLResponse("<p>Penawaran tidak ditemukan</p>", status_code=404)
    if doc.status == "locked":
        return HTMLResponse("<p>Penawaran sudah dikunci</p>", status_code=400)

    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc_id)
        .order_by(PenawaranItem.urutan)
    )
    items = result.scalars().all()

    # Build existing data as JSON for Alpine.js to consume
    existing_data = {
        "id": doc.id,
        "nomor": doc.nomor,
        "customer_id": doc.customer_id or "",
        "supplier_mode": doc.supplier_mode,
        "price_mode": doc.price_mode,
        "terms_of_payment": doc.terms_of_payment or "",
        "terms_of_delivery": doc.terms_of_delivery or "",
        "validity_days": doc.validity_days or 30,
        "notes": doc.notes or "",
        "items": [
            {
                "item_id": pi.item_id,
                "supplier_id": pi.supplier_id or "",
                "quantity": float(pi.quantity),
                "berat_beli_per_unit": float(pi.berat_beli_per_unit),
                "hpp_per_unit": float(pi.hpp_per_unit),
                "harga_jual_per_unit": float(pi.harga_jual_per_unit),
                "different_scale": pi.different_scale,
                "berat_jual_per_unit": float(pi.berat_jual_per_unit) if pi.berat_jual_per_unit else 0,
                "urutan": pi.urutan,
                "notes": pi.notes or "",
            }
            for pi in items
        ],
    }

    return templates.TemplateResponse("penawaran/new.html", {
        "request": request,
        "active": "penawaran",
        "edit_mode": True,
        "existing_data": json.dumps(existing_data),
    })
