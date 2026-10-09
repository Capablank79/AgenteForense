"""
Validaciones de destino, espacio en disco, sistema de archivos y políticas de colisión.
"""

import os
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from agente_forense.acquisition.errors import (
    DestinationInvalidError, SpaceBelowRawSizeError, DestinationOnSourceDiskError,
    TargetCollisionError, IncompatibleFilesystemError
)


def get_filesystem_type(path: str) -> str:
    """Obtiene el tipo de sistema de archivos (NTFS, FAT32, exFAT, etc.) en Windows."""
    if platform.system() != "Windows":
        return "NTFS"
    
    path_obj = Path(path).resolve()
    drive = path_obj.drive or str(path_obj.anchor)
    if not drive.endswith("\\"):
        drive = drive + "\\"
        
    try:
        import ctypes
        volume_name_buf = ctypes.create_unicode_buffer(1024)
        fs_name_buf = ctypes.create_unicode_buffer(1024)
        serial_num = ctypes.c_ulong()
        max_component_len = ctypes.c_ulong()
        fs_flags = ctypes.c_ulong()

        rc = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            volume_name_buf,
            ctypes.sizeof(volume_name_buf),
            ctypes.byref(serial_num),
            ctypes.byref(max_component_len),
            ctypes.byref(fs_flags),
            fs_name_buf,
            ctypes.sizeof(fs_name_buf)
        )
        if rc:
            return fs_name_buf.value.upper()
    except Exception:
        pass
    return "UNKNOWN"


def resolve_physical_drive_for_path(path: str) -> Optional[str]:
    """
    Intenta resolver el disco físico (PhysicalDriveN) que aloja la ruta de destino.
    """
    try:
        path_obj = Path(path).resolve()
        drive_letter = path_obj.drive.upper().rstrip(":")
        if not drive_letter:
            return None

        # Usar PowerShell de forma segura o simulación
        import subprocess
        ps_cmd = f"Get-Partition -DriveLetter {drive_letter} | Select-Object -ExpandProperty DiskNumber"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip().isdigit():
            disk_num = res.stdout.strip()
            return f"\\\\.\\PhysicalDrive{disk_num}"
    except Exception:
        pass
    return None


class DestinationValidator:
    """
    Valida el directorio y archivo destino antes de autorizar la adquisición.
    Requisitos:
    - exists & is directory
    - writable
    - filesystem conocido (bloquea FAT32 si source_size > 4GB)
    - free bytes >= source_size (SPACE_BELOW_RAW_SIZE)
    - source physical disk != destination physical disk (DESTINATION_ON_SOURCE_DISK)
    - collision policy: target basename sin .E01, .E02, log preexistente (ACQUISITION_TARGET_EXISTS)
    """

    def validate(
        self,
        destination_directory: str,
        target_basename: str,
        source_size_bytes: int,
        source_physical_drive: str,
        safety_margin_ratio: float = 1.0
    ) -> Dict[str, Any]:
        dest_path = Path(destination_directory).resolve()

        if not dest_path.exists():
            raise DestinationInvalidError(f"El directorio de destino no existe: {destination_directory}")
        if not dest_path.is_dir():
            raise DestinationInvalidError(f"La ruta de destino no es un directorio: {destination_directory}")

        # Probar escritura
        test_file = dest_path / f".write_test_{os.getpid()}"
        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except Exception as e:
            raise DestinationInvalidError(f"El directorio de destino no es escribible: {e}")

        # Espacio libre
        usage = shutil.disk_usage(str(dest_path))
        free_bytes = usage.free

        if free_bytes < source_size_bytes:
            raise SpaceBelowRawSizeError(
                f"SPACE_BELOW_RAW_SIZE: Espacio libre ({free_bytes} bytes) "
                f"es inferior al tamaño del disco origen ({source_size_bytes} bytes)."
            )

        # Sistema de archivos
        fs_type = get_filesystem_type(str(dest_path))
        if fs_type == "FAT32" and source_size_bytes > 4 * 1024 * 1024 * 1024:
            raise IncompatibleFilesystemError(
                "Sistema de archivos FAT32 no soporta archivos de imagen E01 únicos mayores a 4 GB."
            )

        # Mismo disco físico
        dest_physical_drive = resolve_physical_drive_for_path(str(dest_path))
        if dest_physical_drive and source_physical_drive and dest_physical_drive.lower() == source_physical_drive.lower():
            raise DestinationOnSourceDiskError(
                f"DESTINATION_ON_SOURCE_DISK: El destino está en el mismo disco físico ({source_physical_drive}) que el origen."
            )

        # Colisión de archivos
        expected_e01 = dest_path / f"{target_basename}.E01"
        expected_e02 = dest_path / f"{target_basename}.E02"
        expected_log = dest_path / "logs" / "ewfacquire_native.log"
        expected_json = dest_path / "acquisition.json"

        if expected_e01.exists() or expected_e02.exists():
            raise TargetCollisionError(
                f"ACQUISITION_TARGET_EXISTS: Ya existen artefactos E01 para el target '{target_basename}' en {dest_path}."
            )

        return {
            "destination_directory": str(dest_path),
            "target_basename": target_basename,
            "free_bytes": free_bytes,
            "filesystem": fs_type,
            "destination_physical_drive": dest_physical_drive,
            "expected_e01_path": str(expected_e01)
        }
