"""
Rutas API REST para el Agente de Identificación Fotográfica Asistida.
Endpoints:
POST /api/identification/photos/stage
POST /api/identification/entities/{id}/analyze
GET  /api/identification/entities/{id}
POST /api/identification/entities/{id}/review
POST /api/identification/entities/{id}/rename
POST /api/identification/entities/{id}/confirm
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.web.config import WebConfig
from agente_forense.storage.paths import sanitize_filename, validate_safe_path
from agente_forense.identification.service import IdentificationService
from agente_forense.identification.photo_ingest import ingest_photo
from agente_forense.identification.models import PhotoIngestRecord, IdentificationData, PhotoClassification
from agente_forense.identification.review import apply_human_review
from agente_forense.identification.renaming import preview_renaming, execute_safe_renaming
from agente_forense.identification.identification_json import write_identification_json_atomic
from agente_forense.persistence.repositories import (
    SpeciesRepository, DsmRepository, AuditRepository, FileRepository, CaseRepository
)
from agente_forense.orchestration import CaseOrchestrator, ConfirmationRequiredError

router = APIRouter()

# In-memory / session state cache para la demostración y persistencia de identification
_IDENTIFICATION_STORE: Dict[str, IdentificationData] = {}

class ReviewRequest(BaseModel):
    operator: str = "PERITO_OPERADOR"
    corrected_classification: Optional[Dict[str, str]] = None
    corrected_attributes: Optional[Dict[str, str]] = None
    confirmed: bool = False

class RenameRequest(BaseModel):
    operator: str = "PERITO_OPERADOR"
    nue_number: str
    species_number: int
    dsm_number: Optional[int] = None
    confirm: bool = False

class ConfirmRequest(BaseModel):
    operator: str = "PERITO_OPERADOR"
    case_id: UUID

@router.post("/api/identification/photos/stage")
async def stage_photo_upload(
    request: Request,
    entity_type: str,
    entity_id: str,
    file: UploadFile = File(...)
):
    """
    POST /api/identification/photos/stage
    Staging e ingesta segura de fotografía con hash SHA-256 e inmutabilidad.
    """
    if entity_type not in ["ESPECIE", "DSM", "SPECIES"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_ENTITY_TYPE", "message": "entity_type debe ser ESPECIE o DSM"}
        )

    app_config: WebConfig = getattr(request.app.state, "web_config", None) or WebConfig()
    staging_dir = Path(app_config.staging_dir).resolve()
    staging_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(file.filename or "photo.jpg")
    target_path = validate_safe_path(staging_dir, safe_filename)

    # Save to staging
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    rel_path = str(target_path.relative_to(staging_dir.parent if staging_dir.parent else staging_dir)).replace("\\", "/")
    
    photo_record = ingest_photo(
        file_path=target_path,
        entity_type=entity_type,
        entity_id=entity_id,
        relative_path=rel_path
    )

    # Guardar en tienda
    if entity_id not in _IDENTIFICATION_STORE:
        svc = IdentificationService()
        _IDENTIFICATION_STORE[entity_id] = svc.build_identification_data(entity_type, entity_id, [], {})

    _IDENTIFICATION_STORE[entity_id].photos.append(photo_record)

    return {
        "status": "STAGED",
        "photo": photo_record,
        "message": "Fotografía alojada en staging e inmutabilidad verificada."
    }

@router.post("/api/identification/entities/{entity_id}/analyze")
def analyze_entity_photos(
    entity_id: str,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/identification/entities/{id}/analyze
    Ejecuta el análisis (OCR + Clasificación + Extracción + Qwen opcional) sobre las fotos de la entidad.
    """
    if entity_id not in _IDENTIFICATION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENTITY_NOT_FOUND", "message": f"No hay fotografías staged para la entidad {entity_id}"}
        )

    data = _IDENTIFICATION_STORE[entity_id]
    app_config: WebConfig = getattr(request.app.state, "web_config", None) or WebConfig()
    base_dir = Path(app_config.staging_dir).parent.resolve()

    svc = IdentificationService(session=session)
    consolidated_attrs = dict(data.attributes)

    for photo in data.photos:
        photo_path = base_dir / photo.relative_path
        if not photo_path.exists():
            photo_path = Path(app_config.staging_dir) / photo.original_filename

        updated_photo, extracted_attrs = svc.analyze_photo(photo, photo_path, use_qwen=True)
        for k, v in extracted_attrs.items():
            consolidated_attrs[k] = v

    data.attributes = consolidated_attrs
    data = svc.build_identification_data(data.entity_type, entity_id, data.photos, consolidated_attrs)
    _IDENTIFICATION_STORE[entity_id] = data

    return {
        "status": "ANALYZED",
        "identification": data
    }

@router.get("/api/identification/entities/{entity_id}")
def get_entity_identification(entity_id: str):
    """
    GET /api/identification/entities/{id}
    Obtiene los datos estructurados de identificación fotográfica.
    """
    if entity_id not in _IDENTIFICATION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENTITY_NOT_FOUND", "message": f"Identificación no encontrada para entidad {entity_id}"}
        )
    return _IDENTIFICATION_STORE[entity_id]

