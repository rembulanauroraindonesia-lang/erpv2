from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.sales_order import SalesOrder, SalesOrderItem
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderResponse,
    SalesOrderDetailResponse,
    SOItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/sales-order", tags=["sales-order"])

PpnRate = Decimal("0.11")


def _calc_totals(items, price_mode="include_ppn"):
    total = sum(item["quantity"] * item["unit_price"] for item in items)
    if price_mode == "include_ppn":
        ppn = total / Decimal("1.11") * PpnRate
        grand = total
    else:
        ppn = total * PpnRate
        grand = total + ppn
    return {"total": total, "ppn_amount": ppn, "grand_total": grand}


@router.get("")
async def list_so(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
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
    total_count = (await db.execute(count_query)).scalar()

    query = query.order_by(SalesOrder.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "data": [SalesOrderResponse.model_validate(i) for i in items],
        "total": total_count,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_so(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Sales Order not found")

    result = await db.execute(
        select(SalesOrderItem)
        .where(SalesOrderItem.sales_order_id == doc_id)
        .order_by(SalesOrderItem.urutan)
    )
    items = result.scalars().all()
    resp = SalesOrderDetailResponse.model_validate(doc)
    resp.items = [SOItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_so(body: SalesOrderCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "sales_order")
    items_data = [item.model_dump() for item in body.items]
    totals = _calc_totals(items_data)

    doc = SalesOrder(
        nomor=nomor,
        penawaran_id=body.penawaran_id,
        customer_id=body.customer_id,
        pic_name=body.pic_name,
        pic_phone=body.pic_phone,
        delivery_address=body.delivery_address,
        terms_of_payment=body.terms_of_payment,
        terms_of_delivery=body.terms_of_delivery,
        order_date=body.order_date or date.today(),
        delivery_date=body.delivery_date,
        notes=body.notes,
        total=totals["total"],
        ppn_amount=totals["ppn_amount"],
        grand_total=totals["grand_total"],
        margin=totals["total"] - totals["total"],  # placeholder until we have HPP
    )
    db.add(doc)
    await db.flush()

    for i, item_data in enumerate(body.items):
        qty = Decimal(str(item_data.quantity))
        price = Decimal(str(item_data.unit_price))
        pi = SalesOrderItem(
            sales_order_id=doc.id,
            item_id=item_data.item_id,
            quantity=qty,
            unit_price=price,
            total=qty * price,
            urutan=item_data.urutan if item_data.urutan else i,
            notes=item_data.notes,
        )
        db.add(pi)

    await db.flush()
    resp = SalesOrderDetailResponse.model_validate(doc)
    result = await db.execute(
        select(SalesOrderItem)
        .where(SalesOrderItem.sales_order_id == doc.id)
        .order_by(SalesOrderItem.urutan)
    )
    resp.items = [SOItemResponse.model_validate(i) for i in result.scalars().all()]
    return resp


@router.patch("/{doc_id}")
async def update_so(doc_id: str, body: SalesOrderUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Sales Order not found")
    if doc.status == "locked":
        raise HTTPException(400, "Cannot edit a locked Sales Order")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    for key, value in update_data.items():
        setattr(doc, key, value)

    if items_data is not None:
        totals = _calc_totals(items_data)
        doc.total = totals["total"]
        doc.ppn_amount = totals["ppn_amount"]
        doc.grand_total = totals["grand_total"]

        await db.execute(delete(SalesOrderItem).where(SalesOrderItem.sales_order_id == doc_id))

        for i, item_data in enumerate(items_data):
            qty = Decimal(str(item_data["quantity"]))
            price = Decimal(str(item_data["unit_price"]))
            pi = SalesOrderItem(
                sales_order_id=doc_id,
                item_id=item_data["item_id"],
                quantity=qty,
                unit_price=price,
                total=qty * price,
                urutan=item_data.get("urutan", i),
                notes=item_data.get("notes"),
            )
            db.add(pi)

    await db.flush()
    resp = SalesOrderDetailResponse.model_validate(doc)
    result = await db.execute(
        select(SalesOrderItem)
        .where(SalesOrderItem.sales_order_id == doc_id)
        .order_by(SalesOrderItem.urutan)
    )
    resp.items = [SOItemResponse.model_validate(i) for i in result.scalars().all()]
    return resp


@router.delete("/{doc_id}")
async def delete_so(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Sales Order not found")
    doc.is_deleted = True
    await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/revise")
async def revise_so(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Sales Order not found")
    new_doc = await create_revision(db, SalesOrder, SalesOrderItem, doc_id, "sales_order_id")
    return SalesOrderResponse.model_validate(new_doc)


@router.post("/{doc_id}/lock")
async def lock_so(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Sales Order not found")
    doc.status = "locked"
    await db.flush()
    return SalesOrderResponse.model_validate(doc)
