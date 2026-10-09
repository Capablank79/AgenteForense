"""
Conflict detection module for Petition extraction.
Detects MULTIPLE_RUC, RUC_MISSING, MULTIPLE_NUE_CANDIDATES, NUE_MISSING, MULTIPLE_OFICIO, AMBIGUOUS_DATE, etc.
"""
from typing import List
from agente_forense.petition.models import ExtractedField, ExtractionConflict, ConflictType, FieldStatus

class ConflictDetector:
    def detect_conflicts(
        self,
        fields: List[ExtractedField],
        total_ocr_text_length: int = 0
    ) -> List[ExtractionConflict]:
        conflicts: List[ExtractionConflict] = []

        # Check OCR Empty
        if total_ocr_text_length == 0:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.OCR_EMPTY,
                field_name="document_text",
                description="No text could be extracted or recognized from the petition document.",
                details={}
            ))
            return conflicts

        # Check RUC
        ruc_fields = [f for f in fields if f.field_name == "ruc"]
        if not ruc_fields or ruc_fields[0].status == FieldStatus.NOT_FOUND or not ruc_fields[0].value:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.RUC_MISSING,
                field_name="ruc",
                description="RUC was not found in the petition document. Human review required.",
                details={}
            ))
        elif ruc_fields[0].status == FieldStatus.CONFLICT:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.MULTIPLE_RUC,
                field_name="ruc",
                description="Multiple distinct RUC values detected in document.",
                details={"found_value": ruc_fields[0].value}
            ))

        # Check NUE
        nue_fields = [f for f in fields if f.field_name == "nue" and f.status != FieldStatus.NOT_FOUND and f.value]
        if not nue_fields:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.NUE_MISSING,
                field_name="nue",
                description="No NUE was found in the petition document. Human review required.",
                details={}
            ))
        elif len(nue_fields) > 1:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.MULTIPLE_NUE_CANDIDATES,
                field_name="nue",
                description=f"Multiple distinct NUE candidates found ({len(nue_fields)} NUEs).",
                details={"nues": [f.value for f in nue_fields]}
            ))

        # Check Oficio Number
        oficio_fields = [f for f in fields if f.field_name == "oficio_number"]
        if oficio_fields and oficio_fields[0].status == FieldStatus.CONFLICT:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.MULTIPLE_OFICIO,
                field_name="oficio_number",
                description="Multiple distinct petition numbers detected.",
                details={"found_value": oficio_fields[0].value}
            ))

        # Check Date Ambiguity
        date_fields = [f for f in fields if f.field_name == "petition_date"]
        if date_fields and date_fields[0].status == FieldStatus.UNCERTAIN:
            conflicts.append(ExtractionConflict(
                conflict_type=ConflictType.AMBIGUOUS_DATE,
                field_name="petition_date",
                description="Petition date is ambiguous or uncertain.",
                details={"found_value": date_fields[0].value}
            ))

        return conflicts
