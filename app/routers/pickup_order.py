from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pickup_order import PickupOrder, PickupOrderItem
from app.models.system import ActivityLog
from app.schemas.pickup_order import (
    PickupOrderCreate, PickupOrderUpdate,
    PickupOrderResponse, PickupOrderDetailResponse, PUItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/pickup-order", tags=["pickup-order"])


@router.get("")
async def list_pu(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PickupOrder).where(
        PickupOrder.is_deleted == False, PickupOrder.is_current == True,
    )
    if search: query = query.where(PickupOrder.nomor.ilike(f"%{search}%"))
    if status: query = query.where(PickupOrder.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(PickupOrder.created_at.desc()).offset((page-1)*per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [PickupOrderResponse.model_validate(i) for i in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_pu(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    items = (await db.execute(
        select(PickupOrderItem).where(PickupOrderItem.pickup_order_id == doc_id).order_by(PickupOrderItem.urutan)
    )).scalars().all()
    resp = PickupOrderDetailResponse.model_validate(doc)
    resp.items = [PUItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_pu(body: PickupOrderCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "pickup_order")

    doc = PickupOrder(
        nomor=nomor, supplier_id=body.supplier_id, po_id=body.po_id,
        pic_name=body.pic_name, pic_phone=body.pic_phone,
        pickup_address=body.pickup_address,
        terms_of_payment=body.terms_of_payment,
        terms_of_delivery=body.terms_of_delivery,
        pickup_date=body.pickup_date or date.today(),
        vehicle_plate=body.vehicle_plate,
        driver_name=body.driver_name,
        driver_phone=body.driver_phone,
        expedition_id=body.expedition_id,
        received_date=body.received_date,
        notes=body.notes,
    )
    db.add(doc); await db.flush()

    for i, it in enumerate(body.items):
        db.add(PickupOrderItem(
            pickup_order_id=doc.id, item_id=it.item_id,
            quantity=Decimal(str(it.quantity)),
            urutan=it.urutan if it.urutan else i, notes=it.notes,
        ))
    await db.flush()

    db.add(ActivityLog(entity_type="pickup_order", entity_id=doc.id, action="create",
                       description=f"Created Pickup Order {doc.nomor}"))
    await db.flush()

    items = (await db.execute(
        select(PickupOrderItem).where(PickupOrderItem.pickup_order_id == doc.id).order_by(PickupOrderItem.urutan)
    )).scalars().all()
    resp = PickupOrderDetailResponse.model_validate(doc)
    resp.items = [PUItemResponse.model_validate(i) for i in items]
    return resp


@router.patch("/{doc_id}")
async def update_pu(doc_id: str, body: PickupOrderUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)
    for k, v in update_data.items(): setattr(doc, k, v)

    if items_data is not None:
        await db.execute(delete(PickupOrderItem).where(PickupOrderItem.pickup_order_id == doc_id))
        for i, it in enumerate(items_data):
            db.add(PickupOrderItem(
                pickup_order_id=doc_id, item_id=it["item_id"],
                quantity=Decimal(str(it.get("quantity", 0))),
                urutan=it.get("urutan", i), notes=it.get("notes"),
            ))
    await db.flush()

    db.add(ActivityLog(entity_type="pickup_order", entity_id=doc_id, action="update",
                       description=f"Updated Pickup Order {doc.nomor}"))
    await db.flush()

    items = (await db.execute(
        select(PickupOrderItem).where(PickupOrderItem.pickup_order_id == doc_id).order_by(PickupOrderItem.urutan)
    )).scalars().all()
    resp = PickupOrderDetailResponse.model_validate(doc)
    resp.items = [PUItemResponse.model_validate(i) for i in items]
    return resp


@router.delete("/{doc_id}")
async def delete_pu(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.is_deleted = True
    db.add(ActivityLog(entity_type="pickup_order", entity_id=doc_id, action="delete",
                       description=f"Deleted Pickup Order {doc.nomor}"))
    await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/status")
async def status_pu(doc_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Pickup Order not found")
    new_status = body.get("status")
    allowed = {
        "draft": ["sent"],
        "sent": ["picked_up"],
        "picked_up": ["received", "cancelled", "revised", "obsolete"],
    }
    if new_status not in allowed.get(doc.status, []):
        raise HTTPException(400, f"Invalid transition from {doc.status} to {new_status}")
    old_status = doc.status
    doc.status = new_status
    db.add(ActivityLog(entity_type="pickup_order", entity_id=doc_id, action="status_change",
                       description=f"Pickup Order {doc.nomor}: {old_status} → {new_status}"))
    await db.flush()
    return PickupOrderResponse.model_validate(doc)


@router.post("/{doc_id}/revise")
async def revise_pu(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    new_doc = await create_revision(db, PickupOrder, PickupOrderItem, doc_id, "pickup_order_id")
    db.add(ActivityLog(entity_type="pickup_order", entity_id=doc_id, action="revise",
                       description=f"Revised Pickup Order {doc.nomor} → {new_doc.nomor} v{new_doc.version}"))
    await db.flush()
    return PickupOrderResponse.model_validate(new_doc)
