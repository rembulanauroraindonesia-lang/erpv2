from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import get_all_settings
from app.models.contacts import Contact
from app.models.items import Item

jinja_env = Environment(loader=FileSystemLoader("app/templates"))


async def generate_pdf(doc_type: str, doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template(f"print/{doc_type}.html")

    from app.utils.format import format_rupiah, format_date_wib

    # Resolve customer
    customer = None
    if hasattr(doc, 'customer_id') and doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    # Resolve item names and supplier names
    item_ids = [pi.item_id for pi in items]
    supplier_ids = [pi.supplier_id for pi in items if pi.supplier_id]

    item_map = {}
    supplier_map = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_map = {i.id: i for i in result.scalars().all()}
    if supplier_ids:
        result = await db.execute(select(Contact).where(Contact.id.in_(supplier_ids)))
        supplier_map = {c.id: c for c in result.scalars().all()}

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        customer=customer,
        item_map=item_map,
        supplier_map=supplier_map,
        format_rupiah=format_rupiah,
        format_date=format_date_wib,
    )
    return HTML(string=html_content).write_pdf()
