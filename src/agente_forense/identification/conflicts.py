"""
Detección de conflictos entre fotografías y atributos de una entidad.
"""

from typing import List, Dict
from agente_forense.identification.models import (
    ConflictRecord, ConflictCode, AttributeValue, PhotoIngestRecord, AttributeStatus
)

def detect_conflicts(
    photos: List[PhotoIngestRecord],
    attributes: Dict[str, AttributeValue]
) -> List[ConflictRecord]:
    """
    Detecta conflictos operacionales y de integridad en la evidencia de la entidad.
    """
    conflicts: List[ConflictRecord] = []

    # 1. Siempre reportar NO_VISION_PROVIDER al carecer de VLM local
    conflicts.append(
        ConflictRecord(
            code=ConflictCode.NO_VISION_PROVIDER.value,
            description="No se dispone de proveedor VLM local. Clasificación visual y color no inferibles automáticamente.",
            severity="WARNING"
        )
    )

    # 2. Verificar si hay fotografías sin texto OCR
    photos_no_text = [p.photo_id for p in photos if p.ocr_text == "" or p.analysis_status == "NO_TEXT"]
    if photos_no_text:
        conflicts.append(
            ConflictRecord(
                code=ConflictCode.NO_TEXT.value,
                description=f"OCR no detectó texto visible en {len(photos_no_text)} fotografía(s).",
                severity="WARNING",
                photo_ids=photos_no_text
            )
        )

    # 3. Discrepancias / Múltiples valores en Serial
    serials_found = set()
    for p in photos:
        # Si la foto tiene OCR, buscar seriales
        pass

    # Inspeccionar atributos en busca de conflictos marcados
    for field_name, attr in attributes.items():
        if attr.status == AttributeStatus.CONFLICT.value:
            if field_name == "serial":
                conflicts.append(
                    ConflictRecord(
                        code=ConflictCode.SERIAL_MULTIPLE_VALUES.value,
                        description="Existen múltiples números de serie no concordantes reportados.",
                        severity="BLOCKING",
                        affected_fields=["serial"]
                    )
                )
            elif field_name == "model":
                conflicts.append(
                    ConflictRecord(
                        code=ConflictCode.MODEL_MULTIPLE_VALUES.value,
                        description="Existen múltiples modelos no concordantes reportados.",
                        severity="BLOCKING",
                        affected_fields=["model"]
                    )
                )
            elif field_name == "brand":
                conflicts.append(
                    ConflictRecord(
                        code=ConflictCode.BRAND_CONFLICT.value,
                        description="Conflicto detectado en la marca del dispositivo.",
                        severity="WARNING",
                        affected_fields=["brand"]
                    )
                )
            elif field_name == "capacity":
                conflicts.append(
                    ConflictRecord(
                        code=ConflictCode.CAPACITY_CONFLICT.value,
                        description="Conflicto detectado en la capacidad del dispositivo.",
                        severity="WARNING",
                        affected_fields=["capacity"]
                    )
                )

    return conflicts
