# SPRINT_R05_1 — Implementación Productiva del Pipeline Petitorio → OCR → CaseStructureDraft

## 1. Objetivo

Implementar el pipeline productivo local del AGENTE FORENSE para procesar un oficio petitorio desde la interfaz web y convertirlo en una propuesta estructurada reutilizando el dominio vigente:

```text
PETITORIO ORIGINAL
→ STAGING CONTROLADO
→ HASH SHA-256
→ DETECCIÓN DE TIPO
→ EXTRACCIÓN DE TEXTO / OCR LOCAL
→ RAW TEXT
→ NORMALIZED TEXT
→ EXTRACCIÓN DETERMINISTA DE CAMPOS
→ PROVENANCE
→ DETECCIÓN DE CONFLICTOS
→ REVISIÓN HUMANA
→ CaseStructureDraft
```

El pipeline debe soportar:

```text
PDF con capa de texto
PDF escaneado
JPG
JPEG
PNG
```

utilizando las capacidades verificadas:

```text
pypdf                    → PDFs con texto
Windows.Data.Pdf         → render de PDFs escaneados
Windows.Media.Ocr        → OCR local
winsdk 1.0.0b10          → bindings WinRT verificados
Pillow 12.3.0            → imágenes/fixtures
```

Este sprint NO debe crear automáticamente un caso definitivo a partir de OCR sin revisión humana.

Estado esperado:

```text
PETITION_PIPELINE_READY
```

---

## 2. Evidencia técnica ya validada

R05:

```text
Windows OCR disponible
es-ES y es-MX instalados
pypdf seleccionado para extracción PDF textual
Ollama 0.40.0 disponible
qwen2.5:3b = texto, NO visión
```

R05.0.1:

```text
Python 3.10.11
Windows 10 build 19045
winsdk 1.0.0b10
Windows.Media.Ocr
es-ES
RecognizeAsync real
3 ejecuciones exitosas
sin MSIX/package identity
```

R05.0.2:

```text
Windows.Data.Pdf
PdfDocument load
2 páginas
RenderToStreamAsync
SoftwareBitmap BGRA8
Windows OCR es-ES
9/9 tokens esperados
page provenance preservada
PDF SHA-256 intacto
```

No volver a investigar esos puntos salvo que el entorno real haya cambiado.

---

## 3. Documentación obligatoria

Antes de modificar código, TRAE debe leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md

SPRINT_R00.md
SPRINT_R01.md
SPRINT_R01_1.md
SPRINT_R02.md
SPRINT_R02_1.md
SPRINT_R03.md
SPRINT_R04.md
SPRINT_R05.md
SPRINT_R05_0_1_VALIDACION_WINDOWS_OCR.md
SPRINT_R05_0_2_VALIDACION_PDF_RENDER_OCR.md
SPRINT_R05_1.md

RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
PERSISTENCE_ARCHITECTURE.md
WEB_STACK_CAPABILITIES.md
WEB_ARCHITECTURE.md
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
PETITION_PIPELINE_CAPABILITIES.md
WINDOWS_OCR_RUNTIME_VALIDATION.md
PDF_RENDER_OCR_RUNTIME_VALIDATION.md
```

Revisar además reportes finales R00–R05.0.2.

---

## 4. Baseline esperado

```text
PYTHON:
3.10.11

WINDOWS:
Windows 10 Pro build 19045

POSTGRESQL:
18.6

DB:
agente_forense_db

DB HOST:
127.0.0.1

DB PORT:
5433

WEB:
127.0.0.1:8085

WINSDK:
1.0.0b10

PILLOW:
12.3.0

TESTS:
108 passed

ORCHESTRATION:
ORCHESTRATION_FOUNDATION_READY
```

Antes de modificar:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Si hay regresión:

```text
DETENER
DOCUMENTAR
NO IMPLEMENTAR
```

---

# 5. Dependencias

Instalar dentro de `.venv`:

```text
pypdf
```

`winsdk` y `Pillow` ya deben estar instalados por R05.0.1.

Registrar versiones exactas reales.

No instalar:

```text
PyMuPDF
Poppler
Ghostscript
Tesseract
PaddleOCR
EasyOCR
```

en este sprint.

---

# 6. Arquitectura del módulo Petitorio

Crear paquete desacoplado, por ejemplo:

```text
src/agente_forense/petition/
    __init__.py
    models.py
    errors.py
    detector.py
    text_extractors.py
    pdf_renderer.py
    ocr.py
    normalization.py
    field_extractors.py
    conflicts.py
    provenance.py
    draft_mapper.py
    service.py
