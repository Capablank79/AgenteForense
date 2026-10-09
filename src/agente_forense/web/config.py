"""
Configuración de la plataforma Web.
"""

import os
from typing import Optional
from dataclasses import dataclass
from agente_forense.core.errors import SafetyViolationError

VALID_HOSTS = {"127.0.0.1", "localhost"}

@dataclass
class WebConfig:
    host: str = "127.0.0.1"
    port: int = 8085
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB default conservador
    staging_dir: Optional[str] = None

    def __post_init__(self):
        env_host = os.environ.get("AGENTE_FORENSE_WEB_HOST")
        if env_host:
            self.host = env_host

        env_port = os.environ.get("AGENTE_FORENSE_WEB_PORT")
        if env_port:
            try:
                self.port = int(env_port)
            except ValueError:
                pass

        env_max = os.environ.get("AGENTE_FORENSE_MAX_UPLOAD_BYTES")
        if env_max:
            try:
                self.max_upload_bytes = int(env_max)
            except ValueError:
                pass

        self.validate()

    def validate(self):
        if self.host not in VALID_HOSTS:
            raise SafetyViolationError(
                f"Binding web no autorizado: '{self.host}'. Solo se permite binding en loopback (127.0.0.1 / localhost)."
            )
        if self.port <= 0 or self.port > 65535:
            raise SafetyViolationError(f"Puerto web inválido: {self.port}")
