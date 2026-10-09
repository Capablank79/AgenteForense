"""
Excepciones y errores específicos del dominio de Agente Forense.
"""

from agente_forense.core.errors import AgenteForenseError


class DomainError(AgenteForenseError):
    """Error general de regla de dominio."""
    pass


class InvalidRUCError(DomainError):
    """RUC no cumple con validaciones sintácticas/seguridad."""
    pass


class InvalidNUEError(DomainError):
    """NUE no cumple con validaciones sintácticas/seguridad."""
    pass


class CaseAlreadyExistsError(DomainError):
    """El RUC ya existe en el sistema."""
    pass


class DuplicateNUEError(DomainError):
    """Existe una NUE duplicada dentro del mismo RUC."""
    pass


class DuplicateSpeciesError(DomainError):
    """Existe una Especie duplicada dentro de la misma NUE."""
    pass


class DuplicateDSMError(DomainError):
    """Existe un DSM duplicado dentro de la misma Especie."""
    pass


class InvalidStorageTopologyError(DomainError):
    """Topología física/lógica inválida (ej. SELF_STORAGE con >1 DSM o 0 DSM)."""
    pass


class StructureComparisonConflictError(DomainError):
    """Error cuando existen conflictos no resueltos entre la extracción y la inspección física."""
    pass


class ReconciliationError(DomainError):
    """Error durante la reconciliación entre DB y case.json."""
    pass
