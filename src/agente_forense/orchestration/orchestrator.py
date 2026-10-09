"""
Orquestador principal del caso (CaseOrchestrator).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from agente_forense.orchestration.states import CaseState, OperativeState, ReservedState
from agente_forense.orchestration.context import OrchestrationContext
from agente_forense.orchestration.transitions import get_transition_spec
from agente_forense.orchestration.policies import PolicyEngine, PolicyDecision
from agente_forense.orchestration.human_gate import HumanGate, ConfirmationStatus
from agente_forense.orchestration.actions import (
    ActionHandler,
    StartIdentificationHandler,
    CompleteIdentificationHandler,
    CompleteIdentificationMockHandler,
    PrepareAcquisitionHandler,
    AbortCaseHandler,
    FailCaseHandler,
)
from agente_forense.orchestration.errors import (
    InvalidTransitionError,
    PolicyDeniedError,
    ConfirmationRequiredError,
    ConfirmationNotFoundError,
    ConfirmationAlreadyResolvedError,
    ConcurrencyConflictError,
    OrchestrationPersistenceError,
)
from agente_forense.persistence.models import CaseModel, CaseEventModel
from agente_forense.persistence.repositories import (
    CaseRepository,
    NueRepository,
    SpeciesRepository,
    DsmRepository,
    CaseEventRepository,
    AuditRepository,
)
from agente_forense.storage.case_json import CaseJsonService
from agente_forense.domain.enums import ReconciliationStatus


@dataclass
class AllowedActionInfo:
    action: str
    allowed: bool
    requires_confirmation: bool
    reason: str


class CaseOrchestrator:
    """
    Orquestador principal de dominio para el Agente Forense.
    Gestiona la máquina de estados, el motor de políticas, el Human Gate,
    transacciones de base de datos, actualización atómica de case.json, reconciliación y auditoría.
    """

    def __init__(self, session: Session, storage_root: Optional[Path] = None):
        self.session = session
        self.storage_root = storage_root
        self.case_repo = CaseRepository(session)
        self.nue_repo = NueRepository(session)
        self.species_repo = SpeciesRepository(session)
        self.dsm_repo = DsmRepository(session)
        self.event_repo = CaseEventRepository(session)
        self.audit_repo = AuditRepository(session)
        self.policy_engine = PolicyEngine()
        self.human_gate = HumanGate(session)
        self.case_json_service = CaseJsonService(session, storage_root=storage_root)

        self._handlers: Dict[str, ActionHandler] = {
            "START_IDENTIFICATION": StartIdentificationHandler(),
            "COMPLETE_IDENTIFICATION": CompleteIdentificationHandler(),
            "COMPLETE_IDENTIFICATION_MOCK": CompleteIdentificationMockHandler(),
            "PREPARE_ACQUISITION": PrepareAcquisitionHandler(),
            "ABORT_CASE": AbortCaseHandler(),
            "FAIL_CASE": FailCaseHandler(),
        }

    def build_context(
        self,
        case_id: UUID,
        operator: Optional[str] = None,
        request_id: Optional[str] = None,
        selected_dsm_id: Optional[UUID] = None,
        active_disk_snapshot: Optional[Dict[str, Any]] = None,
    ) -> OrchestrationContext:
        """Carga el estado del caso, jerarquía relational y estado de case.json."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise InvalidTransitionError(f"El caso {case_id} no fue encontrado.")

        current_state = CaseState(case.status)
        state_version = getattr(case, "state_version", 1)

        nues = self.nue_repo.list_by_case(case_id)
        nues_data = [{"id": str(n.id), "nue_number": n.nue_number} for n in nues]

        species_data = []
        dsms_data = []
        for n in nues:
            sp_list = self.species_repo.list_by_nue(n.id)
            for sp in sp_list:
                species_data.append({"id": str(sp.id), "species_number": sp.species_number, "label": sp.label})
                d_list = self.dsm_repo.list_by_species(sp.id)
                for d in d_list:
                    dsms_data.append({"id": str(d.id), "dsm_number": d.dsm_number, "label": d.label})

        case_data = {
            "id": str(case.id),
            "ruc": case.ruc,
            "status": case.status,
            "case_root": case.case_root,
        }

        # case.json validation & reconciliation
        case_json_exists = False
        case_json_valid = False
        reconciliation_match = False
        critical_errors = []

        if case.case_root:
            case_json_path = Path(case.case_root) / "case.json"
            if case_json_path.exists():
                case_json_exists = True
                status, msg = self.case_json_service.reconcile(case_id, case_json_path, actor=operator or "SYSTEM", request_id=request_id)
                if status == ReconciliationStatus.MATCH:
                    case_json_valid = True
                    reconciliation_match = True
                elif status == ReconciliationStatus.INVALID_JSON:
                    case_json_valid = False
                    critical_errors.append(msg or "JSON inválido")
                else:
                    case_json_valid = True
                    critical_errors.append(msg or "Mismatch de contenido")
            else:
                case_json_exists = False

        active_snap_dict = None
        if isinstance(active_disk_snapshot, dict):
            active_snap_dict = active_disk_snapshot
        elif hasattr(active_disk_snapshot, "model_dump"):
            active_snap_dict = active_disk_snapshot.model_dump(mode="json")

        disk_binding_data = None
        if selected_dsm_id:
            from agente_forense.hardware.bindings import DiskBindingService
            binding_service = DiskBindingService(self.session)
            active_binding = binding_service.get_active_binding(case_id=case_id, dsm_id=selected_dsm_id)
            if active_binding:
                disk_binding_data = {
                    "id": str(active_binding.id),
                    "status": active_binding.status,
                    "physical_drive": active_binding.physical_drive,
                    "disk_number": active_binding.disk_number,
                    "snapshot": active_binding.snapshot_json,
                }

        return OrchestrationContext(
            case_id=case_id,
            current_state=current_state,
            state_version=state_version,
            case_data=case_data,
            nues=nues_data,
            species=species_data,
            dsms=dsms_data,
            case_json_exists=case_json_exists,
            case_json_valid=case_json_valid,
            reconciliation_match=reconciliation_match,
            critical_reconciliation_errors=critical_errors,
            request_id=request_id,
            selected_dsm_id=selected_dsm_id,
            disk_binding_data=disk_binding_data,
            active_disk_snapshot=active_snap_dict,
        )

    def get_allowed_actions(self, case_id: UUID) -> List[AllowedActionInfo]:
        """Calcula todas las acciones permitidas y bloqueadas para un caso."""
        ctx = self.build_context(case_id)
        results = []

        possible_actions = [
            "START_IDENTIFICATION",
            "COMPLETE_IDENTIFICATION",
            "COMPLETE_IDENTIFICATION_MOCK",
            "PREPARE_ACQUISITION",
            "ABORT_CASE",
            "FAIL_CASE",
        ]

        for action_name in possible_actions:
            spec = get_transition_spec(action_name, ctx.current_state)
            if not spec:
                results.append(
                    AllowedActionInfo(
                        action=action_name,
                        allowed=False,
                        requires_confirmation=False,
                        reason=f"Transición no permitida desde el estado actual ({ctx.current_state.value}).",
                    )
                )
                continue

            policy_results = self.policy_engine.evaluate_policies(spec.policy_checks, ctx, spec.target_state)
            denied_policies = [p for p in policy_results if p.decision == PolicyDecision.DENY]

            if denied_policies:
                reasons = "; ".join([f"{p.policy_name}: {p.reason}" for p in denied_policies])
                results.append(
                    AllowedActionInfo(
                        action=action_name,
                        allowed=False,
                        requires_confirmation=spec.requires_human_confirmation,
                        reason=f"Bloqueado por políticas: {reasons}",
                    )
                )
            else:
                results.append(
                    AllowedActionInfo(
                        action=action_name,
                        allowed=True,
                        requires_confirmation=spec.requires_human_confirmation,
                        reason="Acción permitida por la máquina de estados y motor de políticas.",
                    )
                )

        return results

    def execute_action(
        self,
        case_id: UUID,
        action: str,
        confirmation_id: Optional[str] = None,
        operator: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta de manera segura, transaccional y fail-closed una acción sobre el caso.
        """
        actor = operator or "SYSTEM"
        payload_dict = payload or {}
        selected_dsm = payload_dict.get("selected_dsm_id")
        active_snap = payload_dict.get("active_disk_snapshot")

        ctx = self.build_context(
            case_id,
            operator=actor,
            request_id=request_id,
            selected_dsm_id=UUID(selected_dsm) if isinstance(selected_dsm, str) else selected_dsm,
            active_disk_snapshot=active_snap,
        )

        # Auditoría STATE_TRANSITION_REQUESTED
        self.audit_repo.append(
            actor=actor,
            module="ORCHESTRATION",
            tool="CaseOrchestrator",
            tool_version="1.0.0",
            event_type="STATE_TRANSITION_REQUESTED",
            action=action,
            result="REQUESTED",
            case_id=case_id,
            previous_state=ctx.current_state.value,
            details={"request_id": request_id, "confirmation_id": confirmation_id},
        )
        self.session.flush()

        # 1. Verificar especificación de transición
        spec = get_transition_spec(action, ctx.current_state)
        if not spec:
            self._audit_rejected(case_id, action, ctx.current_state.value, "Transición no válida", actor, request_id)
            self.session.commit()
            raise InvalidTransitionError(
                f"La acción '{action}' no es válida para el estado actual '{ctx.current_state.value}'."
            )

        # 2. Control de concurrencia
        if expected_version is not None and ctx.state_version != expected_version:
            msg = f"Conflicto de concurrencia: versión esperada {expected_version}, versión actual {ctx.state_version}."
            self._audit_rejected(case_id, action, ctx.current_state.value, msg, actor, request_id)
            self.session.commit()
            raise ConcurrencyConflictError(msg)

        # 3. Evaluación de políticas
        policy_results = self.policy_engine.evaluate_policies(spec.policy_checks, ctx, spec.target_state)
        for p in policy_results:
            self.audit_repo.append(
                actor=actor,
                module="POLICY_ENGINE",
                tool="PolicyEngine",
                tool_version="1.0.0",
                event_type="POLICY_EVALUATED",
                action=action,
                result=p.decision.value,
                case_id=case_id,
                previous_state=ctx.current_state.value,
                details={"policy_name": p.policy_name, "reason": p.reason, "request_id": request_id},
            )
        self.session.flush()

        denied_policies = [p for p in policy_results if p.decision == PolicyDecision.DENY]
        if denied_policies:
            reasons = "; ".join([f"{p.policy_name}: {p.reason}" for p in denied_policies])
            self._audit_rejected(case_id, action, ctx.current_state.value, reasons, actor, request_id)
            self.session.commit()
            raise PolicyDeniedError(f"Acción '{action}' denegada por políticas: {reasons}")

        # 4. Human Gate Check
        if spec.requires_human_confirmation:
            if not confirmation_id:
                # Crear solicitud de confirmación si no fue provista
                conf_record = self.human_gate.create_confirmation(
                    case_id=case_id,
                    requested_action=action,
                    summary=f"Confirmación explícita requerida para ejecutar '{action}' en caso {case_id}.",
                    operator=actor,
                    request_id=request_id,
                )
                self.audit_repo.append(
                    actor=actor,
                    module="HUMAN_GATE",
                    tool="HumanGate",
                    tool_version="1.0.0",
                    event_type="HUMAN_CONFIRMATION_REQUESTED",
                    action=action,
                    result="PENDING",
                    case_id=case_id,
                    previous_state=ctx.current_state.value,
                    human_confirmation=True,
                    details={"confirmation_id": conf_record.confirmation_id, "request_id": request_id},
                )
                self.session.commit()
                raise ConfirmationRequiredError(
                    f"La acción '{action}' requiere confirmación humana.",
                    confirmation_id=conf_record.confirmation_id,
                )
            else:
                conf_record = self.human_gate.get_confirmation(confirmation_id)
                if not conf_record:
                    raise ConfirmationNotFoundError(f"Confirmación {confirmation_id} no encontrada.")
                if conf_record.status != ConfirmationStatus.CONFIRMED:
                    msg = f"La confirmación {confirmation_id} no se encuentra en estado CONFIRMED (Estado: {conf_record.status.value})."
                    self._audit_rejected(case_id, action, ctx.current_state.value, msg, actor, request_id)
                    self.session.commit()
                    raise PolicyDeniedError(msg)

                self.audit_repo.append(
                    actor=actor,
                    module="HUMAN_GATE",
                    tool="HumanGate",
                    tool_version="1.0.0",
                    event_type="HUMAN_CONFIRMATION_RECORDED",
                    action=action,
                    result="CONFIRMED",
                    case_id=case_id,
                    human_confirmation=True,
                    details={"confirmation_id": confirmation_id, "request_id": request_id},
                )
                self.session.flush()

        # 5. Ejecutar ActionHandler
        handler = self._handlers.get(action)
        if not handler:
            msg = f"Sin handler registrado para la acción {action}."
            self._audit_rejected(case_id, action, ctx.current_state.value, msg, actor, request_id)
            self.session.commit()
            raise OrchestrationError(msg)

        try:
            handler_res = handler.execute(ctx, payload=payload)
        except Exception as exc:
            self.session.rollback()
            self._audit_error(case_id, action, ctx.current_state.value, str(exc), actor, request_id)
            self.session.commit()
            raise OrchestrationError(f"Fallo al ejecutar handler de {action}: {exc}") from exc

        if not handler_res.success:
            self.session.rollback()
            self._audit_rejected(case_id, action, ctx.current_state.value, handler_res.message, actor, request_id)
            self.session.commit()
            raise OrchestrationError(f"Error en ejecución de {action}: {handler_res.message}")

        # 6. Actualizar Estado en DB y Transacción
        try:
            case_model = self.case_repo.get_by_id(case_id)
            if not case_model:
                raise OrchestrationPersistenceError("Caso no encontrado durante actualización de estado.")

            prev_state_str = case_model.status
            new_state_str = handler_res.target_state.value

            # Si ya está en el mismo estado y es idempotente, no romper
            case_model.status = new_state_str
            case_model.state_version += 1

            # Case Event
            self.event_repo.record_event(
                case_id=case_id,
                event_type=spec.audit_event,
                previous_state=prev_state_str,
                new_state=new_state_str,
                result="SUCCESS",
                details={"action": action, "operator": actor, "request_id": request_id, **handler_res.details},
            )

            # Audit Event
            self.audit_repo.append(
                actor=actor,
                module="ORCHESTRATION",
                tool="CaseOrchestrator",
                tool_version="1.0.0",
                event_type="ACTION_EXECUTED",
                action=action,
                result="SUCCESS",
                case_id=case_id,
                previous_state=prev_state_str,
                new_state=new_state_str,
                details={"request_id": request_id, "state_version": case_model.state_version},
            )

            self.session.flush()

            # 7. Actualizar case.json (Snapshot & Reconciliation)
            if case_model.case_root:
                case_root_path = Path(case_model.case_root)
                self.case_json_service.write_case_json_atomic(case_id, case_root_path, actor=actor, request_id=request_id)
                # Sincronización/Reconciliación posterior
                rec_status, rec_msg = self.case_json_service.reconcile(case_id, case_root_path / "case.json", actor=actor, request_id=request_id)
                if rec_status != ReconciliationStatus.MATCH:
                    self.audit_repo.append(
                        actor=actor,
                        module="ORCHESTRATION",
                        tool="CaseOrchestrator",
                        tool_version="1.0.0",
                        event_type="RECONCILIATION_WARNING",
                        action=action,
                        result="MISMATCH",
                        case_id=case_id,
                        details={"reconciliation_status": rec_status.value, "message": rec_msg},
                    )

            self.audit_repo.append(
                actor=actor,
                module="ORCHESTRATION",
                tool="CaseOrchestrator",
                tool_version="1.0.0",
                event_type="STATE_TRANSITION_COMPLETED",
                action=action,
                result="SUCCESS",
                case_id=case_id,
                previous_state=prev_state_str,
                new_state=new_state_str,
                details={"request_id": request_id},
            )

            self.session.commit()

            return {
                "success": True,
                "case_id": str(case_id),
                "previous_state": prev_state_str,
                "current_state": new_state_str,
                "state_version": case_model.state_version,
                "message": handler_res.message,
                "details": handler_res.details,
            }

        except Exception as exc:
            self.session.rollback()
            self._audit_error(case_id, action, ctx.current_state.value, str(exc), actor, request_id)
            self.session.commit()
            raise OrchestrationPersistenceError(f"Error de persistencia en orquestación: {exc}") from exc

    def _audit_rejected(
        self, case_id: UUID, action: str, current_state: str, reason: str, actor: str, request_id: Optional[str]
    ):
        self.audit_repo.append(
            actor=actor,
            module="ORCHESTRATION",
            tool="CaseOrchestrator",
            tool_version="1.0.0",
            event_type="STATE_TRANSITION_REJECTED",
            action=action,
            result="DENIED",
            case_id=case_id,
            previous_state=current_state,
            error=reason,
            details={"request_id": request_id},
        )

    def _audit_error(
        self, case_id: UUID, action: str, current_state: str, error_msg: str, actor: str, request_id: Optional[str]
    ):
        self.audit_repo.append(
            actor=actor,
            module="ORCHESTRATION",
            tool="CaseOrchestrator",
            tool_version="1.0.0",
            event_type="ORCHESTRATION_ERROR",
            action=action,
            result="ERROR",
            case_id=case_id,
            previous_state=current_state,
            error=error_msg,
            details={"request_id": request_id},
        )
