"""
Estructura CaseStructureDraft para validar y preparar la jerarquía antes de la persistencia.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import uuid

from agente_forense.domain.enums import StorageRelation, CaseStatus
from agente_forense.domain.validation import validate_ruc, validate_nue
from agente_forense.domain.errors import (
    DuplicateNUEError, DuplicateSpeciesError, DuplicateDSMError, InvalidStorageTopologyError
)
from agente_forense.domain.hierarchy import (
    CaseDomain, NUEDomain, SpeciesDomain, DSMDomain,
    make_label_species, make_label_dsm
)


@dataclass
class DSMDraft:
    dsm_number: int
    same_physical_object_as_species: bool = True
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    capacity_bytes: Optional[int] = None


@dataclass
class SpeciesDraft:
    species_number: int
    storage_relation: StorageRelation
    dsms: List[DSMDraft] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class NUEDraft:
    nue_number: str
    species: List[SpeciesDraft] = field(default_factory=list)
    description_from_petition: Optional[str] = None


@dataclass
class CaseStructureDraft:
    ruc: str
    nues: List[NUEDraft] = field(default_factory=list)
    requesting_unit: Optional[str] = None
    requesting_rut: Optional[str] = None
    request_type: Optional[str] = None

    def validate(self) -> None:
        """
        Valida exhaustivamente todas las invariantes del borrador:
        - RUC sintáctico y seguro.
        - NUEs sintácticas y no duplicadas.
        - Especies correlativas y no duplicadas.
        - DSMs correlativos y no duplicados.
        - Invariantes de SELF_STORAGE vs CONTAINED_STORAGE.
        """
        validated_ruc = validate_ruc(self.ruc)
        self.ruc = validated_ruc

        seen_nues = set()
        for nue_draft in self.nues:
            val_nue = validate_nue(nue_draft.nue_number)
            nue_draft.nue_number = val_nue
            if val_nue in seen_nues:
                raise DuplicateNUEError(f"NUE duplicada en el borrador: {val_nue}")
            seen_nues.add(val_nue)

            seen_species = set()
            for sp_draft in nue_draft.species:
                if sp_draft.species_number in seen_species:
                    raise DuplicateSpeciesError(
                        f"Especie {sp_draft.species_number} duplicada en la NUE {val_nue}"
                    )
                seen_species.add(sp_draft.species_number)

                # Validaciones de topología física
                if sp_draft.storage_relation == StorageRelation.SELF_STORAGE:
                    if len(sp_draft.dsms) == 0:
                        # Auto-construir el DSM 1 implícito para SELF_STORAGE si no fue provisto
                        sp_draft.dsms = [DSMDraft(dsm_number=1, same_physical_object_as_species=True)]
                    elif len(sp_draft.dsms) != 1:
                        raise InvalidStorageTopologyError(
                            f"SELF_STORAGE exige exactamente 1 DSM, pero se enviaron {len(sp_draft.dsms)}"
                        )

                    dsm_0 = sp_draft.dsms[0]
                    if dsm_0.dsm_number != 1:
                        raise InvalidStorageTopologyError(
                            f"SELF_STORAGE exige que dsm_number sea 1, recibido: {dsm_0.dsm_number}"
                        )
                    dsm_0.same_physical_object_as_species = True

                elif sp_draft.storage_relation == StorageRelation.CONTAINED_STORAGE:
                    if len(sp_draft.dsms) < 1:
                        raise InvalidStorageTopologyError(
                            f"CONTAINED_STORAGE exige 1 o más DSMs en la Especie {sp_draft.species_number}"
                        )

                seen_dsms = set()
                for dsm_draft in sp_draft.dsms:
                    if dsm_draft.dsm_number in seen_dsms:
                        raise DuplicateDSMError(
                            f"DSM {dsm_draft.dsm_number} duplicado en la Especie {sp_draft.species_number}"
                        )
                    seen_dsms.add(dsm_draft.dsm_number)

    def to_domain(self) -> CaseDomain:
        """Convierte el borrador validado en un objeto CaseDomain listo para persistir."""
        self.validate()

        nues_domain = []
        for nue_d in self.nues:
            species_domain = []
            for sp_d in nue_d.species:
                dsms_domain = []
                for dsm_d in sp_d.dsms:
                    dsm_label = make_label_dsm(
                        nue_d.nue_number, sp_d.species_number, dsm_d.dsm_number
                    )
                    dsms_domain.append(
                        DSMDomain(
                            dsm_number=dsm_d.dsm_number,
                            same_physical_object_as_species=dsm_d.same_physical_object_as_species,
                            label=dsm_label,
                            device_type=dsm_d.device_type,
                            brand=dsm_d.brand,
                            model=dsm_d.model,
                            serial=dsm_d.serial,
                            capacity_bytes=dsm_d.capacity_bytes,
                        )
                    )

                sp_label = make_label_species(nue_d.nue_number, sp_d.species_number)
                sp_dom = SpeciesDomain(
                    species_number=sp_d.species_number,
                    storage_relation=sp_d.storage_relation,
                    label=sp_label,
                    description=sp_d.description,
                    dsms=dsms_domain,
                )
                species_domain.append(sp_dom)

            nue_dom = NUEDomain(
                nue_number=nue_d.nue_number,
                description_from_petition=nue_d.description_from_petition,
                species=species_domain,
            )
            nues_domain.append(nue_dom)

        return CaseDomain(
            ruc=self.ruc,
            requesting_unit=self.requesting_unit,
            requesting_rut=self.requesting_rut,
            request_type=self.request_type,
            nues=nues_domain,
        )
