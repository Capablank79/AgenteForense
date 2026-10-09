"""
Generación atómica de acquisition.json y actualización de case.json.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import UUID
from agente_forense.storage.case_json import CaseJsonService

SCHEMA_VERSION = "1.0.0"


def atomic_write_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Escribe un archivo JSON de forma atómica mediante archivo temporal y reemplazo en el mismo volumen."""
    file_path = Path(file_path).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    temp_fd, temp_path_str = tempfile.mkstemp(dir=file_path.parent, prefix=".tmp_json_")
    temp_path = Path(temp_path_str)

    try:
        with open(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise e


class AcquisitionArtifactsManager:
    """Gestiona la estructura de salida de adquisición y la creación de acquisition.json."""

    @staticmethod
    def build_acquisition_json_data(
        job_data: Dict[str, Any],
        preflight_data: Dict[str, Any],
        parsed_output: Dict[str, Any],
        generated_files: List[str],
        generated_segment_count: int,
        status: str,
        errors: List[str] = None
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "schema_version": SCHEMA_VERSION,
            "case_id": preflight_data.get("case_id"),
            "ruc": preflight_data.get("ruc"),
            "nue": preflight_data.get("nue_number"),
            "species": preflight_data.get("species_number"),
            "dsm": preflight_data.get("dsm_number"),
            "binding_id": preflight_data.get("binding_id"),
            "source_snapshot": {
                "physical_drive": preflight_data.get("source_physical_drive"),
                "serial_number": preflight_data.get("source_serial"),
                "size_bytes": preflight_data.get("source_size_bytes")
            },
            "destination": preflight_data.get("destination_directory"),
            "ewfacquire": {
                "path": job_data.get("binary_path"),
                "sha256": preflight_data.get("binary_sha256"),
                "version": preflight_data.get("binary_version")
            },
            "command": job_data.get("command"),
            "format": preflight_data.get("format", "encase6"),
            "compression": preflight_data.get("compression", "best"),
            "hashes_requested": ["md5", "sha256"],
            "segment_strategy": "single_file",
            "human_confirmation": {
                "exact": job_data.get("human_confirmation_exact"),
                "operator": job_data.get("operator"),
                "confirmed_at": job_data.get("human_confirmed_at")
            },
            "job_id": job_data.get("job_id"),
            "pid": job_data.get("pid"),
            "started_at": job_data.get("started_at"),
            "finished_at": job_data.get("finished_at") or now_iso,
            "exit_code": job_data.get("exit_code"),
            "generated_files": generated_files,
            "generated_segment_count": generated_segment_count,
            "reported_hashes": {
                "md5": parsed_output.get("md5"),
                "sha256": parsed_output.get("sha256")
            },
            "status": status,
            "errors": errors or [],
            "tool_versions": {
                "ewfacquire": preflight_data.get("binary_version"),
                "agente_forense": "1.0.0"
            }
        }

    @staticmethod
    def create_acquisition_json(
        output_dir: Path,
        json_data: Dict[str, Any]
    ) -> Path:
        target_path = output_dir / "acquisition.json"
        atomic_write_json(target_path, json_data)
        return target_path

    def update_case_json_acquisition(self, session, case_id_str: str, dsm_id_str: str, acquisition_data: Dict[str, Any], storage_root: str):
        case_json_svc = CaseJsonService(session, storage_root=Path(storage_root))
        case_json_svc.generate_and_save_case_json(UUID(case_id_str))
