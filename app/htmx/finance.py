from datetime import date
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.purchase_order import PurchaseOrder

router = APIRouter(prefix="/app/finance", tags=["htmx-finance"])
templates = Jinja2Templates(directory="app/templates")

STATUS_PIUTANG = ["draft", "locked", "paid"]


@router.get("")
async def finance_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    # --- Total Piutang (AR) - invoices not yet paid ---
    piutang_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.grand_total), 0)).where(
            Invoice.is_deleted == False,
            Invoice.is_current == True,
            Invoice.status.in_(["draft", "locked"]),
        )
    )
    total_piutang = (piutang_result.scalar() or 0)

    # --- Total Hutang (AP) - POs that are locked/ordered but not yet "received" ---
    hutang_result = await db.execute(
        select(func.coalesce(func.sum(PurchaseOrder.total), 0)).where(
            PurchaseOrder.is_deleted == False,
            PurchaseOrder.is_current == True,
            PurchaseOrder.status.in_(["draft", "locked"]),
        )
    )
    total_hutang = (hutang_result.scalar() or 0)

    # --- Unpaid Invoices count ---
    unpaid_result = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.is_deleted == False,
            Invoice.is_current == True,
            Invoice.status == "locked",
        )
    )
    unpaid_count = (unpaid_result.scalar() or 0)

    # --- Overdue Payments count ---
    overdue_result = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.is_deleted == False,
            Invoice.is_current == True,
            Invoice.status == "locked",
            Invoice.due_date < today,
        )
    )
    overdue_count = (overdue_result.scalar() or 0)

    # --- Outstanding Invoices (unpaid + overdue) ---
    outstanding = (await db.execute(
        select(Invoice).where(
            Invoice.is_deleted == False,
            Invoice.is_current == True,
            Invoice.status == "locked",
        ).order_by(Invoice.due_date.asc().nulls_last()).limit(20)
    )).scalars().all()

    # --- Recent Payments ---
    recent_payments = (await db.execute(
        select(Payment).where(
            Payment.status.in_(["cleared", "pending"]),
        ).order_by(Payment.payment_date.desc().nulls_last(), Payment.created_at.desc()).limit(10)
    )).scalars().all()

    # --- Collect contact names ---
    contact_ids = set()
    for inv in outstanding:
        if inv.customer_id:
            contact_ids.add(inv.customer_id)

    contacts = {}
    if contact_ids:
        c_result = await db.execute(
            select(Contact.id, Contact.name).where(Contact.id.in_(contact_ids))
        )
        contacts = {c.id: c.name for c in c_result.all()}

    return templates.TemplateResponse("finance/index.html", {
        "request": request,
        "active": "finance",
        "total_piutang": total_piutang,
        "total_hutang": total_hutang,
        "unpaid_count": unpaid_count,
        "overdue_count": overdue_count,
        "outstanding": outstanding,
        "recent_payments": recent_payments,
        "contacts": contacts,
        "today": today,
    })
