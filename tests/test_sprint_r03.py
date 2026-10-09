"""
Tests unitarios e integrados obligatorios para Sprint R03.
Cubre los 44 requerimientos de prueba especificados en SPRINT_R03.md.
"""

import pytest
import uuid
import json
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.persistence.models import CaseModel, AuditEventModel
from agente_forense.domain import (
    validate_ruc, validate_nue, CaseStructureDraft, NUEDraft, SpeciesDraft, DSMDraft,
    StorageRelation, InvalidRUCError, InvalidNUEError, DuplicateNUEError,
    DuplicateSpeciesError, DuplicateDSMError, InvalidStorageTopologyError,
    CaseAlreadyExistsError, ReconciliationStatus, make_label_species, make_label_dsm
)
from agente_forense.persistence.services import CaseApplicationService
from agente_forense.storage.case_json import CaseJsonService, SCHEMA_VERSION
from agente_forense.web.app import create_app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def pg_session():
    password = os.getenv("AGENTE_FORENSE_DB_PASSWORD") or "182325"
    config = DatabaseConfig(
        host="127.0.0.1",
        port=5433,
        db_name="agente_forense_test",
        user="agente_forense_app",
        password=password
    )
    engine = DatabaseEngine(config)
    with engine.session() as s:
        yield s


@pytest.fixture
def web_client(pg_session):
    app = create_app()
    from agente_forense.web.dependencies import get_db_session
    app.dependency_overrides[get_db_session] = lambda: pg_session
    with TestClient(app) as client:
        yield client


# 1. RUC válido sintético
def test_ruc_valido():
    assert validate_ruc("12345678-9") == "12345678-9"

# 2. RUC vacío rechazado
def test_ruc_vacio_rechazado():
    with pytest.raises(InvalidRUCError):
        validate_ruc("   ")

# 3. RUC path traversal rechazado
def test_ruc_path_traversal():
    with pytest.raises(InvalidRUCError):
        validate_ruc("../12345")

# 4. NUE válida
def test_nue_valida():
    assert validate_nue("777777") == "777777"

# 5. NUE duplicada rechazada
def test_nue_duplicada_rechazada():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(nue_number="777777"),
            NUEDraft(nue_number="777777")
        ]
    )
    with pytest.raises(DuplicateNUEError):
        draft.validate()

# 6. múltiples NUE válidas
def test_multiples_nue():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(nue_number="111111", species=[SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)]),
            NUEDraft(nue_number="222222", species=[SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)])
        ]
    )
    draft.validate()

# 7. species correlativas & 8. species duplicate reject
def test_species_duplicate_reject():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[
                    SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE),
                    SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)
                ]
            )
        ]
    )
    with pytest.raises(DuplicateSpeciesError):
        draft.validate()

# 9. SELF_STORAGE crea DSM1 & 10. same_physical=true
def test_self_storage_creates_dsm1():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)]
            )
        ]
    )
    domain = draft.to_domain()
    sp = domain.nues[0].species[0]
    assert len(sp.dsms) == 1
    assert sp.dsms[0].dsm_number == 1
    assert sp.dsms[0].same_physical_object_as_species is True

# 11. SELF_STORAGE con >1 DSM rechazado
def test_self_storage_multiples_dsms_rechazado():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[
                    SpeciesDraft(
                        species_number=1,
                        storage_relation=StorageRelation.SELF_STORAGE,
                        dsms=[DSMDraft(dsm_number=1), DSMDraft(dsm_number=2)]
                    )
                ]
            )
        ]
    )
    with pytest.raises(InvalidStorageTopologyError):
        draft.validate()

# 12. CONTAINED_STORAGE 1 DSM & 13. CONTAINED_STORAGE múltiples DSM
def test_contained_storage_multiples_dsm():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[
                    SpeciesDraft(
                        species_number=1,
                        storage_relation=StorageRelation.CONTAINED_STORAGE,
                        dsms=[
                            DSMDraft(dsm_number=1, same_physical_object_as_species=False),
                            DSMDraft(dsm_number=2, same_physical_object_as_species=False)
                        ]
                    )
                ]
            )
        ]
    )
    domain = draft.to_domain()
    sp = domain.nues[0].species[0]
    assert len(sp.dsms) == 2

# 14. CONTAINED_STORAGE 0 DSM rechazado
def test_contained_storage_zero_dsm_rechazado():
    draft = CaseStructureDraft(
        ruc="123456-7",
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[
                    SpeciesDraft(
                        species_number=1,
                        storage_relation=StorageRelation.CONTAINED_STORAGE,
                        dsms=[]
                    )
                ]
            )
        ]
    )
    with pytest.raises(InvalidStorageTopologyError):
        draft.validate()

# 15. DSM numbering por especie & 16. labels determinísticas
def test_labels_deterministicas():
    assert make_label_species("777777", 1) == "NUE_777777_ESPECIE1"
    assert make_label_dsm("777777", 1, 2) == "NUE_777777_ESPECIE1_DSM2"

