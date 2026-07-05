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


async def generate_so_pdf(doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template("print/sales_order.html")

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [pi.item_id for pi in items]
    item_names = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in result.scalars().all()}

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        customer_name=customer.name if customer else '-',
        customer_npwp=getattr(customer, 'npwp', None),
        customer_address=getattr(customer, 'address', None),
        item_names=item_names,
    )
    return HTML(string=html_content).write_pdf()


async def generate_pu_pdf(doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template("print/pickup_order.html")

    supplier = None
    if doc.supplier_id:
        supplier = await db.get(Contact, doc.supplier_id)
    
    expedition = None
    if doc.expedition_id:
        expedition = await db.get(Contact, doc.expedition_id)

    item_ids = [pi.item_id for pi in items]
    item_names = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in result.scalars().all()}

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        supplier_name=supplier.name if supplier else '-',
        supplier_address=getattr(supplier, 'address', None) if supplier else None,
        expedition_name=expedition.name if expedition else '-',
        item_names=item_names,
    )
    return HTML(string=html_content).write_pdf()


async def generate_dn_pdf(doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template("print/delivery_note.html")

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)
    
    expedition = None
    if doc.expedition_id:
        expedition = await db.get(Contact, doc.expedition_id)

    item_ids = [pi.item_id for pi in items]
    item_names = {}
    item_units = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        for i in result.scalars().all():
            item_names[i.id] = i.name
            item_units[i.id] = getattr(i, 'unit', '-')

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        customer_name=customer.name if customer else '-',
        customer_npwp=getattr(customer, 'npwp', None),
        customer_address=getattr(customer, 'address', None),
        expedition_name=expedition.name if expedition else '-',
        item_names=item_names,
        item_units=item_units,
    )
    return HTML(string=html_content).write_pdf()


async def generate_inv_pdf(doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template("print/invoice.html")

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [pi.item_id for pi in items if pi.item_id]
    item_names = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in result.scalars().all()}

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        customer_name=customer.name if customer else '-',
        customer_npwp=getattr(customer, 'npwp', None),
        customer_address=getattr(customer, 'address', None),
        item_names=item_names,
    )
    return HTML(string=html_content).write_pdf()


async def generate_pi_pdf(doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template("print/proforma_invoice.html")

    customer = None
    if doc.customer_id:
        customer = await db.get(Contact, doc.customer_id)

    item_ids = [pi.item_id for pi in items if pi.item_id]
    item_names = {}
    if item_ids:
        result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
        item_names = {i.id: i.name for i in result.scalars().all()}

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        customer_name=customer.name if customer else '-',
        customer_npwp=getattr(customer, 'npwp', None),
        customer_address=getattr(customer, 'address', None),
        item_names=item_names,
    )
    return HTML(string=html_content).write_pdf()
