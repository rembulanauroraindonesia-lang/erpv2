from datetime import date
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact
from app.models.pickup_order import PickupOrder
from app.models.delivery_note import DeliveryNote

router = APIRouter(prefix="/app/shipping", tags=["htmx-shipping"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def shipping_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    # --- Summary counts ---
    active_pu = (await db.execute(
        select(func.count()).select_from(PickupOrder).where(
            PickupOrder.is_deleted == False,
            PickupOrder.is_current == True,
            PickupOrder.status.in_(["draft", "locked"]),
        )
    )).scalar() or 0

    active_sj = (await db.execute(
        select(func.count()).select_from(DeliveryNote).where(
            DeliveryNote.is_deleted == False,
            DeliveryNote.is_current == True,
            DeliveryNote.status.in_(["draft", "locked"]),
        )
    )).scalar() or 0

    vehicles_out = (await db.execute(
        select(func.count()).select_from(DeliveryNote).where(
            DeliveryNote.is_deleted == False,
            DeliveryNote.is_current == True,
            DeliveryNote.status == "locked",
            DeliveryNote.delivery_date == today,
        )
    )).scalar() or 0

    pending_pu = (await db.execute(
        select(func.count()).select_from(PickupOrder).where(
            PickupOrder.is_deleted == False,
            PickupOrder.is_current == True,
            PickupOrder.status == "draft",
        )
    )).scalar() or 0

    # --- Pickup Orders Today ---
    pu_today = (await db.execute(
        select(PickupOrder).where(
            PickupOrder.is_deleted == False,
            PickupOrder.is_current == True,
            PickupOrder.pickup_date == today,
        ).order_by(PickupOrder.created_at.desc()).limit(20)
    )).scalars().all()

    # --- Delivery Notes Today ---
    sj_today = (await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.is_deleted == False,
            DeliveryNote.is_current == True,
            DeliveryNote.delivery_date == today,
        ).order_by(DeliveryNote.created_at.desc()).limit(20)
    )).scalars().all()

    # --- Collect contact names ---
    contact_ids = set()
    for pu in pu_today:
        if pu.supplier_id:
            contact_ids.add(pu.supplier_id)
    for sj in sj_today:
        if sj.customer_id:
            contact_ids.add(sj.customer_id)

    contacts = {}
    if contact_ids:
        c_result = await db.execute(
            select(Contact.id, Contact.name).where(Contact.id.in_(contact_ids))
        )
        contacts = {c.id: c.name for c in c_result.all()}

    return templates.TemplateResponse("shipping/index.html", {
        "request": request,
        "active": "shipping",
        "active_pu": active_pu,
        "active_sj": active_sj,
        "vehicles_out": vehicles_out,
        "pending_pu": pending_pu,
        "pu_today": pu_today,
        "sj_today": sj_today,
        "contacts": contacts,
        "today": today,
    })
