"""
Validación Anti-Invención de Atributos.
Compara cualquier valor propuesto por Qwen contra el texto OCR fuente y metadatos estructurados.
Si un valor no tiene soporte en el texto OCR o corrección humana, es RECHAZADO (`REJECTED_UNSUPPORTED`).
"""

import re
from typing import Optional

def validate_anti_invention(field_name: str, proposed_value: Optional[str], ocr_text: str) -> bool:
    """
    Verifica si proposed_value tiene sustento directo en ocr_text.
    Reglas de sustento:
    - trim / case-insensitive match
    - ocr_text contiene el valor propuesto (o subcadena significativa)
    - no permite completar abreviaturas ni inferir fabricantes externos (ej. NVIDIA por GTX si NVIDIA no aparece).
    """
    if not proposed_value or not proposed_value.strip():
        return False

    if not ocr_text:
        return False

    prop_norm = proposed_value.strip().upper()
    ocr_norm = ocr_text.upper()

    # Si es una marca o modelo o serial, debe aparecer explícitamente en el OCR
    if prop_norm in ocr_norm:
        return True

    # Para capacidad, permitir si los números aparecen
    if field_name == "capacity":
        digits = "".join(c for c in prop_norm if c.isdigit())
        if digits and digits in ocr_norm:
            return True

    return False
