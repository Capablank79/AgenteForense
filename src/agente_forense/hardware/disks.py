"""
Escáner seguro de discos físicos Windows mediante PowerShell Get-Disk y Win32_DiskDrive.
"""

import json
import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from agente_forense.hardware.models import DiskSnapshot, ClassifiedDisk, ForensicDiskClassification
from agente_forense.hardware.errors import (
    PowerShellUnavailableError,
    StorageModuleUnavailableError,
    DiskScanTimeoutError,
    DiskScanParseError,
    UnsupportedDiskRepresentationError
)

POWERSHELL_PATH = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

GET_DISK_COMMAND = (
    "Get-Disk | Select-Object Number, FriendlyName, SerialNumber, UniqueId, Path, Size, BusType, "
    "PartitionStyle, IsReadOnly, IsSystem, IsBoot, IsOffline, OperationalStatus, HealthStatus | "
    "ConvertTo-Json -Depth 4 -Compress"
)

WIN32_DISKDRIVE_COMMAND = (
    "Get-WmiObject Win32_DiskDrive | Select-Object Index, DeviceID, Model, SerialNumber, PNPDeviceID | "
    "ConvertTo-Json -Depth 4 -Compress"
)


class DiskScanner:
    """Escáner de discos de solo lectura para Windows."""

    def __init__(self, powershell_executable: str = POWERSHELL_PATH, timeout: int = 15):
        self.powershell_executable = powershell_executable
        self.timeout = timeout

    def _run_powershell_json(self, command: str) -> Any:
        try:
            res = subprocess.run(
                [self.powershell_executable, "-NoProfile", "-Command", command],
                shell=False,
                capture_output=True,
                timeout=self.timeout
            )
        except FileNotFoundError:
            raise PowerShellUnavailableError(f"No se encontró el ejecutable PowerShell en {self.powershell_executable}")
        except subprocess.TimeoutExpired:
            raise DiskScanTimeoutError(f"La ejecución del comando PowerShell superó el tiempo límite de {self.timeout}s.")

        if res.returncode != 0:
            err_msg = res.stderr.decode("windows-1252", errors="replace") if res.stderr else "Error desconocido"
            raise StorageModuleUnavailableError(f"Error al ejecutar PowerShell Get-Disk: {err_msg}")

        output = res.stdout.decode("utf-8", errors="replace").strip()
        if not output:
            return []

        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            # Reintentar decodificando con windows-1252 por si acaso
            try:
                output_w = res.stdout.decode("windows-1252", errors="replace").strip()
                return json.loads(output_w)
            except Exception:
                raise DiskScanParseError(f"Error al parsear la salida JSON de PowerShell: {e}")

    def scan_disks(self) -> List[DiskSnapshot]:
        raw_disks = self._run_powershell_json(GET_DISK_COMMAND)
        if isinstance(raw_disks, dict):
            raw_disks = [raw_disks]

        raw_win32 = self._run_powershell_json(WIN32_DISKDRIVE_COMMAND)
        if isinstance(raw_win32, dict):
            raw_win32 = [raw_win32]

        win32_map: Dict[int, Dict[str, Any]] = {}
        for w in raw_win32:
            idx = w.get("Index")
            if idx is not None:
                win32_map[int(idx)] = w

        snapshots: List[DiskSnapshot] = []
        observed_at = datetime.now(timezone.utc)

        for d in raw_disks:
            num = d.get("Number")
            if num is None:
                continue

            num_int = int(num)
            wmi_item = win32_map.get(num_int)
            
            # Cross-check Win32_DiskDrive
            if wmi_item:
                dev_id = wmi_item.get("DeviceID", "").upper()
                expected_dev = f"\\\\.\\PHYSICALDRIVE{num_int}"
                if dev_id != expected_dev:
                    raise UnsupportedDiskRepresentationError(
                        f"Descalce de DeviceID entre Get-Disk (Number={num_int}) y Win32_DiskDrive ({dev_id})."
                    )
                physical_drive = f"\\\\.\\PHYSICALDRIVE{num_int}"
                pnp_id = wmi_item.get("PNPDeviceID")
            else:
                physical_drive = f"\\\\.\\PHYSICALDRIVE{num_int}"
                pnp_id = None

            # Normalización del SerialNumber
            serial = d.get("SerialNumber")
            if serial is not None:
                serial = str(serial).strip()
                if not serial:
                    serial = None

            snap = DiskSnapshot(
                disk_number=num_int,
                physical_drive=physical_drive,
                friendly_name=d.get("FriendlyName"),
                serial_number=serial,
                unique_id=d.get("UniqueId"),
                path=d.get("Path"),
                size_bytes=int(d.get("Size") or 0),
                bus_type=d.get("BusType"),
                partition_style=d.get("PartitionStyle"),
                is_read_only=bool(d.get("IsReadOnly", False)),
                is_system=bool(d.get("IsSystem", False)),
                is_boot=bool(d.get("IsBoot", False)),
                is_offline=d.get("IsOffline"),
                operational_status=d.get("OperationalStatus"),
                health_status=d.get("HealthStatus"),
                pnp_device_id=pnp_id,
                observed_at=observed_at,
                source="WINDOWS_STORAGE_API"
            )
            snapshots.append(snap)

        return snapshots

    @staticmethod
    def classify_disk(snap: DiskSnapshot) -> ClassifiedDisk:
        reasons = []
        is_ro = snap.is_read_only
        is_sys = snap.is_system
        is_boot = snap.is_boot

        if not is_ro:
            reasons.append("IsReadOnly es False (El disco no está protegido contra escritura).")
        if is_sys:
            reasons.append("IsSystem es True (Es el disco donde está instalado el sistema operativo).")
        if is_boot:
            reasons.append("IsBoot es True (Es el disco de arranque del sistema).")

        if is_ro and not is_sys and not is_boot:
            classification = ForensicDiskClassification.FORENSIC_CANDIDATE
        elif not is_ro and (is_sys or is_boot):
            classification = ForensicDiskClassification.BLOCKED_MULTIPLE_REASONS
        elif not is_ro:
            classification = ForensicDiskClassification.BLOCKED_NOT_READ_ONLY
        elif is_sys:
            classification = ForensicDiskClassification.BLOCKED_SYSTEM_DISK
        elif is_boot:
            classification = ForensicDiskClassification.BLOCKED_BOOT_DISK
        else:
            classification = ForensicDiskClassification.UNSUPPORTED_DISK_REPRESENTATION

        return ClassifiedDisk(
            snapshot=snap,
            classification=classification,
            reasons=reasons
        )

    def scan_and_classify(self) -> List[ClassifiedDisk]:
        snapshots = self.scan_disks()
        return [self.classify_disk(s) for s in snapshots]
