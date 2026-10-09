"""
Módulo para la comparación lado a lado entre datos declarados en Petitorio (Petition)
y la inspección física (Physical Inspection) para P05.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class ComparisonStatus(str, Enum):
    MATCH = "MATCH"
    CONFLICT = "CONFLICT"
    NOT_OBSERVABLE = "NOT_OBSERVABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class FieldComparison:
    field_name: str
    declared_value: Optional[str]
    observed_value: Optional[str]
    status: ComparisonStatus
    details: Optional[str] = None


@dataclass
class ItemComparisonResult:
    nue_number: str
    species_number: Optional[int] = None
    dsm_number: Optional[int] = None
    comparisons: List[FieldComparison] = None
    has_conflicts: bool = False

    def __post_init__(self):
        if self.comparisons is None:
            self.comparisons = []
        self.has_conflicts = any(c.status == ComparisonStatus.CONFLICT for c in self.comparisons)


def compare_text_fields(field_name: str, declared: Optional[str], observed: Optional[str]) -> FieldComparison:
    """
    Compara dos valores de texto (declarado vs observado).
    - Si ambos son Nulos o Vacíos -> NOT_APPLICABLE
    - Si declarado tiene valor y observado no -> NOT_OBSERVABLE
    - Si ambos existen y son iguales (case-insensitive strip) -> MATCH
    - Si difieren -> CONFLICT
    """
    decl_clean = declared.strip() if declared and declared.strip() else None
    obs_clean = observed.strip() if observed and observed.strip() else None

    if not decl_clean and not obs_clean:
        return FieldComparison(field_name, declared, observed, ComparisonStatus.NOT_APPLICABLE)

    if decl_clean and not obs_clean:
        return FieldComparison(
            field_name, declared, observed, ComparisonStatus.NOT_OBSERVABLE,
            details="Valor declarado en petitorio pero no observado en la inspección física."
        )

    if not decl_clean and obs_clean:
        return FieldComparison(
            field_name, declared, observed, ComparisonStatus.MATCH,
            details="Observado en inspección física (sin dato previo en petitorio)."
        )

    if decl_clean.lower() == obs_clean.lower():
        return FieldComparison(field_name, declared, observed, ComparisonStatus.MATCH)
    else:
        return FieldComparison(
            field_name, declared, observed, ComparisonStatus.CONFLICT,
            details=f"Incongruencia entre lo declarado ('{decl_clean}') y lo observado ('{obs_clean}')."
        )
