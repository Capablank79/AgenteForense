"""
Módulo para generación y lectura del artefacto identification.json.
"""

import json
import tempfile
import os
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any
from agente_forense.identification.models import IdentificationData

IDENTIFICATION_SCHEMA_VERSION = 1

def generate_identification_json_dict(data: IdentificationData) -> Dict[str, Any]:
    """Genera la estructura de diccionario serializable a JSON."""
    return {
        "schema_version": data.schema_version,
        "entity_type": data.entity_type,
        "entity_id": data.entity_id,
        "entity_label": data.entity_label,
        "status": data.status,
        "photos": [asdict(p) for p in data.photos],
        "attributes": {k: asdict(v) for k, v in data.attributes.items()},
        "conflicts": [asdict(c) for c in data.conflicts],
        "human_review": data.human_review,
        "tool_versions": data.tool_versions,
        "timestamps": data.timestamps
    }

def write_identification_json_atomic(data: IdentificationData, target_dir: Path) -> Path:
    """Escribe identification.json de forma atómica en target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    final_path = target_dir / "identification.json"

    dict_data = generate_identification_json_dict(data)

    temp_fd, temp_path_str = tempfile.mkstemp(dir=target_dir, prefix="ident_", suffix=".tmp")
    temp_path = Path(temp_path_str)

    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(dict_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, final_path)
        return final_path
    except Exception as e:
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise e
