# RAI ERP v2 — Design Specification

**Date:** 2026-07-05
**Project:** ERP PT Rembulan Aurora Indonesia (Redesign)
**Repo:** https://github.com/rembulanauroraindonesia-lang/erpv2

---

## Overview

Sistem ERP untuk PT Rembulan Aurora Indonesia — mengelola quotation, purchase order, sales order, pickup order, delivery note, proforma invoice, invoice, items, shipping, finance, contacts, dan settings.

**Locale:** Bahasa Indonesia (UI), English di beberapa bagian teknis. Mata uang Rp. Waktu WIB (Asia/Jakarta).

**Key outputs:** PDF generation untuk semua dokumen + tracking dashboard.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Runtime | Python | 3.11 | Language |
| Framework | FastAPI | 0.115+ | API + HTMX routing |
| Server | Uvicorn | 0.30+ | ASGI server |
| ORM | SQLAlchemy | 2.0+ (async) | Models + queries |
| DB Driver | aiosqlite | 0.20+ | Async SQLite |
| Migrations | Alembic | 1.13+ | Database migrations |
| Templates | Jinja2 | 3.1+ | Server-rendered HTML |
| Frontend | HTMX | 2.0 | Interactivity |
| Frontend | Alpine.js | 3.14 | Live calc, UI state |
| CSS | TailwindCSS | 3.4 (CDN) | Styling — no build step |
| PDF | WeasyPrint | 62+ | HTML → PDF |
| Validation | Pydantic | 2.9+ | Request/response schemas |
| File Upload | python-multipart | 0.0.9+ | Multipart form handling |

**Dependencies: ~12 packages.**

---

## Architecture

### Approach: Monolith Simple (Single Docker Container)

```
┌─────────────────────────────────────┐
│  Docker Container                   │
│  ┌───────────────────────────────┐  │
│  │ FastAPI (port 8000)           │  │
│  │ ├─ REST API (/api/*)          │  │
│  │ ├─ HTMX Routes (/app/*)       │  │
│  │ ├─ SQLAlchemy + SQLite        │  │
│  │ ├─ WeasyPrint PDF generation  │  │
│  │ └─ Static files + uploads     │  │
│  └───────────────────────────────┘  │
│  Volume: ./data (sqlite + uploads)  │
└─────────────────────────────────────┘
```

**~50MB RAM total. Zero external dependencies.**

### Production Migration Path

Docker untuk development. Production = native (systemd + nginx/caddy). Migration:
1. Stop container
2. `tar -czf backup.tar.gz data/`
3. Copy ke production server
4. Restore + systemd service + nginx/caddy reverse proxy

SQLite single-file = zero downtime backup (just copy `.db` file).

---

## Database Schema (21 Tables)

### Core Entities

#### `contacts`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| type | ENUM | supplier, customer, expedition, marketing |
| name | VARCHAR(200) | NOT NULL |
| email | VARCHAR(200) | nullable |
| phone | VARCHAR(50) | nullable |
| address | TEXT | nullable |
| npwp | VARCHAR(50) | nullable |
| tax_info | TEXT | nullable |
| notes | TEXT | nullable |
| is_deleted | BOOLEAN | default false (soft delete) |
| created_at | DATETIME | WIB |
| updated_at | DATETIME | WIB |

#### `contact_top_history`
Terms of Payment history — TOP bisa berubah per contact seiring waktu.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| contact_id | UUID (FK → contacts) | NOT NULL |
| top_type | VARCHAR(20) | CBD, COD, GBD, GOD, Tempo |
| tempo_days | INT | nullable, only for Tempo |
| effective_date | DATE | NOT NULL |
| notes | TEXT | nullable |
| created_at | DATETIME | |

Latest TOP: `ORDER BY effective_date DESC LIMIT 1`

