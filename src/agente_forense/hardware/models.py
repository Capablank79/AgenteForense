"""
Modelos Pydantic / dataclasses para la captura, clasificación y binding de discos.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ForensicDiskClassification(str, Enum):
    FORENSIC_CANDIDATE = "FORENSIC_CANDIDATE"
    BLOCKED_NOT_READ_ONLY = "BLOCKED_NOT_READ_ONLY"
    BLOCKED_SYSTEM_DISK = "BLOCKED_SYSTEM_DISK"
    BLOCKED_BOOT_DISK = "BLOCKED_BOOT_DISK"
    BLOCKED_MULTIPLE_REASONS = "BLOCKED_MULTIPLE_REASONS"
    UNSUPPORTED_DISK_REPRESENTATION = "UNSUPPORTED_DISK_REPRESENTATION"


class MatchingStatus(str, Enum):
    MATCH = "MATCH"
    COMPATIBLE = "COMPATIBLE"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class BindingStatus(str, Enum):
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    INVALIDATED = "INVALIDATED"
    REJECTED = "REJECTED"


class DiskSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    disk_number: int
    physical_drive: str  # ej: "\\\\.\\PHYSICALDRIVE4"
    friendly_name: Optional[str] = None
    serial_number: Optional[str] = None
    unique_id: Optional[str] = None
    path: Optional[str] = None
    size_bytes: int
    bus_type: Optional[str] = None
    partition_style: Optional[str] = None
    is_read_only: bool
    is_system: bool
    is_boot: bool
    is_offline: Optional[bool] = None
    operational_status: Optional[str] = None
    health_status: Optional[str] = None
    pnp_device_id: Optional[str] = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "WINDOWS_STORAGE_API"


class ClassifiedDisk(BaseModel):
    snapshot: DiskSnapshot
    classification: ForensicDiskClassification
    reasons: List[str] = Field(default_factory=list)


class DsmDiskComparison(BaseModel):
    dsm_id: str
    disk_number: int
    physical_drive: str
    status: MatchingStatus
    reasons: List[str] = Field(default_factory=list)
    serial_matched: Optional[bool] = None
    capacity_matched: Optional[bool] = None
    model_matched: Optional[bool] = None
