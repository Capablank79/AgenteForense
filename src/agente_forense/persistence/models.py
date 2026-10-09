"""
Modelos ORM SQLAlchemy mapeados al esquema 'forensic'.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import (
    Column, String, Text, BigInteger, Boolean, Integer,
    ForeignKey, UniqueConstraint, CheckConstraint, DateTime, Table
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from agente_forense.persistence.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SchemaMigrationModel(Base):
    __tablename__ = "schema_migrations"
    __table_args__ = {"schema": "forensic"}

    version = Column(String(64), primary_key=True)
    description = Column(Text, nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class CaseModel(Base):
    __tablename__ = "cases"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ruc = Column(String(64), unique=True, nullable=True)
    status = Column(String(64), nullable=False, default="NEW")
    requesting_unit = Column(String(255), nullable=True)
    requesting_rut = Column(String(64), nullable=True)
    request_type = Column(String(128), nullable=True)
    case_root = Column(Text, nullable=True)
    state_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    nues = relationship("NueModel", back_populates="case", passive_deletes=False)
    files = relationship("FileModel", back_populates="case", passive_deletes=False)
    events = relationship("CaseEventModel", back_populates="case", passive_deletes=False)


class NueModel(Base):
    __tablename__ = "nues"
    __table_args__ = (
        UniqueConstraint("case_id", "nue_number", name="unique_case_nue"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    nue_number = Column(String(64), nullable=False)
    description_from_petition = Column(Text, nullable=True)
    status = Column(String(64), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    case = relationship("CaseModel", back_populates="nues")
    species = relationship("SpeciesModel", back_populates="nue", passive_deletes=False)


class SpeciesModel(Base):
    __tablename__ = "species"
    __table_args__ = (
        UniqueConstraint("nue_id", "species_number", name="unique_nue_species"),
        CheckConstraint("storage_relation IN ('SELF_STORAGE', 'CONTAINED_STORAGE')", name="check_storage_relation"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nue_id = Column(UUID(as_uuid=True), ForeignKey("forensic.nues.id", ondelete="RESTRICT"), nullable=False)
    species_number = Column(Integer, nullable=False)
    label = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    storage_relation = Column(String(64), nullable=False)
    status = Column(String(64), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    nue = relationship("NueModel", back_populates="species")
    dsms = relationship("DsmModel", back_populates="species", passive_deletes=False)


class DsmModel(Base):
    __tablename__ = "dsms"
    __table_args__ = (
        UniqueConstraint("species_id", "dsm_number", name="unique_species_dsm"),
        CheckConstraint("capacity_bytes IS NULL OR capacity_bytes >= 0", name="check_dsm_capacity"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species_id = Column(UUID(as_uuid=True), ForeignKey("forensic.species.id", ondelete="RESTRICT"), nullable=False)
    dsm_number = Column(Integer, nullable=False)
    label = Column(String(128), nullable=False)
    same_physical_object_as_species = Column(Boolean, nullable=False, default=True)
    device_type = Column(String(64), nullable=True)
    brand = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    serial = Column(String(128), nullable=True)
    capacity_bytes = Column(BigInteger, nullable=True)
    status = Column(String(64), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    species = relationship("SpeciesModel", back_populates="dsms")


class FileModel(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint(
            "file_role IN ('PETITION', 'PHOTO', 'E01', 'AXIOM_EXPORT', 'PROCESS_SHEET', 'PORTABLE', 'RAR', 'REPORT', 'LOG', 'METADATA', 'OTHER')",
            name="check_file_role"
        ),
        CheckConstraint("size_bytes >= 0", name="check_file_size"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    nue_id = Column(UUID(as_uuid=True), ForeignKey("forensic.nues.id", ondelete="RESTRICT"), nullable=True)
    species_id = Column(UUID(as_uuid=True), ForeignKey("forensic.species.id", ondelete="RESTRICT"), nullable=True)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=True)
    file_role = Column(String(64), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    relative_path = Column(Text, nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False)
    integrity_status = Column(String(32), nullable=False, default="VERIFIED")
    source = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    case = relationship("CaseModel", back_populates="files")


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("document_type IN ('PETITION', 'REPORT', 'OTHER')", name="check_doc_type"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("forensic.files.id", ondelete="RESTRICT"), nullable=False)
    document_type = Column(String(64), nullable=False)
    ocr_status = Column(String(32), nullable=False, default="NOT_PROCESSED")
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class PhotoModel(Base):
    __tablename__ = "photos"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("forensic.files.id", ondelete="RESTRICT"), nullable=False)
    photo_type = Column(String(64), nullable=False, default="GENERAL")
    classification_status = Column(String(32), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class HashModel(Base):
    __tablename__ = "hashes"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("forensic.files.id", ondelete="RESTRICT"), nullable=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=True)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=True)
    algorithm = Column(String(32), nullable=False)
    hash_value = Column(Text, nullable=False)
    source = Column(String(64), nullable=False)
    verification_status = Column(String(32), nullable=False, default="VERIFIED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ToolVersionModel(Base):
    __tablename__ = "tool_versions"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_name = Column(String(128), nullable=False)
    tool_version = Column(String(128), nullable=False)
    executable_path = Column(Text, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    details = Column(JSONB, nullable=True)


class CaseEventModel(Base):
    __tablename__ = "case_events"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    event_type = Column(String(64), nullable=False)
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=True)
    result = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    details = Column(JSONB, nullable=True)

    case = relationship("CaseModel", back_populates="events")


class AuditLogModel(Base):
    __tablename__ = "audit_events"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=True)
    nue_id = Column(UUID(as_uuid=True), ForeignKey("forensic.nues.id", ondelete="RESTRICT"), nullable=True)
    species_id = Column(UUID(as_uuid=True), ForeignKey("forensic.species.id", ondelete="RESTRICT"), nullable=True)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=True)
    actor = Column(String(128), nullable=False)
    module = Column(String(64), nullable=False)
    tool = Column(String(64), nullable=False)
    tool_version = Column(String(32), nullable=False)
    event_type = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    source = Column(Text, nullable=True)
    destination = Column(Text, nullable=True)
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=True)
    result = Column(String(32), nullable=False)
    exit_code = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    human_confirmation = Column(Boolean, nullable=False, default=False)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)

AuditEventModel = AuditLogModel


class HumanConfirmationModel(Base):
    __tablename__ = "human_confirmations"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    confirmation_id = Column(String(128), unique=True, nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    requested_action = Column(String(128), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="PENDING")
    operator = Column(String(128), nullable=True)
    request_id = Column(String(128), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)


class AcquisitionModel(Base):
    __tablename__ = "acquisitions"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=False)
    binding_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsm_disk_bindings.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(64), nullable=False, default="PREPARED")
    target_basename = Column(Text, nullable=False)
    target_directory = Column(Text, nullable=False)
    expected_e01_path = Column(Text, nullable=False)
    acquisition_json_path = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class AcquisitionJobModel(Base):
    __tablename__ = "acquisition_jobs"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(128), unique=True, nullable=False)
    acquisition_id = Column(UUID(as_uuid=True), ForeignKey("forensic.acquisitions.id", ondelete="RESTRICT"), nullable=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=False)
    binding_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsm_disk_bindings.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(64), nullable=False, default="PREPARED")
    pid = Column(Integer, nullable=True)
    command_json = Column(JSONB, nullable=False)
    stdout_path = Column(Text, nullable=False)
    stderr_path = Column(Text, nullable=False)
    native_log_path = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    exit_code = Column(Integer, nullable=True)
    error_code = Column(String(128), nullable=True)
    human_confirmation_exact = Column(String(64), nullable=True)
    human_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    operator = Column(String(128), nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class WriteBlockerModel(Base):
    __tablename__ = "write_blockers"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(String(128), unique=True, nullable=False)
    operator_label = Column(String(128), nullable=False)
    manufacturer = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    serial_number = Column(String(128), nullable=True)
    bus = Column(String(64), nullable=True)
    pnp_device_id = Column(Text, nullable=True)
    device_instance_id = Column(Text, nullable=True)
    vid = Column(String(32), nullable=True)
    pid = Column(String(32), nullable=True)
    location_path = Column(Text, nullable=True)
    os_visible = Column(Boolean, nullable=False, default=True)
    provenance = Column(String(128), nullable=False, default="WINDOWS_PNP_CIM_INSPECTION")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class WriteBlockerObservationModel(Base):
    __tablename__ = "write_blocker_observations"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(String(128), ForeignKey("forensic.write_blockers.blocker_id", ondelete="RESTRICT"), nullable=False)
    operator_label = Column(String(128), nullable=False)
    manufacturer = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    serial_number = Column(String(128), nullable=True)
    bus = Column(String(64), nullable=True)
    pnp_device_id = Column(Text, nullable=True)
    device_instance_id = Column(Text, nullable=True)
    vid = Column(String(32), nullable=True)
    pid = Column(String(32), nullable=True)
    location_path = Column(Text, nullable=True)
    os_visible = Column(Boolean, nullable=False, default=True)
    provenance = Column(String(128), nullable=False, default="WINDOWS_PNP_CIM_INSPECTION")
    observed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    details = Column(JSONB, nullable=True)


class WriteBlockerAttachmentModel(Base):
    __tablename__ = "write_blocker_attachments"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(String(128), ForeignKey("forensic.write_blockers.blocker_id", ondelete="RESTRICT"), nullable=False)
    disk_number = Column(Integer, nullable=True)
    physical_drive = Column(String(128), nullable=True)
    disk_friendly_name = Column(String(255), nullable=True)
    disk_serial = Column(String(128), nullable=True)
    disk_unique_id = Column(String(255), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    is_read_only = Column(Boolean, nullable=False, default=True)
    is_system = Column(Boolean, nullable=False, default=False)
    is_boot = Column(Boolean, nullable=False, default=False)
    relation_status = Column(String(64), nullable=False, default="CONFIRMED")
    provenance = Column(String(128), nullable=False, default="PNP_ATTACHMENT_CORRELATION")
    observed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class WriteBlockerSelectionModel(Base):
    __tablename__ = "write_blocker_selections"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("forensic.cases.id", ondelete="RESTRICT"), nullable=False)
    dsm_id = Column(UUID(as_uuid=True), ForeignKey("forensic.dsms.id", ondelete="RESTRICT"), nullable=False)
    blocker_id = Column(String(128), ForeignKey("forensic.write_blockers.blocker_id", ondelete="RESTRICT"), nullable=False)
    attachment_id = Column(UUID(as_uuid=True), ForeignKey("forensic.write_blocker_attachments.id", ondelete="RESTRICT"), nullable=True)
    physical_drive = Column(String(128), nullable=False)
    operator = Column(String(128), nullable=False, default="HUMAN_OPERATOR")
    status = Column(String(64), nullable=False, default="CONFIRMED")
    selected_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


# ==========================================
# MODELOS DE PERSISTENCIA DEL OFICIO PETITORIO (SPRINT P01)
# ==========================================

class PetitionModel(Base):
    __tablename__ = "petitions"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("forensic.files.id", ondelete="RESTRICT"), nullable=False)

    document_type = Column(String(64), nullable=False, default="PETITION")
    petition_number = Column(String(128), nullable=True)
    petition_date = Column(String(64), nullable=True)
    city = Column(String(128), nullable=True)
    log_reference = Column(String(128), nullable=True)

    ruc = Column(String(64), nullable=True)
    crime_context = Column(Text, nullable=True)
    other_references = Column(Text, nullable=True)

    requesting_unit = Column(String(255), nullable=True)
    prosecutor_office = Column(String(255), nullable=True)
    prosecutor_name = Column(String(255), nullable=True)
    investigator_name = Column(String(255), nullable=True)
    investigator_rank = Column(String(128), nullable=True)
    contact_details = Column(Text, nullable=True)
    addressee = Column(String(255), nullable=True)
    informed_copies = Column(Text, nullable=True)

    processing_status = Column(String(64), nullable=False, default="STAGED")
    review_status = Column(String(64), nullable=False, default="PENDING")

    sha256 = Column(String(64), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    evidence_items = relationship("PetitionEvidenceItemModel", back_populates="petition", passive_deletes=False)
    requested_actions = relationship("PetitionRequestedActionModel", back_populates="petition", passive_deletes=False)
    attachments = relationship("PetitionAttachmentModel", back_populates="petition", passive_deletes=False)
    field_reviews = relationship("PetitionFieldReviewModel", back_populates="petition", passive_deletes=False)


class PetitionEvidenceItemModel(Base):
    __tablename__ = "petition_evidence_items"
    __table_args__ = (
        CheckConstraint("quantity IS NULL OR quantity > 0", name="check_petition_evidence_quantity"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    petition_id = Column(UUID(as_uuid=True), ForeignKey("forensic.petitions.id", ondelete="RESTRICT"), nullable=False)
    nue_number = Column(String(64), nullable=True)
    quantity = Column(Integer, nullable=True)
    description_original = Column(Text, nullable=True)
    evidence_type_declared = Column(String(128), nullable=True)
    brand_declared = Column(String(128), nullable=True)
    model_declared = Column(String(128), nullable=True)
    serial_number_declared = Column(String(128), nullable=True)
    capacity_declared = Column(String(128), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    petition = relationship("PetitionModel", back_populates="evidence_items")


class PetitionRequestedActionModel(Base):
    __tablename__ = "petition_requested_actions"
    __table_args__ = (
        CheckConstraint("action_order >= 1", name="check_petition_action_order"),
        {"schema": "forensic"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    petition_id = Column(UUID(as_uuid=True), ForeignKey("forensic.petitions.id", ondelete="RESTRICT"), nullable=False)
    action_order = Column(Integer, nullable=False)
    source_text = Column(Text, nullable=False)
    normalized_action = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    petition = relationship("PetitionModel", back_populates="requested_actions")


class PetitionAttachmentModel(Base):
    __tablename__ = "petition_attachments"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    petition_id = Column(UUID(as_uuid=True), ForeignKey("forensic.petitions.id", ondelete="RESTRICT"), nullable=False)
    attachment_type = Column(String(64), nullable=False, default="ACTA")
    description = Column(Text, nullable=True)
    reference_number = Column(String(128), nullable=True)
    source_page = Column(Integer, nullable=True)
    physically_received = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    petition = relationship("PetitionModel", back_populates="attachments")


class PetitionFieldReviewModel(Base):
    __tablename__ = "petition_field_reviews"
    __table_args__ = {"schema": "forensic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    petition_id = Column(UUID(as_uuid=True), ForeignKey("forensic.petitions.id", ondelete="RESTRICT"), nullable=False)
    field_name = Column(String(128), nullable=False)
    observed_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=True)
    confirmed_value = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_excerpt = Column(Text, nullable=True)
    extraction_method = Column(String(64), nullable=True)
    status = Column(String(64), nullable=False, default="EXTRACTED")
    review_action = Column(String(64), nullable=True)
    reviewed_by = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    petition = relationship("PetitionModel", back_populates="field_reviews")



