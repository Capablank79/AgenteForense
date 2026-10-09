"""
Provenance tracking and audit mapping helpers.
"""
from typing import List, Dict, Any
from agente_forense.petition.models import FieldProvenance, ExtractedField

def format_provenance_summary(provenance: List[FieldProvenance]) -> List[Dict[str, Any]]:
    return [p.model_dump() for p in provenance]
