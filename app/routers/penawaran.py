from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.penawaran import Penawaran, PenawaranItem
from app.models.system import ActivityLog
from app.schemas.penawaran import (
    PenawaranCreate,
    PenawaranUpdate,
    PenawaranResponse,
    PenawaranDetailResponse,
    PenawaranItemResponse,
)
from app.services.counter import get_next_number
from app.services.calc import (
    calc_row_total_beli,
    calc_row_total_jual,
    validate_penawaran_calc,
)
from app.services.revision import create_revision

router = APIRouter(prefix="/api/penawaran", tags=["penawaran"])


@router.get("")
async def list_penawaran(
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
    items = result.scalars().all()

    return {
        "data": [PenawaranResponse.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")

    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc_id)
        .order_by(PenawaranItem.urutan)
    )
    items = result.scalars().all()

    resp = PenawaranDetailResponse.model_validate(doc)
    resp.items = [PenawaranItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_penawaran(body: PenawaranCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "penawaran")

    # Recalculate totals server-side
    items_data = [item.model_dump() for item in body.items]
    totals = validate_penawaran_calc(items_data, body.price_mode)

    doc = Penawaran(
        nomor=nomor,
        customer_id=body.customer_id,
        pic_name=body.pic_name,
        pic_phone=body.pic_phone,
        delivery_address=body.delivery_address,
        supplier_mode=body.supplier_mode,
        price_mode=body.price_mode,
        terms_of_payment=body.terms_of_payment,
        terms_of_delivery=body.terms_of_delivery,
        validity_days=body.validity_days,
        notes=body.notes,
        total_beli=totals["total_beli"],
        total_jual=totals["total_jual"],
        ppn_amount=totals["ppn_amount"],
        grand_total=totals["grand_total"],
        margin=totals["total_jual"] - totals["total_beli"],
    )
    db.add(doc)
    await db.flush()

    # Create items
    for item_data in body.items:
        qty = Decimal(str(item_data.quantity))
        berat_beli = Decimal(str(item_data.berat_beli_per_unit))
        hpp = Decimal(str(item_data.hpp_per_unit))
        harga_jual = Decimal(str(item_data.harga_jual_per_unit))
        berat_jual = Decimal(str(item_data.berat_jual_per_unit or 0))

        row_beli = calc_row_total_beli(qty, berat_beli, hpp)
        row_jual = calc_row_total_jual(
            qty, berat_beli, harga_jual,
            item_data.different_scale, berat_jual if item_data.different_scale else None,
        )

        pi = PenawaranItem(
            penawaran_id=doc.id,
            item_id=item_data.item_id,
            supplier_id=item_data.supplier_id,
            quantity=item_data.quantity,
            berat_beli_per_unit=item_data.berat_beli_per_unit,
            hpp_per_unit=item_data.hpp_per_unit,
            total_beli=row_beli,
            harga_jual_per_unit=item_data.harga_jual_per_unit,
            total_jual=row_jual,
            different_scale=item_data.different_scale,
            berat_jual_per_unit=item_data.berat_jual_per_unit,
            urutan=item_data.urutan,
            notes=item_data.notes,
        )
        db.add(pi)

    await db.flush()

    db.add(ActivityLog(entity_type="penawaran", entity_id=doc.id, action="create",
                       description=f"Created Penawaran {doc.nomor}"))
    await db.flush()

    resp = PenawaranDetailResponse.model_validate(doc)
    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc.id)
        .order_by(PenawaranItem.urutan)
    )
    resp.items = [PenawaranItemResponse.model_validate(i) for i in result.scalars().all()]
    return resp


