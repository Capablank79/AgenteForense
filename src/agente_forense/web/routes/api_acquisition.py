"""
Rutas API para la preparación, confirmación, ejecución y monitoreo de la Adquisición Físico-Forense E01.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.acquisition.service import AcquisitionService
from agente_forense.acquisition.jobs import AcquisitionJobManager
from agente_forense.acquisition.capabilities import EwfBinaryVerifier
from agente_forense.acquisition.models import HumanGatePayload
from agente_forense.acquisition.errors import (
    AcquisitionError,
    EwfBinaryChangedError,
    SourceChangedError,
    AdminPrivilegesRequiredError,
    SpaceBelowRawSizeError,
    DestinationOnSourceDiskError,
    TargetCollisionError,
    HumanGateAbortedError,
    AcquisitionJobNotFoundError,
    AcquisitionJobInvalidStateError,
    AcquisitionProcessFailedError,
    SegmentedArtifactsError,
    AcquisitionIncompleteError,
)

router = APIRouter(prefix="/api/cases/{case_id}/dsms/{dsm_id}/acquisition", tags=["Acquisition"])


class PrepareAcquisitionRequest(BaseModel):
    binding_id: str
    destination_directory: str
    current_system_disks: List[Dict[str, Any]]
    expected_binding_dict: Dict[str, Any]
    operator: Optional[str] = "WEB_USER"


class ConfirmAcquisitionRequest(BaseModel):
    job_id: str
    confirmation_input: str
    operator: Optional[str] = "WEB_USER"


class StartAcquisitionRequest(BaseModel):
    job_id: str
    expected_binding_dict: Dict[str, Any]
    current_system_disks: List[Dict[str, Any]]
    operator: Optional[str] = "WEB_USER"


class CancelAcquisitionRequest(BaseModel):
    job_id: str
    reason: Optional[str] = "User requested cancellation"
    operator: Optional[str] = "WEB_USER"


def _map_acquisition_error_to_http(e: AcquisitionError) -> HTTPException:
    if isinstance(e, EwfBinaryChangedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "EWFACQUIRE_BINARY_CHANGED", "message": str(e)}
        )
    elif isinstance(e, SourceChangedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "SOURCE_CHANGED", "message": str(e)}
        )
    elif isinstance(e, AdminPrivilegesRequiredError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "ADMIN_PRIVILEGES_REQUIRED", "message": str(e)}
        )
    elif isinstance(e, SpaceBelowRawSizeError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "INSUFFICIENT_STORAGE_SPACE", "message": str(e)}
        )
    elif isinstance(e, DestinationOnSourceDiskError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "DESTINATION_ON_SOURCE_DISK", "message": str(e)}
        )
    elif isinstance(e, TargetCollisionError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "TARGET_ALREADY_EXISTS", "message": str(e)}
        )
    elif isinstance(e, HumanGateAbortedError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "HUMAN_GATE_ABORTED", "message": str(e)}
        )
    elif isinstance(e, AcquisitionJobNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": str(e)}
        )
    elif isinstance(e, AcquisitionJobInvalidStateError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "INVALID_JOB_STATE", "message": str(e)}
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "ACQUISITION_ERROR", "message": str(e)}
        )


@router.get("/readiness")
def check_acquisition_readiness():
    """
    Verifica si el binario ewfacquire.exe cumple con la firma esperada SHA256.
    """
    verifier = EwfBinaryVerifier()
    try:
        caps = verifier.verify()
        return {
            "status": "READY",
            "capabilities": caps.to_dict()
        }
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)


@router.post("/prepare")
def prepare_acquisition(
    case_id: str,
    dsm_id: str,
    req: PrepareAcquisitionRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Ejecuta las validaciones preflight y genera el payload para el Human Gate.
    """
    case_root_base = getattr(request.app.state.web_config, "case_root_base", "J:\\AgenteForense\\Casos")
    service = AcquisitionService(db_session=db, case_root_base=case_root_base)

    try:
        payload = service.prepare_acquisition(
            case_id=case_id,
            dsm_id=dsm_id,
            binding_id=req.binding_id,
            destination_directory=req.destination_directory,
            current_system_disks=req.current_system_disks,
            expected_binding_dict=req.expected_binding_dict,
            operator=req.operator
        )
        return payload.to_dict()
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "INVALID_INPUT", "message": str(e)})


@router.post("/confirm")
def confirm_acquisition(
    case_id: str,
    dsm_id: str,
    req: ConfirmAcquisitionRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Recibe la confirmación humana ('ADQUIRIR') y transiciona el job a WAITING_CONFIRMATION o ABORTED.
    """
    case_root_base = getattr(request.app.state.web_config, "case_root_base", "J:\\AgenteForense\\Casos")
    manager = AcquisitionJobManager(db_session=db, case_root_base=case_root_base)

    try:
        job_rec = manager.confirm_human_gate(
            job_id=req.job_id,
            user_input=req.confirmation_input,
            operator=req.operator
        )
        return job_rec.to_dict()
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)


@router.post("/start")
def start_acquisition(
    case_id: str,
    dsm_id: str,
    req: StartAcquisitionRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Revalida en caliente el disco de origen e inicia la ejecución de ewfacquire en segundo plano.
    """
    case_root_base = getattr(request.app.state.web_config, "case_root_base", "J:\\AgenteForense\\Casos")
    manager = AcquisitionJobManager(db_session=db, case_root_base=case_root_base)

    try:
        job_rec = manager.start_job(
            job_id=req.job_id,
            expected_binding_dict=req.expected_binding_dict,
            current_system_disks=req.current_system_disks,
            operator=req.operator
        )
        return job_rec.to_dict()
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)


@router.get("/job/{job_id}")
def get_acquisition_job(
    case_id: str,
    dsm_id: str,
    job_id: str,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Consulta y actualiza el estado de un job de adquisición.
    """
    case_root_base = getattr(request.app.state.web_config, "case_root_base", "J:\\AgenteForense\\Casos")
    manager = AcquisitionJobManager(db_session=db, case_root_base=case_root_base)

    try:
        job_rec = manager.poll_job_status(job_id=job_id)
        return job_rec.to_dict()
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)


@router.post("/cancel")
def cancel_acquisition(
    case_id: str,
    dsm_id: str,
    req: CancelAcquisitionRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Cancela un job en ejecución matando el proceso de ewfacquire limpiamente.
    """
    case_root_base = getattr(request.app.state.web_config, "case_root_base", "J:\\AgenteForense\\Casos")
    manager = AcquisitionJobManager(db_session=db, case_root_base=case_root_base)

    try:
        job_rec = manager.cancel_job(
            job_id=req.job_id,
            reason=req.reason,
            operator=req.operator
        )
        return job_rec.to_dict()
    except AcquisitionError as e:
        raise _map_acquisition_error_to_http(e)