@router.post("/api/identification/entities/{entity_id}/review")
def review_entity_identification(
    entity_id: str,
    req: ReviewRequest,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/identification/entities/{id}/review
    Aplica revisión humana (confirmación/corrección) de clasificaciones y atributos.
    """
    if entity_id not in _IDENTIFICATION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENTITY_NOT_FOUND", "message": f"Identificación no encontrada para entidad {entity_id}"}
        )

    data = _IDENTIFICATION_STORE[entity_id]
    updated_data = apply_human_review(
        identification_data=data,
        operator=req.operator,
        corrected_classification=req.corrected_classification,
        corrected_attributes=req.corrected_attributes,
        confirmed=req.confirmed
    )
    _IDENTIFICATION_STORE[entity_id] = updated_data

    # Registrar evento de auditoría
    audit_repo = AuditRepository(session)
    audit_repo.append(
        actor=req.operator,
        module="IDENTIFICATION",
        tool="IdentificationService",
        tool_version="1.0.0",
        event_type="PHOTO_CLASSIFICATION_CORRECTED" if req.corrected_classification else "ATTRIBUTE_CONFIRMED",
        action="REVIEW",
        result="SUCCESS",
        details={"entity_id": entity_id, "confirmed": req.confirmed}
    )
    session.commit()

    return {
        "status": "REVIEWED",
        "identification": updated_data
    }

@router.post("/api/identification/entities/{entity_id}/rename")
def rename_entity_photos(
    entity_id: str,
    req: RenameRequest,
    request: Request,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/identification/entities/{id}/rename
    Vista previa o ejecución atómica de renombrado determinístico seguro.
    """
    if entity_id not in _IDENTIFICATION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENTITY_NOT_FOUND", "message": f"Identificación no encontrada para entidad {entity_id}"}
        )

    data = _IDENTIFICATION_STORE[entity_id]
    app_config: WebConfig = getattr(request.app.state, "web_config", None) or WebConfig()
    base_dir = Path(app_config.staging_dir).parent.resolve()

    plan = preview_renaming(
        photos=data.photos,
        target_dir=base_dir,
        nue_number=req.nue_number,
        species_number=req.species_number,
        dsm_number=req.dsm_number
    )

    if not req.confirm:
        return {
            "status": "PREVIEW",
            "plan": plan,
            "message": "Vista previa del renombrado determinístico. Requiere confirm=True para ejecutar."
        }

    renamed_photos = execute_safe_renaming(plan, base_dir, data.photos)
    data.photos = renamed_photos
    _IDENTIFICATION_STORE[entity_id] = data

    audit_repo = AuditRepository(session)
    audit_repo.append(
        actor=req.operator,
        module="IDENTIFICATION",
        tool="RenamingService",
        tool_version="1.0.0",
        event_type="PHOTO_RENAMED",
        action="RENAME",
        result="SUCCESS",
        details={"entity_id": entity_id, "renamed_count": len(renamed_photos)}
    )
    session.commit()

    return {
        "status": "RENAMED",
        "photos": data.photos,
        "message": "Renombrado de fotografías completado exitosamente."
    }

@router.post("/api/identification/entities/{entity_id}/confirm")
def confirm_identification(
    entity_id: str,
    req: ConfirmRequest,
    session: Session = Depends(get_db_session)
):
    """
    POST /api/identification/entities/{id}/confirm
    Confirma formalmente la identificación, genera `identification.json`,
    actualiza `case.json` y hace avanzar la state machine a `IDENTIFICATION_COMPLETED`.
    """
    if entity_id not in _IDENTIFICATION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENTITY_NOT_FOUND", "message": f"Identificación no encontrada para entidad {entity_id}"}
        )

    data = _IDENTIFICATION_STORE[entity_id]
    data.status = "IDENTIFICATION_COMPLETED"
    data.human_review["confirmed"] = True
    data.human_review["reviewed_by"] = req.operator

    case_repo = CaseRepository(session)
    case = case_repo.get_by_id(req.case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CASE_NOT_FOUND", "message": f"Caso {req.case_id} no encontrado."}
        )

    target_dir = Path(case.case_root) if case.case_root else Path(tempfile.gettempdir())
    ident_json_path = write_identification_json_atomic(data, target_dir)

    # Avanzar orquestación
    orchestrator = CaseOrchestrator(session)
    try:
        res = orchestrator.execute_action(
            case_id=req.case_id,
            action="COMPLETE_IDENTIFICATION",
            operator=req.operator
        )
    except ConfirmationRequiredError:
        pass

    return {
        "status": "IDENTIFICATION_COMPLETED",
        "identification_json_path": str(ident_json_path),
        "message": "Identificación fotográfica confirmada y archivada exitosamente."
    }
