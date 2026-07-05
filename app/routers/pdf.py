from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.penawaran import Penawaran, PenawaranItem
from app.services.pdf import generate_pdf

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.get("/penawaran/{doc_id}")
async def pdf_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Penawaran, doc_id)
    if not doc:
        raise HTTPException(404, "Penawaran tidak ditemukan")
    result = await db.execute(
        select(PenawaranItem)
        .where(PenawaranItem.penawaran_id == doc_id)
        .order_by(PenawaranItem.urutan)
    )
    items = result.scalars().all()
    pdf_bytes = await generate_pdf("penawaran", doc, items, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=penawaran-{doc.nomor}.pdf"},
    )
