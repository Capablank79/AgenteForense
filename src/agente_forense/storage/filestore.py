"""
Módulo de FileStore controlado para almacenamiento seguro de archivos.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, Union
from agente_forense.core.errors import SafetyViolationError
from agente_forense.storage.paths import sanitize_filename, validate_safe_path
from agente_forense.storage.hashing import calculate_sha256

class FileStore:
    """
    Servicio desacoplado para almacenar y verificar archivos en un directorio controlado.
    Garantiza:
    - Validación anti-path traversal
    - Verificación SHA-256 pre y post copy
    - Protección contra sobrescritura silenciosa
    """
    def __init__(self, root_dir: Union[str, Path]):
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True, exist_ok=True)

    def store_file(
        self,
        source_path: Union[str, Path],
        target_relative_dir: str,
        target_filename: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        source = Path(source_path).resolve()
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"Archivo fuente no existe: {source_path}")

        # Sanitizar nombre de archivo
        safe_name = sanitize_filename(target_filename)

        # Validar target directory y resolver path completo
        target_dir = validate_safe_path(self.root_dir, target_relative_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = validate_safe_path(target_dir, safe_name)

        if target_path.exists() and not overwrite:
            raise SafetyViolationError(f"El archivo destino ya existe y overwrite=False: {target_path}")

        # Hash origen
        source_sha256 = calculate_sha256(source)
        source_size = source.stat().st_size

        # Copia de archivo
        shutil.copy2(source, target_path)

        # Hash destino post-copy
        target_sha256 = calculate_sha256(target_path)

        if source_sha256 != target_sha256:
            # Revertir copia corrupta
            if target_path.exists():
                target_path.unlink()
            raise SafetyViolationError("Fallo de integridad post-copy: SHA-256 no coincide.")

        rel_path = target_path.relative_to(self.root_dir)

        return {
            "original_filename": source.name,
            "stored_filename": safe_name,
            "relative_path": str(rel_path).replace("\\", "/"),
            "full_path": str(target_path),
            "size_bytes": source_size,
            "sha256": target_sha256,
            "integrity_status": "VERIFIED",
        }
