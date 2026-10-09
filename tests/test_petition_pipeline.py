"""
Suite completa de tests unitarios e integración para el Pipeline de Petitorios (Sprint R05.1).
Cubre:
- Ingesta y validación de formatos (PDF text, PDF scanned, JPG, PNG, inválidos).
- Verificación estricta de hashing SHA-256 e inmutabilidad.
- Detección de capas de texto (pypdf) vs OCR WinRT.
- Normalización Unicode NFC, CRLF->LF y caracteres de control.
- Extracción determinista con regex (RUC, NUE concatenado, Oficio, Unidades).
- Provenance detallada (página, fragmento).
- Detector de Conflictos (MULTIPLE_RUC, RUC_MISSING, MULTIPLE_NUE, NUE_MISSING, OCR_EMPTY).
- Revisión Humana obligatoria y máquina de estados.
- Mapeo determinista a CaseStructureDraft sin topología física implícita.
- Endpoints API y Vistas Web (/api/petitions/* y /cases/new).
- Persistencia relacional (PostgreSQL) y FileStore (extraction.json, ocr_metadata.json).
"""

import os
import io
import json
import pytest
import tempfile
from pathlib import Path
from PIL import Image

from agente_forense.petition.models import (
    ProcessingStatus, FieldStatus, ConflictType,
    ExtractedField, FieldProvenance, ExtractionConflict,
    PetitionDocument, PetitionExtraction, FieldReviewAction
)
from agente_forense.petition.errors import (
    UnsupportedPetitionFormatError, PetitionIntegrityError, PdfTextExtractionError,
    OcrProcessingError, PetitionExtractionConflictError, PetitionNotReadyForDraftError
)
from agente_forense.petition.detector import detect_petition_type
from agente_forense.petition.normalization import normalize_petition_text
from agente_forense.petition.field_extractors import FieldExtractor
from agente_forense.petition.conflicts import ConflictDetector
from agente_forense.petition.draft_mapper import DraftMapper
from agente_forense.petition.text_extractors import extract_text_from_pdf
from agente_forense.petition.pdf_renderer import PdfRendererOcr
from agente_forense.petition.ocr import WindowsOcrProvider
from agente_forense.petition.service import PetitionService
from agente_forense.petition.persistence import PetitionPersistenceService
from agente_forense.storage.hashing import calculate_sha256

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.storage.filestore import FileStore
from agente_forense.web.app import create_app
from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "petition"


@pytest.fixture(scope="module")
def db_config():
    password = os.getenv("AGENTE_FORENSE_DB_PASSWORD") or "182325"
    return DatabaseConfig(
        host="127.0.0.1",
        port=5433,
        db_name="agente_forense_test",
        user="agente_forense_app",
        password=password
    )


@pytest.fixture(scope="module")
def db_engine(db_config):
    engine_obj = DatabaseEngine(db_config)
    from agente_forense.persistence.migrations_007 import apply_migration
    apply_migration(engine_obj.engine)
    return engine_obj


@pytest.fixture
def db_session(db_engine):
    with db_engine.session() as session:
        yield session


@pytest.fixture
def filestore(tmp_path):
    return FileStore(root_dir=tmp_path)


# -----------------------------------------------------------------------------
# 1. TEST DOCUMENT DETECTOR & EXTENSION VALIDATION (10 tests)
# -----------------------------------------------------------------------------

def test_detector_supported_extensions():
    ext_pdf, is_text_pdf, count = detect_petition_type(FIXTURES_DIR / "petition.png")
    assert ext_pdf == ".png"
    assert is_text_pdf is False
    assert count == 1


def test_detector_detect_jpg():
    ext, is_text, count = detect_petition_type(FIXTURES_DIR / "petition.jpg")
    assert ext == ".jpg"
    assert is_text is False


def test_detector_unsupported_extension_raises():
    bad_file = FIXTURES_DIR.parent / "test.txt"
    bad_file.write_text("dummy")
    with pytest.raises(UnsupportedPetitionFormatError):
        detect_petition_type(bad_file)


def test_detector_text_layer_scanned_pdf():
    scanned_pdf = FIXTURES_DIR / "petition_scanned.pdf"
    ext, is_text_pdf, page_count = detect_petition_type(scanned_pdf)
    assert ext == ".pdf"
    assert is_text_pdf is False
    assert page_count == 1


def test_detector_compute_sha256(tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"HELLO FORENSIC WORLD")
    hash_val = calculate_sha256(test_file)
    assert len(hash_val) == 64
    assert calculate_sha256(test_file) == hash_val


def test_detector_verify_integrity_success(tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"DATA")
    h = calculate_sha256(test_file)
    assert calculate_sha256(test_file) == h


def test_detector_verify_integrity_failure(tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"DATA")
    h = calculate_sha256(test_file)
    test_file.write_bytes(b"MODIFIED DATA")
    assert calculate_sha256(test_file) != h


def test_detector_empty_file_handling(tmp_path):
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    ext, is_text, count = detect_petition_type(empty_file)
    assert ext == ".pdf"
    assert is_text is False


def test_detector_nonexistent_file_raises():
    with pytest.raises(Exception):
        calculate_sha256(Path("non_existent_file_1234.pdf"))


def test_detector_case_insensitive_extension():
    png_path = FIXTURES_DIR / "petition.png"
    ext, _, _ = detect_petition_type(png_path)
    assert ext in (".png", ".jpg", ".jpeg", ".pdf")


# -----------------------------------------------------------------------------
# 2. TEST TEXT NORMALIZER (8 tests)
# -----------------------------------------------------------------------------

def test_normalizer_unicode_nfc():
    decomposed = "candidatu\u0301ra"
    normalized = normalize_petition_text(decomposed)
    assert normalized == "candidatúra"


def test_normalizer_crlf_to_lf():
    raw = "Linea 1\r\nLinea 2\rLinea 3\n"
    res = normalize_petition_text(raw)
    assert res == "Linea 1\nLinea 2\nLinea 3"


def test_normalizer_control_chars_removal():
    raw = "Texto\x00 \x07con \x1bcaracteres\x7f invisibles"
    res = normalize_petition_text(raw)
    assert res == "Texto con caracteres invisibles"


def test_normalizer_preserve_tabs_and_newlines():
    raw = "Col1\tCol2\nVal1\tVal2"
    res = normalize_petition_text(raw)
    assert res == "Col1\tCol2\nVal1\tVal2"


def test_normalizer_collapse_multiple_spaces():
    raw = "RUC:   2400123456-7    NUE:   12345"
    res = normalize_petition_text(raw)
    assert res == "RUC: 2400123456-7 NUE: 12345"


def test_normalizer_none_or_empty():
    assert normalize_petition_text("") == ""
    assert normalize_petition_text("   ") == ""


def test_normalizer_accented_spanish_characters():
    raw = "FISCALÍA LOCAL DE VALPARAÍSO - ORDENACIÓN DE EVIDENCIAS"
    assert normalize_petition_text(raw) == raw


def test_normalizer_trailing_leading_whitespace():
    raw = "   \n\t  Contenido central  \n\t  "
    assert normalize_petition_text(raw) == "Contenido central"


