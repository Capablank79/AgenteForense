"""
Rutas API para escaneo de discos físicos y vinculación segura (Binding) con DSM.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.hardware.service import HardwareService
from agente_forense.hardware.bindings import DiskBindingService
from agente_forense.hardware.models import (
    ClassifiedDisk, DsmDiskComparison, ForensicDiskClassification, DiskSnapshot
)
from agente_forense.hardware.errors import (
    HardwareError,
    PowerShellUnavailableError,
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
    SourceChangedError,
    WriteBlockerNotFoundError,
    UnresolvedRelationError,
    WriteBlockerCrossAssignmentError,
)
from agente_forense.hardware.write_blockers import WriteBlockerService


class SelectWriteBlockerRequest(BaseModel):
    blocker_id: str
    operator: Optional[str] = "HUMAN_OPERATOR"

router = APIRouter()


class ProposeBindingRequest(BaseModel):
    disk_number: int
    operator: Optional[str] = "WEB_USER"
    override_snapshot: Optional[Dict[str, Any]] = None


class ConfirmBindingRequest(BaseModel):
    binding_id: UUID
    operator: Optional[str] = "HUMAN_OPERATOR"


class RevalidateBindingRequest(BaseModel):
    operator: Optional[str] = "SYSTEM"
    override_snapshot: Optional[Dict[str, Any]] = None


def _map_hardware_error_to_http(e: HardwareError) -> HTTPException:
    if isinstance(e, DiskNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "DISK_NOT_FOUND", "message": str(e)}
        )
    elif isinstance(e, DiskNotReadOnlyError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "DISK_NOT_READ_ONLY", "message": str(e)}
        )
    elif isinstance(e, SystemDiskBlockedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "SYSTEM_DISK_BLOCKED", "message": str(e)}
        )
    elif isinstance(e, BootDiskBlockedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "BOOT_DISK_BLOCKED", "message": str(e)}
        )
    elif isinstance(e, UnsupportedDiskRepresentationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "UNSUPPORTED_DISK_REPRESENTATION", "message": str(e)}
        )
    elif isinstance(e, DiskIdentityConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "DISK_IDENTITY_CONFLICT", "message": str(e)}
        )
    elif isinstance(e, MultipleCandidatesError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "MULTIPLE_CANDIDATES", "message": str(e)}
        )
    elif isinstance(e, DiskBindingNotConfirmedError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "DISK_BINDING_NOT_CONFIRMED", "message": str(e)}
        )
    elif isinstance(e, SourceChangedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "SOURCE_CHANGED", "message": str(e)}
        )
    elif isinstance(e, WriteBlockerNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "WRITE_BLOCKER_NOT_FOUND", "message": str(e)}
        )
    elif isinstance(e, UnresolvedRelationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "UNRESOLVED_RELATION", "message": str(e)}
        )
    elif isinstance(e, WriteBlockerCrossAssignmentError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CROSS_ASSIGNMENT_BLOCKED", "message": str(e)}
        )
    elif isinstance(e, PowerShellUnavailableError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "POWERSHELL_UNAVAILABLE", "message": str(e)}
        )
    elif isinstance(e, DiskScanTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error_code": "DISK_SCAN_TIMEOUT", "message": str(e)}
        )
    elif isinstance(e, DiskScanParseError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DISK_SCAN_PARSE_ERROR", "message": str(e)}
        )
    else:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "HARDWARE_ERROR", "message": str(e)}
        )


@router.get("/api/system/disks")
def get_system_disks(
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/system/disks
    Escanea discos físicos en el sistema host y retorna clasificación forense.
    """
    service = HardwareService(session)
    request_id = getattr(request.state, "request_id", None)
    try:
        classified = service.scan_and_classify_disks(operator="WEB_USER")
        return [
            {
                "disk_number": c.snapshot.disk_number,
                "physical_drive": c.snapshot.physical_drive,
                "friendly_name": c.snapshot.friendly_name,
                "serial_number": c.snapshot.serial_number,
                "unique_id": c.snapshot.unique_id,
                "size_bytes": c.snapshot.size_bytes,
                "bus_type": c.snapshot.bus_type,
                "is_read_only": c.snapshot.is_read_only,
                "is_system": c.snapshot.is_system,
                "is_boot": c.snapshot.is_boot,
                "is_offline": c.snapshot.is_offline,
                "classification": c.classification.value,
                "reasons": c.reasons
            }
            for c in classified
        ]
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


