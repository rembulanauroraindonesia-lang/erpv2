from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.invoice import Invoice, InvoiceItem
from app.models.system import ActivityLog
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate,
    InvoiceResponse, InvoiceDetailResponse, InvItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/invoice", tags=["invoice"])

PPN_RATE = Decimal("0.11")


def _calc_totals(items, include_ppn=True):
    subtotal = sum(Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0)))
                   for it in items)
    if include_ppn:
        # Harga exclude PPN
        ppn = (subtotal * PPN_RATE).quantize(Decimal("0.01"))
        grand = subtotal + ppn
    else:
        # Harga include PPN
        grand = subtotal
        ppn = (subtotal * PPN_RATE / (1 + PPN_RATE)).quantize(Decimal("0.01"))
    return {"total": subtotal.quantize(Decimal("0.01")), "ppn_amount": ppn, "grand_total": grand}


@router.get("")
async def list_invoices(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Invoice).where(Invoice.is_deleted == False, Invoice.is_current == True)
    if search: query = query.where(Invoice.nomor.ilike(f"%{search}%"))
    if status: query = query.where(Invoice.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(Invoice.created_at.desc()).offset((page-1)*per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [InvoiceResponse.model_validate(i) for i in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    items = (await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == doc_id).order_by(InvoiceItem.urutan)
    )).scalars().all()
    resp = InvoiceDetailResponse.model_validate(doc)
    resp.items = [InvItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_invoice(body: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "invoice")
    items_data = [it.model_dump() for it in body.items]
    totals = _calc_totals(items_data, body.include_ppn)

    doc = Invoice(
        nomor=nomor, customer_id=body.customer_id,
        pic_name=body.pic_name, pic_phone=body.pic_phone,
        terms_of_delivery=body.terms_of_delivery,
        sales_order_id=body.sales_order_id,
        delivery_note_id=body.delivery_note_id,
        total=totals["total"], ppn_amount=totals["ppn_amount"],
        grand_total=totals["grand_total"],
        invoice_date=body.invoice_date or date.today(),
        due_date=body.due_date,
        terms_of_payment=body.terms_of_payment,
        notes=body.notes,
        bukti_bayar_file=body.bukti_bayar_file,
    )
    db.add(doc); await db.flush()

    for i, it in enumerate(body.items):
        db.add(InvoiceItem(
            invoice_id=doc.id, item_id=it.item_id,
            description=it.description,
            quantity=Decimal(str(it.quantity)), unit_price=Decimal(str(it.unit_price)),
            total=Decimal(str(it.quantity)) * Decimal(str(it.unit_price)),
            urutan=it.urutan if it.urutan else i, notes=it.notes,
        ))
    await db.flush()

    db.add(ActivityLog(entity_type="invoice", entity_id=doc.id, action="create",
                       description=f"Created Invoice {doc.nomor}"))
    await db.flush()

    items = (await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == doc.id).order_by(InvoiceItem.urutan)
    )).scalars().all()
    resp = InvoiceDetailResponse.model_validate(doc)
    resp.items = [InvItemResponse.model_validate(i) for i in items]
    return resp


@router.patch("/{doc_id}")
async def update_invoice(doc_id: str, body: InvoiceUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    # If items updated, recalc with include_ppn based on existing doc
    if items_data is not None:
        totals = _calc_totals(items_data, True)
        doc.total = totals["total"]
        doc.ppn_amount = totals["ppn_amount"]
        doc.grand_total = totals["grand_total"]

    for k, v in update_data.items():
        setattr(doc, k, v)

    if items_data is not None:
        await db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == doc_id))
        for i, it in enumerate(items_data):
            db.add(InvoiceItem(
                invoice_id=doc_id, item_id=it.get("item_id"),
                description=it.get("description"),
                quantity=Decimal(str(it.get("quantity", 0))),
                unit_price=Decimal(str(it.get("unit_price", 0))),
                total=Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0))),
                urutan=it.get("urutan", i), notes=it.get("notes"),
            ))
    await db.flush()

    db.add(ActivityLog(entity_type="invoice", entity_id=doc_id, action="update",
                       description=f"Updated Invoice {doc.nomor}"))
    await db.flush()

    items = (await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == doc_id).order_by(InvoiceItem.urutan)
    )).scalars().all()
    resp = InvoiceDetailResponse.model_validate(doc)
    resp.items = [InvItemResponse.model_validate(i) for i in items]
    return resp


@router.delete("/{doc_id}")
async def delete_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.is_deleted = True
    db.add(ActivityLog(entity_type="invoice", entity_id=doc_id, action="delete",
                       description=f"Deleted Invoice {doc.nomor}"))
    await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/status")
async def status_invoice(doc_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted:
        raise HTTPException(404, "Invoice not found")
    new_status = body.get("status")
    allowed = {
        "draft": ["locked"],
        "locked": ["paid", "partially_paid", "bad_debt", "cancelled", "revised", "obsolete"],
        "partially_paid": ["paid", "bad_debt"],
    }
    if new_status not in allowed.get(doc.status, []):
        raise HTTPException(400, f"Invalid transition from {doc.status} to {new_status}")
    old_status = doc.status
    doc.status = new_status
    db.add(ActivityLog(entity_type="invoice", entity_id=doc_id, action="status_change",
                       description=f"Invoice {doc.nomor}: {old_status} → {new_status}"))
    await db.flush()
    return InvoiceResponse.model_validate(doc)


@router.post("/{doc_id}/revise")
async def revise_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    new_doc = await create_revision(db, Invoice, InvoiceItem, doc_id, "invoice_id")
    db.add(ActivityLog(entity_type="invoice", entity_id=doc_id, action="revise",
                       description=f"Revised Invoice {doc.nomor} → {new_doc.nomor} v{new_doc.version}"))
    await db.flush()
    return InvoiceResponse.model_validate(new_doc)