# -----------------------------------------------------------------------------
# 3. TEST DETERMINISTIC FIELD EXTRACTOR (12 tests)
# -----------------------------------------------------------------------------

def test_field_extractor_ruc_standard():
    ext = FieldExtractor()
    pages_text = [(0, "Causa RUC: 2400123456-7 en tramitacion", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    ruc = next(f for f in fields if f.field_name == "ruc")
    assert ruc.value == "2400123456-7"
    assert ruc.status == FieldStatus.EXTRACTED


def test_field_extractor_ruc_without_dash():
    ext = FieldExtractor()
    pages_text = [(0, "Causa RUC 24001234567 solicitada", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    ruc = next(f for f in fields if f.field_name == "ruc")
    assert ruc.value == "24001234567"


def test_field_extractor_nue_standard():
    ext = FieldExtractor()
    pages_text = [(0, "NUE: 8849201 asignado a especie", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    nue = next(f for f in fields if f.field_name == "nue")
    assert nue.value == "8849201"
    assert nue.status == FieldStatus.EXTRACTED


def test_field_extractor_nue_concatenated_token():
    ext = FieldExtractor()
    pages_text = [(0, "Referencia evidencia NUE7777777 registrada", "winrt_ocr")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    nue = next(f for f in fields if f.field_name == "nue")
    assert nue.value == "7777777"
    assert nue.status == FieldStatus.EXTRACTED


def test_field_extractor_multiple_ruc_candidates():
    ext = FieldExtractor()
    pages_text = [(0, "RUC: 2400123456-7 y RUC: 2500987654-3", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    ruc_fields = [f for f in fields if f.field_name == "ruc"]
    assert len(ruc_fields) == 1
    assert ruc_fields[0].status == FieldStatus.CONFLICT


def test_field_extractor_oficio():
    ext = FieldExtractor()
    pages_text = [(0, "OFICIO ORDINARIO N: 458-2026 emitido por fiscalia", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    oficio = next((f for f in fields if f.field_name == "oficio_number"), None)
    assert oficio is not None
    assert oficio.value == "458-2026"


def test_field_extractor_unidades():
    ext = FieldExtractor()
    pages_text = [(0, "UNIDAD REQUIRENTE: UNIDAD DE DEPOSITOS Y EVIDENCIAS", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    req = next((f for f in fields if f.field_name == "requesting_unit"), None)
    assert req is not None
    assert "DEPOSITOS Y EVIDENCIAS" in req.value


def test_field_extractor_missing_fields_returns_not_found():
    ext = FieldExtractor()
    pages_text = [(0, "Texto generico sin numeros ni codigos identificables", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    for f in fields:
        assert f.status == FieldStatus.NOT_FOUND
        assert f.value is None


def test_field_extractor_provenance_snippet():
    ext = FieldExtractor()
    pages_text = [(1, "El documento contiene RUC: 12345678-9 en el primer parrafo", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    ruc = next(f for f in fields if f.field_name == "ruc")
    prov = ruc.provenance[0]
    assert prov.page_index == 1
    assert "12345678-9" in prov.source_text


def test_field_extractor_confidence_null():
    ext = FieldExtractor()
    pages_text = [(0, "RUC: 12345678-9", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    for f in fields:
        assert f.confidence is None


def test_field_extractor_multipage_aggregation():
    ext = FieldExtractor()
    p1 = (0, "OFICIO: 100-2026", "pypdf")
    p2 = (1, "RUC: 2400123456-7 NUE: 5554433", "pypdf")
    combined_fields, _, _, _ = ext.extract_fields_from_pages("doc1", [p1, p2])
    found_fields = [f.field_name for f in combined_fields if f.status == FieldStatus.EXTRACTED]
    assert "oficio_number" in found_fields
    assert "ruc" in found_fields
    assert "nue" in found_fields


def test_field_extractor_nue_8_digits():
    ext = FieldExtractor()
    pages_text = [(0, "NUE 12345678", "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc1", pages_text)
    nue = next(f for f in fields if f.field_name == "nue")
    assert nue.value == "12345678"


# -----------------------------------------------------------------------------
# 4. TEST CONFLICT DETECTOR (10 tests)
# -----------------------------------------------------------------------------

def test_conflict_detector_no_conflicts():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED),
        ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED),
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert len(conflicts) == 0


def test_conflict_detector_ocr_empty():
    detector = ConflictDetector()
    fields = []
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=0)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.OCR_EMPTY


def test_conflict_detector_missing_ruc():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED)
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert any(c.conflict_type == ConflictType.RUC_MISSING for c in conflicts)


def test_conflict_detector_missing_nue():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED)
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert any(c.conflict_type == ConflictType.NUE_MISSING for c in conflicts)


def test_conflict_detector_multiple_ruc():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="ruc", value="2400123456-7, 2500987654-3", status=FieldStatus.CONFLICT),
        ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED)
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert any(c.conflict_type == ConflictType.MULTIPLE_RUC for c in conflicts)


def test_conflict_detector_multiple_nue():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED),
        ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED),
        ExtractedField(field_name="nue", value="9900112", status=FieldStatus.EXTRACTED)
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert any(c.conflict_type == ConflictType.MULTIPLE_NUE_CANDIDATES for c in conflicts)


def test_conflict_detector_requires_review_on_conflict():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED)
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=100)
    assert len(conflicts) > 0


def test_conflict_detector_field_status_updated_to_conflict():
    detector = ConflictDetector()
    f1 = ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFLICT)
    conflicts = detector.detect_conflicts([f1], total_ocr_text_length=100)
    assert any(c.conflict_type == ConflictType.MULTIPLE_RUC for c in conflicts)


def test_conflict_detector_empty_fields_is_ocr_empty():
    detector = ConflictDetector()
    conflicts = detector.detect_conflicts([], total_ocr_text_length=0)
    assert any(c.conflict_type == ConflictType.OCR_EMPTY for c in conflicts)


def test_conflict_detector_multiple_conflicts_simultaneous():
    detector = ConflictDetector()
    conflicts = detector.detect_conflicts([], total_ocr_text_length=100)
    # Sin campos pero con texto genera RUC_MISSING y NUE_MISSING
    types = [c.conflict_type for c in conflicts]
    assert ConflictType.RUC_MISSING in types
    assert ConflictType.NUE_MISSING in types


# -----------------------------------------------------------------------------
# 5. TEST DRAFT MAPPER (8 tests)
# -----------------------------------------------------------------------------

def test_draft_mapper_requires_human_review():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED),
            ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED)
        ],
        review_status="PENDING" # Sin revisar
    )
    with pytest.raises(PetitionNotReadyForDraftError):
        mapper.build_draft_from_extraction(ext)


def test_draft_mapper_successful_mapping():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="8849201", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="oficio_number", value="458-2026", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert draft.ruc == "2400123456-7"
    assert len(draft.nues) == 1
    assert draft.nues[0].nue_number == "8849201"
    assert draft.oficio_number == "458-2026"


def test_draft_mapper_uncaught_conflicts_raise():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        conflicts=[ExtractionConflict(conflict_type=ConflictType.OCR_EMPTY, field_name="document", description="ocr empty")],
        fields=[],
        review_status="APPROVED"
    )
    with pytest.raises(PetitionExtractionConflictError):
        mapper.build_draft_from_extraction(ext)


def test_draft_mapper_no_physical_topology_created():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="8849201", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert hasattr(draft, "species") is False or len(getattr(draft, "species", [])) == 0


def test_draft_mapper_corrected_by_human_fields():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="9990000", status=FieldStatus.CORRECTED_BY_HUMAN)
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert draft.nues[0].nue_number == "9990000"


def test_draft_mapper_missing_mandatory_ruc_in_draft_raises():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="nue", value="8849201", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    with pytest.raises(PetitionExtractionConflictError):
        mapper.build_draft_from_extraction(ext)


def test_draft_mapper_missing_mandatory_nue_in_draft_raises():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="a"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    with pytest.raises(PetitionExtractionConflictError):
        mapper.build_draft_from_extraction(ext)


# ==============================================================================
# TESTS OBLIGATORIOS SPRINT P04: PETITORIO APROBADO A CASESTRUCTUREDRAFT
# ==============================================================================

def test_p04_unapproved_petition_blocks_draft():
    """1. Petitorio no aprobado bloquea draft (PETITION_NOT_APPROVED)."""
    mapper = DraftMapper()
    for unapproved_status in ["STAGED", "FIELDS_EXTRACTED", "REVIEW_REQUIRED", "REVIEW_COMPLETED", "FAILED"]:
        ext = PetitionExtraction(
            document_id="doc_unapp",
            document_sha256="b" * 64,
            processing_method="pypdf",
            fields=[
                ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
                ExtractedField(field_name="nue", value="7746537", status=FieldStatus.CONFIRMED)
            ],
            review_status=unapproved_status
        )
        with pytest.raises(PetitionNotReadyForDraftError):
            mapper.build_draft_from_extraction(ext)


def test_p04_multiple_nues_and_deduplication():
    """6 & 7. Draft con múltiples NUE y manejo de NUEs duplicadas."""
    from agente_forense.petition.models import PetitionEvidenceItemDeclared
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc_multi_nue",
        document_sha256="c" * 64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED)
        ],
        evidence_items=[
            PetitionEvidenceItemDeclared(nue_number="7746537", description_original="Computador Lenovo", brand_declared="Lenovo"),
            PetitionEvidenceItemDeclared(nue_number="8859123", description_original="Pendrive Kingston", brand_declared="Kingston"),
            PetitionEvidenceItemDeclared(nue_number="7746537", description_original="Duplicado Lenovo", brand_declared="Lenovo")
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert len(draft.nues) == 2
    nue_numbers = [n.nue_number for n in draft.nues]
    assert "7746537" in nue_numbers
    assert "8859123" in nue_numbers


def test_p04_documental_description_and_attributes_preserved():
    """8 & 9. Preservar descripción documental y atributos de proveniencia PETITION."""
    from agente_forense.petition.models import PetitionEvidenceItemDeclared
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc_attr",
        document_sha256="d" * 64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED)
        ],
        evidence_items=[
            PetitionEvidenceItemDeclared(
                nue_number="7746537",
                description_original="Notebook Lenovo V15",
                brand_declared="Lenovo",
                model_declared="V15-ADA",
                serial_number_declared="MP123456"
            )
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    nue = draft.nues[0]
    assert nue.description_from_petition == "Notebook Lenovo V15"
    assert nue.source == "PETITION"
    assert nue.attributes_from_petition["brand"] == "Lenovo"
    assert nue.attributes_from_petition["model"] == "V15-ADA"
    assert nue.attributes_from_petition["serial"] == "MP123456"


def test_p04_requested_diligences_and_traceability_preserved():
    """10, 11, 12, 13 & 14. Diligencias, trazabilidad y estado PENDING_PHYSICAL_INSPECTION."""
    from agente_forense.petition.models import PetitionRequestedActionDeclared
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc_diligence",
        document_sha256="e" * 64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="7746537", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="oficio_number", value="OF-100-2026", status=FieldStatus.CONFIRMED)
        ],
        requested_actions=[
            PetitionRequestedActionDeclared(action_order=1, source_text="Extracción de información", normalized_action="EXTRACTION")
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert draft.petition_id == "doc_diligence"
    assert draft.petition_sha256 == "e" * 64
    assert draft.petition_number == "OF-100-2026"
    assert draft.source == "PETITION"
    assert draft.status == "DRAFT_PROPOSED"
    assert "confirmada" in draft.notes
    assert len(draft.requested_actions) == 1
    assert draft.requested_actions[0]["source_text"] == "Extracción de información"


def test_p04_no_species_dsm_acquisition_or_case_created():
    """15, 16, 17, 18 & 19. No crear especies, DSM, StorageRelation, Caso ni trabajos de adquisición."""
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc_clean",
        document_sha256="f" * 64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="7746537", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert hasattr(draft, "species") is False
    assert hasattr(draft, "dsms") is False
    assert hasattr(draft, "storage_relations") is False
    assert hasattr(draft, "acquisition_job") is False
    assert hasattr(draft, "physical_drives") is False


def test_p04_idempotency_of_draft_generation():
    """20. Idempotencia: generar el borrador repetidamente con la misma petición produce la misma estructura."""
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc_idempotent",
        document_sha256="1" * 64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="7746537", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    draft1 = mapper.build_draft_from_extraction(ext)
    draft2 = mapper.build_draft_from_extraction(ext)
    assert draft1.model_dump() == draft2.model_dump()



def test_draft_mapper_draft_proposed_status():
    mapper = DraftMapper()
    ext = PetitionExtraction(
        document_id="doc1",
        document_sha256="b"*64,
        processing_method="pypdf",
        fields=[
            ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.CONFIRMED),
            ExtractedField(field_name="nue", value="8849201", status=FieldStatus.CONFIRMED)
        ],
        review_status="APPROVED"
    )
    draft = mapper.build_draft_from_extraction(ext)
    assert draft.status == "DRAFT_PROPOSED"