#### `items`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | VARCHAR(200) | NOT NULL |
| sku | VARCHAR(50) | nullable, unique |
| unit | VARCHAR(20) | pcs, kg, box, etc |
| default_hpp | DECIMAL(15,2) | default 0 |
| notes | TEXT | nullable |
| is_deleted | BOOLEAN | default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### Sales Flow

#### `penawaran` (Quotation)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: PEN-2026-001 |
| customer_id | UUID (FK → contacts) | nullable |
| supplier_mode | VARCHAR(10) | single, multi |
| price_mode | VARCHAR(20) | include_ppn, exclude_ppn |
| terms_of_payment | TEXT | nullable |
| terms_of_delivery | TEXT | nullable |
| validity_days | INT | nullable |
| notes | TEXT | nullable |
| status | VARCHAR(20) | draft, locked, approved, revised, obsolete |
| total_beli | DECIMAL(15,2) | |
| total_jual | DECIMAL(15,2) | |
| ppn_amount | DECIMAL(15,2) | |
| grand_total | DECIMAL(15,2) | |
| version | INT | default 1 |
| parent_id | UUID (FK → penawaran) | nullable, NULL for v1 |
| is_current | BOOLEAN | default true |
| is_deleted | BOOLEAN | default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

#### `penawaran_items`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| penawaran_id | UUID (FK → penawaran) | NOT NULL |
| item_id | UUID (FK → items) | NOT NULL |
| supplier_id | UUID (FK → contacts) | nullable if supplier_mode=single |
| quantity | DECIMAL(15,4) | |
| berat_beli_per_unit | DECIMAL(10,4) | kg, 0 = mode per unit |
| hpp_per_unit | DECIMAL(15,2) | |
| total_beli | DECIMAL(15,2) | computed |
| harga_jual_per_unit | DECIMAL(15,2) | |
| total_jual | DECIMAL(15,2) | computed |
| different_scale | BOOLEAN | default false |
| berat_jual_per_unit | DECIMAL(10,4) | nullable, only if different_scale=true |
| urutan | INT | display order |
| notes | TEXT | nullable |

**Calculation logic:**
- `total_beli` = quantity × berat_beli_per_unit × hpp_per_unit (if berat > 0), else quantity × hpp_per_unit
- `total_jual` = quantity × (different_scale ? berat_jual_per_unit : berat_beli_per_unit) × harga_jual_per_unit (if berat > 0), else quantity × harga_jual_per_unit
- PPN: include mode → extract from total_jual (total/1.11 × 0.11), exclude mode → add to total_jual (total × 0.11)

#### `sales_orders`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: SO-2026-001 |
| penawaran_id | UUID (FK → penawaran) | nullable (flexible linking) |
| customer_id | UUID (FK → contacts) | nullable |
| status | VARCHAR(20) | draft, confirmed, in_progress, completed, cancelled, revised, obsolete |
| total | DECIMAL(15,2) | |
| ppn_amount | DECIMAL(15,2) | |
| grand_total | DECIMAL(15,2) | |
| order_date | DATE | |
| delivery_date | DATE | nullable |
| notes | TEXT | |
| version | INT | default 1 |
| parent_id | UUID | nullable |
| is_current | BOOLEAN | default true |
| is_deleted | BOOLEAN | default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

#### `sales_order_items`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| sales_order_id | UUID (FK) | NOT NULL |
| item_id | UUID (FK) | NOT NULL |
| quantity | DECIMAL(15,4) | |
| unit_price | DECIMAL(15,2) | |
| total | DECIMAL(15,2) | |
| urutan | INT | |
| notes | TEXT | |

#### `purchase_orders`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: PO-2026-001 |
| sales_order_id | UUID (FK) | nullable |
| penawaran_id | UUID (FK) | nullable |
| supplier_id | UUID (FK → contacts) | nullable |
| status | VARCHAR(20) | draft, sent, confirmed, received, cancelled, revised, obsolete |
| total | DECIMAL(15,2) | |
| ppn_amount | DECIMAL(15,2) | |
| grand_total | DECIMAL(15,2) | |
| order_date | DATE | |
| expected_delivery | DATE | nullable |
| bukti_po_file | VARCHAR(500) | nullable, upload path |
| notes | TEXT | |
| version, parent_id, is_current, is_deleted | — | standard revision fields |
| created_at, updated_at | DATETIME | |

