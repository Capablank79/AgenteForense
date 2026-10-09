# PETITION_PIPELINE_ARCHITECTURE.md — Arquitectura del Pipeline Petitorio OCR y Draft

## 1. Visión General
El módulo de Pipeline Petitorio (`agente_forense.petition`) procesa oficios petitorios desde la interfaz web o API REST, convirtiendo documentos heterogéneos en propuestas estructuradas (`CaseStructureDraft`) sin alterar la inmutabilidad de la evidencia original y garantizando la revisión humana obligatoria (fail-closed).

## 2. Flujo de Datos y Pipeline
```text
PETITORIO ORIGINAL (PDF / JPG / PNG)
  │
  ├─► 1. STAGING CONTROLADO & VERIFICACIÓN SHA-256 PRE-PROCESAMIENTO
  │
  ├─► 2. DETECCIÓN DE FORMATO & RUTA DE EXTRACCIÓN:
  │      ├─► PDF Textual  ─► pypdf (sin OCR)
  │      ├─► PDF Escaneado─► Windows.Data.Pdf ─► Render ─► Windows OCR (es-ES)
  │      └─► Imagen JPG/PNG─► SoftwareBitmap ─► Windows OCR (es-ES)
  │
  ├─► 3. VERIFICACIÓN SHA-256 POST-PROCESAMIENTO (Inmutabilidad garantizada)
  │
  ├─► 4. NORMALIZACIÓN DE TEXTO & REGISTRO DE PROVENANCE (Raw + Normalized)
  │
  ├─► 5. EXTRACCIÓN DETERMINISTA DE CAMPOS (Regex RUC, NUE, Oficio, Unidad)
  │
  ├─► 6. DETECCIÓN DE CONFLICTOS Y REVISIÓN HUMANA OBLIGATORIA (REVIEW_REQUIRED)
  │
  └─► 7. GENERACIÓN DE DRAFT (CaseStructureDraft / PetitionCaseDraft)
```

## 3. Componentes Principales
- **`detector.py`**: Evalúa si un PDF posee una capa de texto utilizable (`TEXT_LAYER_USABLE`) usando `pypdf`, o si requiere rasterización y OCR local.
- **`text_extractors.py`**: Extractor especializado basado en `pypdf` para documentos vectoriales/textuales.
- **`pdf_renderer.py` & `ocr.py`**: Renderizado de páginas PDF a stream BGRA8 con `Windows.Data.Pdf` y posterior reconocimiento óptico con `Windows.Media.Ocr` (`es-ES`) vía `winsdk`.
- **`field_extractors.py`**: Reglas deterministas y expresiones regulares ajustadas para RUC chileno (con/sin guion, DV K/k), NUEs concatenadas por OCR (`NUE777777`), números de Oficio y unidades solicitantes.
- **`conflicts.py`**: Evaluador de inconsistencias que fuerza el estado `REVIEW_REQUIRED` ante múltiples valores, ausencia de RUC/NUE o fallos de OCR.
- **`service.py` & `persistence.py`**: Servicio de negocio y persistencia que interactúa con PostgreSQL (`forensic.files`, `forensic.documents`, `forensic.hashes`, `forensic.audit_events`) y almacena artefactos derivados en `FileStore`.

## 4. Garantías de Seguridad e Inmutabilidad
- **SHA-256 Check**: `SHA256_BEFORE == SHA256_AFTER`. Ante cualquier discrepancia se aborta con `PetitionIntegrityError`.
- **No Creación Automática de Casos**: `build-draft` genera un borrador intermedio. No invoca `create_case()` ni modifica la estructura definitiva del caso sin confirmación explícita.
- **Sin Invención Semántica**: Si un campo no está explícito (ej. topología física, DSM, especies), permanece `NOT_FOUND` / `REVIEW_REQUIRED`.
