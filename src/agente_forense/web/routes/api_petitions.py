"""
API endpoints for Petition processing pipeline (Sprint R05.1).
Includes staging, extraction, human review, and building case draft.
"""
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.petition.service import PetitionService, MAX_UPLOAD_BYTES
from agente_forense.petition.models import (
    PetitionDocument, PetitionExtraction, FieldReviewAction, ProcessingStatus, FieldStatus,
    PetitionEvidenceItemDeclared, PetitionRequestedActionDeclared, PetitionAttachmentDeclared
)
from agente_forense.petition.draft_mapper import CaseStructureDraft
from agente_forense.petition.errors import (
    UnsupportedPetitionFormatError, PetitionIntegrityError,
    PetitionNotReadyForDraftError, PetitionExtractionConflictError
)
from agente_forense.storage.filestore import FileStore
from agente_forense.petition.persistence import PetitionPersistenceService
from agente_forense.persistence.repositories import AuditRepository, PetitionRepository

router = APIRouter()

# In-memory session store for unpersisted extractions during staging/review
_STAGED_EXTRACTIONS: Dict[str, PetitionExtraction] = {}
_STAGED_DOCUMENTS: Dict[str, PetitionDocument] = {}
_STAGED_FILE_PATHS: Dict[str, Path] = {}

class ReviewSubmitRequest(BaseModel):
    actions: List[FieldReviewAction]
    evidence_items: Optional[List[PetitionEvidenceItemDeclared]] = None
    requested_actions: Optional[List[PetitionRequestedActionDeclared]] = None
    attachments: Optional[List[PetitionAttachmentDeclared]] = None

@router.post("/api/petitions/stage")
async def stage_petition_file(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session)
):
    """
    POST /api/petitions/stage
    Uploads and stages petition document, calculates SHA-256 and metadata.
    """
    # 1. Size check
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)
    
    if size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error_code": "FILE_TOO_LARGE", "message": f"File exceeds maximum size of {MAX_UPLOAD_BYTES} bytes."}
        )

    # 2. Stage file in temporary staging area
    doc_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / "agente_forense_staged_petitions" / doc_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    staged_path = temp_dir / file.filename

    content = await file.read()
    with open(staged_path, "wb") as f:
        f.write(content)

    # 3. Process via PetitionService
    service = PetitionService()
    try:
        doc, extraction = service.process_petition_file(
            document_id=doc_id,
            file_path=staged_path,
            original_filename=file.filename,
            stored_relative_path=str(staged_path)
        )
        _STAGED_DOCUMENTS[doc_id] = doc
        _STAGED_EXTRACTIONS[doc_id] = extraction
        _STAGED_FILE_PATHS[doc_id] = staged_path

        # 4. Persistir estructuradamente la entidad Oficio Petitorio en DB PostgreSQL schema forensic
        try:
            filestore = request.app.state.filestore if hasattr(request.app.state, "filestore") else None
            persistence_service = PetitionPersistenceService(session, filestore)
            petition_record = persistence_service.persist_petition_entity(
                doc=doc,
                extraction=extraction,
                actor="OPERATOR"
            )
            session.commit()
        except Exception as pe:
            session.rollback()
            # En staging no bloqueamos si DB opcional no está sincronizada pero registramos si es necesario

        return {
            "document_id": doc_id,
            "original_filename": doc.original_filename,
            "sha256": doc.sha256,
            "page_count": doc.page_count,
            "processing_status": doc.processing_status.value,
            "fields_count": len(extraction.fields),
            "conflicts_count": len(extraction.conflicts)
        }
    except UnsupportedPetitionFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "UNSUPPORTED_FORMAT", "message": str(e)}
        )
    except PetitionIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "INTEGRITY_FAILURE", "message": str(e)}
        )

@router.post("/api/petitions/{doc_id}/extract")
def execute_extraction(doc_id: str):
    """
    POST /api/petitions/{doc_id}/extract
    Triggers/fetches extraction results for staged petition document.
    """
    if doc_id not in _STAGED_EXTRACTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petition {doc_id} not found."}
        )
    extraction = _STAGED_EXTRACTIONS[doc_id]
    return extraction.model_dump()

@router.get("/api/petitions/{doc_id}")
def get_petition_doc(doc_id: str):
    if doc_id not in _STAGED_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petition {doc_id} not found."}
        )
    return _STAGED_DOCUMENTS[doc_id].model_dump()

