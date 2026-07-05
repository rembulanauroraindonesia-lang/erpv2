from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.delivery_note import DeliveryNote, DeliveryNoteItem
from app.schemas.delivery_note import (
    DeliveryNoteCreate, DeliveryNoteUpdate,
    DeliveryNoteResponse, DeliveryNoteDetailResponse, DNItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/delivery-note", tags=["delivery-note"])


@router.get("")
async def list_dn(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DeliveryNote).where(
        DeliveryNote.is_deleted == False, DeliveryNote.is_current == True,
    )
    if search: query = query.where(DeliveryNote.nomor.ilike(f"%{search}%"))
    if status: query = query.where(DeliveryNote.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(DeliveryNote.created_at.desc()).offset((page-1)*per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [DeliveryNoteResponse.model_validate(i) for i in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_dn(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    items = (await db.execute(
        select(DeliveryNoteItem).where(DeliveryNoteItem.delivery_note_id == doc_id).order_by(DeliveryNoteItem.urutan)
    )).scalars().all()
    resp = DeliveryNoteDetailResponse.model_validate(doc)
    resp.items = [DNItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_dn(body: DeliveryNoteCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "delivery_note")

    doc = DeliveryNote(
        nomor=nomor, customer_id=body.customer_id, so_id=body.so_id,
        pic_name=body.pic_name, pic_phone=body.pic_phone,
        delivery_address=body.delivery_address,
        terms_of_delivery=body.terms_of_delivery,
        delivery_date=body.delivery_date or date.today(),
        vehicle_plate=body.vehicle_plate,
        driver_name=body.driver_name,
        driver_phone=body.driver_phone,
        notes=body.notes,
    )
    db.add(doc); await db.flush()

    for i, it in enumerate(body.items):
        db.add(DeliveryNoteItem(
            delivery_note_id=doc.id, item_id=it.item_id,
            quantity=Decimal(str(it.quantity)),
            urutan=it.urutan if it.urutan else i, notes=it.notes,
        ))
    await db.flush()

    items = (await db.execute(
        select(DeliveryNoteItem).where(DeliveryNoteItem.delivery_note_id == doc.id).order_by(DeliveryNoteItem.urutan)
    )).scalars().all()
    resp = DeliveryNoteDetailResponse.model_validate(doc)
    resp.items = [DNItemResponse.model_validate(i) for i in items]
    return resp


@router.patch("/{doc_id}")
async def update_dn(doc_id: str, body: DeliveryNoteUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)
    for k, v in update_data.items(): setattr(doc, k, v)

    if items_data is not None:
        await db.execute(delete(DeliveryNoteItem).where(DeliveryNoteItem.delivery_note_id == doc_id))
        for i, it in enumerate(items_data):
            db.add(DeliveryNoteItem(
                delivery_note_id=doc_id, item_id=it["item_id"],
                quantity=Decimal(str(it.get("quantity", 0))),
                urutan=it.get("urutan", i), notes=it.get("notes"),
            ))
    await db.flush()

    items = (await db.execute(
        select(DeliveryNoteItem).where(DeliveryNoteItem.delivery_note_id == doc_id).order_by(DeliveryNoteItem.urutan)
    )).scalars().all()
    resp = DeliveryNoteDetailResponse.model_validate(doc)
    resp.items = [DNItemResponse.model_validate(i) for i in items]
    return resp


@router.delete("/{doc_id}")
async def delete_dn(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.is_deleted = True; await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/revise")
async def revise_dn(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    new_doc = await create_revision(db, DeliveryNote, DeliveryNoteItem, doc_id, "delivery_note_id")
    return DeliveryNoteResponse.model_validate(new_doc)