```

Puede ajustarse si la arquitectura existente lo justifica.

No colocar toda la lógica en routes.

---

# 7. Modelos

Crear modelos explícitos equivalentes a:

```text
PetitionDocument
PetitionPageText
PetitionExtraction
ExtractedField
FieldProvenance
ExtractionConflict
PetitionProcessingResult
```

Usar type hints.

---

# 8. PetitionDocument

Debe representar, como mínimo:

```text
document_id
original_filename
stored_relative_path
size_bytes
sha256
extension
mime_observed
page_count
processing_status
created_at
```

No almacenar ruta absoluta como dato portable salvo donde internamente corresponda.

---

# 9. Estados de procesamiento

Definir estados explícitos:

```text
STAGED
HASHED
TEXT_EXTRACTION_PENDING
TEXT_EXTRACTED
OCR_PENDING
OCR_COMPLETED
FIELDS_EXTRACTED
REVIEW_REQUIRED
READY_FOR_DRAFT
FAILED
```

No confundirlos con estados globales del caso.

---

# 10. Ingesta

Implementar staging del petitorio desde Web/API.

Pipeline:

```text
UploadFile
→ validación tamaño
→ nombre seguro
→ staging
→ SHA-256
→ metadata
```

Reutilizar FileStore/hashing existentes cuando corresponda.

No cargar archivo completo en RAM.

---

# 11. Tamaño máximo

Agregar configuración específica o reutilizar:

```text
AGENTE_FORENSE_MAX_UPLOAD_BYTES
```

Mantener límite configurable.

Exceso:

```text
HTTP 413
```

Limpiar parcial de forma controlada.

---

# 12. Tipos aceptados

Aceptar únicamente:

```text
.pdf
.jpg
.jpeg
.png
```

en R05.1.

No aceptar TIFF todavía porque no fue parte del camino validado end-to-end.

Extensión y MIME son señales, no verdad absoluta.

---

# 13. Hash original

Calcular:

```text
SHA-256
```

antes de procesamiento.

Recalcular al terminar el procesamiento.

Debe cumplir:

```text
SHA256_BEFORE == SHA256_AFTER
```

Si difiere:

```text
PETITION_INTEGRITY_FAILURE
```

y detener.

---

# 14. Detección del tipo de PDF

Para `.pdf`:

1. abrir con `pypdf`;
2. extraer texto por página;
3. evaluar si existe texto útil;
4. si existe texto útil → ruta textual;
5. si no existe/insuficiente → ruta Windows.Data.Pdf + OCR.

No usar únicamente tamaño del texto como verdad semántica.

Documentar criterio técnico usado para `TEXT_LAYER_USABLE`.

---

# 15. PDF con texto

Usar `pypdf`.

Por cada página registrar:

```text
page_index
raw_text
extraction_method = PYPDF_TEXT
```

No ejecutar OCR innecesariamente.

---

# 16. PDF escaneado

Usar:

```text
Windows.Data.Pdf
PdfDocument
PdfPage
RenderToStreamAsync
```

Por cada página:

```text
render
→ SoftwareBitmap
→ Windows.Media.Ocr es-ES
→ text
```

Conservar:

```text
page_index
render dimensions
ocr language
ocr method
ocr latency si se registra
```

No persistir necesariamente render temporal si no aporta trazabilidad; si se persiste, marcarlo como DERIVED.

---

# 17. Imagen

Para JPG/JPEG/PNG:

```text
archivo original
→ decode SoftwareBitmap
→ Windows OCR es-ES
```

No recomprimir ni regrabar original.

---

# 18. OCR provider

Implementar interfaz:

```text
OcrProvider
```

y provider:

```text
WindowsOcrProvider
```

Debe quedar desacoplado para permitir futuro fallback.

No integrar Tesseract todavía.

---

# 19. OCR Language

Default operativo:

```text
es-ES
```

Verificar al inicio que el idioma siga disponible.

Si no:

```text
OCR_LANGUAGE_UNAVAILABLE
```

No cambiar automáticamente a otro idioma sin registrar decisión.

---

# 20. MaxImageDimension

Consultar valor real del OcrEngine.

Si una imagen renderizada excede límite:

- reducir de manera controlada;
- mantener aspect ratio;
- registrar transformación derivada;
- nunca modificar original.

Agregar test.

---

# 21. Raw Text

Persistir texto bruto por página.

No corregir OCR antes de conservarlo.

Modelo:

```text
page_index
method
raw_text
```

---

# 22. Normalized Text

Generar copia normalizada separada.

Permitido:

```text
CRLF → LF
normalización Unicode segura
colapso controlado de espacios/tabs
limpieza de caracteres de control no imprimibles
```

No permitido:

- completar palabras;
- inventar números;
- corregir nombres propios por intuición;
- insertar separaciones semánticas no observadas sin registro.

---

# 23. Regla crítica sobre tokens unidos

Windows OCR observó:

```text
NUE777777
SOLICITADILIGENCIAFORENSE
```

Por lo tanto, el extractor debe contemplar tokens concatenados de forma determinista.

Ejemplo:

```text
NUE777777
```

puede mapearse a:

```text
label=NUE
value=777777
```

solo mediante patrón explícito testeado.

No aplicar "corrección inteligente" libre.

---

# 24. Extracción determinista de campos

Implementar primero reglas deterministas.

Campos iniciales:

```text
ruc
nues[]
requesting_unit
requesting_rut
oficio_number
oficio_date
evidence_description
requested_diligence
perceptual_questions
observations
```

Los nombres internos pueden ajustarse al dominio existente.

---

# 25. RUC

Extraer solo si existe evidencia textual compatible.

No inventar algoritmo jurídico.

Mantener:

```text
raw_value
normalized_value
page
source_text
method
status
```

---

# 26. NUE

Debe soportar:

```text
1 NUE
múltiples NUE
NUE repetida
NUE en varias páginas
```

Deduplicar únicamente si el valor textual es exactamente equivalente tras normalización segura.

Conservar todas las ocurrencias en provenance.

---

# 27. Otros campos

Para campos de texto libre:

```text
requesting_unit
evidence_description
requested_diligence
perceptual_questions
observations
```

no exigir extracción automática completa si no existe patrón suficientemente sustentado.

Puede quedar:

```text
NOT_FOUND
REVIEW_REQUIRED
```

---

# 28. Provenance

Cada `ExtractedField` debe incluir:

```text
field_name
value
normalized_value
source_document_id
page_index
source_text
extraction_method
status
confidence
```

`confidence`:

```text
nullable
```

Regla:

```text
NO fabricar confidence.
```

Si Windows OCR no entrega confidence fiable para ese dato:

```text
confidence = null
```

---

# 29. Estados de campo

Usar:

```text
OBSERVED
EXTRACTED
UNCERTAIN
CONFLICT
NOT_FOUND
CONFIRMED
CORRECTED_BY_HUMAN
```

Distinguir claramente máquina vs humano.

---

# 30. Conflictos

Implementar detección al menos de:

```text
MULTIPLE_RUC
RUC_MISSING
MULTIPLE_NUE_CANDIDATES
NUE_MISSING
FIELD_MULTIPLE_VALUES
OCR_EMPTY
TEXT_EXTRACTION_FAILED
DOCUMENT_INTEGRITY_FAILURE
```

Conflicto material:

```text
REVIEW_REQUIRED
```

---

# 31. No inventar obligatoriedad

RUC y NUE son importantes para construir el dominio, pero si faltan:

NO inventarlos.

El resultado puede ser:

```text
REVIEW_REQUIRED
```

y la UI debe permitir corrección humana.

---

# 32. Human Review

Implementar pantalla de revisión antes de `CaseStructureDraft`.

Mostrar:

```text
campo
valor propuesto
página
fragmento fuente
método
estado
conflicto
```

Permitir:

```text
confirmar
corregir
marcar no encontrado
```

Cada corrección debe auditarse.

---

# 33. CSRF

Toda acción de revisión/corrección state-changing requiere CSRF vigente.

No debilitar middleware R03/R04.

---

# 34. CaseStructureDraft

Implementar:

```text
PetitionExtraction
+ HumanReview
→ CaseStructureDraft
```

Reutilizar las clases del dominio R03.

No duplicar:

```text
RUC → NUE → ESPECIE → DSM
```

---

# 35. Límite del Petitorio

El petitorio normalmente puede aportar:

```text
RUC
NUE
descripciones
diligencias
unidad solicitante
```

pero NO necesariamente determina automáticamente:

```text
species_number
storage_relation
DSM count
SELF_STORAGE / CONTAINED_STORAGE
```

Si esa topología física no está explícita y validada:

dejarla pendiente.

No inventarla.

---

# 36. Draft parcial

Permitir que `CaseStructureDraft` o estructura intermedia represente información pendiente cuando el dominio lo soporte.

Si el contrato actual exige species/DSM completos:

NO falsificar datos.

En ese caso:

- crear un `PetitionCaseDraft` previo;
- documentar conversión posterior;
- o extender el contrato de forma explícita y testeada.

No romper invariantes existentes.

---

# 37. Creación definitiva del caso

R05.1 NO debe crear el caso definitivo automáticamente tras OCR.

Flujo:

```text
EXTRACTION
→ HUMAN REVIEW
→ BUILD DRAFT
→ PREVIEW
```

La persistencia definitiva del caso debe requerir una acción humana explícita o flujo posterior autorizado.

---

# 38. Integración Orchestrator

No avanzar estados forenses críticos automáticamente.

Puede registrar eventos del pipeline documental.

No marcar:

```text
IDENTIFICATION_COMPLETED
ACQUISITION_READY
```

por procesar un petitorio.

---

# 39. Persistencia PostgreSQL

Reutilizar:

```text
forensic.files
forensic.documents
forensic.hashes
forensic.audit_events
```

Antes de modificar schema:

inspeccionar columnas reales.

R05 reportó que no se requería migración.

Si el schema actual resulta insuficiente:

DETENER y documentar necesidad.

No editar `0001_initial_schema.sql`.

Solo crear migración nueva si es estrictamente necesaria y justificada.

---

# 40. File role

Petitorio:

```text
file_role = PETITION
```

Registrar SHA-256 en tabla de hashes conforme arquitectura existente.

---

# 41. Documents

Usar:

```text
document_type = PETITION
```

Persistir según columnas reales:

```text
ocr_status
ocr_text
```

o equivalentes observados.

No inventar columnas.

---

# 42. Artefactos derivados

Guardar de manera controlada:

```text
raw_text
normalized_text
extraction.json
ocr_metadata.json
```

Preferir FileStore / storage controlado.

Nunca escribir derivados encima del original.

---

# 43. extraction.json

Debe contener:

```text
document_id
document_sha256
processing_method
pages[]
fields[]
conflicts[]
review_status
created_at
tool_versions
```

No secrets.

---

# 44. Tool Versions

Registrar:

```text
Python
pypdf
winsdk
Windows build
Windows OCR language
Pillow
application version
```

---

# 45. Auditoría

Registrar como mínimo:

```text
PETITION_STAGED
PETITION_HASHED
PETITION_TEXT_EXTRACTED
PETITION_OCR_STARTED
PETITION_OCR_COMPLETED
PETITION_OCR_FAILED
PETITION_FIELDS_EXTRACTED
PETITION_CONFLICT_DETECTED
PETITION_REVIEW_STARTED
PETITION_FIELD_CONFIRMED
PETITION_FIELD_CORRECTED
PETITION_DRAFT_BUILT
```

---

# 46. API

Implementar:

```text
POST /api/petitions/stage
POST /api/petitions/{id}/extract
GET  /api/petitions/{id}
GET  /api/petitions/{id}/extraction
POST /api/petitions/{id}/review
POST /api/petitions/{id}/build-draft
```

Ajustar nombres solo si arquitectura existente lo exige.

---

# 47. Web

Actualizar `/cases/new` con flujo:

```text
1. Subir petitorio
2. Procesar
3. Ver texto extraído/OCR
4. Revisar campos
5. Resolver conflictos
6. Generar draft
7. Vista previa
```

No crear automáticamente caso definitivo.

---

# 48. Seguridad Web

Mantener:

```text
127.0.0.1
CSRF
request_id
security headers
no-store
errores seguros
```

---

# 49. Error Model

Crear errores equivalentes:

```text
UnsupportedPetitionFormatError
PetitionIntegrityError
PdfTextExtractionError
PdfRenderError
OcrUnavailableError
OcrLanguageUnavailableError
OcrProcessingError
PetitionExtractionConflictError
PetitionNotReadyForDraftError
```

Mapear a error model web existente.

---

# 50. Logs

Registrar:

```text
document_id
request_id
stage
duration
result
error_code
```

No registrar cuerpo completo del petitorio en logs operativos.

Texto derivado debe vivir en artefactos/DB controlados, no en logs generales.

---

# 51. Ollama / Qwen

NO integrar Qwen en el pipeline productivo de R05.1.

Razón:

la extracción determinista y OCR ya están validados.

Qwen quedará para una capa semántica posterior, con anti-invención y provenance.

No ejecutar Ollama en tests R05.1.

---

# 52. Tests obligatorios

Mantener los 108 tests.

Agregar como mínimo:

1. stage PDF permitido.
2. stage JPG.
3. stage JPEG.
4. stage PNG.
5. extensión no permitida.
6. upload demasiado grande.
7. SHA-256 before/after match.
8. original no modificado.
9. PDF textual detectado.
10. pypdf usado para PDF textual.
11. OCR no ejecutado en PDF textual útil.
12. PDF escaneado detectado.
13. Windows.Data.Pdf render ejecutado.
14. Windows OCR ejecutado.
15. es-ES usado.
16. PDF multi-page conserva page_index.
17. image OCR JPG.
18. image OCR PNG.
19. corrupt PDF controlado.
20. invalid image controlado.
21. OCR language unavailable.
22. MaxImageDimension controlado.
23. raw text preservado.
24. normalized text separado.
25. no modificación semántica silenciosa.
26. token `NUE777777` extraído correctamente.
27. RUC simple.
28. NUE simple.
29. múltiples NUE.
30. NUE duplicada provenance múltiple, valor único.
31. multiple RUC conflict.
32. missing RUC review required.
33. missing NUE review required.
34. field provenance page.
35. field source_text.
36. confidence null si no existe.
37. field NOT_FOUND.
38. field CONFLICT.
39. human confirm audit.
40. human correction audit.
41. corrected value conserva original provenance.
42. build draft requiere review.
43. draft reutiliza dominio R03.
44. no topología física inventada.
45. no species inventada desde texto ambiguo.
46. no DSM inventado.
47. PostgreSQL file role PETITION.
48. document type PETITION.
49. hashes persistidos.
50. audit events.
51. extraction JSON.
52. tool versions.
53. API stage.
54. API extract.
55. API extraction.
56. API review CSRF.
57. API build draft.
58. web upload.
59. web review.
60. web conflict rendering.
61. request_id.
62. no secrets.
63. no raw document body in logs.
64. `casos/` real intacto.
65. no PhysicalDrive.
66. no EWF.
67. no AXIOM.
68. no Ollama.
69. no OpenClaw.
70. no cloud.

---

# 53. Fixtures

Crear fixtures sintéticos controlados:

```text
petition_text.pdf
petition_scanned.pdf
petition.jpg
petition.png
petition_conflict.pdf
petition_missing_ruc.pdf
petition_missing_nue.pdf
```

No usar documentos reales para tests automatizados.

---

# 54. Prueba funcional local

Después de tests:

usar únicamente un fixture sintético representativo:

```text
RUC 12345678
NUE 777777
OFICIO 123
SOLICITA DILIGENCIA FORENSE
```

Verificar:

```text
upload
hash
extract
review
build draft
```

No crear caso definitivo.

---

# 55. Caso de PDF textual

Debe demostrar:

```text
PDF
→ pypdf
→ text
→ fields
```

sin OCR.

---

# 56. Caso de PDF escaneado

Debe demostrar:

```text
PDF
→ Windows.Data.Pdf
→ RenderToStreamAsync
→ Windows OCR
→ fields
```

---

# 57. Imagen

Debe demostrar:

```text
PNG/JPG
→ Windows OCR
→ fields
```

---

# 58. Human Review obligatoria

Antes de `build-draft`, el sistema debe exigir que:

- conflictos críticos estén resueltos;
- RUC esté confirmado/corregido;
- NUE(s) estén confirmadas/corregidas.

No auto-confirmar por confianza heurística.

---

# 59. No crear caso automáticamente

El endpoint `build-draft` debe retornar propuesta estructurada.

No llamar directamente a:

```text
CaseApplicationService.create_case()
```

sin acción posterior explícita.

---

# 60. No realizar

Prohibido:

- petitorio real en tests;
- evidencia real;
- PhysicalDrive;
- Set-Disk;
- DiskPart;
- CHKDSK;
- ewfacquire;
- ewfverify;
- AXIOM;
- Ollama/Qwen productivo;
- OpenClaw;
- Portable;
- RAR;
- Word;
- cloud;
- LAN exposure.

---

# 61. Documentación

Crear:

```text
PETITION_PIPELINE_ARCHITECTURE.md
PETITION_EXTRACTION_SCHEMA.md
```

Documentar:

- input types;
- detector;
- pypdf path;
- Windows.Data.Pdf path;
- Windows OCR;
- normalization;
- fields;
- provenance;
- conflict model;
- human review;
- draft mapping;
- DB;
- artifacts;
- API;
- Web;
- audit;
- errors;
- tool versions;
- limitations.

---

# 62. Criterio de aceptación

R05.1 queda COMPLETO si:

- baseline completo verde;
- pypdf instalado/versionado;
- PDF textual funcional;
- PDF escaneado funcional;
- imagen OCR funcional;
- Windows OCR es-ES funcional;
- originales inmutables;
- SHA-256 pre/post MATCH;
- raw text preservado;
- normalized text separado;
- extraction determinista;
- provenance por campo;
- `confidence=null` cuando no existe fuente real;
- conflictos explícitos;
- human review funcional;
- correcciones auditadas;
- `CaseStructureDraft` generado desde flujo revisado;
- no se inventan species/DSM/topología;
- API funcional;
- Web funcional;
- DB/FileStore integrados;
- CSRF;
- no caso definitivo automático;
- `casos/` productivo no tocado durante tests;
- no herramientas forenses;
- no cloud;
- suite completa verde;
- documentación creada.

Estado:

```text
PETITION_PIPELINE_READY
```

Si falta requisito crítico:

```text
PETITION_PIPELINE_BLOCKED
```

---

# 63. Git

Antes de commit:

```text
pytest
git status
```

Confirmar ausencia de:

```text
.env
secrets
petitorios reales
runtime staging
fixtures generados fuera de tests
casos/
E01
fotos reales
```

Commit sugerido:

```text
Sprint R05.1: implementa pipeline local de petitorios OCR y draft
```

---

# 64. Reporte final obligatorio

```text
SPRINT R05.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...

