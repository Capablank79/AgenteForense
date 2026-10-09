# SPRINT_R06 — Investigación del Agente de Identificación por Fotografías

## 1. Objetivo
Investigar y definir, con evidencia del entorno real, cómo implementar el Agente de Identificación fotográfica del AGENTE FORENSE.

Pipeline futuro:

```text
FOTOGRAFÍAS
→ INGESTA SEGURA
→ HASH / INMUTABILIDAD
→ OCR VISIBLE
→ CLASIFICACIÓN DE FOTO
→ EXTRACCIÓN DE ATRIBUTOS
→ VALIDACIÓN ANTI-INVENCIÓN
→ CONFLICTOS
→ REVISIÓN HUMANA
→ identification.json
→ case.json
```

Este sprint es de INVESTIGACIÓN Y DISEÑO. NO debe implementar todavía el agente productivo completo.

Estado esperado:

```text
PHOTO_IDENTIFICATION_CAPABILITIES_VERIFIED
```

o:

```text
PHOTO_IDENTIFICATION_BLOCKED
```

## 2. Documentación obligatoria
Leer completos antes de investigar:

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
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
PETITION_PIPELINE_CAPABILITIES.md
PETITION_PIPELINE_ARCHITECTURE.md
PETITION_EXTRACTION_SCHEMA.md
SPRINT_R06.md
```

Revisar además reportes reales R00–R05.1.

## 3. Baseline
Esperado:

```text
PYTHON: 3.10.11
WINDOWS: Windows 10 Pro build 19045
POSTGRESQL: 18.6
WEB: 127.0.0.1:8085
TESTS: 188 passed
PETITION PIPELINE: PETITION_PIPELINE_READY
```

Ejecutar antes:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe -m pytest
```

Sin regresiones.

## 4. Objetivos permanentes del Agente de Identificación
El agente futuro debe trabajar con fotografías de ESPECIE, DSM, etiquetas, seriales, marca/modelo, capacidad, conectores y detalles físicos.

Debe producir datos estructurados como:

```text
object_type
brand
model
serial
capacity
color
visible_labels
description
photo classifications
field provenance
conflicts
review status
```

No inventar campos.

## 5. Capacidades ya conocidas
Ya están verificadas:

```text
Windows.Media.Ocr
es-ES
winsdk 1.0.0b10
Pillow
OCR local
```

También está verificado que:

```text
Windows OCR = texto, NO visión semántica
qwen2.5:3b = texto, NO visión
```

No confundir OCR con clasificación visual.

## 6. Inventario real de visión local
Investigar qué proveedores de visión existen realmente en el equipo.

Revisar como mínimo:

```text
Ollama
modelos instalados
Qwen-VL / Qwen2.5-VL si existen
LLaVA
Gemma vision
MiniCPM-V
otros modelos multimodales locales
OpenCV
Windows APIs útiles
ONNX Runtime
DirectML
PyTorch si está instalado
```

Registrar por proveedor:

```text
INSTALLED
NOT_INSTALLED
VERSION
MODEL
VISION CAPABLE
TEXT ONLY
LOCAL/OFFLINE
GPU/CPU
MEMORY REQUIREMENT
API
LICENSE
```

No descargar modelos en R06.

## 7. Ollama
Verificar:

```text
ollama --version
ollama list
```

No ejecutar `ollama pull`.

Si hay modelo vision-capable ya instalado, hacer solo prueba controlada con fixture sintético.

## 8. OCR aplicado a fotografías
Validar con imágenes sintéticas/laboratorio:

```text
etiqueta con serial
etiqueta con capacidad
texto inclinado
texto pequeño
reflejo
bajo contraste
```

Registrar:

```text
OCR text
latency
failure modes
orientation issues
```

No usar fotos reales de evidencia sin autorización explícita.

## 9. Clasificación automática
Investigar categorías candidatas:

```text
GENERAL
FRONTAL
POSTERIOR
LATERAL
ETIQUETA
SERIAL
CONEXION
DETALLE
NO_CLASIFICADA
```

Distinguir claramente:

```text
clasificación visual
clasificación textual derivada de OCR
clasificación humana
```

## 10. Regla de cantidad de fotografías
La documentación histórica usaba 3 fotografías por objeto físico identificable, pero esta regla no está todavía consolidada como norma activa de reconstrucción.

R06 debe investigar y documentar:

- si sigue siendo requisito operacional real;
- si aplica a ESPECIE;
- si aplica a DSM contenido;
- comportamiento SELF_STORAGE;
- qué ocurre con 0/1/2/>3 fotos;
- si es regla obligatoria o recomendación.

NO hardcodear aún la regla.

Resultado esperado:

```text
PHOTO_COUNT_POLICY
```

## 11. SELF_STORAGE
Definir futura política para:

