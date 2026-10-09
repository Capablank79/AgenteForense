"""
CaseStructureDraft generator and mapper.
Maps reviewed extraction fields into CaseStructureDraft without inventing species, DSMs, or storage topology.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agente_forense.petition.models import PetitionExtraction, FieldStatus
from agente_forense.petition.errors import PetitionNotReadyForDraftError, PetitionExtractionConflictError

class DraftNue(BaseModel):
    nue_number: str
    description_from_petition: Optional[str] = None
    quantity: Optional[int] = 1
    declared_evidence_type: Optional[str] = None
    attributes_from_petition: Optional[Dict[str, Any]] = None
    source: str = "PETITION"

class CaseStructureDraft(BaseModel):
    ruc: str
    nues: List[DraftNue] = Field(default_factory=list)
    requesting_unit: Optional[str] = None
    requesting_rut: Optional[str] = None
    oficio_number: Optional[str] = None
    petition_date: Optional[str] = None
    city: Optional[str] = None
    prosecutor_office: Optional[str] = None
    prosecutor_name: Optional[str] = None
    investigator_name: Optional[str] = None
    crime_context: Optional[str] = None
    requested_diligence: Optional[str] = None
    requested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    petition_id: Optional[str] = None
    petition_sha256: Optional[str] = None
    petition_number: Optional[str] = None
    source: str = "PETITION"
    status: str = "DRAFT_PROPOSED"
    notes: Optional[str] = "La estructura física de especies y dispositivos de almacenamiento aún debe ser confirmada."

class DraftMapper:
    def build_draft_from_extraction(self, extraction: PetitionExtraction) -> CaseStructureDraft:
        # P04: Only APPROVED petitions can generate a CaseStructureDraft
        if extraction.review_status != "APPROVED":
            raise PetitionNotReadyForDraftError("El Oficio Petitorio debe estar en estado APPROVED para generar el borrador de estructura de caso.")

        if extraction.conflicts and len(extraction.conflicts) > 0:
            raise PetitionExtractionConflictError("No se puede generar borrador con conflictos de extracción abiertos.")

        ruc_val: Optional[str] = None
        requesting_unit: Optional[str] = None
        requesting_rut: Optional[str] = None
        oficio_number: Optional[str] = None
        petition_date: Optional[str] = None
        city: Optional[str] = None
        prosecutor_office: Optional[str] = None
        prosecutor_name: Optional[str] = None
        investigator_name: Optional[str] = None
        crime_context: Optional[str] = None
        requested_diligence: Optional[str] = None

        # Standard fields mapping
        for field in extraction.fields:
            if field.status in (FieldStatus.NOT_FOUND, FieldStatus.UNCERTAIN) and not field.value:
                continue

            if field.field_name == "ruc" and field.value:
                ruc_val = field.value
            elif field.field_name == "requesting_unit" and field.value:
                requesting_unit = field.value
            elif field.field_name == "requesting_rut" and field.value:
                requesting_rut = field.value
            elif field.field_name == "oficio_number" and field.value:
                oficio_number = field.value
            elif field.field_name == "petition_date" and field.value:
                petition_date = field.value
            elif field.field_name == "city" and field.value:
                city = field.value
            elif field.field_name == "prosecutor_office" and field.value:
                prosecutor_office = field.value
            elif field.field_name == "prosecutor_name" and field.value:
                prosecutor_name = field.value
            elif field.field_name == "investigator_name" and field.value:
                investigator_name = field.value
            elif field.field_name == "crime_context" and field.value:
                crime_context = field.value
            elif field.field_name == "requested_diligence" and field.value:
                requested_diligence = field.value

        if not ruc_val:
            raise PetitionExtractionConflictError("No se puede generar el borrador sin un RUC confirmado.")

        # Collect and deduplicate NUEs from evidence_items AND fields
        nues_map: Dict[str, DraftNue] = {}

        # 1. From evidence items
        if extraction.evidence_items:
            for item in extraction.evidence_items:
                if item.nue_number:
                    num = item.nue_number.strip()
                    if num and num not in nues_map:
                        attrs = {}
                        if item.brand_declared:
                            attrs["brand"] = item.brand_declared
                        if item.model_declared:
                            attrs["model"] = item.model_declared
                        if item.serial_number_declared:
                            attrs["serial"] = item.serial_number_declared

                        nues_map[num] = DraftNue(
                            nue_number=num,
                            description_from_petition=item.description_original,
                            quantity=item.quantity or 1,
                            attributes_from_petition=attrs if attrs else None,
                            source="PETITION"
                        )

        # 2. From fields (if nue field present and not yet in map)
        for field in extraction.fields:
            if field.field_name == "nue" and field.value:
                num = field.value.strip()
                if num and num not in nues_map:
                    desc_val = next((f.value for f in extraction.fields if f.field_name == "evidence_description"), None)
                    nues_map[num] = DraftNue(
                        nue_number=num,
                        description_from_petition=desc_val,
                        quantity=1,
                        source="PETITION"
                    )

        nues_list = list(nues_map.values())
        if not nues_list:
            raise PetitionExtractionConflictError("No se puede generar el borrador sin al menos 1 NUE confirmada.")

        # Requested actions
        req_actions_list = []
        if extraction.requested_actions:
            for act in extraction.requested_actions:
                req_actions_list.append({
                    "action_order": act.action_order,
                    "source_text": act.source_text,
                    "normalized_action": act.normalized_action,
                    "source": "PETITION"
                })

        return CaseStructureDraft(
            ruc=ruc_val,
            nues=nues_list,
            requesting_unit=requesting_unit,
            requesting_rut=requesting_rut,
            oficio_number=oficio_number or next((f.value for f in extraction.fields if f.field_name == "petition_number"), None),
            petition_date=petition_date,
            city=city,
            prosecutor_office=prosecutor_office,
            prosecutor_name=prosecutor_name,
            investigator_name=investigator_name,
            crime_context=crime_context,
            requested_diligence=requested_diligence,
            requested_actions=req_actions_list,
            petition_id=extraction.document_id,
            petition_sha256=extraction.document_sha256,
            petition_number=oficio_number or next((f.value for f in extraction.fields if f.field_name == "petition_number"), None),
            source="PETITION",
            status="DRAFT_PROPOSED",
            notes="La estructura física de especies y dispositivos de almacenamiento aún debe ser confirmada."
        )

