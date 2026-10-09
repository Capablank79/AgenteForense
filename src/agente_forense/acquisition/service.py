"""
Servicio unificado de orquestación de la adquisición E01 (Sprint R08.1).
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from agente_forense.acquisition.capabilities import EwfBinaryVerifier
from agente_forense.acquisition.command_builder import EwfAcquireCommandBuilder
from agente_forense.acquisition.preflight import verify_execution_privileges, revalidate_source_disk
from agente_forense.acquisition.destination import DestinationValidator
from agente_forense.acquisition.jobs import AcquisitionJobManager
from agente_forense.acquisition.models import HumanGatePayload, PreflightSummary, AcquisitionJobStatus
from agente_forense.acquisition.errors import HumanGateAbortedError
from agente_forense.persistence.models import CaseModel, DsmModel, AcquisitionJobModel, AuditEventModel
from agente_forense.storage.case_json import CaseJsonService


class AcquisitionService:
    """
    Coordina el flujo de adquisición E01:
    1. Check Capabilities & Binary verifier.
    2. Revalidate Source (R07.1).
    3. Validate Destination & Disk space.
    4. Build CLI Command.
    5. Human Gate exact "ADQUIRIR".
    6. Persistent Job creation & process execution.
    """

    def __init__(self, db_session: Session, case_root_base: str):
        self.session = db_session
        self.case_root_base = case_root_base
        self.binary_verifier = EwfBinaryVerifier()
        self.command_builder = EwfAcquireCommandBuilder()
        self.destination_validator = DestinationValidator()
        self.job_manager = AcquisitionJobManager(db_session, case_root_base)

    def prepare_acquisition(
        self,
        case_id: str,
        dsm_id: str,
        binding_id: str,
        destination_directory: str,
        current_system_disks: list,
        expected_binding_dict: Dict[str, Any],
        operator: Optional[str] = None
    ) -> HumanGatePayload:
        # 1. Verificador del binario
        caps = self.binary_verifier.verify()

        # 2. Privilegios de Administrador
        verify_execution_privileges()

        # 3. Revalidar origen
        source_disk_dict = revalidate_source_disk(expected_binding_dict, current_system_disks)

        # 4. Obtener jerarquía del caso desde DB
        case_rec = self.session.query(CaseModel).filter_by(id=case_id).first()
        if not case_rec:
            raise ValueError(f"Caso {case_id} no encontrado.")

        dsm_rec = self.session.query(DsmModel).filter_by(id=dsm_id).first()
        if not dsm_rec:
            raise ValueError(f"DSM {dsm_id} no encontrado.")

        species_rec = dsm_rec.species
        nue_rec = species_rec.nue

        # Nombre oficial del target: NUE_<NUE>_ESPECIE<n>_DSM<m>
        target_basename = f"NUE_{nue_rec.nue_number}_ESPECIE{species_rec.species_number}_DSM{dsm_rec.dsm_number}"

        # Estructura jerárquica de destino: ADQUISICION\NUE_<NUE>\NUE_<NUE>_ESPECIE<n>\NUE_<NUE>_ESPECIE<n>_DSM<m>\
        full_dest_dir = Path(destination_directory) / "ADQUISICION" / f"NUE_{nue_rec.nue_number}" / f"NUE_{nue_rec.nue_number}_ESPECIE{species_rec.species_number}" / target_basename
        full_dest_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = full_dest_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # 5. Validar destino
        dest_info = self.destination_validator.validate(
            destination_directory=str(full_dest_dir),
            target_basename=target_basename,
            source_size_bytes=source_disk_dict["size_bytes"],
            source_physical_drive=source_disk_dict["physical_drive"]
        )

        # 6. Build command
        native_log_path = str(logs_dir / "ewfacquire_native.log")
        command = self.command_builder.build_command(
            source_physical_drive=source_disk_dict["physical_drive"],
            target_basename_no_ext=target_basename,
            case_number=case_rec.ruc,
            evidence_number=nue_rec.nue_number,
            examiner=operator or "AgenteForense",
            description=dsm_rec.label,
            notes=f"E01 Single File Acquisition for DSM {dsm_rec.dsm_number}",
            compression="best",
            format_type="encase6",
            digest="sha256",
            segment_size="0",
            native_log_path=native_log_path
        )

        # Crear job persistente
        job_id = f"JOB-ACQ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        stdout_path = str(logs_dir / "stdout.log")
        stderr_path = str(logs_dir / "stderr.log")

        job_rec = self.job_manager.create_job(
            job_id=job_id,
            case_id=case_id,
            dsm_id=dsm_id,
            binding_id=binding_id,
            command=command,
            target_directory=str(full_dest_dir),
            target_basename=target_basename,
            expected_e01_path=dest_info["expected_e01_path"],
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            native_log_path=native_log_path,
            operator=operator
        )

        preflight = PreflightSummary(
            case_id=str(case_rec.id),
            ruc=case_rec.ruc or "",
            nue_number=nue_rec.nue_number,
            species_number=species_rec.species_number,
            dsm_number=dsm_rec.dsm_number,
            dsm_id=str(dsm_rec.id),
            binding_id=binding_id,
            source_physical_drive=source_disk_dict["physical_drive"],
            source_disk_number=source_disk_dict.get("disk_number", 0),
            source_serial=source_disk_dict.get("serial_number"),
            source_size_bytes=source_disk_dict["size_bytes"],
            is_read_only=source_disk_dict["is_read_only"],
            is_system=source_disk_dict["is_system"],
            is_boot=source_disk_dict["is_boot"],
            destination_directory=str(full_dest_dir),
            destination_physical_drive=dest_info.get("destination_physical_drive"),
            destination_filesystem=dest_info.get("filesystem", "NTFS"),
            destination_free_bytes=dest_info["free_bytes"],
            target_basename=target_basename,
            expected_e01_path=dest_info["expected_e01_path"],
            binary_sha256=caps.sha256,
            binary_version=caps.version,
            format="encase6",
            compression="best",
            segment_size="0",
            digest="sha256"
        )

        prompt_text = (
            f"CONFIRMACIÓN REQUERIDA DE ADQUISICIÓN E01:\n"
            f"Caso: {preflight.ruc} | NUE: {preflight.nue_number} | DSM: {preflight.dsm_number}\n"
            f"Origen: {preflight.source_physical_drive} ({preflight.source_size_bytes} bytes)\n"
            f"Destino: {preflight.expected_e01_path}\n"
            f"Binario: {caps.path} (SHA256: {caps.sha256[:12]}...)\n"
            f"Escriba exactamente 'ADQUIRIR' para proceder."
        )

        return HumanGatePayload(
            preflight=preflight,
            prompt_text=prompt_text,
            required_confirmation="ADQUIRIR"
        )