```text
ESPECIE = DSM
```

Objetivo preferente: una sola copia física de cada foto, con referencias compartidas.

No duplicar archivos.

## 12. CONTAINED_STORAGE
Para:

```text
ESPECIE
└── DSM1
└── DSM2
```

investigar cómo distinguir fotografías del objeto contenedor y de cada DSM.

## 13. Inmutabilidad de fotografías
Diseñar regla obligatoria:

```text
SHA256 before
analysis
SHA256 after
```

Debe coincidir.

No recomprimir, editar EXIF, rotar físicamente, re-guardar JPEG, recortar original ni aplicar filtros destructivos.

## 14. Metadata por fotografía
Diseñar:

```text
photo_id
entity_type
entity_id
original_filename
relative_path
size_bytes
sha256
width
height
format
captured_at si existe y es confiable
classification
ocr_text
analysis_status
```

## 15. Provenance de atributos
Cada atributo debe incluir:

```text
field_name
value
source_photo_id
source_region si existe
source_text
method
status
confidence si el proveedor realmente la entrega
human_confirmed
```

No fabricar confidence.

## 16. Campos de identificación
Investigar extracción de:

```text
object_type
brand
model
serial
capacity
color
visible_labels
part_number
imei si aplica
mac_address si aplica
```

## 17. Estados por campo
Diseñar:

```text
OBSERVED
EXTRACTED
UNCERTAIN
NOT_VISIBLE
NOT_FOUND
CONFLICT
CONFIRMED
CORRECTED_BY_HUMAN
REJECTED_UNSUPPORTED
```

## 18. Serial
Nunca completar caracteres ilegibles ni inferir dígitos.

Si es parcial:

```text
UNCERTAIN
```

## 19. Marca/modelo
Distinguir texto observado, normalización segura e inferencia comercial.

Ejemplo: OCR `GEFORCE GTX` NO autoriza automáticamente `brand = NVIDIA` sin fuente explícita o confirmación humana.

## 20. Capacidad
Investigar normalización segura:

```text
64 GB
64GB
1 TB
```

Separar display_value, normalized_value y bytes calculados solo con regla matemática explícita.

## 21. Color
No usar OCR para inferir color.

Sin visión real:

```text
NOT_EVALUATED
```

o revisión humana.

## 22. Descripción automática
Diseñar generador futuro que use únicamente campos confirmados. La descripción es presentación derivada, no fuente de verdad.

## 23. Proveedor de visión
Definir interfaz conceptual:

```text
VisionProvider
```

con salida estructurada estricta y reemplazable.

## 24. LLM/VLM anti-invención
Si existe proveedor VLM, todo valor propuesto debe conservar provenance y no persistirse sin soporte.

## 25. Qwen textual
`qwen2.5:3b` puede evaluarse solo como razonador sobre OCR/texto. No puede declararse analizador visual.

## 26. Conflictos
Diseñar al menos:

```text
SERIAL_MULTIPLE_VALUES
MODEL_MULTIPLE_VALUES
BRAND_CONFLICT
CAPACITY_CONFLICT
PHOTO_ENTITY_MISMATCH
LOW_VISIBILITY
NO_TEXT
NO_VISION_PROVIDER
```

## 27. Human Review
Diseñar pantalla futura con foto, clasificación, OCR, atributos propuestos, fuente, estado y conflictos.

Operador puede confirmar, corregir, rechazar o clasificar manualmente.

Toda corrección debe auditarse.

## 28. Renombrado
Investigar política segura:

```text
propuesta
preview
collision check
human confirmation
rename/move
hash after
rollback
```

No renombrar automáticamente originales en R06.

## 29. Nomenclatura futura
Evaluar nombres determinísticos basados en NUE, ESPECIE, DSM, clasificación y secuencia.

No fijar estándar definitivo sin revisar formatos históricos reales.

## 30. identification.json
Diseñar schema futuro con:

```text
entity
photos
ocr
attributes
provenance
conflicts
human_review
tool_versions
timestamps
```

## 31. case.json
Definir qué referencias/resumen deben sincronizarse.

## 32. PostgreSQL
Inspeccionar uso actual de:

```text
forensic.photos
forensic.files
forensic.hashes
forensic.audit_events
```

No modificar schema en R06.

## 33. Web futura
Diseñar flujo:

```text
seleccionar caso/NUE/ESPECIE/DSM
→ cargar fotos
→ hash
→ OCR
→ visión si existe
→ propuestas
→ conflictos
→ revisión humana
→ confirmar identificación
```

## 34. API futura
Diseñar contratos conceptuales:

```text
POST /api/identification/photos/stage
POST /api/identification/entities/{id}/analyze
GET  /api/identification/entities/{id}
POST /api/identification/entities/{id}/review
POST /api/identification/entities/{id}/confirm
```

