# PETITION PIPELINE CAPABILITIES & SPECIFICATION
# Project: AGENTE FORENSE
# Sprint: SPRINT_R05 — Investigación del Pipeline Petitorio -> OCR -> CaseStructureDraft

---

## 1. BASELINE

- **PYTHON**: 3.10.11 (`.venv\Scripts\python.exe`)
- **POSTGRESQL**: 18.6 (Listening on `127.0.0.1:5433`, DB: `agente_forense_db`)
- **WEB SERVER**: FastAPI / Uvicorn listening on `127.0.0.1:8085`
- **TEST SUITE**: 108 passed (0 failures)
- **ORCHESTRATION STATUS**: `ORCHESTRATION_FOUNDATION_READY`
- **GIT BRANCH / COMMIT**: `main` / `e1bf433 Sprint R00: inicializa reconstruccion tecnica desde cero`

---

## 2. DOCUMENT FORMATS

Investigación y caracterización de formatos soportables en el pipeline petitorio:

1. **PDF con capa de texto (Digital native PDF)**:
   - Contiene streams de texto vectoriales/fuentes embebidas.
   - Ruta óptima: Extracción directa de texto mediante librerías Python de parsing. No requiere OCR.
2. **PDF escaneado (Image-only / Raster PDF)**:
   - Contiene páginas codificadas como imágenes (JPEG/PNG/CCITT).
   - Ruta óptima: Renderizado de páginas a imágenes -> OCR motor local -> texto normalizado.
3. **JPG / JPEG**:
   - Formato de imagen estándar para capturas o escaneos fotográficos de oficios.
   - Ruta óptima: Ingesta directa -> preprocesamiento (escalado/grises) -> OCR local -> texto normalizado.
4. **PNG**:
   - Formato de imagen sin pérdida.
   - Ruta óptima: Ingesta directa -> OCR local -> texto normalizado.
5. **TIFF**:
   - Formato multipágina de escáneres institucionales (si aplica en el futuro).

---

## 3. LOCAL PDF EXTRACTORS INVENTORY

Estado real verificado en la máquina local (`Python 3.10.11` en `.venv`):

- **PyMuPDF (`fitz`)**: `NOT_INSTALLED`
- **pypdf**: `NOT_INSTALLED`
- **pdfplumber**: `NOT_INSTALLED`
- **pdfminer.six**: `NOT_INSTALLED`
- **pypdfium2**: `NOT_INSTALLED`

*Conclusión / Selección para R05.1*: Para la extracción determinista de PDFs digitales nativos sin dependencias C++ pesadas, se preselecciona `pypdf` (o `pypdfium2` / `PyMuPDF`) como dependencia candidata para instalar en **Sprint R05.1**.

---

## 4. LOCAL OCR ENGINES INVENTORY

Estado real inventariado en el sistema operativo Windows 11 / Entorno local:

