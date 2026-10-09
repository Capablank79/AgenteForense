"""
Tests unitarios e integración para Sprint R07.1:
Pruebas de escaneo de discos, clasificación fail-closed, matching DSM, persistencia append-oriented,
revalidación, transiciones de orquestación a ACQUISITION_READY y rutas API con CSRF.
"""

import os
from typing import Tuple, Optional, Dict, Any
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.persistence.models import CaseModel, NueModel, SpeciesModel, DsmModel
from agente_forense.orchestration.errors import ConfirmationRequiredError
from agente_forense.hardware.models import (
    DiskSnapshot, ClassifiedDisk, ForensicDiskClassification, BindingStatus
)
from agente_forense.hardware.disks import DiskScanner
from agente_forense.hardware.matching import compare_dsm_with_disk
from agente_forense.hardware.bindings import DiskBindingService, DsmDiskBindingModel
from agente_forense.hardware.revalidation import DiskRevalidator
from agente_forense.hardware.service import HardwareService
from agente_forense.hardware.errors import (
    DiskNotReadOnlyError, SystemDiskBlockedError, BootDiskBlockedError,
    DiskNotFoundError, SourceChangedError, DiskBindingNotConfirmedError
)
from agente_forense.orchestration.orchestrator import CaseOrchestrator
from agente_forense.orchestration.states import OperativeState
from agente_forense.web.app import create_app
from agente_forense.web.dependencies import get_db_session


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
    engine = DatabaseEngine(db_config)
    return engine


@pytest.fixture
def db_session(db_engine):
    with db_engine.session() as session:
        yield session


@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    with TestClient(app) as c:
        yield c


def create_test_hierarchy(session: Session) -> Tuple[CaseModel, DsmModel]:
    unique_ruc = f"12345678-{uuid.uuid4().hex[:4]}"
    case = CaseModel(id=uuid.uuid4(), ruc=unique_ruc, status="NEW", state_version=1)
    session.add(case)
    session.flush()

    nue = NueModel(id=uuid.uuid4(), case_id=case.id, nue_number=f"NUE_{uuid.uuid4().hex[:4]}", status="PENDING")
    session.add(nue)
    session.flush()

    species = SpeciesModel(
        id=uuid.uuid4(),
        nue_id=nue.id,
        species_number=1,
        label="Especie Pendrive",
        storage_relation="SELF_STORAGE",
        status="PENDING"
    )
    session.add(species)
    session.flush()

    dsm = DsmModel(
        id=uuid.uuid4(),
        species_id=species.id,
        dsm_number=1,
        label="DSM Kingston 64GB",
        brand="Kingston",
        model="DataTraveler 3.0",
        serial="KNG123456789",
        capacity_bytes=64000000000
    )
    session.add(dsm)
    session.commit()
    return case, dsm


def test_disk_classification_fail_closed():
    # Disco 0: Sistema, Boot, No ReadOnly -> Bloqueado por múltiples razones
    snap_sys = DiskSnapshot(
        disk_number=0, physical_drive="\\\\.\\PhysicalDrive0", friendly_name="NVMe OS",
        size_bytes=512000000000, is_read_only=False, is_system=True, is_boot=True
    )
    classified_sys = DiskScanner.classify_disk(snap_sys)
    assert classified_sys.classification == ForensicDiskClassification.BLOCKED_MULTIPLE_REASONS
    assert any("IsReadOnly" in r for r in classified_sys.reasons)
    assert any("IsSystem" in r for r in classified_sys.reasons)

    # Disco 1: No ReadOnly -> BLOCKED_NOT_READ_ONLY
    snap_rw = DiskSnapshot(
        disk_number=1, physical_drive="\\\\.\\PhysicalDrive1", friendly_name="USB Pendrive",
        size_bytes=64000000000, is_read_only=False, is_system=False, is_boot=False
    )
    classified_rw = DiskScanner.classify_disk(snap_rw)
    assert classified_rw.classification == ForensicDiskClassification.BLOCKED_NOT_READ_ONLY

    # Disco 2: ReadOnly, Not System, Not Boot -> FORENSIC_CANDIDATE
    snap_candidate = DiskSnapshot(
        disk_number=2, physical_drive="\\\\.\\PhysicalDrive2", friendly_name="Kingston USB",
        serial_number="KNG123456789", size_bytes=64000000000, is_read_only=True, is_system=False, is_boot=False
    )
    classified_cand = DiskScanner.classify_disk(snap_candidate)
    assert classified_cand.classification == ForensicDiskClassification.FORENSIC_CANDIDATE


