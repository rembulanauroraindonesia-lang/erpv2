from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.items import Item
from app.schemas.items import ItemCreate, ItemUpdate, ItemResponse

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("")
async def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Item).where(Item.is_deleted == False)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(Item.name.ilike(search_term), Item.sku.ilike(search_term))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Item, sort, Item.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "data": [ItemResponse.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{item_id}")
async def get_item(item_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item or item.is_deleted:
        raise HTTPException(404, "Item not found")
    return ItemResponse.model_validate(item)


@router.post("", status_code=201)
async def create_item(body: ItemCreate, db: AsyncSession = Depends(get_db)):
    item = Item(**body.model_dump())
    db.add(item)
    await db.flush()
    return ItemResponse.model_validate(item)


@router.patch("/{item_id}")
async def update_item(
    item_id: str, body: ItemUpdate, db: AsyncSession = Depends(get_db)
):
    item = await db.get(Item, item_id)
    if not item or item.is_deleted:
        raise HTTPException(404, "Item not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.flush()
    return ItemResponse.model_validate(item)


@router.delete("/{item_id}")
async def delete_item(item_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item or item.is_deleted:
        raise HTTPException(404, "Item not found")
    item.is_deleted = True
    await db.flush()
    return {"ok": True}
