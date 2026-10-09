"""
Modelos de datos y enums para el motor de adquisición E01.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AcquisitionJobStatus(str, Enum):
    PREPARED = "PREPARED"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    PROCESS_MISSING_REVIEW_REQUIRED = "PROCESS_MISSING_REVIEW_REQUIRED"
    COMPLETED_PENDING_INSPECTION = "COMPLETED_PENDING_INSPECTION"


@dataclass
class EwfBinaryCapabilities:
    path: str
    exists: bool
    sha256: str
    version: str
    verified: bool
    single_e01_feasible: bool = True
    default_format: str = "encase6"
    default_compression: str = "best"
    supported_digests: List[str] = field(default_factory=lambda: ["md5", "sha256"])


@dataclass
class PreflightSummary:
    case_id: str
    ruc: str
    nue_number: str
    species_number: int
    dsm_number: int
    dsm_id: str
    binding_id: str
    source_physical_drive: str
    source_disk_number: int
    source_serial: Optional[str]
    source_size_bytes: int
    is_read_only: bool
    is_system: bool
    is_boot: bool
    destination_directory: str
    destination_physical_drive: Optional[str]
    destination_filesystem: str
    destination_free_bytes: int
    target_basename: str
    expected_e01_path: str
    binary_sha256: str
    binary_version: str
    format: str = "encase6"
    compression: str = "best"
    segment_size: str = "0"
    digest: str = "sha256"


@dataclass
class HumanGatePayload:
    preflight: PreflightSummary
    prompt_text: str
    required_confirmation: str = "ADQUIRIR"


@dataclass
class AcquisitionJob:
    job_id: str
    case_id: str
    dsm_id: str
    binding_id: str
    status: AcquisitionJobStatus
    pid: Optional[int]
    command: List[str]
    stdout_path: str
    stderr_path: str
    native_log_path: Optional[str]
    target_directory: str
    target_basename: str
    expected_e01_path: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_code: Optional[str] = None
    human_confirmation_exact: Optional[str] = None
    operator: Optional[str] = None
    reported_md5: Optional[str] = None
    reported_sha256: Optional[str] = None
    bytes_acquired: Optional[int] = None
    generated_files: List[str] = field(default_factory=list)
    generated_segment_count: int = 0
