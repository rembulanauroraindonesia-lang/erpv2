from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import Payment, PaymentHistory
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentStatusUpdate,
    PaymentResponse, PaymentHistoryResponse,
)
from app.services.counter import get_next_number

router = APIRouter(prefix="/api/payment", tags=["payment"])


def _record_history(
    payment_id: str, action: str,
    old_status: Optional[str] = None, new_status: Optional[str] = None,
    amount_before=None, amount_after=None,
    due_date_before=None, due_date_after=None,
    notes: Optional[str] = None, user_info: Optional[str] = None,
) -> PaymentHistory:
    return PaymentHistory(
        payment_id=payment_id, action=action,
        old_status=old_status, new_status=new_status,
        amount_before=amount_before, amount_after=amount_after,
        due_date_before=due_date_before, due_date_after=due_date_after,
        notes=notes, user_info=user_info,
    )


@router.get("")
async def list_payments(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    invoice_id: Optional[str] = None, proforma_invoice_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment)
    if search: query = query.where(Payment.payment_number.ilike(f"%{search}%"))
    if status: query = query.where(Payment.status == status)
    if invoice_id: query = query.where(Payment.invoice_id == invoice_id)
    if proforma_invoice_id: query = query.where(Payment.proforma_invoice_id == proforma_invoice_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.order_by(Payment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return {
        "data": [PaymentResponse.model_validate(p) for p in result.scalars().all()],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/{payment_id}")
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Payment, payment_id)
    if not doc: raise HTTPException(404, "Not found")
    history = (await db.execute(
        select(PaymentHistory).where(PaymentHistory.payment_id == payment_id).order_by(PaymentHistory.created_at.desc())
    )).scalars().all()
    resp = PaymentResponse.model_validate(doc)
    return {"payment": resp, "history": [PaymentHistoryResponse.model_validate(h) for h in history]}


@router.get("/{payment_id}/history")
async def get_payment_history(payment_id: str, db: AsyncSession = Depends(get_db)):
    history = (await db.execute(
        select(PaymentHistory).where(PaymentHistory.payment_id == payment_id).order_by(PaymentHistory.created_at.desc())
    )).scalars().all()
    return [PaymentHistoryResponse.model_validate(h) for h in history]


@router.post("", status_code=201)
async def create_payment(body: PaymentCreate, db: AsyncSession = Depends(get_db)):
    payment_number = await get_next_number(db, "payment")

    doc = Payment(
        payment_number=payment_number,
        invoice_id=body.invoice_id,
        proforma_invoice_id=body.proforma_invoice_id,
        amount=body.amount,
        payment_method=body.payment_method,
        payment_date=body.payment_date or date.today(),
        due_date=body.due_date,
        giro_bank=body.giro_bank,
        giro_number=body.giro_number,
        notes=body.notes,
    )
    db.add(doc); await db.flush()

    db.add(_record_history(
        doc.id, action="created", new_status="pending",
        amount_after=doc.amount,
    ))
    await db.flush()

    return PaymentResponse.model_validate(doc)


@router.patch("/{payment_id}")
async def update_payment(payment_id: str, body: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Payment, payment_id)
    if not doc: raise HTTPException(404, "Not found")

    update_data = body.model_dump(exclude_unset=True)
    old_amount = doc.amount
    for k, v in update_data.items():
        setattr(doc, k, v)
    await db.flush()

    if "amount" in update_data and old_amount != doc.amount:
        db.add(_record_history(doc.id, action="updated",
                               amount_before=old_amount, amount_after=doc.amount))
        await db.flush()

    return PaymentResponse.model_validate(doc)


@router.delete("/{payment_id}")
async def delete_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Payment, payment_id)
    if not doc: raise HTTPException(404, "Not found")
    await db.delete(doc); await db.flush()
    return {"ok": True}


@router.post("/{payment_id}/status")
async def update_payment_status(payment_id: str, body: PaymentStatusUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Payment, payment_id)
    if not doc: raise HTTPException(404, "Not found")

    old_status = doc.status
    old_due = doc.due_date

    if body.action == "cleared":
        doc.status = "cleared"
        doc.cleared_date = body.cleared_date or date.today()
    elif body.action == "extended":
        if body.due_date_new:
            old_due = doc.due_date
            doc.status = "extended"
            doc.extension_count = (doc.extension_count or 0) + 1
            doc.due_date = body.due_date_new
    elif body.action == "bad_debt_declared":
        doc.status = "bad_debt"
        doc.bad_debt_reason = body.bad_debt_reason
    elif body.action == "cancelled":
        doc.status = "cancelled"
    else:
        raise HTTPException(400, f"Invalid action: {body.action}")

    await db.flush()

    db.add(_record_history(
        doc.id, action=body.action,
        old_status=old_status, new_status=doc.status,
        due_date_before=old_due, due_date_after=doc.due_date,
        notes=body.notes, user_info=body.user_info,
    ))
    await db.flush()

    return PaymentResponse.model_validate(doc)
