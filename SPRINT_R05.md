# SPRINT_R05 — Investigación del Pipeline Petitorio → OCR → CaseStructureDraft

## 1. Objetivo

Investigar el entorno REAL disponible para procesar un oficio petitorio y definir técnicamente el pipeline:

```text
PETITORIO
→ INGESTA
→ EXTRACCIÓN DE TEXTO
→ OCR SI ES NECESARIO
→ NORMALIZACIÓN
→ EXTRACCIÓN ESTRUCTURADA
→ VALIDACIÓN
→ CaseStructureDraft
```

Este sprint NO implementa todavía el pipeline productivo completo.

Debe determinar con evidencia:

- formatos reales de entrada;
- capacidades locales de PDF/texto/OCR;
- motores disponibles y versiones;
- soporte de español;
- estrategia PDF con texto vs PDF escaneado vs imagen;
- campos que el petitorio puede aportar;
- trazabilidad/provenance por campo;
- cómo alimentar `CaseStructureDraft`;
- qué requiere revisión humana;
- cómo integrar Web/API/DB/FileStore sin romper trazabilidad.

Estado esperado:

```text
PETITION_PIPELINE_CAPABILITIES_VERIFIED
```

o:

```text
PETITION_PIPELINE_BLOCKED
```

## 2. Documentación obligatoria

