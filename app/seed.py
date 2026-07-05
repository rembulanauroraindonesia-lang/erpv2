"""Seed data for development."""
import asyncio
from sqlalchemy import text
from app.database import async_session_factory
from app.models.contacts import Contact, ContactTopHistory
from app.models.items import Item
from app.services.settings import get_setting, set_setting


async def seed():
    async with async_session_factory() as db:
        # --- Settings (company + defaults) ---
        if await get_setting(db, "company_name") is None:
            await set_setting(db, "company_name", "PT Rembulan Aurora Indonesia")
        if await get_setting(db, "company_address") is None:
            await set_setting(db, "company_address", "Jl. Raya Industri No. 88, Kawasan Industri Pulogadung, Jakarta Timur")
        if await get_setting(db, "company_phone") is None:
            await set_setting(db, "company_phone", "021-5555-1234")
        if await get_setting(db, "company_email") is None:
            await set_setting(db, "company_email", "info@rembulan-aurora.co.id")
        if await get_setting(db, "company_npwp") is None:
            await set_setting(db, "company_npwp", "01.234.567.8-901.000")
        if await get_setting(db, "company_city") is None:
            await set_setting(db, "company_city", "Jakarta")
        if await get_setting(db, "default_supplier_mode") is None:
            await set_setting(db, "default_supplier_mode", "single")
        if await get_setting(db, "default_price_mode") is None:
            await set_setting(db, "default_price_mode", "include_ppn")
        if await get_setting(db, "default_ppn_rate") is None:
            await set_setting(db, "default_ppn_rate", 11)
        if await get_setting(db, "default_validity_days") is None:
            await set_setting(db, "default_validity_days", 14)

        # --- Customers ---
        result = await db.execute(text("SELECT COUNT(*) FROM contacts WHERE type='customer'"))
        if result.scalar() == 0:
            customers = [
                Contact(type="customer", name="PT Maju Bersama", email="purchasing@majubersama.co.id",
                        phone="021-8888-1001", address="Jl. Sudirman No. 45, Jakarta Pusat 10220",
                        npwp="02.111.222.3-401.000", contact_person="Bpk. Hendra — Purchasing",
                        contact_phone="0812-1111-1001", pic_name="Bpk. Hendra", pic_phone="0812-1111-1001",
                        terms_of_payment="TOP 30 hari",
                        terms_of_delivery="Franco Gudang Pembeli",
                        notes="TOP 30 hari, customer loyal sejak 2022"),
                Contact(type="customer", name="CV Sumber Rezeki", email="admin@sumberrezeki.co.id",
                        phone="031-7777-2002", address="Jl. Ahmad Yani No. 22, Surabaya 60231",
                        npwp="03.222.333.4-502.000", contact_person="Ibu Rina — Finance",
                        contact_phone="0813-2222-2002", pic_name="Ibu Rina", pic_phone="0813-2222-2002",
                        terms_of_payment="TOP 14 hari",
                        terms_of_delivery="Franco Gudang Pembeli",
                        notes="TOP 14 hari, pembayaran via transfer BCA"),
                Contact(type="customer", name="UD Berkah Abadi", email="berkahabadi@gmail.com",
                        phone="022-6666-3003", address="Jl. Raya Bandung No. 10, Bandung 40123",
                        npwp="04.333.444.5-603.000", contact_person="Bpk. Agus — Direktur",
                        contact_phone="0814-3333-3003", pic_name="Bpk. Agus", pic_phone="0814-3333-3003",
                        terms_of_payment="TOP 7 hari",
                        terms_of_delivery="Diantar ke Alamat",
                        notes="TOP 7 hari, customer baru sejak 2026"),
            ]
            db.add_all(customers)
            print(f"Seeded {len(customers)} customers")

        # --- Suppliers ---
        result = await db.execute(text("SELECT COUNT(*) FROM contacts WHERE type='supplier'"))
        if result.scalar() == 0:
            suppliers = [
                Contact(type="supplier", name="PT Indo Steel Industries", email="sales@indosteel.co.id",
                        phone="021-4444-5001", address="Jl. Raya Industri No. 55, Bekasi 17530",
                        npwp="05.444.555.6-704.000", contact_person="Ibu Dewi — Sales Manager",
                        contact_phone="0815-4444-5001", pic_name="Ibu Dewi", pic_phone="0815-4444-5001",
                        terms_of_payment="TOP 30 hari",
                        terms_of_delivery="Franco Gudang Supplier"),
                Contact(type="supplier", name="CV Metal Parts Nusantara", email="metalparts@gmail.com",
                        phone="024-3333-6002", address="Jl. Raya Semarang No. 33, Semarang 50123",
                        npwp="06.555.666.7-805.000", contact_person="Bpk. Toni — Owner",
                        contact_phone="0816-5555-6002", pic_name="Bpk. Toni", pic_phone="0816-5555-6002",
                        terms_of_payment="Cash on Delivery",
                        terms_of_delivery="Diantar ke Alamat"),
                Contact(type="supplier", name="PT Global Steel Supply", email="order@globalsteel.co.id",
                        phone="021-2222-7003", address="Jl. Raya Tangerang No. 77, Tangerang 15123",
                        npwp="07.666.777.8-906.000", contact_person="Ibu Sari — Purchasing",
                        contact_phone="0817-6666-7003", pic_name="Ibu Sari", pic_phone="0817-6666-7003",
                        terms_of_payment="TOP 14 hari",
                        terms_of_delivery="Franco Gudang Pembeli"),
            ]
            db.add_all(suppliers)
            print(f"Seeded {len(suppliers)} suppliers")

        # --- Expeditions ---
        result = await db.execute(text("SELECT COUNT(*) FROM contacts WHERE type='expedition'"))
        if result.scalar() == 0:
            expeditions = [
                Contact(type="expedition", name="SiCepat Ekspres", phone="021-1111-8001",
                        address="Jl. Raya Cakung No. 20, Jakarta Timur",
                        contact_phone="0818-1111-8001", pic_name="CS SiCepat", pic_phone="0818-1111-8001",
                        terms_of_payment="Cash on Delivery",
                        terms_of_delivery="Diantar ke Alamat"),
                Contact(type="expedition", name="JNE Express", phone="021-2222-9002",
                        address="Jl. Tomang Raya No. 11, Jakarta Barat",
                        contact_phone="0819-2222-9002", pic_name="CS JNE", pic_phone="0819-2222-9002",
                        terms_of_payment="TOP 7 hari",
                        terms_of_delivery="Diantar ke Alamat"),
            ]
            db.add_all(expeditions)
            print(f"Seeded {len(expeditions)} expeditions")

        # --- Marketing contacts ---
        result = await db.execute(text("SELECT COUNT(*) FROM contacts WHERE type='marketing'"))
        if result.scalar() == 0:
            marketing = [
                Contact(type="marketing", name="Ibu Maya — Marketing Manager",
                        phone="0812-3456-7890", email="maya@rembulan-aurora.co.id",
                        contact_phone="0812-3456-7890", pic_name="Ibu Maya", pic_phone="0812-3456-7890",
                        terms_of_payment="TOP 14 hari",
                        terms_of_delivery="Diantar ke Alamat",
                        notes="Staff internal — handle penawaran dan follow-up customer"),
            ]
            db.add_all(marketing)
            print(f"Seeded {len(marketing)} marketing contacts")

        # --- Items ---
        result = await db.execute(text("SELECT COUNT(*) FROM items"))
        if result.scalar() == 0:
            items = [
                Item(name="Besi Beton Ulir 13mm", sku="BBU-013", unit="kg", default_hpp=12500,
                     notes="Standar SNI, panjang 12m"),
                Item(name="Plat Besi 3mm", sku="PLT-003", unit="kg", default_hpp=11000,
                     notes="Ukuran 1.2m x 2.4m"),
                Item(name="Pipa Galvanis 2 inch", sku="PGV-200", unit="pcs", default_hpp=185000,
                     notes="Panjang 6m, SCH 40"),
                Item(name="Wiremesh M8", sku="WM8-015", unit="lembar", default_hpp=450000,
                     notes="Ukuran 2.1m x 5.4m"),
                Item(name="Baut Mur 12mm", sku="BM-012", unit="pcs", default_hpp=2500,
                     notes="Grade 8.8, full drat"),
            ]
            db.add_all(items)
            print(f"Seeded {len(items)} items")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
