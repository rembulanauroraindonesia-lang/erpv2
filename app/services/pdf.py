from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import get_all_settings

jinja_env = Environment(loader=FileSystemLoader("app/templates"))


async def generate_pdf(doc_type: str, doc, items, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template(f"print/{doc_type}.html")

    from app.utils.format import format_rupiah, format_date_wib

    html_content = template.render(
        doc=doc,
        items=items,
        company=company,
        format_rupiah=format_rupiah,
        format_date=format_date_wib,
    )
    return HTML(string=html_content).write_pdf()