TESTS BEFORE:
...

DEPENDENCIES:
pypdf:
winsdk:
Pillow:

PETITION MODULE:
...

SUPPORTED INPUTS:
...

PDF TEXT PATH:
...

PDF SCANNED PATH:
...

IMAGE OCR PATH:
...

WINDOWS OCR:
...

OCR LANGUAGE:
...

HASH INTEGRITY:
...

RAW TEXT:
...

NORMALIZED TEXT:
...

FIELD EXTRACTION:
...

RUC:
...

NUE:
...

OTHER FIELDS:
...

PROVENANCE:
...

CONFIDENCE POLICY:
...

CONFLICTS:
...

HUMAN REVIEW:
...

CASESTRUCTUREDRAFT:
...

TOPOLOGY INVENTED:
NO / SI

DATABASE:
...

FILES:
...

DERIVED ARTIFACTS:
...

AUDIT:
...

API:
...

WEB:
...

CSRF:
...

FILES CREATED:
...

FILES MODIFIED:
...

MIGRATIONS:
...

TESTS ADDED:
...

TESTS FINAL:
...

FUNCTIONAL PDF TEXT TEST:
...

FUNCTIONAL SCANNED PDF TEST:
...

FUNCTIONAL IMAGE TEST:
...

POSTGRESQL MODIFIED:
NO / SI
DETALLE:
...