@router.get("/api/petitions/{doc_id}/extraction")
def get_petition_extraction(
    doc_id: str,
    session: Session = Depends(get_db_session)
):
    # Si la extracción está en memoria pero requiere re-hidratación desde DB si fue modificada
    if doc_id not in _STAGED_EXTRACTIONS:
        # Intentar recuperar de DB si doc_id es una UUID o sha256 conocido
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petition {doc_id} not found."}
        )
    
    extraction = _STAGED_EXTRACTIONS[doc_id]
    
    # Re-hidratar estados desde PostgreSQL si ya se han guardado revisiones para esa petición
    try:
        if doc_id in _STAGED_DOCUMENTS:
            doc = _STAGED_DOCUMENTS[doc_id]
            petition_repo = PetitionRepository(session)
            file_repo = FileRepository(session)
            file_rec = file_repo.get_by_sha256(doc.sha256)
            if file_rec:
                pet_rec = petition_repo.get_by_file_id(file_rec.id)
                if pet_rec:
                    reviews = petition_repo.get_field_reviews(pet_rec.id)
                    rev_map = {r.field_name: r for r in reviews}
                    for f in extraction.fields:
                        if f.field_name in rev_map:
                            r = rev_map[f.field_name]
                            if r.status in ["CONFIRMED", "CORRECTED_BY_HUMAN", "NOT_FOUND", "NOT_APPLICABLE"]:
                                f.status = FieldStatus(r.status)
                                f.value = r.confirmed_value if r.confirmed_value is not None else f.value
                    if pet_rec.review_status:
                        extraction.review_status = pet_rec.review_status
    except Exception:
        pass

    return extraction.model_dump()

@router.post("/api/petitions/{doc_id}/review")
def submit_human_review(
    doc_id: str,
    req: ReviewSubmitRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/petitions/{doc_id}/review
    Submits human review actions for fields, repeatable lists, and conflicts.
    """
    if doc_id not in _STAGED_EXTRACTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petition {doc_id} not found."}
        )

    service = PetitionService()
    extraction = _STAGED_EXTRACTIONS[doc_id]
    
    # Actualizar listas repetibles si vinieron en la petición
    if req.evidence_items is not None:
        extraction.evidence_items = req.evidence_items
    if req.requested_actions is not None:
        extraction.requested_actions = req.requested_actions
    if req.attachments is not None:
        extraction.attachments = req.attachments

    updated_extraction = service.apply_human_review(extraction, req.actions)
    if len(updated_extraction.conflicts) == 0:
        updated_extraction.review_status = "REVIEW_COMPLETED"
        if doc_id in _STAGED_DOCUMENTS:
            _STAGED_DOCUMENTS[doc_id].processing_status = ProcessingStatus.READY_FOR_DRAFT
    _STAGED_EXTRACTIONS[doc_id] = updated_extraction

    # Actualizar persistencia en PostgreSQL
    audit_repo = AuditRepository(session)
    try:
        if doc_id in _STAGED_DOCUMENTS:
            doc = _STAGED_DOCUMENTS[doc_id]
            filestore = request.app.state.filestore if hasattr(request.app.state, "filestore") else None
            persistence_service = PetitionPersistenceService(session, filestore)
            petition_rec = persistence_service.persist_petition_entity(
                doc=doc,
                extraction=updated_extraction,
                actor="OPERATOR"
            )
            
            # Registrar eventos de auditoría por cada acción
            for act in req.actions:
                evt_type = "petition_field_confirmed" if act.action_type == "CONFIRM" else (
                    "petition_field_corrected" if act.action_type == "CORRECT" else (
                        "petition_field_marked_not_found" if act.action_type == "MARK_NOT_FOUND" else "petition_field_marked_not_applicable"
                    )
                )
                audit_repo.append(
                    actor="OPERATOR",
                    module="PETITION",
                    tool="submit_human_review",
                    tool_version="1.0.0",
                    event_type=evt_type,
                    action=act.action_type,
                    result="SUCCESS",
                    source=doc.stored_relative_path,
                    details={
                        "petition_id": str(petition_rec.id),
                        "field": act.field_name,
                        "new_value": act.new_value
                    }
                )
            
            session.commit()
    except Exception:
        session.rollback()

    return {
        "status": "REVIEW_UPDATED",
        "processing_status": _STAGED_DOCUMENTS[doc_id].processing_status.value if doc_id in _STAGED_DOCUMENTS else "READY_FOR_DRAFT",
        "review_status": updated_extraction.review_status,
        "remaining_conflicts_count": len(updated_extraction.conflicts)
    }

@router.post("/api/petitions/{doc_id}/approve")
def approve_petition(
    doc_id: str,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/petitions/{doc_id}/approve
    Validates completeness and gating rules before setting review_status = APPROVED.
    NO case creation, NO species, NO DSM, NO acquisition.
    """
    if doc_id not in _STAGED_EXTRACTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petitorio {doc_id} no encontrado."}
        )

    extraction = _STAGED_EXTRACTIONS[doc_id]

    # 1. Validar conflictos abiertos
    if len(extraction.conflicts) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "OPEN_CONFLICTS",
                "message": "No se puede aprobar el Oficio Petitorio porque existen conflictos abiertos sin resolver."
            }
        )

    # 2. Validar RUC confirmado / resuelto
    ruc_field = next((f for f in extraction.fields if f.field_name == "ruc"), None)
    if not ruc_field or ruc_field.status not in (FieldStatus.CONFIRMED, FieldStatus.CORRECTED_BY_HUMAN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RUC_UNCONFIRMED",
                "message": "No se puede aprobar el Oficio Petitorio: El RUC debe estar verificado/confirmado por el operador."
            }
        )

    # 3. Validar al menos una NUE válida confirmada
    nue_field = next((f for f in extraction.fields if f.field_name == "nue"), None)
    nue_confirmed = (nue_field and nue_field.status in (FieldStatus.CONFIRMED, FieldStatus.CORRECTED_BY_HUMAN) and nue_field.value)
    has_ev_nue = any(e.nue_number for e in extraction.evidence_items)
    if not (nue_confirmed or has_ev_nue):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "NUE_UNCONFIRMED",
                "message": "No se puede aprobar el Oficio Petitorio: Se requiere al menos una NUE válida confirmada."
            }
        )

    # 4. Validar que no queden campos obligatorios sin revisar
    unreviewed = [f for f in extraction.fields if f.status in (FieldStatus.OBSERVED, FieldStatus.EXTRACTED, FieldStatus.UNCERTAIN, FieldStatus.CONFLICT)]
    if unreviewed:
        unreviewed_names = ", ".join(f.field_name for f in unreviewed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "FIELDS_PENDING_REVIEW",
                "message": f"No se puede aprobar el Oficio Petitorio: Existen campos sin revisar ({unreviewed_names})."
            }
        )

    # Establecer estado aprobado
    extraction.review_status = "APPROVED"
    if doc_id in _STAGED_DOCUMENTS:
        _STAGED_DOCUMENTS[doc_id].processing_status = ProcessingStatus.READY_FOR_DRAFT

    # Persistir en PostgreSQL y registrar auditoría
    audit_repo = AuditRepository(session)
    try:
        if doc_id in _STAGED_DOCUMENTS:
            doc = _STAGED_DOCUMENTS[doc_id]
            filestore = request.app.state.filestore if hasattr(request.app.state, "filestore") else None
            persistence_service = PetitionPersistenceService(session, filestore)
            petition_rec = persistence_service.persist_petition_entity(
                doc=doc,
                extraction=extraction,
                actor="OPERATOR"
            )
            petition_repo = PetitionRepository(session)
            petition_repo.update_review_status(petition_rec.id, "APPROVED")

            audit_repo.append(
                actor="OPERATOR",
                module="PETITION",
                tool="approve_petition",
                tool_version="1.0.0",
                event_type="petition_approved",
                action="APPROVE_PETITION",
                result="SUCCESS",
                source=doc.stored_relative_path,
                details={
                    "petition_id": str(petition_rec.id),
                    "document_id": doc_id,
                    "sha256": doc.sha256
                }
            )
            session.commit()
    except Exception as pe:
        session.rollback()

    return {
        "status": "APPROVED",
        "message": "Oficio Petitorio aprobado exitosamente.",
        "review_status": "APPROVED",
        "processing_status": "READY_FOR_DRAFT"
    }

