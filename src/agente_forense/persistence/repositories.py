"""
Capa de repositorios tipados para el acceso a datos.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from agente_forense.persistence.models import (
    CaseModel, NueModel, SpeciesModel, DsmModel, FileModel,
    DocumentModel, PhotoModel, HashModel, ToolVersionModel,
    CaseEventModel, AuditEventModel, WriteBlockerModel,
    WriteBlockerObservationModel, WriteBlockerAttachmentModel,
    WriteBlockerSelectionModel, PetitionModel, PetitionEvidenceItemModel,
    PetitionRequestedActionModel, PetitionAttachmentModel, PetitionFieldReviewModel
)
from agente_forense.core.errors import AgenteForenseError


class RepositoryError(AgenteForenseError):
    """Error al realizar operaciones en el repositorio."""
    pass


class CaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        ruc: Optional[str] = None,
        requesting_unit: Optional[str] = None,
        requesting_rut: Optional[str] = None,
        request_type: Optional[str] = None,
        case_root: Optional[str] = None,
        status: str = "NEW"
    ) -> CaseModel:
        case = CaseModel(
            ruc=ruc,
            requesting_unit=requesting_unit,
            requesting_rut=requesting_rut,
            request_type=request_type,
            case_root=case_root,
            status=status
        )
        self.session.add(case)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al crear el caso (RUC posiblemente duplicado: {ruc})") from e
        return case

    def get_by_id(self, case_id: UUID) -> Optional[CaseModel]:
        return self.session.query(CaseModel).filter(CaseModel.id == case_id).first()

    def get_by_ruc(self, ruc: str) -> Optional[CaseModel]:
        return self.session.query(CaseModel).filter(CaseModel.ruc == ruc).first()

    def list_all(self) -> List[CaseModel]:
        return self.session.query(CaseModel).all()

    def update_status(self, case_id: UUID, new_status: str) -> CaseModel:
        case = self.get_by_id(case_id)
        if not case:
            raise RepositoryError(f"Caso con id {case_id} no encontrado.")
        case.status = new_status
        self.session.flush()
        return case


# ==========================================
# REPOSITORIO DE OFICIO PETITORIO (SPRINT P01)
# ==========================================

class PetitionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_petition(
        self,
        file_id: UUID,
        sha256: str,
        document_type: str = "PETITION",
        petition_number: Optional[str] = None,
        petition_date: Optional[str] = None,
        city: Optional[str] = None,
        log_reference: Optional[str] = None,
        ruc: Optional[str] = None,
        crime_context: Optional[str] = None,
        other_references: Optional[str] = None,
        requesting_unit: Optional[str] = None,
        prosecutor_office: Optional[str] = None,
        prosecutor_name: Optional[str] = None,
        investigator_name: Optional[str] = None,
        investigator_rank: Optional[str] = None,
        contact_details: Optional[str] = None,
        addressee: Optional[str] = None,
        informed_copies: Optional[str] = None,
        processing_status: str = "STAGED",
        review_status: str = "PENDING"
    ) -> PetitionModel:
        petition = PetitionModel(
            file_id=file_id,
            sha256=sha256,
            document_type=document_type,
            petition_number=petition_number,
            petition_date=petition_date,
            city=city,
            log_reference=log_reference,
            ruc=ruc,
            crime_context=crime_context,
            other_references=other_references,
            requesting_unit=requesting_unit,
            prosecutor_office=prosecutor_office,
            prosecutor_name=prosecutor_name,
            investigator_name=investigator_name,
            investigator_rank=investigator_rank,
            contact_details=contact_details,
            addressee=addressee,
            informed_copies=informed_copies,
            processing_status=processing_status,
            review_status=review_status
        )
        self.session.add(petition)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al crear el petitorio para file_id {file_id}") from e
        return petition

    def get_by_id(self, petition_id: UUID) -> Optional[PetitionModel]:
        return self.session.query(PetitionModel).filter(PetitionModel.id == petition_id).first()

    def get_by_file_id(self, file_id: UUID) -> Optional[PetitionModel]:
        return self.session.query(PetitionModel).filter(PetitionModel.file_id == file_id).first()

    def get_by_sha256(self, sha256: str) -> Optional[PetitionModel]:
        return self.session.query(PetitionModel).filter(PetitionModel.sha256 == sha256).first()

    def add_evidence_item(
        self,
        petition_id: UUID,
        nue_number: Optional[str] = None,
        quantity: Optional[int] = None,
        description_original: Optional[str] = None,
        evidence_type_declared: Optional[str] = None,
        brand_declared: Optional[str] = None,
        model_declared: Optional[str] = None,
        serial_number_declared: Optional[str] = None,
        capacity_declared: Optional[str] = None,
        source_page: Optional[int] = None,
        source_text: Optional[str] = None
    ) -> PetitionEvidenceItemModel:
        item = PetitionEvidenceItemModel(
            petition_id=petition_id,
            nue_number=nue_number,
            quantity=quantity,
            description_original=description_original,
            evidence_type_declared=evidence_type_declared,
            brand_declared=brand_declared,
            model_declared=model_declared,
            serial_number_declared=serial_number_declared,
            capacity_declared=capacity_declared,
            source_page=source_page,
            source_text=source_text
        )
        self.session.add(item)
        self.session.flush()
        return item

    def add_requested_action(
        self,
        petition_id: UUID,
        action_order: int,
        source_text: str,
        normalized_action: Optional[str] = None,
        source_page: Optional[int] = None
    ) -> PetitionRequestedActionModel:
        action = PetitionRequestedActionModel(
            petition_id=petition_id,
            action_order=action_order,
            source_text=source_text,
            normalized_action=normalized_action,
            source_page=source_page
        )
        self.session.add(action)
        self.session.flush()
        return action

    def add_attachment(
        self,
        petition_id: UUID,
        attachment_type: str = "ACTA",
        description: Optional[str] = None,
        reference_number: Optional[str] = None,
        source_page: Optional[int] = None,
        physically_received: bool = False
    ) -> PetitionAttachmentModel:
        attachment = PetitionAttachmentModel(
            petition_id=petition_id,
            attachment_type=attachment_type,
            description=description,
            reference_number=reference_number,
            source_page=source_page,
            physically_received=physically_received
        )
        self.session.add(attachment)
        self.session.flush()
        return attachment

    def add_field_review(
        self,
        petition_id: UUID,
        field_name: str,
        observed_value: Optional[str] = None,
        proposed_value: Optional[str] = None,
        confirmed_value: Optional[str] = None,
        source_page: Optional[int] = None,
        source_excerpt: Optional[str] = None,
        extraction_method: Optional[str] = None,
        status: str = "EXTRACTED",
        review_action: Optional[str] = None,
        reviewed_by: Optional[str] = None,
        reviewed_at: Optional[Any] = None
    ) -> PetitionFieldReviewModel:
        existing = self.session.query(PetitionFieldReviewModel).filter(
            PetitionFieldReviewModel.petition_id == petition_id,
            PetitionFieldReviewModel.field_name == field_name
        ).first()

        if existing:
            existing.observed_value = observed_value
            existing.proposed_value = proposed_value
            if confirmed_value is not None:
                existing.confirmed_value = confirmed_value
            existing.source_page = source_page
            existing.source_excerpt = source_excerpt
            existing.extraction_method = extraction_method
            existing.status = status
            if review_action:
                existing.review_action = review_action
            if reviewed_by:
                existing.reviewed_by = reviewed_by
            if reviewed_at:
                existing.reviewed_at = reviewed_at
            self.session.flush()
            return existing

        review = PetitionFieldReviewModel(
            petition_id=petition_id,
            field_name=field_name,
            observed_value=observed_value,
            proposed_value=proposed_value,
            confirmed_value=confirmed_value,
            source_page=source_page,
            source_excerpt=source_excerpt,
            extraction_method=extraction_method,
            status=status,
            review_action=review_action,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at
        )
        self.session.add(review)
        self.session.flush()
        return review

    def get_field_reviews(self, petition_id: UUID) -> List[PetitionFieldReviewModel]:
        return self.session.query(PetitionFieldReviewModel).filter(PetitionFieldReviewModel.petition_id == petition_id).all()

    def get_evidence_items(self, petition_id: UUID) -> List[PetitionEvidenceItemModel]:
        return self.session.query(PetitionEvidenceItemModel).filter(PetitionEvidenceItemModel.petition_id == petition_id).all()

    def get_requested_actions(self, petition_id: UUID) -> List[PetitionRequestedActionModel]:
        return self.session.query(PetitionRequestedActionModel).filter(PetitionRequestedActionModel.petition_id == petition_id).all()

    def get_attachments(self, petition_id: UUID) -> List[PetitionAttachmentModel]:
        return self.session.query(PetitionAttachmentModel).filter(PetitionAttachmentModel.petition_id == petition_id).all()

    def update_processing_status(self, petition_id: UUID, status: str) -> PetitionModel:
        petition = self.get_by_id(petition_id)
        if not petition:
            raise RepositoryError(f"Petitorio {petition_id} no encontrado.")
        petition.processing_status = status
        self.session.flush()
        return petition

    def update_review_status(self, petition_id: UUID, status: str) -> PetitionModel:
        petition = self.get_by_id(petition_id)
        if not petition:
            raise RepositoryError(f"Petitorio {petition_id} no encontrado.")
        petition.review_status = status
        self.session.flush()
        return petition


class NueRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        case_id: UUID,
        nue_number: str,
        description_from_petition: Optional[str] = None,
        status: str = "PENDING"
    ) -> NueModel:
        nue = NueModel(
            case_id=case_id,
            nue_number=nue_number,
            description_from_petition=description_from_petition,
            status=status
        )
        self.session.add(nue)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al crear la NUE {nue_number} para el caso {case_id}") from e
        return nue

    def get_by_id(self, nue_id: UUID) -> Optional[NueModel]:
        return self.session.query(NueModel).filter(NueModel.id == nue_id).first()

    def list_by_case(self, case_id: UUID) -> List[NueModel]:
        return self.session.query(NueModel).filter(NueModel.case_id == case_id).all()


class SpeciesRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        nue_id: UUID,
        species_number: int,
        label: str,
        storage_relation: str,
        description: Optional[str] = None,
        status: str = "PENDING"
    ) -> SpeciesModel:
        if storage_relation not in ("SELF_STORAGE", "CONTAINED_STORAGE"):
            raise RepositoryError(f"storage_relation inválido: {storage_relation}")

        species = SpeciesModel(
            nue_id=nue_id,
            species_number=species_number,
            label=label,
            storage_relation=storage_relation,
            description=description,
            status=status
        )
        self.session.add(species)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al crear Especie {species_number} para NUE {nue_id}") from e
        return species

    def get_by_id(self, species_id: UUID) -> Optional[SpeciesModel]:
        return self.session.query(SpeciesModel).filter(SpeciesModel.id == species_id).first()

    def list_by_nue(self, nue_id: UUID) -> List[SpeciesModel]:
        return self.session.query(SpeciesModel).filter(SpeciesModel.nue_id == nue_id).all()


class DsmRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        species_id: UUID,
        dsm_number: int,
        label: str,
        same_physical_object_as_species: bool = True,
        device_type: Optional[str] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        serial: Optional[str] = None,
        capacity_bytes: Optional[int] = None,
        status: str = "PENDING"
    ) -> DsmModel:
        dsm = DsmModel(
            species_id=species_id,
            dsm_number=dsm_number,
            label=label,
            same_physical_object_as_species=same_physical_object_as_species,
            device_type=device_type,
            brand=brand,
            model=model,
            serial=serial,
            capacity_bytes=capacity_bytes,
            status=status
        )
        self.session.add(dsm)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al crear DSM {dsm_number} para especie {species_id}") from e
        return dsm

    def get_by_id(self, dsm_id: UUID) -> Optional[DsmModel]:
        return self.session.query(DsmModel).filter(DsmModel.id == dsm_id).first()

    def list_by_species(self, species_id: UUID) -> List[DsmModel]:
        return self.session.query(DsmModel).filter(DsmModel.species_id == species_id).all()


class FileRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        case_id: UUID,
        file_role: str,
        original_filename: str,
        stored_filename: str,
        relative_path: str,
        mime_type: str,
        size_bytes: int,
        sha256: str,
        source: str,
        nue_id: Optional[UUID] = None,
        species_id: Optional[UUID] = None,
        dsm_id: Optional[UUID] = None,
        integrity_status: str = "VERIFIED"
    ) -> FileModel:
        file_record = FileModel(
            case_id=case_id,
            nue_id=nue_id,
            species_id=species_id,
            dsm_id=dsm_id,
            file_role=file_role,
            original_filename=original_filename,
            stored_filename=stored_filename,
            relative_path=relative_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256=sha256.lower(),
            source=source,
            integrity_status=integrity_status
        )
        self.session.add(file_record)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"Error al insertar metadata de archivo {stored_filename}") from e
        return file_record

    def get_by_id(self, file_id: UUID) -> Optional[FileModel]:
        return self.session.query(FileModel).filter(FileModel.id == file_id).first()

    def get_by_sha256(self, sha256: str) -> Optional[FileModel]:
        return self.session.query(FileModel).filter(FileModel.sha256 == sha256.lower()).first()

    def list_by_case(self, case_id: UUID) -> List[FileModel]:
        return self.session.query(FileModel).filter(FileModel.case_id == case_id).all()


class CaseEventRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_event(
        self,
        case_id: UUID,
        event_type: str,
        result: str,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> CaseEventModel:
        event = CaseEventModel(
            case_id=case_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            result=result,
            details=details
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_by_case(self, case_id: UUID) -> List[CaseEventModel]:
        return self.session.query(CaseEventModel).filter(CaseEventModel.case_id == case_id).order_by(CaseEventModel.created_at.desc()).all()


class AuditRepository:
    """Repositorio append-only para registros de auditoría."""

    def __init__(self, session: Session):
        self.session = session

    def append(
        self,
        actor: str,
        module: str,
        tool: str,
        tool_version: str,
        event_type: str,
        action: str,
        result: str,
        case_id: Optional[UUID] = None,
        nue_id: Optional[UUID] = None,
        species_id: Optional[UUID] = None,
        dsm_id: Optional[UUID] = None,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        exit_code: Optional[int] = None,
        error: Optional[str] = None,
        human_confirmation: bool = False,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEventModel:
        event = AuditEventModel(
            case_id=case_id,
            nue_id=nue_id,
            species_id=species_id,
            dsm_id=dsm_id,
            actor=actor,
            module=module,
            tool=tool,
            tool_version=tool_version,
            event_type=event_type,
            action=action,
            source=source,
            destination=destination,
            previous_state=previous_state,
            new_state=new_state,
            result=result,
            exit_code=exit_code,
            error=error,
            human_confirmation=human_confirmation,
            details=details
        )
        self.session.add(event)
        self.session.flush()
        return event

    def get_by_id(self, audit_id: UUID) -> Optional[AuditEventModel]:
        return self.session.query(AuditEventModel).filter(AuditEventModel.id == audit_id).first()

    def list_by_case(self, case_id: UUID) -> List[AuditEventModel]:
        return self.session.query(AuditEventModel).filter(AuditEventModel.case_id == case_id).all()

    # NOTA: AuditRepository intencionalmente NO ofrece métodos update() ni delete().


class ToolVersionRepository:
    def __init__(self, session: Session):
        self.session = session

    def register_tool(
        self,
        tool_name: str,
        tool_version: str,
        executable_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ToolVersionModel:
        record = ToolVersionModel(
            tool_name=tool_name,
            tool_version=tool_version,
            executable_path=executable_path,
            details=details
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_tools(self) -> List[ToolVersionModel]:
        return self.session.query(ToolVersionModel).all()


class CaseSnapshotRepository:
    """Contrato de interfaz para futura sincronización bidireccional entre PostgreSQL y case.json."""

    def __init__(self, session: Session):
        self.session = session


class WriteBlockerRepository:
    """Repositorio para gestionar Write-Blockers, observaciones, attachments y selecciones."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_blocker(
        self,
        blocker_id: str,
        operator_label: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        bus: Optional[str] = None,
        pnp_device_id: Optional[str] = None,
        device_instance_id: Optional[str] = None,
        vid: Optional[str] = None,
        pid: Optional[str] = None,
        location_path: Optional[str] = None,
        os_visible: bool = True,
        provenance: str = "WINDOWS_PNP_CIM_INSPECTION"
    ) -> WriteBlockerModel:
        blocker = self.session.query(WriteBlockerModel).filter(WriteBlockerModel.blocker_id == blocker_id).first()
        if not blocker:
            blocker = WriteBlockerModel(
                blocker_id=blocker_id,
                operator_label=operator_label,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                bus=bus,
                pnp_device_id=pnp_device_id,
                device_instance_id=device_instance_id,
                vid=vid,
                pid=pid,
                location_path=location_path,
                os_visible=os_visible,
                provenance=provenance
            )
            self.session.add(blocker)
        else:
            blocker.operator_label = operator_label
            blocker.manufacturer = manufacturer
            blocker.model = model
            blocker.serial_number = serial_number
            blocker.bus = bus
            blocker.pnp_device_id = pnp_device_id
            blocker.device_instance_id = device_instance_id
            blocker.vid = vid
            blocker.pid = pid
            blocker.location_path = location_path
            blocker.os_visible = os_visible
            blocker.provenance = provenance
        self.session.flush()
        return blocker

    def record_observation(
        self,
        blocker_id: str,
        operator_label: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        bus: Optional[str] = None,
        pnp_device_id: Optional[str] = None,
        device_instance_id: Optional[str] = None,
        vid: Optional[str] = None,
        pid: Optional[str] = None,
        location_path: Optional[str] = None,
        os_visible: bool = True,
        provenance: str = "WINDOWS_PNP_CIM_INSPECTION",
        details: Optional[Dict[str, Any]] = None
    ) -> WriteBlockerObservationModel:
        obs = WriteBlockerObservationModel(
            blocker_id=blocker_id,
            operator_label=operator_label,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            bus=bus,
            pnp_device_id=pnp_device_id,
            device_instance_id=device_instance_id,
            vid=vid,
            pid=pid,
            location_path=location_path,
            os_visible=os_visible,
            provenance=provenance,
            details=details
        )
        self.session.add(obs)
        self.session.flush()
        return obs

    def record_attachment(
        self,
        blocker_id: str,
        disk_number: Optional[int] = None,
        physical_drive: Optional[str] = None,
        disk_friendly_name: Optional[str] = None,
        disk_serial: Optional[str] = None,
        disk_unique_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        is_read_only: bool = True,
        is_system: bool = False,
        is_boot: bool = False,
        relation_status: str = "CONFIRMED",
        provenance: str = "PNP_ATTACHMENT_CORRELATION"
    ) -> WriteBlockerAttachmentModel:
        attachment = WriteBlockerAttachmentModel(
            blocker_id=blocker_id,
            disk_number=disk_number,
            physical_drive=physical_drive,
            disk_friendly_name=disk_friendly_name,
            disk_serial=disk_serial,
            disk_unique_id=disk_unique_id,
            size_bytes=size_bytes,
            is_read_only=is_read_only,
            is_system=is_system,
            is_boot=is_boot,
            relation_status=relation_status,
            provenance=provenance
        )
        self.session.add(attachment)
        self.session.flush()
        return attachment

    def record_selection(
        self,
        case_id: UUID,
        dsm_id: UUID,
        blocker_id: str,
        attachment_id: Optional[UUID],
        physical_drive: str,
        operator: str = "HUMAN_OPERATOR",
        status: str = "CONFIRMED"
    ) -> WriteBlockerSelectionModel:
        selection = self.session.query(WriteBlockerSelectionModel).filter(
            WriteBlockerSelectionModel.case_id == case_id,
            WriteBlockerSelectionModel.dsm_id == dsm_id
        ).first()

        if selection:
            selection.blocker_id = blocker_id
            selection.attachment_id = attachment_id
            selection.physical_drive = physical_drive
            selection.operator = operator
            selection.status = status
        else:
            selection = WriteBlockerSelectionModel(
                case_id=case_id,
                dsm_id=dsm_id,
                blocker_id=blocker_id,
                attachment_id=attachment_id,
                physical_drive=physical_drive,
                operator=operator,
                status=status
            )
            self.session.add(selection)
        self.session.flush()
        return selection

    def get_blocker_by_id(self, blocker_id: str) -> Optional[WriteBlockerModel]:
        return self.session.query(WriteBlockerModel).filter(WriteBlockerModel.blocker_id == blocker_id).first()

    def list_all_blockers(self) -> List[WriteBlockerModel]:
        return self.session.query(WriteBlockerModel).order_by(WriteBlockerModel.blocker_id.asc()).all()

    def get_latest_attachment_for_blocker(self, blocker_id: str) -> Optional[WriteBlockerAttachmentModel]:
        return self.session.query(WriteBlockerAttachmentModel).filter(
            WriteBlockerAttachmentModel.blocker_id == blocker_id
        ).order_by(WriteBlockerAttachmentModel.created_at.desc()).first()

    def get_active_selection_for_dsm(self, case_id: UUID, dsm_id: UUID) -> Optional[WriteBlockerSelectionModel]:
        return self.session.query(WriteBlockerSelectionModel).filter(
            WriteBlockerSelectionModel.case_id == case_id,
            WriteBlockerSelectionModel.dsm_id == dsm_id,
            WriteBlockerSelectionModel.status == "CONFIRMED"
        ).first()

    def get_selection_by_blocker(self, blocker_id: str) -> Optional[WriteBlockerSelectionModel]:
        return self.session.query(WriteBlockerSelectionModel).filter(
            WriteBlockerSelectionModel.blocker_id == blocker_id,
            WriteBlockerSelectionModel.status == "CONFIRMED"
        ).first()


    def generate_snapshot_data(self, case_id: UUID) -> Dict[str, Any]:
        """Genera un diccionario representativo del snapshot portable de case.json."""
        case = self.session.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not case:
            raise RepositoryError(f"Caso {case_id} no encontrado")

        return {
            "case_id": str(case.id),
            "ruc": case.ruc,
            "status": case.status,
            "requesting_unit": case.requesting_unit,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "nues_count": len(case.nues),
            "files_count": len(case.files),
        }
