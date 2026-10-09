"""
Interfaces y Mocks de Action Handlers para Sprint R04.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID
from agente_forense.orchestration.context import OrchestrationContext
from agente_forense.orchestration.states import CaseState


@dataclass
class ActionResult:
    success: bool
    target_state: CaseState
    message: str
    details: Dict[str, Any]


class ActionHandler:
    """Interfaz base para handlers de acciones."""

    action_name: str

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        raise NotImplementedError


class StartIdentificationHandler(ActionHandler):
    action_name = "START_IDENTIFICATION"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        return ActionResult(
            success=True,
            target_state=CaseState.IDENTIFICATION_PENDING,
            message="Fase de identificación iniciada.",
            details={"phase": "IDENTIFICATION"},
        )


class CompleteIdentificationHandler(ActionHandler):
    action_name = "COMPLETE_IDENTIFICATION"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        return ActionResult(
            success=True,
            target_state=CaseState.IDENTIFICATION_COMPLETED,
            message="Identificación fotográfica confirmada y completada.",
            details={"identification": "CONFIRMED"},
        )


class CompleteIdentificationMockHandler(ActionHandler):
    action_name = "COMPLETE_IDENTIFICATION_MOCK"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        return ActionResult(
            success=True,
            target_state=CaseState.IDENTIFICATION_COMPLETED,
            message="Identificación mock completada exitosamente.",
            details={"mock_ocr": "COMPLETED", "mock_photographs": "CLASSIFIED"},
        )


class PrepareAcquisitionHandler(ActionHandler):
    action_name = "PREPARE_ACQUISITION"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        return ActionResult(
            success=True,
            target_state=CaseState.ACQUISITION_READY,
            message="Caso listo para adquisición (ACQUISITION_READY).",
            details={"acquisition_plan": "READY_STUB"},
        )


class AbortCaseHandler(ActionHandler):
    action_name = "ABORT_CASE"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        reason = payload.get("reason", "Cancelación manual por el operador.") if payload else "Cancelación manual."
        return ActionResult(
            success=True,
            target_state=CaseState.ABORTED,
            message=f"Caso abortado. Motivo: {reason}",
            details={"abort_reason": reason},
        )


class FailCaseHandler(ActionHandler):
    action_name = "FAIL_CASE"

    def execute(self, ctx: OrchestrationContext, payload: Optional[Dict[str, Any]] = None) -> ActionResult:
        error_code = payload.get("error_code", "ORCHESTRATION_FAILURE") if payload else "ORCHESTRATION_FAILURE"
        return ActionResult(
            success=True,
            target_state=CaseState.FAILED,
            message=f"Caso marcado como FAILED. Error: {error_code}",
            details={"failed_action": payload.get("failed_action") if payload else None, "error_code": error_code},
        )
