"""
Rutas HTML para navegación Web con Jinja2.
"""

from typing import Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.persistence.repositories import CaseRepository, AuditRepository, NueRepository
from agente_forense.persistence.config import DatabaseConfig
from agente_forense.web.config import WebConfig
from agente_forense.persistence.models import AuditEventModel, CaseEventModel
from agente_forense.orchestration import CaseOrchestrator
from agente_forense.orchestration.human_gate import HumanGate

from agente_forense.hardware.write_blockers import WriteBlockerService
from agente_forense.acquisition.capabilities import EwfBinaryVerifier

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request, session: Session = Depends(get_db_session)):
    case_repo = CaseRepository(session)
    cases = case_repo.list_all()
    
    db_status = "ok"
    recent_events = []
    pending_confirmations_count = 0
    wb_detected = 0
    ro_media_count = 0
    active_bindings_count = 0
    
    try:
        recent_events = session.query(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(5).all()
        from agente_forense.persistence.models import HumanConfirmationModel
        from agente_forense.hardware.bindings import DsmDiskBindingModel
        pending_confirmations_count = session.query(HumanConfirmationModel).filter(HumanConfirmationModel.status == "PENDING").count()
        
        wb_service = WriteBlockerService(session)
        topo = wb_service.get_topology_summary()
        wb_detected = len(topo.channels)
        ro_media_count = sum(1 for a in topo.attachments if a.is_read_only)
        active_bindings_count = session.query(DsmDiskBindingModel).filter(DsmDiskBindingModel.status == "CONFIRMED").count()
    except Exception as e:
        import logging
        logging.error(f"Dashboard Exception: {e}", exc_info=True)
        db_status = "error"

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": "AGENTE FORENSE",
            "db_status": db_status,
            "cases_count": len(cases),
            "cases": cases,
            "pending_confirmations_count": pending_confirmations_count,
            "recent_events": recent_events,
            "wb_detected": wb_detected,
            "ro_media_count": ro_media_count,
            "active_bindings_count": active_bindings_count,
        }
    )

@router.get("/cases", response_class=HTMLResponse)
def page_cases(request: Request, session: Session = Depends(get_db_session)):
    case_repo = CaseRepository(session)
    cases = case_repo.list_all()
    return templates.TemplateResponse(
        request=request,
        name="cases.html",
        context={
            "cases": cases
        }
    )

@router.get("/cases/new", response_class=HTMLResponse)
def page_case_new(request: Request):
    return templates.TemplateResponse(request=request, name="case_new.html")

@router.get("/cases/{case_id}", response_class=HTMLResponse)
def page_case_detail(case_id: UUID, request: Request, session: Session = Depends(get_db_session)):
    case_repo = CaseRepository(session)
    case = case_repo.get_by_id(case_id)
    if not case:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "error_code": "CASE_NOT_FOUND",
                "message": f"Caso {case_id} no encontrado."
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    nue_repo = NueRepository(session)
    nues = nue_repo.list_by_case(case_id)

    orchestrator = CaseOrchestrator(session)
    ctx = orchestrator.build_context(case_id)
    allowed_actions = orchestrator.get_allowed_actions(case_id)

    gate = HumanGate(session)
    pending_confirmations = gate.get_pending_by_case(case_id)

    case_events = session.query(CaseEventModel).filter(CaseEventModel.case_id == case_id).order_by(CaseEventModel.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="case_detail.html",
        context={
            "case": case,
            "nues": nues,
            "orchestration_context": ctx,
            "allowed_actions": allowed_actions,
            "pending_confirmations": pending_confirmations,
            "case_events": case_events,
        }
    )

@router.get("/hardware", response_class=HTMLResponse)
def page_hardware(request: Request, session: Session = Depends(get_db_session)):
    wb_service = WriteBlockerService(session)
    topology = wb_service.get_topology_summary()
    
    # Emparejar canales con sus adjuntos
    card_items = []
    for channel in topology.channels:
        attachment = next((a for a in topology.attachments if a.blocker_id == channel.blocker_id), None)
        card_items.append({
            "channel": channel,
            "attachment": attachment
        })
        
    return templates.TemplateResponse(
        request=request,
        name="hardware.html",
        context={
            "card_items": card_items,
            "unresolved_disks": topology.unresolved_disks
        }
    )

@router.get("/acquisitions", response_class=HTMLResponse)
def page_acquisitions(request: Request, session: Session = Depends(get_db_session)):
    from agente_forense.persistence.models import AcquisitionJobModel
    jobs = session.query(AcquisitionJobModel).order_by(AcquisitionJobModel.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="acquisitions.html",
        context={
            "jobs": jobs
        }
    )
@router.get("/audit", response_class=HTMLResponse)
def page_audit(request: Request, session: Session = Depends(get_db_session)):
    events = session.query(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        request=request,
        name="audit.html",
        context={
            "events": events
        }
    )

@router.get("/system", response_class=HTMLResponse)
def page_system(request: Request, session: Session = Depends(get_db_session)):
    db_config = DatabaseConfig()
    web_config = WebConfig()

    ewf_info = {"status": "UNKNOWN", "hash": None, "path": None}
    wb_count = 0
    last_scan = None
    try:
        verifier = EwfBinaryVerifier()
        caps = verifier.verify()
        ewf_info = {
            "status": caps.verification_status,
            "hash": caps.sha256_hash,
            "path": caps.binary_path,
            "version": caps.version
        }
        wb_service = WriteBlockerService(session)
        topo = wb_service.get_topology_summary()
        wb_count = len(topo.channels)
        if topo.channels:
            last_scan = max(c.observed_at for c in topo.channels)
    except Exception:
        pass

    return templates.TemplateResponse(
        request=request,
        name="system.html",
        context={
            "app_version": "0.3.0",
            "web_host": web_config.host,
            "web_port": web_config.port,
            "db_host": db_config.host,
            "db_port": db_config.port,
            "db_name": db_config.db_name,
            "db_user": db_config.user,
            "ewf_info": ewf_info,
            "wb_count": wb_count,
            "last_scan": last_scan
        }
    )


@router.get("/petitions", response_class=HTMLResponse)
def get_petitions_page(request: Request):
    """
    Renders the petitions review & upload page.
    """
    return templates.TemplateResponse("petitions.html", {"request": request})


@router.get("/cases/physical-structure", response_class=HTMLResponse)
def get_physical_structure_page(request: Request):
    """
    Renders the physical structure confirmation page (P05).
    """
    return templates.TemplateResponse("physical_structure.html", {"request": request})
