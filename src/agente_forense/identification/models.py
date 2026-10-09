"""
Modelos de datos Pydantic / Dataclasses para el módulo de identificación.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class PhotoClassification(str, Enum):
    GENERAL = "GENERAL"
    FRONTAL = "FRONTAL"
    POSTERIOR = "POSTERIOR"
    LATERAL = "LATERAL"
    ETIQUETA = "ETIQUETA"
    SERIAL = "SERIAL"
    CONEXION = "CONEXION"
    DETALLE = "DETALLE"
    NO_CLASIFICADA = "NO_CLASIFICADA"


class AttributeStatus(str, Enum):
    OBSERVED = "OBSERVED"
    EXTRACTED = "EXTRACTED"
    UNCERTAIN = "UNCERTAIN"
    NOT_VISIBLE = "NOT_VISIBLE"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    CONFIRMED = "CONFIRMED"
    CORRECTED_BY_HUMAN = "CORRECTED_BY_HUMAN"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"


class ConflictCode(str, Enum):
    SERIAL_MULTIPLE_VALUES = "SERIAL_MULTIPLE_VALUES"
    MODEL_MULTIPLE_VALUES = "MODEL_MULTIPLE_VALUES"
    BRAND_CONFLICT = "BRAND_CONFLICT"
    CAPACITY_CONFLICT = "CAPACITY_CONFLICT"
    PHOTO_ENTITY_MISMATCH = "PHOTO_ENTITY_MISMATCH"
    LOW_VISIBILITY = "LOW_VISIBILITY"
    NO_TEXT = "NO_TEXT"
    NO_VISION_PROVIDER = "NO_VISION_PROVIDER"


@dataclass
class PhotoIngestRecord:
    photo_id: str
    entity_type: str  # "ESPECIE" | "DSM"
    entity_id: str
    original_filename: str
    relative_path: str
    size_bytes: int
    sha256: str
    width: int
    height: int
    format: str  # "JPEG" | "PNG"
    classification: str = PhotoClassification.NO_CLASIFICADA.value
    classification_final: Optional[str] = None
    ocr_text: str = ""
    analysis_status: str = "PENDING"
    captured_at: Optional[str] = None


@dataclass
class AttributeProvenance:
    field_name: str
    value: Optional[str]
    source_photo_id: Optional[str]
    source_text: Optional[str]
    method: str  # "REGEX", "WINDOWS_OCR", "QWEN2.5_TEXT", "HUMAN"
    status: str
    confidence: Optional[float] = None
    human_confirmed: bool = False


@dataclass
class AttributeValue:
    field_name: str
    value: Optional[str] = None
    normalized_value: Optional[str] = None
    bytes_value: Optional[int] = None
    status: str = AttributeStatus.NOT_FOUND.value
    provenance: Optional[AttributeProvenance] = None


@dataclass
class ConflictRecord:
    code: str
    description: str
    severity: str  # "WARNING" | "BLOCKING"
    affected_fields: List[str] = field(default_factory=list)
    photo_ids: List[str] = field(default_factory=list)


@dataclass
class IdentificationData:
    schema_version: int = 1
    entity_type: str = "SPECIES"
    entity_id: str = ""
    entity_label: str = ""
    status: str = "IDENTIFICATION_PENDING"
    photos: List[PhotoIngestRecord] = field(default_factory=list)
    attributes: Dict[str, AttributeValue] = field(default_factory=dict)
    conflicts: List[ConflictRecord] = field(default_factory=list)
    human_review: Dict[str, Any] = field(default_factory=lambda: {
        "reviewed": False,
        "reviewed_by": None,
        "reviewed_at": None,
        "confirmed": False
    })
    tool_versions: Dict[str, str] = field(default_factory=lambda: {
        "ocr_engine": "Windows.Media.Ocr es-ES (winsdk 1.0.0b10)",
        "llm_engine": "qwen2.5:3b (Text-Only via Ollama)"
    })
    timestamps: Dict[str, str] = field(default_factory=dict)
