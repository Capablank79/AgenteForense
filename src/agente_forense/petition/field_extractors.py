"""
Deterministic field extraction from petition text (RUC, NUE, Oficio, Evidences, Actions, Attachments, etc.).
"""
import re
from typing import List, Tuple, Optional, Dict, Any
from agente_forense.petition.models import (
    ExtractedField, FieldProvenance, FieldStatus,
    PetitionEvidenceItemDeclared, PetitionRequestedActionDeclared, PetitionAttachmentDeclared
)

# Patterns for scalar fields
RUC_PATTERNS = [
    r"(?:RUC|R\.U\.C\.?)\s*[:#-]?\s*([0-9]{7,10}-[0-9Kk])",
    r"(?:RUC|R\.U\.C\.?)\s*[:#-]?\s*([0-9]{9,11})",
    r"\b([0-9]{7,10}-[0-9Kk])\b"
]

NUE_PATTERNS = [
    r"(?:NUE|N\.U\.E\.?)\s*[:#-]?\s*([0-9]{6,10})",
    r"NUE([0-9]{6,10})",
    r"\bNUE\s*([0-9]{6,10})\b"
]

OFICIO_PATTERNS = [
    r"(?:OFICIO|ORD\.?|OF\.?)\s*(?:[A-ZÁÉÍÓÚÑ]+\s+)*N?[º°\.\s:]*([0-9]{1,10}(?:[-/][0-9]{2,4})?)",
]

FECHA_PATTERNS = [
    r"(?:FECHA|SANTIAGO,|VALPARAÍSO,|CONCEPCIÓN,|[A-ZÁÉÍÓÚÑ]+,)\s*([0-9]{1,2}\s+DE\s+[A-ZÁÉÍÓÚÑ]+\s+DE\s+[0-9]{4})",
    r"\b([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})\b",
    r"\b([0-9]{1,2}\s+(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\.?\s+[0-9]{4})\b"
]

CIUDAD_PATTERNS = [
    r"\b(SANTIAGO|VALPARAÍSO|CONCEPCIÓN|ANTOFAGASTA|TEMUCO|RANCAGUA|TALCA|IQUIQUE|PUERTO MONTT|LA SERENA|COPIAPÓ|ARICA|VALDIVIA|COYHAIQUE|PUNTA ARENAS)\b"
]

REQUESTING_UNIT_PATTERNS = [
    r"(?:UNIDAD\s+SOLICITANTE|UNIDAD|SOLICITANTE)\s*[:#-]?\s*([^\n\r]+)",
]

PROSECUTOR_OFFICE_PATTERNS = [
    r"(?:FISCALÍA|FISCALIA)\s+([^\n\r,]+)",
]

PROSECUTOR_NAME_PATTERNS = [
    r"(?:FISCAL)\s*:\s*([A-ZÁÉÍÓÚÑ\s]{3,40})",
]

INVESTIGATOR_PATTERNS = [
    r"(?:INVESTIGADOR|ENCARGADO|INSPECTOR|OFICIAL)\s*[:#-]?\s*([^\n\r]+)",
]

CRIME_CONTEXT_PATTERNS = [
    r"(?:DELITO|CAUSA|INVESTIGACIÓN\s+POR)\s*[:#-]?\s*([^\n\r]+)",
]

BITACORA_PATTERNS = [
    r"(?:BITÁCORA|BITACORA)(?:\s+WEB)?\s*N?[º°\.\s:]*([0-9A-Z-]+)",
]


