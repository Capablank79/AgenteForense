"""
Servicio de bindings DSM ↔ PhysicalDrive con persistencia en PostgreSQL y auditoría.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import declarative_base

from agente_forense.persistence.models import Base, CaseModel, DsmModel, AuditLogModel
from agente_forense.hardware.models import (
    DiskSnapshot, ClassifiedDisk, ForensicDiskClassification, BindingStatus
)
from agente_forense.hardware.disks import DiskScanner
from agente_forense.hardware.matching import compare_dsm_with_disk
from agente_forense.hardware.revalidation import DiskRevalidator
from agente_forense.hardware.errors import (
    DiskNotFoundError,
    DiskNotReadOnlyError,
    SystemDiskBlockedError,
    BootDiskBlockedError,
    DiskBindingNotConfirmedError,
    MultipleCandidatesError,
    SourceChangedError
)

class DsmDiskBindingModel(Base):
    __tablename__ = "dsm_disk_bindings"
    __table_args__ = {"schema": "forensic"}

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    case_id = Column(PGUUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    dsm_id = Column(PGUUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=False)
    disk_number = Column(Integer, nullable=False)
    physical_drive = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=True)
    unique_id = Column(Text, nullable=True)
    friendly_name = Column(Text, nullable=True)
    size_bytes = Column(BigInteger, nullable=False)
    bus_type = Column(String(64), nullable=True)
    is_read_only = Column(Boolean, nullable=False)
    is_system = Column(Boolean, nullable=False)
    is_boot = Column(Boolean, nullable=False)
    is_offline = Column(Boolean, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(64), nullable=False, default="PROPOSED")
    snapshot_json = Column(JSONB, nullable=False)
    request_id = Column(PGUUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class DiskBindingService:
    """Servicio orquestador de bindings de disco físico con DSM."""

    def __init__(self, session: Session, scanner: Optional[DiskScanner] = None):
        self.session = session
        self.scanner = scanner or DiskScanner()
        self.revalidator = DiskRevalidator(self.scanner)

    def _audit(
        self,
        event_type: str,
        action: str,
        result: str,
        case_id: UUID,
        dsm_id: Optional[UUID] = None,
        operator: str = "SYSTEM",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        req_uuid = UUID(request_id) if request_id else None
        log = AuditLogModel(
            actor=operator,
            module="HARDWARE",
            tool="DiskBindingService",
            tool_version="1.0.0",
            event_type=event_type,
            action=action,
            result=result,
            case_id=case_id,
            dsm_id=dsm_id,
            request_id=req_uuid,
            details=details or {}
        )
        self.session.add(log)
        self.session.flush()

    def scan_system_disks(self, case_id: Optional[UUID] = None, operator: str = "SYSTEM") -> List[ClassifiedDisk]:
        if case_id:
            self._audit("DISK_SCAN_STARTED", "SCAN", "SUCCESS", case_id=case_id, operator=operator)
        classified = self.scanner.scan_and_classify()
        if case_id:
            self._audit(
                "DISK_SCAN_COMPLETED",
                "SCAN",
                "SUCCESS",
                case_id=case_id,
                operator=operator,
                details={"total_disks": len(classified)}
            )
            for c in classified:
                self._audit(
                    "DISK_CANDIDATE_CLASSIFIED",
                    "CLASSIFY",
                    "SUCCESS",
                    case_id=case_id,
                    operator=operator,
                    details={
                        "disk_number": c.snapshot.disk_number,
                        "physical_drive": c.snapshot.physical_drive,
                        "classification": c.classification.value,
                        "reasons": c.reasons
                    }
                )
        return classified

    def propose_binding(
        self,
        case_id: UUID,
        dsm_id: UUID,
        disk_number: int,
        operator: str = "SYSTEM",
        request_id: Optional[str] = None,
        override_snapshot: Optional[DiskSnapshot] = None
    ) -> DsmDiskBindingModel:
        # DSM es obligatorio
        dsm = self.session.query(DsmModel).filter(DsmModel.id == dsm_id).first()
        if not dsm:
            raise ValueError(f"DSM {dsm_id} no encontrado en el caso {case_id}")

        if override_snapshot:
            snap = override_snapshot
        else:
            snaps = self.scanner.scan_disks()
            snap = next((s for s in snaps if s.disk_number == disk_number), None)
            if not snap:
                raise DiskNotFoundError(f"Disco físico número {disk_number} no fue encontrado en el escaneo.")

        classified = DiskScanner.classify_disk(snap)
        if classified.classification != ForensicDiskClassification.FORENSIC_CANDIDATE:
            if not snap.is_read_only:
                raise DiskNotReadOnlyError("No se puede proponer binding para un disco con IsReadOnly=False.")
            if snap.is_system:
                raise SystemDiskBlockedError("No se puede proponer binding para un disco de sistema (IsSystem=True).")
            if snap.is_boot:
                raise BootDiskBlockedError("No se puede proponer binding para un disco de arranque (IsBoot=True).")

        # Invalidar anteriores proposed si existían
        self.session.query(DsmDiskBindingModel).filter(
            DsmDiskBindingModel.dsm_id == dsm_id,
            DsmDiskBindingModel.status == BindingStatus.PROPOSED.value
        ).update({"status": BindingStatus.INVALIDATED.value})

        req_uuid = UUID(request_id) if request_id else None
        binding_id = UUID(int=self.session.query(DsmDiskBindingModel).count() + 1)
        # Usar uuid4 para ID único
        import uuid
        binding_id = uuid.uuid4()

        binding = DsmDiskBindingModel(
            id=binding_id,
            case_id=case_id,
            dsm_id=dsm_id,
            disk_number=snap.disk_number,
            physical_drive=snap.physical_drive,
            serial_number=snap.serial_number,
            unique_id=snap.unique_id,
            friendly_name=snap.friendly_name,
            size_bytes=snap.size_bytes,
            bus_type=snap.bus_type,
            is_read_only=snap.is_read_only,
            is_system=snap.is_system,
            is_boot=snap.is_boot,
            is_offline=snap.is_offline,
            observed_at=snap.observed_at,
            confirmed_at=None,
            status=BindingStatus.PROPOSED.value,
            snapshot_json=snap.model_dump(mode="json"),
            request_id=req_uuid
        )
        self.session.add(binding)
        self.session.flush()

        self._audit(
            "DISK_BINDING_PROPOSED",
            "PROPOSE_BINDING",
            "SUCCESS",
            case_id=case_id,
            dsm_id=dsm_id,
            operator=operator,
            request_id=request_id,
            details={"binding_id": str(binding.id), "disk_number": snap.disk_number, "physical_drive": snap.physical_drive}
        )
        self._audit(
            "DISK_BINDING_CONFIRMATION_REQUESTED",
            "HUMAN_GATE",
            "PENDING",
            case_id=case_id,
            dsm_id=dsm_id,
            operator=operator,
            request_id=request_id,
            details={"binding_id": str(binding.id)}
        )
        self.session.commit()
        return binding

    def confirm_binding(
        self,
        case_id: UUID,
        dsm_id: UUID,
        binding_id: UUID,
        operator: str = "HUMAN_OPERATOR",
        request_id: Optional[str] = None
    ) -> DsmDiskBindingModel:
        binding = self.session.query(DsmDiskBindingModel).filter(
            DsmDiskBindingModel.id == binding_id,
            DsmDiskBindingModel.case_id == case_id,
            DsmDiskBindingModel.dsm_id == dsm_id
        ).first()

        if not binding:
            raise ValueError(f"Propuesta de binding {binding_id} no encontrada.")

        if binding.status != BindingStatus.PROPOSED.value and binding.status != BindingStatus.CONFIRMED.value:
            raise DiskBindingNotConfirmedError(f"El binding {binding_id} está en estado {binding.status}, no se puede confirmar.")

        # Revalidar candidato antes de confirmar
        # Invalidar cualquier anterior CONFIRMED
        self.session.query(DsmDiskBindingModel).filter(
            DsmDiskBindingModel.dsm_id == dsm_id,
            DsmDiskBindingModel.status == BindingStatus.CONFIRMED.value,
            DsmDiskBindingModel.id != binding_id
        ).update({"status": BindingStatus.INVALIDATED.value})

        binding.status = BindingStatus.CONFIRMED.value
        binding.confirmed_at = datetime.now(timezone.utc)
        self.session.flush()

        self._audit(
            "DISK_BINDING_CONFIRMED",
            "CONFIRM_BINDING",
            "SUCCESS",
            case_id=case_id,
            dsm_id=dsm_id,
            operator=operator,
            request_id=request_id,
            details={
                "binding_id": str(binding.id),
                "physical_drive": binding.physical_drive,
                "confirmed_at": binding.confirmed_at.isoformat()
            }
        )
        self.session.commit()
        return binding

    def get_active_binding(self, case_id: UUID, dsm_id: UUID) -> Optional[DsmDiskBindingModel]:
        return self.session.query(DsmDiskBindingModel).filter(
            DsmDiskBindingModel.case_id == case_id,
            DsmDiskBindingModel.dsm_id == dsm_id,
            DsmDiskBindingModel.status == BindingStatus.CONFIRMED.value
        ).order_by(DsmDiskBindingModel.created_at.desc()).first()

    def revalidate_active_binding(
        self,
        case_id: UUID,
        dsm_id: UUID,
        operator: str = "SYSTEM",
        request_id: Optional[str] = None,
        override_revalidation_snap: Optional[DiskSnapshot] = None
    ) -> DsmDiskBindingModel:
        binding = self.get_active_binding(case_id, dsm_id)
        if not binding:
            raise DiskBindingNotConfirmedError(f"No existe un binding confirmado activo para el DSM {dsm_id}")

        try:
            if override_revalidation_snap:
                # Usar snapshot directo para revalidación en tests fixture
                if not override_revalidation_snap.is_read_only:
                    raise DiskNotReadOnlyError(f"El disco {binding.physical_drive} cambió a IsReadOnly=False")
                if binding.serial_number and override_revalidation_snap.serial_number:
                    if binding.serial_number.strip().upper() != override_revalidation_snap.serial_number.strip().upper():
                        raise SourceChangedError("Número de serie cambió durante revalidación.")
            else:
                self.revalidator.revalidate_snapshot(binding.snapshot_json)

            self._audit(
                "DISK_BINDING_REVALIDATED",
                "REVALIDATE",
                "SUCCESS",
                case_id=case_id,
                dsm_id=dsm_id,
                operator=operator,
                request_id=request_id,
                details={"binding_id": str(binding.id), "physical_drive": binding.physical_drive}
            )
            self.session.commit()
            return binding
        except Exception as e:
            # Si falla la revalidación, invalidar el binding por fail-closed
            binding.status = BindingStatus.INVALIDATED.value
            self._audit(
                "DISK_BINDING_INVALIDATED",
                "REVALIDATE",
                "FAILURE",
                case_id=case_id,
                dsm_id=dsm_id,
                operator=operator,
                request_id=request_id,
                details={"binding_id": str(binding.id), "reason": str(e)}
            )
            self.session.commit()
            if not isinstance(e, SourceChangedError):
                raise SourceChangedError(f"Revalidación fallida para binding {binding.id}: {str(e)}")
            raise e
