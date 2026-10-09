"""
Servicio de revalidación segura de vínculos DSM ↔ PhysicalDrive.
"""

from typing import Optional, Dict, Any
from agente_forense.hardware.disks import DiskScanner
from agente_forense.hardware.models import DiskSnapshot
from agente_forense.hardware.errors import (
    SourceChangedError,
    DiskNotFoundError,
    DiskNotReadOnlyError,
    SystemDiskBlockedError,
    BootDiskBlockedError
)


class DiskRevalidator:
    """Revalida un DiskSnapshot o binding contra el estado actual de los discos de Windows."""

    def __init__(self, scanner: Optional[DiskScanner] = None):
        self.scanner = scanner or DiskScanner()

    def revalidate_snapshot(self, binding_snapshot: Dict[str, Any]) -> DiskSnapshot:
        """
        Reconsulta los discos del sistema y verifica si el disco de binding_snapshot sigue presente,
        con el mismo número, physical_drive, serial, unique_id, size_bytes y manteniéndose read-only.
        Si hay un cambio crítico, lanza SourceChangedError.
        """
        current_snapshots = self.scanner.scan_disks()
        target_num = binding_snapshot.get("disk_number")
        target_pd = binding_snapshot.get("physical_drive")
        target_serial = binding_snapshot.get("serial_number")
        target_uid = binding_snapshot.get("unique_id")

        matched: Optional[DiskSnapshot] = None
        for curr in current_snapshots:
            if curr.disk_number == target_num and curr.physical_drive == target_pd:
                matched = curr
                break

        if not matched:
            raise SourceChangedError(
                f"El disco {target_pd} (número {target_num}) ya no se encuentra conectado al sistema."
            )

        # Verificar re-clasificación / lectura
        if not matched.is_read_only:
            raise DiskNotReadOnlyError(
                f"El disco {target_pd} ha cambiado a IsReadOnly=False. Operación bloqueada."
            )
        if matched.is_system:
            raise SystemDiskBlockedError(f"El disco {target_pd} se detectó como disco de sistema.")
        if matched.is_boot:
            raise BootDiskBlockedError(f"El disco {target_pd} se detectó como disco de arranque.")

        # Verificar serial si existía
        if target_serial and matched.serial_number:
            if target_serial.strip().upper() != matched.serial_number.strip().upper():
                raise SourceChangedError(
                    f"Conflicto de número de serie en revalidación: registrado='{target_serial}' vs actual='{matched.serial_number}'"
                )

        # Verificar size_bytes
        if binding_snapshot.get("size_bytes") and matched.size_bytes != binding_snapshot.get("size_bytes"):
            raise SourceChangedError(
                f"El tamaño en bytes del disco ha cambiado: registrado={binding_snapshot.get('size_bytes')} vs actual={matched.size_bytes}"
            )

        return matched