#### `purchase_order_items`
Same structure as sales_order_items + supplier_id.

#### `pickup_orders`
Instruksi internal untuk ambil barang dari supplier (kasih ke expedition/driver).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: PU-2026-001 |
| purchase_order_id | UUID (FK) | nullable |
| supplier_id | UUID (FK → contacts) | nullable |
| expedition_id | UUID (FK → contacts) | nullable |
| status | VARCHAR(20) | draft, sent, picked_up, received, cancelled, revised, obsolete |
| pickup_date | DATE | nullable |
| received_date | DATE | nullable |
| notes | TEXT | |
| version, parent_id, is_current, is_deleted | — | standard |
| created_at, updated_at | DATETIME | |

#### `pickup_order_items`
Standard item structure.

#### `delivery_notes` (Surat Jalan)
Pengiriman ke customer.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: SJ-2026-001 |
| sales_order_id | UUID (FK) | nullable |
| customer_id | UUID (FK → contacts) | nullable |
| expedition_id | UUID (FK → contacts) | nullable |
| status | VARCHAR(20) | draft, sent, delivered, cancelled, revised, obsolete |
| shipping_date | DATE | nullable |
| delivered_date | DATE | nullable |
| bukti_kirim_file | VARCHAR(500) | nullable |
| notes | TEXT | |
| version, parent_id, is_current, is_deleted | — | standard |
| created_at, updated_at | DATETIME | |

#### `delivery_note_items`
Standard item structure.

### Finance

#### `proforma_invoices`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: PI-2026-001 |
| sales_order_id | UUID (FK) | nullable |
| customer_id | UUID (FK → contacts) | nullable |
| status | VARCHAR(20) | draft, sent, paid, cancelled, revised, obsolete |
| subtotal | DECIMAL(15,2) | |
| ppn_amount | DECIMAL(15,2) | |
| total | DECIMAL(15,2) | |
| due_date | DATE | nullable |
| payment_method | VARCHAR(20) | nullable: transfer, giro, cek |
| bukti_bayar_file | VARCHAR(500) | nullable |
| bukti_giro_cek_file | VARCHAR(500) | nullable |
| notes | TEXT | |
| version, parent_id, is_current, is_deleted | — | standard |
| created_at, updated_at | DATETIME | |

#### `proforma_invoice_items`
Standard item structure.

#### `invoices`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| nomor | VARCHAR(20) | auto: INV-2026-001 |
| sales_order_id | UUID (FK) | nullable |
| proforma_invoice_id | UUID (FK) | nullable |
| customer_id | UUID (FK → contacts) | nullable |
| supplier_id | UUID (FK → contacts) | nullable (for purchase invoices) |
| type | VARCHAR(20) | penjualan, pembelian |
| status | VARCHAR(20) | draft, sent, partially_paid, paid, overdue, cancelled, revised, obsolete |
| subtotal | DECIMAL(15,2) | |
| ppn_amount | DECIMAL(15,2) | |
| total | DECIMAL(15,2) | |
| paid_amount | DECIMAL(15,2) | default 0 |
| due_date | DATE | nullable |
| notes | TEXT | |
| version, parent_id, is_current, is_deleted | — | standard |
| created_at, updated_at | DATETIME | |

#### `invoice_items`
Standard item structure.

