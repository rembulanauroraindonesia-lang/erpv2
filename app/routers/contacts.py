from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact, ContactTopHistory
from app.schemas.contacts import (
    ContactCreate, ContactUpdate, ContactResponse,
    TopHistoryCreate, TopHistoryResponse,
)

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("")
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)

    if type:
        query = query.where(Contact.type == type)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(Contact.name.ilike(search_term), Contact.email.ilike(search_term))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Contact, sort, Contact.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    contacts = result.scalars().all()

    return {
        "data": [ContactResponse.model_validate(c) for c in contacts],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{contact_id}")
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    return ContactResponse.model_validate(contact)


@router.post("", status_code=201)
async def create_contact(body: ContactCreate, db: AsyncSession = Depends(get_db)):
    contact = Contact(**body.model_dump())
    db.add(contact)
    await db.flush()
    return ContactResponse.model_validate(contact)


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: str, body: ContactUpdate, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    await db.flush()
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    contact.is_deleted = True
    await db.flush()
    return {"ok": True}


@router.get("/{contact_id}/top-history")
async def get_top_history(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContactTopHistory)
        .where(ContactTopHistory.contact_id == contact_id)
        .order_by(ContactTopHistory.effective_date.desc())
    )
    history = result.scalars().all()
    return [TopHistoryResponse.model_validate(h) for h in history]


@router.post("/{contact_id}/top-history", status_code=201)
async def add_top_history(
    contact_id: str, body: TopHistoryCreate, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    history = ContactTopHistory(contact_id=contact_id, **body.model_dump())
    db.add(history)
    await db.flush()
    return TopHistoryResponse.model_validate(history)
