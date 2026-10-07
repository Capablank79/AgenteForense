"""
Excepciones base de Agente Forense.
"""


class AgenteForenseError(Exception):
    """Excepción base para todos los errores de Agente Forense."""

    pass


class ConfigurationError(AgenteForenseError):
    """Excepción para errores de configuración de rutas o entorno."""

    pass


class SafetyViolationError(AgenteForenseError):
    """Excepción para violaciones de seguridad forense (ej: fail-closed)."""

    pass