#### `payments`
Multi-payment per invoice. Giro lifecycle tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| invoice_id | UUID (FK) | nullable |
| proforma_invoice_id | UUID (FK) | nullable |
| payment_number | VARCHAR(20) | auto: PAY-2026-001 |
| amount | DECIMAL(15,2) | |
| payment_method | VARCHAR(20) | transfer, giro, cek, cash |
| status | VARCHAR(20) | pending, cleared, extended, bad_debt, cancelled |
| payment_date | DATE | nullable |
| due_date | DATE | nullable (for giro/tempo) |
| cleared_date | DATE | nullable |
| bukti_bayar_file | VARCHAR(500) | nullable |
| bukti_giro_cek_file | VARCHAR(500) | nullable |
| giro_bank | VARCHAR(100) | nullable |
| giro_number | VARCHAR(50) | nullable |
| extension_count | INT | default 0 |
| bad_debt_reason | TEXT | nullable |
| notes | TEXT | |
| created_at, updated_at | DATETIME | |

#### `payment_history`
Full audit trail for payment state changes.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| payment_id | UUID (FK → payments) | NOT NULL |
| action | VARCHAR(30) | created, cleared, extended, bad_debt_declared, cancelled |
| old_status | VARCHAR(20) | |
| new_status | VARCHAR(20) | |
| amount_before | DECIMAL(15,2) | nullable |
| amount_after | DECIMAL(15,2) | nullable |
| due_date_before | DATE | nullable |
| due_date_after | DATE | nullable |
| notes | TEXT | nullable |
| user_info | VARCHAR(100) | nullable |
| created_at | DATETIME | |

### System

#### `settings`
Key-value store for application configuration.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| key | VARCHAR(100) | UNIQUE |
| value | TEXT | JSON string |
| updated_at | DATETIME | |

**Default settings keys:**
- `company_name`, `company_address`, `company_phone`, `company_email`, `company_npwp`
- `company_logo` (upload path)
- `bank_name`, `bank_account`, `bank_holder`
- `default_supplier_mode` = "single"
- `default_price_mode` = "include_ppn"
- `pdf_header_text`
- `auth_pin_ttl_minutes` = 5
- `auth_max_attempts` = 5
- `notification_email_enabled` = false
- `notification_email_smtp_host`, `notification_email_smtp_port`, etc.

#### `counters`
Sequential numbering per document type per year.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| type | VARCHAR(30) | penawaran, sales_order, purchase_order, pickup_order, delivery_note, proforma_invoice, invoice, payment |
| year | INT | |
| last_number | INT | default 0 |
| updated_at | DATETIME | |

**Format:** `{PREFIX}-{YYYY}-{000}`
- PEN, SO, PO, PU, SJ, PI, INV, PAY

#### `activity_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| entity_type | VARCHAR(30) | |
| entity_id | UUID | |
| action | VARCHAR(30) | create, update, delete, upload, generate_pdf, status_change, revise |
| description | TEXT | |
| user_info | VARCHAR(100) | nullable |
| created_at | DATETIME | |

---

## Key Design Decisions

### Flexible Document Linking
Semua foreign keys (penawaran_id, sales_order_id, purchase_order_id, dll) adalah **nullable**. Dokumen bisa dibuat dalam urutan apapun — linking dilakukan manual saat diperlukan. Tidak ada enforced workflow sequence.

### Revision System
Setiap dokumen bisa direvisi. Pattern:
1. User click "Revisi" → system duplicate dokumen + items
2. Old: `is_current = false`, `status = obsolete`
3. New: `version += 1`, `parent_id = old.id`, `is_current = true`, `status = draft`
4. `nomor` tetap sama across versions
5. Query current: `WHERE is_current = true`
6. Version history: `WHERE nomor = X ORDER BY version DESC`

### Default Configuration
- **Hybrid approach:** code fallback + settings override
- Default supplier mode: `single`
- Default price mode: `include_ppn`
- User bisa override per-penawaran via dropdown
- Admin bisa change defaults via Pengaturan page

### Payment Tracking (Future)
Payments table supports:
- Multiple payments per invoice (partial payment)
- Giro lifecycle (diterima → cair / gagal → perpanjang / bad debt)
- Due date extensions
- Full audit trail via payment_history
- Status transitions: pending → cleared | extended | bad_debt | cancelled

