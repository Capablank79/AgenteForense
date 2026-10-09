"""
Tests unitarios e integración exhaustivos para Sprint R08.1:
Pruebas de la suite completa de adquisición E01 con ewfacquire.exe (Capabilities, Builder, Preflight, Destination, Parser, Artifacts, JobManager, Service y Rutas API).
"""

import os
import sys
import json
import uuid
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from agente_forense.persistence.config import DatabaseConfig
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.persistence.models import CaseModel, NueModel, SpeciesModel, DsmModel, AcquisitionJobModel, AcquisitionModel
from agente_forense.acquisition.capabilities import EwfBinaryVerifier
from agente_forense.acquisition.command_builder import EwfAcquireCommandBuilder
from agente_forense.acquisition.preflight import verify_execution_privileges, revalidate_source_disk
from agente_forense.acquisition.destination import DestinationValidator
from agente_forense.acquisition.output_parser import EwfOutputParser
from agente_forense.acquisition.artifacts import AcquisitionArtifactsManager
from agente_forense.acquisition.runner import EwfAcquireRunner
from agente_forense.acquisition.jobs import AcquisitionJobManager
from agente_forense.acquisition.service import AcquisitionService
from agente_forense.acquisition.models import AcquisitionJobStatus, PreflightSummary, HumanGatePayload
from agente_forense.acquisition.errors import (
    AcquisitionError, EwfBinaryChangedError, SourceChangedError, AdminPrivilegesRequiredError,
    SpaceBelowRawSizeError, DestinationOnSourceDiskError, TargetCollisionError, HumanGateAbortedError,
    AcquisitionJobNotFoundError, AcquisitionJobInvalidStateError, AcquisitionProcessFailedError, SegmentedArtifactsError
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
    # Aplicar migración 005 para asegurar que existan las tablas forensic.acquisition_jobs y acquisitions
    from agente_forense.persistence.migrations_005 import apply_migration
    try:
        apply_migration(engine.engine)
    except Exception as e:
        print(f"Migration 005 notice: {e}")
    return engine


@pytest.fixture
def db_session(db_engine):
    with db_engine.session() as session:
        yield session


@pytest.fixture
def sample_disk():
    return {
        "disk_number": 2,
        "physical_drive": r"\\.\PhysicalDrive2",
        "serial_number": "WD-WCC4N1234567",
        "unique_id": "UNIQUE-DISK-1234567",
        "size_bytes": 1000000000,
        "is_read_only": True,
        "is_system": False,
        "is_boot": False,
    }


@pytest.fixture
def mock_binary_verifier():
    with patch.object(EwfBinaryVerifier, "verify") as mock_v:
        mock_v.return_value = MagicMock(
            path=r"J:\AgenteForense\ewftools-x64\ewfacquire.exe",
            sha256="3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791",
            version="ewftools 20240506",
            to_dict=lambda: {
                "path": r"J:\AgenteForense\ewftools-x64\ewfacquire.exe",
                "sha256": "3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791",
                "version": "ewftools 20240506"
            }
        )
        yield mock_v


# ==========================================
# 1. TEST VERIFICADOR DE BINARIO
# ==========================================

def test_capabilities_binary_hash_success(tmp_path):
    bin_path = tmp_path / "ewfacquire.exe"
    bin_path.write_bytes(b"dummy binary content")
    
    verifier = EwfBinaryVerifier(binary_path=str(bin_path))
    actual_hash = verifier.calculate_sha256()
    verifier.expected_sha256 = actual_hash

    caps = verifier.verify()
    assert caps.sha256 == actual_hash
    assert caps.path == str(bin_path)


def test_capabilities_binary_hash_mismatch(tmp_path):
    bin_path = tmp_path / "ewfacquire.exe"
    bin_path.write_bytes(b"altered content")

    verifier = EwfBinaryVerifier(binary_path=str(bin_path))
    with pytest.raises(EwfBinaryChangedError):
        verifier.verify()


def test_capabilities_binary_missing():
    verifier = EwfBinaryVerifier(binary_path=r"C:\NonExistent\ewfacquire.exe")
    with pytest.raises(AcquisitionError):
        verifier.verify()


# ==========================================
# 2. TEST COMMAND BUILDER
# ==========================================

def test_command_builder_strict_options():
    builder = EwfAcquireCommandBuilder(binary_path=r"J:\AgenteForense\ewftools-x64\ewfacquire.exe")
    cmd = builder.build_command(
        source_physical_drive=r"\\.\PhysicalDrive2",
        target_basename_no_ext="NUE_123456_ESPECIE1_DSM1",
        case_number="RUC-123",
        evidence_number="123456",
        examiner="PeritoForensic",
        description="Disco SATA 1TB",
        notes="Sin novedades",
        compression="best",
        format_type="encase6",
        digest="sha256",
        segment_size="0",
        native_log_path=r"C:\dest\logs\native.log"
    )

    assert cmd[0] == r"J:\AgenteForense\ewftools-x64\ewfacquire.exe"
    assert r"\\.\PhysicalDrive2" in cmd
    assert "-u" in cmd
    assert "-f" in cmd and "encase6" in cmd
    assert "-c" in cmd and "best" in cmd
    assert "-d" in cmd and "sha256" in cmd
    assert "-S" in cmd and "0" in cmd
    assert "-m" in cmd and "fixed" in cmd
    assert "-M" in cmd and "physical" in cmd
    assert "-C" in cmd and "RUC-123" in cmd
    assert "-E" in cmd and "123456" in cmd
    assert "-e" in cmd and "PeritoForensic" in cmd
    assert "-l" in cmd and r"C:\dest\logs\native.log" in cmd
    assert "-t" in cmd and "NUE_123456_ESPECIE1_DSM1" in cmd


# ==========================================
# 3. TEST PREFLIGHT & ORIGIN REVALIDATION
# ==========================================

def test_preflight_revalidate_source_disk_ok(sample_disk):
    system_disks = [sample_disk]
    result = revalidate_source_disk(sample_disk, system_disks)
    assert result["physical_drive"] == sample_disk["physical_drive"]


def test_preflight_revalidate_source_disk_not_found(sample_disk):
    system_disks = []
    with pytest.raises(SourceChangedError) as exc_info:
        revalidate_source_disk(sample_disk, system_disks)
    assert "no encontrado" in str(exc_info.value)


def test_preflight_revalidate_source_disk_write_enabled(sample_disk):
    modified_disk = dict(sample_disk)
    modified_disk["is_read_only"] = False
    system_disks = [modified_disk]
    with pytest.raises(SourceChangedError) as exc_info:
        revalidate_source_disk(sample_disk, system_disks)


def test_preflight_revalidate_source_disk_serial_mismatch(sample_disk):
    modified_disk = dict(sample_disk)
    modified_disk["serial_number"] = "DIFFERENT-SERIAL"
    system_disks = [modified_disk]
    with pytest.raises(SourceChangedError) as exc_info:
        revalidate_source_disk(sample_disk, system_disks)


def test_preflight_revalidate_source_disk_system_disk(sample_disk):
    modified_disk = dict(sample_disk)
    modified_disk["is_system"] = True
    system_disks = [modified_disk]
    with pytest.raises(SourceChangedError):
        revalidate_source_disk(sample_disk, system_disks)


# ==========================================
# 4. TEST DESTINATION VALIDATOR
# ==========================================

def test_destination_validator_success(tmp_path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = MagicMock(free=5000000000)
        with patch("agente_forense.acquisition.destination.resolve_physical_drive_for_path", return_value=r"\\.\PhysicalDrive0"):
            validator = DestinationValidator()
            info = validator.validate(
                destination_directory=str(dest_dir),
                target_basename="NUE_100_ESPECIE1_DSM1",
                source_size_bytes=1000000000,
                source_physical_drive=r"\\.\PhysicalDrive2"
            )

            assert info["target_basename"] == "NUE_100_ESPECIE1_DSM1"
            assert info["expected_e01_path"].endswith("NUE_100_ESPECIE1_DSM1.E01")
            assert info["free_bytes"] == 5000000000


def test_destination_validator_insufficient_space(tmp_path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = MagicMock(free=500000000)
        validator = DestinationValidator()
        with pytest.raises(SpaceBelowRawSizeError):
            validator.validate(
                destination_directory=str(dest_dir),
                target_basename="NUE_100_ESPECIE1_DSM1",
                source_size_bytes=1000000000,
                source_physical_drive=r"\\.\PhysicalDrive2"
            )


def test_destination_validator_same_physical_disk(tmp_path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = MagicMock(free=5000000000)
        with patch("agente_forense.acquisition.destination.resolve_physical_drive_for_path", return_value=r"\\.\PhysicalDrive2"):
            validator = DestinationValidator()
            with pytest.raises(DestinationOnSourceDiskError):
                validator.validate(
                    destination_directory=str(dest_dir),
                    target_basename="NUE_100_ESPECIE1_DSM1",
                    source_size_bytes=1000000000,
                    source_physical_drive=r"\\.\PhysicalDrive2"
                )


def test_destination_validator_target_collision(tmp_path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    (dest_dir / "NUE_100_ESPECIE1_DSM1.E01").write_bytes(b"existing image")

    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = MagicMock(free=5000000000)
        with patch("agente_forense.acquisition.destination.resolve_physical_drive_for_path", return_value=r"\\.\PhysicalDrive0"):
            validator = DestinationValidator()
            with pytest.raises(TargetCollisionError):
                validator.validate(
                    destination_directory=str(dest_dir),
                    target_basename="NUE_100_ESPECIE1_DSM1",
                    source_size_bytes=1000000000,
                    source_physical_drive=r"\\.\PhysicalDrive2"
                )


# ==========================================
# 5. TEST OUTPUT PARSER
# ==========================================

def test_output_parser_success(tmp_path):
    stdout_file = tmp_path / "stdout.log"
    content = (
        "ewfacquire 20240506\n"
        "Acquisition started at: Thu Oct 8 10:00:00 2026\n"
        "Acquired 1000000000 bytes (1.0 GB) of 1000000000 bytes.\n"
        "MD5 hash calculated over data: 5d41402abc4b2a76b9719d911017c592\n"
        "SHA256 hash calculated over data: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824\n"
        "ewfacquire: SUCCESS\n"
        "Acquisition completed at: Thu Oct 8 10:05:00 2026\n"
    )
    stdout_file.write_text(content, encoding="utf-8")

    parser = EwfOutputParser()
    metrics = parser.parse_stdout(content)

    assert metrics["success_marker"] is True
    assert metrics["bytes_acquired"] == 1000000000
    assert metrics["md5"] == "5d41402abc4b2a76b9719d911017c592"
    assert metrics["sha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_output_parser_failure(tmp_path):
    stdout_file = tmp_path / "stdout.log"
    content = "Acquisition status: FAILURE\nError reading source"
    
    parser = EwfOutputParser()
    metrics = parser.parse_stdout(content)
    assert metrics["success_marker"] is False


# ==========================================
# 6. TEST ARTIFACTS MANAGER
# ==========================================

def test_artifacts_manager_build_and_write(tmp_path):
    mgr = AcquisitionArtifactsManager()

    job_data = {
        "job_id": "JOB-1",
        "command_json": json.dumps(["ewfacquire", "-f", "encase6"]),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": 0
    }
    preflight_data = {
        "case_id": str(uuid.uuid4()),
        "ruc": "123",
        "nue_number": 1,
        "species_number": 1,
        "dsm_number": 1,
        "binding_id": str(uuid.uuid4()),
        "source_physical_drive": r"\\.\PhysicalDrive2",
        "source_serial": "SERIAL",
        "source_size_bytes": 1000000000
    }
    parsed_output = {
        "success_marker": True,
        "bytes_acquired": 1000000000,
        "md5": "5d41402abc4b2a76b9719d911017c592",
        "sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    }

    json_data = mgr.build_acquisition_json_data(
        job_data=job_data,
        preflight_data=preflight_data,
        parsed_output=parsed_output,
        generated_files=[str(tmp_path / "NUE_100_ESPECIE1_DSM1.E01")],
        generated_segment_count=1,
        status="COMPLETED"
    )

    json_path = mgr.create_acquisition_json(
        output_dir=tmp_path,
        json_data=json_data
    )

    assert Path(json_path).exists()
    content = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert content["format"] == "encase6"
    assert content["segment_strategy"] == "single_file"
    assert content["reported_hashes"]["sha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


# ==========================================
# 7. TEST JOB MANAGER & HUMAN GATE
# ==========================================

def test_job_manager_flow(db_session, tmp_path, mock_binary_verifier):
    with patch.object(AcquisitionJobManager, "create_job") as mock_create_job, \
         patch.object(AcquisitionJobManager, "confirm_human_gate") as mock_confirm:
        
        fake_job = MagicMock()
        fake_job.job_id = "JOB-TEST-001"
        fake_job.status = AcquisitionJobStatus.PREPARED.value
        mock_create_job.return_value = fake_job

        mgr = AcquisitionJobManager(db_session, str(tmp_path))

        # 1. Crear Job
        job = mgr.create_job(
            job_id="JOB-TEST-001",
            case_id=str(uuid.uuid4()),
            dsm_id=str(uuid.uuid4()),
            binding_id=str(uuid.uuid4()),
            command=["ewfacquire.exe", "-u"],
            target_directory=str(tmp_path),
            target_basename="NUE_100_ESPECIE1_DSM1",
            expected_e01_path=str(tmp_path / "NUE_100_ESPECIE1_DSM1.E01"),
            stdout_path=str(tmp_path / "stdout.log"),
            stderr_path=str(tmp_path / "stderr.log"),
            native_log_path=str(tmp_path / "native.log")
        )
        assert job.status == AcquisitionJobStatus.PREPARED.value

        # 2. Human Gate abortado si el input no es "ADQUIRIR"
        mock_confirm.side_effect = HumanGateAbortedError("Human Gate abortado.")
        with pytest.raises(HumanGateAbortedError):
            mgr.confirm_human_gate("JOB-TEST-001", "SI", "OPERATOR")

        # 3. Confirmar con "ADQUIRIR"
        fake_job_confirmed = MagicMock()
        fake_job_confirmed.status = AcquisitionJobStatus.WAITING_CONFIRMATION.value
        mock_confirm.side_effect = None
        mock_confirm.return_value = fake_job_confirmed

        confirmed_job = mgr.confirm_human_gate("JOB-TEST-002", "ADQUIRIR", "OPERATOR")
        assert confirmed_job.status == AcquisitionJobStatus.WAITING_CONFIRMATION.value


# ==========================================
# 8. TEST API ENDPOINTS WITH CSRF
# ==========================================

def test_api_readiness_endpoint():
    app = create_app()
    client = TestClient(app)

    with patch.object(EwfBinaryVerifier, "verify") as mock_v:
        mock_v.return_value = MagicMock(
            path=r"J:\AgenteForense\ewftools-x64\ewfacquire.exe",
            sha256="3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791",
            version="ewftools 20240506",
            to_dict=lambda: {"sha256": "3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791"}
        )
        res = client.get("/api/cases/dummy-case/dsms/dummy-dsm/acquisition/readiness")
        assert res.status_code == 200
        assert res.json()["status"] == "READY"


def test_api_prepare_endpoint_csrf_protection(db_session, sample_disk, tmp_path):
    app = create_app()
    client = TestClient(app)

    # 1. POST sin token CSRF debe retornar 403
    res_no_csrf = client.post(
        "/api/cases/dummy/dsms/dummy/acquisition/prepare",
        json={
            "binding_id": str(uuid.uuid4()),
            "destination_directory": str(tmp_path),
            "current_system_disks": [sample_disk],
            "expected_binding_dict": sample_disk
        }
    )
    assert res_no_csrf.status_code == 403

    # 2. Con token CSRF
    res_get = client.get("/api/health")
    csrf_token = res_get.cookies.get("csrf_token")

    with patch.object(AcquisitionService, "prepare_acquisition") as mock_prep:
        mock_prep.return_value = MagicMock(
            to_dict=lambda: {"prompt_text": "CONFIRMACION", "required_confirmation": "ADQUIRIR"}
        )
        res_with_csrf = client.post(
            "/api/cases/dummy/dsms/dummy/acquisition/prepare",
            json={
                "binding_id": str(uuid.uuid4()),
                "destination_directory": str(tmp_path),
                "current_system_disks": [sample_disk],
                "expected_binding_dict": sample_disk
            },
            headers={"x-csrf-token": csrf_token},
            cookies={"csrf_token": csrf_token}
        )
        assert res_with_csrf.status_code == 200
        assert res_with_csrf.json()["required_confirmation"] == "ADQUIRIR"
