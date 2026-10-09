"""
Modelo de errores uniforme y manejadores HTTP.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("agente_forense.web")

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str
    details_safe: Dict[str, Any] = Field(default_factory=dict)

async def agente_forense_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[%s] Error no capturado: %s", request_id, str(exc), exc_info=True)
    
    body = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="Ha ocurrido un error interno seguro en la aplicación web.",
        request_id=request_id,
        details_safe={}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body.model_dump()
    )