## 35. Estados de orquestación
Investigar integración con:

```text
IDENTIFICATION_PENDING
IDENTIFICATION_COMPLETED
ACQUISITION_READY
```

No modificar State Machine en R06.

## 36. Datos de prueba
Preferir fixtures sintéticos, fotos de laboratorio no sensibles y objetos propios.

No usar evidencia real.

## 37. Prueba técnica opcional
Si existe proveedor vision-capable YA instalado, se permite prueba con imagen sintética/laboratorio.

Registrar input, model, version, prompt, structured output, latency y valores no sustentados.

## 38. No realizar
Prohibido:

- descargar modelos;
- `ollama pull`;
- cloud;
- evidencia real;
- modificar fotos originales;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- OpenClaw;
- Portable;
- RAR;
- Word;
- cambiar PostgreSQL;
- tocar `casos/` productivo.

## 39. Tests
Baseline:

```text
188 passed
```

Final:

```text
188 passed
```

o más si se agregan utilidades de inspección.

## 40. Entregable obligatorio
Crear:

```text
PHOTO_IDENTIFICATION_CAPABILITIES.md
```

Debe incluir:

```text
BASELINE
OCR CAPABILITIES
VISION PROVIDERS
OLLAMA MODELS
VISION-CAPABLE MODELS
PHOTO COUNT POLICY
SELF_STORAGE POLICY
CONTAINED_STORAGE POLICY
PHOTO METADATA
ATTRIBUTE MODEL
PROVENANCE MODEL
CONFLICT MODEL
RENAMING POLICY
HUMAN REVIEW
IDENTIFICATION.JSON DESIGN
CASE.JSON IMPACT
DATABASE IMPACT
WEB FLOW
API CONTRACT
ORCHESTRATION IMPACT
DEPENDENCIES FOR R06.1
RISKS
BLOCKERS
```

## 41. Criterio de aceptación
R06 queda COMPLETO si:

- baseline verde;
- proveedores reales inventariados;
- se determina si existe visión local real;
- OCR fotográfico investigado;
- limitaciones conocidas;
- política de cantidad de fotos documentada;
- SELF_STORAGE documentado;
- CONTAINED_STORAGE documentado;
- provenance definida;
- anti-invención definida;
- conflictos definidos;
- human review definida;
- renombrado seguro diseñado;
- identification.json diseñado;
- integración DB/Web/API/orchestrator definida;
- dependencias para R06.1 definidas;
- no evidencia real;
- no cloud;
- no herramientas forenses;
- suite verde.

Estado:

```text
PHOTO_IDENTIFICATION_CAPABILITIES_VERIFIED
```

o:

```text
PHOTO_IDENTIFICATION_BLOCKED
```

## 42. Reporte final obligatorio

```text
SPRINT R06:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
WINDOWS OCR:
...
VISION PROVIDERS DETECTED:
...
OLLAMA VERSION:
...
OLLAMA MODELS:
...
VISION-CAPABLE MODEL:
...
QWEN2.5:3B:
TEXT ONLY / OTHER
PHOTO OCR TEST:
...
PHOTO COUNT POLICY:
...
SELF_STORAGE:
...
CONTAINED_STORAGE:
...
PHOTO METADATA:
...
ATTRIBUTE MODEL:
...
PROVENANCE:
...
CONFLICTS:
...
HUMAN REVIEW:
...
RENAMING POLICY:
...
IDENTIFICATION.JSON:
...
CASE.JSON:
...
DATABASE IMPACT:
...
WEB FLOW:
...
API:
...
ORCHESTRATION:
...
DEPENDENCIES REQUIRED FOR R06.1:
...
FILES CREATED:
...
FILES MODIFIED:
...
POSTGRESQL MODIFIED:
NO / SI
CASOS/ MODIFIED:
NO / SI
REAL EVIDENCE PHOTOS:
NO / SI
CLOUD:
NO / SI
OLLAMA PULL:
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
TESTS FINAL:
...
RISKS:
...
BLOCKERS:
...
STATUS:
PHOTO_IDENTIFICATION_CAPABILITIES_VERIFIED / PHOTO_IDENTIFICATION_BLOCKED
```

## 43. Instrucción final
TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. inventaría OCR y visión reales;
4. inspecciona Ollama y modelos instalados;
5. no descargues modelos;
6. prueba OCR fotográfico con fixtures seguros;
7. prueba visión solo si ya existe provider local;
8. define política de fotos;
9. define provenance y conflictos;
10. diseña review/rename/identification.json;
11. define integración DB/Web/API/orchestrator;
12. crea `PHOTO_IDENTIFICATION_CAPABILITIES.md`;
13. ejecuta tests finales;
14. entrega reporte;
15. detente;
16. NO inicies R06.1.

Comienza ahora.
