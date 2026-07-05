# RAI ERP v2 — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation + Penawaran as proof-of-concept document type — enough to demonstrate the full stack (Docker, FastAPI, HTMX, Alpine.js, SQLite, PDF, uploads).

**Architecture:** Single FastAPI container with SQLAlchemy/SQLite, HTMX+Alpine.js frontend, WeasyPrint PDF. Phase 1 proves the pattern; Phase 2 adds remaining document types.

**Tech Stack:** Python 3.11, FastAPI 0.115, SQLAlchemy 2.0 (async), aiosqlite, Jinja2, HTMX 2.0, Alpine.js 3.14, TailwindCSS 3.4 (CDN), WeasyPrint 62, Alembic.

## Global Constraints

- Locale: Bahasa Indonesia UI, Rp currency, WIB timezone (Asia/Jakarta)
- All document FKs nullable (flexible linking)
- All documents have version/parent_id/is_current (revision system)
- Sequential numbering: {PREFIX}-{YYYY}-{000}, reset yearly
- Soft delete (is_deleted flag), never hard delete
- File uploads: PDF/JPEG/PNG/WebP, max 5MB, stored in ./data/uploads/
- No alert() — use toast notifications only
- No React — HTMX + Alpine.js only
- TailwindCSS via CDN — no build step
- shadcn-inspired components, professional layout

## Phase 2 (Not in this plan)
Sales Order, Purchase Order, Pickup Order, Delivery Note, Proforma Invoice, Invoice, Payments, Shipping dashboard, Finance dashboard.

---

### Task 1: Docker + Project Scaffold

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `docker-compose.dev.yml`
- Create: `requirements.txt`
- Create: `.env`
- Create: `.gitignore` (already exists)
- Create: `app/__init__.py`
- Create: `app/main.py` (stub)
- Create: `app/config.py`

**Interfaces:**
- Produces: running container at localhost:8000, `/health` endpoint returns `{"status": "ok"}`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.*
uvicorn[standard]==0.30.*
sqlalchemy[asyncio]==2.0.*
aiosqlite==0.20.*
alembic==1.13.*
jinja2==3.1.*
pydantic==2.9.*
pydantic-settings==2.5.*
python-multipart==0.0.9
weasyprint==62.*
python-dateutil==2.9.*
httpx==0.27.*
```

- [ ] **Step 2: Create .env**

```
DATA_DIR=./data
TIMEZONE=Asia/Jakarta
DEV_MODE=true
APP_VERSION=0.1.0
```

- [ ] **Step 3: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: str = "./data"
    timezone: str = "Asia/Jakarta"
    dev_mode: bool = False
    app_version: str = "0.1.0"

    # Defaults (can be overridden via settings table)
    default_supplier_mode: str = "single"
    default_price_mode: str = "include_ppn"

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 4: Create app/main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure data dirs exist
    import os
    os.makedirs(f"{settings.data_dir}/uploads", exist_ok=True)
    yield
    # Shutdown: nothing


app = FastAPI(
    title="RAI ERP",
    version=settings.app_version,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
```

- [ ] **Step 5: Create app/__init__.py** (empty file)

```python
```

- [ ] **Step 6: Create minimal static files**

Create `app/static/css/app.css`:
```css
/* Custom styles on top of Tailwind CDN */
.nav-link {
    @apply flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors;
}
.nav-link.active {
    @apply bg-blue-50 text-blue-700 font-medium;
}
```

Create `app/static/js/app.js`:
```javascript
// RAI ERP — Alpine.js components & utilities

function formatRupiah(value) {
    if (!value || isNaN(value)) return 'Rp 0';
    return 'Rp ' + Math.round(value).toLocaleString('id-ID');
}

function formatNumber(value) {
    if (!value || isNaN(value)) return '0';
    return Number(value).toLocaleString('id-ID');
}

// Toast notification system
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    toast.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg mb-2 transition-all duration-300 transform translate-x-0`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
```

- [ ] **Step 7: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

# WeasyPrint system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/uploads

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: Create docker-compose.yml**

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

- [ ] **Step 9: Create docker-compose.dev.yml**

```yaml
version: "3.8"

services:
  rai-erp:
    container_name: rai-erp-dev
    volumes:
      - ./app:/app/app
      - ./data:/data
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 10: Build and verify**

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Expected: Container starts, image builds successfully.

Then verify:
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "feat: docker scaffold + fastapi app entry with health check"
```

---

### Task 2: Database + SQLAlchemy Setup

**Files:**
- Create: `app/database.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/.gitkeep`
- Modify: `app/main.py` (add DB init to lifespan)

**Interfaces:**
- Produces: `get_db()` dependency for FastAPI, `async_session_factory`, `engine`
- Consumes: `Settings.data_dir` from Task 1

- [ ] **Step 1: Create app/database.py**

```python
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.data_dir}/rai_erp.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.dev_mode,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = sqlite+aiosqlite:///./data/rai_erp.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Create alembic/env.py**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.database import Base
from app.config import settings

# Import all models so Alembic sees them
from app.models import *  # noqa: F401, F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override URL from env
config.set_main_option(
    "sqlalchemy.url",
    f"sqlite+aiosqlite:///{settings.data_dir}/rai_erp.db",
)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create alembic/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 5: Create alembic/versions/.gitkeep** (empty file)

