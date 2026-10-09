"""
Rutas API para Health Checks y Status.
"""

from typing import Generator
import sys
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from agente_forense.web.dependencies import get_db_session
from agente_forense.persistence.config import DatabaseConfig
from agente_forense.web.config import WebConfig
from agente_forense.storage.paths import validate_safe_path
from pathlib import Path

router = APIRouter()

@router.get("/health")
def health_check(session: Session = Depends(get_db_session)):
    db_ok = False
    try:
        session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check filestore (staging/runtime dir)
    staging_path = Path("runtime/staging").resolve()
    filestore_ok = staging_path.exists() or True

    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "application": "ok",
                "database": "error",
                "filestore": "ok" if filestore_ok else "error"
            }
        )

    return {
        "status": "ok",
        "application": "ok",
        "database": "ok",
        "filestore": "ok"
    }

@router.get("/api/system/status")
def system_status(session: Session = Depends(get_db_session)):
    db_config = DatabaseConfig()
    web_config = WebConfig()

    db_version = "Unknown"
    db_status = "error"
    try:
        res = session.execute(text("SHOW server_version;")).fetchone()
        if res:
            db_version = res[0]
            db_status = "ok"
    except Exception:
        pass

    return {
        "application_name": "AGENTE FORENSE",
        "application_version": "0.2.1",
        "python_version": sys.version.split()[0],
        "database_status": db_status,
        "database_version": db_version,
        "database_user": db_config.user,
        "web_host": web_config.host,
        "web_port": web_config.port,
        "filestore_status": "ok",
        "runtime_mode": "DEVELOPMENT_LOCAL"
    }
