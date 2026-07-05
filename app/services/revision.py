from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import new_id


async def create_revision(db: AsyncSession, doc_model, items_model, doc_id: str, doc_fk_field: str):
    """Create a new revision of a document. Clones doc + items, marks old as revised."""
    old_doc = await db.get(doc_model, doc_id)
    if not old_doc:
        raise ValueError("Document not found")

    # Mark old as obsolete
    old_doc.is_current = False
    old_doc.status = "revised"

    # Clone document header
    new_doc = doc_model(
        id=new_id(),
        nomor=old_doc.nomor,
        version=old_doc.version + 1,
        parent_id=old_doc.id,
        is_current=True,
        status="draft",
        customer_id=getattr(old_doc, "customer_id", None),
        supplier_mode=getattr(old_doc, "supplier_mode", "single"),
        price_mode=getattr(old_doc, "price_mode", "include_ppn"),
        terms_of_payment=getattr(old_doc, "terms_of_payment", None),
        terms_of_delivery=getattr(old_doc, "terms_of_delivery", None),
        validity_days=getattr(old_doc, "validity_days", None),
        notes=getattr(old_doc, "notes", None),
        total_beli=getattr(old_doc, "total_beli", 0),
        total_jual=getattr(old_doc, "total_jual", 0),
        ppn_amount=getattr(old_doc, "ppn_amount", 0),
        grand_total=getattr(old_doc, "grand_total", 0),
    )
    db.add(new_doc)
    await db.flush()

    # Clone items
    result = await db.execute(
        select(items_model).where(getattr(items_model, doc_fk_field) == doc_id)
    )
    old_items = result.scalars().all()
    for old_item in old_items:
        item_data = {}
        for c in items_model.__table__.columns:
            if c.name not in ("id", doc_fk_field):
                item_data[c.name] = getattr(old_item, c.name)
        item_data[doc_fk_field] = new_doc.id
        item_data["id"] = new_id()
        new_item = items_model(**item_data)
        db.add(new_item)

    await db.flush()
    return new_doc