Payment chain logic (CBD/COD/GBD/GOD/Tempo) akan diimplementasikan sebagai business logic layer, bukan database constraint.

---

## Module Structure

```
erpv2/
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .gitignore
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│
├── app/
│   ├── main.py                   # App entry, middleware, lifespan
│   ├── config.py                 # pydantic-settings
│   ├── database.py               # SQLAlchemy async engine + session
│   │
│   ├── models/                   # SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── base.py               # Base + TimestampMixin + RevisionMixin
│   │   ├── contacts.py
│   │   ├── items.py
│   │   ├── penawaran.py
│   │   ├── sales_order.py
│   │   ├── purchase_order.py
│   │   ├── pickup_order.py
│   │   ├── delivery_note.py
│   │   ├── proforma_invoice.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   └── system.py
│   │
│   ├── schemas/                  # Pydantic
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── contacts.py
│   │   ├── items.py
│   │   ├── penawaran.py
│   │   ├── sales_order.py
│   │   ├── purchase_order.py
│   │   ├── pickup_order.py
│   │   ├── delivery_note.py
│   │   ├── proforma_invoice.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   └── settings.py
│   │
│   ├── routers/                  # REST API (/api/*)
│   │   ├── __init__.py
│   │   ├── contacts.py
│   │   ├── items.py
│   │   ├── penawaran.py
│   │   ├── sales_orders.py
│   │   ├── purchase_orders.py
│   │   ├── pickup_orders.py
│   │   ├── delivery_notes.py
│   │   ├── proforma_invoices.py
│   │   ├── invoices.py
│   │   ├── payments.py
│   │   ├── uploads.py
│   │   ├── pdf.py
│   │   └── settings.py
│   │
│   ├── htmx/                     # HTMX pages (/app/*)
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── penawaran.py
│   │   ├── sales_orders.py
│   │   ├── purchase_orders.py
│   │   ├── pickup_orders.py
│   │   ├── delivery_notes.py
│   │   ├── proforma_invoices.py
│   │   ├── invoices.py
│   │   ├── items.py
│   │   ├── contacts.py
│   │   ├── shipping.py
│   │   ├── finance.py
│   │   └── settings.py
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── counter.py            # Sequential numbering
│   │   ├── revision.py           # Document revision
│   │   ├── calc.py               # Penawaran calculations + validation
│   │   ├── pdf.py                # WeasyPrint rendering
│   │   └── upload.py             # File validation + storage
│   │
│   ├── templates/                # Jinja2
│   │   ├── shared/
│   │   │   ├── _base.html
│   │   │   ├── _sidebar.html
│   │   │   ├── _table.html
│   │   │   ├── _form.html
│   │   │   ├── _modal.html
│   │   │   └── _upload.html
│   │   ├── penawaran/
│   │   ├── penjualan/
│   │   ├── purchase_orders/
│   │   ├── pickup_orders/
│   │   ├── delivery_notes/
│   │   ├── proforma_invoices/
│   │   ├── invoices/
│   │   ├── items/
│   │   ├── contacts/
│   │   ├── shipping/
│   │   ├── finance/
│   │   ├── settings/
│   │   ├── dashboard/
│   │   └── print/
│   │       ├── penawaran.html
│   │       ├── sales_order.html
│   │       ├── purchase_order.html
│   │       ├── pickup_order.html
│   │       ├── delivery_note.html
│   │       ├── proforma_invoice.html
│   │       └── invoice.html
│   │
│   └── static/
│       ├── css/app.css
│       └── js/app.js
│
├── data/                         # Docker volume (gitignored)
│   ├── rai_erp.db
│   └── uploads/
│
└── tests/
    ├── conftest.py
    ├── test_models/
    ├── test_routers/
    └── test_services/
```

---

## API Endpoints

