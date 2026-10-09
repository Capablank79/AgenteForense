"""
Rutas API para la gestión de Casos y Dominio (RUC, NUE, ESPECIE, DSM, case.json, Reconciliación).
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from pathlib import Path
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.persistence.repositories import CaseRepository, NueRepository, SpeciesRepository, DsmRepository
from agente_forense.persistence.services import CaseApplicationService
from agente_forense.storage.case_json import CaseJsonService
from agente_forense.domain.cases import (
    CaseStructureDraft, NUEDraft, SpeciesDraft, DSMDraft
)
from agente_forense.domain.enums import StorageRelation, ReconciliationStatus
from agente_forense.domain.errors import (
    DomainError, InvalidRUCError, InvalidNUEError, CaseAlreadyExistsError,
    DuplicateNUEError, DuplicateSpeciesError, DuplicateDSMError, InvalidStorageTopologyError
)
from agente_forense.orchestration import (
    CaseOrchestrator,
    OrchestrationError,
    InvalidTransitionError,
    PolicyDeniedError,
    ConfirmationRequiredError,
    ConfirmationNotFoundError,
    ConfirmationAlreadyResolvedError,
    ConcurrencyConflictError,
    OrchestrationPersistenceError,
)
from agente_forense.orchestration.human_gate import HumanGate

router = APIRouter()


# Schemas Pydantic
class DSMCreateRequest(BaseModel):
    dsm_number: int
    same_physical_object_as_species: bool = True
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    capacity_bytes: Optional[int] = None


class SpeciesCreateRequest(BaseModel):
    species_number: int
    storage_relation: StorageRelation
    description: Optional[str] = None
    dsms: List[DSMCreateRequest] = Field(default_factory=list)


class NUECreateRequest(BaseModel):
    nue_number: str
    description_from_petition: Optional[str] = None
    species: List[SpeciesCreateRequest] = Field(default_factory=list)


class CaseCreateRequest(BaseModel):
    ruc: str
    requesting_unit: Optional[str] = None
    requesting_rut: Optional[str] = None
    request_type: Optional[str] = None
    confirmed_by_human: bool = False
    nues: List[NUECreateRequest] = Field(default_factory=list)


class ActionExecuteRequest(BaseModel):
    confirmation_id: Optional[str] = None
    operator: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    expected_version: Optional[int] = None



# Funciones auxiliares para convertir Pydantic a Draft
def pydantic_to_draft(req: CaseCreateRequest) -> CaseStructureDraft:
    nues_draft = []
    for nue_req in req.nues:
        species_draft = []
        for sp_req in nue_req.species:
            dsms_draft = [
                DSMDraft(
                    dsm_number=d.dsm_number,
                    same_physical_object_as_species=d.same_physical_object_as_species,
                    device_type=d.device_type,
                    brand=d.brand,
                    model=d.model,
                    serial=d.serial,
                    capacity_bytes=d.capacity_bytes
                )
                for d in sp_req.dsms
            ]
            species_draft.append(
                SpeciesDraft(
                    species_number=sp_req.species_number,
                    storage_relation=sp_req.storage_relation,
                    description=sp_req.description,
                    dsms=dsms_draft
                )
            )
        nues_draft.append(
            NUEDraft(
                nue_number=nue_req.nue_number,
                description_from_petition=nue_req.description_from_petition,
                species=species_draft
            )
        )
    return CaseStructureDraft(
        ruc=req.ruc,
        requesting_unit=req.requesting_unit,
        requesting_rut=req.requesting_rut,
        request_type=req.request_type,
        nues=nues_draft
    )


@router.post("/api/cases/draft")
def validate_case_draft(req: CaseCreateRequest):
    """
    POST /api/cases/draft
    Valida las invariantes del borrador de caso y NO persiste en base de datos.
    """
    try:
        draft = pydantic_to_draft(req)
        draft.validate()
        return {
            "status": "VALID",
            "message": "Borrador de estructura de caso válido.",
            "ruc": draft.ruc,
            "nues_count": len(draft.nues)
        }
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": e.__class__.__name__, "message": str(e)}
        )


@router.post("/api/cases", status_code=status.HTTP_201_CREATED)
def create_case(
    req: CaseCreateRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/cases
    Valida, exige confirmación humana implícita/explícita, persiste de forma atómica transaccional en PostgreSQL,
    escribe `case.json` en root temporal de test, registra eventos de auditoría y responde.
    """
    if not req.confirmed_by_human:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "HUMAN_CONFIRMATION_REQUIRED",
                "message": "Se requiere confirmación humana explícita para materializar la estructura física del caso."
            }
        )

    try:
        draft = pydantic_to_draft(req)
        request_id = getattr(request.state, "request_id", None)
        
        service = CaseApplicationService(session)
        case_model = service.create_case_from_draft(
            draft=draft,
            actor="WEB_API",
            request_id=request_id
        )

        # Generar case.json en root temporal de test
        temp_root = Path(tempfile.gettempdir()) / "agente_forense_test_roots" / f"RUC_{case_model.ruc}"
        json_service = CaseJsonService(session)
        json_path = json_service.write_case_json_atomic(
            case_id=case_model.id,
            target_dir=temp_root,
            actor="WEB_API",
            request_id=request_id
        )

        return {
            "status": "CREATED",
            "case_id": str(case_model.id),
            "ruc": case_model.ruc,
            "case_json_path": str(json_path),
            "message": "Caso persistido exitosamente en DB y snapshot case.json escrito de forma atómica."
        }
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": e.__class__.__name__, "message": str(e)}
        )


