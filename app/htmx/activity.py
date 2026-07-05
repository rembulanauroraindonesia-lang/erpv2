from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.system import ActivityLog

router = APIRouter(prefix="/app/activity", tags=["htmx-activity"])
templates = Jinja2Templates(directory="app/templates")

WIB = timezone(timedelta(hours=7))


@router.get("")
async def activity_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show recent 50 activity logs."""
    result = await db.execute(
        select(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()

    entity_labels = {
        "penawaran": "Penawaran",
        "sales_order": "Sales Order",
        "purchase_order": "Purchase Order",
        "pickup_order": "Pickup Order",
        "delivery_note": "Surat Jalan",
        "invoice": "Invoice",
        "proforma_invoice": "Proforma Invoice",
        "payment": "Payment",
    }

    action_labels = {
        "create": "Created",
        "update": "Updated",
        "delete": "Deleted",
        "status_change": "Status Changed",
        "revise": "Revised",
    }

    action_colors = {
        "create": "bg-green-100 text-green-800",
        "update": "bg-blue-100 text-blue-800",
        "delete": "bg-red-100 text-red-800",
        "status_change": "bg-amber-100 text-amber-800",
        "revise": "bg-purple-100 text-purple-800",
    }

    return templates.TemplateResponse("activity/index.html", {
        "request": request,
        "logs": logs,
        "entity_labels": entity_labels,
        "action_labels": action_labels,
        "action_colors": action_colors,
        "active": "activity",
    })
