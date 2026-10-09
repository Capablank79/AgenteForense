"""
Módulo de interfaz web de Agente Forense.
"""

from agente_forense.web.config import WebConfig
from agente_forense.web.app import create_app

__all__ = ["WebConfig", "create_app"]
