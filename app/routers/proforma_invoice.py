from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.proforma_invoice import ProformaInvoice, ProformaInvoiceItem
from app.schemas.proforma_invoice import (
    ProformaInvoiceCreate, ProformaInvoiceUpdate,
    ProformaInvoiceResponse, ProformaInvoiceDetailResponse, PIItemResponse,
)
from app.services.counter import get_next_number
from app.services.revision import create_revision

router = APIRouter(prefix="/api/proforma-invoice", tags=["proforma-invoice"])

PPN_RATE = Decimal("0.11")


def _calc_totals(items, include_ppn=True):
    subtotal = sum(Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0)))
                   for it in items)
    if include_ppn:
        ppn = (subtotal * PPN_RATE).quantize(Decimal("0.01"))
        total = subtotal + ppn
    else:
        total = subtotal
        ppn = (subtotal * PPN_RATE / (1 + PPN_RATE)).quantize(Decimal("0.01"))
    return {"subtotal": subtotal.quantize(Decimal("0.01")), "ppn_amount": ppn, "total": total}


@router.get("")
async def list_proforma_invoices(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ProformaInvoice).where(ProformaInvoice.is_deleted == False, ProformaInvoice.is_current == True)
    if search: query = query.where(ProformaInvoice.nomor.ilike(f"%{search}%"))
    if status: query = query.where(ProformaInvoice.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(ProformaInvoice.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [ProformaInvoiceResponse.model_validate(i) for i in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{doc_id}")
async def get_proforma_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    items = (await db.execute(
        select(ProformaInvoiceItem).where(ProformaInvoiceItem.proforma_invoice_id == doc_id).order_by(ProformaInvoiceItem.urutan)
    )).scalars().all()
    resp = ProformaInvoiceDetailResponse.model_validate(doc)
    resp.items = [PIItemResponse.model_validate(i) for i in items]
    return resp


@router.post("", status_code=201)
async def create_proforma_invoice(body: ProformaInvoiceCreate, db: AsyncSession = Depends(get_db)):
    nomor = await get_next_number(db, "proforma_invoice")
    items_data = [it.model_dump() for it in body.items]
    totals = _calc_totals(items_data, body.include_ppn)

    doc = ProformaInvoice(
        nomor=nomor, customer_id=body.customer_id,
        sales_order_id=body.sales_order_id,
        subtotal=totals["subtotal"], ppn_amount=totals["ppn_amount"], total=totals["total"],
        due_date=body.due_date,
        payment_method=body.payment_method,
        terms_of_payment=body.terms_of_payment,
        terms_of_delivery=body.terms_of_delivery,
        pic_name=body.pic_name, pic_phone=body.pic_phone,
        notes=body.notes,
    )
    db.add(doc); await db.flush()

    for i, it in enumerate(body.items):
        db.add(ProformaInvoiceItem(
            proforma_invoice_id=doc.id, item_id=it.item_id,
            description=it.description,
            quantity=Decimal(str(it.quantity)), unit_price=Decimal(str(it.unit_price)),
            total=Decimal(str(it.quantity)) * Decimal(str(it.unit_price)),
            urutan=it.urutan if it.urutan else i, notes=it.notes,
        ))
    await db.flush()

    items = (await db.execute(
        select(ProformaInvoiceItem).where(ProformaInvoiceItem.proforma_invoice_id == doc.id).order_by(ProformaInvoiceItem.urutan)
    )).scalars().all()
    resp = ProformaInvoiceDetailResponse.model_validate(doc)
    resp.items = [PIItemResponse.model_validate(i) for i in items]
    return resp


@router.patch("/{doc_id}")
async def update_proforma_invoice(doc_id: str, body: ProformaInvoiceUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    if items_data is not None:
        totals = _calc_totals(items_data, True)
        doc.subtotal = totals["subtotal"]
        doc.ppn_amount = totals["ppn_amount"]
        doc.total = totals["total"]

    for k, v in update_data.items():
        setattr(doc, k, v)

    if items_data is not None:
        await db.execute(delete(ProformaInvoiceItem).where(ProformaInvoiceItem.proforma_invoice_id == doc_id))
        for i, it in enumerate(items_data):
            db.add(ProformaInvoiceItem(
                proforma_invoice_id=doc_id, item_id=it.get("item_id"),
                description=it.get("description"),
                quantity=Decimal(str(it.get("quantity", 0))),
                unit_price=Decimal(str(it.get("unit_price", 0))),
                total=Decimal(str(it.get("quantity", 0))) * Decimal(str(it.get("unit_price", 0))),
                urutan=it.get("urutan", i), notes=it.get("notes"),
            ))
    await db.flush()

    items = (await db.execute(
        select(ProformaInvoiceItem).where(ProformaInvoiceItem.proforma_invoice_id == doc_id).order_by(ProformaInvoiceItem.urutan)
    )).scalars().all()
    resp = ProformaInvoiceDetailResponse.model_validate(doc)
    resp.items = [PIItemResponse.model_validate(i) for i in items]
    return resp


@router.delete("/{doc_id}")
async def delete_proforma_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.is_deleted = True; await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/revise")
async def revise_proforma_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    new_doc = await create_revision(db, ProformaInvoice, ProformaInvoiceItem, doc_id, "proforma_invoice_id")
    return ProformaInvoiceResponse.model_validate(new_doc)


@router.post("/{doc_id}/send")
async def send_proforma_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    if doc.status not in ("draft", "revised"):
        raise HTTPException(400, "Only draft/revised PI can be sent")
    doc.status = "sent"; await db.flush()
    return ProformaInvoiceResponse.model_validate(doc)


@router.post("/{doc_id}/mark-paid")
async def mark_pi_paid(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.status = "paid"; await db.flush()
    return ProformaInvoiceResponse.model_validate(doc)


@router.post("/{doc_id}/cancel")
async def cancel_proforma_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(ProformaInvoice, doc_id)
    if not doc or doc.is_deleted: raise HTTPException(404, "Not found")
    doc.status = "cancelled"; await db.flush()
    return ProformaInvoiceResponse.model_validate(doc)
