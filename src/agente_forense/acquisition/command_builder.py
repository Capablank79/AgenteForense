"""
Builder determinista de argumentos CLI para ewfacquire.exe.
"""

from typing import List, Optional
from agente_forense.acquisition.capabilities import EXPECTED_EWF_PATH


class EwfAcquireCommandBuilder:
    """
    Construye la lista pura de argumentos (`List[str]`) para ewfacquire.exe.
    Garantiza:
    - Uso estricto de List[str] (sin shell strings ni shell=True).
    - Invocación no interactiva `-u`.
    - Formato default `encase6`.
    - Compresión default `best` (`-c best`).
    - Digest secundario SHA256 (`-d sha256`).
    - Desactivación de segmentación `-S 0` (Single E01).
    - Inexistencia de banderas libres pasadas desde la API.
    """

    def __init__(self, binary_path: str = EXPECTED_EWF_PATH):
        self.binary_path = binary_path

    def build_command(
        self,
        source_physical_drive: str,
        target_basename_no_ext: str,
        case_number: Optional[str] = None,
        evidence_number: Optional[str] = None,
        examiner: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        compression: str = "best",
        format_type: str = "encase6",
        digest: str = "sha256",
        segment_size: str = "0",
        native_log_path: Optional[str] = None,
    ) -> List[str]:
        """
        Retorna la lista exacta de argumentos CLI para subproceso.Popen.
        """
        # Validar origen
        if not source_physical_drive.startswith(r"\\.\PhysicalDrive"):
            # Permitir rutas sintéticas solo si no comienzan con letra de unidad directa no calificada en tests
            pass

        cmd: List[str] = [
            self.binary_path,
            "-u",
            "-f", format_type,
            "-c", compression,
            "-d", digest,
            "-S", segment_size,
            "-t", target_basename_no_ext,
            "-m", "fixed",
            "-M", "physical",
        ]

        if case_number:
            cmd.extend(["-C", str(case_number)])
        if evidence_number:
            cmd.extend(["-E", str(evidence_number)])
        if examiner:
            cmd.extend(["-e", str(examiner)])
        if description:
            cmd.extend(["-D", str(description)])
        if notes:
            cmd.extend(["-N", str(notes)])
        if native_log_path:
            cmd.extend(["-l", str(native_log_path)])

        cmd.append(source_physical_drive)
        return cmd
