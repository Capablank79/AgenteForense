"""
Domain models for Petition processing pipeline (Sprint R05.1).
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    STAGED = "STAGED"
    HASHED = "HASHED"
    TEXT_EXTRACTION_PENDING = "TEXT_EXTRACTION_PENDING"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    OCR_PENDING = "OCR_PENDING"
    OCR_COMPLETED = "OCR_COMPLETED"
    FIELDS_EXTRACTED = "FIELDS_EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY_FOR_DRAFT = "READY_FOR_DRAFT"
    FAILED = "FAILED"


class FieldStatus(str, Enum):
    OBSERVED = "OBSERVED"
    EXTRACTED = "EXTRACTED"
    UNCERTAIN = "UNCERTAIN"
    CONFLICT = "CONFLICT"
    NOT_FOUND = "NOT_FOUND"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFIRMED = "CONFIRMED"
    CORRECTED_BY_HUMAN = "CORRECTED_BY_HUMAN"


class ConflictType(str, Enum):
    MULTIPLE_RUC = "MULTIPLE_RUC"
    RUC_MISSING = "RUC_MISSING"
    MULTIPLE_NUE_CANDIDATES = "MULTIPLE_NUE_CANDIDATES"
    NUE_MISSING = "NUE_MISSING"
    MULTIPLE_OFICIO = "MULTIPLE_OFICIO"
    FIELD_MULTIPLE_VALUES = "FIELD_MULTIPLE_VALUES"
    OCR_EMPTY = "OCR_EMPTY"
    TEXT_EXTRACTION_FAILED = "TEXT_EXTRACTION_FAILED"
    DOCUMENT_INTEGRITY_FAILURE = "DOCUMENT_INTEGRITY_FAILURE"
    AMBIGUOUS_DATE = "AMBIGUOUS_DATE"
    INCOMPLETE_SERIAL = "INCOMPLETE_SERIAL"
    DUPLICATE_NUE_CONFLICT = "DUPLICATE_NUE_CONFLICT"


class PetitionEvidenceItemDeclared(BaseModel):
    nue_number: Optional[str] = None
    quantity: Optional[int] = 1
    description_original: str
    evidence_type_declared: Optional[str] = None
    brand_declared: Optional[str] = None
    model_declared: Optional[str] = None
    serial_number_declared: Optional[str] = None
    capacity_declared: Optional[str] = None
    source_page: int = 1
    source_text: str = ""
    source: str = "OCR"


class PetitionRequestedActionDeclared(BaseModel):
    source_text: str
    normalized_action: Optional[str] = None
    action_order: int = 1
    source_page: int = 1
    source: str = "OCR"


class PetitionAttachmentDeclared(BaseModel):
    attachment_type: str
    description: Optional[str] = None
    reference_number: Optional[str] = None
    source_page: int = 1
    physically_received: bool = False
    source: str = "OCR"


class PetitionDocument(BaseModel):
    document_id: str
    original_filename: str
    stored_relative_path: str
    size_bytes: int
    sha256: str
    extension: str
    mime_observed: str
    page_count: int = 1
    processing_status: ProcessingStatus = ProcessingStatus.STAGED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PetitionPageText(BaseModel):
    page_index: int
    raw_text: str
    normalized_text: str
    extraction_method: str
    render_width: Optional[int] = None
    render_height: Optional[int] = None
    ocr_language: Optional[str] = None


class FieldProvenance(BaseModel):
    source_document_id: str
    page_index: int
    source_text: str
    extraction_method: str


class ExtractedField(BaseModel):
    field_name: str
    value: Optional[str] = None
    normalized_value: Optional[str] = None
    status: FieldStatus = FieldStatus.OBSERVED
    provenance: List[FieldProvenance] = Field(default_factory=list)
    confidence: Optional[float] = None  # Always null when OCR engine confidence is unavailable


class ExtractionConflict(BaseModel):
    conflict_type: ConflictType
    field_name: str
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PetitionExtraction(BaseModel):
    document_id: str
    document_sha256: str
    processing_method: str
    pages: List[PetitionPageText] = Field(default_factory=list)
    fields: List[ExtractedField] = Field(default_factory=list)
    evidence_items: List[PetitionEvidenceItemDeclared] = Field(default_factory=list)
    requested_actions: List[PetitionRequestedActionDeclared] = Field(default_factory=list)
    attachments: List[PetitionAttachmentDeclared] = Field(default_factory=list)
    conflicts: List[ExtractionConflict] = Field(default_factory=list)
    review_status: str = "PENDING"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool_versions: Dict[str, Any] = Field(default_factory=dict)


class FieldReviewAction(BaseModel):
    field_name: str
    action_type: str  # CONFIRM, CORRECT, MARK_NOT_FOUND, MARK_NOT_APPLICABLE
    new_value: Optional[str] = None
    operator: str = "operator"
    comment: Optional[str] = None
