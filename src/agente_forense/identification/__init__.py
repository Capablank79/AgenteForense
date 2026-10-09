"""
Módulo de Identificación Fotográfica Asistida.
"""

from agente_forense.identification.models import (
    PhotoClassification,
    AttributeStatus,
    ConflictCode,
    PhotoIngestRecord,
    AttributeProvenance,
    AttributeValue,
    ConflictRecord,
    IdentificationData,
)
from agente_forense.identification.errors import (
    IdentificationError,
    PhotoIntegrityError,
    UnsupportedFormatError,
    InvalidEntityError,
    QwenTimeoutError,
    RenameCollisionError,
)
from agente_forense.identification.photo_ingest import ingest_photo, verify_photo_integrity
from agente_forense.identification.text_classifier import classify_photo_textually
from agente_forense.identification.attribute_extractor import extract_deterministic_attributes, normalize_capacity
from agente_forense.identification.qwen_text import query_qwen_text_analysis
from agente_forense.identification.anti_invention import validate_anti_invention
from agente_forense.identification.conflicts import detect_conflicts
from agente_forense.identification.review import apply_human_review
from agente_forense.identification.renaming import preview_renaming, execute_safe_renaming
from agente_forense.identification.identification_json import write_identification_json_atomic
from agente_forense.identification.service import IdentificationService

__all__ = [
    "PhotoClassification",
    "AttributeStatus",
    "ConflictCode",
    "PhotoIngestRecord",
    "AttributeProvenance",
    "AttributeValue",
    "ConflictRecord",
    "IdentificationData",
    "IdentificationError",
    "PhotoIntegrityError",
    "UnsupportedFormatError",
    "InvalidEntityError",
    "QwenTimeoutError",
    "RenameCollisionError",
    "ingest_photo",
    "verify_photo_integrity",
    "classify_photo_textually",
    "extract_deterministic_attributes",
    "normalize_capacity",
    "query_qwen_text_analysis",
    "validate_anti_invention",
    "detect_conflicts",
    "apply_human_review",
    "preview_renaming",
    "execute_safe_renaming",
    "write_identification_json_atomic",
    "IdentificationService",
]
