"""
Reutilización de Windows OCR es-ES para fotografías.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from agente_forense.petition.ocr import WindowsOcrProvider

_ocr_provider: Optional[WindowsOcrProvider] = None

def get_ocr_provider() -> WindowsOcrProvider:
    global _ocr_provider
    if _ocr_provider is None:
        _ocr_provider = WindowsOcrProvider()
    return _ocr_provider

def run_photo_ocr(photo_path: Path, language_tag: str = "es-ES") -> Dict[str, Any]:
    """
    Ejecuta Windows OCR es-ES sobre el archivo de fotografía.
    Retorna diccionario con raw_text, language y status.
    """
    provider = get_ocr_provider()
    if not provider.is_available():
        return {
            "raw_text": "",
            "language": language_tag,
            "status": "OCR_UNAVAILABLE",
            "error": "Windows OCR es-ES no disponible"
        }

    try:
        raw_text = provider.recognize_image_file(str(photo_path), language_tag=language_tag)
        raw_text = raw_text.strip() if raw_text else ""
        return {
            "raw_text": raw_text,
            "language": language_tag,
            "status": "SUCCESS" if raw_text else "NO_TEXT",
            "error": None
        }
    except Exception as e:
        return {
            "raw_text": "",
            "language": language_tag,
            "status": "ERROR",
            "error": str(e)
        }
