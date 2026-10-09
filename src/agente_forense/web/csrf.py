"""
Middleware para protección CSRF con patrón Double Submit Cookie o Header validation.
"""

import hmac
import secrets
import hashlib
from typing import Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


import logging

logger = logging.getLogger("agente_forense.web.csrf")

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
CSRF_FORM_NAME = "csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str = "forensic-csrf-secret-key-r03"):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        
        new_token_generated = False
        if not cookie_token:
            cookie_token = generate_csrf_token()
            new_token_generated = True

        # Si el método altera estado (POST, PUT, DELETE, PATCH)
        if request.method not in SAFE_METHODS and not getattr(request.state, "skip_csrf", False):
            header_token = request.headers.get(CSRF_HEADER_NAME)
            
            form_token = None
            if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                try:
                    form_data = await request.form()
                    form_token = form_data.get(CSRF_FORM_NAME)
                except Exception:
                    pass

            submitted_token = header_token or form_token

            csrf_cookie_present = cookie_token is not None
            csrf_header_present = submitted_token is not None
            csrf_match = bool(submitted_token and cookie_token and hmac.compare_digest(submitted_token, cookie_token))

            logger.info(
                f"csrf_cookie_present={csrf_cookie_present} "
                f"csrf_header_present={csrf_header_present} "
                f"csrf_match={csrf_match} "
                f"request_path={request.url.path} "
                f"method={request.method}"
            )

            # Validación estricta CSRF para peticiones mutantes
            if not csrf_match:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error_code": "CSRF_ERROR", "message": "Token CSRF inválido o ausente."}
                )

        response = await call_next(request)

        # Garantizar que el cookie csrf_token siempre esté presente en la respuesta si no existía previamente o para refrescar directivas
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=cookie_token,
            httponly=False,  # Permitir lectura por JS para patrón Double Submit Cookie
            samesite="lax",
            secure=False,  # HTTP local dev
            path="/"
        )

        return response
