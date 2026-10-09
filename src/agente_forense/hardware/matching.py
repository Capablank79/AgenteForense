"""
Motor de coincidencia / comparación entre un DSM (Storage Device) y un DiskSnapshot físico.
"""

from typing import Dict, Any, Optional, List
from agente_forense.hardware.models import DiskSnapshot, DsmDiskComparison, MatchingStatus


def compare_dsm_with_disk(dsm_data: Dict[str, Any], disk: DiskSnapshot) -> DsmDiskComparison:
    """
    Compara los metadatos de un DSM lógico (de base de datos) contra un DiskSnapshot de disco físico.
    dsm_data contiene: id, brand, model, serial, capacity_bytes, etc.
    """
    reasons: List[str] = []
    
    dsm_serial = dsm_data.get("serial")
    if dsm_serial:
        dsm_serial = str(dsm_serial).strip()
        if not dsm_serial:
            dsm_serial = None

    disk_serial = disk.serial_number
    if disk_serial:
        disk_serial = str(disk_serial).strip()
        if not disk_serial:
            disk_serial = None

    # Comparación de Serial
    serial_matched: Optional[bool] = None
    if dsm_serial and disk_serial:
        if dsm_serial.upper() == disk_serial.upper():
            serial_matched = True
            reasons.append(f"Número de serie coincide exactamente: {dsm_serial}")
        else:
            serial_matched = False
            reasons.append(f"Conflicto de número de serie: DSM='{dsm_serial}' vs Disco='{disk_serial}'")

    # Comparación de Capacidad
    capacity_matched: Optional[bool] = None
    dsm_bytes = dsm_data.get("capacity_bytes")
    if dsm_bytes is not None and dsm_bytes > 0:
        disk_bytes = disk.size_bytes
        # Tolerancia del 5% para diferencias de cálculo comercial vs OS/sectores
        diff = abs(disk_bytes - dsm_bytes)
        ratio = diff / float(dsm_bytes)
        if ratio <= 0.05:
            capacity_matched = True
            reasons.append(f"Capacidad compatible ({disk_bytes} bytes OS vs {dsm_bytes} bytes DSM)")
        else:
            capacity_matched = False
            reasons.append(f"Capacidad discrepante: DSM={dsm_bytes} bytes vs Disco={disk_bytes} bytes")

    # Comparación de Modelo/Marca
    model_matched: Optional[bool] = None
    dsm_model = dsm_data.get("model")
    dsm_brand = dsm_data.get("brand")
    friendly = disk.friendly_name or ""

    if dsm_model:
        dsm_model_clean = str(dsm_model).strip().upper()
        if dsm_model_clean in friendly.upper():
            model_matched = True
            reasons.append(f"Modelo DSM '{dsm_model}' encontrado en FriendlyName del disco")

    # Determinar status final de coincidencia
    if serial_matched is False or capacity_matched is False:
        status = MatchingStatus.CONFLICT
    elif serial_matched is True:
        status = MatchingStatus.MATCH
    elif model_matched is True or capacity_matched is True:
        status = MatchingStatus.COMPATIBLE
    elif not dsm_serial:
        status = MatchingStatus.INSUFFICIENT_DATA
        reasons.append("DSM no posee número de serie registrado para comparar")
    else:
        status = MatchingStatus.NOT_COMPARABLE

    return DsmDiskComparison(
        dsm_id=str(dsm_data.get("id")),
        disk_number=disk.disk_number,
        physical_drive=disk.physical_drive,
        status=status,
        reasons=reasons,
        serial_matched=serial_matched,
        capacity_matched=capacity_matched,
        model_matched=model_matched
    )
