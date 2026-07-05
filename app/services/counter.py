from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import Counter

WIB = timezone(timedelta(hours=7))

COUNTER_PREFIX = {
    "penawaran": "PEN",
    "sales_order": "SO",
    "purchase_order": "PO",
    "pickup_order": "PU",
    "delivery_note": "SJ",
    "proforma_invoice": "PI",
    "invoice": "INV",
    "payment": "PAY",
}


async def get_next_number(db: AsyncSession, doc_type: str) -> str:
    year = datetime.now(WIB).year
    prefix = COUNTER_PREFIX.get(doc_type)
    if not prefix:
        raise ValueError(f"Unknown document type: {doc_type}")

    result = await db.execute(
        select(Counter).where(Counter.type == doc_type, Counter.year == year)
    )
    counter = result.scalar_one_or_none()

    if counter is None:
        counter = Counter(type=doc_type, year=year, last_number=0)
        db.add(counter)

    counter.last_number += 1
    await db.flush()

    return f"{prefix}-{year}-{counter.last_number:03d}"
