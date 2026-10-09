"""
Pruebas para el sprint PETITORIO P05: Estructura Física Confirmada (RUC -> NUE -> ESPECIE -> DSM).
"""

import os
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.web import create_app
from agente_forense.web.dependencies import get_db_session
from agente_forense.persistence.models import PetitionModel, CaseModel, NueModel, SpeciesModel, DsmModel
from agente_forense.domain.enums import StorageRelation
from agente_forense.domain.comparison import compare_text_fields, ComparisonStatus


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
    return DatabaseEngine(db_config)


@pytest.fixture
def db_session(db_engine):
    with db_engine.session() as session:
        yield session


@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    with TestClient(app) as c:
        # Obtener cookie CSRF
        resp = c.get("/")
        csrf_token = resp.cookies.get("csrf_token") or "test_csrf_token"
        c.headers.update({"x-csrf-token": csrf_token})
        yield c


def test_comparison_domain_logic():
    """Valida los estados de comparación MATCH, CONFLICT, NOT_OBSERVABLE, NOT_APPLICABLE."""
    # NOT_APPLICABLE
    c1 = compare_text_fields("serial", None, None)
    assert c1.status == ComparisonStatus.NOT_APPLICABLE

    # NOT_OBSERVABLE
    c2 = compare_text_fields("serial", "12345", "")
    assert c2.status == ComparisonStatus.NOT_OBSERVABLE

    # MATCH (ambos informados o solo observado)
    c3 = compare_text_fields("brand", "Lenovo", "lenovo")
    assert c3.status == ComparisonStatus.MATCH

    # CONFLICT
    c4 = compare_text_fields("serial", "ABC-123", "XYZ-999")
    assert c4.status == ComparisonStatus.CONFLICT
    assert "Incongruencia" in c4.details


def test_create_case_requires_human_confirmation(client, db_session: Session):
    """Verifica que POST /api/cases requiera confirmed_by_human = True."""
    test_ruc = f"RUC_P05_{uuid4().hex[:8]}"
    payload = {
        "ruc": test_ruc,
        "requesting_unit": "OS9",
        "request_type": "FORENSIC",
        "confirmed_by_human": False,
        "nues": [
            {
                "nue_number": "7746537",
                "species": [
                    {
                        "species_number": 1,
                        "storage_relation": "SELF_STORAGE",
                        "description": "Pendrive Kingston",
                        "dsms": [
                            {
                                "dsm_number": 1,
                                "same_physical_object_as_species": True,
                                "device_type": "PENDRIVE"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Sin confirmación humana debe fallar con 400
    res = client.post("/api/cases", json=payload)
    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "HUMAN_CONFIRMATION_REQUIRED"

    # Con confirmación humana explícita debe ser exitoso (201)
    payload["confirmed_by_human"] = True
    res2 = client.post("/api/cases", json=payload)
    assert res2.status_code == 201, res2.json()
    data = res2.json()
    assert data["ruc"] == test_ruc
    assert "case_id" in data

    # Verificar en PostgreSQL
    c_db = db_session.query(CaseModel).filter_by(id=data["case_id"]).first()
    assert c_db is not None
    assert c_db.ruc == test_ruc

    # Verificar Especie y DSM creados
    sp_db = db_session.query(SpeciesModel).filter_by(species_number=1).first()
    assert sp_db is not None
    assert sp_db.storage_relation == StorageRelation.SELF_STORAGE

    dsm_db = db_session.query(DsmModel).filter_by(label="NUE_7746537_ESPECIE1_DSM1").first()
    assert dsm_db is not None
    assert dsm_db.same_physical_object_as_species is True


def test_contained_storage_topology_validation(client):
    """Verifica que CONTAINED_STORAGE sin DSMs falle la validación de topología física."""
    payload = {
        "ruc": "2609999999-9",
        "confirmed_by_human": False,
        "nues": [
            {
                "nue_number": "888888",
                "species": [
                    {
                        "species_number": 1,
                        "storage_relation": "CONTAINED_STORAGE",
                        "description": "Notebook sin discos",
                        "dsms": [] # INVÁLIDO para CONTAINED_STORAGE
                    }
                ]
            }
        ]
    }
    res = client.post("/api/cases/draft", json=payload)
    assert res.status_code == 400
    assert "CONTAINED_STORAGE exige 1 o más DSMs" in res.json()["detail"]["message"]


def test_case_json_includes_petition_metadata(client, db_session: Session):
    """Verifica que case.json generado tras la confirmación incluya el bloque 'petition'."""
    test_ruc = f"RUC_P05_{uuid4().hex[:8]}"

    # Crear caso de prueba previo en BD
    c_rec = CaseModel(id=uuid4(), ruc=f"PREV_{test_ruc}", status="NEW")
    db_session.add(c_rec)
    db_session.flush()

    # Crear archivo de soporte en BD para la relación de file_id
    from agente_forense.persistence.models import FileModel
    f_rec = FileModel(
        id=uuid4(),
        case_id=c_rec.id,
        file_role="PETITION",
        original_filename="petitorio.pdf",
        stored_filename="petitorio.pdf",
        relative_path="/tmp/petitorio.pdf",
        sha256="abc123sha256hash",
        mime_type="application/pdf",
        size_bytes=1024,
        source="UPLOAD"
    )
    db_session.add(f_rec)
    db_session.flush()

    # Crear petición aprobada previa en BD
    pet = PetitionModel(
        id=uuid4(),
        file_id=f_rec.id,
        ruc=test_ruc,
        petition_number="OF-100-2026",
        prosecutor_office="Fiscalía Santiago",
        review_status="APPROVED",
        sha256="abc123sha256hash"
    )
    db_session.add(pet)
    db_session.commit()

    payload = {
        "ruc": test_ruc,
        "confirmed_by_human": True,
        "nues": [
            {
                "nue_number": "112233",
                "species": [
                    {
                        "species_number": 1,
                        "storage_relation": "SELF_STORAGE",
                        "dsms": [
                            {
                                "dsm_number": 1,
                                "same_physical_object_as_species": True
                            }
                        ]
                    }
                ]
            }
        ]
    }
    res = client.post("/api/cases", json=payload)
    assert res.status_code == 201, res.json()

    # Leer el snapshot case.json generado
    from agente_forense.storage.case_json import CaseJsonService
    svc = CaseJsonService(db_session)
    c_data = svc.generate_case_json_data(res.json()["case_id"])

    assert "petition" in c_data
    assert c_data["petition"] is not None
    assert c_data["petition"]["petition_id"] == str(pet.id)
    assert c_data["petition"]["sha256"] == "abc123sha256hash"
    assert c_data["petition"]["status"] == "APPROVED"