@router.patch("/{doc_id}")
async def update_penawaran(
    doc_id: str, body: PenawaranUpdate, db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")
    if doc.status == "locked":
        raise HTTPException(400, "Cannot edit a locked penawaran")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    for key, value in update_data.items():
        setattr(doc, key, value)

    if items_data is not None:
        # Recalculate totals
        totals = validate_penawaran_calc(items_data, doc.price_mode)
        doc.total_beli = totals["total_beli"]
        doc.total_jual = totals["total_jual"]
        doc.ppn_amount = totals["ppn_amount"]
        doc.grand_total = totals["grand_total"]
        doc.margin = totals["total_jual"] - totals["total_beli"]

        # Delete old items
        await db.execute(
            delete(PenawaranItem).where(PenawaranItem.penawaran_id == doc_id)
        )

        # Create new items
        for item_data in items_data:
            qty = Decimal(str(item_data["quantity"]))
            berat_beli = Decimal(str(item_data.get("berat_beli_per_unit", 0)))
            hpp = Decimal(str(item_data["hpp_per_unit"]))
            harga_jual = Decimal(str(item_data["harga_jual_per_unit"]))
            diff_scale = item_data.get("different_scale", False)
            berat_jual = Decimal(str(item_data.get("berat_jual_per_unit") or 0))

            row_beli = calc_row_total_beli(qty, berat_beli, hpp)
            row_jual = calc_row_total_jual(
                qty, berat_beli, harga_jual,
                diff_scale, berat_jual if diff_scale else None,
            )

            pi = PenawaranItem(
                penawaran_id=doc_id,
                item_id=item_data["item_id"],
                supplier_id=item_data.get("supplier_id"),
                quantity=qty,
                berat_beli_per_unit=berat_beli,
                hpp_per_unit=hpp,
                total_beli=row_beli,
                harga_jual_per_unit=harga_jual,
                total_jual=row_jual,
                different_scale=diff_scale,
                berat_jual_per_unit=berat_jual if diff_scale else None,
                urutan=item_data.get("urutan", 0),
                notes=item_data.get("notes"),
            )
            db.add(pi)

    await db.flush()

    db.add(ActivityLog(entity_type="penawaran", entity_id=doc_id, action="update",
                       description=f"Updated Penawaran {doc.nomor}"))
    await db.flush()

    resp = PenawaranDetailResponse.model_validate(doc)
    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc_id)
        .order_by(PenawaranItem.urutan)
    )
    resp.items = [PenawaranItemResponse.model_validate(i) for i in result.scalars().all()]
    return resp


@router.delete("/{doc_id}")
async def delete_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")
    doc.is_deleted = True
    db.add(ActivityLog(entity_type="penawaran", entity_id=doc_id, action="delete",
                       description=f"Deleted Penawaran {doc.nomor}"))
    await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/revise")
async def revise_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")

    new_doc = await create_revision(
        db, Penawaran, PenawaranItem, doc_id, "penawaran_id"
    )
    db.add(ActivityLog(entity_type="penawaran", entity_id=doc_id, action="revise",
                       description=f"Revised Penawaran {doc.nomor} → {new_doc.nomor} v{new_doc.version}"))
    await db.flush()
    return PenawaranResponse.model_validate(new_doc)


@router.post("/{doc_id}/status")
async def status_penawaran(doc_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")
    new_status = body.get("status")
    allowed = {"draft": ["locked"], "locked": ["approved", "revised", "obsolete"]}
    current = doc.status
    if new_status not in allowed.get(current, []):
        raise HTTPException(400, f"Invalid transition from {current} to {new_status}")
    doc.status = new_status
    db.add(ActivityLog(entity_type="penawaran", entity_id=doc_id, action="status_change",
                       description=f"Penawaran {doc.nomor}: {current} → {new_status}"))
    await db.flush()
    return PenawaranResponse.model_validate(doc)


@router.post("/{doc_id}/lock")
async def lock_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")
    doc.status = "locked"
    await db.flush()
    return PenawaranResponse.model_validate(doc)


@router.get("/{doc_id}/versions")
async def list_versions(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Penawaran not found")

    result = await db.execute(
        select(Penawaran)
        .where(Penawaran.nomor == doc.nomor, Penawaran.is_deleted == False)
        .order_by(Penawaran.version.desc())
    )
    versions = result.scalars().all()
    return [PenawaranResponse.model_validate(v) for v in versions]
