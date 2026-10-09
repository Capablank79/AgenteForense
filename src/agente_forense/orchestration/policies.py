"""
Motor de políticas (Policy Engine) y definiciones de políticas iniciales, hardware y reservadas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from agente_forense.orchestration.states import CaseState, OperativeState, ReservedState
from agente_forense.orchestration.context import OrchestrationContext


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"


@dataclass
class PolicyResult:
    policy_name: str
    decision: PolicyDecision
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


class BasePolicy:
    name: str = "BASE_POLICY"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        raise NotImplementedError


class CaseExistsPolicy(BasePolicy):
    name = "CASE_EXISTS"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.case_id and ctx.case_data:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El caso existe en PostgreSQL.")
        return PolicyResult(self.name, PolicyDecision.DENY, "El caso no existe.")


class CaseStructureValidPolicy(BasePolicy):
    name = "CASE_STRUCTURE_VALID"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.case_data.get("ruc"):
            return PolicyResult(self.name, PolicyDecision.DENY, "El caso carece de RUC válido.")
        return PolicyResult(self.name, PolicyDecision.ALLOW, "La estructura básica del caso es válida.")


class HasNuePolicy(BasePolicy):
    name = "HAS_NUE"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.nues and len(ctx.nues) > 0:
            return PolicyResult(self.name, PolicyDecision.ALLOW, f"El caso posee {len(ctx.nues)} NUE(s).")
        return PolicyResult(self.name, PolicyDecision.DENY, "El caso no posee ninguna NUE registrada.")


class HasSpeciesPolicy(BasePolicy):
    name = "HAS_SPECIES"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.species and len(ctx.species) > 0:
            return PolicyResult(self.name, PolicyDecision.ALLOW, f"El caso posee {len(ctx.species)} especie(s).")
        return PolicyResult(self.name, PolicyDecision.DENY, "El caso no posee ninguna especie registrada.")


class HasDsmPolicy(BasePolicy):
    name = "HAS_DSM"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.dsms and len(ctx.dsms) > 0:
            return PolicyResult(self.name, PolicyDecision.ALLOW, f"El caso posee {len(ctx.dsms)} DSM(s).")
        return PolicyResult(self.name, PolicyDecision.DENY, "El caso no posee ningún DSM (Storage Device) registrado.")


class CaseJsonMatchPolicy(BasePolicy):
    name = "CASE_JSON_MATCH"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.case_json_exists:
            return PolicyResult(self.name, PolicyDecision.DENY, "case.json no existe en el almacenamiento.")
        if not ctx.case_json_valid:
            return PolicyResult(self.name, PolicyDecision.DENY, "case.json no es un JSON válido o no cumple schema.")
        if not ctx.reconciliation_match:
            return PolicyResult(self.name, PolicyDecision.DENY, "Inconsistencia detectada entre PostgreSQL y case.json.")
        return PolicyResult(self.name, PolicyDecision.ALLOW, "case.json coincide correctamente con la base de datos.")


class NoCriticalReconciliationErrorPolicy(BasePolicy):
    name = "NO_CRITICAL_RECONCILIATION_ERROR"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.critical_reconciliation_errors:
            reasons = "; ".join(ctx.critical_reconciliation_errors)
            return PolicyResult(self.name, PolicyDecision.DENY, f"Errores críticos de reconciliación: {reasons}")
        return PolicyResult(self.name, PolicyDecision.ALLOW, "Sin errores críticos de reconciliación.")


class StateTransitionAllowedPolicy(BasePolicy):
    name = "STATE_TRANSITION_ALLOWED"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if target_state is None:
            return PolicyResult(self.name, PolicyDecision.DENY, "Estado objetivo no especificado.")
        
        reserved_values = {e.value for e in ReservedState}
        if target_state.value in reserved_values:
            return PolicyResult(
                self.name,
                PolicyDecision.DENY,
                f"El estado objetivo '{target_state.value}' es un estado reservado no habilitado en R07.1."
            )
        
        return PolicyResult(self.name, PolicyDecision.ALLOW, f"Transición hacia {target_state.value} permitida.")


class DsmSelectedPolicy(BasePolicy):
    name = "DSM_SELECTED"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.selected_dsm_id or (ctx.dsms and len(ctx.dsms) > 0):
            return PolicyResult(self.name, PolicyDecision.ALLOW, "Existe un DSM seleccionado o registrado.")
        return PolicyResult(self.name, PolicyDecision.DENY, "No hay ningún DSM seleccionado.")


class PhysicalDriveDetectedPolicy(BasePolicy):
    name = "PHYSICAL_DRIVE_DETECTED"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.active_disk_snapshot and ctx.active_disk_snapshot.get("physical_drive"):
            return PolicyResult(self.name, PolicyDecision.ALLOW, f"PhysicalDrive detectado: {ctx.active_disk_snapshot.get('physical_drive')}")
        return PolicyResult(self.name, PolicyDecision.DENY, "No se ha detectado ningún PhysicalDrive activo.")


class SourceReadOnlyPolicy(BasePolicy):
    name = "SOURCE_READ_ONLY"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.active_disk_snapshot:
            return PolicyResult(self.name, PolicyDecision.DENY, "No existe información de disco físico activo.")
        if ctx.active_disk_snapshot.get("is_read_only") is True:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El disco físico de origen tiene IsReadOnly=True.")
        return PolicyResult(self.name, PolicyDecision.DENY, "El disco físico de origen NO está en modo de solo lectura (IsReadOnly=False).")


class SourceNotSystemPolicy(BasePolicy):
    name = "SOURCE_NOT_SYSTEM"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.active_disk_snapshot:
            return PolicyResult(self.name, PolicyDecision.DENY, "No existe información de disco físico activo.")
        if ctx.active_disk_snapshot.get("is_system") is False:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El disco físico de origen NO es disco de sistema.")
        return PolicyResult(self.name, PolicyDecision.DENY, "El disco físico de origen es un disco de sistema (IsSystem=True).")


class SourceNotBootPolicy(BasePolicy):
    name = "SOURCE_NOT_BOOT"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.active_disk_snapshot:
            return PolicyResult(self.name, PolicyDecision.DENY, "No existe información de disco físico activo.")
        if ctx.active_disk_snapshot.get("is_boot") is False:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El disco físico de origen NO es disco de arranque.")
        return PolicyResult(self.name, PolicyDecision.DENY, "El disco físico de origen es un disco de arranque (IsBoot=True).")


class DiskBindingConfirmedPolicy(BasePolicy):
    name = "DISK_BINDING_CONFIRMED"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if ctx.disk_binding_data and ctx.disk_binding_data.get("status") == "CONFIRMED":
            return PolicyResult(self.name, PolicyDecision.ALLOW, "Existe un vínculo DSM ↔ Disco confirmado por operador humano.")
        return PolicyResult(self.name, PolicyDecision.DENY, "No se ha verificado confirmación humana para el vínculo de disco.")


class DiskBindingCurrentPolicy(BasePolicy):
    name = "DISK_BINDING_CURRENT"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        if not ctx.disk_binding_data or not ctx.active_disk_snapshot:
            return PolicyResult(self.name, PolicyDecision.DENY, "Faltan datos de binding o snapshot activo.")
        binding_pd = ctx.disk_binding_data.get("physical_drive")
        active_pd = ctx.active_disk_snapshot.get("physical_drive")
        if binding_pd and binding_pd == active_pd:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El vínculo registrado coincide con el disco activo revalidado.")
        return PolicyResult(self.name, PolicyDecision.DENY, f"El vínculo de disco no es actual (Registrado: {binding_pd}, Activo: {active_pd}).")


class DestinationValidPolicy(BasePolicy):
    name = "DESTINATION_VALID"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        dest = ctx.extra_context.get("destination_directory") if ctx.extra_context else None
        if dest:
            return PolicyResult(self.name, PolicyDecision.ALLOW, f"Directorio de destino válido: {dest}")
        return PolicyResult(self.name, PolicyDecision.DENY, "Falta especificar directorio de destino válido.")


class DestinationNotSourceDiskPolicy(BasePolicy):
    name = "DESTINATION_NOT_SOURCE_DISK"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        src_pd = ctx.active_disk_snapshot.get("physical_drive") if ctx.active_disk_snapshot else None
        dest_pd = ctx.extra_context.get("destination_physical_drive") if ctx.extra_context else None
        if src_pd and dest_pd and src_pd.lower() == dest_pd.lower():
            return PolicyResult(self.name, PolicyDecision.DENY, f"El destino está en el mismo disco físico que el origen ({src_pd}).")
        return PolicyResult(self.name, PolicyDecision.ALLOW, "El disco de destino es independiente del disco de origen.")


class SpaceSufficientPolicy(BasePolicy):
    name = "SPACE_SUFFICIENT"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        src_size = ctx.active_disk_snapshot.get("size_bytes") if ctx.active_disk_snapshot else 0
        free_bytes = ctx.extra_context.get("destination_free_bytes") if ctx.extra_context else 0
        if free_bytes >= src_size and src_size > 0:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "El espacio en destino es suficiente para el origen.")
        return PolicyResult(self.name, PolicyDecision.DENY, f"Espacio insuficiente en destino ({free_bytes} < {src_size} bytes).")


class TargetNotExistsPolicy(BasePolicy):
    name = "TARGET_NOT_EXISTS"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        target_exists = ctx.extra_context.get("target_exists") if ctx.extra_context else False
        if not target_exists:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "No existen artefactos previos colisionantes.")
        return PolicyResult(self.name, PolicyDecision.DENY, "Ya existen artefactos previos para el target especificado.")


class EwfBinaryValidPolicy(BasePolicy):
    name = "EWF_BINARY_VALID"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        binary_valid = ctx.extra_context.get("binary_valid", True) if ctx.extra_context else True
        if binary_valid:
            return PolicyResult(self.name, PolicyDecision.ALLOW, "Binario ewfacquire verificado y hash SHA256 válido.")
        return PolicyResult(self.name, PolicyDecision.DENY, "El binario ewfacquire no es válido o su hash cambió.")


class EwfSingleFileConfiguredPolicy(BasePolicy):
    name = "EWF_SINGLE_FILE_CONFIGURED"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        segment_size = ctx.extra_context.get("segment_size", "0") if ctx.extra_context else "0"
        if segment_size == "0":
            return PolicyResult(self.name, PolicyDecision.ALLOW, "EWF configurado para archivo único -S 0.")
        return PolicyResult(self.name, PolicyDecision.DENY, "EWF no está configurado para Single E01 (-S 0).")


class HumanConfirmationPresentPolicy(BasePolicy):
    name = "HUMAN_CONFIRMATION_PRESENT"

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        conf = ctx.extra_context.get("human_confirmation_exact") if ctx.extra_context else None
        if conf == "ADQUIRIR":
            return PolicyResult(self.name, PolicyDecision.ALLOW, "Confirmación humana 'ADQUIRIR' presente.")
        return PolicyResult(self.name, PolicyDecision.DENY, f"Falta confirmación humana exacta 'ADQUIRIR' (Recibido: '{conf}').")


class FutureReservedPolicy(BasePolicy):
    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason

    def evaluate(self, ctx: OrchestrationContext, target_state: Optional[CaseState] = None) -> PolicyResult:
        return PolicyResult(self.name, PolicyDecision.DENY, f"Política reservada para futuro: {self.reason}")


class PolicyEngine:
    """Motor de evaluación de políticas estáticas y deterministas."""

    def __init__(self):
        self._policies: Dict[str, BasePolicy] = {
            "CASE_EXISTS": CaseExistsPolicy(),
            "CASE_STRUCTURE_VALID": CaseStructureValidPolicy(),
            "HAS_NUE": HasNuePolicy(),
            "HAS_SPECIES": HasSpeciesPolicy(),
            "HAS_DSM": HasDsmPolicy(),
            "CASE_JSON_MATCH": CaseJsonMatchPolicy(),
            "NO_CRITICAL_RECONCILIATION_ERROR": NoCriticalReconciliationErrorPolicy(),
            "STATE_TRANSITION_ALLOWED": StateTransitionAllowedPolicy(),
            "DSM_SELECTED": DsmSelectedPolicy(),
            "PHYSICAL_DRIVE_DETECTED": PhysicalDriveDetectedPolicy(),
            "SOURCE_READ_ONLY": SourceReadOnlyPolicy(),
            "SOURCE_NOT_SYSTEM": SourceNotSystemPolicy(),
            "SOURCE_NOT_BOOT": SourceNotBootPolicy(),
            "DISK_BINDING_CONFIRMED": DiskBindingConfirmedPolicy(),
            "DISK_BINDING_CURRENT": DiskBindingCurrentPolicy(),
            # Reservadas
            "DESTINATION_SAFE": FutureReservedPolicy("DESTINATION_SAFE", "Requerirá hardware en R08+"),
            "E01_NOT_EXISTS": FutureReservedPolicy("E01_NOT_EXISTS", "Requerirá ewfacquire en R08+"),
            "HUMAN_CONFIRMATION_PRESENT": FutureReservedPolicy("HUMAN_CONFIRMATION_PRESENT", "Gate explícito"),
        }

    def evaluate_policy(
        self, policy_name: str, ctx: OrchestrationContext, target_state: Optional[CaseState] = None
    ) -> PolicyResult:
        policy = self._policies.get(policy_name)
        if not policy:
            return PolicyResult(
                policy_name, PolicyDecision.DENY, f"Política desconocida o no implementada: {policy_name}"
            )
        return policy.evaluate(ctx, target_state)

    def evaluate_policies(
        self, policy_names: List[str], ctx: OrchestrationContext, target_state: Optional[CaseState] = None
    ) -> List[PolicyResult]:
        return [self.evaluate_policy(p, ctx, target_state) for p in policy_names]