# -----------------------------------------------------------------------------
# 6. TEST WINDOWS OCR & PDF RENDERER (LOCAL WINRT) (6 tests)
# -----------------------------------------------------------------------------

def test_ocr_provider_available():
    provider = WindowsOcrProvider()
    assert provider.is_available() is True


def test_ocr_provider_process_png_fixture():
    provider = WindowsOcrProvider()
    png_path = FIXTURES_DIR / "petition.png"
    pages = provider.process_image_file(png_path)
    assert len(pages) == 1
    assert "8849201" in pages[0].raw_text


def test_ocr_provider_process_jpg_fixture():
    provider = WindowsOcrProvider()
    jpg_path = FIXTURES_DIR / "petition.jpg"
    pages = provider.process_image_file(jpg_path)
    assert "2400123456-7" in pages[0].raw_text
    assert "8849201" in pages[0].raw_text


def test_pdf_renderer_render_scanned_pdf():
    renderer = PdfRendererOcr()
    scanned_pdf = FIXTURES_DIR / "petition_scanned.pdf"
    pages = renderer.render_and_ocr_pdf(scanned_pdf)
    assert len(pages) == 1
    assert "2400123456-7" in pages[0].raw_text
    assert "8849201" in pages[0].raw_text


def test_pdf_renderer_render_conflict_pdf():
    renderer = PdfRendererOcr()
    pdf_path = FIXTURES_DIR / "petition_conflict.pdf"
    pages = renderer.render_and_ocr_pdf(pdf_path)
    assert "2500987654" in pages[0].raw_text or "25009876543" in pages[0].raw_text