### Standard CRUD Pattern (per document type)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/{module}` | List (filter, search, paginate, sort) |
| GET | `/api/{module}/{id}` | Detail + related data |
| POST | `/api/{module}` | Create (auto-generate nomor) |
| PATCH | `/api/{module}/{id}` | Update |
| DELETE | `/api/{module}/{id}` | Soft delete |
| POST | `/api/{module}/{id}/revise` | Create revision |
| PATCH | `/api/{module}/{id}/status` | Update status |

### Modules with standard CRUD:
- `/api/contacts` (+ GET/POST `/api/contacts/{id}/top-history`)
- `/api/items`
- `/api/penawaran` (+ POST `/{id}/lock`, POST `/{id}/convert-to-so`, GET `/{id}/versions`)
- `/api/sales-orders`
- `/api/purchase-orders`
- `/api/pickup-orders`
- `/api/delivery-notes`
- `/api/proforma-invoices`
- `/api/invoices`
- `/api/payments`

### Special Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/uploads` | Upload file (multipart: file, module, entity_id, field) |
| GET | `/api/uploads/{path}` | Serve uploaded file |
| DELETE | `/api/uploads/{path}` | Delete uploaded file |
| GET | `/api/pdf/{type}/{id}` | Generate PDF (inline display) |
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings` | Update settings (bulk) |
| POST | `/api/settings/logo` | Upload company logo |

### HTMX Routes (/app/*)

| Path | Description |
|------|-------------|
| `/app/` | Dashboard |
| `/app/penawaran` | Penawaran list + CRUD |
| `/app/penawaran/new` | Builder (Alpine.js live calc) |
| `/app/penawaran/{id}` | Detail |
| `/app/penawaran/{id}/edit` | Edit builder |
| `/app/penjualan` | Sales Orders list |
| `/app/purchase-order` | Purchase Orders list |
| `/app/pickup-order` | Pickup Orders list |
| `/app/surat-jalan` | Delivery Notes list |
| `/app/proforma` | Proforma Invoices list |
| `/app/invoice` | Invoices list |
| `/app/items` | Items master data |
| `/app/kontak` | Contacts (all types) |
| `/app/shipping` | Shipping dashboard |
| `/app/finance` | Finance dashboard |
| `/app/pengaturan` | Settings |

---

## Penawaran Calculation Logic

### Input Fields (per item row)
```
Nama Barang | Qty | Berat/Unit (Kg) [beli]
HPP/Unit | Total Beli
Harga Jual/Unit | Total Jual
[Different Scale] | Berat/Unit (Kg) [jual] ← only if different scale ON
```

### Formulas

```python
# Total Beli
if berat_beli_per_unit > 0:
    total_beli = quantity × berat_beli_per_unit × hpp_per_unit
else:
    total_beli = quantity × hpp_per_unit

# Total Jual
berat_jual = berat_jual_per_unit if different_scale else berat_beli_per_unit

if berat_jual > 0:
    total_jual = quantity × berat_jual × harga_jual_per_unit
else:
    total_jual = quantity × harga_jual_per_unit

# PPN
if price_mode == "include_ppn":
    # Total jual sudah include PPN
    ppn_amount = (total_jual / 1.11) * 0.11
    grand_total = total_jual
else:
    # Exclude PPN — tambah PPN 11%
    ppn_amount = total_jual * 0.11
    grand_total = total_jual + ppn_amount
