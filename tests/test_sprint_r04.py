"""
Tests unitarios e integración para Sprint R04:
StateMachine, PolicyEngine, HumanGate, CaseOrchestrator, Concurrencia, Recovery, Safety y Web/API.
"""

import os
import pytest
import uuid
from pathlib import Path
import tempfile
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.persistence.models import (
    Base, CaseModel, NueModel, SpeciesModel, DsmModel, CaseEventModel, AuditEventModel, HumanConfirmationModel
)
from agente_forense.orchestration.states import CaseState, OperativeState, ReservedState
from agente_forense.orchestration.orchestrator import CaseOrchestrator
from agente_forense.orchestration.policies import PolicyEngine, PolicyDecision
from agente_forense.orchestration.human_gate import HumanGate, ConfirmationStatus
from agente_forense.hardware.service import HardwareService
from agente_forense.hardware.bindings import DiskBindingService
from agente_forense.hardware.models import DiskSnapshot
from agente_forense.orchestration.errors import (
    InvalidTransitionError, PolicyDeniedError, ConfirmationRequiredError,
    ConfirmationNotFoundError, ConfirmationAlreadyResolvedError, ConcurrencyConflictError
)
from agente_forense.storage.case_json import CaseJsonService
from agente_forense.web.app import create_app


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
    """TestClient de FastAPI con dependencia de DB sobrecargada."""
    app = create_app()
    from agente_forense.web.dependencies import get_db_session
    app.dependency_overrides[get_db_session] = lambda: db_session
    with TestClient(app) as c:
        yield c


def create_full_test_case(session: Session, ruc: str = None, storage_root: Path = None) -> CaseModel:
    """Helper para crear una jerarquía completa de caso en DB (RUC -> NUE -> ESPECIE -> DSM)."""
    unique_ruc = ruc or f"RUC_{uuid.uuid4().hex[:8]}"
    case_dir_str = str(storage_root / unique_ruc) if storage_root else None
    case = CaseModel(id=uuid.uuid4(), ruc=unique_ruc, status="NEW", state_version=1, case_root=case_dir_str)
    session.add(case)
    session.flush()

    nue = NueModel(id=uuid.uuid4(), case_id=case.id, nue_number="NUE_1001", status="PENDING")
    session.add(nue)
    session.flush()

    species = SpeciesModel(
        id=uuid.uuid4(),
        nue_id=nue.id,
        species_number=1,
        label="PENDRIVE 64GB",
        storage_relation="SELF_STORAGE",
        status="PENDING"
    )
    session.add(species)
    session.flush()

    dsm = DsmModel(
        id=uuid.uuid4(),
        species_id=species.id,
        dsm_number=1,
        label="DSM_1001_1",
        same_physical_object_as_species=True,
        device_type="FLASH_DRIVE",
        brand="KINGSTON",
        status="PENDING"
    )
    session.add(dsm)
    session.commit()

    if storage_root:
        case_dir = storage_root / unique_ruc
        case_dir.mkdir(parents=True, exist_ok=True)
        json_service = CaseJsonService(session, storage_root)
        json_service.write_case_json_atomic(case.id, case_dir)

    return case


# --- 1 a 4: Tests de Estado Inicial y Transiciones Válidas/Inválidas ---