- [ ] **Step 6: Create app/models/__init__.py**

```python
from app.models.base import Base, TimestampMixin, RevisionMixin, SoftDeleteMixin
from app.models.system import Settings, Counter, ActivityLog
from app.models.contacts import Contact, ContactTopHistory
from app.models.items import Item

__all__ = [
    "Base", "TimestampMixin", "RevisionMixin", "SoftDeleteMixin",
    "Settings", "Counter", "ActivityLog",
    "Contact", "ContactTopHistory",
    "Item",
]
```

- [ ] **Step 7: Update app/main.py lifespan to create tables on first run**

Replace the lifespan function:
```python
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    os.makedirs(f"{settings.data_dir}/uploads", exist_ok=True)
    # Auto-create tables (Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
```

- [ ] **Step 8: Build and verify DB creation**

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Then:
```bash
ls -la data/rai_erp.db
```

Expected: SQLite file exists (created after first request hits the app).

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"0.1.0"}` — and `data/rai_erp.db` now exists.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: SQLAlchemy async setup + Alembic migrations"
```

---

### Task 3: Base Models + Mixins

**Files:**
- Create: `app/models/base.py`

**Interfaces:**
- Produces: `TimestampMixin`, `RevisionMixin`, `SoftDeleteMixin` — used by all document models

- [ ] **Step 1: Create app/models/base.py**

```python
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase

WIB = timezone(timedelta(hours=7))


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(WIB), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(WIB),
        onupdate=lambda: datetime.now(WIB),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)


class RevisionMixin:
    version = Column(Integer, default=1, nullable=False)
    parent_id = Column(String(36), nullable=True)  # UUID as string
    is_current = Column(Boolean, default=True, nullable=False)


def new_id() -> str:
    return str(uuid.uuid4())
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: base model mixins (Timestamp, SoftDelete, Revision)"
```

---

### Task 4: System Models (Settings, Counter, ActivityLog)

**Files:**
- Create: `app/models/system.py`
- Create: `app/services/counter.py`
- Create: `app/services/__init__.py`

**Interfaces:**
- Produces: `Settings` model, `Counter` model, `ActivityLog` model
- Produces: `get_next_number(db, doc_type)` — returns string like "PEN-2026-001"
- Produces: `get_setting(db, key, fallback)` — returns setting value or fallback
- Consumes: `Base`, `TimestampMixin` from Task 3

- [ ] **Step 1: Create app/services/__init__.py** (empty)

- [ ] **Step 2: Create app/models/system.py**

```python
import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from app.models.base import Base, TimestampMixin, new_id


class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=new_id)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)  # JSON string


class Counter(Base):
    __tablename__ = "counters"
    __table_args__ = (UniqueConstraint("type", "year"),)

    id = Column(String(36), primary_key=True, default=new_id)
    type = Column(String(30), nullable=False)
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=new_id)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(36), nullable=False)
    action = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    user_info = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False)
```

- [ ] **Step 3: Create app/services/counter.py**

```python
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
```

- [ ] **Step 4: Create helper for reading settings**

Add to `app/services/settings.py`:

```python
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import Settings


async def get_setting(db: AsyncSession, key: str, fallback=None):
    result = await db.execute(select(Settings).where(Settings.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return fallback
    try:
        return json.loads(row.value)
    except (json.JSONDecodeError, TypeError):
        return row.value


async def set_setting(db: AsyncSession, key: str, value):
    result = await db.execute(select(Settings).where(Settings.key == key))
    row = result.scalar_one_or_none()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    if row is None:
        db.add(Settings(key=key, value=serialized))
    else:
        row.value = serialized
    await db.flush()


async def get_all_settings(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings))
    rows = result.scalars().all()
    settings = {}
    for row in rows:
        try:
            settings[row.key] = json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            settings[row.key] = row.value
    return settings
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: system models (Settings, Counter, ActivityLog) + counter service"
```

---

### Task 5: Contacts Model + API + HTMX

**Files:**
- Create: `app/models/contacts.py`
- Create: `app/schemas/contacts.py`
- Create: `app/routers/contacts.py`
- Create: `app/htmx/contacts.py`
- Create: `app/schemas/common.py`
- Create: `app/templates/contacts/index.html`
- Create: `app/templates/contacts/_rows.html`
- Create: `app/templates/contacts/_form.html`
- Create: `app/templates/contacts/detail.html`
- Modify: `app/main.py` (register routers)
- Modify: `app/models/__init__.py` (add imports)

**Interfaces:**
- Consumes: `Base`, `TimestampMixin`, `SoftDeleteMixin` from Task 3
- Produces: Contact CRUD API at `/api/contacts`
- Produces: Contact HTMX pages at `/app/kontak`
- Produces: `ContactTopHistory` model

- [ ] **Step 1: Create app/schemas/common.py**

```python
from pydantic import BaseModel
from typing import Optional


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20
    search: Optional[str] = None
    sort: str = "created_at"
    order: str = "desc"


class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    per_page: int
```

- [ ] **Step 2: Create app/models/contacts.py**