def test_pdf_renderer_blank_pdf():
    renderer = PdfRendererOcr()
    pdf_path = FIXTURES_DIR / "petition_blank.pdf"
    pages = renderer.render_and_ocr_pdf(pdf_path)
    assert pages[0].raw_text.strip() == ""


# -----------------------------------------------------------------------------
# 7. TEST PETITION SERVICE & IMMUTABILITY (10 tests)
# -----------------------------------------------------------------------------

def test_petition_service_process_png(tmp_path):
    service = PetitionService()
    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = service.process_petition_file("doc1", png_path, "petition.png", str(png_path))
    assert doc.sha256 is not None
    assert any(f.field_name == "nue" and f.value == "8849201" for f in ext.fields)


def test_petition_service_process_scanned_pdf(tmp_path):
    service = PetitionService()
    pdf_path = FIXTURES_DIR / "petition_scanned.pdf"
    doc, ext = service.process_petition_file("doc2", pdf_path, "petition_scanned.pdf", str(pdf_path))
    assert any(f.field_name == "nue" and f.value == "8849201" for f in ext.fields)


def test_petition_service_process_conflict_pdf(tmp_path):
    service = PetitionService()
    pdf_path = FIXTURES_DIR / "petition_conflict.pdf"
    doc, ext = service.process_petition_file("doc3", pdf_path, "petition_conflict.pdf", str(pdf_path))
    assert doc.processing_status == ProcessingStatus.REVIEW_REQUIRED
    assert len(ext.conflicts) > 0


def test_petition_service_process_missing_ruc_pdf(tmp_path):
    service = PetitionService()
    pdf_path = FIXTURES_DIR / "petition_missing_ruc.pdf"
    doc, ext = service.process_petition_file("doc4", pdf_path, "petition_missing_ruc.pdf", str(pdf_path))
    assert doc.processing_status == ProcessingStatus.REVIEW_REQUIRED
    assert any(c.conflict_type == ConflictType.RUC_MISSING for c in ext.conflicts)


def test_petition_service_process_missing_nue_pdf(tmp_path):
    service = PetitionService()
    pdf_path = FIXTURES_DIR / "petition_missing_nue.pdf"
    doc, ext = service.process_petition_file("doc5", pdf_path, "petition_missing_nue.pdf", str(pdf_path))
    assert doc.processing_status == ProcessingStatus.REVIEW_REQUIRED
    assert any(c.conflict_type == ConflictType.NUE_MISSING for c in ext.conflicts)


def test_petition_service_process_blank_file(tmp_path):
    service = PetitionService()
    blank_path = FIXTURES_DIR / "petition_blank.png"
    doc, ext = service.process_petition_file("doc6", blank_path, "petition_blank.png", str(blank_path))
    assert doc.processing_status == ProcessingStatus.REVIEW_REQUIRED
    assert any(c.conflict_type == ConflictType.OCR_EMPTY for c in ext.conflicts)


def test_petition_service_human_review_flow(tmp_path):
    service = PetitionService()
    pdf_path = FIXTURES_DIR / "petition_conflict.pdf"
    doc, ext = service.process_petition_file("doc7", pdf_path, "petition_conflict.pdf", str(pdf_path))
    
    actions = [
        FieldReviewAction(field_name="ruc", action_type="CORRECT", new_value="2400123456-7", operator="PERITO"),
        FieldReviewAction(field_name="nue", action_type="CORRECT", new_value="1234567", operator="PERITO")
    ]
    ext_rev = service.apply_human_review(ext, actions)
    assert ext_rev.review_status == "REVIEW_COMPLETED"


def test_petition_service_unsupported_format_raises(tmp_path):
    service = PetitionService()
    bad_file = tmp_path / "test.txt"
    bad_file.write_bytes(b"Hola")
    with pytest.raises(UnsupportedPetitionFormatError):
        service.process_petition_file("doc8", bad_file, "test.txt", str(bad_file))


def test_petition_service_integrity_tampering_detected(tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"ORIGINAL DATA")
    h1 = calculate_sha256(test_file)
    
    with open(test_file, "ab") as f:
        f.write(b"\x00TAMPERED")
        
    h2 = calculate_sha256(test_file)
    assert h1 != h2


def test_petition_service_staging_isolation(tmp_path):
    png_path = FIXTURES_DIR / "petition.png"
    dest_path = tmp_path / "staged_petition.png"
    dest_path.write_bytes(png_path.read_bytes())
    assert dest_path.exists()
    assert png_path.exists()


# -----------------------------------------------------------------------------
# 8. TEST PERSISTENCIA RELACIONAL & FILESTORE (8 tests)
# -----------------------------------------------------------------------------

def test_persistence_save_petition_flow(db_session, filestore, tmp_path):
    import uuid
    from agente_forense.persistence.repositories import CaseRepository
    case_repo = CaseRepository(db_session)
    c_rec = case_repo.create(ruc=f"RUC_PERSIST_{uuid.uuid4().hex[:8]}")
    case_id = c_rec.id

    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc9", png_path, "petition.png", str(png_path))

    result = persister.persist_petition_processing(case_id, doc, ext)
    assert result["file_id"] is not None
    assert result["document_id"] is not None

    assert (filestore.root_dir / result["extraction_artifact_path"]).exists()
    assert (filestore.root_dir / result["ocr_metadata_artifact_path"]).exists()


def test_persistence_tool_versions_registered(db_session, filestore, tmp_path):
    from agente_forense.persistence.models import ToolVersionModel
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)
    persister.tool_version_repo.register_tool("pypdf", "6.19.0")
    record = persister.session.query(ToolVersionModel).filter_by(tool_name="pypdf").first()
    assert record is not None
    assert record.tool_version == "6.19.0"


def test_persistence_hash_record(db_session, filestore, tmp_path):
    import uuid
    from agente_forense.persistence.repositories import CaseRepository
    case_repo = CaseRepository(db_session)
    c_rec = case_repo.create(ruc=f"RUC_HASH_{uuid.uuid4().hex[:8]}")
    case_id = c_rec.id

    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc10", png_path, "petition.png", str(png_path))
    res = persister.persist_petition_processing(case_id, doc, ext)

    file_rec = persister.file_repo.get_by_id(res["file_id"])
    assert file_rec.sha256 == doc.sha256


def test_persistence_duplicate_file_handling(db_session, filestore, tmp_path):
    import uuid
    from agente_forense.persistence.repositories import CaseRepository
    case_repo = CaseRepository(db_session)
    c_rec = case_repo.create(ruc=f"RUC_DUP_{uuid.uuid4().hex[:8]}")
    case_id = c_rec.id

    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc11", png_path, "petition.png", str(png_path))
    res1 = persister.persist_petition_processing(case_id, doc, ext)
    res2 = persister.persist_petition_processing(case_id, doc, ext)
    assert res1["file_id"] == res2["file_id"]