CASOS/ MODIFIED:
NO / SI

REAL PETITION READ:
NO / SI

CLOUD:
NO / SI

OLLAMA:
NO / SI

PHYSICALDRIVE:
NO / SI

EWFACQUIRE:
NO / SI

EWFVERIFY:
NO / SI

AXIOM:
NO / SI

OPENCLAW:
NO / SI

RISKS:
...

BLOCKERS:
...

STATUS:
PETITION_PIPELINE_READY / PETITION_PIPELINE_BLOCKED
```

---

# 65. Instrucción final

TRAE:

1. lee toda la documentación vigente;
2. ejecuta baseline;
3. instala/versiona `pypdf`;
4. inspecciona schema DB real antes de persistir;
5. implementa módulo `petition`;
6. implementa PDF textual;
7. implementa PDF escaneado;
8. implementa OCR de imágenes;
9. preserva originales;
10. implementa raw/normalized text;
11. implementa extracción determinista;
12. implementa provenance;
13. implementa conflictos;
14. implementa human review;
15. implementa mapping a `CaseStructureDraft`;
16. integra DB/FileStore;
17. integra API/Web;
18. agrega tests;
19. ejecuta pruebas funcionales sintéticas;
20. ejecuta suite completa;
21. revisa Git;
22. entrega reporte final;
23. detente;
24. NO inicies R06.

Comienza ahora.
