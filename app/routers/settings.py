import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.settings import get_all_settings, set_setting
from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Return all settings as a dict."""
    return await get_all_settings(db)


@router.put("")
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Update multiple settings at once."""
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            await set_setting(db, key, value)
    return await get_all_settings(db)


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload company logo."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Get extension from filename
    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    filename = f"logo{ext}"
    filepath = os.path.join(settings.data_dir, filename)

    os.makedirs(settings.data_dir, exist_ok=True)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    await set_setting(db, "logo_path", f"/data/{filename}")

    return {"ok": True, "path": f"/data/{filename}"}