```python
from sqlalchemy import Boolean, Column, Date, Integer, String, Text, ForeignKey
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, new_id


class Contact(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=new_id)
    type = Column(String(20), nullable=False)  # supplier, customer, expedition, marketing
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    npwp = Column(String(50), nullable=True)
    tax_info = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class ContactTopHistory(Base):
    __tablename__ = "contact_top_history"

    id = Column(String(36), primary_key=True, default=new_id)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False)
    top_type = Column(String(20), nullable=False)  # CBD, COD, GBD, GOD, Tempo
    tempo_days = Column(Integer, nullable=True)
    effective_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(Date, nullable=True)
```

- [ ] **Step 3: Create app/schemas/contacts.py**

```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class ContactCreate(BaseModel):
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: str
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    npwp: Optional[str] = None
    tax_info: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopHistoryCreate(BaseModel):
    top_type: str
    tempo_days: Optional[int] = None
    effective_date: date
    notes: Optional[str] = None


class TopHistoryResponse(BaseModel):
    id: str
    contact_id: str
    top_type: str
    tempo_days: Optional[int] = None
    effective_date: date
    notes: Optional[str] = None
    created_at: Optional[date] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create app/routers/contacts.py**

```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact, ContactTopHistory
from app.schemas.contacts import (
    ContactCreate, ContactUpdate, ContactResponse,
    TopHistoryCreate, TopHistoryResponse,
)

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("")
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)

    if type:
        query = query.where(Contact.type == type)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(Contact.name.ilike(search_term), Contact.email.ilike(search_term))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Sort + paginate
    sort_col = getattr(Contact, sort, Contact.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    contacts = result.scalars().all()

    return {
        "data": [ContactResponse.model_validate(c) for c in contacts],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{contact_id}")
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    return ContactResponse.model_validate(contact)


@router.post("", status_code=201)
async def create_contact(body: ContactCreate, db: AsyncSession = Depends(get_db)):
    contact = Contact(**body.model_dump())
    db.add(contact)
    await db.flush()
    return ContactResponse.model_validate(contact)


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: str, body: ContactUpdate, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    await db.flush()
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    contact.is_deleted = True
    await db.flush()
    return {"ok": True}


@router.get("/{contact_id}/top-history")
async def get_top_history(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContactTopHistory)
        .where(ContactTopHistory.contact_id == contact_id)
        .order_by(ContactTopHistory.effective_date.desc())
    )
    history = result.scalars().all()
    return [TopHistoryResponse.model_validate(h) for h in history]


@router.post("/{contact_id}/top-history", status_code=201)
async def add_top_history(
    contact_id: str, body: TopHistoryCreate, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        raise HTTPException(404, "Contact not found")
    history = ContactTopHistory(contact_id=contact_id, **body.model_dump())
    db.add(history)
    await db.flush()
    return TopHistoryResponse.model_validate(history)
```

- [ ] **Step 5: Create app/htmx/__init__.py** (empty)

- [ ] **Step 6: Create app/htmx/contacts.py**

```python
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contacts import Contact

router = APIRouter(prefix="/app/kontak", tags=["htmx-contacts"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def contacts_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)
    if type:
        query = query.where(Contact.type == type)
    if search:
        query = query.where(
            or_(Contact.name.ilike(f"%{search}%"), Contact.email.ilike(f"%{search}%"))
        )
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Contact.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return templates.TemplateResponse("contacts/index.html", {
        "request": request,
        "contacts": contacts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "search": search or "",
        "type_filter": type or "",
        "active": "kontak",
    })


@router.get("/rows")
async def contacts_rows(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Contact).where(Contact.is_deleted == False)
    if type:
        query = query.where(Contact.type == type)
    if search:
        query = query.where(
            or_(Contact.name.ilike(f"%{search}%"), Contact.email.ilike(f"%{search}%"))
        )
    query = query.order_by(Contact.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return templates.TemplateResponse("contacts/_rows.html", {
        "request": request,
        "contacts": contacts,
    })


@router.get("/form")
async def contacts_create_form(request: Request):
    return templates.TemplateResponse("contacts/_form.html", {
        "request": request,
        "contact": None,
    })


@router.get("/{contact_id}/form")
async def contacts_edit_form(
    request: Request, contact_id: str, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Contact tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("contacts/_form.html", {
        "request": request,
        "contact": contact,
    })


@router.get("/{contact_id}")
async def contacts_detail(
    request: Request, contact_id: str, db: AsyncSession = Depends(get_db)
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.is_deleted:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<p>Contact tidak ditemukan</p>", status_code=404)
    return templates.TemplateResponse("contacts/detail.html", {
        "request": request,
        "contact": contact,
        "active": "kontak",
    })
```

- [ ] **Step 7: Create contact templates**

Create `app/templates/contacts/index.html`:
```html
{% extends "shared/_base.html" %}

{% block title %}Kontak — RAI ERP{% endblock %}
{% block page_title %}Kontak{% endblock %}

{% block page_actions %}
<button hx-get="/app/kontak/form" hx-target="#modal-content" hx-swap="innerHTML"
        @click="$dispatch('open-modal')"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
    + Tambah Kontak
</button>
{% endblock %}

{% block content %}
<div class="space-y-4">
    <!-- Toolbar -->
    <div class="flex gap-2 items-center">
        <input type="text" placeholder="Cari kontak..."
               name="search" value="{{ search }}"
               hx-get="/app/kontak/rows" hx-target="#contact-rows" hx-trigger="keyup changed delay:300ms"
               hx-include="[name='type']"
               class="px-3 py-2 border rounded-lg text-sm max-w-md w-full">
        <select name="type"
                hx-get="/app/kontak/rows" hx-target="#contact-rows" hx-trigger="change"
                hx-include="[name='search']"
                class="px-3 py-2 border rounded-lg text-sm">
            <option value="">Semua Tipe</option>
            <option value="supplier" {% if type_filter == 'supplier' %}selected{% endif %}>Supplier</option>
            <option value="customer" {% if type_filter == 'customer' %}selected{% endif %}>Customer</option>
            <option value="expedition" {% if type_filter == 'expedition' %}selected{% endif %}>Expedition</option>
            <option value="marketing" {% if type_filter == 'marketing' %}selected{% endif %}>Marketing</option>
        </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-lg border overflow-hidden">
        <table class="w-full table-fixed">
            <thead class="bg-gray-50 border-b">
                <tr>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase w-16">Tipe</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Nama</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">Email</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">Telepon</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase w-24">Aksi</th>
                </tr>
            </thead>
            <tbody id="contact-rows">
                {% include "contacts/_rows.html" %}
            </tbody>
        </table>
    </div>

    {% if total == 0 %}
    <div class="flex flex-col items-center justify-center min-h-[35vh] text-gray-400">
        <svg class="w-16 h-16 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        <p class="text-sm">Belum ada kontak</p>
    </div>
    {% endif %}
</div>

<!-- Modal -->
<div x-data="{ open: false }"
     @open-modal.window="open = true"
     @close-modal.window="open = false"
     x-show="open" x-cloak
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6" @click.outside="open = false">
        <div id="modal-content"></div>
    </div>
</div>
{% endblock %}
```

Create `app/templates/contacts/_rows.html`:
```html
{% for c in contacts %}
<tr class="border-b hover:bg-gray-50 cursor-pointer"
    hx-get="/app/kontak/{{ c.id }}" hx-target="body" hx-push-url="true">
    <td class="px-4 py-3">
        <span class="inline-block px-2 py-0.5 text-xs rounded-full
            {% if c.type == 'supplier' %}bg-purple-100 text-purple-700
            {% elif c.type == 'customer' %}bg-blue-100 text-blue-700
            {% elif c.type == 'expedition' %}bg-green-100 text-green-700
            {% else %}bg-gray-100 text-gray-700{% endif %}">
            {{ c.type }}
        </span>
    </td>
    <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ c.name }}</td>
    <td class="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{{ c.email or '-' }}</td>
    <td class="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{{ c.phone or '-' }}</td>
    <td class="px-4 py-3">
        <button hx-get="/app/kontak/{{ c.id }}/form" hx-target="#modal-content" hx-swap="innerHTML"
                @click.stop="$dispatch('open-modal')"
                class="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
    </td>
</tr>
{% endfor %}
```

Create `app/templates/contacts/_form.html`:
```html
<form {% if contact %}
      hx-patch="/api/contacts/{{ contact.id }}"
      {% else %}
      hx-post="/api/contacts"
      {% endif %}
      hx-target="body"
      @submit.prevent="$event.target.dispatchEvent(new Event('submit'))"
      class="space-y-4">
    <h3 class="text-lg font-semibold">
        {% if contact %}Edit Kontak{% else %}Tambah Kontak{% endif %}
    </h3>

    <div>
        <label class="block text-sm font-medium mb-1">Tipe</label>
        <select name="type" required class="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="supplier" {% if contact and contact.type == 'supplier' %}selected{% endif %}>Supplier</option>
            <option value="customer" {% if contact and contact.type == 'customer' %}selected{% endif %}>Customer</option>
            <option value="expedition" {% if contact and contact.type == 'expedition' %}selected{% endif %}>Expedition</option>
            <option value="marketing" {% if contact and contact.type == 'marketing' %}selected{% endif %}>Marketing</option>
        </select>
    </div>

    <div>
        <label class="block text-sm font-medium mb-1">Nama</label>
        <input type="text" name="name" required value="{{ contact.name if contact else '' }}"
               class="w-full border rounded-lg px-3 py-2 text-sm">
    </div>

    <div class="grid grid-cols-2 gap-3">
        <div>
            <label class="block text-sm font-medium mb-1">Email</label>
            <input type="email" name="email" value="{{ contact.email if contact else '' }}"
                   class="w-full border rounded-lg px-3 py-2 text-sm">
        </div>
        <div>
            <label class="block text-sm font-medium mb-1">Telepon</label>
            <input type="text" name="phone" value="{{ contact.phone if contact else '' }}"
                   class="w-full border rounded-lg px-3 py-2 text-sm">
        </div>
    </div>

    <div>
        <label class="block text-sm font-medium mb-1">Alamat</label>
        <textarea name="address" rows="2" class="w-full border rounded-lg px-3 py-2 text-sm">{{ contact.address if contact else '' }}</textarea>
    </div>

    <div class="grid grid-cols-2 gap-3">
        <div>
            <label class="block text-sm font-medium mb-1">NPWP</label>
            <input type="text" name="npwp" value="{{ contact.npwp if contact else '' }}"
                   class="w-full border rounded-lg px-3 py-2 text-sm">
        </div>
        <div>
            <label class="block text-sm font-medium mb-1">Catatan</label>
            <input type="text" name="notes" value="{{ contact.notes if contact else '' }}"
                   class="w-full border rounded-lg px-3 py-2 text-sm">
        </div>
    </div>

    <div class="flex gap-2 justify-end pt-2">
        <button type="button" @click="$dispatch('close-modal')"
                class="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            Batal
        </button>
        <button type="submit"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            {% if contact %}Simpan Perubahan{% else %}Tambah{% endif %}
        </button>
    </div>
</form>
```

Create `app/templates/contacts/detail.html`:
```html
{% extends "shared/_base.html" %}

{% block title %}{{ contact.name }} — RAI ERP{% endblock %}
{% block page_title %}
<div class="flex items-center gap-3">
    <a href="/app/kontak" class="text-gray-400 hover:text-gray-600">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
    </a>
    {{ contact.name }}
</div>
{% endblock %}

{% block page_actions %}
<button hx-get="/app/kontak/{{ contact.id }}/form" hx-target="#modal-content" hx-swap="innerHTML"
        @click="$dispatch('open-modal')"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
    Edit
</button>
{% endblock %}

{% block content %}
<div class="space-y-6">
    <div class="bg-white rounded-lg border p-6">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
                <div class="text-xs text-gray-500 uppercase mb-1">Tipe</div>
                <span class="inline-block px-2 py-0.5 text-xs rounded-full
                    {% if contact.type == 'supplier' %}bg-purple-100 text-purple-700
                    {% elif contact.type == 'customer' %}bg-blue-100 text-blue-700
                    {% elif contact.type == 'expedition' %}bg-green-100 text-green-700
                    {% else %}bg-gray-100 text-gray-700{% endif %}">
                    {{ contact.type }}
                </span>
            </div>
            <div>
                <div class="text-xs text-gray-500 uppercase mb-1">Email</div>
                <div class="text-sm">{{ contact.email or '-' }}</div>
            </div>
            <div>
                <div class="text-xs text-gray-500 uppercase mb-1">Telepon</div>
                <div class="text-sm">{{ contact.phone or '-' }}</div>
            </div>
            <div class="col-span-2 md:col-span-3">
                <div class="text-xs text-gray-500 uppercase mb-1">Alamat</div>
                <div class="text-sm">{{ contact.address or '-' }}</div>
            </div>
            <div>
                <div class="text-xs text-gray-500 uppercase mb-1">NPWP</div>
                <div class="text-sm">{{ contact.npwp or '-' }}</div>
            </div>
        </div>
    </div>
</div>

<!-- Modal for edit -->
<div x-data="{ open: false }"
     @open-modal.window="open = true"
     @close-modal.window="open = false"
     x-show="open" x-cloak
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6" @click.outside="open = false">
        <div id="modal-content"></div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 8: Register routers in app/main.py**

Add to main.py after app creation:
```python
from app.routers import contacts as contacts_api
from app.htmx import contacts as contacts_htmx

app.include_router(contacts_api.router)
app.include_router(contacts_htmx.router)
```

- [ ] **Step 9: Verify**

Restart container, visit `http://localhost:8000/app/kontak` — should see empty contacts page with sidebar.

Test API:
```bash
curl -X POST http://localhost:8000/api/contacts \
  -H "Content-Type: application/json" \
  -d '{"type":"supplier","name":"PT Test Supplier","email":"test@test.com"}'
```

Expected: JSON response with created contact.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: contacts CRUD (API + HTMX pages)"
```

---

### Task 6: Items Model + API + HTMX

**Files:**
- Create: `app/models/items.py`
- Create: `app/schemas/items.py`
- Create: `app/routers/items.py`
- Create: `app/htmx/items.py`
- Create: `app/templates/items/index.html`
- Create: `app/templates/items/_rows.html`
- Create: `app/templates/items/_form.html`
- Modify: `app/main.py` (register routers)

**Interfaces:**
- Produces: Item CRUD API at `/api/items`
- Produces: Item HTMX pages at `/app/items`
- Pattern: identical to contacts (Task 5) — copy, adjust fields

- [ ] **Step 1: Create app/models/items.py**

```python
from sqlalchemy import Column, Numeric, String, Text
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, new_id


class Item(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=new_id)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=True, unique=True)
    unit = Column(String(20), default="pcs", nullable=False)
    default_hpp = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
```

- [ ] **Step 2: Create app/schemas/items.py**

```python
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    unit: str = "pcs"
    default_hpp: Decimal = Decimal("0")
    notes: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    default_hpp: Optional[Decimal] = None
    notes: Optional[str] = None


class ItemResponse(BaseModel):
    id: str
    name: str
    sku: Optional[str] = None
    unit: str
    default_hpp: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Create app/routers/items.py**

Follow same pattern as contacts router (Task 5, Step 4) — list with search/sort/paginate, get, post, patch, delete (soft).

- [ ] **Step 4: Create app/htmx/items.py**

Follow same pattern as contacts HTMX (Task 5, Step 6).

- [ ] **Step 5: Create item templates**

Follow same pattern as contacts templates — index.html, _rows.html, _form.html.
Columns: SKU, Nama, Unit, HPP Default.

- [ ] **Step 6: Register routers in main.py, verify, commit**

```bash
git add -A
git commit -m "feat: items CRUD (API + HTMX pages)"
```

---

### Task 7: Base Template + Sidebar

**Files:**
- Create: `app/templates/shared/_base.html`
- Create: `app/templates/shared/_sidebar.html`

**Interfaces:**
- Produces: base layout used by all HTMX pages
- Blocks: `title`, `page_title`, `page_actions`, `content`, `scripts`

- [ ] **Step 1: Create _base.html** (as defined in spec Section 10)

- [ ] **Step 2: Create _sidebar.html** (as defined in spec Section 10)

- [ ] **Step 3: Update contact/item templates to extend _base.html** (already done in Task 5-6)

- [ ] **Step 4: Verify sidebar renders correctly at /app/kontak**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: base template + sidebar layout"
```

---

### Task 8: Penawaran Model + API

**Files:**
- Create: `app/models/penawaran.py`
- Create: `app/schemas/penawaran.py`
- Create: `app/routers/penawaran.py`
- Create: `app/services/revision.py`
- Create: `app/services/calc.py`
- Modify: `app/main.py`

**Interfaces:**
- Consumes: `get_next_number()` from counter service
- Consumes: `Base`, `TimestampMixin`, `SoftDeleteMixin`, `RevisionMixin`
- Produces: Penawaran CRUD API at `/api/penawaran`
- Produces: `create_revision(db, model_class, items_model, doc_id)` — generic revision
- Produces: `validate_penawaran_calc(items, price_mode)` — server-side validation

- [ ] **Step 1: Create app/models/penawaran.py**

```python
from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text, ForeignKey
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, RevisionMixin, new_id


class Penawaran(TimestampMixin, SoftDeleteMixin, RevisionMixin, Base):
    __tablename__ = "penawaran"

    id = Column(String(36), primary_key=True, default=new_id)
    nomor = Column(String(20), nullable=False)
    customer_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    supplier_mode = Column(String(10), default="single", nullable=False)
    price_mode = Column(String(20), default="include_ppn", nullable=False)
    terms_of_payment = Column(Text, nullable=True)
    terms_of_delivery = Column(Text, nullable=True)
    validity_days = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    total_beli = Column(Numeric(15, 2), default=0, nullable=False)
    total_jual = Column(Numeric(15, 2), default=0, nullable=False)
    ppn_amount = Column(Numeric(15, 2), default=0, nullable=False)
    grand_total = Column(Numeric(15, 2), default=0, nullable=False)


class PenawaranItem(Base):
    __tablename__ = "penawaran_items"

    id = Column(String(36), primary_key=True, default=new_id)
    penawaran_id = Column(String(36), ForeignKey("penawaran.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    supplier_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    berat_beli_per_unit = Column(Numeric(10, 4), default=0, nullable=False)
    hpp_per_unit = Column(Numeric(15, 2), default=0, nullable=False)
    total_beli = Column(Numeric(15, 2), default=0, nullable=False)
    harga_jual_per_unit = Column(Numeric(15, 2), default=0, nullable=False)
    total_jual = Column(Numeric(15, 2), default=0, nullable=False)
    different_scale = Column(Boolean, default=False, nullable=False)
    berat_jual_per_unit = Column(Numeric(10, 4), nullable=True)
    urutan = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
```

- [ ] **Step 2: Create app/services/calc.py**

```python
from decimal import Decimal


def calc_row_total_beli(quantity, berat_beli_per_unit, hpp_per_unit):
    if berat_beli_per_unit and berat_beli_per_unit > 0:
        return quantity * berat_beli_per_unit * hpp_per_unit
    return quantity * hpp_per_unit


def calc_row_total_jual(quantity, berat_beli_per_unit, harga_jual_per_unit,
                         different_scale=False, berat_jual_per_unit=None):
    berat_jual = berat_jual_per_unit if (different_scale and berat_jual_per_unit) else berat_beli_per_unit
    if berat_jual and berat_jual > 0:
        return quantity * berat_jual * harga_jual_per_unit
    return quantity * harga_jual_per_unit


def calc_ppn(total_jual, price_mode):
    if price_mode == "include_ppn":
        ppn = (total_jual / Decimal("1.11")) * Decimal("0.11")
        grand_total = total_jual
    else:
        ppn = total_jual * Decimal("0.11")
        grand_total = total_jual + ppn
    return ppn, grand_total


def validate_penawaran_calc(items_data, price_mode):
    total_beli = Decimal("0")
    total_jual = Decimal("0")

    for item in items_data:
        qty = Decimal(str(item["quantity"]))
        berat_beli = Decimal(str(item.get("berat_beli_per_unit", 0)))
        hpp = Decimal(str(item["hpp_per_unit"]))
        harga_jual = Decimal(str(item["harga_jual_per_unit"]))
        diff_scale = item.get("different_scale", False)
        berat_jual = Decimal(str(item.get("berat_jual_per_unit") or 0))

        row_beli = calc_row_total_beli(qty, berat_beli, hpp)
        row_jual = calc_row_total_jual(qty, berat_beli, harga_jual, diff_scale, berat_jual)

        total_beli += row_beli
        total_jual += row_jual

    ppn_amount, grand_total = calc_ppn(total_jual, price_mode)

    return {
        "total_beli": total_beli,
        "total_jual": total_jual,
        "ppn_amount": ppn_amount,
        "grand_total": grand_total,
    }
```

- [ ] **Step 3: Create app/services/revision.py**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import new_id


async def create_revision(db, doc_model, items_model, doc_id, doc_fk_field):
    old_doc = await db.get(doc_model, doc_id)
    if not old_doc:
        raise ValueError("Document not found")

    # Mark old as obsolete
    old_doc.is_current = False
    old_doc.status = "revised"

    # Clone document
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
        item_data = {c.name: getattr(old_item, c.name) for c in items_model.__table__.columns
                     if c.name not in ("id", doc_fk_field)}
        item_data[doc_fk_field] = new_doc.id
        item_data["id"] = new_id()
        new_item = items_model(**item_data)
        db.add(new_item)

    await db.flush()
    return new_doc
```

- [ ] **Step 4: Create app/schemas/penawaran.py**

```python
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class PenawaranItemCreate(BaseModel):
    item_id: str
    supplier_id: Optional[str] = None
    quantity: Decimal
    berat_beli_per_unit: Decimal = Decimal("0")
    hpp_per_unit: Decimal = Decimal("0")
    harga_jual_per_unit: Decimal = Decimal("0")
    different_scale: bool = False
    berat_jual_per_unit: Optional[Decimal] = None
    urutan: int = 0
    notes: Optional[str] = None


class PenawaranItemResponse(BaseModel):
    id: str
    penawaran_id: str
    item_id: str
    supplier_id: Optional[str] = None
    quantity: Decimal
    berat_beli_per_unit: Decimal
    hpp_per_unit: Decimal
    total_beli: Decimal
    harga_jual_per_unit: Decimal
    total_jual: Decimal
    different_scale: bool
    berat_jual_per_unit: Optional[Decimal] = None
    urutan: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PenawaranCreate(BaseModel):
    customer_id: Optional[str] = None
    supplier_mode: str = "single"
    price_mode: str = "include_ppn"
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    notes: Optional[str] = None
    items: list[PenawaranItemCreate] = []


class PenawaranUpdate(BaseModel):
    customer_id: Optional[str] = None
    supplier_mode: Optional[str] = None
    price_mode: Optional[str] = None
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    notes: Optional[str] = None
    items: Optional[list[PenawaranItemCreate]] = None


class PenawaranResponse(BaseModel):
    id: str
    nomor: str
    customer_id: Optional[str] = None
    supplier_mode: str
    price_mode: str
    terms_of_payment: Optional[str] = None
    terms_of_delivery: Optional[str] = None
    validity_days: Optional[int] = None
    notes: Optional[str] = None
    status: str
    total_beli: Decimal
    total_jual: Decimal
    ppn_amount: Decimal
    grand_total: Decimal
    version: int
    parent_id: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PenawaranDetailResponse(PenawaranResponse):
    items: list[PenawaranItemResponse] = []
```

- [ ] **Step 5: Create app/routers/penawaran.py**

Full CRUD: list, get (with items), create (with items + counter), update (replace items), delete, revise, lock, versions.

- [ ] **Step 6: Register in main.py, verify, commit**

```bash
git add -A
git commit -m "feat: penawaran model + API + calc + revision services"
```

---

### Task 9: Penawaran HTMX Builder (Alpine.js Live Calc)

**Files:**
- Create: `app/htmx/penawaran.py`
- Create: `app/templates/penawaran/index.html`
- Create: `app/templates/penawaran/_table.html`
- Create: `app/templates/penawaran/new.html` (builder)
- Create: `app/templates/penawaran/detail.html`
- Modify: `app/main.py`

**Interfaces:**
- Consumes: penawaran API endpoints
- Produces: `/app/penawaran` list, `/app/penawaran/new` builder, `/app/penawaran/{id}` detail
- Key: Alpine.js `penawaranBuilder` component for live calculation

- [ ] **Step 1-5: Create HTMX routes + templates**

The builder template (new.html) contains the full Alpine.js component as specified in the design spec Section 5.

- [ ] **Step 6: Verify live calc works**

Visit `/app/penawaran/new`, add items, change quantities/prices — totals should update in real-time.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: penawaran HTMX builder with Alpine.js live calc"
```

---

### Task 10: Upload Service + Component

**Files:**
- Create: `app/services/upload.py`
- Create: `app/routers/uploads.py`
- Create: `app/templates/shared/_upload.html`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `POST /api/uploads` → returns `{path, filename, size, content_type}`
- Produces: `GET /api/uploads/{path}` → serves file
- Produces: `DELETE /api/uploads/{path}` → deletes file
- Produces: `_upload.html` reusable Jinja2 include

- [ ] **Step 1: Create app/services/upload.py**

```python
import os
from datetime import datetime, timezone, timedelta
from fastapi import UploadFile, HTTPException

WIB = timezone(timedelta(hours=7))

ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_SIZE_MB = 5


async def upload_file(file: UploadFile, module: str, entity_id: str, field: str, data_dir: str) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Tipe file {file.content_type} tidak diizinkan")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(400, f"File terlalu besar ({size_mb:.1f}MB, maks {MAX_SIZE_MB}MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    timestamp = datetime.now(WIB).strftime("%Y%m%d-%H%M%S")
    filename = f"{field}-{timestamp}.{ext}"

    dir_path = os.path.join(data_dir, "uploads", module, entity_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "path": f"uploads/{module}/{entity_id}/{filename}",
        "filename": filename,
        "size": len(content),
        "content_type": file.content_type,
    }
```

- [ ] **Step 2: Create app/routers/uploads.py**

```python
import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.config import settings
from app.services.upload import upload_file

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload(
    file: UploadFile = File(...),
    module: str = Form(...),
    entity_id: str = Form(...),
    field: str = Form(...),
):
    return await upload_file(file, module, entity_id, field, settings.data_dir)


@router.get("/{path:path}")
async def serve(path: str):
    file_path = os.path.join(settings.data_dir, path)
    if not os.path.isfile(file_path):
        raise HTTPException(404, "File tidak ditemukan")
    return FileResponse(file_path)


@router.delete("/{path:path}")
async def delete(path: str):
    file_path = os.path.join(settings.data_dir, path)
    if not os.path.isfile(file_path):
        raise HTTPException(404, "File tidak ditemukan")
    os.remove(file_path)
    return {"ok": True}
```

- [ ] **Step 3: Create _upload.html component**

- [ ] **Step 4: Register router, verify, commit**

```bash
git add -A
git commit -m "feat: file upload service + component"
```

---

### Task 11: PDF Generation Service

**Files:**
- Create: `app/services/pdf.py`
- Create: `app/routers/pdf.py`
- Create: `app/templates/print/penawaran.html`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `GET /api/pdf/penawaran/{id}` → PDF bytes
- Consumes: WeasyPrint, print templates

- [ ] **Step 1: Create app/services/pdf.py**

```python
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import get_all_settings

jinja_env = Environment(loader=FileSystemLoader("app/templates"))


async def generate_pdf(doc_type: str, doc, db: AsyncSession) -> bytes:
    company = await get_all_settings(db)
    template = jinja_env.get_template(f"print/{doc_type}.html")

    from app.utils.format import format_rupiah, format_date_wib

    html_content = template.render(
        doc=doc,
        company=company,
        format_rupiah=format_rupiah,
        format_date=format_date_wib,
    )
    return HTML(string=html_content).write_pdf()
```

- [ ] **Step 2: Create app/utils/format.py**

```python
from datetime import datetime
from decimal import Decimal


def format_rupiah(value) -> str:
    if value is None:
        return "Rp 0"
    return "Rp {:,.0f}".format(Decimal(str(value))).replace(",", ".")


def format_date_wib(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d %B %Y")
    return str(value)
```

- [ ] **Step 3: Create app/routers/pdf.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pdf import generate_pdf

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.get("/penawaran/{doc_id}")
async def pdf_penawaran(doc_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.penawaran import Penawaran
    doc = await db.get(Penawaran, doc_id)
    if not doc:
        raise HTTPException(404, "Penawaran tidak ditemukan")
    pdf_bytes = await generate_pdf("penawaran", doc, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=penawaran-{doc.nomor}.pdf"},
    )
```

- [ ] **Step 4: Create print template for penawaran**

- [ ] **Step 5: Verify PDF renders, commit**

```bash
git add -A
git commit -m "feat: PDF generation service + penawaran print template"
```

---

### Task 12: Settings API + Page

**Files:**
- Create: `app/routers/settings.py`
- Create: `app/htmx/settings.py`
- Create: `app/schemas/settings.py`
- Create: `app/templates/settings/index.html`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `GET/PUT /api/settings`, `POST /api/settings/logo`
- Produces: `/app/pengaturan` settings page

- [ ] **Step 1-4: Create settings routes + template**

- [ ] **Step 5: Verify, commit**

```bash
git add -A
git commit -m "feat: settings API + pengaturan page"
```

---

### Task 13: Dashboard + Seed Data

**Files:**
- Create: `app/htmx/dashboard.py`
- Create: `app/templates/dashboard/index.html`
- Create: `app/seed.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `/app/` dashboard with summary stats
- Produces: seed script for sample data

- [ ] **Step 1: Create dashboard page**

Stats: total penawaran, total contacts, total items, recent activity.

- [ ] **Step 2: Create seed script**

Sample: 3 customers, 3 suppliers, 2 expeditions, 5 items.

- [ ] **Step 3: Verify, commit**

```bash
git add -A
git commit -m "feat: dashboard + seed data"
```

---

## After Phase 1

The app will have:
- ✅ Working Docker dev environment
- ✅ Contact management (4 types + TOP history)
- ✅ Item management
- ✅ Penawaran (full CRUD + live calc + revision + PDF)
- ✅ File upload (reusable component)
- ✅ Settings page
- ✅ Dashboard
- ✅ Uniform layout + sidebar

**Phase 2** adds: Sales Order, Purchase Order, Pickup Order, Delivery Note, Proforma Invoice, Invoice — all following the same pattern proven in Phase 1.

**Phase 3** adds: Payments tracking, Shipping dashboard, Finance dashboard, payment chains.
