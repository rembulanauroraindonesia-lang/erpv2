from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import Payment, PaymentHistory
from app.models.contacts import Contact
from app.schemas.payment import PaymentHistoryResponse

router = APIRouter(prefix="/app/payment", tags=["htmx-payment"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def payment_index(
    request: Request, page: int = Query(1, ge=1), search: str = None, status: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment)
    if search: query = query.where(Payment.payment_number.ilike(f"%{search}%"))
    if status: query = query.where(Payment.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    per_page = 20
    total_pages = max(1, (total + per_page - 1) // per_page)

    query = query.order_by(Payment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    docs = result.scalars().all()

    return templates.TemplateResponse("payment/index.html", {
        "request": request, "active": "payment",
        "docs": docs,
        "page": page, "total": total, "per_page": per_page,
        "total_pages": total_pages, "search": search or "", "status_filter": status or "",
    })


@router.get("/{payment_id}")
async def payment_detail(payment_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Payment, payment_id)
    if not doc:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/app/payment", 302)

    history = (await db.execute(
        select(PaymentHistory).where(PaymentHistory.payment_id == payment_id).order_by(PaymentHistory.created_at.desc())
    )).scalars().all()

    from datetime import date
    return templates.TemplateResponse("payment/detail.html", {
        "request": request, "active": "payment",
        "doc": doc, "history": history, "today": date.today(),
    })
