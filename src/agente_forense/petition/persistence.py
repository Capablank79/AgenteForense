"""
Persistence and artifact storage integration for Petition Pipeline (Sprint R05.1).
Connects Petition service results with FileStore, PostgreSQL (files/documents/hashes/audit), and JSON artifacts.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from agente_forense.petition.models import PetitionDocument, PetitionExtraction
from agente_forense.persistence.repositories import (
    FileRepository, AuditRepository, ToolVersionRepository, PetitionRepository
)
from agente_forense.persistence.models import DocumentModel, HashModel, PetitionModel
from agente_forense.storage.filestore import FileStore

class PetitionPersistenceService:
    def __init__(self, session: Session, filestore: FileStore):
        self.session = session
        self.filestore = filestore
        self.file_repo = FileRepository(session)
        self.audit_repo = AuditRepository(session)
        self.tool_version_repo = ToolVersionRepository(session)
        self.petition_repo = PetitionRepository(session)

    def persist_petition_entity(
        self,
        doc: PetitionDocument,
        extraction: PetitionExtraction,
        case_id: Optional[UUID] = None,
        actor: str = "OPERATOR"
    ) -> PetitionModel:
        """
        Persiste el Oficio Petitorio como entidad propia e independiente en PostgreSQL.
        Transaccional: Guarda tabla principal, evidencia declarada, acciones solicitadas, actas y revisiones de campos.
        """
        # 1. Obtener o crear FileModel
        file_record = self.file_repo.get_by_sha256(doc.sha256)
        if not file_record:
            # Si no hay case_id asignado aún, se puede usar un UUID nulo o asociar si viene
            # En schema forensic, file_id no requiere case_id si es independiente
            file_record = self.file_repo.create(
                case_id=case_id,
                file_role="PETITION",
                original_filename=doc.original_filename,
                stored_filename=Path(doc.stored_relative_path).name,
                relative_path=doc.stored_relative_path,
                mime_type=doc.mime_observed,
                size_bytes=doc.size_bytes,
                sha256=doc.sha256,
                source="USER_UPLOAD",
                integrity_status="VERIFIED"
            )

        # Verificar si ya existe registro en petitions
        existing_petition = self.petition_repo.get_by_file_id(file_record.id)
        if existing_petition:
            petition_model = existing_petition
            petition_model.processing_status = doc.processing_status.value
            petition_model.review_status = extraction.review_status
        else:
            # Extraer campos clave de extraction.fields para poblar la tabla principal
            fields_dict = {f.field_name: f.value for f in extraction.fields}
            
            petition_model = self.petition_repo.create_petition(
                file_id=file_record.id,
                sha256=doc.sha256,
                document_type="PETITION",
                petition_number=fields_dict.get("petition_number"),
                petition_date=fields_dict.get("petition_date"),
                city=fields_dict.get("city"),
                log_reference=fields_dict.get("log_reference"),
                ruc=fields_dict.get("ruc"),
                crime_context=fields_dict.get("crime_context"),
                other_references=fields_dict.get("other_references"),
                requesting_unit=fields_dict.get("requesting_unit"),
                prosecutor_office=fields_dict.get("prosecutor_office"),
                prosecutor_name=fields_dict.get("prosecutor_name"),
                investigator_name=fields_dict.get("investigator_name"),
                investigator_rank=fields_dict.get("investigator_rank"),
                contact_details=fields_dict.get("contact_details"),
                addressee=fields_dict.get("addressee"),
                informed_copies=fields_dict.get("informed_copies"),
                processing_status=doc.processing_status.value,
                review_status=extraction.review_status
            )

        # 2. Persistir Field Reviews (Garantizar idempotencia y preservar revisiones humanas previas)
        for f in extraction.fields:
            src_page = f.provenance[0].page_index + 1 if f.provenance else None
            src_excerpt = f.provenance[0].source_text if f.provenance else None
            ext_method = f.provenance[0].extraction_method if f.provenance else None
            
            # Buscar revisión previa existente para el campo
            existing_reviews = self.petition_repo.get_field_reviews(petition_model.id)
            existing_rev = next((r for r in existing_reviews if r.field_name == f.field_name), None)
            
            if existing_rev:
                # Si el campo ya fue revisado por un humano o f tiene estado confirmado/corregido/no_encontrado/no_aplica
                if f.status.value in ["CONFIRMED", "CORRECTED_BY_HUMAN", "NOT_FOUND", "NOT_APPLICABLE"]:
                    confirmed_val = f.value
                    status_val = f.status.value
                    obs_val = existing_rev.observed_value if existing_rev.observed_value is not None else f.value
                elif existing_rev.status in ["CONFIRMED", "CORRECTED_BY_HUMAN", "NOT_FOUND", "NOT_APPLICABLE"] or existing_rev.confirmed_value is not None:
                    confirmed_val = existing_rev.confirmed_value
                    status_val = existing_rev.status
                    obs_val = existing_rev.observed_value
                else:
                    confirmed_val = f.value if f.status.value in ["CONFIRMED", "CORRECTED_BY_HUMAN"] else None
                    status_val = f.status.value
                    obs_val = f.value
            else:
                confirmed_val = f.value if f.status.value in ["CONFIRMED", "CORRECTED_BY_HUMAN"] else None
                status_val = f.status.value
                obs_val = f.value
            
            self.petition_repo.add_field_review(
                petition_id=petition_model.id,
                field_name=f.field_name,
                observed_value=obs_val,
                proposed_value=f.normalized_value,
                confirmed_value=confirmed_val,
                source_page=src_page,
                source_excerpt=src_excerpt,
                extraction_method=ext_method,
                status=status_val,
                reviewed_by=actor
            )

        # 3. Persistir Evidence Items declaradas (evitando duplicados en re-extracción)
        existing_evidences = self.petition_repo.get_evidence_items(petition_model.id)
        if extraction.evidence_items:
            for ev in extraction.evidence_items:
                already_exists = any(
                    (e.nue_number == ev.nue_number and e.description_original == ev.description_original)
                    for e in existing_evidences
                )
                if not already_exists:
                    self.petition_repo.add_evidence_item(
                        petition_id=petition_model.id,
                        nue_number=ev.nue_number,
                        quantity=ev.quantity or 1,
                        description_original=ev.description_original,
                        brand_declared=ev.brand_declared,
                        model_declared=ev.model_declared,
                        serial_number_declared=ev.serial_number_declared
                    )
        else:
            nue_val = next((f.value for f in extraction.fields if f.field_name == "nue"), None)
            desc_val = next((f.value for f in extraction.fields if f.field_name == "evidence_description"), None)
            brand_val = next((f.value for f in extraction.fields if f.field_name == "brand"), None)
            model_val = next((f.value for f in extraction.fields if f.field_name == "model"), None)
            serial_val = next((f.value for f in extraction.fields if f.field_name == "serial_number"), None)
            
            if desc_val or nue_val or serial_val:
                already_exists = any(
                    (e.nue_number == nue_val and e.description_original == desc_val)
                    for e in existing_evidences
                )
                if not already_exists:
                    self.petition_repo.add_evidence_item(
                        petition_id=petition_model.id,
                        nue_number=nue_val,
                        quantity=1,
                        description_original=desc_val,
                        brand_declared=brand_val,
                        model_declared=model_val,
                        serial_number_declared=serial_val
                    )

        # 4. Persistir Requested Actions (diligencias solicitadas)
        existing_actions = self.petition_repo.get_requested_actions(petition_model.id)
        for act in extraction.requested_actions:
            already_exists = any(a.source_text == act.source_text for a in existing_actions)
            if not already_exists:
                self.petition_repo.add_requested_action(
                    petition_id=petition_model.id,
                    source_text=act.source_text,
                    normalized_action=act.normalized_action,
                    action_order=act.action_order,
                    source_page=act.source_page
                )

        # 5. Persistir Attachments (actas y anexos)
        existing_atts = self.petition_repo.get_attachments(petition_model.id)
        for att in extraction.attachments:
            already_exists = any(a.description == att.description for a in existing_atts)
            if not already_exists:
                self.petition_repo.add_attachment(
                    petition_id=petition_model.id,
                    attachment_type=att.attachment_type,
                    description=att.description,
                    reference_number=att.reference_number,
                    source_page=att.source_page,
                    physically_received=att.physically_received
                )

        # 4. Registrar evento de auditoría
        self.audit_repo.append(
            actor=actor,
            module="PETITION",
            tool="PetitionPersistenceService",
            tool_version="1.0.0",
            event_type="PETITION_PERSISTED",
            action="PERSIST_PETITION",
            result="SUCCESS",
            source=doc.stored_relative_path,
            details={
                "petition_id": str(petition_model.id),
                "file_id": str(file_record.id),
                "sha256": doc.sha256,
                "review_status": extraction.review_status
            }
        )

        return petition_model

    def persist_petition_processing(
        self,
        case_id: UUID,
        doc: PetitionDocument,
        extraction: PetitionExtraction,
        actor: str = "SYSTEM",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Persists petition file metadata, document OCR record, hashes, derived JSON artifacts, and audit events.
        """
        # 1. File Record (Deduplicated by SHA-256)
        file_record = self.file_repo.get_by_sha256(doc.sha256)
        if not file_record:
            file_record = self.file_repo.create(
                case_id=case_id,
                file_role="PETITION",
                original_filename=doc.original_filename,
                stored_filename=Path(doc.stored_relative_path).name,
                relative_path=doc.stored_relative_path,
                mime_type=doc.mime_observed,
                size_bytes=doc.size_bytes,
                sha256=doc.sha256,
                source="USER_UPLOAD",
                integrity_status="VERIFIED"
            )

        # 2. Document Record
        full_raw_text = "\n\n".join(f"--- PAGE {p.page_index + 1} ---\n{p.raw_text}" for p in extraction.pages)
        doc_record = DocumentModel(
            file_id=file_record.id,
            document_type="PETITION",
            ocr_status=doc.processing_status.value,
            ocr_text=full_raw_text
        )
        self.session.add(doc_record)
        self.session.flush()

        # 3. Hash Record
        hash_record = HashModel(
            file_id=file_record.id,
            case_id=case_id,
            algorithm="SHA-256",
            hash_value=doc.sha256,
            source="PETITION_PIPELINE",
            verification_status="VERIFIED"
        )
        self.session.add(hash_record)
        self.session.flush()

        # 4. Save derived JSON artifacts in FileStore
        extraction_filename = f"petition_{doc.document_id}_extraction.json"
        ocr_metadata_filename = f"petition_{doc.document_id}_ocr_metadata.json"

        extraction_bytes = json.dumps(extraction.model_dump(), indent=2, ensure_ascii=False).encode("utf-8")
        ocr_metadata_bytes = json.dumps({
            "document_id": doc.document_id,
            "processing_method": extraction.processing_method,
            "tool_versions": extraction.tool_versions,
            "pages_meta": [
                {
                    "page_index": p.page_index,
                    "render_width": p.render_width,
                    "render_height": p.render_height,
                    "ocr_language": p.ocr_language,
                    "raw_length": len(p.raw_text),
                    "normalized_length": len(p.normalized_text)
                } for p in extraction.pages
            ]
        }, indent=2, ensure_ascii=False).encode("utf-8")

        temp_dir = self.filestore.root_dir / "temp_artifacts"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        ext_tmp = temp_dir / extraction_filename
        ocr_tmp = temp_dir / ocr_metadata_filename
        ext_tmp.write_bytes(extraction_bytes)
        ocr_tmp.write_bytes(ocr_metadata_bytes)

        try:
            ext_meta = self.filestore.store_file(
                source_path=ext_tmp,
                target_relative_dir="derived_artifacts",
                target_filename=extraction_filename,
                overwrite=True
            )
            ocr_meta = self.filestore.store_file(
                source_path=ocr_tmp,
                target_relative_dir="derived_artifacts",
                target_filename=ocr_metadata_filename,
                overwrite=True
            )
        finally:
            if ext_tmp.exists():
                ext_tmp.unlink()
            if ocr_tmp.exists():
                ocr_tmp.unlink()

        ext_rel_path = ext_meta["relative_path"]
        ocr_rel_path = ocr_meta["relative_path"]

        # 5. Tool versions audit
        for t_name, t_ver in extraction.tool_versions.items():
            self.tool_version_repo.register_tool(
                tool_name=t_name,
                tool_version=str(t_ver)
            )

        # 6. Audit Event
        self.audit_repo.append(
            actor=actor,
            module="PETITION",
            tool="PetitionPersistenceService",
            tool_version="1.0.0",
            event_type="PETITION_PROCESSED",
            action="PROCESS_PETITION",
            result="SUCCESS",
            case_id=case_id,
            source=doc.stored_relative_path,
            destination=ext_rel_path,
            details={
                "document_id": doc.document_id,
                "sha256": doc.sha256,
                "processing_method": extraction.processing_method,
                "fields_count": len(extraction.fields),
                "conflicts_count": len(extraction.conflicts),
                "request_id": request_id
            }
        )

        self.session.commit()
        return {
            "file_id": str(file_record.id),
            "document_id": str(doc_record.id),
            "document_record_id": str(doc_record.id),
            "extraction_artifact_path": ext_rel_path,
            "ocr_metadata_artifact_path": ocr_rel_path
        }
