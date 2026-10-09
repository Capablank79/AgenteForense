"""
Contenedores de contexto para la evaluación de políticas de orquestación.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from uuid import UUID
from agente_forense.orchestration.states import CaseState


@dataclass
class OrchestrationContext:
    case_id: UUID
    current_state: CaseState
    state_version: int
    case_data: Dict[str, Any] = field(default_factory=dict)
    nues: List[Dict[str, Any]] = field(default_factory=list)
    species: List[Dict[str, Any]] = field(default_factory=list)
    dsms: List[Dict[str, Any]] = field(default_factory=list)
    case_json_data: Optional[Dict[str, Any]] = None
    case_json_exists: bool = False
    case_json_valid: bool = False
    reconciliation_match: bool = True
    critical_reconciliation_errors: List[str] = field(default_factory=list)
    selected_dsm_id: Optional[UUID] = None
    disk_binding_data: Optional[Dict[str, Any]] = None
    active_disk_snapshot: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    @property
    def disk_binding_confirmed(self) -> bool:
        return self.disk_binding_data is not None and self.disk_binding_data.get("status") == "CONFIRMED"

    @property
    def source_read_only(self) -> bool:
        if self.active_disk_snapshot:
            return self.active_disk_snapshot.get("is_read_only") is True
        return False
