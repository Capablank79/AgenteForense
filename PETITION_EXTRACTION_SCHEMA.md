# PETITION_EXTRACTION_SCHEMA.md — Esquema de Artefactos de Extracción Petitoria

## 1. Estructura de `extraction.json`

Cada petitorio procesado genera un artefacto `extraction.json` dentro del directorio de derivados de `FileStore`, cuyo esquema cumple el siguiente formato:

```json
{
  "document_id": "doc_uuid_12345",
  "document_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "processing_method": "WINDOWS_OCR_SCANNED_PDF",
  "pages": [
    {
      "page_index": 0,
      "method": "WINDOWS_OCR",
      "raw_text": "RUC: 12345678-9\nNUE: 777777",
      "normalized_text": "RUC: 12345678-9 NUE: 777777"
    }
  ],
  "fields": [
    {
      "field_name": "ruc",
      "value": "12345678-9",
      "normalized_value": "12345678-9",
      "page_index": 0,
      "source_text": "RUC: 12345678-9",
      "extraction_method": "REGEX_DETERMINISTIC",
      "status": "EXTRACTED",
      "confidence": null
    },
    {
      "field_name": "nue",
      "value": "777777",
      "normalized_value": "777777",
      "page_index": 0,
      "source_text": "NUE: 777777",
      "extraction_method": "REGEX_DETERMINISTIC",
      "status": "EXTRACTED",
      "confidence": null
    }
  ],
  "conflicts": [],
  "review_status": "REVIEW_REQUIRED",
  "created_at": "2026-10-07T12:00:00Z",
  "tool_versions": {
    "python": "3.10.11",
    "pypdf": "5.3.0",
    "winsdk": "1.0.0b10",
    "pillow": "12.3.0",
    "ocr_language": "es-ES"
  }
}
```

## 2. Definición de Campos y Provenance
- **`confidence`**: Siempre `null` si la herramienta de OCR no suministra una métrica probada de confianza a nivel de token. Prohibido fabricar un valor numérico ficticio.
- **`status`**:
  - `EXTRACTED`: Extraído por motor determinista.
  - `CONFIRMED`: Verificado sin cambios por el usuario.
  - `CORRECTED_BY_HUMAN`: Editado manualmente por el usuario.
  - `CONFLICT`: Presenta múltiples discrepancias.
  - `NOT_FOUND`: No identificado en el documento.

## 3. Tool Versions Audit
Se persisten en la tabla `forensic.tool_versions` y en el JSON del borrador para trazabilidad forense completa.
