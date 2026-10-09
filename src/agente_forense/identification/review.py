"""
Módulo de Revisión Humana (Human Review).
Permite confirmar, corregir o rechazar clasificaciones de fotos y atributos propuestos.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from agente_forense.identification.models import IdentificationData, AttributeStatus

def apply_human_review(
    identification_data: IdentificationData,
    operator: str,
    corrected_classification: Optional[Dict[str, str]] = None,
    corrected_attributes: Optional[Dict[str, str]] = None,
    confirmed: bool = False
) -> IdentificationData:
    """
    Aplica las correcciones o confirmaciones del operador perito.
    Registra trazabilidad y cambia el estado de los atributos a CONFIRMED o CORRECTED_BY_HUMAN.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # Corrección de clasificaciones fotográficas
    if corrected_classification:
        for photo in identification_data.photos:
            if photo.photo_id in corrected_classification:
                photo.classification_final = corrected_classification[photo.photo_id]

    # Corrección de atributos
    if corrected_attributes:
        for field_name, new_val in corrected_attributes.items():
            if field_name in identification_data.attributes:
                attr = identification_data.attributes[field_name]
                if new_val is None or new_val.strip() == "":
                    attr.value = None
                    attr.status = AttributeStatus.REJECTED_UNSUPPORTED.value
                else:
                    attr.value = new_val.strip()
                    attr.status = AttributeStatus.CORRECTED_BY_HUMAN.value
                    if attr.provenance:
                        attr.provenance.human_confirmed = True
                        attr.provenance.status = AttributeStatus.CORRECTED_BY_HUMAN.value

    if confirmed:
        identification_data.human_review["reviewed"] = True
        identification_data.human_review["reviewed_by"] = operator
        identification_data.human_review["reviewed_at"] = now_iso
        identification_data.human_review["confirmed"] = True

        for attr in identification_data.attributes.values():
            if attr.status == AttributeStatus.EXTRACTED.value:
                attr.status = AttributeStatus.CONFIRMED.value
                if attr.provenance:
                    attr.provenance.human_confirmed = True

    return identification_data
