"""
Verificaciones preflight de privilegios de administrador y revalidación de origen.
"""

import ctypes
import os
from typing import Dict, Any, Optional
from agente_forense.acquisition.errors import (
    AdminPrivilegesRequiredError, SourceChangedError
)


def check_admin_privileges() -> bool:
    """Verifica si el proceso actual en Windows posee derechos de Administrador."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def verify_execution_privileges() -> None:
    """Lanza AdminPrivilegesRequiredError si no es Administrador."""
    if not check_admin_privileges():
        raise AdminPrivilegesRequiredError(
            "ADMIN_PRIVILEGES_REQUIRED: Se requieren privilegios de Administrador "
            "para abrir dispositivos físicos \\\\.\\PhysicalDriveN."
        )


def revalidate_source_disk(
    expected_binding: Dict[str, Any],
    current_system_disks: list
) -> Dict[str, Any]:
    """
    Revalida inmediatamente el disco de origen contra la información actual del sistema.
    Exige:
    - is_read_only == True
    - is_system == False
    - is_boot == False
    - Coincidencia de disk_number, physical_drive, serial_number y size_bytes.
    """
    target_num = expected_binding.get("disk_number")
    target_pd = expected_binding.get("physical_drive")
    target_serial = expected_binding.get("serial_number")

    matched = None
    for curr in current_system_disks:
        if isinstance(curr, dict):
            if curr.get("disk_number") == target_num and curr.get("physical_drive") == target_pd:
                matched = curr
                break
        else:
            if getattr(curr, "disk_number", None) == target_num and getattr(curr, "physical_drive", None) == target_pd:
                matched = curr.__dict__ if hasattr(curr, "__dict__") else curr
                break

    if not matched:
        raise SourceChangedError(f"SOURCE_CHANGED: Disco {target_pd} (número {target_num}) no encontrado.")

    is_ro = matched.get("is_read_only") if isinstance(matched, dict) else getattr(matched, "is_read_only", False)
    if not is_ro:
        raise SourceChangedError(f"SOURCE_CHANGED: El disco {target_pd} tiene la protección de escritura deshabilitada (is_read_only=False).")

    is_sys = matched.get("is_system") if isinstance(matched, dict) else getattr(matched, "is_system", True)
    if is_sys:
        raise SourceChangedError(f"SOURCE_CHANGED: El disco {target_pd} se detectó como disco de sistema.")

    is_boot = matched.get("is_boot") if isinstance(matched, dict) else getattr(matched, "is_boot", True)
    if is_boot:
        raise SourceChangedError(f"SOURCE_CHANGED: El disco {target_pd} se detectó como disco de arranque.")

    if target_serial:
        curr_serial = matched.get("serial_number") if isinstance(matched, dict) else getattr(matched, "serial_number", None)
        if curr_serial != target_serial:
            raise SourceChangedError(f"SOURCE_CHANGED: Número de serie cambió de {target_serial} a {curr_serial}.")

    return matched if isinstance(matched, dict) else matched.__dict__
