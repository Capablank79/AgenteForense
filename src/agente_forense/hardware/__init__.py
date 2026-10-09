"""
Paquete hardware para la gestión de discos y vínculos físicos DSM ↔ PhysicalDrive.
"""

from agente_forense.hardware.models import (
    DiskSnapshot,
    ClassifiedDisk,
    DsmDiskComparison,
    ForensicDiskClassification,
    MatchingStatus,
    BindingStatus
)
from agente_forense.hardware.errors import (
    HardwareError,
    PowerShellUnavailableError,
    StorageModuleUnavailableError,
    DiskScanTimeoutError,
    DiskScanParseError,
    DiskNotFoundError,
    DiskNotReadOnlyError,
    SystemDiskBlockedError,
    BootDiskBlockedError,
    UnsupportedDiskRepresentationError,
    DiskIdentityConflictError,
    MultipleCandidatesError,
    DiskBindingNotConfirmedError,
    SourceChangedError
)
from agente_forense.hardware.disks import DiskScanner
from agente_forense.hardware.matching import compare_dsm_with_disk
from agente_forense.hardware.revalidation import DiskRevalidator
from agente_forense.hardware.bindings import DiskBindingService, DsmDiskBindingModel
from agente_forense.hardware.service import HardwareService

__all__ = [
    "DiskSnapshot",
    "ClassifiedDisk",
    "DsmDiskComparison",
    "ForensicDiskClassification",
    "MatchingStatus",
    "BindingStatus",
    "HardwareError",
    "PowerShellUnavailableError",
    "StorageModuleUnavailableError",
    "DiskScanTimeoutError",
    "DiskScanParseError",
    "DiskNotFoundError",
    "DiskNotReadOnlyError",
    "SystemDiskBlockedError",
    "BootDiskBlockedError",
    "UnsupportedDiskRepresentationError",
    "DiskIdentityConflictError",
    "MultipleCandidatesError",
    "DiskBindingNotConfirmedError",
    "SourceChangedError",
    "DiskScanner",
    "compare_dsm_with_disk",
    "DiskRevalidator",
    "DiskBindingService",
    "DsmDiskBindingModel",
    "HardwareService",
]
