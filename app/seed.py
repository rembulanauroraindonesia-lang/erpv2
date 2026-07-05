"""Seed script: populate database with sample data."""
import asyncio
from sqlalchemy import select
from app.database import async_session_factory
from app.models.contacts import Contact
from app.models.items import Item
from app.models.system import Settings


async def seed():
    async with async_session_factory() as db:
        # Company settings
        defaults = [
            ("company_name", "PT Rembulan Aurora Indonesia"),
            ("company_address", "Jl. Raya Bisnis No. 1, Jakarta"),
            ("company_phone", "021-1234567"),
            ("company_email", "info@rembulanaurora.co.id"),
        ]
        for key, value in defaults:
            existing = await db.execute(
                select(Settings).where(Settings.key == key)
            )
            if not existing.scalar_one_or_none():
                db.add(Settings(key=key, value=value))

        # Customers
        customers = [
            Contact(type="customer", name="PT Maju Bersama", email="info@majubersama.co.id", phone="021-5551234", address="Jakarta"),
            Contact(type="customer", name="CV Sinar Jaya", email="sinar@jaya.com", phone="022-5557890", address="Bandung"),
            Contact(type="customer", name="PT Global Teknik", email="info@globaltek.co.id", phone="031-5554567", address="Surabaya"),
        ]
        for c in customers:
            db.add(c)

        # Suppliers
        suppliers = [
            Contact(type="supplier", name="PT Bahan Baku Utama", email="sales@bahanbaku.co.id", phone="021-5558888", address="Tangerang"),
            Contact(type="supplier", name="CV Material Prima", email="info@materialprima.com", phone="021-5559999", address="Bekasi"),
            Contact(type="supplier", name="PT Sumber Daya Mandiri", email="sales@sumberdaya.co.id", phone="022-5556666", address="Bandung"),
        ]
        for s in suppliers:
            db.add(s)

        # Expeditions
        expeditions = [
            Contact(type="expedition", name="JNE Express", email="cs@jne.co.id", phone="021-5551111"),
            Contact(type="expedition", name="SiCepat", email="info@sicepat.com", phone="021-5552222"),
        ]
        for e in expeditions:
            db.add(e)

        # Items
        items = [
            Item(name="Baja Ringan C75", sku="BR-C75", unit="batang", default_hpp=85000),
            Item(name="Baja Ringan C100", sku="BR-C100", unit="batang", default_hpp=110000),
            Item(name="Atap Galvalum 0.35mm", sku="AG-035", unit="lembar", default_hpp=75000),
            Item(name="Skrup Baja Ringan", sku="SKR-BR", unit="box", default_hpp=45000),
            Item(name="Dynabolt M10x80", sku="DB-M10", unit="box", default_hpp=35000),
        ]
        for i in items:
            db.add(i)

        await db.commit()
        print(f"Seeded: {len(customers)} customers, {len(suppliers)} suppliers, {len(expeditions)} expeditions, {len(items)} items, {len(defaults)} settings")


if __name__ == "__main__":
    asyncio.run(seed())
