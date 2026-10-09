"""
Módulo de orquestación para Agente Forense.
"""

from agente_forense.orchestration.states import CaseState, OperativeState, ReservedState
from agente_forense.orchestration.orchestrator import CaseOrchestrator, AllowedActionInfo
from agente_forense.orchestration.policies import PolicyEngine, PolicyDecision, PolicyResult
from agente_forense.orchestration.human_gate import HumanGate, ConfirmationStatus, HumanConfirmationRecord
from agente_forense.orchestration.errors import (
    OrchestrationError,
    InvalidTransitionError,
    PolicyDeniedError,
    ConfirmationRequiredError,
    ConfirmationNotFoundError,
    ConfirmationAlreadyResolvedError,
    ConcurrencyConflictError,
    OrchestrationPersistenceError,
)

__all__ = [
    "CaseState",
    "OperativeState",
    "ReservedState",
    "CaseOrchestrator",
    "AllowedActionInfo",
    "PolicyEngine",
    "PolicyDecision",
    "PolicyResult",
    "HumanGate",
    "ConfirmationStatus",
    "HumanConfirmationRecord",
    "OrchestrationError",
    "InvalidTransitionError",
    "PolicyDeniedError",
    "ConfirmationRequiredError",
    "ConfirmationNotFoundError",
    "ConfirmationAlreadyResolvedError",
    "ConcurrencyConflictError",
    "OrchestrationPersistenceError",
]
