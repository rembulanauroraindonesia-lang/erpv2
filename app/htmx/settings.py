from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.settings import get_all_settings

router = APIRouter(prefix="/app/pengaturan", tags=["htmx-settings"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def settings_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Settings page with form showing all current settings."""
    all_settings = await get_all_settings(db)
    return templates.TemplateResponse("settings/index.html", {
        "request": request,
        "settings": all_settings,
        "active": "pengaturan",
    })