@router.get("/api/cases/{case_id}/dsms/{dsm_id}/disk-candidates")
def get_disk_candidates_for_dsm_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/cases/{case_id}/dsms/{dsm_id}/disk-candidates
    Compara discos físicos escaneados contra la especificación DSM.
    """
    service = HardwareService(session)
    try:
        candidates = service.get_disk_candidates_for_dsm(case_id=case_id, dsm_id=dsm_id, operator="WEB_USER")
        return [
            {
                "disk": {
                    "disk_number": c.snapshot.disk_number,
                    "physical_drive": c.snapshot.physical_drive,
                    "friendly_name": c.snapshot.friendly_name,
                    "serial_number": c.snapshot.serial_number,
                    "unique_id": c.snapshot.unique_id,
                    "size_bytes": c.snapshot.size_bytes,
                    "bus_type": c.snapshot.bus_type,
                    "is_read_only": c.snapshot.is_read_only,
                    "is_system": c.snapshot.is_system,
                    "is_boot": c.snapshot.is_boot,
                    "is_offline": c.snapshot.is_offline,
                    "classification": c.classification.value,
                    "reasons": c.reasons
                },
                "comparison": {
                    "dsm_id": str(comp.dsm_id),
                    "disk_number": comp.disk_number,
                    "physical_drive": comp.physical_drive,
                    "status": comp.status.value if hasattr(comp.status, "value") else str(comp.status),
                    "reasons": comp.reasons,
                    "serial_matched": comp.serial_matched,
                    "capacity_matched": comp.capacity_matched,
                    "model_matched": comp.model_matched
                }
            }
            for c, comp in candidates
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "NOT_FOUND", "message": str(e)})
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


@router.post("/api/cases/{case_id}/dsms/{dsm_id}/disk-binding/propose")
def propose_disk_binding_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    req: ProposeBindingRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/propose
    Propone vincular un disk_number con un DSM. Fails-closed si no es read-only o es system/boot.
    """
    binding_service = DiskBindingService(session)
    request_id = getattr(request.state, "request_id", None)
    operator = req.operator or "WEB_USER"

    override_snap = None
    if req.override_snapshot:
        override_snap = DiskSnapshot(**req.override_snapshot)

    try:
        binding = binding_service.propose_binding(
            case_id=case_id,
            dsm_id=dsm_id,
            disk_number=req.disk_number,
            operator=operator,
            request_id=request_id,
            override_snapshot=override_snap
        )
        return {
            "binding_id": str(binding.id),
            "case_id": str(binding.case_id),
            "dsm_id": str(binding.dsm_id),
            "disk_number": binding.disk_number,
            "physical_drive": binding.physical_drive,
            "status": binding.status,
            "observed_at": binding.observed_at.isoformat() if binding.observed_at else None,
            "snapshot": binding.snapshot_json
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "NOT_FOUND", "message": str(e)})
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


@router.post("/api/cases/{case_id}/dsms/{dsm_id}/disk-binding/confirm")
def confirm_disk_binding_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    req: ConfirmBindingRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/confirm
    Confirma el binding propuesto previa validación por Human Gate.
    """
    binding_service = DiskBindingService(session)
    request_id = getattr(request.state, "request_id", None)
    operator = req.operator or "HUMAN_OPERATOR"

    try:
        binding = binding_service.confirm_binding(
            case_id=case_id,
            dsm_id=dsm_id,
            binding_id=req.binding_id,
            operator=operator,
            request_id=request_id
        )
        return {
            "binding_id": str(binding.id),
            "case_id": str(binding.case_id),
            "dsm_id": str(binding.dsm_id),
            "disk_number": binding.disk_number,
            "physical_drive": binding.physical_drive,
            "status": binding.status,
            "confirmed_at": binding.confirmed_at.isoformat() if binding.confirmed_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "NOT_FOUND", "message": str(e)})
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


@router.get("/api/cases/{case_id}/dsms/{dsm_id}/disk-binding")
def get_active_disk_binding_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/cases/{case_id}/dsms/{dsm_id}/disk-binding
    Retorna el binding activo actualmente para el DSM si existe.
    """
    binding_service = DiskBindingService(session)
    binding = binding_service.get_active_binding(case_id=case_id, dsm_id=dsm_id)
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "BINDING_NOT_FOUND", "message": f"No hay binding activo para el DSM {dsm_id}"}
        )

    return {
        "binding_id": str(binding.id),
        "case_id": str(binding.case_id),
        "dsm_id": str(binding.dsm_id),
        "disk_number": binding.disk_number,
        "physical_drive": binding.physical_drive,
        "serial_number": binding.serial_number,
        "unique_id": binding.unique_id,
        "friendly_name": binding.friendly_name,
        "size_bytes": binding.size_bytes,
        "bus_type": binding.bus_type,
        "is_read_only": binding.is_read_only,
        "is_system": binding.is_system,
        "is_boot": binding.is_boot,
        "is_offline": binding.is_offline,
        "observed_at": binding.observed_at.isoformat() if binding.observed_at else None,
        "confirmed_at": binding.confirmed_at.isoformat() if binding.confirmed_at else None,
        "status": binding.status,
        "snapshot": binding.snapshot_json
    }


