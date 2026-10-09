"""
Rutas API para Auditoría.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agente_forense.web.dependencies import get_db_session
from agente_forense.persistence.models import AuditEventModel

router = APIRouter()

@router.get("/api/audit")
def list_audit_events_json(session: Session = Depends(get_db_session)):
    events = session.query(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(100).all()
    
    return [
        {
            "id": str(e.id),
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "actor": e.actor,
            "module": e.module,
            "tool": e.tool,
            "event_type": e.event_type,
            "action": e.action,
            "result": e.result,
            "case_id": str(e.case_id) if e.case_id else None,
            "error": e.error
        }
        for e in events
    ]
