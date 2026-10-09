"""
App Factory principal de FastAPI.
"""

from typing import Optional
import uuid
import time
import logging

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles

from agente_forense.web.config import WebConfig
from agente_forense.web.errors import agente_forense_exception_handler
from agente_forense.web.routes import (
    pages, api_health, api_cases, api_audit, api_files, api_petitions, api_identification, api_hardware, api_acquisition
)
from agente_forense.web.csrf import CSRFMiddleware

logger = logging.getLogger("agente_forense.web")

def create_app(config: Optional[WebConfig] = None) -> FastAPI:
    web_config = config or WebConfig()
    web_config.validate()

    app = FastAPI(
        title="AGENTE FORENSE Web API",
        version="0.3.0",
        docs_url=None,  # Deshabilitar Swagger UI expuesto públicamente por seguridad por defecto
        redoc_url=None
    )
    app.state.web_config = web_config

    # Middleware CSRF Real
    app.add_middleware(CSRFMiddleware)

    # Middleware: Request ID, Logging estructurado y Security Headers
    @app.middleware("http")
    async def middleware_request_lifecycle(request: Request, call_next):
        req_id = str(uuid.uuid4())
        request.state.request_id = req_id
        start_time = time.time()

        response: Response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"request_id={req_id} method={request.method} path={request.url.path} "
            f"status={response.status_code} duration={duration:.4f}s"
        )

        # Security Headers obligatorios
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cache-Control no-store para endpoints sensibles de API y casos
        path_str = request.url.path
        if path_str.startswith("/api/") or path_str.startswith("/cases") or path_str.startswith("/audit"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        return response

    # Exception Handlers uniformes
    app.add_exception_handler(Exception, agente_forense_exception_handler)

    # Incluir routers
    app.include_router(pages.router)
    app.include_router(api_health.router)
    app.include_router(api_cases.router)
    app.include_router(api_audit.router)
    app.include_router(api_files.router)
    app.include_router(api_petitions.router)
    app.include_router(api_identification.router)
    app.include_router(api_hardware.router)
    app.include_router(api_acquisition.router)

    return app