@router.post("/api/cases/{case_id}/dsms/{dsm_id}/disk-binding/revalidate")
def revalidate_disk_binding_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    req: RevalidateBindingRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/revalidate
    Revalida en caliente que el disco físico siga presente, sano y en modo ReadOnly.
    """
    binding_service = DiskBindingService(session)
    request_id = getattr(request.state, "request_id", None)
    operator = req.operator or "SYSTEM"

    override_snap = None
    if req.override_snapshot:
        override_snap = DiskSnapshot(**req.override_snapshot)

    try:
        binding = binding_service.revalidate_active_binding(
            case_id=case_id,
            dsm_id=dsm_id,
            operator=operator,
            request_id=request_id,
            override_revalidation_snap=override_snap
        )
        return {
            "revalidated": True,
            "binding_id": str(binding.id),
            "status": binding.status,
            "physical_drive": binding.physical_drive
        }
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


# Write-Blocker Endpoints (Sprint R08.2.1 REV2)

@router.get("/api/system/write-blockers")
def get_system_write_blockers(
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/system/write-blockers
    Retorna la topología actual de Write-Blockers y medios conectados.
    """
    wb_service = WriteBlockerService(session)
    summary = wb_service.get_topology_summary()
    return summary.model_dump()


@router.post("/api/system/write-blockers/scan")
def scan_system_write_blockers(
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/system/write-blockers/scan
    Re-escanea e inspecciona la topología de Write-Blockers, persiste en DB y refresca.
    Mutación protegida con CSRF.
    """
    wb_service = WriteBlockerService(session)
    summary = wb_service.scan_and_persist_topology(operator="WEB_OPERATOR")
    return summary.model_dump()


@router.get("/api/system/write-blockers/{blocker_id}/media")
def get_write_blocker_media(
    blocker_id: str,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/system/write-blockers/{blocker_id}/media
    Retorna el medio adjunto a un Write-Blocker específico.
    """
    wb_service = WriteBlockerService(session)
    summary = wb_service.get_topology_summary()
    att = next((a for a in summary.attachments if a.blocker_id == blocker_id), None)
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ATTACHMENT_NOT_FOUND", "message": f"No hay medio asociado al bloqueador {blocker_id}"}
        )
    return att.model_dump()


@router.post("/api/cases/{case_id}/dsms/{dsm_id}/write-blocker/select")
def select_write_blocker_for_dsm_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    req: SelectWriteBlockerRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/cases/{case_id}/dsms/{dsm_id}/write-blocker/select
    Selecciona un Write-Blocker para un DSM.
    Resuelve el PhysicalDrive, realiza validaciones R07.1, actualiza PostgreSQL y case.json.
    Mutación protegida con CSRF.
    """
    wb_service = WriteBlockerService(session)
    operator = req.operator or "HUMAN_OPERATOR"
    try:
        res = wb_service.select_blocker_for_dsm(
            case_id=case_id,
            dsm_id=dsm_id,
            blocker_id=req.blocker_id,
            operator=operator
        )
        return res
    except HardwareError as e:
        raise _map_hardware_error_to_http(e)


@router.get("/api/cases/{case_id}/dsms/{dsm_id}/source-selection")
def get_dsm_source_selection_endpoint(
    case_id: UUID,
    dsm_id: UUID,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/cases/{case_id}/dsms/{dsm_id}/source-selection
    Retorna la selección activa de Write-Blocker y la fuente resuelta para el DSM.
    """
    wb_service = WriteBlockerService(session)
    sel = wb_service.get_source_selection_for_dsm(case_id=case_id, dsm_id=dsm_id)
    if not sel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "SELECTION_NOT_FOUND", "message": f"No hay selección de bloqueador para el DSM {dsm_id}"}
        )
    return sel

