"""
Configuración de conexión a PostgreSQL.
"""

import os
from pathlib import Path
from typing import Optional
from agente_forense.core.errors import ConfigurationError


class DatabaseConfig:
    """Configuración explícita de base de datos PostgreSQL."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        env_file: Optional[Path] = None,
    ):
        # Intentar cargar variables desde .env si existe
        if env_file is None:
            env_file = Path.cwd() / ".env"

        env_vars = {}
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()

        self.host = host or os.getenv("AGENTE_FORENSE_DB_HOST") or env_vars.get("AGENTE_FORENSE_DB_HOST") or "127.0.0.1"
        
        raw_port = port or os.getenv("AGENTE_FORENSE_DB_PORT") or env_vars.get("AGENTE_FORENSE_DB_PORT") or 5433
        self.port = int(raw_port)

        self.db_name = db_name or os.getenv("AGENTE_FORENSE_DB_NAME") or env_vars.get("AGENTE_FORENSE_DB_NAME") or "agente_forense_db"
        self.user = user or os.getenv("AGENTE_FORENSE_DB_USER") or env_vars.get("AGENTE_FORENSE_DB_USER") or "agente_forense_app"

        self.password = password or os.getenv("AGENTE_FORENSE_DB_PASSWORD") or env_vars.get("AGENTE_FORENSE_DB_PASSWORD")

        if not self.password:
            raise ConfigurationError("AGENTE_FORENSE_DB_PASSWORD es obligatorio y no tiene valor por defecto.")

        if self.port == 5432:
            raise ConfigurationError("El puerto 5432 está reservado para la instancia legacy. Se debe usar el puerto 5433.")

        if os.getenv("ENVIRONMENT") == "TEST" or os.getenv("PYTEST_CURRENT_TEST"):
            if "test" not in self.db_name.lower():
                raise ConfigurationError(
                    f"SEGURIDAD DE PERSISTENCIA: Se intentó ejecutar tests conectándose a la BD de producción/operación '{self.db_name}'. "
                    f"Los tests deben conectarse exclusivamente a una base de datos con nombre conteniendo 'test' (ej: agente_forense_test)."
                )

    @property
    def connection_string(self) -> str:
        """Devuelve el DSN de conexión en formato SQLAlchemy / psycopg."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
