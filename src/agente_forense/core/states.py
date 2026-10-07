"""
Estados base del sistema.
"""

from enum import Enum


class SystemState(Enum):
    """Estados fundamentales del ciclo de vida del sistema."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
