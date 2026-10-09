"""
Service facade for Petition processing pipeline (Sprint R05.1).
Coordinates staging, hashing, detection, extraction, OCR, conflicts, review, and draft generation.
"""
import sys
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import pypdf
import PIL

from agente_forense.petition.models import (
    PetitionDocument, PetitionPageText, ExtractedField, PetitionExtraction,
    ProcessingStatus, FieldStatus, FieldReviewAction
)
from agente_forense.petition.errors import (
    UnsupportedPetitionFormatError, PetitionIntegrityError, PetitionNotReadyForDraftError
)
from agente_forense.petition.detector import detect_petition_type
from agente_forense.petition.text_extractors import extract_text_from_pdf
from agente_forense.petition.pdf_renderer import PdfRendererOcr
from agente_forense.petition.ocr import WindowsOcrProvider
from agente_forense.petition.normalization import normalize_petition_text
from agente_forense.petition.field_extractors import FieldExtractor
from agente_forense.petition.conflicts import ConflictDetector
from agente_forense.petition.draft_mapper import DraftMapper, CaseStructureDraft
from agente_forense.storage.hashing import calculate_sha256

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB default

def get_tool_versions(ocr_language: str = "es-ES") -> Dict[str, Any]:
    return {
        "python": sys.version,
        "pypdf": getattr(pypdf, "__version__", "6.19.0"),
        "winsdk": "1.0.0b10",
        "pillow": getattr(PIL, "__version__", "12.3.0"),
        "windows_build": platform.version(),
        "ocr_language": ocr_language,
        "application_version": "1.0.0"
    }

