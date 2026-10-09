"""
Renombrado Seguro de Fotografías con vista previa, verificación de colisiones y rollback.
Nomenclatura: NUE_{nue}_ESPECIE{sp}_[DSM{dsm}_]{clasificacion}_{seq:02d}.ext
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from agente_forense.storage.hashing import calculate_sha256
from agente_forense.identification.errors import RenameCollisionError, PhotoIntegrityError
from agente_forense.identification.models import PhotoIngestRecord

def build_deterministic_filename(
    nue_number: str,
    species_number: int,
    dsm_number: Optional[int],
    classification: str,
    sequence: int,
    extension: str
) -> str:
    """Genera el nombre normalizado determinístico para la fotografía."""
    ext = extension.lstrip(".").lower()
    if ext not in ["jpg", "jpeg", "png"]:
        ext = "jpg"

    cls_str = classification.upper() if classification else "GENERAL"
    
    if dsm_number is not None:
        return f"NUE_{nue_number}_ESPECIE{species_number}_DSM{dsm_number}_{cls_str}_{sequence:02d}.{ext}"
    else:
        return f"NUE_{nue_number}_ESPECIE{species_number}_{cls_str}_{sequence:02d}.{ext}"

def preview_renaming(
    photos: List[PhotoIngestRecord],
    target_dir: Path,
    nue_number: str,
    species_number: int,
    dsm_number: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Genera una vista previa del plan de renombrado sin modificar archivos en disco.
    """
    plan = []
    seq_counter: Dict[str, int] = {}

    for photo in photos:
        cls = photo.classification_final or photo.classification or "GENERAL"
        seq_counter[cls] = seq_counter.get(cls, 0) + 1
        seq = seq_counter[cls]

        ext = Path(photo.original_filename).suffix
        new_name = build_deterministic_filename(
            nue_number=nue_number,
            species_number=species_number,
            dsm_number=dsm_number,
            classification=cls,
            sequence=seq,
            extension=ext
        )
        plan.append({
            "photo_id": photo.photo_id,
            "old_filename": photo.original_filename,
            "new_filename": new_name,
            "old_path": photo.relative_path,
            "new_path": str(Path(photo.relative_path).parent / new_name).replace("\\", "/")
        })
    return plan

def execute_safe_renaming(
    plan: List[Dict[str, str]],
    base_directory: Path,
    photos: List[PhotoIngestRecord]
) -> List[PhotoIngestRecord]:
    """
    Ejecuta el renombrado seguro de lote.
    Comprueba colisiones antes de renombrar.
    Si cualquier renombrado falla o la integridad de hash falla, realiza rollback completo.
    """
    # 1. Collision check
    targets = [base_directory / item["new_path"] for item in plan]
    for target in targets:
        if target.exists() and target not in [base_directory / item["old_path"] for item in plan]:
            raise RenameCollisionError(f"Colisión de renombrado: el archivo {target} ya existe.")

    executed_renames: List[Tuple[Path, Path, str]] = [] # (old_path, new_path, photo_id)

    photo_map = {p.photo_id: p for p in photos}

    try:
        for item in plan:
            old_p = base_directory / item["old_path"]
            new_p = base_directory / item["new_path"]
            photo_id = item["photo_id"]
            photo = photo_map[photo_id]

            # Verify hash before rename
            hash_before = calculate_sha256(old_p)
            if hash_before != photo.sha256:
                raise PhotoIntegrityError(f"Integridad fallida en {old_p.name} antes de renombrar.")

            # Perform atomic move / rename
            new_p.parent.mkdir(parents=True, exist_ok=True)
            os.replace(old_p, new_p)
            executed_renames.append((old_p, new_p, photo_id))

            # Verify hash after rename
            hash_after = calculate_sha256(new_p)
            if hash_after != photo.sha256:
                raise PhotoIntegrityError(f"Integridad fallida en {new_p.name} después de renombrar.")

            # Update record
            photo.relative_path = item["new_path"]
            photo.original_filename = item["new_filename"]

        return list(photo_map.values())

    except Exception as e:
        # Rollback
        for old_p, new_p, photo_id in reversed(executed_renames):
            if new_p.exists():
                try:
                    os.replace(new_p, old_p)
                    photo_map[photo_id].relative_path = str(old_p)
                    photo_map[photo_id].original_filename = old_p.name
                except Exception:
                    pass
        raise e