def test_dsm_disk_matching():
    dsm_data = {
        "id": str(uuid.uuid4()),
        "brand": "Kingston",
        "model": "DataTraveler 3.0",
        "serial": "KNG123456789",
        "capacity_bytes": 64000000000
    }
    snap_match = DiskSnapshot(
        disk_number=2, physical_drive="\\\\.\\PhysicalDrive2", friendly_name="Kingston DataTraveler 3.0",
        serial_number="  KNG123456789  ", size_bytes=64000000000, is_read_only=True, is_system=False, is_boot=False
    )

    comp = compare_dsm_with_disk(dsm_data, snap_match)
    assert comp.serial_matched is True
    assert comp.capacity_matched is True
    assert comp.model_matched is True


def test_binding_flow_and_revalidation(db_session):
    case, dsm = create_test_hierarchy(db_session)
    binding_service = DiskBindingService(db_session)

    snap_read_write = DiskSnapshot(
        disk_number=1, physical_drive="\\\\.\\PhysicalDrive1", friendly_name="Writeable USB",
        size_bytes=64000000000, is_read_only=False, is_system=False, is_boot=False
    )

    # Intento de binding sobre disco no read-only debe fallar por fail-closed
    with pytest.raises(DiskNotReadOnlyError):
        binding_service.propose_binding(case.id, dsm.id, disk_number=1, override_snapshot=snap_read_write)

    # Proponer binding sintético válido (Read-Only)
    snap_valid = DiskSnapshot(
        disk_number=2, physical_drive="\\\\.\\PhysicalDrive2", friendly_name="Kingston USB Blocked",
        serial_number="KNG123456789", size_bytes=64000000000, is_read_only=True, is_system=False, is_boot=False
    )

    prop = binding_service.propose_binding(case.id, dsm.id, disk_number=2, override_snapshot=snap_valid)
    assert prop.status == BindingStatus.PROPOSED.value

    # Confirmar binding por Human Gate
    confirmed = binding_service.confirm_binding(case.id, dsm.id, binding_id=prop.id)
    assert confirmed.status == BindingStatus.CONFIRMED.value
    assert confirmed.confirmed_at is not None

    # Revalidación exitosa
    reval = binding_service.revalidate_active_binding(case.id, dsm.id, override_revalidation_snap=snap_valid)
    assert reval.status == BindingStatus.CONFIRMED.value

    # Revalidación fallida por cambio de Write Blocker (IsReadOnly -> False)
    snap_tampered = DiskSnapshot(
        disk_number=2, physical_drive="\\\\.\\PhysicalDrive2", friendly_name="Kingston USB Blocked",
        serial_number="KNG123456789", size_bytes=64000000000, is_read_only=False, is_system=False, is_boot=False
    )
    with pytest.raises(SourceChangedError):
        binding_service.revalidate_active_binding(case.id, dsm.id, override_revalidation_snap=snap_tampered)

    # Verificar que el binding anterior fue invalidado por fail-closed
    invalidated = db_session.query(DsmDiskBindingModel).filter(DsmDiskBindingModel.id == confirmed.id).first()
    assert invalidated.status == BindingStatus.INVALIDATED.value