Antes de investigar, leer completos:

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
SPRINT_R05.md
```

Revisar también los reportes finales reales de R00 a R04.

## 3. Baseline

Esperado:

```text
PYTHON: 3.10.11
POSTGRESQL: 18.6
DB: agente_forense_db
DB HOST: 127.0.0.1
DB PORT: 5433
WEB: 127.0.0.1:8085
TESTS: 108 passed
ORCHESTRATION: ORCHESTRATION_FOUNDATION_READY
```

Ejecutar antes:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Si existe regresión: DETENER y DOCUMENTAR.

## 4. Regla principal

NO elegir un OCR ni parser por preferencia.

Investigar primero:

1. herramientas instaladas;
2. versiones;
3. ayuda local;
4. capacidades reales;
5. soporte español;
6. soporte PDF;
7. soporte imagen;
8. extracción de texto embebido;
9. OCR de PDF escaneado;
10. OCR de imágenes;
11. salida estructurable;
12. precisión observable;
13. procesamiento local/offline;
14. licencia;
15. integración Python;
16. consumo de recursos;
17. fallos;
18. trazabilidad;
19. reproducibilidad.

## 5. Formatos objetivo

Investigar como mínimo:

```text
PDF con capa de texto
PDF escaneado
JPG
JPEG
PNG
TIFF si está presente/justificado
```

No declarar soporte de formatos no probados.

## 6. PDF con texto

Investigar si están disponibles o son viables:

```text
PyMuPDF
pypdf
pdfplumber
pdfminer.six
```

No instalar todavía.

Determinar:

- detección de texto embebido;
- orden de lectura;
- páginas;
- metadata;
- fallos;
- rendimiento;
- preservación del original.

## 7. OCR local

Inventariar motores realmente disponibles:

```text
Tesseract
Windows OCR
PaddleOCR
EasyOCR
Qwen/VLM local
Ollama models
otros motores instalados
```

Registrar por herramienta:

```text
INSTALLED / NOT_INSTALLED
VERSION
PATH
LANGUAGES
OFFLINE
API/CLI
```

No descargar modelos en R05.

## 8. Windows OCR

Investigar:

- versión de Windows;
- APIs accesibles;
- idioma español;
- restricciones;
- dependencia WinRT/UWP;
- integración Python;
- comportamiento sin internet.

No asumir.

## 9. Tesseract

Si está instalado:

```text
tesseract --version
tesseract --list-langs
tesseract --help
```

Registrar versión, idiomas, `spa`, salida, configuración, soporte real y limitaciones.

## 10. Qwen / Ollama

Existe históricamente:

```text
J:\AgenteForense\OllamaModels
```

Investigar únicamente:

- modelos realmente presentes;
- si alguno tiene capacidad visual;
- versión real de Ollama;
- compatibilidad con imágenes;
- salida estructurada;
- procesamiento completamente local.

No usar Qwen como fuente automática de verdad.

No ejecutar modelos salvo prueba local expresamente necesaria y documentada.

## 11. Pipeline por tipo

### PDF con texto

```text
PDF → extractor de texto → normalized text
```

### PDF escaneado

```text
PDF → render por página → OCR → normalized text
```

### Imagen

```text
imagen → OCR → normalized text
```

Evitar OCR si existe texto embebido confiable.

## 12. Preservación del original

El petitorio original debe permanecer inmutable.

Registrar:

```text
original_filename
size_bytes
sha256
mime_observed
extension
received_at
```

No reescribir, recomprimir ni modificar metadata del original.

## 13. Artefactos derivados

Diseñar derivados separados, por ejemplo:

```text
raw_text.txt
normalized_text.txt
extraction.json
ocr_metadata.json
```

No confundirlos con el original.

## 14. Campos potenciales

Investigar extracción de:

```text
RUC
NUE
unidad solicitante
RUT o identificador institucional
número de oficio
fecha del oficio
descripción de evidencia
diligencia solicitada
preguntas periciales
observaciones
otros identificadores administrativos
```

No asumir que todos aparecen siempre.

## 15. Provenance por campo

Cada dato debe poder guardar:

```text
value
source_document
page
source_text
extraction_method
confidence si existe realmente
status
```

Estados sugeridos:

```text
OBSERVED
EXTRACTED
UNCERTAIN
CONFLICT
NOT_FOUND
```

No inventar `confidence`.

## 16. Observado vs inferido

Distinguir:

```text
OBSERVED_TEXT
EXTRACTED_FIELD
NORMALIZED_FIELD
INFERRED_FIELD
```

`INFERRED_FIELD` no crea estructura definitiva.

## 17. CaseStructureDraft

Diseñar:

```text
PetitionExtraction → CaseStructureDraft
```

Reutilizar exactamente el contrato de dominio existente.

No crear una segunda jerarquía paralela.

## 18. Revisión humana

La política vigente mantiene revisión humana antes de convertir OCR en estructura definitiva.

En R05:

- no cambiar esa política;
- identificar campos potencialmente autoaceptables;
- identificar ambigüedades bloqueantes;
- documentar una futura evolución hacia mayor autonomía.

No crear caso definitivo automáticamente.

## 19. Conflictos

Diseñar al menos:

```text
RUC múltiple
NUE repetida/inconsistente
RUC distinto al existente
número ilegible
campo con dos candidatos
petitorio sin RUC
petitorio sin NUE
```

No elegir arbitrariamente.

Usar:

```text
REVIEW_REQUIRED
```

cuando corresponda.

## 20. Normalización

Investigar reglas seguras para:

```text
espacios
saltos de línea
Unicode
guiones
artefactos OCR
mayúsculas/minúsculas
```

Conservar siempre raw y normalized text por separado.

## 21. Extracción determinista primero

Evaluar:

```text
regex
anchors
layout/text rules
known labels
```

antes de LLM.

No inventar patrones sin observar ejemplos.

## 22. Uso futuro de LLM

Si se usa posteriormente:

solo para clasificación, extracción semántica, ayuda ante ambigüedad, resumen y mapping a schema.

Nunca inventar campos ausentes.

No dar acceso irrestricto al filesystem.

## 23. Datos reales

Preferir:

- fixtures sintéticos;
- documentos públicos/no sensibles;
- ejemplos anonimizados.

No subir petitorios reales a servicios externos.

Si se usa uno real localmente para validar layout:
- no modificar;
- no subir;
- no copiar contenido sensible al reporte;
- registrar solo hallazgos técnicos.

## 24. Web

Diseñar flujo futuro:

```text
Subir petitorio
↓
hash + staging
↓
detectar tipo
↓
extraer texto / OCR
↓
mostrar campos propuestos
↓
marcar conflictos
↓
revisión
↓
CaseStructureDraft
```

No implementarlo productivamente en R05.

## 25. API futura

Diseñar contratos conceptuales:

```text
POST /api/petitions/stage
POST /api/petitions/{id}/extract
GET  /api/petitions/{id}
GET  /api/petitions/{id}/extraction
POST /api/petitions/{id}/build-draft
```

## 26. Persistencia

Inspeccionar encaje con:

```text
files
documents
hashes
audit_events
```

Determinar si `documents` ya permite guardar tipo PETITION, referencia al original, textos derivados, extracción JSON y estado.

Si falta soporte, documentar migración necesaria para R05.1.

No modificar DB en R05.

## 27. Auditoría futura

Diseñar eventos:

```text
PETITION_STAGED
PETITION_HASHED
TEXT_EXTRACTED
OCR_STARTED
OCR_COMPLETED
OCR_FAILED
FIELDS_EXTRACTED
FIELD_CONFLICT_DETECTED
DRAFT_BUILT
HUMAN_REVIEW_REQUIRED
```

## 28. Tool Versions

Todas las herramientas evaluadas deben registrar versión real.

No usar etiquetas vagas como `latest`.

## 29. Dependencias candidatas

Crear lista exacta para R05.1.

No instalar en R05.

## 30. Prueba técnica mínima

Se permite crear fixtures sintéticos:

1. PDF con texto;
2. PDF escaneado sintético;
3. imagen con texto español.

No persistir en `casos/`.

## 31. Matriz de evaluación

Para cada camino/motor registrar:

```text
INPUT
OUTPUT
SPANISH
PAGE INFO
CONFIDENCE
LAYOUT
OFFLINE
PYTHON INTEGRATION
FAILURE MODE
RESOURCE COST
LICENSE
```

## 32. Selección

R05 debe terminar seleccionando:

```text
PRIMARY TEXT EXTRACTOR
PRIMARY OCR ENGINE
OPTIONAL SECONDARY/FALLBACK
STRUCTURED EXTRACTION STRATEGY
```

Si falta evidencia:

```text
PETITION_PIPELINE_BLOCKED
```

## 33. No realizar

Prohibido:

- modificar PostgreSQL;
- crear migraciones;
- crear caso real;
- tocar `casos/`;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- adquisición;
- verificación;
- Portable;
- RAR;
- Word;
- OpenClaw;
- exposición LAN;
- servicios cloud;
- subir documentación real a terceros.

## 34. Tests

Antes:

```text
108 passed
```

Al final:

```text
108 passed
```

o más si se agregaron utilidades de inspección.

Sin regresiones.

## 35. Entregable obligatorio

Crear:

```text
PETITION_PIPELINE_CAPABILITIES.md
```

Debe incluir:

```text
BASELINE
DOCUMENT FORMATS
LOCAL PDF EXTRACTORS
LOCAL OCR ENGINES
WINDOWS OCR
TESSERACT
OLLAMA/QWEN INVENTORY
SELECTED TEXT EXTRACTOR
SELECTED OCR ENGINE
FALLBACK STRATEGY
PIPELINE BY INPUT TYPE
SPANISH SUPPORT
PROVENANCE MODEL
FIELD MODEL
CONFLICT MODEL
NORMALIZATION RULES
CASESTRUCTUREDRAFT MAPPING
WEB FLOW
API CONTRACT
DATABASE IMPACT
AUDIT EVENTS
DEPENDENCIES FOR R05.1
RISKS
BLOCKERS
```

## 36. Criterio de aceptación

R05 queda COMPLETO si:

- baseline verde;
- capacidades reales inventariadas;
- PDF con texto investigado;
- OCR local investigado;
- español verificado;
- versiones registradas;
- estrategia por tipo definida;
- original preservado;
- derivados separados;
- provenance definida;
- campos potenciales definidos;
- conflictos definidos;
- mapping a `CaseStructureDraft` definido;
- impacto DB definido;
- dependencias R05.1 definidas;
- ninguna herramienta prohibida ejecutada;
- `casos/` intacto;
- tests verdes;
- `PETITION_PIPELINE_CAPABILITIES.md` creado.

Estado:

```text
PETITION_PIPELINE_CAPABILITIES_VERIFIED
```

o:

```text
PETITION_PIPELINE_BLOCKED
```

## 37. Reporte final obligatorio

```text
SPRINT R05:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
PDF TEXT EXTRACTORS:
...
OCR ENGINES DETECTED:
...
WINDOWS OCR:
...
TESSERACT:
...
OLLAMA:
...
QWEN / VISION MODELS:
...
SELECTED TEXT EXTRACTOR:
...
SELECTED OCR ENGINE:
...
FALLBACK:
...
SUPPORTED INPUTS:
...
SPANISH SUPPORT:
...
PROVENANCE:
...
FIELDS:
...
CONFLICTS:
...
NORMALIZATION:
...
CASESTRUCTUREDRAFT MAPPING:
...
WEB FLOW:
...
API:
...
DATABASE IMPACT:
...
DEPENDENCIES REQUIRED FOR R05.1:
...
FILES CREATED:
...
FILES MODIFIED:
...
POSTGRESQL MODIFIED:
NO / SI
CASOS/ MODIFIED:
NO / SI
REAL PETITION READ:
NO / SI
CLOUD USED:
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
PETITION_PIPELINE_CAPABILITIES_VERIFIED / PETITION_PIPELINE_BLOCKED
```

## 38. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. inventaría herramientas PDF/OCR reales;
4. inspecciona versiones y capacidades;
5. crea fixtures sintéticos cuando sea útil;
6. prueba rutas de extracción sin tocar casos reales;
7. compara resultados;
8. diseña provenance y mapping;
9. crea `PETITION_PIPELINE_CAPABILITIES.md`;
10. ejecuta tests finales;
11. entrega reporte;
12. detente;
13. NO inicies R05.1.

Comienza ahora.
