"""
Validaciones sintácticas y de seguridad para RUC y NUE.
"""

import re
from agente_forense.domain.errors import InvalidRUCError, InvalidNUEError

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def validate_ruc(ruc: str) -> str:
    """
    Valida y normaliza un identificador RUC.
    No realiza validación jurídica, sólo validación técnica segura:
    - No vacío o compuesto únicamente por espacios.
    - Sin path traversal (..).
    - Sin separadores de ruta (/ o \\).
    - Sin nombres reservados de Windows.
    """
    if not ruc or not ruc.strip():
        raise InvalidRUCError("El RUC no puede estar vacío.")

    cleaned = ruc.strip()

    if ".." in cleaned:
        raise InvalidRUCError(f"RUC inválido por sospecha de path traversal: '{ruc}'")

    if "/" in cleaned or "\\" in cleaned:
        raise InvalidRUCError(f"RUC inválido por contener separadores de ruta: '{ruc}'")

    # Verificar caracteres de control o no imprimibles
    if any(ord(c) < 32 for c in cleaned):
        raise InvalidRUCError(f"RUC contiene caracteres no válidos: '{ruc}'")

    base_name = cleaned.split(".")[0].upper()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise InvalidRUCError(f"RUC coincide con un nombre reservado de Windows: '{ruc}'")

    return cleaned


def validate_nue(nue: str) -> str:
    """
    Valida y normaliza un número de NUE.
    - No vacío.
    - Sin path traversal.
    - Sin separadores de ruta.
    - Sin nombres reservados de Windows.
    """
    if not nue or not nue.strip():
        raise InvalidNUEError("El NUE no puede estar vacío.")

    cleaned = nue.strip()

    if ".." in cleaned:
        raise InvalidNUEError(f"NUE inválida por sospecha de path traversal: '{nue}'")

    if "/" in cleaned or "\\" in cleaned:
        raise InvalidNUEError(f"NUE inválida por contener separadores de ruta: '{nue}'")

    if any(ord(c) < 32 for c in cleaned):
        raise InvalidNUEError(f"NUE contiene caracteres no válidos: '{nue}'")

    base_name = cleaned.split(".")[0].upper()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise InvalidNUEError(f"NUE coincide con un nombre reservado de Windows: '{nue}'")

    return cleaned