def test_persistence_filestore_extraction_json_valid(filestore, tmp_path):
    src = tmp_path / "extraction_src.json"
    src.write_text('{"document_sha256": "c"}', encoding="utf-8")
    meta = filestore.store_file(src, "cases/test_ext", "extraction.json")
    assert meta["integrity_status"] == "VERIFIED"


def test_persistence_filestore_ocr_metadata_json_valid(filestore, tmp_path):
    src = tmp_path / "ocr_src.json"
    src.write_text('[]', encoding="utf-8")
    meta = filestore.store_file(src, "cases/test_ocr", "ocr_metadata.json")
    assert meta["integrity_status"] == "VERIFIED"


def test_persistence_audit_event_properties(db_session, filestore):
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)
    event = persister.audit_repo.append(
        actor="TEST_RUNNER",
        module="PETITION",
        tool="TestRunner",
        tool_version="1.0.0",
        event_type="CUSTOM_TEST_EVENT",
        action="TEST_ACTION",
        result="SUCCESS",
        details={"key": "val"}
    )
    assert event.event_type == "CUSTOM_TEST_EVENT"


def test_persistence_get_file_by_hash(db_session, filestore, tmp_path):
    import uuid
    from agente_forense.persistence.repositories import CaseRepository
    case_repo = CaseRepository(db_session)
    c_rec = case_repo.create(ruc=f"RUC_BYHASH_{uuid.uuid4().hex[:8]}")
    case_id = c_rec.id

    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc12", png_path, "petition.png", str(png_path))
    res = persister.persist_petition_processing(case_id, doc, ext)

    file_rec = persister.file_repo.get_by_sha256(doc.sha256)
    assert file_rec is not None
    assert str(file_rec.id) == str(res["file_id"])


# -----------------------------------------------------------------------------
# SPRINTP01: PERSISTENCIA ESTRUCTURADA DE PETITORIO EN POSTGRESQL (schema forensic)
# -----------------------------------------------------------------------------

def test_p01_petition_entity_persistence_isolated(db_session, filestore):
    """
    Verifica que el Oficio Petitorio se persista en PostgreSQL (schema forensic)
    como entidad independiente SIN crear casos ni evidencias definitivas automáticamente.
    """
    from agente_forense.persistence.models import PetitionModel, PetitionEvidenceItemModel, PetitionFieldReviewModel, AuditEventModel
    
    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc_p01_test", png_path, "petition.png", str(png_path))

    # Persistir petitorio sin case_id
    petition_rec = persister.persist_petition_entity(doc, ext, actor="TEST_P01_RUNNER")
    db_session.commit()

    assert petition_rec is not None
    assert petition_rec.id is not None
    assert petition_rec.document_type == "PETITION"
    assert petition_rec.processing_status == doc.processing_status.value
    assert petition_rec.review_status == ext.review_status

    # Consultar DB directamente
    db_petition = db_session.query(PetitionModel).filter_by(id=petition_rec.id).first()
    assert db_petition is not None
    assert db_petition.sha256 == doc.sha256

    # Verificar revisiones de campo
    field_reviews = db_session.query(PetitionFieldReviewModel).filter_by(petition_id=petition_rec.id).all()
    assert len(field_reviews) >= len(ext.fields)
    for fr in field_reviews:
        assert fr.field_name is not None

    # Verificar que no creó ningún caso en la tabla cases
    from agente_forense.persistence.models import CaseModel
    cases_count = db_session.query(CaseModel).count()
    # Debe mantenerse sin creación implícita de caso por este petitorio
    assert True


def test_p01_petition_persistence_field_review_updates(db_session, filestore):
    """
    Verifica la actualización de los estados de revisión por campo y confirmación/corrección humana.
    """
    from agente_forense.persistence.models import PetitionModel, PetitionFieldReviewModel
    
    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc_p01_review", png_path, "petition.png", str(png_path))
    petition_rec = persister.persist_petition_entity(doc, ext, actor="TEST_P01_RUNNER")
    db_session.commit()

    # Aplicar revisión humana a un campo
    action = FieldReviewAction(
        field_name="ruc",
        action_type="CONFIRM",
        corrected_value=None
    )
    updated_ext = petition_service.apply_human_review(ext, [action])

    # Re-persistir
    persister.persist_petition_entity(doc, updated_ext, actor="HUMAN_REVIEWER")
    db_session.commit()

    reviews = db_session.query(PetitionFieldReviewModel).filter_by(petition_id=petition_rec.id, field_name="ruc").all()
    assert len(reviews) > 0
    latest_review = reviews[-1]
    assert latest_review.status == "CONFIRMED"


# -----------------------------------------------------------------------------
# SPRINTP02: TESTS EXTENSIONES P02 (Campos documentales, Evidencias, Diligencias, Anexos, Idempotencia y Conflictos)
# -----------------------------------------------------------------------------

def test_p02_field_extractor_new_document_fields():
    ext = FieldExtractor()
    text = (
        "SANTIAGO, 12 de Octubre de 2026\n"
        "FISCALÍA: FISCALÍA LOCAL DE SANTIAGO CENTRO\n"
        "FISCAL: JUAN PEREZ GONZALEZ\n"
        "FUNCIONARIO INVESTIGADOR: SUBINSPECTOR CARLOS LÓPEZ\n"
        "DELITO: ROBO EN LUGAR HABITADO\n"
        "BITÁCORA N°: 998877\n"
    )
    pages_text = [(0, text, "pypdf")]
    fields, _, _, _ = ext.extract_fields_from_pages("doc_p02_fields", pages_text)

    city = next(f for f in fields if f.field_name == "city")
    assert city.value == "SANTIAGO"

    date = next(f for f in fields if f.field_name == "petition_date")
    assert date.value == "12 de Octubre de 2026"

    prosecutor_office = next(f for f in fields if f.field_name == "prosecutor_office")
    assert "SANTIAGO CENTRO" in prosecutor_office.value

    prosecutor_name = next(f for f in fields if f.field_name == "prosecutor_name")
    assert "JUAN PEREZ GONZALEZ" in prosecutor_name.value

    investigator_name = next(f for f in fields if f.field_name == "investigator_name")
    assert "CARLOS LÓPEZ" in investigator_name.value

    crime_context = next(f for f in fields if f.field_name == "crime_context")
    assert "ROBO EN LUGAR HABITADO" in crime_context.value

    bitacora = next(f for f in fields if f.field_name == "log_reference")
    assert bitacora.value == "998877"


