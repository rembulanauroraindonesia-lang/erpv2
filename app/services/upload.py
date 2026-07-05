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