class PetitionService:
    def __init__(
        self,
        ocr_provider: Optional[WindowsOcrProvider] = None,
        field_extractor: Optional[FieldExtractor] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        draft_mapper: Optional[DraftMapper] = None
    ):
        self.ocr_provider = ocr_provider or WindowsOcrProvider()
        self.pdf_renderer = PdfRendererOcr(ocr_provider=self.ocr_provider)
        self.field_extractor = field_extractor or FieldExtractor()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.draft_mapper = draft_mapper or DraftMapper()

    def process_petition_file(
        self,
        document_id: str,
        file_path: Path,
        original_filename: str,
        stored_relative_path: str
    ) -> Tuple[PetitionDocument, PetitionExtraction]:
        """
        Executes full local petition pipeline on staged file.
        Verifies SHA-256 before and after processing to guarantee original file immutability.
        """
        # 1. SHA-256 before
        sha_before = calculate_sha256(file_path)
        size_bytes = file_path.stat().st_size

        # 2. Detect type
        ext, is_text_pdf, page_count = detect_petition_type(file_path)

        doc = PetitionDocument(
            document_id=document_id,
            original_filename=original_filename,
            stored_relative_path=stored_relative_path,
            size_bytes=size_bytes,
            sha256=sha_before,
            extension=ext,
            mime_observed="application/pdf" if ext == ".pdf" else f"image/{ext.replace('.', '')}",
            page_count=page_count,
            processing_status=ProcessingStatus.HASHED
        )

        pages: List[PetitionPageText] = []
        processing_method = ""

        # 3. Extraction / OCR
        if ext == ".pdf":
            if is_text_pdf:
                doc.processing_status = ProcessingStatus.TEXT_EXTRACTION_PENDING
                processing_method = "PYPDF_TEXT"
                extracted_pages = extract_text_from_pdf(file_path)
                doc.processing_status = ProcessingStatus.TEXT_EXTRACTED
                for idx, raw_txt in extracted_pages:
                    norm_txt = normalize_petition_text(raw_txt)
                    pages.append(PetitionPageText(
                        page_index=idx,
                        raw_text=raw_txt,
                        normalized_text=norm_txt,
                        extraction_method=processing_method
                    ))
            else:
                doc.processing_status = ProcessingStatus.OCR_PENDING
                processing_method = "WINDOWS_PDF_RENDER_OCR"
                rendered_pages = self.pdf_renderer.render_and_ocr_pdf(file_path, "es-ES")
                doc.processing_status = ProcessingStatus.OCR_COMPLETED
                for p in rendered_pages:
                    norm_txt = normalize_petition_text(p.raw_text)
                    pages.append(PetitionPageText(
                        page_index=p.page_index,
                        raw_text=p.raw_text,
                        normalized_text=norm_txt,
                        extraction_method=processing_method,
                        render_width=p.width,
                        render_height=p.height,
                        ocr_language="es-ES"
                    ))
        else:
            # JPG / JPEG / PNG
            doc.processing_status = ProcessingStatus.OCR_PENDING
            processing_method = "WINDOWS_IMAGE_OCR"
            raw_txt = self.ocr_provider.recognize_image_file(str(file_path), "es-ES")
            doc.processing_status = ProcessingStatus.OCR_COMPLETED
            norm_txt = normalize_petition_text(raw_txt)
            pages.append(PetitionPageText(
                page_index=0,
                raw_text=raw_txt,
                normalized_text=norm_txt,
                extraction_method=processing_method,
                ocr_language="es-ES"
            ))

        # 4. SHA-256 integrity verification
        sha_after = calculate_sha256(file_path)
        if sha_before != sha_after:
            doc.processing_status = ProcessingStatus.FAILED
            raise PetitionIntegrityError(
                f"Original file modified during processing! SHA_BEFORE={sha_before} != SHA_AFTER={sha_after}"
            )

        # 5. Deterministic Field Extraction
        pages_input = [(p.page_index, p.raw_text, p.extraction_method) for p in pages]
        fields, ev_items, req_actions, atts = self.field_extractor.extract_fields_from_pages(document_id, pages_input)

        # 6. Conflict Detection
        total_ocr_len = sum(len(p.raw_text.strip()) for p in pages)
        conflicts = self.conflict_detector.detect_conflicts(fields, total_ocr_len)

        if conflicts:
            doc.processing_status = ProcessingStatus.REVIEW_REQUIRED
        else:
            doc.processing_status = ProcessingStatus.FIELDS_EXTRACTED

        extraction = PetitionExtraction(
            document_id=document_id,
            document_sha256=sha_before,
            processing_method=processing_method,
            pages=pages,
            fields=fields,
            evidence_items=ev_items,
            requested_actions=req_actions,
            attachments=atts,
            conflicts=conflicts,
            review_status="PENDING" if conflicts else "APPROVED",
            tool_versions=get_tool_versions()
        )

        return doc, extraction

    def apply_human_review(
        self,
        extraction: PetitionExtraction,
        actions: List[FieldReviewAction]
    ) -> PetitionExtraction:
        """
        Applies human review actions (confirm, correct, mark not found) to extraction fields.
        """
        for act in actions:
            target_fields = [f for f in extraction.fields if f.field_name == act.field_name]
            if not target_fields and act.field_name == "nue" and act.action_type in ("CONFIRM", "CORRECT"):
                # Human added a new NUE field
                new_f = ExtractedField(
                    field_name="nue",
                    value=act.new_value,
                    normalized_value=act.new_value,
                    status=FieldStatus.CORRECTED_BY_HUMAN,
                    provenance=[],
                    confidence=None
                )
                extraction.fields.append(new_f)
                continue

            for f in target_fields:
                if act.action_type == "CONFIRM":
                    f.status = FieldStatus.CONFIRMED
                    if act.new_value is not None and act.new_value != "":
                        f.value = act.new_value
                        f.normalized_value = act.new_value
                elif act.action_type == "CORRECT":
                    f.status = FieldStatus.CORRECTED_BY_HUMAN
                    f.value = act.new_value
                    f.normalized_value = act.new_value
                elif act.action_type == "MARK_NOT_FOUND":
                    f.status = FieldStatus.NOT_FOUND
                    f.value = None
                    f.normalized_value = None
                elif act.action_type == "MARK_NOT_APPLICABLE":
                    f.status = FieldStatus.NOT_APPLICABLE
                    f.value = None
                    f.normalized_value = None

        # Clear resolved conflicts
        extraction.conflicts = [
            c for c in extraction.conflicts
            if not any(f.field_name == c.field_name and f.status in (FieldStatus.CONFIRMED, FieldStatus.CORRECTED_BY_HUMAN, FieldStatus.NOT_FOUND, FieldStatus.NOT_APPLICABLE) for f in extraction.fields)
        ]
        extraction.review_status = "REVIEW_COMPLETED"
        return extraction

    def build_case_draft(self, extraction: PetitionExtraction) -> CaseStructureDraft:
        return self.draft_mapper.build_draft_from_extraction(extraction)