@router.get("/api/cases")
def list_cases_json(session: Session = Depends(get_db_session)):
    repo = CaseRepository(session)
    cases = repo.list_all()
    return [
        {
            "id": str(c.id),
            "ruc": c.ruc,
            "requesting_unit": c.requesting_unit,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in cases
    ]


@router.get("/api/cases/{case_id}")
def get_case_detail_json(case_id: UUID, session: Session = Depends(get_db_session)):
    case_repo = CaseRepository(session)
    case = case_repo.get_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CASE_NOT_FOUND", "message": f"Caso {case_id} no encontrado."}
        )

    nue_repo = NueRepository(session)
    nues = nue_repo.list_by_case(case_id)

    nues_data = []
    species_repo = SpeciesRepository(session)
    dsm_repo = DsmRepository(session)

    for nue in nues:
        species_list = species_repo.list_by_nue(nue.id)
        species_data = []
        for sp in species_list:
            dsms = dsm_repo.list_by_species(sp.id)
            dsm_data = [
                {
                    "id": str(d.id),
                    "dsm_number": d.dsm_number,
                    "label": d.label,
                    "same_physical_object_as_species": d.same_physical_object_as_species,
                    "device_type": d.device_type,
                    "brand": d.brand,
                    "model": d.model,
                    "status": d.status,
                    "physical_drive": None,
                    "acquisition_status": d.status,
                    "verification_status": "PENDING"
                }
                for d in dsms
            ]
            species_data.append({
                "id": str(sp.id),
                "species_number": sp.species_number,
                "label": sp.label,
                "storage_relation": sp.storage_relation,
                "status": sp.status,
                "identification_status": sp.status,
                "storage_devices": dsm_data
            })

        nues_data.append({
            "id": str(nue.id),
            "nue": nue.nue_number,
            "nue_number": nue.nue_number,
            "status": nue.status,
            "species": species_data
        })

    return {
        "id": str(case.id),
        "ruc": case.ruc,
        "requesting_unit": case.requesting_unit,
        "requesting_rut": case.requesting_rut,
        "request_type": case.request_type,
        "status": case.status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "nues": nues_data
    }


