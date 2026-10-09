# ESQUEMA IDENTIFICATION.JSON (v1.0)

## Estructura Principal
El archivo `identification.json` se escribe de manera atómica (`tempfile` + `fsync` + `os.replace`) en el directorio de la entidad correspondiente.

```json
{
  "schema_version": 1,
  "entity_type": "SPECIES",
  "entity_id": "SPECIES-001",
  "entity_label": "Disco Duro Interno WD",
  "status": "IDENTIFICATION_PENDING",
  "photos": [
    {
      "photo_id": "PHOTO-A1B2C3D4",
      "entity_type": "ESPECIE",
      "entity_id": "SPECIES-001",
      "original_filename": "photo_serial.jpg",
      "relative_path": "photos/NUE_777777_ESPECIE1_SERIAL_01.jpg",
      "size_bytes": 124500,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "width": 600,
      "height": 200,
      "format": "JPEG",
      "classification": "SERIAL",
      "classification_final": "SERIAL",
      "ocr_text": "WESTERN DIGITAL MODEL WD10EZEX S/N: WCC6Y0123456 1.0 TB",
      "analysis_status": "ANALYZED",
      "captured_at": "2026-10-07T12:00:00Z"
    }
  ],
  "attributes": {
    "serial": {
      "field_name": "serial",
      "value": "WCC6Y0123456",
      "normalized_value": "WCC6Y0123456",
      "bytes_value": null,
      "status": "EXTRACTED",
      "provenance": {
        "field_name": "serial",
        "value": "WCC6Y0123456",
        "source_photo_id": "PHOTO-A1B2C3D4",
        "source_text": "S/N: WCC6Y0123456",
        "method": "REGEX",
        "status": "EXTRACTED",
        "confidence": null,
        "human_confirmed": false
      }
    }
  },
  "conflicts": [
    {
      "code": "NO_VISION_PROVIDER",
      "description": "Sin VLM disponible en el sistema local. Atributos como color y daños requieren revisión humana o etiquetas explícitas.",
      "severity": "WARNING",
      "affected_fields": ["color"],
      "photo_ids": []
    }
  ],
  "human_review": {
    "reviewed": true,
    "reviewed_by": "Perito Forense",
    "reviewed_at": "2026-10-07T12:05:00Z",
    "confirmed": true
  },
  "tool_versions": {
    "ocr_engine": "Windows.Media.Ocr es-ES (winsdk 1.0.0b10)",
    "llm_engine": "qwen2.5:3b (Text-Only via Ollama)"
  },
  "timestamps": {
    "created_at": "2026-10-07T12:00:00Z",
    "updated_at": "2026-10-07T12:05:00Z"
  }
}
```
