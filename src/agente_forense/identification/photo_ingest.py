"""
Ingesta segura de fotografías con verificación de hash SHA-256 e inmutabilidad.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image
from uuid import uuid4

from agente_forense.storage.hashing import calculate_sha256
from agente_forense.identification.errors import UnsupportedFormatError, PhotoIntegrityError, InvalidEntityError
from agente_forense.identification.models import PhotoIngestRecord, PhotoClassification

ALLOWED_FORMATS = {"JPEG", "JPG", "PNG"}

def verify_photo_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verifica que el archivo no haya sido modificado en disco."""
    if not file_path.exists():
        return False
    current_hash = calculate_sha256(file_path)
    return current_hash.lower() == expected_hash.lower()

def ingest_photo(
    file_path: Path,
    entity_type: str,
    entity_id: str,
    relative_path: str,
    photo_id: Optional[str] = None,
) -> PhotoIngestRecord:
    """
    Ingresa una fotografía calculando metadata y hash SHA-256.
    Garantiza que el archivo original no sea modificado.
    """
    if not entity_type or not entity_id:
        raise InvalidEntityError("La fotografía debe asociarse explícitamente a una entidad (ESPECIE o DSM).")

    if not file_path.exists():
        raise FileNotFoundError(f"El archivo de fotografía no existe: {file_path}")

    # Hash BEFORE
    sha256_before = calculate_sha256(file_path)

    # Decodificar metadata visual mediante PIL
    try:
        with Image.open(file_path) as img:
            fmt = (img.format or "").upper()
            width, height = img.size
    except Exception as e:
        raise UnsupportedFormatError(f"No se pudo decodificar la imagen: {str(e)}")

    if fmt not in ALLOWED_FORMATS and file_path.suffix.upper().lstrip(".") not in ALLOWED_FORMATS:
        raise UnsupportedFormatError(f"Formato no soportado: {fmt}. Formatos válidos: JPG, JPEG, PNG.")

    norm_fmt = "PNG" if "PNG" in fmt else "JPEG"

    # Hash AFTER para verificar inmutabilidad durante lectura
    sha256_after = calculate_sha256(file_path)
    if sha256_before != sha256_after:
        raise PhotoIntegrityError(f"PHOTO_INTEGRITY_FAILURE: El archivo {file_path.name} cambió durante la ingesta.")

    if not photo_id:
        photo_id = f"PHOTO-{uuid4().hex[:8].upper()}"

    return PhotoIngestRecord(
        photo_id=photo_id,
        entity_type=entity_type,
        entity_id=entity_id,
        original_filename=file_path.name,
        relative_path=relative_path,
        size_bytes=file_path.stat().st_size,
        sha256=sha256_before,
        width=width,
        height=height,
        format=norm_fmt,
        classification=PhotoClassification.NO_CLASIFICADA.value,
        ocr_text="",
        analysis_status="STAGED"
    )
