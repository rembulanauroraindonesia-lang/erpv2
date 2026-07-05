import os
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
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
