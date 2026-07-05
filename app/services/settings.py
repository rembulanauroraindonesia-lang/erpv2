import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import Settings


async def get_setting(db: AsyncSession, key: str, fallback=None):
    result = await db.execute(select(Settings).where(Settings.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return fallback
    try:
        return json.loads(row.value)
    except (json.JSONDecodeError, TypeError):
        return row.value


async def set_setting(db: AsyncSession, key: str, value):
    result = await db.execute(select(Settings).where(Settings.key == key))
    row = result.scalar_one_or_none()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    if row is None:
        db.add(Settings(key=key, value=serialized))
    else:
        row.value = serialized
    await db.flush()


async def get_all_settings(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings))
    rows = result.scalars().all()
    settings = {}
    for row in rows:
        try:
            settings[row.key] = json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            settings[row.key] = row.value
    return settings
