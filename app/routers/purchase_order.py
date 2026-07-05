from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.schemas.purchase_order import (
    PurchaseOrderCreate, PurchaseOrderUpdate,
    PurchaseOrderResponse, PurchaseOrderDetailResponse, POItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/purchase-order", tags=["purchase-order"])


def _calc_total(items):
    return sum(Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0)))
               for it in items)


@router.get("")
async def list_po(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PurchaseOrder).where(
        PurchaseOrder.is_deleted == False, PurchaseOrder.is_current == True,
    )
    if search: query = query.where(PurchaseOrder.nomor.ilike(f"%{search}%"))
    if status: query = query.where(PurchaseOrder.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(PurchaseOrder.created_at.desc()).offset((page-1)*per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [PurchaseOrderResponse.model_validate(i) for i in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_po(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PurchaseOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    items = (await db.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == doc_id).order_by(PurchaseOrderItem.urutan)
    )).scalars().all()
    resp = PurchaseOrderDetailResponse.model_validate(doc)
    resp.items = [POItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_po(body: PurchaseOrderCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "purchase_order")
    items_data = [it.model_dump() for it in body.items]
    total = _calc_total(items_data)

    doc = PurchaseOrder(
        nomor=nomor, supplier_id=body.supplier_id,
        terms_of_payment=body.terms_of_payment, terms_of_delivery=body.terms_of_delivery,
        order_date=body.order_date or date.today(), expected_date=body.expected_date,
        notes=body.notes, total=total,
    )
    db.add(doc); await db.flush()

    for i, it in enumerate(body.items):
        db.add(PurchaseOrderItem(
            purchase_order_id=doc.id, item_id=it.item_id,
            quantity=Decimal(str(it.quantity)), unit_price=Decimal(str(it.unit_price)),
            total=Decimal(str(it.quantity)) * Decimal(str(it.unit_price)),
            urutan=it.urutan if it.urutan else i, notes=it.notes,
        ))
    await db.flush()

    items = (await db.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == doc.id).order_by(PurchaseOrderItem.urutan)
    )).scalars().all()
    resp = PurchaseOrderDetailResponse.model_validate(doc)
    resp.items = [POItemResponse.model_validate(i) for i in items]
    return resp


@router.patch("/{doc_id}")
async def update_po(doc_id: str, body: PurchaseOrderUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PurchaseOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)
    for k, v in update_data.items(): setattr(doc, k, v)

    if items_data is not None:
        doc.total = _calc_total(items_data)
        await db.execute(delete(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == doc_id))
        for i, it in enumerate(items_data):
            db.add(PurchaseOrderItem(
                purchase_order_id=doc_id, item_id=it["item_id"],
                quantity=Decimal(str(it.get("quantity", 0))),
                unit_price=Decimal(str(it.get("unit_price", 0))),
                total=Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0))),
                urutan=it.get("urutan", i), notes=it.get("notes"),
            ))
    await db.flush()

    items = (await db.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == doc_id).order_by(PurchaseOrderItem.urutan)
    )).scalars().all()
    resp = PurchaseOrderDetailResponse.model_validate(doc)
    resp.items = [POItemResponse.model_validate(i) for i in items]
    return resp


@router.delete("/{doc_id}")
async def delete_po(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PurchaseOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.is_deleted = True; await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/revise")
async def revise_po(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PurchaseOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    new_doc = await create_revision(db, PurchaseOrder, PurchaseOrderItem, doc_id, "purchase_order_id")
    return PurchaseOrderResponse.model_validate(new_doc)
