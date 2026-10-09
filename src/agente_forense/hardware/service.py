"""
Servicio unificado de hardware para orquestación de escaneo, matching, binding y revalidación.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from agente_forense.hardware.models import (
    DiskSnapshot, ClassifiedDisk, DsmDiskComparison, ForensicDiskClassification
)
from agente_forense.hardware.disks import DiskScanner
from agente_forense.hardware.matching import compare_dsm_with_disk
from agente_forense.hardware.bindings import DiskBindingService, DsmDiskBindingModel
from agente_forense.persistence.models import DsmModel


class HardwareService:
    """Servicio de alto nivel para operaciones de hardware en Agente Forense."""

    def __init__(self, session: Session, scanner: Optional[DiskScanner] = None):
        self.session = session
        self.scanner = scanner or DiskScanner()
        self.binding_service = DiskBindingService(session, self.scanner)

    def scan_and_classify_disks(self, case_id: Optional[UUID] = None, operator: str = "SYSTEM") -> List[ClassifiedDisk]:
        return self.binding_service.scan_system_disks(case_id=case_id, operator=operator)

    def get_disk_candidates_for_dsm(
        self,
        case_id: UUID,
        dsm_id: UUID,
        operator: str = "SYSTEM"
    ) -> List[Tuple[ClassifiedDisk, DsmDiskComparison]]:
        dsm = self.session.query(DsmModel).filter(DsmModel.id == dsm_id).first()
        if not dsm:
            raise ValueError(f"DSM {dsm_id} no encontrado en el caso {case_id}")

        dsm_data = {
            "id": str(dsm.id),
            "brand": dsm.brand,
            "model": dsm.model,
            "serial": dsm.serial,
            "capacity_bytes": dsm.capacity_bytes
        }

        classified_disks = self.scan_and_classify_disks(case_id=case_id, operator=operator)
        results = []
        for c in classified_disks:
            comp = compare_dsm_with_disk(dsm_data, c.snapshot)
            results.append((c, comp))

        return results