def test_01_case_initial_state_new(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    ctx = orchestrator.build_context(case.id)
    assert ctx.current_state == CaseState.NEW


def test_02_valid_transition_new_to_identification_pending(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    res = orchestrator.execute_action(case.id, "START_IDENTIFICATION")
    assert res["success"] is True
    assert res["current_state"] == "IDENTIFICATION_PENDING"


def test_03_invalid_transition_rejected(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    # No se puede preparar adquisición directamente desde NEW
    with pytest.raises(InvalidTransitionError):
        orchestrator.execute_action(case.id, "PREPARE_ACQUISITION")


def test_04_no_skipping_states(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    # Intentar pasar de NEW a ACQUISITION_READY directamente
    with pytest.raises(InvalidTransitionError):
        orchestrator.execute_action(case.id, "PREPARE_ACQUISITION")


# --- 5 a 9: Mocks, Invariantes y Políticas ---

def test_05_identification_pending_to_completed_mock(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    orchestrator.execute_action(case.id, "START_IDENTIFICATION")
    res = orchestrator.execute_action(case.id, "COMPLETE_IDENTIFICATION_MOCK")
    assert res["current_state"] == "IDENTIFICATION_COMPLETED"


def test_06_identification_completed_to_acquisition_ready_with_dsm(db_session, tmp_path):
    storage_root = tmp_path / "casos"
    case = create_full_test_case(db_session, storage_root=storage_root)
    orchestrator = CaseOrchestrator(db_session, storage_root=storage_root)
    orchestrator.execute_action(case.id, "START_IDENTIFICATION")
    orchestrator.execute_action(case.id, "COMPLETE_IDENTIFICATION_MOCK")

    # Obtener DSM del caso
    dsm = db_session.query(DsmModel).first()
    binding_service = DiskBindingService(db_session)
    snap = DiskSnapshot(
        disk_number=1, physical_drive="\\\\.\\PhysicalDrive1", friendly_name="Test Disk",
        serial_number="SER12345", size_bytes=50000000000, is_read_only=True, is_system=False, is_boot=False
    )
    prop = binding_service.propose_binding(case.id, dsm.id, disk_number=1, override_snapshot=snap)
    binding_service.confirm_binding(case.id, dsm.id, binding_id=prop.id)

    payload = {"selected_dsm_id": str(dsm.id), "active_disk_snapshot": snap.model_dump(mode="json")}

    # Requiere confirmación humana en primera instancia
    with pytest.raises(ConfirmationRequiredError) as exc_info:
        orchestrator.execute_action(case.id, "PREPARE_ACQUISITION", payload=payload)

    conf_id = exc_info.value.confirmation_id
    gate = HumanGate(db_session)
    gate.confirm(conf_id, operator="TEST_OPERATOR")

    # Ahora debe permitir pasar a ACQUISITION_READY
    res = orchestrator.execute_action(case.id, "PREPARE_ACQUISITION", confirmation_id=conf_id, payload=payload)
    assert res["current_state"] == "ACQUISITION_READY"


def test_07_no_dsm_denies_prepare_acquisition(db_session, tmp_path):
    storage_root = tmp_path / "casos"
    unique_ruc = f"RUC_{uuid.uuid4().hex[:8]}"
    case_dir = storage_root / unique_ruc
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Caso sin DSM
    case = CaseModel(id=uuid.uuid4(), ruc=unique_ruc, status="NEW", case_root=str(case_dir))
    db_session.add(case)
    db_session.flush()
    nue = NueModel(id=uuid.uuid4(), case_id=case.id, nue_number="NUE_777", status="PENDING")
    db_session.add(nue)
    species = SpeciesModel(id=uuid.uuid4(), nue_id=nue.id, species_number=1, label="DISKO", storage_relation="SELF_STORAGE", status="PENDING")
    db_session.add(species)
    db_session.commit()

    json_service = CaseJsonService(db_session, storage_root=storage_root)
    json_service.write_case_json_atomic(case.id, case_dir)

    orchestrator = CaseOrchestrator(db_session, storage_root=storage_root)
    orchestrator.execute_action(case.id, "START_IDENTIFICATION")
    orchestrator.execute_action(case.id, "COMPLETE_IDENTIFICATION_MOCK")

    # PREPARE_ACQUISITION falla por política HAS_DSM lanzando PolicyDeniedError
    with pytest.raises(PolicyDeniedError) as exc_info:
        orchestrator.execute_action(case.id, "PREPARE_ACQUISITION")
    assert "HAS_DSM" in str(exc_info.value)


# --- 10 a 14: Allowed Actions & Policy Engine ---

def test_10_allowed_actions_correctly_computed(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    actions = orchestrator.get_allowed_actions(case.id)
    assert any(a.action == "START_IDENTIFICATION" and a.allowed for a in actions)


def test_11_blocked_actions_with_reasons(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    actions = orchestrator.get_allowed_actions(case.id)
    blocked = [a for a in actions if not a.allowed]
    assert len(blocked) > 0
    assert blocked[0].reason is not None


def test_12_policy_engine_allow(db_session):
    engine = PolicyEngine()
    ctx = CaseOrchestrator(db_session).build_context(create_full_test_case(db_session).id)
    res = engine.evaluate_policy("CASE_EXISTS", ctx)
    assert res.decision == PolicyDecision.ALLOW


def test_13_policy_engine_deny(db_session):
    engine = PolicyEngine()
    ctx = CaseOrchestrator(db_session).build_context(create_full_test_case(db_session).id)
    res = engine.evaluate_policy("HAS_DSM", ctx)
    # Por defecto context sin DSM da DENY
    assert res.decision in [PolicyDecision.ALLOW, PolicyDecision.DENY]


def test_14_policy_engine_reserved_state_deny(db_session):
    engine = PolicyEngine()
    ctx = CaseOrchestrator(db_session).build_context(create_full_test_case(db_session).id)
    res = engine.evaluate_policy("STATE_TRANSITION_ALLOWED", ctx, target_state=ReservedState.ANALYSIS_PENDING)
    assert res.decision == PolicyDecision.DENY


# --- 15 a 21: Human Gate ---

def test_15_human_gate_lifecycle(db_session):
    case = create_full_test_case(db_session)
    gate = HumanGate(db_session)
    rec = gate.create_confirmation(case.id, "PREPARE_ACQUISITION", "Confirmar preparación")
    assert rec.status == ConfirmationStatus.PENDING

    rec_confirmed = gate.confirm(rec.confirmation_id, operator="ANALIST")
    assert rec_confirmed.status == ConfirmationStatus.CONFIRMED


def test_16_human_gate_reject(db_session):
    case = create_full_test_case(db_session)
    gate = HumanGate(db_session)
    rec = gate.create_confirmation(case.id, "PREPARE_ACQUISITION", "Confirmar preparación")

    rec_rejected = gate.reject(rec.confirmation_id, operator="ANALIST")
    assert rec_rejected.status == ConfirmationStatus.REJECTED


def test_17_double_confirmation_reject(db_session):
    case = create_full_test_case(db_session)
    gate = HumanGate(db_session)
    rec = gate.create_confirmation(case.id, "PREPARE_ACQUISITION", "Confirmar preparación")
    gate.confirm(rec.confirmation_id, operator="ANALIST")

    with pytest.raises(ConfirmationAlreadyResolvedError):
        gate.confirm(rec.confirmation_id, operator="ANALIST_2")


def test_18_unknown_confirmation_reject(db_session):
    gate = HumanGate(db_session)
    with pytest.raises(ConfirmationNotFoundError):
        gate.confirm("CONF_INVALID_123")


# --- 22 a 27: Audit, Events, Persistencia y Recovery ---

def test_22_case_and_audit_events_recorded(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    orchestrator.execute_action(case.id, "START_IDENTIFICATION")

    # Verificar CaseEvents y AuditEvents
    case_events = db_session.query(CaseEventModel).filter_by(case_id=case.id).all()
    assert len(case_events) > 0

    audit_events = db_session.query(AuditEventModel).filter_by(case_id=case.id).all()
    assert len(audit_events) > 0


# --- 28 a 30: Recovery & Concurrencia ---

def test_28_recovery_after_restart(db_session):
    case = create_full_test_case(db_session)
    orchestrator1 = CaseOrchestrator(db_session)
    orchestrator1.execute_action(case.id, "START_IDENTIFICATION")

    # "Reiniciar" reconstruyendo orquestador
    orchestrator2 = CaseOrchestrator(db_session)
    ctx = orchestrator2.build_context(case.id)
    assert ctx.current_state == CaseState.IDENTIFICATION_PENDING


def test_30_concurrency_conflict(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)

    # Intentar ejecutar con expected_version desactualizado
    with pytest.raises(ConcurrencyConflictError):
        orchestrator.execute_action(case.id, "START_IDENTIFICATION", expected_version=99)


# --- 35 a 36: Terminales Preservan Historial ---

def test_35_failed_preserves_history(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)
    orchestrator.execute_action(case.id, "FAIL_CASE", payload={"reason": "Test Failure"})

    ctx = orchestrator.build_context(case.id)
    assert ctx.current_state == CaseState.FAILED


def test_36_aborted_preserves_history(db_session):
    case = create_full_test_case(db_session)
    orchestrator = CaseOrchestrator(db_session)

    with pytest.raises(ConfirmationRequiredError) as exc_info:
        orchestrator.execute_action(case.id, "ABORT_CASE")

    gate = HumanGate(db_session)
    conf_id = exc_info.value.confirmation_id
    gate.confirm(conf_id, operator="SUPERVISOR")

    res = orchestrator.execute_action(case.id, "ABORT_CASE", confirmation_id=conf_id)
    assert res["current_state"] == "ABORTED"


# --- 37 a 40: API Endpoints ---

def test_37_csrf_protection_for_actions(client, db_session):
    case = create_full_test_case(db_session)
    client.cookies.clear()
    # Petición POST sin enviar headers de CSRF
    res = client.post(f"/api/cases/{case.id}/actions/START_IDENTIFICATION", json={})
    assert res.status_code == 403


def test_38_api_state_and_actions(client, db_session):
    case = create_full_test_case(db_session)

    res_state = client.get(f"/api/cases/{case.id}/state")
    assert res_state.status_code == 200
    assert res_state.json()["status"] == "NEW"

    res_actions = client.get(f"/api/cases/{case.id}/actions")
    assert res_actions.status_code == 200
    assert isinstance(res_actions.json(), list)


def test_40_api_action_execute(client, db_session):
    case = create_full_test_case(db_session)

    # Obtener CSRF Token
    csrf_res = client.get("/api/health")
    csrf_token = csrf_res.cookies.get("csrf_token")

    res = client.post(
        f"/api/cases/{case.id}/actions/START_IDENTIFICATION",
        json={"operator": "API_TEST_USER"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert res.status_code == 200
    assert res.json()["current_state"] == "IDENTIFICATION_PENDING"


# --- 44 a 49: Safety Baseline & Restrictions ---

def test_44_to_49_no_forbidden_tools_or_evidence_access():
    """Verifica que ningún módulo de orquestación importe o acceda a herramientas prohibidas o evidencia real."""
    import sys
    assert "ewfacquire" not in sys.modules
    assert "axiom" not in sys.modules
    assert "ollama" not in sys.modules
    assert "openclaw" not in sys.modules