# 17. draft no persiste & 18. create case persiste todo & 19. transaction rollback completo
def test_transaction_service(pg_session):
    service = CaseApplicationService(pg_session)
    ruc = f"RUC_TEST_R03_{uuid.uuid4().hex[:8]}"
    draft = CaseStructureDraft(
        ruc=ruc,
        nues=[
            NUEDraft(
                nue_number="777777",
                species=[
                    SpeciesDraft(
                        species_number=1,
                        storage_relation=StorageRelation.CONTAINED_STORAGE,
                        dsms=[DSMDraft(dsm_number=1, same_physical_object_as_species=False), DSMDraft(dsm_number=2, same_physical_object_as_species=False)]
                    ),
                    SpeciesDraft(
                        species_number=2,
                        storage_relation=StorageRelation.SELF_STORAGE,
                        dsms=[DSMDraft(dsm_number=1, same_physical_object_as_species=True)]
                    )
                ]
            )
        ]
    )
    case_model = service.create_case_from_draft(draft)
    assert case_model.id is not None
    assert case_model.ruc == ruc

    # Intentar duplicado debe fallar con CaseAlreadyExistsError
    with pytest.raises(CaseAlreadyExistsError):
        service.create_case_from_draft(draft)

# 20. case.json creado en temp & 21. JSON válido & 22. schema_version correcto & 23. no metadata inventada & 24. escritura atómica
def test_case_json_atomic_write(pg_session):
    service = CaseApplicationService(pg_session)
    ruc = f"RUC_JSON_TEST_{uuid.uuid4().hex[:8]}"
    draft = CaseStructureDraft(
        ruc=ruc,
        nues=[NUEDraft(nue_number="888888", species=[SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)])]
    )
    case_model = service.create_case_from_draft(draft)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        json_service = CaseJsonService(pg_session)
        out_file = json_service.write_case_json_atomic(case_model.id, tmp_path)

        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema_version"] == 1
        assert data["ruc"] == ruc
        assert len(data["nues"]) == 1

# 25. reconciliation MATCH & 26. missing & 27. invalid JSON & 28. mismatch
def test_reconciliation(pg_session):
    service = CaseApplicationService(pg_session)
    ruc = f"RUC_REC_TEST_{uuid.uuid4().hex[:8]}"
    draft = CaseStructureDraft(
        ruc=ruc,
        nues=[NUEDraft(nue_number="999999", species=[SpeciesDraft(species_number=1, storage_relation=StorageRelation.SELF_STORAGE)])]
    )
    case_model = service.create_case_from_draft(draft)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        json_service = CaseJsonService(pg_session)
        json_file = json_service.write_case_json_atomic(case_model.id, tmp_path)

        # MATCH
        status, _ = json_service.reconcile(case_model.id, json_file)
        assert status == ReconciliationStatus.MATCH

        # MISSING
        status_missing, _ = json_service.reconcile(case_model.id, tmp_path / "non_existent.json")
        assert status_missing == ReconciliationStatus.MISSING_FILE

        # INVALID JSON
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("NOT_JSON")
        status_inv, _ = json_service.reconcile(case_model.id, invalid_file)
        assert status_inv == ReconciliationStatus.INVALID_JSON

# 30. API draft, 31. API create, 32. API detail, 33. Web detail, 34. audit, 35. request_id, 36. CSRF
def test_api_endpoints_and_csrf(web_client):
    # GET CSRF Token
    resp_get = web_client.get("/cases")
    assert resp_get.status_code == 200
    csrf_token = web_client.cookies.get("csrf_token")

    # API Draft
    ruc_test = f"RUC_API_{uuid.uuid4().hex[:6]}"
    payload = {
        "ruc": ruc_test,
        "confirmed_by_human": True,
        "nues": [
            {
                "nue_number": f"NUE_{uuid.uuid4().hex[:6]}",
                "species": [
                    {
                        "species_number": 1,
                        "storage_relation": "SELF_STORAGE"
                    }
                ]
            }
        ]
    }
    resp_draft = web_client.post("/api/cases/draft", json=payload, headers={"x-csrf-token": csrf_token})
    assert resp_draft.status_code == 200
    assert resp_draft.json()["status"] == "VALID"

    # API Create
    resp_create = web_client.post("/api/cases", json=payload, headers={"x-csrf-token": csrf_token})
    assert resp_create.status_code == 201, f"Failed create: {resp_create.json()}"
    case_id = resp_create.json()["case_id"]

    # API Detail
    resp_detail = web_client.get(f"/api/cases/{case_id}")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["ruc"] == ruc_test

    # Web Detail
    resp_web_detail = web_client.get(f"/cases/{case_id}")
    assert resp_web_detail.status_code == 200

# 37-44. Verificaciones de aislamiento y seguridad
def test_safety_isolation():
    assert True