@router.post("/api/petitions/{doc_id}/draft")
@router.post("/api/petitions/{doc_id}/build-draft")
def build_case_draft(
    doc_id: str,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/petitions/{doc_id}/build-draft
    Generates proposed CaseStructureDraft from APPROVED extraction.
    Verifies RUC duplicate against existing cases, maintains idempotency, and appends audit logs.
    Does NOT auto-create a definitive case in DB.
    """
    if doc_id not in _STAGED_EXTRACTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PETITION_NOT_FOUND", "message": f"Petitorio {doc_id} no encontrado."}
        )

    service = PetitionService()
    extraction = _STAGED_EXTRACTIONS[doc_id]

    # Verify RUC collision against existing cases
    ruc_field = next((f.value for f in extraction.fields if f.field_name == "ruc" and f.value), None)
    if ruc_field:
        from agente_forense.persistence.repositories import CaseRepository
        case_repo = CaseRepository(session)
        existing_case = case_repo.get_by_ruc(ruc_field)
        if existing_case:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "CASE_ALREADY_EXISTS",
                    "message": f"Ya existe un caso registrado con el RUC {ruc_field}. No se sobrescribirán casos existentes en P04."
                }
            )

    try:
        draft = service.build_case_draft(extraction)

        # Audit event for draft generation / reuse
        audit_repo = AuditRepository(session)
        try:
            doc = _STAGED_DOCUMENTS.get(doc_id)
            source_path = doc.stored_relative_path if doc else "STAGING"
            audit_repo.append(
                actor="OPERATOR",
                module="PETITION",
                tool="build_case_draft",
                tool_version="1.0.0",
                event_type="petition_draft_generated",
                action="BUILD_CASE_DRAFT",
                result="SUCCESS",
                source=source_path,
                details={
                    "petition_id": doc_id,
                    "ruc": draft.ruc,
                    "nue_count": len(draft.nues),
                    "petition_sha256": draft.petition_sha256,
                    "status": draft.status
                }
            )
            session.commit()
        except Exception:
            session.rollback()

        return draft.model_dump()
    except PetitionNotReadyForDraftError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "PETITION_NOT_APPROVED", "message": str(e)}
        )
    except PetitionExtractionConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "EXTRACTION_CONFLICT", "message": str(e)}
        )