@router.get("/api/cases/{case_id}/reconciliation")
def get_case_reconciliation(
    case_id: UUID,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    GET /api/cases/{case_id}/reconciliation
    Ejecuta reconciliación entre DB y case.json.
    """
    case_repo = CaseRepository(session)
    case = case_repo.get_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CASE_NOT_FOUND", "message": f"Caso {case_id} no encontrado."}
        )

    request_id = getattr(request.state, "request_id", None)
    temp_root = Path(tempfile.gettempdir()) / "agente_forense_test_roots" / f"RUC_{case.ruc}"
    json_path = temp_root / "case.json"

    json_service = CaseJsonService(session)
    rec_status, message = json_service.reconcile(
        case_id=case_id,
        case_json_path=json_path,
        actor="WEB_API",
        request_id=request_id
    )

    return {
        "case_id": str(case_id),
        "ruc": case.ruc,
        "reconciliation_status": rec_status.value,
        "detail": message,
        "case_json_path": str(json_path)
    }


# Endpoints de Orquestación y Human Gate (Sprint R04)

@router.get("/api/cases/{case_id}/state")
def get_case_state_endpoint(case_id: UUID, session: Session = Depends(get_db_session)):
    orchestrator = CaseOrchestrator(session)
    try:
        ctx = orchestrator.build_context(case_id)
        return {
            "case_id": str(case_id),
            "status": ctx.current_state.value,
            "state_version": ctx.state_version,
            "case_json_exists": ctx.case_json_exists,
            "case_json_valid": ctx.case_json_valid,
            "reconciliation_match": ctx.reconciliation_match,
            "critical_reconciliation_errors": ctx.critical_reconciliation_errors,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CASE_NOT_FOUND", "message": str(e)}
        )


@router.get("/api/cases/{case_id}/actions")
def get_case_actions_endpoint(case_id: UUID, session: Session = Depends(get_db_session)):
    orchestrator = CaseOrchestrator(session)
    try:
        actions = orchestrator.get_allowed_actions(case_id)
        return [
            {
                "action": a.action,
                "allowed": a.allowed,
                "requires_confirmation": a.requires_confirmation,
                "reason": a.reason,
            }
            for a in actions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CASE_NOT_FOUND", "message": str(e)}
        )


@router.post("/api/cases/{case_id}/actions/{action}")
def execute_case_action_endpoint(
    case_id: UUID,
    action: str,
    req: ActionExecuteRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    orchestrator = CaseOrchestrator(session)
    request_id = getattr(request.state, "request_id", None)
    operator = req.operator or "WEB_USER"

    try:
        res = orchestrator.execute_action(
            case_id=case_id,
            action=action,
            confirmation_id=req.confirmation_id,
            operator=operator,
            request_id=request_id,
            payload=req.payload,
            expected_version=req.expected_version,
        )
        return res
    except ConfirmationRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "CONFIRMATION_REQUIRED",
                "message": str(e),
                "confirmation_id": e.confirmation_id,
            }
        )
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_TRANSITION", "message": str(e)}
        )
    except PolicyDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "POLICY_DENIED", "message": str(e)}
        )
    except ConcurrencyConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CONCURRENCY_CONFLICT", "message": str(e)}
        )
    except OrchestrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "ORCHESTRATION_ERROR", "message": str(e)}
        )


@router.post("/api/confirmations/{confirmation_id}/confirm")
def confirm_human_gate_endpoint(
    confirmation_id: str,
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    session: Session = Depends(get_db_session)
):
    gate = HumanGate(session)
    operator = (payload.get("operator") if payload else None) or "WEB_OPERATOR"
    try:
        record = gate.confirm(confirmation_id, operator=operator)
        session.commit()
        return {
            "status": "CONFIRMED",
            "confirmation_id": record.confirmation_id,
            "case_id": str(record.case_id),
            "requested_action": record.requested_action,
            "operator": record.operator,
        }
    except ConfirmationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CONFIRMATION_NOT_FOUND", "message": str(e)}
        )
    except ConfirmationAlreadyResolvedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "CONFIRMATION_ALREADY_RESOLVED", "message": str(e)}
        )


@router.post("/api/confirmations/{confirmation_id}/reject")
def reject_human_gate_endpoint(
    confirmation_id: str,
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    session: Session = Depends(get_db_session)
):
    gate = HumanGate(session)
    operator = (payload.get("operator") if payload else None) or "WEB_OPERATOR"
    try:
        record = gate.reject(confirmation_id, operator=operator)
        session.commit()
        return {
            "status": "REJECTED",
            "confirmation_id": record.confirmation_id,
            "case_id": str(record.case_id),
            "requested_action": record.requested_action,
            "operator": record.operator,
        }
    except ConfirmationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CONFIRMATION_NOT_FOUND", "message": str(e)}
        )
    except ConfirmationAlreadyResolvedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "CONFIRMATION_ALREADY_RESOLVED", "message": str(e)}
        )