```

### Live Calc (Alpine.js)
- Real-time calculation di browser saat user input
- Server-side validation on save (recalculate + compare)
- Alpine.js component: `penawaranBuilder`

---

## File Upload

### Storage
- **Local filesystem** dalam Docker volume
- Path: `data/uploads/{module}/{entity_id}/{field}-{timestamp}.{ext}`
- Example: `data/uploads/purchase_orders/uuid-123/bukti-po-20260705-143022.pdf`

### Upload Component (_upload.html)
- Drag & drop + click to browse
- File type validation (PDF, JPEG, PNG, WebP)
- Size limit: 5MB per file
- Progress bar (Alpine.js)
- Preview (image: thumbnail, PDF: icon + filename)
- Replace button: compact `[G]` inline
- Delete button with confirmation

### Upload Flow
1. POST `/api/uploads` (multipart: file, module, entity_id, field)
2. Validate type + size
3. Save to disk
4. Return `{ path, filename, size, content_type }`
5. Frontend updates entity with returned path

### Upload Fields Per Document
| Document | Fields |
|----------|--------|
| Purchase Order | bukti_po |
| Proforma Invoice | bukti_bayar, bukti_giro_cek |
| Invoice | bukti_bayar, bukti_giro_cek |
| Delivery Note | bukti_kirim |

---

## Sequential Numbering

```
PEN-2026-001  (Penawaran)
SO-2026-001   (Sales Order)
PO-2026-001   (Purchase Order)
PU-2026-001   (Pickup Order)
SJ-2026-001   (Surat Jalan / Delivery Note)
PI-2026-001   (Proforma Invoice)
INV-2026-001  (Invoice)
PAY-2026-001  (Payment)
```

Reset per year. Atomic increment via transaction.

---

## UI/UX Layout Rules

- **Wrapper:** `space-y-6`
- **Header:** flex, font-display text-2xl, actions right-aligned
- **Cards:** grid responsive (1 col mobile, 2 sm, 4 lg)
- **Toolbar:** flex gap-2, search input (max-w-md), filter selects, page size
- **Table:** table-fixed, fixed-width columns, sortable headers
- **Mobile:** card list (md:hidden)
- **Pagination:** prev/next
- **Empty state:** min-h-[35vh] + icon + message
- **shadcn-inspired components** (TailwindCSS only)
- **toast.error()** — never alert()
- **Secondary actions** (Ganti/Replace) below primary info, compact `[G]` format

---

## PDF Generation

- **Engine:** WeasyPrint
- **Templates:** `templates/print/{type}.html`
- **CSS:** `@page { size: A4; margin: 15mm; }` — full CSS Paged Media support
- **Header:** logo (h-16) LEFT of company info (flex items-center gap-4)
- **Labels:** Generic ("SURAT JALAN", not "SURAT JALAN CLIENT")
- **Endpoint:** `GET /api/pdf/{type}/{id}` → inline PDF
- **Print page:** new tab, controls = Cetak + Simpan only

---

## Sidebar Navigation

```
📊 Dashboard
───────────────
Dokumen
📋 Penawaran
🛒 Purchase Order
📦 Sales Order
🚛 Pickup Order
📝 Surat Jalan
💰 Proforma Invoice
🧾 Invoice
───────────────
Master
📦 Items
🚢 Shipping
💳 Finance
───────────────
System
👤 Kontak
⚙️ Pengaturan
```

---

## Settings Page

Tabs:
1. **Perusahaan** — name, address, phone, email, NPWP, logo, bank info
2. **Aplikasi** — default modes (supplier, price), app name
3. **PDF** — header text, margin, paper size
4. **Notifikasi** — email SMTP config, enable/disable

---

## Development Workflow

```bash
# Start dev
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Edit code → auto-reload (uvicorn --reload)
# SQLite + uploads persist di ./data/ (host mounted)

# View logs
docker-compose logs -f

# Database migration (after model changes)
# Alembic auto-runs on app startup

# Seed/reset sample data
docker-compose exec rai-erp python -m app.seed --reset
```

---

## Docker Config

### Dockerfile
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data/uploads
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: "3.8"
services:
  rai-erp:
    build: .
    container_name: rai-erp
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - DATA_DIR=/data
      - TIMEZONE=Asia/Jakarta
      - DEV_MODE=true
    restart: unless-stopped
```

### docker-compose.dev.yml
```yaml
version: "3.8"
services:
  rai-erp:
    container_name: rai-erp-dev
    volumes:
      - ./app:/app/app
      - ./data:/data
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
