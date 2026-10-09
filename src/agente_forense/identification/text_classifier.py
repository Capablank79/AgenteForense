"""
Clasificador textual automático de fotografías basado en soporte textual OCR explícito.
"""

import re
from agente_forense.identification.models import PhotoClassification

def classify_photo_textually(ocr_text: str) -> str:
    """
    Propone una clasificación para la foto basándose ÚNICAMENTE en patrones textuales explícitos del OCR.
    Si no hay soporte textual claro, retorna NO_CLASIFICADA.
    NO clasifica FRONTAL / LATERAL / POSTERIOR sin soporte textual.
    """
    if not ocr_text:
        return PhotoClassification.NO_CLASIFICADA.value

    text_upper = ocr_text.upper()

    # Patrones para SERIAL
    serial_patterns = [
        r"\bS/N\b", r"\bSERIAL\b", r"\bSERIAL\s*NO\b", r"\bSERIAL\s*NUMBER\b", r"\bSN:\b", r"\bN/S\b"
    ]
    for pat in serial_patterns:
        if re.search(pat, text_upper):
            return PhotoClassification.SERIAL.value

    # Patrones para ETIQUETA / ETIQUETAS MÚLTIPLES
    label_keywords = ["MODEL", "PN", "PART NUMBER", "P/N", "REV", "RATING", "VOLTS", "MADE IN", "FACTORY", "WARRANTY", "WWN"]
    match_count = sum(1 for kw in label_keywords if kw in text_upper)
    if match_count >= 2:
        return PhotoClassification.ETIQUETA.value

    return PhotoClassification.NO_CLASIFICADA.value
