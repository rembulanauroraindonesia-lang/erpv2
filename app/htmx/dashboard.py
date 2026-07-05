from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact
from app.models.items import Item
from app.models.penawaran import Penawaran

router = APIRouter(prefix="/app", tags=["htmx-dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
@router.get("")
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Dashboard page with summary stats."""
    # Count penawaran
    p_count = (await db.execute(
        select(func.count()).select_from(Penawaran).where(
            Penawaran.is_current == True,
            Penawaran.is_deleted == False,
        )
    )).scalar() or 0

    # Count contacts
    c_count = (await db.execute(
        select(func.count()).select_from(Contact).where(
            Contact.is_deleted == False,
        )
    )).scalar() or 0

    # Count items
    i_count = (await db.execute(
        select(func.count()).select_from(Item).where(
            Item.is_deleted == False,
        )
    )).scalar() or 0

    # Recent penawaran (last 5)
    recent_result = await db.execute(
        select(Penawaran)
        .where(Penawaran.is_current == True, Penawaran.is_deleted == False)
        .order_by(Penawaran.created_at.desc())
        .limit(5)
    )
    recent_penawaran = recent_result.scalars().all()

    # Get customer names for recent penawaran
    customer_ids = [p.customer_id for p in recent_penawaran if p.customer_id]
    customers = {}
    if customer_ids:
        c_result = await db.execute(
            select(Contact).where(Contact.id.in_(customer_ids))
        )
        customers = {c.id: c.name for c in c_result.scalars().all()}

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "penawaran_count": p_count,
        "contact_count": c_count,
        "item_count": i_count,
        "recent_penawaran": recent_penawaran,
        "customers": customers,
        "active": "dashboard",
    })
