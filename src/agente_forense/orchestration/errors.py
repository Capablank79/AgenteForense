"""
Excepciones de la capa de orquestación.
"""

from agente_forense.core.errors import AgenteForenseError


class OrchestrationError(AgenteForenseError):
    """Excepción base para errores de orquestación."""
    pass


class InvalidTransitionError(OrchestrationError):
    """Transición de estado no permitida o desconocida."""
    pass


class PolicyDeniedError(OrchestrationError):
    """Una o más políticas denegaron la ejecución de la acción."""
    pass


class ConfirmationRequiredError(OrchestrationError):
    """La acción requiere confirmación humana antes de ejecutarse."""
    def __init__(self, message: str, confirmation_id: str):
        super().__init__(message)
        self.confirmation_id = confirmation_id


class ConfirmationNotFoundError(OrchestrationError):
    """La confirmación humana especificada no existe."""
    pass


class ConfirmationAlreadyResolvedError(OrchestrationError):
    """La confirmación humana ya fue aceptada, rechazada o expirada."""
    pass


class ConcurrencyConflictError(OrchestrationError):
    """El estado o versionamiento del caso cambió concurrentemente."""
    pass


class OrchestrationPersistenceError(OrchestrationError):
    """Fallo en la persistencia de estado, eventos o case.json durante la orquestación."""
    pass
