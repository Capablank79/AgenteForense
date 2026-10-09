"""
Servicio principal del Agente de Identificación Fotográfica Asistida.
Coordina staging, OCR, clasificación, extracción, anti-invención, Qwen opcional,
revisión humana, renombrado e integración con PostgreSQL y case.json.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from agente_forense.identification.models import (
    IdentificationData, PhotoIngestRecord, AttributeValue, AttributeStatus,
    AttributeProvenance, ConflictRecord, PhotoClassification
)
from agente_forense.identification.photo_ingest import ingest_photo, verify_photo_integrity
from agente_forense.identification.photo_ocr import run_photo_ocr
from agente_forense.identification.text_classifier import classify_photo_textually
from agente_forense.identification.attribute_extractor import extract_deterministic_attributes
from agente_forense.identification.qwen_text import query_qwen_text_analysis
from agente_forense.identification.anti_invention import validate_anti_invention
from agente_forense.identification.conflicts import detect_conflicts
from agente_forense.identification.review import apply_human_review
from agente_forense.identification.renaming import preview_renaming, execute_safe_renaming
from agente_forense.identification.identification_json import write_identification_json_atomic
from agente_forense.persistence.repositories import (
    SpeciesRepository, DsmRepository, FileRepository, AuditRepository, CaseRepository
)
from agente_forense.storage.case_json import CaseJsonService

class IdentificationService:
    """
    Servicio orquestador del módulo de identificación fotográfica.
    """

    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self.species_repo = SpeciesRepository(session) if session else None
        self.dsm_repo = DsmRepository(session) if session else None
        self.file_repo = FileRepository(session) if session else None
        self.audit_repo = AuditRepository(session) if session else None
        self.case_repo = CaseRepository(session) if session else None

    def analyze_photo(
        self,
        photo_record: PhotoIngestRecord,
        photo_file_path: Path,
        use_qwen: bool = True
    ) -> Tuple[PhotoIngestRecord, Dict[str, AttributeValue]]:
        """
        Ejecuta el pipeline de análisis sobre una fotografía:
        1. OCR Windows
        2. Clasificación textual automática
        3. Extracción determinista (regex)
        4. Extracción opcional con Qwen + Anti-invención
        """
        # 1. OCR
        ocr_res = run_photo_ocr(photo_file_path, language_tag="es-ES")
        photo_record.ocr_text = ocr_res.get("raw_text", "")
        photo_record.analysis_status = ocr_res.get("status", "PROCESSED")

        # 2. Clasificación textual
        photo_record.classification = classify_photo_textually(photo_record.ocr_text)

        # 3. Extracción determinista
        extracted = extract_deterministic_attributes(photo_record.ocr_text, photo_record.photo_id)

        # 4. Qwen opcional
        if use_qwen and photo_record.ocr_text:
            qwen_res = query_qwen_text_analysis(photo_record.ocr_text, timeout_seconds=2.0)
            if qwen_res:
                for key, val in qwen_res.items():
                    if key in ["brand", "model", "serial", "capacity", "part_number"] and val:
                        val_str = str(val).strip()
                        # Validar anti-invención
                        if validate_anti_invention(key, val_str, photo_record.ocr_text):
                            if key not in extracted or extracted[key].status == AttributeStatus.NOT_FOUND.value:
                                extracted[key] = AttributeValue(
                                    field_name=key,
                                    value=val_str,
                                    normalized_value=val_str,
                                    status=AttributeStatus.EXTRACTED.value,
                                    provenance=AttributeProvenance(
                                        field_name=key,
                                        value=val_str,
                                        source_photo_id=photo_record.photo_id,
                                        source_text=val_str,
                                        method="QWEN2.5_TEXT",
                                        status=AttributeStatus.EXTRACTED.value
                                    )
                                )
                        else:
                            # Atributo rechazado por invención
                            extracted[key + "_rejected"] = AttributeValue(
                                field_name=key,
                                value=val_str,
                                status=AttributeStatus.REJECTED_UNSUPPORTED.value,
                                provenance=AttributeProvenance(
                                    field_name=key,
                                    value=val_str,
                                    source_photo_id=photo_record.photo_id,
                                    source_text=val_str,
                                    method="QWEN2.5_TEXT",
                                    status=AttributeStatus.REJECTED_UNSUPPORTED.value
                                )
                            )

        return photo_record, extracted

    def build_identification_data(
        self,
        entity_type: str,
        entity_id: str,
        photos: List[PhotoIngestRecord],
        attributes_map: Dict[str, AttributeValue]
    ) -> IdentificationData:
        """Construye la estructura consolidada IdentificationData."""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Evaluar conflictos
        conflicts = detect_conflicts(photos, attributes_map)

        status = "IDENTIFICATION_PENDING"
        if len(photos) == 0:
            status = "PENDING"
        elif 1 <= len(photos) <= 2:
            status = "INCOMPLETE"
        elif len(photos) == 3:
            status = "READY"
        else:
            status = "REVIEW_REQUIRED"

        return IdentificationData(
            schema_version=1,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            photos=photos,
            attributes=attributes_map,
            conflicts=conflicts,
            timestamps={"created_at": now_iso, "updated_at": now_iso}
        )
