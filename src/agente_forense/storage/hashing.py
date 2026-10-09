"""
Módulo de cálculo de hash SHA-256 e integridad.
"""

import hashlib
from pathlib import Path
from typing import Union

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calcula el hash SHA-256 de un archivo de manera eficiente en bloques.
    Devuelve la cadena hexadecimal en minúsculas.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Archivo no encontrado para hashing: {file_path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest().lower()
