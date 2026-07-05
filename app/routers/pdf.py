from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.penawaran import Penawaran, PenawaranItem
from app.models.sales_order import SalesOrder, SalesOrderItem
from app.models.pickup_order import PickupOrder, PickupOrderItem
from app.models.delivery_note import DeliveryNote, DeliveryNoteItem
from app.models.invoice import Invoice, InvoiceItem
from app.services.pdf import generate_pdf, generate_so_pdf, generate_pu_pdf, generate_dn_pdf, generate_inv_pdf

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


@router.get("/sales-order/{doc_id}")
async def pdf_sales_order(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SalesOrder, doc_id)
    if not doc:
        raise HTTPException(404, "Sales Order tidak ditemukan")
    result = await db.execute(
        select(SalesOrderItem)
        .where(SalesOrderItem.sales_order_id == doc_id)
        .order_by(SalesOrderItem.urutan)
    )
    items = result.scalars().all()
    pdf_bytes = await generate_so_pdf(doc, items, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=so-{doc.nomor}.pdf"},
    )


@router.get("/pickup-order/{doc_id}")
async def pdf_pickup_order(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PickupOrder, doc_id)
    if not doc:
        raise HTTPException(404, "Pickup Order tidak ditemukan")
    result = await db.execute(
        select(PickupOrderItem)
        .where(PickupOrderItem.pickup_order_id == doc_id)
        .order_by(PickupOrderItem.urutan)
    )
    items = result.scalars().all()
    pdf_bytes = await generate_pu_pdf(doc, items, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=pu-{doc.nomor}.pdf"},
    )


@router.get("/delivery-note/{doc_id}")
async def pdf_delivery_note(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(DeliveryNote, doc_id)
    if not doc:
        raise HTTPException(404, "Surat Jalan tidak ditemukan")
    result = await db.execute(
        select(DeliveryNoteItem)
        .where(DeliveryNoteItem.delivery_note_id == doc_id)
        .order_by(DeliveryNoteItem.urutan)
    )
    items = result.scalars().all()
    pdf_bytes = await generate_dn_pdf(doc, items, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=sj-{doc.nomor}.pdf"},
    )


@router.get("/invoice/{doc_id}")
async def pdf_invoice(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Invoice, doc_id)
    if not doc:
        raise HTTPException(404, "Invoice tidak ditemukan")
    result = await db.execute(
        select(InvoiceItem)
        .where(InvoiceItem.invoice_id == doc_id)
        .order_by(InvoiceItem.urutan)
    )
    items = result.scalars().all()
    pdf_bytes = await generate_inv_pdf(doc, items, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=inv-{doc.nomor}.pdf"},
    )