class FieldExtractor:
    def extract_fields_from_pages(
        self,
        source_doc_id: str,
        pages_text: List[Tuple[int, str, str]]  # list of (page_index, raw_text, extraction_method)
    ) -> Tuple[List[ExtractedField], List[PetitionEvidenceItemDeclared], List[PetitionRequestedActionDeclared], List[PetitionAttachmentDeclared]]:
        """
        Extracts structured fields, declared evidence items, requested actions, and attachments deterministically.
        """
        extracted_fields: List[ExtractedField] = []
        evidence_items: List[PetitionEvidenceItemDeclared] = []
        requested_actions: List[PetitionRequestedActionDeclared] = []
        attachments: List[PetitionAttachmentDeclared] = []

        # Store matches per field: key -> list of (value, page_idx, snippet, method)
        raw_matches: Dict[str, List[Tuple[str, int, str, str]]] = {
            "ruc": [],
            "nue": [],
            "oficio_number": [],
            "petition_date": [],
            "city": [],
            "requesting_unit": [],
            "prosecutor_office": [],
            "prosecutor_name": [],
            "investigator_name": [],
            "crime_context": [],
            "log_reference": []
        }

        for page_idx, raw_txt, method in pages_text:
            lines = raw_txt.splitlines()

            # 1. Scalar regex extractions
            self._extract_regex(raw_matches["ruc"], RUC_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["nue"], NUE_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["oficio_number"], OFICIO_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["petition_date"], FECHA_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["city"], CIUDAD_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["requesting_unit"], REQUESTING_UNIT_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["prosecutor_office"], PROSECUTOR_OFFICE_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["prosecutor_name"], PROSECUTOR_NAME_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["investigator_name"], INVESTIGATOR_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["crime_context"], CRIME_CONTEXT_PATTERNS, raw_txt, page_idx, method)
            self._extract_regex(raw_matches["log_reference"], BITACORA_PATTERNS, raw_txt, page_idx, method)

            # 2. Extract Evidence Items declared
            # Pattern: N.U.E. 7746537 : 01 Computador portátil, marca Lenovo, E-41-55, Nro de serie MPIZGTX4
            for line in lines:
                l_strip = line.strip()
                if any(kw in l_strip.upper() for kw in ["NUE", "EVIDENCIA", "ESPECIE", "MARCA", "SERIE"]):
                    ev_item = self._parse_evidence_line(l_strip, page_idx + 1)
                    if ev_item:
                        evidence_items.append(ev_item)

            # 3. Extract Requested Actions (Diligencias)
            # Lines matching SOLICITA, PERITAJE, EXTRACCIÓN, COPIA, ANALISIS
            action_order = 1
            for line in lines:
                l_strip = line.strip()
                if l_strip.rstrip(":").upper() in ["DILIGENCIAS SOLICITADAS", "DILIGENCIAS", "SOLICITA", "SE SOLICITA"]:
                    continue
                l_upper = l_strip.upper()
                if any(kw in l_upper for kw in ["SOLICITA", "DILIGENCIA", "PERITAJE", "EXTRACCIÓN", "EXTRACCION", "ANALIZAR", "PERICIAR"]):
                    if len(l_strip) > 10:
                        requested_actions.append(PetitionRequestedActionDeclared(
                            source_text=l_strip,
                            normalized_action=l_strip.upper(),
                            action_order=action_order,
                            source_page=page_idx + 1
                        ))
                        action_order += 1

            # 4. Extract Attachments / Actas
            for line in lines:
                l_strip = line.strip()
                if l_strip.rstrip(":").upper() in ["ANEXOS", "ACTAS", "ANEXOS / ACTAS", "ACTAS / ANEXOS"]:
                    continue
                l_upper = l_strip.upper()
                if any(kw in l_upper for kw in ["ACTA", "ANEXO", "CADENA DE CUSTODIA", "ADJUNTO"]):
                    if len(l_strip) > 5:
                        att_type = "ACTA" if "ACTA" in l_upper else ("ANEXO" if "ANEXO" in l_upper else "DOCUMENTO")
                        attachments.append(PetitionAttachmentDeclared(
                            attachment_type=att_type,
                            description=l_strip,
                            reference_number=None,
                            source_page=page_idx + 1,
                            physically_received=False
                        ))

        # Build ExtractedField objects with provenance and status handling
        for field_name, matches in raw_matches.items():
            if not matches:
                extracted_fields.append(ExtractedField(
                    field_name=field_name,
                    value=None,
                    normalized_value=None,
                    status=FieldStatus.NOT_FOUND,
                    provenance=[],
                    confidence=None
                ))
            else:
                unique_vals = list({m[0] for m in matches})
                # Check requesting_unit overflow protection (reject full page / > 200 chars)
                first_val = matches[0][0]
                if field_name == "requesting_unit" and len(first_val) > 150:
                    status = FieldStatus.UNCERTAIN
                elif len(unique_vals) > 1:
                    status = FieldStatus.CONFLICT
                else:
                    status = FieldStatus.EXTRACTED

                provs = [
                    FieldProvenance(
                        source_document_id=source_doc_id,
                        page_index=m[1],
                        source_text=m[2],
                        extraction_method=m[3]
                    ) for m in matches
                ]

                # Date normalization check
                norm_val = first_val
                if field_name == "petition_date":
                    norm_val = self._normalize_date(first_val)
                    if "?" in first_val or not norm_val:
                        status = FieldStatus.UNCERTAIN

                extracted_fields.append(ExtractedField(
                    field_name=field_name,
                    value=first_val,
                    normalized_value=norm_val,
                    status=status,
                    provenance=provs,
                    confidence=None
                ))

        return extracted_fields, evidence_items, requested_actions, attachments

    def _extract_regex(self, target_list: List[Tuple[str, int, str, str]], patterns: List[str], text: str, page_idx: int, method: str):
        for pat in patterns:
            matches = list(re.finditer(pat, text, re.IGNORECASE))
            for match in matches:
                val = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else match.group(0).strip()
                target_list.append((val, page_idx, match.group(0), method))
            if matches:
                break

    def _parse_evidence_line(self, line: str, page_num: int) -> Optional[PetitionEvidenceItemDeclared]:
        line_str = line.strip()
        if len(line_str) < 10:
            return None

        if line_str.rstrip(":").upper() in ["EVIDENCIAS DECLARADAS", "EVIDENCIAS", "ESPECIES DECLARADAS", "ESPECIES"]:
            return None

        # Try to find NUE number in line
        nue_match = re.search(r"(?:NUE|N\.U\.E\.?)\s*[:#-]?\s*([0-9]{6,10})", line_str, re.IGNORECASE)
        nue_num = nue_match.group(1) if nue_match else None

        # Try to find brand
        brand_match = re.search(r"(?:MARCA)\s*[:#-]?\s*([A-Z0-9_-]+)", line_str, re.IGNORECASE)
        brand = brand_match.group(1) if brand_match else None

        # Try to find model
        model_match = re.search(r"(?:MODELO)\s*[:#-]?\s*([A-Z0-9_-]+)", line_str, re.IGNORECASE)
        model = model_match.group(1) if model_match else None

        # Try to find serial
        serial_match = re.search(r"(?:SERIE|S/N|NRO DE SERIE|Nº DE SERIE)\s*[:#-]?\s*([A-Z0-9_-]+)", line_str, re.IGNORECASE)
        serial = serial_match.group(1) if serial_match else None

        # Try to find quantity
        qty_match = re.search(r"\b(0?[1-9]|[1-9][0-9])\b\s+(?:UNIDAD|COMPUTADOR|DISCO|TELÉFONO|TELEFONO|EQUIPO|NOTEBOOK|CELULAR)", line_str, re.IGNORECASE)
        qty = int(qty_match.group(1)) if qty_match else 1

        # Try to find capacity
        cap_match = re.search(r"\b([0-9]+\s*(?:GB|TB|MB))\b", line_str, re.IGNORECASE)
        capacity = cap_match.group(1) if cap_match else None

        return PetitionEvidenceItemDeclared(
            nue_number=nue_num,
            quantity=qty,
            description_original=line_str,
            evidence_type_declared=None,
            brand_declared=brand,
            model_declared=model,
            serial_number_declared=serial,
            capacity_declared=capacity,
            source_page=page_num,
            source_text=line_str
        )

    def _normalize_date(self, date_str: str) -> Optional[str]:
        # Simple date normalizer e.g., '21 AGO. 2026' -> '2026-08-21'
        months = {
            "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
            "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12"
        }
        upper_d = date_str.upper()
        for m_name, m_num in months.items():
            if m_name in upper_d:
                parts = re.findall(r"\d+", date_str)
                if len(parts) >= 2:
                    day = parts[0].zfill(2)
                    year = parts[-1]
                    if len(year) == 4:
                        return f"{year}-{m_num}-{day}"
        return date_str