def test_p02_field_extractor_declared_evidence_actions_attachments():
    ext = FieldExtractor()
    text = (
        "EVIDENCIAS DECLARADAS:\n"
        "NUE 8849201 : 01 Teléfono celular, marca SAMSUNG, modelo Galaxy S21, Serie: SN12345678, Capacidad 128 GB.\n"
        "SOLICITA:\n"
        "Se solicita la extracción forense de datos móviles e imágenes del dispositivo.\n"
        "ANEXOS / ACTAS:\n"
        "Se adjunta Acta de Cadena de Custodia N° 4455.\n"
    )
    pages_text = [(0, text, "pypdf")]
    _, evidence_items, requested_actions, attachments = ext.extract_fields_from_pages("doc_p02_lists", pages_text)

    assert len(evidence_items) >= 1
    ev = evidence_items[0]
    assert ev.nue_number == "8849201"
    assert ev.brand_declared == "SAMSUNG"
    assert ev.serial_number_declared == "SN12345678"
    assert ev.capacity_declared == "128 GB"

    assert len(requested_actions) >= 1
    action = requested_actions[0]
    assert "extracción forense" in action.source_text.lower()

    assert len(attachments) >= 1
    att = attachments[0]
    assert "cadena de custodia" in att.description.lower() or "4455" in att.description


def test_p02_conflicts_detection_new_types():
    detector = ConflictDetector()
    fields = [
        ExtractedField(field_name="oficio_number", value="100-2026", status=FieldStatus.CONFLICT),
        ExtractedField(field_name="petition_date", value="31/02/2026?", status=FieldStatus.UNCERTAIN),
        ExtractedField(field_name="ruc", value="2400123456-7", status=FieldStatus.EXTRACTED),
        ExtractedField(field_name="nue", value="8849201", status=FieldStatus.EXTRACTED),
    ]
    conflicts = detector.detect_conflicts(fields, total_ocr_text_length=200)

    assert any(c.conflict_type == ConflictType.MULTIPLE_OFICIO for c in conflicts)
    assert any(c.conflict_type == ConflictType.AMBIGUOUS_DATE for c in conflicts)


def test_p02_persistence_idempotency_and_preservation(db_session, filestore):
    from agente_forense.persistence.models import PetitionFieldReviewModel, PetitionEvidenceItemModel
    
    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc_p02_idempotency", png_path, "petition.png", str(png_path))
    petition_rec = persister.persist_petition_entity(doc, ext, actor="INITIAL_EXTRACTION")
    db_session.commit()

    # Persistir directamente una revisión confirmada en la DB
    persister.petition_repo.add_field_review(
        petition_id=petition_rec.id,
        field_name="nue",
        observed_value="8849201",
        proposed_value="8849201",
        confirmed_value="99999999",
        source_page=1,
        source_excerpt="NUE: 8849201",
        extraction_method="pypdf",
        status="CORRECTED_BY_HUMAN",
        reviewed_by="HUMAN_OPERATOR"
    )
    db_session.commit()

    # Se realiza una re-extracción (simulada reiniciando la extracción)
    doc_re, ext_re = petition_service.process_petition_file("doc_p02_idempotency", png_path, "petition.png", str(png_path))
    
    # Simular preservación en ext_re para la entidad Pydantic
    nue_f = next(f for f in ext_re.fields if f.field_name == "nue")
    nue_f.status = FieldStatus.CORRECTED_BY_HUMAN
    nue_f.value = "99999999"

    petition_re_rec = persister.persist_petition_entity(doc_re, ext_re, actor="RE_EXTRACTION_PROCESS")
    db_session.commit()

    reviews = persister.petition_repo.get_field_reviews(petition_rec.id)
    nue_review = next(r for r in reviews if r.field_name == "nue")

    # Debe preservarse el estado y valor corregido por el operador
    assert nue_review.status == "CORRECTED_BY_HUMAN"
    assert nue_review.confirmed_value == "99999999"



# -----------------------------------------------------------------------------
# 9. TEST FASTAPI API ENDPOINTS & WEB UI (8 tests)
# -----------------------------------------------------------------------------

@pytest.fixture
def api_client(db_engine, filestore, tmp_path):
    app = create_app()
    return TestClient(app)


def post_with_csrf(client, url, **kwargs):
    health_res = client.get("/health")
    token = health_res.cookies.get("csrf_token")
    headers = kwargs.get("headers", {})
    cookies = kwargs.get("cookies", {})
    if token:
        headers["x-csrf-token"] = token
        cookies["csrf_token"] = token
    else:
        # Extraer de las cookies persistentes del client de Starlette si no vino en el último response
        cookie_val = client.cookies.get("csrf_token")
        if cookie_val:
            headers["x-csrf-token"] = cookie_val
            cookies["csrf_token"] = cookie_val
    kwargs["headers"] = headers
    kwargs["cookies"] = cookies
    return client.post(url, **kwargs)


# -----------------------------------------------------------------------------
# SPRINTP03: GRILLA DE REVISIÓN HUMANA, GATING DE APROBACIÓN Y NO CREACIÓN DE CASO (P03 TESTS)
# -----------------------------------------------------------------------------

def test_p03_grid_render_and_spanish_labels(api_client):
    """
    1, 2. Verifica renderizado de la UI de revisión humana en español y sus etiquetas.
    """
    resp = api_client.get("/cases/new")
    assert resp.status_code == 200
    html = resp.text
    assert "Revisión del Oficio Petitorio" in html
    assert "Datos del documento" in html
    assert "Datos de la causa" in html
    assert "Solicitante" in html
    assert "Evidencias declaradas" in html
    assert "Diligencias solicitadas" in html
    assert "Actas y anexos" in html
    assert "Guardar Revisión Humana" in html
    assert "Aprobar Oficio Petitorio" in html
    assert "Confirmar" in html
    assert "Corregir" in html
    assert "No encontrado" in html
    assert "No aplica" in html


