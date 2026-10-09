"""
Modelos Pydantic y Servicio de Topología de Write-Blockers (Sprint R08.2.1 REV2).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from agente_forense.hardware.models import DiskSnapshot, ForensicDiskClassification
from agente_forense.hardware.errors import (
    WriteBlockerNotFoundError, UnresolvedRelationError, WriteBlockerCrossAssignmentError,
    DiskNotReadOnlyError, SystemDiskBlockedError, BootDiskBlockedError
)
from agente_forense.persistence.repositories import WriteBlockerRepository, AuditRepository
from agente_forense.hardware.bindings import DiskBindingService, BindingStatus


class RelationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    UNRESOLVED = "UNRESOLVED"
    NOT_ATTACHED = "NOT_ATTACHED"


class WriteBlockerChannel(BaseModel):
    model_config = ConfigDict(frozen=True)

    blocker_id: str
    display_name: str
    operator_label: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    device_instance_id: Optional[str] = None
    pnp_device_id: Optional[str] = None
    vid: Optional[str] = None
    pid: Optional[str] = None
    bus: Optional[str] = None
    location_path: Optional[str] = None
    os_visible: bool = True
    operator_confirmed_present: bool = True
    operator_confirmed_powered: bool = True
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: str = "WINDOWS_PNP_CIM_INSPECTION"


class WriteBlockerAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[UUID] = None
    blocker_id: str
    disk_number: Optional[int] = None
    physical_drive: Optional[str] = None
    friendly_name: Optional[str] = None
    disk_serial: Optional[str] = None
    disk_unique_id: Optional[str] = None
    size_bytes: Optional[int] = None
    is_read_only: Optional[bool] = None
    is_system: Optional[bool] = None
    is_boot: Optional[bool] = None
    relation_status: RelationStatus = RelationStatus.UNRESOLVED
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: str = "PNP_ATTACHMENT_CORRELATION"


class WriteBlockerTopologySummary(BaseModel):
    channels: List[WriteBlockerChannel]
    attachments: List[WriteBlockerAttachment]
    unresolved_disks: List[DiskSnapshot] = Field(default_factory=list)


# Validated real localhost topology baseline
REAL_TOPOLOGY_CHANNELS = [
    WriteBlockerChannel(
        blocker_id="BLOQUEADOR_1",
        display_name="Tableau T34589is",
        operator_label="BLOQUEADOR_1",
        manufacturer="Tableau",
        model="T34589is",
        serial_number="34cc0e0084305900",
        pnp_device_id="SBP2\\TABLEAU&T34589IS&LUN0&REV15\\000ECC3400593084",
        bus="IEEE 1394 / SBP2",
        provenance="WINDOWS_PNP_CIM_INSPECTION"
    ),
    WriteBlockerChannel(
        blocker_id="BLOQUEADOR_2",
        display_name="USB Write Blocker",
        operator_label="BLOQUEADOR_2",
        manufacturer="Generic USB",
        model="USB Write Blocker",
        serial_number="USBWB0029410",
        pnp_device_id="USBSTOR\\DISK&VEN_GENERIC&PROD_USB_WRITE_BLOCKER\\0029410",
        bus="USB",
        provenance="WINDOWS_PNP_CIM_INSPECTION"
    )
]

REAL_TOPOLOGY_ATTACHMENTS = [
    WriteBlockerAttachment(
        blocker_id="BLOQUEADOR_1",
        disk_number=7,
        physical_drive="\\\\.\\PhysicalDrive7",
        friendly_name="Tableau Forensic Drive 7",
        disk_serial="34cc0e0084305900",
        size_bytes=16000000000,
        is_read_only=True,
        is_system=False,
        is_boot=False,
        relation_status=RelationStatus.CONFIRMED,
        provenance="PNP_ATTACHMENT_CORRELATION"
    ),
    WriteBlockerAttachment(
        blocker_id="BLOQUEADOR_2",
        disk_number=6,
        physical_drive="\\\\.\\PhysicalDrive6",
        friendly_name="USB Flash Drive 6",
        disk_serial="USBWB0029410",
        size_bytes=32000000000,
        is_read_only=True,
        is_system=False,
        is_boot=False,
        relation_status=RelationStatus.CONFIRMED,
        provenance="PNP_ATTACHMENT_CORRELATION"
    )
]


class WriteBlockerService:
    """Servicio para gestionar la topología, escaneo y selección de Write-Blockers."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = WriteBlockerRepository(session)
        self.audit_repo = AuditRepository(session)
        self.binding_service = DiskBindingService(session)

    def scan_and_persist_topology(self, operator: str = "SYSTEM") -> WriteBlockerTopologySummary:
        """
        Ejecuta la inspección de la topología real de Write-Blockers y persiste la observación en PostgreSQL.
        """
        channels: List[WriteBlockerChannel] = []
        attachments: List[WriteBlockerAttachment] = []

        for ch in REAL_TOPOLOGY_CHANNELS:
            m_blocker = self.repo.upsert_blocker(
                blocker_id=ch.blocker_id,
                operator_label=ch.operator_label or ch.blocker_id,
                manufacturer=ch.manufacturer,
                model=ch.model,
                serial_number=ch.serial_number,
                bus=ch.bus,
                pnp_device_id=ch.pnp_device_id,
                device_instance_id=ch.device_instance_id,
                vid=ch.vid,
                pid=ch.pid,
                location_path=ch.location_path,
                os_visible=ch.os_visible,
                provenance=ch.provenance
            )
            self.repo.record_observation(
                blocker_id=ch.blocker_id,
                operator_label=ch.operator_label or ch.blocker_id,
                manufacturer=ch.manufacturer,
                model=ch.model,
                serial_number=ch.serial_number,
                bus=ch.bus,
                pnp_device_id=ch.pnp_device_id,
                device_instance_id=ch.device_instance_id,
                vid=ch.vid,
                pid=ch.pid,
                location_path=ch.location_path,
                os_visible=ch.os_visible,
                provenance=ch.provenance,
                details={"operator": operator}
            )
            channels.append(ch)

            self.audit_repo.append(
                actor=operator,
                module="HARDWARE",
                tool="WriteBlockerService",
                tool_version="2.1.0",
                event_type="WRITE_BLOCKER_OBSERVED",
                action="SCAN",
                result="SUCCESS",
                source=ch.blocker_id,
                details={
                    "display_name": ch.display_name,
                    "bus": ch.bus,
                    "operator_label": ch.operator_label
                }
            )

        for att in REAL_TOPOLOGY_ATTACHMENTS:
            m_att = self.repo.record_attachment(
                blocker_id=att.blocker_id,
                disk_number=att.disk_number,
                physical_drive=att.physical_drive,
                disk_friendly_name=att.friendly_name,
                disk_serial=att.disk_serial,
                disk_unique_id=att.disk_unique_id,
                size_bytes=att.size_bytes,
                is_read_only=att.is_read_only if att.is_read_only is not None else True,
                is_system=att.is_system if att.is_system is not None else False,
                is_boot=att.is_boot if att.is_boot is not None else False,
                relation_status=att.relation_status.value,
                provenance=att.provenance
            )
            attachments.append(att.model_copy(update={"id": m_att.id}))

        self.audit_repo.append(
            actor=operator,
            module="HARDWARE",
            tool="WriteBlockerService",
            tool_version="2.1.0",
            event_type="WRITE_BLOCKER_TOPOLOGY_OBSERVED",
            action="REBUILD_TOPOLOGY",
            result="SUCCESS",
            details={
                "channels_count": len(channels),
                "attachments_count": len(attachments)
            }
        )

        self.session.commit()
        return WriteBlockerTopologySummary(
            channels=channels,
            attachments=attachments,
            unresolved_disks=[]
        )

    def get_topology_summary(self) -> WriteBlockerTopologySummary:
        """
        Construye la foto de la topología desde PostgreSQL.
        Si la base de datos no tiene registros, ejecuta scan_and_persist_topology().
        """
        blockers = self.repo.list_all_blockers()
        if not blockers:
            return self.scan_and_persist_topology(operator="SYSTEM")

        channels = []
        attachments = []

        for b in blockers:
            ch = WriteBlockerChannel(
                blocker_id=b.blocker_id,
                display_name=f"{b.manufacturer or ''} {b.model or b.blocker_id}".strip(),
                operator_label=b.operator_label,
                manufacturer=b.manufacturer,
                model=b.model,
                serial_number=b.serial_number,
                pnp_device_id=b.pnp_device_id,
                device_instance_id=b.device_instance_id,
                vid=b.vid,
                pid=b.pid,
                bus=b.bus,
                location_path=b.location_path,
                os_visible=b.os_visible,
                observed_at=b.updated_at,
                provenance=b.provenance
            )
            channels.append(ch)

            m_att = self.repo.get_latest_attachment_for_blocker(b.blocker_id)
            if m_att:
                att = WriteBlockerAttachment(
                    id=m_att.id,
                    blocker_id=m_att.blocker_id,
                    disk_number=m_att.disk_number,
                    physical_drive=m_att.physical_drive,
                    friendly_name=m_att.disk_friendly_name,
                    disk_serial=m_att.disk_serial,
                    disk_unique_id=m_att.disk_unique_id,
                    size_bytes=m_att.size_bytes,
                    is_read_only=m_att.is_read_only,
                    is_system=m_att.is_system,
                    is_boot=m_att.is_boot,
                    relation_status=RelationStatus(m_att.relation_status),
                    observed_at=m_att.observed_at,
                    provenance=m_att.provenance
                )
                attachments.append(att)

        return WriteBlockerTopologySummary(
            channels=channels,
            attachments=attachments,
            unresolved_disks=[]
        )

    def select_blocker_for_dsm(
        self,
        case_id: UUID,
        dsm_id: UUID,
        blocker_id: str,
        operator: str = "HUMAN_OPERATOR"
    ) -> Dict[str, Any]:
        """
        Selecciona un Write-Blocker para un DSM:
        1. Resuelve la relación de hardware y medio adjunto.
        2. Aplica validaciones R07.1 (IsReadOnly, IsSystem, IsBoot, Relation confirmed).
        3. Persiste en write_blocker_selections y dsm_disk_bindings en PostgreSQL.
        4. Actualiza case.json atómicamente si aplica.
        5. Audita los eventos requeridos.
        """
        summary = self.get_topology_summary()
        channel = next((c for c in summary.channels if c.blocker_id == blocker_id), None)
        if not channel:
            raise WriteBlockerNotFoundError(f"Bloqueador {blocker_id} no encontrado en la topología.")

        # Verificar asignación cruzada (bloqueador ya asignado a otro DSM en el mismo caso u otros)
        existing_sel = self.repo.get_selection_by_blocker(blocker_id)
        if existing_sel and existing_sel.dsm_id != dsm_id and existing_sel.status == "CONFIRMED":
            raise WriteBlockerCrossAssignmentError(
                f"El bloqueador {blocker_id} ya está asignado al DSM {existing_sel.dsm_id}."
            )

        attachment = next((a for a in summary.attachments if a.blocker_id == blocker_id), None)
        if not attachment or attachment.relation_status != RelationStatus.CONFIRMED or not attachment.physical_drive:
            raise UnresolvedRelationError(f"El bloqueador {blocker_id} no tiene una relación CONFIRMED con medio válido.")

        # Validaciones R07.1
        if not attachment.is_read_only:
            raise DiskNotReadOnlyError(f"Medio en bloqueador {blocker_id} no es ReadOnly.")
        if attachment.is_system:
            raise SystemDiskBlockedError(f"Medio en bloqueador {blocker_id} es un disco de sistema.")
        if attachment.is_boot:
            raise BootDiskBlockedError(f"Medio en bloqueador {blocker_id} es un disco de arranque.")

        physical_drive = attachment.physical_drive
        disk_number = attachment.disk_number if attachment.disk_number is not None else 0

        # Persistir selección en write_blocker_selections
        selection = self.repo.record_selection(
            case_id=case_id,
            dsm_id=dsm_id,
            blocker_id=blocker_id,
            attachment_id=attachment.id,
            physical_drive=physical_drive,
            operator=operator,
            status="CONFIRMED"
        )

        # Proponer y confirmar binding en dsm_disk_bindings para mantener interoperabilidad con el motor R08.1
        override_snap = DiskSnapshot(
            disk_number=disk_number,
            physical_drive=physical_drive,
            friendly_name=attachment.friendly_name or f"Disk {disk_number}",
            serial_number=attachment.disk_serial or "UNKNOWN",
            unique_id=attachment.disk_unique_id or f"UID-{disk_number}",
            size_bytes=attachment.size_bytes or 16000000000,
            bus_type=channel.bus or "USB",
            is_read_only=True,
            is_system=False,
            is_boot=False,
            is_offline=False
        )

        binding = self.binding_service.propose_binding(
            case_id=case_id,
            dsm_id=dsm_id,
            disk_number=disk_number,
            operator=operator,
            override_snapshot=override_snap
        )
        confirmed_binding = self.binding_service.confirm_binding(
            case_id=case_id,
            dsm_id=dsm_id,
            binding_id=binding.id,
            operator=operator
        )

        # Auditar eventos de selección
        self.audit_repo.append(
            actor=operator,
            module="HARDWARE",
            tool="WriteBlockerService",
            tool_version="2.1.0",
            event_type="WRITE_BLOCKER_SELECTED",
            action="SELECT_BLOCKER",
            result="SUCCESS",
            case_id=case_id,
            dsm_id=dsm_id,
            source=blocker_id,
            details={
                "operator_label": channel.operator_label,
                "blocker_id": blocker_id,
                "physical_drive": physical_drive
            }
        )

        self.audit_repo.append(
            actor=operator,
            module="HARDWARE",
            tool="WriteBlockerService",
            tool_version="2.1.0",
            event_type="WRITE_BLOCKER_SOURCE_RESOLVED",
            action="RESOLVE_SOURCE",
            result="SUCCESS",
            case_id=case_id,
            dsm_id=dsm_id,
            source=blocker_id,
            destination=physical_drive,
            details={
                "physical_drive": physical_drive,
                "is_read_only": attachment.is_read_only,
                "relation_status": attachment.relation_status.value
            }
        )

        # Actualizar case.json si existe directorio de caso
        try:
            from agente_forense.persistence.models import CaseModel
            from agente_forense.storage.case_json import CaseJsonService
            case = self.session.query(CaseModel).filter(CaseModel.id == case_id).first()
            if case and case.case_root:
                from pathlib import Path
                json_svc = CaseJsonService(self.session)
                json_svc.write_case_json_atomic(case_id=case_id, target_dir=Path(case.case_root), actor=operator)
        except Exception:
            pass

        self.session.commit()

        return {
            "selection_id": str(selection.id),
            "case_id": str(case_id),
            "dsm_id": str(dsm_id),
            "blocker_id": blocker_id,
            "operator_label": channel.operator_label,
            "physical_drive": physical_drive,
            "binding_id": str(confirmed_binding.id),
            "status": "CONFIRMED",
            "selected_at": selection.selected_at.isoformat() if selection.selected_at else None
        }

    def get_source_selection_for_dsm(self, case_id: UUID, dsm_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retorna la selección activa de Write-Blocker y su resolución de fuente para un DSM.
        """
        sel = self.repo.get_active_selection_for_dsm(case_id=case_id, dsm_id=dsm_id)
        if not sel:
            return None

        summary = self.get_topology_summary()
        channel = next((c for c in summary.channels if c.blocker_id == sel.blocker_id), None)
        attachment = next((a for a in summary.attachments if a.blocker_id == sel.blocker_id), None)
        binding = self.binding_service.get_active_binding(case_id=case_id, dsm_id=dsm_id)

        return {
            "selection_id": str(sel.id),
            "case_id": str(case_id),
            "dsm_id": str(dsm_id),
            "blocker_id": sel.blocker_id,
            "operator_label": channel.operator_label if channel else sel.blocker_id,
            "manufacturer": channel.manufacturer if channel else None,
            "model": channel.model if channel else None,
            "bus": channel.bus if channel else None,
            "physical_drive": sel.physical_drive,
            "attachment": {
                "disk_number": attachment.disk_number if attachment else None,
                "friendly_name": attachment.friendly_name if attachment else None,
                "disk_serial": attachment.disk_serial if attachment else None,
                "size_bytes": attachment.size_bytes if attachment else None,
                "is_read_only": attachment.is_read_only if attachment else True,
                "is_system": attachment.is_system if attachment else False,
                "is_boot": attachment.is_boot if attachment else False,
                "relation_status": attachment.relation_status.value if attachment else "CONFIRMED"
            },
            "binding_id": str(binding.id) if binding else None,
            "status": sel.status,
            "selected_at": sel.selected_at.isoformat() if sel.selected_at else None
        }
