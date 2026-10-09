"""
Servicios de aplicación para orquestación de transacciones y operaciones de dominio.
"""

from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from agente_forense.domain import (
    CaseStructureDraft, CaseDomain, CaseAlreadyExistsError,
    DuplicateNUEError, DuplicateSpeciesError, DuplicateDSMError
)
from agente_forense.persistence.models import (
    CaseModel, NueModel, SpeciesModel, DsmModel, AuditEventModel
)
from agente_forense.persistence.repositories import (
    CaseRepository, NueRepository, SpeciesRepository, DsmRepository, AuditRepository
)


class CaseApplicationService:
    """
    Servicio de aplicación para coordinar la creación transaccional de estructuras de caso.
    Garantiza atoricidad: si falla la creación de cualquier entidad (case, nue, especie, dsm),
    se realiza un rollback completo.
    """

    def __init__(self, session: Session):
        self.session = session
        self.case_repo = CaseRepository(session)
        self.nue_repo = NueRepository(session)
        self.species_repo = SpeciesRepository(session)
        self.dsm_repo = DsmRepository(session)
        self.audit_repo = AuditRepository(session)

    def create_case_from_draft(
        self,
        draft: CaseStructureDraft,
        actor: str = "SYSTEM",
        request_id: Optional[str] = None
    ) -> CaseModel:
        """
        Valida el draft y persiste transaccionalmente toda la jerarquía en PostgreSQL.
        Lanza excepciones de dominio específicas en caso de violaciones.
        """
        # 1. Validar y transformar a domain
        domain_case: CaseDomain = draft.to_domain()

        # 2. Verificar existencia previa de RUC en DB
        existing = self.case_repo.get_by_ruc(domain_case.ruc)
        if existing:
            raise CaseAlreadyExistsError(f"El RUC '{domain_case.ruc}' ya se encuentra registrado.")

        try:
            # 3. Transacción atómica
            case_record = self.case_repo.create(
                ruc=domain_case.ruc,
                requesting_unit=domain_case.requesting_unit,
                requesting_rut=domain_case.requesting_rut,
                request_type=domain_case.request_type,
                case_root=domain_case.case_root,
                status=domain_case.status
            )

            # Auditar CASE_CREATED
            self.audit_repo.append(
                actor=actor,
                module="DOMAIN",
                tool="CaseApplicationService",
                tool_version="1.0.0",
                event_type="CASE_CREATED",
                action="CREATE_CASE",
                result="SUCCESS",
                case_id=case_record.id,
                details={"ruc": case_record.ruc, "request_id": request_id}
            )

            for nue_d in domain_case.nues:
                nue_record = self.nue_repo.create(
                    case_id=case_record.id,
                    nue_number=nue_d.nue_number,
                    description_from_petition=nue_d.description_from_petition,
                    status=nue_d.status
                )

                # Auditar NUE_ADDED
                self.audit_repo.append(
                    actor=actor,
                    module="DOMAIN",
                    tool="CaseApplicationService",
                    tool_version="1.0.0",
                    event_type="NUE_ADDED",
                    action="ADD_NUE",
                    result="SUCCESS",
                    case_id=case_record.id,
                    nue_id=nue_record.id,
                    details={"nue_number": nue_record.nue_number, "request_id": request_id}
                )

                for sp_d in nue_d.species:
                    sp_record = self.species_repo.create(
                        nue_id=nue_record.id,
                        species_number=sp_d.species_number,
                        label=sp_d.label or f"NUE_{nue_d.nue_number}_ESPECIE{sp_d.species_number}",
                        storage_relation=sp_d.storage_relation.value if hasattr(sp_d.storage_relation, 'value') else str(sp_d.storage_relation),
                        description=sp_d.description,
                        status=sp_d.identification_status
                    )

                    # Auditar SPECIES_ADDED
                    self.audit_repo.append(
                        actor=actor,
                        module="DOMAIN",
                        tool="CaseApplicationService",
                        tool_version="1.0.0",
                        event_type="SPECIES_ADDED",
                        action="ADD_SPECIES",
                        result="SUCCESS",
                        case_id=case_record.id,
                        nue_id=nue_record.id,
                        species_id=sp_record.id,
                        details={"species_number": sp_record.species_number, "label": sp_record.label, "request_id": request_id}
                    )

                    for dsm_d in sp_d.dsms:
                        dsm_record = self.dsm_repo.create(
                            species_id=sp_record.id,
                            dsm_number=dsm_d.dsm_number,
                            label=dsm_d.label,
                            same_physical_object_as_species=dsm_d.same_physical_object_as_species,
                            device_type=dsm_d.device_type,
                            brand=dsm_d.brand,
                            model=dsm_d.model,
                            serial=dsm_d.serial,
                            capacity_bytes=dsm_d.capacity_bytes,
                            status=dsm_d.acquisition_status
                        )

                        # Auditar DSM_ADDED
                        self.audit_repo.append(
                            actor=actor,
                            module="DOMAIN",
                            tool="CaseApplicationService",
                            tool_version="1.0.0",
                            event_type="DSM_ADDED",
                            action="ADD_DSM",
                            result="SUCCESS",
                            case_id=case_record.id,
                            nue_id=nue_record.id,
                            species_id=sp_record.id,
                            dsm_id=dsm_record.id,
                            details={"dsm_number": dsm_record.dsm_number, "label": dsm_record.label, "request_id": request_id}
                        )

            self.session.commit()
            return case_record

        except Exception as e:
            self.session.rollback()
            raise e
