"""
Proceso Runner para la ejecución durable de ewfacquire mediante subprocess.Popen (shell=False).
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from agente_forense.acquisition.models import AcquisitionJobStatus, AcquisitionJob
from agente_forense.acquisition.output_parser import EwfOutputParser
from agente_forense.acquisition.artifacts import AcquisitionArtifactsManager
from agente_forense.acquisition.errors import UnexpectedSegmentationError, AcquisitionRunnerError


class EwfAcquireRunner:
    """
    Ejecuta ewfacquire con subprocess.Popen(shell=False).
    Redirige stdout/stderr a archivos.
    Mantiene independencia del proceso HTTP/servidor.
    """

    @staticmethod
    def start_process(
        command: List[str],
        stdout_path: str,
        stderr_path: str,
        cwd: Optional[str] = None
    ) -> Tuple[int, subprocess.Popen]:
        """
        Lanza el subproceso con Popen, shell=False y archivos de salida abiertos.
        """
        stdout_p = Path(stdout_path)
        stderr_p = Path(stderr_path)

        stdout_p.parent.mkdir(parents=True, exist_ok=True)
        stderr_p.parent.mkdir(parents=True, exist_ok=True)

        stdout_file = open(stdout_p, "a", encoding="utf-8")
        stderr_file = open(stderr_p, "a", encoding="utf-8")

        try:
            process = subprocess.Popen(
                command,
                shell=False,
                stdout=stdout_file,
                stderr=stderr_file,
                stdin=subprocess.DEVNULL,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            return process.pid, process
        except Exception as e:
            stdout_file.close()
            stderr_file.close()
            raise AcquisitionRunnerError(f"No se pudo iniciar el proceso runner: {e}")

    @staticmethod
    def inspect_output_artifacts(
        target_directory: str,
        target_basename: str
    ) -> Tuple[List[str], int, Optional[str]]:
        """
        Inspecciona el directorio de destino para verificar segmentos E01.
        Sintaxis de regla R08.1:
        - Exactamente un archivo .E01
        - No .E02, .E03, etc. Si aparecen -> UNEXPECTED_SEGMENTATION.
        """
        target_dir = Path(target_directory)
        if not target_dir.exists():
            return [], 0, "MISSING_DESTINATION_DIR"

        e01_files = sorted([f.name for f in target_dir.glob(f"{target_basename}.E*") if f.suffix.upper() == ".E01"])
        unexpected_segments = sorted([f.name for f in target_dir.glob(f"{target_basename}.E*") if f.suffix.upper() not in [".E01", ".JSON", ".LOG"]])

        all_e_segments = sorted([f.name for f in target_dir.glob(f"{target_basename}.E*")])
        segment_count = len([f for f in all_e_segments if re_segment_match(f)])

        if unexpected_segments or segment_count > 1:
            return all_e_segments, segment_count, "UNEXPECTED_SEGMENTATION"

        if not e01_files:
            return [], 0, "MISSING_E01_FILE"

        e01_path = target_dir / e01_files[0]
        if e01_path.stat().st_size == 0:
            return e01_files, 1, "ZERO_BYTE_E01"

        return e01_files, 1, None


def re_segment_match(filename: str) -> bool:
    import re
    return bool(re.search(r"\.E\d+$", filename, re.IGNORECASE))
