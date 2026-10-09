"""
Gestor duradero de trabajos (Jobs) de adquisición E01 con soporte de persistencia y recovery.
"""

import os
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from agente_forense.acquisition.models import AcquisitionJobStatus, AcquisitionJob
from agente_forense.acquisition.runner import EwfAcquireRunner
from agente_forense.acquisition.output_parser import EwfOutputParser
from agente_forense.acquisition.artifacts import AcquisitionArtifactsManager
from agente_forense.acquisition.errors import (
    HumanGateAbortedError, ProcessMissingError, TargetCollisionError
)
from agente_forense.persistence.models import AcquisitionJobModel, AcquisitionModel, CaseModel
from agente_forense.storage.case_json import CaseJsonService


def is_process_running(pid: int) -> bool:
    """Verifica si un PID está activo en el sistema operativo."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x0010
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process == 0:
                return False
            kernel32.CloseHandle(process)
            return True
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


import sys


class AcquisitionJobManager:
    """
    Gestiona el ciclo de vida, la persistencia en PostgreSQL / case.json
    y el control de procesos para adquisición E01.
    """

    def __init__(self, db_session: Session, case_root_base: str):
        self.session = db_session
        self.case_root_base = case_root_base

    def create_job(
        self,
        job_id: str,
        case_id: str,
        dsm_id: str,
        binding_id: str,
        command: List[str],
        target_directory: str,
        target_basename: str,
        expected_e01_path: str,
        stdout_path: str,
        stderr_path: str,
        native_log_path: Optional[str] = None,
        operator: Optional[str] = None
    ) -> AcquisitionJobModel:
        job = AcquisitionJobModel(
            job_id=job_id,
            case_id=case_id,
            dsm_id=dsm_id,
            binding_id=binding_id,
            status=AcquisitionJobStatus.PREPARED.value,
            command_json=command,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            native_log_path=native_log_path,
            operator=operator,
            details={
                "target_directory": target_directory,
                "target_basename": target_basename,
                "expected_e01_path": expected_e01_path
            }
        )
        self.session.add(job)
        self.session.commit()
        return job

    def confirm_human_gate(
        self,
        job_id: str,
        confirmation_text: str,
        operator: Optional[str] = None
    ) -> AcquisitionJobModel:
        job = self.session.query(AcquisitionJobModel).filter_by(job_id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} no encontrado.")

        if confirmation_text != "ADQUIRIR":
            job.status = AcquisitionJobStatus.ABORTED.value
            job.error_code = "HUMAN_GATE_ABORTED"
            self.session.commit()
            raise HumanGateAbortedError(f"Human Gate abortado. Se requiere 'ADQUIRIR', se recibió '{confirmation_text}'.")

        job.human_confirmation_exact = "ADQUIRIR"
        job.human_confirmed_at = datetime.now(timezone.utc)
        job.status = AcquisitionJobStatus.WAITING_CONFIRMATION.value
        if operator:
            job.operator = operator
        self.session.commit()
        return job

    def start_job(self, job_id: str) -> AcquisitionJobModel:
        job = self.session.query(AcquisitionJobModel).filter_by(job_id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} no encontrado.")

        if job.status not in [AcquisitionJobStatus.WAITING_CONFIRMATION.value, AcquisitionJobStatus.PREPARED.value]:
            raise ValueError(f"No se puede iniciar job en estado {job.status}.")

        job.status = AcquisitionJobStatus.STARTING.value
        job.started_at = datetime.now(timezone.utc)
        self.session.commit()

        # Iniciar subproceso
        pid, process = EwfAcquireRunner.start_process(
            command=job.command_json,
            stdout_path=job.stdout_path,
            stderr_path=job.stderr_path,
            cwd=job.details.get("target_directory")
        )

        job.pid = pid
        job.status = AcquisitionJobStatus.RUNNING.value
        self.session.commit()
        return job

    def cancel_job(self, job_id: str) -> AcquisitionJobModel:
        job = self.session.query(AcquisitionJobModel).filter_by(job_id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} no encontrado.")

        if job.pid and is_process_running(job.pid):
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(job.pid)], capture_output=True)
                else:
                    os.kill(job.pid, signal.SIGTERM)
            except Exception:
                pass

        job.status = AcquisitionJobStatus.ABORTED.value
        job.finished_at = datetime.now(timezone.utc)
        job.error_code = "USER_CANCELLED"
        self.session.commit()
        return job

    def poll_job(self, job_id: str, preflight_info: Dict[str, Any] = None) -> Dict[str, Any]:
        job = self.session.query(AcquisitionJobModel).filter_by(job_id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} no encontrado.")

        stdout_content = ""
        if os.path.exists(job.stdout_path):
            try:
                with open(job.stdout_path, "r", encoding="utf-8", errors="replace") as f:
                    stdout_content = f.read()
            except Exception:
                pass

        parsed = EwfOutputParser.parse_stdout(stdout_content)

        # Si estaba RUNNING y el proceso ya terminó
        if job.status == AcquisitionJobStatus.RUNNING.value and job.pid:
            if not is_process_running(job.pid):
                # Proceso finalizado
                job.finished_at = datetime.now(timezone.utc)
                
                # Inspeccionar artefactos
                target_dir = job.details.get("target_directory")
                target_base = job.details.get("target_basename")
                
                gen_files, seg_count, err_code = EwfAcquireRunner.inspect_output_artifacts(target_dir, target_base)
                
                if err_code == "UNEXPECTED_SEGMENTATION":
                    job.status = AcquisitionJobStatus.FAILED.value
                    job.error_code = "UNEXPECTED_SEGMENTATION"
                    job.exit_code = 1
                elif err_code:
                    job.status = AcquisitionJobStatus.FAILED.value
                    job.error_code = err_code
                    job.exit_code = 1
                else:
                    job.status = AcquisitionJobStatus.COMPLETED.value
                    job.exit_code = 0

                self.session.commit()

                # Generar acquisition.json si preflight_info está presente
                if preflight_info and target_dir:
                    job_data = {
                        "job_id": job.job_id,
                        "binary_path": job.command_json[0] if job.command_json else "",
                        "command": job.command_json,
                        "human_confirmation_exact": job.human_confirmation_exact,
                        "operator": job.operator,
                        "human_confirmed_at": job.human_confirmed_at.isoformat() if job.human_confirmed_at else None,
                        "pid": job.pid,
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                        "exit_code": job.exit_code
                    }
                    acq_json_data = AcquisitionArtifactsManager.build_acquisition_json_data(
                        job_data=job_data,
                        preflight_data=preflight_info,
                        parsed_output=parsed,
                        generated_files=gen_files,
                        generated_segment_count=seg_count,
                        status=job.status,
                        errors=[job.error_code] if job.error_code else []
                    )
                    AcquisitionArtifactsManager.create_acquisition_json(Path(target_dir), acq_json_data)

                    # Reconciliar case.json
                    try:
                        case_json_svc = CaseJsonService(self.session, storage_root=Path(self.case_root_base))
                        case_json_svc.generate_and_save_case_json(UUID(job.case_id))
                    except Exception as e:
                        pass

        elapsed_sec = None
        if job.started_at:
            end_t = job.finished_at or datetime.now(timezone.utc)
            elapsed_sec = (end_t - job.started_at).total_seconds()

        return {
            "job_id": job.job_id,
            "status": job.status,
            "pid": job.pid,
            "elapsed_seconds": elapsed_sec,
            "exit_code": job.exit_code,
            "error_code": job.error_code,
            "parsed_output": parsed,
            "stdout_tail": stdout_content[-2000:] if stdout_content else ""
        }

    def recover_jobs() -> List[Dict[str, Any]]:
        """Reconcilia los trabajos que estaban en estado RUNNING tras un reinicio del sistema."""
        running_jobs = self.session.query(AcquisitionJobModel).filter_by(status=AcquisitionJobStatus.RUNNING.value).all()
        recovered = []
        for job in running_jobs:
            if job.pid and not is_process_running(job.pid):
                job.status = AcquisitionJobStatus.PROCESS_MISSING_REVIEW_REQUIRED.value
                job.error_code = "PROCESS_MISSING_REVIEW_REQUIRED"
                job.updated_at = datetime.now(timezone.utc)
                recovered.append({"job_id": job.job_id, "status": job.status})
        self.session.commit()
        return recovered
