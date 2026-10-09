"""
Extractor determinista de atributos y normalización segura.
"""

import re
from typing import Dict, Any, Optional, Tuple
from agente_forense.identification.models import AttributeValue, AttributeStatus, AttributeProvenance

KNOWN_BRANDS = [
    "WESTERN DIGITAL", "WD", "SEAGATE", "TOSHIBA", "SAMSUNG", "KINGSTON",
    "CRUCIAL", "SANDISK", "INTEL", "CORSAIR", "HP", "DELL", "LENOVO",
    "ASUS", "ACER", "APPLE", "HITACHI", "MAXTOR", "FUJITSU", "SONY", "LG"
]

def extract_deterministic_attributes(ocr_text: str, photo_id: str) -> Dict[str, AttributeValue]:
    """
    Extrae candidatos deterministas mediante expresiones regulares sobre el texto OCR.
    Campos: brand, model, serial, capacity, visible_labels, part_number, imei, mac_address.
    """
    attributes: Dict[str, AttributeValue] = {}
    if not ocr_text:
        return attributes

    text_upper = ocr_text.upper()

    # 1. Serial Number
    serial_match = re.search(
        r"(?:S/N|SERIAL(?:\s*NO|\s*NUMBER)?|SN|N/S)[:\s=]*([A-Z0-9\?\-_]{4,30})",
        text_upper
    )
    if serial_match:
        val = serial_match.group(1).strip()
        status = AttributeStatus.UNCERTAIN.value if "?" in val else AttributeStatus.EXTRACTED.value
        attributes["serial"] = AttributeValue(
            field_name="serial",
            value=val,
            normalized_value=val,
            status=status,
            provenance=AttributeProvenance(
                field_name="serial",
                value=val,
                source_photo_id=photo_id,
                source_text=serial_match.group(0),
                method="REGEX",
                status=status
            )
        )

    # 2. Brand
    for b in KNOWN_BRANDS:
        # Match exact word
        pattern = r"\b" + re.escape(b) + r"\b"
        if re.search(pattern, text_upper):
            attributes["brand"] = AttributeValue(
                field_name="brand",
                value=b,
                normalized_value=b,
                status=AttributeStatus.EXTRACTED.value,
                provenance=AttributeProvenance(
                    field_name="brand",
                    value=b,
                    source_photo_id=photo_id,
                    source_text=b,
                    method="REGEX",
                    status=AttributeStatus.EXTRACTED.value
                )
            )
            break

    # 3. Model
    model_match = re.search(
        r"(?:MODEL|MODELO|MDL|M/N)[:\s=]*([A-Z0-9\-_]{3,25})",
        text_upper
    )
    if model_match:
        m_val = model_match.group(1).strip()
        attributes["model"] = AttributeValue(
            field_name="model",
            value=m_val,
            normalized_value=m_val,
            status=AttributeStatus.EXTRACTED.value,
            provenance=AttributeProvenance(
                field_name="model",
                value=m_val,
                source_photo_id=photo_id,
                source_text=model_match.group(0),
                method="REGEX",
                status=AttributeStatus.EXTRACTED.value
            )
        )

    # 4. Capacity
    cap_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(GB|TB|MB)",
        text_upper
    )
    if cap_match:
        raw_cap = cap_match.group(0).strip()
        num_str = cap_match.group(1)
        unit = cap_match.group(2)
        norm_cap, bytes_val = normalize_capacity(num_str, unit)
        attributes["capacity"] = AttributeValue(
            field_name="capacity",
            value=raw_cap,
            normalized_value=norm_cap,
            bytes_value=bytes_val,
            status=AttributeStatus.EXTRACTED.value,
            provenance=AttributeProvenance(
                field_name="capacity",
                value=raw_cap,
                source_photo_id=photo_id,
                source_text=raw_cap,
                method="REGEX",
                status=AttributeStatus.EXTRACTED.value
            )
        )

    # 5. Part Number
    pn_match = re.search(
        r"(?:P/N|PART\s*NO|PART\s*NUMBER)[:\s=]*([A-Z0-9\-_]{4,25})",
        text_upper
    )
    if pn_match:
        pn_val = pn_match.group(1).strip()
        attributes["part_number"] = AttributeValue(
            field_name="part_number",
            value=pn_val,
            normalized_value=pn_val,
            status=AttributeStatus.EXTRACTED.value,
            provenance=AttributeProvenance(
                field_name="part_number",
                value=pn_val,
                source_photo_id=photo_id,
                source_text=pn_match.group(0),
                method="REGEX",
                status=AttributeStatus.EXTRACTED.value
            )
        )

    # 6. IMEI
    imei_match = re.search(
        r"(?:IMEI)[:\s=]*(\d{15})",
        text_upper
    )
    if imei_match:
        imei_val = imei_match.group(1).strip()
        attributes["imei"] = AttributeValue(
            field_name="imei",
            value=imei_val,
            normalized_value=imei_val,
            status=AttributeStatus.EXTRACTED.value,
            provenance=AttributeProvenance(
                field_name="imei",
                value=imei_val,
                source_photo_id=photo_id,
                source_text=imei_match.group(0),
                method="REGEX",
                status=AttributeStatus.EXTRACTED.value
            )
        )

    # 7. MAC Address
    mac_match = re.search(
        r"(?:MAC)[:\s=]*([0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2})",
        text_upper
    )
    if mac_match:
        mac_val = mac_match.group(1).strip()
        attributes["mac_address"] = AttributeValue(
            field_name="mac_address",
            value=mac_val,
            normalized_value=mac_val,
            status=AttributeStatus.EXTRACTED.value,
            provenance=AttributeProvenance(
                field_name="mac_address",
                value=mac_val,
                source_photo_id=photo_id,
                source_text=mac_match.group(0),
                method="REGEX",
                status=AttributeStatus.EXTRACTED.value
            )
        )

    return attributes


def normalize_capacity(num_str: str, unit: str) -> Tuple[str, int]:
    """
    Normaliza capacidad a formato canónico 'N GB' o 'N TB' y calcula bytes exactos.
    """
    val = float(num_str)
    unit = unit.upper()

    if unit == "MB":
        bytes_val = int(val * 1024 * 1024)
        norm_str = f"{int(val) if val.is_integer() else val} MB"
    elif unit == "GB":
        bytes_val = int(val * 1000 * 1000 * 1000)  # Standard storage decimal or binary (1000^3)
        norm_str = f"{int(val) if val.is_integer() else val} GB"
    elif unit == "TB":
        bytes_val = int(val * 1000 * 1000 * 1000 * 1000)
        norm_str = f"{int(val) if val.is_integer() else val} TB"
    else:
        bytes_val = int(val)
        norm_str = f"{val} {unit}"

    return norm_str, bytes_val