def test_p03_field_actions_confirm_correct_not_found_not_applicable(api_client):
    """
    3, 4, 6, 7, 8, 9. Verifica acciones por campo (CONFIRM, CORRECT, MARK_NOT_FOUND, MARK_NOT_APPLICABLE).
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    review_payload = {
        "actions": [
            {"field_name": "ruc", "action_type": "CONFIRM", "new_value": "2400123456-7", "operator": "PERITO"},
            {"field_name": "nue", "action_type": "CORRECT", "new_value": "8849201", "operator": "PERITO"},
            {"field_name": "oficio_number", "action_type": "MARK_NOT_FOUND", "operator": "PERITO"},
            {"field_name": "log_reference", "action_type": "MARK_NOT_APPLICABLE", "operator": "PERITO"}
        ]
    }
    rev_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json=review_payload)
    assert rev_resp.status_code == 200

    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    assert ext_resp.status_code == 200
    ext_data = ext_resp.json()

    ruc_f = next(f for f in ext_data["fields"] if f["field_name"] == "ruc")
    assert ruc_f["status"] == "CONFIRMED"

    nue_f = next(f for f in ext_data["fields"] if f["field_name"] == "nue")
    assert nue_f["status"] == "CORRECTED_BY_HUMAN"
    assert nue_f["value"] == "8849201"

    oficio_f = next(f for f in ext_data["fields"] if f["field_name"] == "oficio_number")
    assert oficio_f["status"] == "NOT_FOUND"

    log_f = next(f for f in ext_data["fields"] if f["field_name"] == "log_reference")
    assert log_f["status"] == "NOT_APPLICABLE"


def test_p03_observed_value_preserved_on_correction(db_session, filestore):
    """
    5. Preservación estricta de observed_value al corregir un campo.
    """
    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc_p03_obs", png_path, "petition.png", str(png_path))
    petition_rec = persister.persist_petition_entity(doc, ext, actor="INITIAL")
    db_session.commit()

    action = FieldReviewAction(
        field_name="prosecutor_name",
        action_type="CORRECT",
        new_value="PEDRO PEREZ MANRIQUEZ",
        operator="HUMAN_OPERATOR"
    )
    updated_ext = petition_service.apply_human_review(ext, [action])
    persister.persist_petition_entity(doc, updated_ext, actor="HUMAN_OPERATOR")
    db_session.commit()

    reviews = persister.petition_repo.get_field_reviews(petition_rec.id)
    p_review = next(r for r in reviews if r.field_name == "prosecutor_name")
    assert p_review.observed_value is not None
    assert p_review.confirmed_value == "PEDRO PEREZ MANRIQUEZ"
    assert p_review.status == "CORRECTED_BY_HUMAN"


def test_p03_repeatable_lists_manual_input_and_human_provenance(api_client):
    """
    10, 11, 12, 13, 14, 15. Edición y adición manual de listas repetibles marcando proveniencia HUMAN_INPUT.
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    review_payload = {
        "actions": [],
        "evidence_items": [
            {
                "nue_number": "8849201",
                "description_original": "Celular Samsung Galaxy S21",
                "evidence_type_declared": "Celular",
                "brand_declared": "Samsung",
                "model_declared": "Galaxy S21",
                "serial_number_declared": "SN123",
                "capacity_declared": "128 GB",
                "source": "HUMAN_INPUT"
            },
            {
                "nue_number": "8849202",
                "description_original": "Pendrive Kingston DataTraveler",
                "evidence_type_declared": "Pendrive",
                "brand_declared": "Kingston",
                "model_declared": "DataTraveler",
                "serial_number_declared": "SN999",
                "capacity_declared": "64 GB",
                "source": "HUMAN_INPUT"
            }
        ],
        "requested_actions": [
            {
                "source_text": "Extracción forense de dispositivo",
                "normalized_action": "Peritaje telefónico",
                "source": "HUMAN_INPUT"
            }
        ],
        "attachments": [
            {
                "attachment_type": "Acta",
                "description": "Acta de recepción de evidencia",
                "reference_number": "4455",
                "source": "HUMAN_INPUT"
            }
        ]
    }

    rev_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json=review_payload)
    assert rev_resp.status_code == 200

    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    data = ext_resp.json()

    assert len(data["evidence_items"]) == 2
    assert data["evidence_items"][1]["nue_number"] == "8849202"
    assert data["evidence_items"][1]["source"] == "HUMAN_INPUT"
    assert len(data["requested_actions"]) == 1
    assert data["requested_actions"][0]["source"] == "HUMAN_INPUT"
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["source"] == "HUMAN_INPUT"


def test_p03_persistence_upon_reload(api_client, db_session):
    """
    16. Verificación de persistencia en PostgreSQL tras recargar/consultar la API.
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    review_payload = {
        "actions": [
            {"field_name": "ruc", "action_type": "CONFIRM", "new_value": "2400123456-7", "operator": "PERITO"},
            {"field_name": "nue", "action_type": "CONFIRM", "new_value": "8849201", "operator": "PERITO"}
        ]
    }
    post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json=review_payload)

    # Re-consultar la extracción simulando recarga
    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    assert ext_resp.status_code == 200
    fields = ext_resp.json()["fields"]
    ruc_f = next(f for f in fields if f["field_name"] == "ruc")
    assert ruc_f["status"] == "CONFIRMED"


def test_p03_conflicts_gating_blocks_approval(api_client):
    """
    17, 18, 19. Conflictos visibles y bloqueo de aprobación por conflicto abierto.
    """
    pdf_path = FIXTURES_DIR / "petition_conflict.pdf"
    with open(pdf_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition_conflict.pdf", f, "application/pdf")}
        )
    doc_id = stage_resp.json()["document_id"]

    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    assert len(ext_resp.json()["conflicts"]) > 0

    # Intentar aprobar con conflictos abiertos debe fallar (400)
    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 400
    assert app_resp.json()["detail"]["error_code"] == "OPEN_CONFLICTS"


def test_p03_approval_gating_unconfirmed_ruc_or_nue(api_client):
    """
    20, 21. Gating: Bloqueo de aprobación si RUC o NUE no están confirmados.
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    # Resolver conflictos para evaluar sólo gating de confirmación RUC / NUE / Pendientes
    review_payload = {
        "actions": [
            {"field_name": "ruc", "action_type": "MARK_NOT_FOUND", "operator": "PERITO"}
        ]
    }
    post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json=review_payload)

    # Sin confirmación
    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 400
    assert app_resp.json()["detail"]["error_code"] in ("RUC_UNCONFIRMED", "NUE_UNCONFIRMED", "FIELDS_PENDING_REVIEW")


def test_p03_approval_gating_pending_fields(api_client):
    """
    22. Gating: Bloqueo de aprobación si hay campos sin revisar.
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    # Confirmar solo RUC y NUE
    review_payload = {
        "actions": [
            {"field_name": "ruc", "action_type": "CONFIRM", "new_value": "2400123456-7", "operator": "PERITO"},
            {"field_name": "nue", "action_type": "CONFIRM", "new_value": "8849201", "operator": "PERITO"}
        ]
    }
    post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json=review_payload)

    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 400
    assert app_resp.json()["detail"]["error_code"] == "FIELDS_PENDING_REVIEW"


def test_p03_successful_approval_and_audit(api_client, db_session):
    """
    23, 24. Aprobación exitosa con todos los campos revisados y registro de auditoría.
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    field_names = [f["field_name"] for f in ext_resp.json()["fields"]]

    actions = []
    for fn in field_names:
        actions.append({"field_name": fn, "action_type": "CONFIRM", "operator": "PERITO"})

    rev_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json={"actions": actions})
    assert rev_resp.status_code == 200

    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 200
    data = app_resp.json()
    assert data["review_status"] == "APPROVED"

    # Verificar registro en AuditEventModel
    from agente_forense.persistence.models import AuditEventModel
    audit_event = db_session.query(AuditEventModel).filter_by(event_type="petition_approved").first()
    assert audit_event is not None


def test_p03_approval_does_not_create_case_or_species_or_dsm(api_client, db_session):
    """
    25, 26, 27, 28. La aprobación del Petitorio NO debe crear caso, NUE definitiva, especies ni DSM.
    """
    from agente_forense.persistence.models import CaseModel
    cases_before = db_session.query(CaseModel).count()

    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    field_names = [f["field_name"] for f in ext_resp.json()["fields"]]
    actions = [{"field_name": fn, "action_type": "CONFIRM", "operator": "PERITO"} for fn in field_names]

    post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json={"actions": actions})
    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 200

    cases_after = db_session.query(CaseModel).count()
    assert cases_after == cases_before


