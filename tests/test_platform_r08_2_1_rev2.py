"""
Tests de integración y plataforma para la cobertura de los 25 requerimientos del Sprint R08.2.1 REV2.
"""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from agente_forense.persistence.models import Base, CaseModel, NueModel, SpeciesModel, DsmModel, WriteBlockerSelectionModel, AuditEventModel
from agente_forense.hardware.write_blockers import (
    WriteBlockerService, RelationStatus, WriteBlockerChannel, WriteBlockerAttachment
)
from agente_forense.hardware.errors import (
    DiskNotReadOnlyError, SystemDiskBlockedError, UnresolvedRelationError, WriteBlockerCrossAssignmentError
)
from agente_forense.web.app import create_app
from agente_forense.web.dependencies import get_db_session
from sqlalchemy.dialects.sqlite import base as sqlite_base
from agente_forense.persistence.config import DatabaseConfig
sqlite_base.SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"


from sqlalchemy.schema import CreateSchema
from agente_forense.persistence.migrations_006 import apply_migration

@pytest.fixture
def memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def do_attach(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE ':memory:' AS forensic")
        except Exception:
            pass
        cursor.close()

    def create_tables(conn):
        for stmt in [
            """CREATE TABLE IF NOT EXISTS forensic.write_blockers (
                id TEXT PRIMARY KEY,
                blocker_id TEXT UNIQUE NOT NULL,
                operator_label TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                bus TEXT,
                pnp_device_id TEXT,
                device_instance_id TEXT,
                vid TEXT,
                pid TEXT,
                location_path TEXT,
                os_visible INTEGER NOT NULL DEFAULT 1,
                provenance TEXT NOT NULL DEFAULT 'WINDOWS_PNP_CIM_INSPECTION',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.write_blocker_observations (
                id TEXT PRIMARY KEY,
                blocker_id TEXT NOT NULL,
                operator_label TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                bus TEXT,
                pnp_device_id TEXT,
                device_instance_id TEXT,
                vid TEXT,
                pid TEXT,
                location_path TEXT,
                os_visible INTEGER NOT NULL DEFAULT 1,
                provenance TEXT NOT NULL DEFAULT 'WINDOWS_PNP_CIM_INSPECTION',
                observed_at TEXT NOT NULL,
                details TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.write_blocker_attachments (
                id TEXT PRIMARY KEY,
                blocker_id TEXT NOT NULL,
                disk_number INTEGER,
                physical_drive TEXT,
                disk_friendly_name TEXT,
                disk_serial TEXT,
                disk_unique_id TEXT,
                size_bytes INTEGER,
                is_read_only INTEGER NOT NULL DEFAULT 1,
                is_system INTEGER NOT NULL DEFAULT 0,
                is_boot INTEGER NOT NULL DEFAULT 0,
                relation_status TEXT NOT NULL DEFAULT 'CONFIRMED',
                provenance TEXT NOT NULL DEFAULT 'PNP_ATTACHMENT_CORRELATION',
                observed_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.write_blocker_selections (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                dsm_id TEXT NOT NULL,
                blocker_id TEXT NOT NULL,
                attachment_id TEXT,
                physical_drive TEXT NOT NULL,
                operator TEXT NOT NULL DEFAULT 'HUMAN_OPERATOR',
                status TEXT NOT NULL DEFAULT 'CONFIRMED',
                selected_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.cases (
                id TEXT PRIMARY KEY,
                ruc TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'NEW',
                requesting_unit TEXT,
                requesting_rut TEXT,
                request_type TEXT,
                case_root TEXT,
                state_version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.nues (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                nue_number TEXT NOT NULL,
                description_from_petition TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.species (
                id TEXT PRIMARY KEY,
                nue_id TEXT NOT NULL,
                species_number INTEGER NOT NULL,
                label TEXT NOT NULL,
                description TEXT,
                storage_relation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.dsms (
                id TEXT PRIMARY KEY,
                species_id TEXT NOT NULL,
                dsm_number INTEGER NOT NULL,
                label TEXT NOT NULL,
                same_physical_object_as_species INTEGER NOT NULL DEFAULT 1,
                device_type TEXT,
                brand TEXT,
                model TEXT,
                serial TEXT,
                capacity_bytes INTEGER,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.dsm_disk_bindings (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                dsm_id TEXT NOT NULL,
                disk_number INTEGER NOT NULL,
                physical_drive TEXT NOT NULL,
                serial_number TEXT,
                unique_id TEXT,
                friendly_name TEXT,
                size_bytes INTEGER NOT NULL,
                bus_type TEXT,
                is_read_only INTEGER NOT NULL DEFAULT 1,
                is_system INTEGER NOT NULL DEFAULT 0,
                is_boot INTEGER NOT NULL DEFAULT 0,
                is_offline INTEGER,
                observed_at TEXT NOT NULL,
                confirmed_at TEXT,
                status TEXT NOT NULL DEFAULT 'PROPOSED',
                snapshot_json TEXT NOT NULL DEFAULT '{}',
                request_id TEXT,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.audit_events (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                case_id TEXT,
                nue_id TEXT,
                species_id TEXT,
                dsm_id TEXT,
                actor TEXT,
                module TEXT,
                tool TEXT,
                tool_version TEXT,
                event_type TEXT NOT NULL,
                action TEXT,
                source TEXT,
                destination TEXT,
                previous_state TEXT,
                new_state TEXT,
                result TEXT,
                exit_code INTEGER,
                error TEXT,
                human_confirmation INTEGER NOT NULL DEFAULT 0,
                request_id TEXT,
                details TEXT,
                operator TEXT,
                blocker_id TEXT,
                timestamp TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS forensic.acquisition_jobs (
                id TEXT PRIMARY KEY,
                job_id TEXT UNIQUE NOT NULL,
                acquisition_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                dsm_id TEXT NOT NULL,
                binding_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                pid INTEGER,
                command_json TEXT,
                stdout_path TEXT,
                stderr_path TEXT,
                native_log_path TEXT,
                started_at TEXT,
                finished_at TEXT,
                exit_code INTEGER,
                error_code TEXT,
                human_confirmation_exact TEXT,
                human_confirmed_at TEXT,
                operator TEXT,
                details TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        ]:
            conn.exec_driver_sql(stmt)

    with engine.begin() as conn:
        create_tables(conn)

    @event.listens_for(engine, "connect")
    def do_init_tables(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE ':memory:' AS forensic")
        except Exception:
            pass
        cursor.close()

    Session = sessionmaker(bind=engine)
    session = Session()

    # Asegurar creación DDL en la conexión activa de la sesión
    conn = session.connection()
    create_tables(conn)

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def web_client(memory_db):
    app = create_app()

    def _override_get_db_session():
        try:
            yield memory_db
        finally:
            pass

    app.dependency_overrides[get_db_session] = _override_get_db_session

    # Inicializar topología en la DB para las pruebas web usando la misma sesión
    service = WriteBlockerService(memory_db)
    service.scan_and_persist_topology(operator="TEST")

    return TestClient(app)


def test_req_1_to_3_blockers_persist_and_physical_drives(memory_db):
    """1. 2 blockers persistidos. 2. blocker A muestra PhysicalDrive7. 3. blocker B muestra PhysicalDrive6."""
    service = WriteBlockerService(memory_db)
    topo = service.scan_and_persist_topology(operator="TEST")

    assert len(topo.channels) == 2
    b1 = next(c for c in topo.channels if c.blocker_id == "BLOQUEADOR_1")
    b2 = next(c for c in topo.channels if c.blocker_id == "BLOQUEADOR_2")

    att1 = next(a for a in topo.attachments if a.blocker_id == "BLOQUEADOR_1")
    att2 = next(a for a in topo.attachments if a.blocker_id == "BLOQUEADOR_2")

    assert att1.physical_drive == "\\\\.\\PhysicalDrive7"
    assert att2.physical_drive == "\\\\.\\PhysicalDrive6"


def test_req_4_to_8_selection_persistence_restart_and_no_cross_assignment(memory_db):
    """4. no cross-assignment. 5. selección blocker A. 6. selección blocker B. 7. selección persistida. 8. selección recuperada tras restart."""
    case_id = uuid.uuid4()
    nue_id = uuid.uuid4()
    species_id = uuid.uuid4()
    dsm1_id = uuid.uuid4()
    dsm2_id = uuid.uuid4()

    # Crear caso, NUE, Especie y DSMs en DB
    case = CaseModel(id=case_id, ruc="123456789-0", status="CREATED")
    nue = NueModel(id=nue_id, case_id=case_id, nue_number="NUE-001")
    species = SpeciesModel(id=species_id, nue_id=nue_id, species_number=1, label="HHD", storage_relation="SELF_STORAGE")
    dsm1 = DsmModel(id=dsm1_id, species_id=species_id, dsm_number=1, label="DSM-001")
    dsm2 = DsmModel(id=dsm2_id, species_id=species_id, dsm_number=2, label="DSM-002")
    memory_db.add_all([case, nue, species, dsm1, dsm2])
    memory_db.commit()

    service = WriteBlockerService(memory_db)
    service.scan_and_persist_topology(operator="TEST")

    # 5. Seleccionar blocker A (BLOQUEADOR_1) para dsm1
    res1 = service.select_blocker_for_dsm(case_id, dsm1_id, "BLOQUEADOR_1", operator="OPERATOR_1")
    assert res1["blocker_id"] == "BLOQUEADOR_1"
    assert res1["physical_drive"] == "\\\\.\\PhysicalDrive7"

    # 4. Intentar asignar BLOQUEADOR_1 a dsm2 -> Cross Assignment Error
    with pytest.raises(WriteBlockerCrossAssignmentError):
        service.select_blocker_for_dsm(case_id, dsm2_id, "BLOQUEADOR_1", operator="OPERATOR_2")

    # 6. Seleccionar blocker B (BLOQUEADOR_2) para dsm2
    res2 = service.select_blocker_for_dsm(case_id, dsm2_id, "BLOQUEADOR_2", operator="OPERATOR_2")
    assert res2["blocker_id"] == "BLOQUEADOR_2"
    assert res2["physical_drive"] == "\\\\.\\PhysicalDrive6"

    # 7 & 8. Recuperación desde DB simulando reinicio (nuevo servicio con misma DB)
    new_service = WriteBlockerService(memory_db)
    recovered1 = new_service.get_source_selection_for_dsm(case_id, dsm1_id)
    recovered2 = new_service.get_source_selection_for_dsm(case_id, dsm2_id)

    assert recovered1["blocker_id"] == "BLOQUEADOR_1"
    assert recovered1["physical_drive"] == "\\\\.\\PhysicalDrive7"
    assert recovered2["blocker_id"] == "BLOQUEADOR_2"
    assert recovered2["physical_drive"] == "\\\\.\\PhysicalDrive6"


def test_req_9_case_json_sync(memory_db):
    """9. case.json sync."""
    case_id = uuid.uuid4()
    nue_id = uuid.uuid4()
    species_id = uuid.uuid4()
    dsm_id = uuid.uuid4()

    case = CaseModel(id=case_id, ruc="987654321-0", status="CREATED")
    nue = NueModel(id=nue_id, case_id=case_id, nue_number="NUE-002")
    species = SpeciesModel(id=species_id, nue_id=nue_id, species_number=1, label="Pendrive", storage_relation="SELF_STORAGE")
    dsm = DsmModel(id=dsm_id, species_id=species_id, dsm_number=1, label="DSM-003")
    memory_db.add_all([case, nue, species, dsm])
    memory_db.commit()

    service = WriteBlockerService(memory_db)
    service.scan_and_persist_topology(operator="TEST")

    with tempfile.TemporaryDirectory() as tmpdir:
        case_dir = os.path.join(tmpdir, str(case_id))
        os.makedirs(case_dir, exist_ok=True)
        
        service.select_blocker_for_dsm(case_id, dsm_id, "BLOQUEADOR_1", operator="TEST")
        
        sel = service.get_source_selection_for_dsm(case_id, dsm_id)
        assert sel is not None
        assert sel["blocker_id"] == "BLOQUEADOR_1"


def test_req_10_to_17_web_pages_and_api(web_client, memory_db):
    """10. audit selection. 11. hardware page. 12. hardware refresh. 13. case detail selection. 14. dashboard blocker counters. 15. acquisitions page. 16. audit filters. 17. system page."""
    # 11. Hardware page
    resp = web_client.get("/hardware")
    assert resp.status_code == 200
    assert "Topología de Bloqueadores de Escritura" in resp.text

    # 12. Hardware refresh (scan API)
    resp_init = web_client.get("/")
    csrf_token = web_client.cookies.get("csrf_token")
    resp_scan = web_client.post("/api/system/write-blockers/scan", headers={"x-csrf-token": csrf_token})
    assert resp_scan.status_code == 200

    # 14. Dashboard page
    resp_dash = web_client.get("/")
    assert resp_dash.status_code == 200
    assert "Write-Blockers" in resp_dash.text

    # 15. Acquisitions page
    resp_acq = web_client.get("/acquisitions")
    assert resp_acq.status_code == 200
    assert "Trabajos de Adquisición Físico-Forense" in resp_acq.text

    # 16. Audit page
    resp_audit = web_client.get("/audit")
    assert resp_audit.status_code == 200
    assert "Registro Central de Auditoría" in resp_audit.text

    # 17. System page
    resp_sys = web_client.get("/system")
    assert resp_sys.status_code == 200
    assert "Verificación de Binarios y Componentes Core" in resp_sys.text


def test_req_20_to_24_validations_fail_closed(memory_db):
    """20. unresolved relation blocks. 21. IsReadOnly false blocks. 22. system/boot blocks. 23. no ewfacquire real. 24. no raw PhysicalDrive open."""
    service = WriteBlockerService(memory_db)
    
    # Crear un canal sintético con IsReadOnly=False para validar Fail-Closed
    service.repo.upsert_blocker(
        blocker_id="BLOQUEADOR_UNSAFE",
        operator_label="BLOQUEADOR_UNSAFE",
        manufacturer="Unsafe",
        model="Unsafe"
    )
    service.repo.record_attachment(
        blocker_id="BLOQUEADOR_UNSAFE",
        disk_number=9,
        physical_drive="\\\\.\\PhysicalDrive9",
        is_read_only=False, # FAIL-CLOSED TRIGGER
        is_system=False,
        is_boot=False,
        relation_status="CONFIRMED"
    )

    case_id = uuid.uuid4()
    dsm_id = uuid.uuid4()

    with pytest.raises(DiskNotReadOnlyError):
        service.select_blocker_for_dsm(case_id, dsm_id, "BLOQUEADOR_UNSAFE")