| Motor OCR / VLM | Estado | Versión | Ruta / Interfaz | Idiomas | Modo Offline | Licencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Windows OCR (Media.Ocr)** | **INSTALLED** | WinRT / Win11 Native | `Windows.Media.Ocr.OcrEngine` (PowerShell / WinRT C# / C++) | `es-ES`, `es-MX` (Verificados) | 100% Offline | Propietaria (Windows OS) |
| **Tesseract OCR** | **NOT_INSTALLED** | N/A | No encontrado en PATH / CLI | N/A | Offline | Apache 2.0 |
| **PaddleOCR** | **NOT_INSTALLED** | N/A | Python module not installed | N/A | Offline | Apache 2.0 |
| **EasyOCR** | **NOT_INSTALLED** | N/A | Python module not installed | N/A | Offline | Apache 2.0 |
| **Ollama (Qwen2.5:3b)** | **INSTALLED** | 0.40.0 | HTTP API (`http://localhost:11434`), CLI | Español / Multilingüe | 100% Offline | Apache 2.0 |

---

## 5. WINDOWS OCR DETAILS

- **Versión de OS**: Windows 11 Build con Runtime UWP/WinRT nativo.
- **APIs accesibles**: `Windows.Media.Ocr.OcrEngine` accesible nativamente vía COM/WinRT (PowerShell, C#, C++, o paquete Python `winsdk` / `winrt-sdk`).
- **Soporte de Español**: Verificado en el sistema: `es-ES` (Español España) y `es-MX` (Español México) instalados y listos.
- **Restricciones**: Operación nativa local de alta velocidad y cero consumo de API externa. Requiere puente de llamada (vía subproceso PowerShell / ejecutable helper C# / bindings `winsdk`).
- **Comportamiento sin internet**: 100% Offline, no realiza peticiones salientes.

---

## 6. TESSERACT DETAILS

- **Estado**: `NOT_INSTALLED`. `where tesseract` no encontró ningún ejecutable.
- **Acción R05.1**: Si se requiere un fallback secundario independiente de Windows, se considerará la instalación de Tesseract 5.x con lenguaje `spa.traineddata`.

---

## 7. OLLAMA / QWEN INVENTORY

- **Servicio Ollama**: Versión `0.40.0` activa y ejecutándose localmente.
- **Modelo presente**: `qwen2.5:3b` (Digest: `357c53fb659c`, Tamaño: 1.9 GB, Quantization: `Q4_K_M`, Context Length: `32768`).
- **Capacidades del modelo**: Modelo de lenguaje (LLM) de texto (`capabilities: ['completion', 'tools']`). NO es un modelo Multimodal/Visión (no procesa imágenes directamente).
- **Uso previsto**: Apoyo exclusivo para estructuración semántica, clasificación, resolución de ambigüedades y formateo JSON a schema a partir del texto ya extraído por OCR o parser PDF.

---

## 8. SELECTED TEXT EXTRACTOR & OCR ENGINE

### Selected Primary Text Extractor (Digital PDF)
- **Candidato Seleccionado**: `pypdf` (vía Python) para Sprint R05.1.
- **Razón**: Permite inspección estructurada de stream de texto, páginas y metadatos sin binarios pesados.

### Selected Primary OCR Engine (Scanned PDF & Images)
- **Motor Seleccionado**: **Windows Native OCR (`Windows.Media.Ocr`)**.
- **Razón**: Ya está **INSTALADO** en el sistema, cuenta con paquetes de idioma `es-ES` y `es-MX` verificados, ejecuta 100% offline y ofrece excelente rendimiento en Windows.

### Selected Fallback Engine
- **Motor Secundario**: **Tesseract OCR (5.x + `spa`)** o **Qwen2.5:3b (Ollama local)** para refinamiento de texto/extracción semántica.

---

## 9. PIPELINE BY INPUT TYPE

### A. PDF con Capa de Texto
```text
[PDF File] -> Hash SHA-256 & Validation -> Text Extractor (pypdf) -> Raw Text -> Normalizer -> Extraction Rules -> CaseStructureDraft
```

### B. PDF Escaneado
```text
[PDF File] -> Hash SHA-256 & Validation -> Render Pages to Images -> Windows OCR (es-ES) -> Raw Text -> Normalizer -> Extraction Rules -> CaseStructureDraft
```

### C. Imagen (JPG/PNG)
```text
[Image File] -> Hash SHA-256 & Validation -> Preprocess (Grayscale/Contrast) -> Windows OCR (es-ES) -> Raw Text -> Normalizer -> Extraction Rules -> CaseStructureDraft
```

---

## 10. SPANISH SUPPORT

- **Verificación**: Comprobada la presencia de los reconocedores de idioma `es-ES` y `es-MX` en el motor de OCR nativo de Windows.
- **Manejo de Caracteres**: Preservación estricta de acentos (`á, é, í, ó, ú`), diéresis (`ü`), eñes (`ñ, Ñ`), y caracteres legales/judiciales (`N°`, `N°`, `§`). Encodings normalizados siempre en `UTF-8`.

---

## 11. PROVENANCE MODEL

Cada dato extraído del petitorio mantendrá trazabilidad completa bajo la siguiente estructura JSON:

```json
{
  "field_name": "ruc",
  "value": "20123456789",
  "source_document": "OFICIO_4582_2026.pdf",
  "page": 1,
  "source_text_snippet": "RUC: 20123456789",
  "extraction_method": "DETERMINISTIC_REGEX",
  "confidence_score": 1.0,
  "status": "EXTRACTED"
}
```

Estados de Provenance: `OBSERVED`, `EXTRACTED`, `UNCERTAIN`, `CONFLICT`, `NOT_FOUND`.

---

## 12. FIELD MODEL

Campos extraíbles del oficio petitorio:

1. `ruc`: Registro Único de Causa (11 dígitos).
2. `nue`: Numeral Único de Evidencia (10 dígitos).
3. `requesting_unit`: Unidad Fiscal / Solicitante (ej. "Fiscalía Especializada...").
4. `requesting_rut` / `institutional_id`: RUT o ID de la autoridad peticionante.
5. `oficio_number`: Número/Código del Oficio Petitorio.
6. `oficio_date`: Fecha de emisión del petitorio.
7. `evidence_description`: Descripción física de las muestras/evidencias.
8. `requested_diligence`: Diligencia pericial solicitada (ej. Extracción / Análisis).
9. `perceptual_questions`: Preguntas periciales planteadas.
10. `observations`: Observaciones o plazos legales adicionales.

---

## 13. CONFLICT MODEL & RESOLUTION

Casos de conflicto identifcados y su manejo:

- **RUC Múltiple**: Se detectan dos RUCs distintos en el documento -> Marcar `CONFLICT` -> Requiere `HUMAN_REVIEW_REQUIRED`.
- **NUE Inconsistente / Invalida**: Formato no numérico o longitud != 10 -> Marcar `UNCERTAIN` -> `HUMAN_REVIEW_REQUIRED`.
- **Petitorio sin RUC o sin NUE**: Marcar estado del borrador como `INCOMPLETE_DRAFT` -> No se permite auto-persistencia.
- **Dos candidatos para Especie**: Marcar `REVIEW_REQUIRED`.

---

## 14. NORMALIZATION RULES

Reglas deterministas de normalización de texto:
1. **Espacios y Saltos de Línea**: Colapsar múltiples espacios y tabulaciones a un solo espacio (`\s+` -> ` `). Normalizar `\r\n` a `\n`.
2. **Artefactos OCR**: Limpieza de caracteres de control ilegibles manteniendo acentos en español.
3. **Guiones y Separadores**: Normalizar guiones tipográficos (`–`, `—`) a guion estándar (`-`).
4. **Preservación Dual**: Mantener siempre `raw_text` (original intacto) y `normalized_text` por separado.

---

## 15. CASESTRUCTUREDRAFT MAPPING

Mapeo de la extracción al contrato de dominio `CaseStructureDraft` existente (`agente_forense.domain.cases`):

```python
CaseStructureDraft(
    ruc=extracted_fields["ruc"].value,
    requesting_unit=extracted_fields["requesting_unit"].value,
    requesting_rut=extracted_fields["requesting_rut"].value,
    request_type=extracted_fields["requested_diligence"].value,
    nues=[
        NUEDraft(
            nue_number=extracted_fields["nue"].value,
            description_from_petition=extracted_fields["evidence_description"].value,
            species=[
                # Species & DSM drafts construidos asistidamente en revisión
            ]
        )
    ]
)
```

---

## 16. WEB FLOW (FUTURE DESIGN FOR R06+)

Flujo conceptual para la UI Web (`agente_forense.web`):

1. **Upload**: El usuario sube el archivo de oficio petitorio (PDF/JPG/PNG).
2. **Staging & Hashing**: Se calcula SHA-256 y se almacena en el FileStore aislado de staging.
3. **Processing**: Se ejecuta extracción de texto/OCR.
4. **Review Screen**: La Web muestra el PDF/Imagen al lado de los campos extraídos (`CaseStructureDraft` propuesto) indicando confianzas y posibles `CONFLICTS`.
5. **Human Approval**: El usuario confirma/edita los campos.
6. **Persist**: Se invoca el servicio de creación de caso en PostgreSQL.

---

## 17. API CONTRACT (FUTURE DESIGN FOR R06+)

Contratos conceptuales REST:

- `POST /api/petitions/stage` -> Ingesta y guardado de archivo en staging.
- `POST /api/petitions/{petition_id}/extract` -> Inicia pipeline de extracción/OCR.
- `GET  /api/petitions/{petition_id}/extraction` -> Obtiene los campos extraídos con provenance.
- `POST /api/petitions/{petition_id}/build-draft` -> Construye y valida `CaseStructureDraft`.

---

## 18. DATABASE IMPACT

- **PostgreSQL 18.6 Schema (`forensic`)**:
  - `forensic.files`: Soporta `file_role='PETITION'`.
  - `forensic.documents`: Permite registrar `document_type='PETITION'`, `ocr_status`, y `ocr_text`.
- **Modificaciones requeridas para R05.1**: Ninguna migración de estructura requerida; las tablas `files` y `documents` existentes satisfacen los requerimientos.

---

## 19. AUDIT EVENTS

Nuevos eventos de auditoría append-only para `forensic.audit_events`:

- `PETITION_STAGED`
- `PETITION_HASHED`
- `TEXT_EXTRACTED`
- `OCR_STARTED`
- `OCR_COMPLETED`
- `OCR_FAILED`
- `FIELDS_EXTRACTED`
- `FIELD_CONFLICT_DETECTED`
- `DRAFT_BUILT`
- `HUMAN_REVIEW_REQUIRED`

---

## 20. DEPENDENCIES FOR R05.1

Lista de paquetes candidatas a instalar en el entorno `.venv` durante el **Sprint R05.1**:

1. `pypdf` (o `pypdfium2`) -> Para lectura de PDF nativo.
2. `winsdk` (o binding WinRT equiv.) -> Para integración Python nativa con Windows OCR.
3. `Pillow` (`PIL`) -> Para manipulación de imágenes de páginas antes de OCR.

---

## 21. RISKS & BLOCKERS

- **Riesgos**:
  - Variabilidad de calidad en petitorios escaneados a mano o con firmas superpuestas sobre el RUC/NUE.
  - Dependencia del sistema operativo Windows para el motor `Windows.Media.Ocr` (mitigado por ser el entorno nativo de producción de la estación).
- **Blockers**:
  - Ninguno. El entorno cuenta con motor OCR local verificado y LLM local Ollama funcional.

---

## 22. STATUS CONCLUIDO

```text
PETITION_PIPELINE_CAPABILITIES_VERIFIED
```
