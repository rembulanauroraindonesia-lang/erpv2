import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: F401, F403


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(f"{settings.data_dir}/uploads", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="RAI ERP",
    version=settings.app_version,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

from app.routers import contacts as contacts_api
from app.routers import items as items_api
from app.htmx import contacts as contacts_htmx
from app.htmx import items as items_htmx

app.include_router(contacts_api.router)
app.include_router(items_api.router)
app.include_router(contacts_htmx.router)
app.include_router(items_htmx.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
