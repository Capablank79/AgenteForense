"""
Módulo de gestión segura de rutas y prevención de Path Traversal.
"""

import os
from pathlib import Path
from typing import Union
from agente_forense.core.errors import SafetyViolationError

# Nombres reservados en Windows (case-insensitive)
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def sanitize_filename(filename: str) -> str:
    """
    Valida y sanitiza un nombre de archivo para evitar path traversal o nombres reservados en Windows.
    """
    if not filename or not isinstance(filename, str):
        raise SafetyViolationError("El nombre de archivo no puede ser nulo o vacío.")
    
    # Prevenir secuencias de traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise SafetyViolationError(f"Intento de Path Traversal detectado en nombre de archivo: {filename}")

    # Prevenir drive letters o rutas absolutas
    if ":" in filename:
        raise SafetyViolationError(f"Ruta absoluta o especificación de unidad detectada: {filename}")

    # Prevenir nombres reservados de Windows
    stem = Path(filename).stem.upper()
    if stem in RESERVED_NAMES:
        raise SafetyViolationError(f"Nombre reservado de sistema operativo detectado: {filename}")

    return filename

def validate_safe_path(base_dir: Union[str, Path], relative_path: Union[str, Path]) -> Path:
    """
    Garantiza que relative_path resuelva estrictamente DENTRO de base_dir.
    Retorna el Path absoluto resuelto.
    """
    base = Path(base_dir).resolve()
    target = (base / relative_path).resolve()

    try:
        target.relative_to(base)
    except ValueError:
        raise SafetyViolationError(f"Path Traversal detectado: {relative_path} escapa de {base_dir}")

    return target
