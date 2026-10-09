"""
Definiciones y clases de jerarquía de dominio (RUC -> NUE -> ESPECIE -> DSM).
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import uuid
from datetime import datetime, timezone

from agente_forense.domain.enums import (
    StorageRelation, CaseStatus, IdentificationStatus,
    AcquisitionStatus, VerificationStatus
)
from agente_forense.domain.errors import (
    InvalidStorageTopologyError, DuplicateSpeciesError, DuplicateDSMError
)


def make_label_ruc(ruc: str) -> str:
    return f"RUC_{ruc}"


def make_label_nue(nue: str) -> str:
    return f"NUE_{nue}"


def make_label_species(nue: str, species_number: int) -> str:
    return f"NUE_{nue}_ESPECIE{species_number}"


def make_label_dsm(nue: str, species_number: int, dsm_number: int) -> str:
    return f"NUE_{nue}_ESPECIE{species_number}_DSM{dsm_number}"


@dataclass
class DSMDomain:
    dsm_number: int
    same_physical_object_as_species: bool
    id: Optional[uuid.UUID] = field(default_factory=uuid.uuid4)
    label: str = ""
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    capacity_bytes: Optional[int] = None
    physical_drive: Optional[str] = None
    acquisition_status: str = AcquisitionStatus.PENDING.value
    verification_status: str = VerificationStatus.PENDING.value


@dataclass
class SpeciesDomain:
    species_number: int
    storage_relation: StorageRelation
    dsms: List[DSMDomain] = field(default_factory=list)
    id: Optional[uuid.UUID] = field(default_factory=uuid.uuid4)
    label: str = ""
    description: Optional[str] = None
    identification_status: str = IdentificationStatus.PENDING.value

    def validate_topology(self) -> None:
        if self.storage_relation == StorageRelation.SELF_STORAGE:
            if len(self.dsms) != 1:
                raise InvalidStorageTopologyError(
                    f"SELF_STORAGE exige exactamente 1 DSM, pero se recibieron {len(self.dsms)}"
                )
            if self.dsms[0].dsm_number != 1:
                raise InvalidStorageTopologyError(
                    f"SELF_STORAGE exige que el DSM tenga dsm_number=1, pero tiene {self.dsms[0].dsm_number}"
                )
            if not self.dsms[0].same_physical_object_as_species:
                raise InvalidStorageTopologyError(
                    "SELF_STORAGE exige que same_physical_object_as_species sea True"
                )
        elif self.storage_relation == StorageRelation.CONTAINED_STORAGE:
            if len(self.dsms) < 1:
                raise InvalidStorageTopologyError(
                    "CONTAINED_STORAGE exige 1 o más DSM"
                )

        # Validar correlatividad y unicidad de DSMs
        seen_numbers = set()
        for idx, dsm in enumerate(self.dsms, start=1):
            if dsm.dsm_number in seen_numbers:
                raise DuplicateDSMError(f"DSM number duplicado {dsm.dsm_number} en la Especie")
            seen_numbers.add(dsm.dsm_number)


@dataclass
class NUEDomain:
    nue_number: str
    species: List[SpeciesDomain] = field(default_factory=list)
    id: Optional[uuid.UUID] = field(default_factory=uuid.uuid4)
    description_from_petition: Optional[str] = None
    status: str = "PENDING"

    def validate(self) -> None:
        seen_species = set()
        for sp in self.species:
            if sp.species_number in seen_species:
                raise DuplicateSpeciesError(f"Species number duplicada {sp.species_number} en la NUE {self.nue_number}")
            seen_species.add(sp.species_number)
            sp.validate_topology()


@dataclass
class CaseDomain:
    ruc: str
    nues: List[NUEDomain] = field(default_factory=list)
    id: Optional[uuid.UUID] = field(default_factory=uuid.uuid4)
    status: str = CaseStatus.NEW.value
    requesting_unit: Optional[str] = None
    requesting_rut: Optional[str] = None
    request_type: Optional[str] = None
    case_root: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
