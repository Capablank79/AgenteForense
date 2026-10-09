"""
Módulo de enums para el dominio de Agente Forense.
"""

from enum import Enum


class StorageRelation(str, Enum):
    SELF_STORAGE = "SELF_STORAGE"
    CONTAINED_STORAGE = "CONTAINED_STORAGE"


class CaseStatus(str, Enum):
    NEW = "NEW"
    DRAFT_SYNTHETIC = "DRAFT_SYNTHETIC"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class IdentificationStatus(str, Enum):
    PENDING = "PENDING"
    IDENTIFIED = "IDENTIFIED"
    REJECTED = "REJECTED"


class AcquisitionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    ACQUIRED = "ACQUIRED"
    FAILED = "FAILED"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"


class ReconciliationStatus(str, Enum):
    MATCH = "MATCH"
    MISSING_FILE = "MISSING_FILE"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    CONTENT_MISMATCH = "CONTENT_MISMATCH"
