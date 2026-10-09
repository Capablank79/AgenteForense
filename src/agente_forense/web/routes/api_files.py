"""
Rutas API para Staging de Archivos.
"""

from pathlib import Path
import os
import hashlib
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status
from agente_forense.web.config import WebConfig
from agente_forense.storage.paths import sanitize_filename, validate_safe_path
from agente_forense.core.errors import SafetyViolationError

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".jpg", ".jpeg", ".png"}
CHUNK_SIZE = 64 * 1024  # 64 KB per chunk

@router.post("/api/files/stage")
async def stage_file_upload(request: Request, file: UploadFile = File(...)):
    app_config: WebConfig = getattr(request.app.state, "web_config", None) or WebConfig()
    staging_dir_setting = app_config.staging_dir
    max_bytes = app_config.max_upload_bytes

    # Sanitización de nombre
    original_name = file.filename or "file_unnamed"
    try:
        safe_filename = sanitize_filename(original_name)
    except SafetyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_FILENAME", "message": str(e)}
        )
    ext = Path(safe_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_FILE_TYPE", "message": f"Extensión de archivo no permitida en R02.1: {ext}"}
        )

    staging_dir = Path(staging_dir_setting or config.staging_dir or "runtime/staging").resolve()
    staging_dir.mkdir(parents=True, exist_ok=True)

    target_path = validate_safe_path(staging_dir, safe_filename)

    if target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "FILE_ALREADY_EXISTS", "message": f"El archivo ya existe en staging: {safe_filename}"}
        )

    hasher = hashlib.sha256()
    bytes_written = 0

    try:
        with open(target_path, "wb") as f_out:
            while chunk := await file.read(CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    f_out.close()
                    if target_path.exists():
                        target_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "error_code": "MAX_UPLOAD_SIZE_EXCEEDED",
                            "message": f"El archivo excede el tamaño máximo permitido de {max_bytes} bytes."
                        }
                    )
                hasher.update(chunk)
                f_out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPLOAD_FAILED", "message": f"Error guardando archivo en staging: {str(e)}"}
        )
    finally:
        await file.close()

    sha256_hash = hasher.hexdigest()

    return {
        "status": "staged",
        "original_filename": original_name,
        "stored_filename": safe_filename,
        "size_bytes": bytes_written,
        "sha256": sha256_hash,
        "staging_path": str(target_path.relative_to(staging_dir.parent.parent if staging_dir.is_absolute() else staging_dir))
    }