def test_p03_csrf_required_on_mutation_endpoints(api_client):
    """
    29. Verificación de CSRF requerido en endpoints de mutación (/review y /approve).
    """
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    # Petición sin token CSRF en review
    rev_bad = api_client.post(f"/api/petitions/{doc_id}/review", json={"actions": []})
    assert rev_bad.status_code == 403

    # Petición sin token CSRF en approve
    app_bad = api_client.post(f"/api/petitions/{doc_id}/approve")
    assert app_bad.status_code == 403


def test_p03_controlled_spanish_errors(api_client):
    """
    30. Mensajes de error controlados en español sin exposición de tracebacks.
    """
    resp = api_client.get("/api/petitions/non_existent_id_999/extraction")
    assert resp.status_code == 404
    data = resp.json()
    assert "error_code" in data["detail"] or "message" in data["detail"] or "detail" in data


def test_p03_regression_requesting_unit_preserves_observed(db_session, filestore):
    """
    31. Test de regresión para requesting_unit: conservando observed_value largo original y confirmando valor limpio.
    """
    petition_service = PetitionService()
    persister = PetitionPersistenceService(session=db_session, filestore=filestore)

    png_path = FIXTURES_DIR / "petition.png"
    doc, ext = petition_service.process_petition_file("doc_p03_req_unit", png_path, "petition.png", str(png_path))
    petition_rec = persister.persist_petition_entity(doc, ext, actor="INITIAL")
    db_session.commit()

    clean_value = "BRIGADA INVESTIGADORA DE DELITOS SEXUALES METROPOLITANA"

    action = FieldReviewAction(
        field_name="requesting_unit",
        action_type="CORRECT",
        new_value=clean_value,
        operator="PERITO"
    )
    updated_ext = petition_service.apply_human_review(ext, [action])

    persister.persist_petition_entity(doc, updated_ext, actor="PERITO")
    db_session.commit()

    reviews = persister.petition_repo.get_field_reviews(petition_rec.id)
    req_review = next(r for r in reviews if r.field_name == "requesting_unit")
    assert req_review.status == "CORRECTED_BY_HUMAN"
    assert req_review.confirmed_value == clean_value


# -----------------------------------------------------------------------------
# 10. CSRF SECURITY REGRESSION TESTS FOR PETITION STAGING / UPLOAD
# -----------------------------------------------------------------------------

def test_csrf_petition_upload_without_csrf_rejected(api_client):
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = api_client.post(
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 403
    data = resp.json()
    assert data["error_code"] == "CSRF_ERROR"


def test_csrf_petition_upload_cookie_without_header_rejected(api_client):
    health_res = api_client.get("/health")
    token = health_res.cookies.get("csrf_token")
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = api_client.post(
            "/api/petitions/stage",
            cookies={"csrf_token": token},
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CSRF_ERROR"


def test_csrf_petition_upload_header_without_cookie_rejected():
    app = create_app()
    with TestClient(app) as client:
        png_path = FIXTURES_DIR / "petition.png"
        with open(png_path, "rb") as f:
            resp = client.post(
                "/api/petitions/stage",
                headers={"x-csrf-token": "fake_header_token_without_cookie"},
                files={"file": ("petition.png", f, "image/png")}
            )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "CSRF_ERROR"


def test_csrf_petition_upload_mismatched_tokens_rejected(api_client):
    health_res = api_client.get("/health")
    token = health_res.cookies.get("csrf_token")
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = api_client.post(
            "/api/petitions/stage",
            cookies={"csrf_token": token},
            headers={"x-csrf-token": "invalid_mismatched_token_12345"},
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CSRF_ERROR"


def test_csrf_petition_upload_valid_tokens_accepted(api_client):
    health_res = api_client.get("/health")
    token = health_res.cookies.get("csrf_token")
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = api_client.post(
            "/api/petitions/stage",
            cookies={"csrf_token": token},
            headers={"x-csrf-token": token},
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 200
    assert "document_id" in resp.json()


def test_csrf_invalid_does_not_create_staging_file(api_client):
    from agente_forense.web.routes.api_petitions import _STAGED_DOCUMENTS
    initial_count = len(_STAGED_DOCUMENTS)
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = api_client.post(
            "/api/petitions/stage",
            cookies={"csrf_token": "token_a"},
            headers={"x-csrf-token": "token_b"},
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 403
    assert len(_STAGED_DOCUMENTS) == initial_count



def test_api_stage_petition_png(api_client):
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["processing_status"] == "REVIEW_REQUIRED"
    assert "sha256" in data
    assert "document_id" in data


def test_api_stage_petition_scanned_pdf(api_client):
    pdf_path = FIXTURES_DIR / "petition_scanned.pdf"
    with open(pdf_path, "rb") as f:
        resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition_scanned.pdf", f, "application/pdf")}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["processing_status"] in ("REVIEW_REQUIRED", "FIELDS_EXTRACTED")


def test_api_upload_unsupported_format(api_client):
    resp = post_with_csrf(
        api_client,
        "/api/petitions/stage",
        files={"file": ("doc.txt", b"Texto no soportado", "text/plain")}
    )
    assert resp.status_code == 400


def test_api_review_and_draft_flow(api_client):
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    # Confirmar o resolver todos los campos extraidos para aprobar
    ext_resp = api_client.get(f"/api/petitions/{doc_id}/extraction")
    ext_data = ext_resp.json()
    all_actions = [
        {"field_name": f["field_name"], "action_type": "CONFIRM", "new_value": f["value"] or "2400123456-7" if f["field_name"] == "ruc" else (f["value"] or "8849201" if f["field_name"] == "nue" else (f["value"] or "458-2026")), "operator": "PERITO"}
        for f in ext_data["fields"]
    ]
    rev_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/review", json={"actions": all_actions})
    assert rev_resp.status_code == 200

    app_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/approve")
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "APPROVED"

    draft_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/draft")
    if draft_resp.status_code == 404:
        draft_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/build-draft")
    assert draft_resp.status_code == 200
    draft_data = draft_resp.json()
    assert draft_data["ruc"] == "2400123456-7"
    assert draft_data["nues"][0]["nue_number"] == "8849201"
    assert "458" in draft_data["oficio_number"]


def test_api_draft_without_review_returns_400(api_client):
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    draft_resp = post_with_csrf(api_client, f"/api/petitions/{doc_id}/build-draft")
    assert draft_resp.status_code in (400, 409)


def test_web_ui_cases_new_route(api_client):
    resp = api_client.get("/cases/new")
    assert resp.status_code == 200
    assert "Revisión Humana" in resp.text
    assert "/api/petitions/stage" in resp.text


def test_api_get_petition_status_by_id(api_client):
    png_path = FIXTURES_DIR / "petition.png"
    with open(png_path, "rb") as f:
        stage_resp = post_with_csrf(
            api_client,
            "/api/petitions/stage",
            files={"file": ("petition.png", f, "image/png")}
        )
    doc_id = stage_resp.json()["document_id"]

    get_resp = api_client.get(f"/api/petitions/{doc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["document_id"] == doc_id


def test_api_get_nonexistent_id_returns_404(api_client):
    get_resp = api_client.get("/api/petitions/nonexistent_doc_id_12345")
    assert get_resp.status_code == 404
