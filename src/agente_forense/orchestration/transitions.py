"""
Definición de transiciones legales entre estados.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from agente_forense.orchestration.states import CaseState, OperativeState, ReservedState


@dataclass(frozen=True)
class TransitionSpec:
    source_state: CaseState
    target_state: CaseState
    action: str
    preconditions: List[str]
    policy_checks: List[str]
    requires_human_confirmation: bool
    audit_event: str


# Registro global de transiciones válidas
LEGAL_TRANSITIONS: Dict[str, TransitionSpec] = {
    "START_IDENTIFICATION": TransitionSpec(
        source_state=CaseState.NEW,
        target_state=CaseState.IDENTIFICATION_PENDING,
        action="START_IDENTIFICATION",
        preconditions=["CASE_EXISTS"],
        policy_checks=["CASE_STRUCTURE_VALID", "STATE_TRANSITION_ALLOWED"],
        requires_human_confirmation=False,
        audit_event="IDENTIFICATION_STARTED",
    ),
    "COMPLETE_IDENTIFICATION": TransitionSpec(
        source_state=CaseState.IDENTIFICATION_PENDING,
        target_state=CaseState.IDENTIFICATION_COMPLETED,
        action="COMPLETE_IDENTIFICATION",
        preconditions=["CASE_EXISTS", "HAS_NUE", "HAS_SPECIES"],
        policy_checks=["CASE_STRUCTURE_VALID", "STATE_TRANSITION_ALLOWED"],
        requires_human_confirmation=True,
        audit_event="IDENTIFICATION_CONFIRMED",
    ),
    "COMPLETE_IDENTIFICATION_MOCK": TransitionSpec(
        source_state=CaseState.IDENTIFICATION_PENDING,
        target_state=CaseState.IDENTIFICATION_COMPLETED,
        action="COMPLETE_IDENTIFICATION_MOCK",
        preconditions=["CASE_EXISTS", "HAS_NUE", "HAS_SPECIES"],
        policy_checks=["CASE_STRUCTURE_VALID", "STATE_TRANSITION_ALLOWED"],
        requires_human_confirmation=False,
        audit_event="IDENTIFICATION_COMPLETED",
    ),
    "PREPARE_ACQUISITION": TransitionSpec(
        source_state=CaseState.IDENTIFICATION_COMPLETED,
        target_state=CaseState.ACQUISITION_READY,
        action="PREPARE_ACQUISITION",
        preconditions=["CASE_EXISTS", "HAS_NUE", "HAS_SPECIES", "HAS_DSM"],
        policy_checks=[
            "CASE_STRUCTURE_VALID",
            "HAS_DSM",
            "DSM_SELECTED",
            "PHYSICAL_DRIVE_DETECTED",
            "SOURCE_READ_ONLY",
            "SOURCE_NOT_SYSTEM",
            "SOURCE_NOT_BOOT",
            "DISK_BINDING_CONFIRMED",
            "DISK_BINDING_CURRENT",
            "CASE_JSON_MATCH",
            "NO_CRITICAL_RECONCILIATION_ERROR",
            "STATE_TRANSITION_ALLOWED",
        ],
        requires_human_confirmation=True,
        audit_event="ACQUISITION_PREPARED",
    ),
    "START_ACQUISITION": TransitionSpec(
        source_state=CaseState.ACQUISITION_READY,
        target_state=CaseState.ACQUIRING,
        action="START_ACQUISITION",
        preconditions=["CASE_EXISTS", "HAS_NUE", "HAS_SPECIES", "HAS_DSM"],
        policy_checks=[
            "DSM_SELECTED",
            "DISK_BINDING_CONFIRMED",
            "DISK_BINDING_CURRENT",
            "SOURCE_READ_ONLY",
            "SOURCE_NOT_SYSTEM",
            "SOURCE_NOT_BOOT",
            "DESTINATION_VALID",
            "DESTINATION_NOT_SOURCE_DISK",
            "SPACE_SUFFICIENT",
            "TARGET_NOT_EXISTS",
            "EWF_BINARY_VALID",
            "EWF_SINGLE_FILE_CONFIGURED",
            "HUMAN_CONFIRMATION_PRESENT",
            "STATE_TRANSITION_ALLOWED",
        ],
        requires_human_confirmation=True,
        audit_event="ACQUISITION_STARTED",
    ),
    "COMPLETE_ACQUISITION": TransitionSpec(
        source_state=CaseState.ACQUIRING,
        target_state=CaseState.ACQUISITION_COMPLETED,
        action="COMPLETE_ACQUISITION",
        preconditions=["CASE_EXISTS"],
        policy_checks=["STATE_TRANSITION_ALLOWED"],
        requires_human_confirmation=False,
        audit_event="ACQUISITION_COMPLETED",
    ),
    "ABORT_CASE": TransitionSpec(
        source_state=CaseState.NEW,
        target_state=CaseState.ABORTED,
        action="ABORT_CASE",
        preconditions=["CASE_EXISTS"],
        policy_checks=["STATE_TRANSITION_ALLOWED"],
        requires_human_confirmation=True,
        audit_event="CASE_ABORTED",
    ),
    "FAIL_CASE": TransitionSpec(
        source_state=CaseState.NEW,
        target_state=CaseState.FAILED,
        action="FAIL_CASE",
        preconditions=["CASE_EXISTS"],
        policy_checks=[],
        requires_human_confirmation=False,
        audit_event="CASE_FAILED",
    ),
}

# Transiciones desde otros estados hacia ABORTED / FAILED
ABORT_FROM_STATES = [
    CaseState.NEW,
    CaseState.IDENTIFICATION_PENDING,
    CaseState.IDENTIFICATION_COMPLETED,
    CaseState.ACQUISITION_READY,
    CaseState.ACQUIRING,
]

FAIL_FROM_STATES = [
    CaseState.NEW,
    CaseState.IDENTIFICATION_PENDING,
    CaseState.IDENTIFICATION_COMPLETED,
    CaseState.ACQUISITION_READY,
    CaseState.ACQUIRING,
]


def get_transition_spec(action: str, current_state: CaseState) -> Optional[TransitionSpec]:
    """Obtiene la especificación de transición para una acción y estado origen dado."""
    if action == "ABORT_CASE" and current_state in ABORT_FROM_STATES:
        return TransitionSpec(
            source_state=current_state,
            target_state=CaseState.ABORTED,
            action="ABORT_CASE",
            preconditions=["CASE_EXISTS"],
            policy_checks=["STATE_TRANSITION_ALLOWED"],
            requires_human_confirmation=True,
            audit_event="CASE_ABORTED",
        )
    if action == "FAIL_CASE" and current_state in FAIL_FROM_STATES:
        return TransitionSpec(
            source_state=current_state,
            target_state=CaseState.FAILED,
            action="FAIL_CASE",
            preconditions=["CASE_EXISTS"],
            policy_checks=[],
            requires_human_confirmation=False,
            audit_event="CASE_FAILED",
        )

    spec = LEGAL_TRANSITIONS.get(action)
    if spec and spec.source_state == current_state:
        return spec
    return None