def test_orchestration_state_acquisition_ready(db_session, tmp_path):
    case, dsm = create_test_hierarchy(db_session)
    case.case_root = str(tmp_path)
    db_session.commit()

    binding_service = DiskBindingService(db_session)
    orchestrator = CaseOrchestrator(db_session, storage_root=tmp_path.parent)

    # Inicializar case.json en el almacenamiento
    orchestrator.case_json_service.write_case_json_atomic(case.id, tmp_path)

    # Crear binding confirmado sintético
    snap_valid = DiskSnapshot(
        disk_number=3, physical_drive="\\\\.\\PhysicalDrive3", friendly_name="Forensic Target",
        serial_number="KNG123456789", size_bytes=64000000000, is_read_only=True, is_system=False, is_boot=False
    )
    prop = binding_service.propose_binding(case.id, dsm.id, disk_number=3, override_snapshot=snap_valid)
    binding_service.confirm_binding(case.id, dsm.id, binding_id=prop.id)

    # Mover el caso a IDENTIFICATION_COMPLETED o avanzar de NEW -> IDENTIFICATION_IN_PROGRESS -> IDENTIFICATION_COMPLETED
    orchestrator.execute_action(case_id=case.id, action="START_IDENTIFICATION", operator="OPERATOR")
    orchestrator.execute_action(case_id=case.id, action="COMPLETE_IDENTIFICATION_MOCK", operator="OPERATOR")

    # Contexto de orquestación debe reflejar binding y permitir avance a ACQUISITION_READY
    ctx = orchestrator.build_context(case.id, selected_dsm_id=dsm.id, active_disk_snapshot=snap_valid)
    assert ctx.disk_binding_confirmed is True
    assert ctx.source_read_only is True

    try:
        orchestrator.execute_action(
            case_id=case.id,
            action="PREPARE_ACQUISITION",
            operator="FORENSIC_OPERATOR",
            payload={"selected_dsm_id": str(dsm.id), "active_disk_snapshot": snap_valid.model_dump(mode="json")}
        )
    except ConfirmationRequiredError as err:
        orchestrator.human_gate.confirm(err.confirmation_id, operator="SUPERVISOR")
        res = orchestrator.execute_action(
            case_id=case.id,
            action="PREPARE_ACQUISITION",
            confirmation_id=err.confirmation_id,
            operator="FORENSIC_OPERATOR",
            payload={"selected_dsm_id": str(dsm.id), "active_disk_snapshot": snap_valid.model_dump(mode="json")}
        )
        assert res["current_state"] == OperativeState.ACQUISITION_READY.value


def test_hardware_api_routes(client, db_session):
    case, dsm = create_test_hierarchy(db_session)

    # 1. Escaneo de discos del sistema
    r_disks = client.get("/api/system/disks")
    assert r_disks.status_code == 200
    disks = r_disks.json()
    assert isinstance(disks, list)

    # 2. Obtener candidatos para DSM
    r_cand = client.get(f"/api/cases/{case.id}/dsms/{dsm.id}/disk-candidates")
    assert r_cand.status_code == 200

    # 3. CSRF Protection check
    r_propose_no_csrf = client.post(
        f"/api/cases/{case.id}/dsms/{dsm.id}/disk-binding/propose",
        json={"disk_number": 999}
    )
    assert r_propose_no_csrf.status_code == 403

    # Obtener CSRF token desde la cookie
    csrf_token = r_disks.cookies.get("csrf_token")
    headers = {"x-csrf-token": csrf_token}

    # Proponer binding con override snapshot
    snap_payload = {
        "disk_number": 5,
        "physical_drive": "\\\\.\\PhysicalDrive5",
        "friendly_name": "API Disk Target",
        "serial_number": "API123456",
        "size_bytes": 64000000000,
        "is_read_only": True,
        "is_system": False,
        "is_boot": False
    }

    r_propose = client.post(
        f"/api/cases/{case.id}/dsms/{dsm.id}/disk-binding/propose",
        json={"disk_number": 5, "override_snapshot": snap_payload},
        headers=headers
    )
    assert r_propose.status_code == 200
    b_data = r_propose.json()
    binding_id = b_data["binding_id"]
    assert b_data["status"] == "PROPOSED"

    # Confirmar binding con CSRF
    r_confirm = client.post(
        f"/api/cases/{case.id}/dsms/{dsm.id}/disk-binding/confirm",
        json={"binding_id": binding_id},
        headers=headers
    )
    assert r_confirm.status_code == 200
    assert r_confirm.json()["status"] == "CONFIRMED"

    # GET active binding
    r_get = client.get(f"/api/cases/{case.id}/dsms/{dsm.id}/disk-binding")
    assert r_get.status_code == 200
    assert r_get.json()["binding_id"] == binding_id

    # Revalidar binding
    r_reval = client.post(
        f"/api/cases/{case.id}/dsms/{dsm.id}/disk-binding/revalidate",
        json={"override_snapshot": snap_payload},
        headers=headers
    )
    assert r_reval.status_code == 200
    assert r_reval.json()["revalidated"] is True
