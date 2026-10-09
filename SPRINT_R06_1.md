# SPRINT_R06_1 — Implementación del Agente de Identificación Fotográfica Asistida

## 1. Objetivo

Implementar el Agente de Identificación Fotográfica del AGENTE FORENSE utilizando únicamente capacidades verificadas:

```text
FOTOGRAFÍAS
→ STAGING / FILESTORE
→ SHA-256
→ WINDOWS OCR es-ES
→ EXTRACCIÓN ESTRUCTURADA
→ QWEN2.5:3B SOLO SOBRE TEXTO OCR
→ VALIDACIÓN ANTI-INVENCIÓN
→ CLASIFICACIÓN TEXTUAL ASISTIDA
→ CONFLICTOS
→ REVISIÓN HUMANA
→ RENOMBRADO SEGURO
→ identification.json
→ case.json
→ AUDITORÍA
```

No existe proveedor visual local.

Por tanto:

```text
NO VISUAL SEMANTIC ANALYSIS
NO COLOR INFERENCE
NO PHYSICAL DAMAGE INFERENCE
NO SHAPE/OBJECT RECOGNITION FROM PIXELS
```

El sistema debe operar de forma útil con OCR, reglas deterministas, Qwen textual y revisión humana.

Estado esperado:

```text
PHOTO_IDENTIFICATION_READY
```

---

## 2. Documentación obligatoria

Leer completos antes de modificar código:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md

SPRINT_R03.md
SPRINT_R04.md
SPRINT_R05.md
SPRINT_R05_1.md
SPRINT_R06.md
SPRINT_R06_1.md

FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
PETITION_PIPELINE_ARCHITECTURE.md
PETITION_EXTRACTION_SCHEMA.md
PHOTO_IDENTIFICATION_CAPABILITIES.md
```

Revisar además reportes finales R03–R06.

---

## 3. Baseline

Esperado:

```text
PYTHON:
3.10.11

WINDOWS:
Windows 10 Pro build 19045

POSTGRESQL:
18.6

WEB:
127.0.0.1:8085

WINDOWS OCR:
winsdk 1.0.0b10
es-ES

OLLAMA:
0.40.0

MODEL:
qwen2.5:3b
TEXT ONLY

VISION PROVIDER:
NONE

TESTS:
188 passed
```

Antes de cambios:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe -m pytest
```

Si existe regresión:

```text
DETENER
DOCUMENTAR
NO IMPLEMENTAR
```

---

## 4. Principio rector

El agente puede:

- leer texto visible;
- extraer candidatos;
- normalizar de forma segura;
- comparar valores;
- detectar conflictos;
- pedir revisión humana;
- usar Qwen para razonar sobre texto OCR.

El agente NO puede:

- “ver” color;
- “ver” daños;
- reconocer objetos por apariencia;
- inventar marca/modelo por conocimiento comercial;
- completar seriales;
- inferir atributos no presentes en OCR/metadata humana.

---

## 5. Arquitectura

Crear paquete equivalente a:

```text
src/agente_forense/identification/
    __init__.py
    models.py
    errors.py
    photo_ingest.py
    photo_ocr.py
    text_classifier.py
    attribute_extractor.py
    qwen_text.py
    anti_invention.py
    conflicts.py
    review.py
    renaming.py
    identification_json.py
    service.py
```

Puede ajustarse si la arquitectura real lo aconseja.

No colocar lógica crítica en routes.

---

## 6. Reutilización de Windows OCR

Reutilizar provider probado en petitorios cuando sea razonable.

No duplicar innecesariamente lógica WinRT.

Debe aceptar:

```text
JPG
JPEG
PNG
```

y producir:

```text
raw_text
lines
words
language
latency
```

si esos datos están disponibles.

---

## 7. Ingesta de fotografías

Implementar staging seguro.

Por foto registrar:

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
classification
ocr_text
analysis_status
```

---

## 8. Entidades válidas

Una fotografía debe asociarse explícitamente a:

```text
SPECIES
DSM
```

No permitir foto sin entidad destino en el flujo productivo.

---

## 9. SELF_STORAGE

Para:

```text
ESPECIE = DSM
```

mantener:

```text
same_physical_object_as_species = true
```

Las fotografías se almacenan una sola vez.

DSM debe referenciar fotos de ESPECIE.

No duplicar bytes.

---

## 10. CONTAINED_STORAGE

Para:

```text
ESPECIE
└── DSM1
└── DSM2
```

las fotografías deben asociarse explícitamente al contenedor o a un DSM concreto.

No adivinar asociación.

---

## 11. Política de cantidad de fotos

Aplicar la decisión de R06:

```text
3 fotos = recomendación operacional
```

No bloquear persistencia legítima con 1 o 2 fotos.

Estados sugeridos:

```text
0 = PENDING
1-2 = INCOMPLETE
3 = READY
>3 = REVIEW_REQUIRED
```

Pero:

```text
1-2 fotos NO deben invalidar automáticamente una identificación
```

si el operador confirma que la evidencia disponible es suficiente.

Registrar excepción/revisión.

---

## 12. Inmutabilidad

Para cada fotografía:

```text
SHA256_BEFORE
analysis
SHA256_AFTER
```

Debe coincidir.

Si no:

```text
PHOTO_INTEGRITY_FAILURE
```

Abortar análisis de esa foto.

---

## 13. Prohibiciones sobre original

No:

- recomprimir;
- re-guardar JPEG;
- editar EXIF;
- rotar físicamente;
- aplicar filtros destructivos;
- redimensionar original;
- sobrescribir.

Transformaciones temporales deben ser en memoria o DERIVED.

---

## 14. OCR de fotografías

Ejecutar Windows OCR es-ES.

Si no hay texto:

```text
NO_TEXT
```

No tratar como fallo técnico si la foto es visual/general.

---

## 15. Clasificación textual automática

Permitida solo con soporte textual explícito.

Ejemplos:

```text
S/N
Serial Number
Número de serie
```

→ puede proponer:

```text
SERIAL
```

Texto con múltiples campos de etiqueta:

→ puede proponer:

```text
ETIQUETA
```

Sin soporte:

```text
NO_CLASIFICADA
```

No clasificar FRONTAL/POSTERIOR/LATERAL por visión inexistente.

---

## 16. Clasificación humana

Categorías permitidas:

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

Operador puede corregir propuesta.

Auditar toda corrección.

---

## 17. Extracción determinista

Extraer candidatos cuando existan patrones explícitos.

Campos:

```text
brand
model
serial
capacity
visible_labels
part_number
imei
mac_address
```

No exigir todos.

---

## 18. Serial

Nunca completar caracteres.

Si OCR entrega:

```text
ABC12?45
```

mantener literal/incertidumbre.

No reconstruir:

```text
ABC12345
```

por intuición.

---

## 19. Marca/modelo

Regla:

```text
texto OCR sustentado
→ candidato
```

No conocimiento externo.

Ejemplo:

```text
GEFORCE GTX
```

no autoriza:

```text
NVIDIA
```

si NVIDIA no aparece en fuente autorizada.

---

## 20. Capacidad

Normalización permitida:

```text
64 GB
64GB
1 TB
```

Guardar:

```text
raw_value
normalized_value
```

Conversión a bytes solo con función matemática explícita y testeada.

---

## 21. Color

Como no existe visión:

```text
color = NOT_EVALUATED
```

salvo que:

- aparezca textual en una etiqueta válida; o
- operador lo confirme manualmente.

---

## 22. Qwen textual

Integrar:

```text
qwen2.5:3b
```

solo con:

```text
OCR text
existing structured metadata
explicit instructions
```

Nunca pasarle autoridad final.

---

## 23. Contrato Qwen

Solicitar JSON estricto.

Ejemplo conceptual:

```json
{
  "brand": null,
  "model": null,
  "serial": null,
  "capacity": null,
  "visible_labels": []
}
```

Rechazar output no parseable.

No extraer hechos desde prosa libre si falla JSON.

---

## 24. Anti-invención

Cada valor Qwen debe validarse contra fuentes autorizadas:

```text
OCR
metadata estructurada actual
corrección humana
```

Si no hay sustento:

```text
REJECTED_UNSUPPORTED
```

No persistir como hecho.

---

## 25. Normalización segura

Permitir únicamente:

- trim;
- case-insensitive comparison;
- espacios repetidos;
- separadores triviales;
- capacidad con regla explícita.

No permitir:

- expansión semántica;
- completar abreviaturas;
- completar serial;
- inferir fabricante;
- inferir modelo comercial.

---

## 26. Provenance

Cada atributo:

```text
field_name
value
source_photo_id
source_text
method
status
confidence
human_confirmed
```

`confidence = null` si el proveedor no entrega score real.

---

## 27. Estados de atributo

Usar:

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

---

## 28. Conflictos

Implementar:

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

Conflicto crítico:

```text
REVIEW_REQUIRED
```

---

## 29. Human Review

Implementar UI que muestre:

```text
foto
nombre original
SHA-256
OCR
clasificación propuesta
clasificación final
atributos candidatos
provenance
conflictos
```

Operador puede:

```text
confirmar
corregir
rechazar
```

---

## 30. Confirmación de identificación

No marcar `IDENTIFICATION_COMPLETED` automáticamente.

Requerir acción explícita:

```text
CONFIRMAR_IDENTIFICACION
```

o mecanismo equivalente.

Registrar Human Gate/auditoría.

---

## 31. Renombrado

Solo después de revisión humana.

Flujo:

```text
preview
collision check
confirmation
rename
SHA256_AFTER
rollback si falla
```

---

## 32. Nombre determinístico

Usar nomenclatura derivada de:

```text
NUE
ESPECIE
DSM
clasificación
secuencia
```

Ejemplo conceptual:

```text
NUE_777777_ESPECIE1_SERIAL_01.jpg
```

Para DSM:

```text
NUE_777777_ESPECIE1_DSM1_SERIAL_01.jpg
```

Documentar estándar implementado.

---

## 33. Confirmación de renombrado

Requerir acción humana explícita:

```text
RENOMBRAR
```

o equivalente vía Web/Human Gate.

No renombrar silenciosamente.

---

## 34. Rollback de renombrado

Si una operación del lote falla:

- revertir las ya aplicadas cuando sea seguro;
- conservar hashes;
- registrar error;
- no dejar colisiones silenciosas.

---

## 35. identification.json

Generar por entidad o grupo de identificación según arquitectura final.

Debe contener:

```text
schema_version
entity
photos[]
ocr
attributes
provenance
conflicts
human_review
tool_versions
timestamps
status
```

---

## 36. case.json

Actualizar atómicamente con:

```text
identification status
reference to identification.json
confirmed attributes summary
photo references
```

No duplicar innecesariamente OCR completo.

---

## 37. PostgreSQL

Reutilizar:

```text
forensic.photos
forensic.files
forensic.hashes
forensic.audit_events
```

Inspeccionar columnas reales antes de persistir.

Si falta soporte material:

documentar y crear migración nueva solo si es estrictamente necesaria.

No editar migraciones ya aplicadas.

---

## 38. Orchestrator

Integrar:

```text
IDENTIFICATION_PENDING
→ IDENTIFICATION_COMPLETED
```

solo después de confirmación humana.

`ACQUISITION_READY` únicamente si las policies existentes también lo permiten.

No saltar state machine.

---

## 39. API

Implementar equivalentes a:

```text
POST /api/identification/photos/stage
POST /api/identification/entities/{id}/analyze
GET  /api/identification/entities/{id}
POST /api/identification/entities/{id}/review
POST /api/identification/entities/{id}/rename
POST /api/identification/entities/{id}/confirm
```

State-changing endpoints requieren CSRF.

---

## 40. Web

Agregar en detalle de caso:

```text
IDENTIFICACIÓN
```

con:

- entidades;
- fotos;
- OCR;
- atributos;
- conflictos;
- estado;
- botones de revisión;
- renombrado;
- confirmación.

---

## 41. Auditoría

Registrar al menos:

```text
PHOTO_STAGED
PHOTO_HASHED
PHOTO_OCR_COMPLETED
PHOTO_CLASSIFICATION_PROPOSED
PHOTO_CLASSIFICATION_CORRECTED
ATTRIBUTE_PROPOSED
ATTRIBUTE_REJECTED_UNSUPPORTED
ATTRIBUTE_CONFIRMED
ATTRIBUTE_CORRECTED
PHOTO_RENAME_REQUESTED
PHOTO_RENAMED
IDENTIFICATION_CONFIRMED
IDENTIFICATION_CONFLICT
```

---

## 42. Qwen no debe estar en ruta crítica

Si Ollama/Qwen falla:

```text
OCR + reglas + revisión humana
```

deben seguir permitiendo completar identificación.

Qwen es asistente, no dependencia crítica.

---

## 43. Timeout Qwen

Implementar timeout configurable.

Ante timeout:

```text
QWEN_UNAVAILABLE
```

No bloquear indefinidamente.

---

## 44. Logs

No registrar imágenes ni grandes OCR blobs en logs generales.

Registrar:

```text
photo_id
request_id
stage
duration
result
error_code
```

---

## 45. Tests obligatorios

Mantener los 188 tests.

Agregar al menos:

1. stage JPG;
2. stage JPEG;
3. stage PNG;
4. formato no soportado;
5. hash pre/post;
6. foto original intacta;
7. OCR con texto;
8. OCR sin texto;
9. clasificación SERIAL por texto;
10. clasificación ETIQUETA por texto;
11. NO_CLASIFICADA;
12. clasificación humana;
13. 0 fotos PENDING;
14. 1 foto INCOMPLETE;
15. 2 fotos INCOMPLETE;
16. 3 fotos READY;
17. >3 REVIEW_REQUIRED;
18. 1-2 fotos pueden confirmarse con revisión humana;
19. SELF_STORAGE no duplica bytes;
20. CONTAINED_STORAGE separa entidades;
21. serial exacto;
22. serial parcial UNCERTAIN;
23. serial no completado;
24. brand sustentado;
25. brand no sustentado rechazado;
26. model sustentado;
27. model inferido rechazado;
28. capacity normalization;
29. color NOT_EVALUATED;
30. Qwen JSON válido;
31. Qwen JSON inválido;
32. Qwen unsupported value rechazado;
33. Qwen timeout;
34. Qwen failure fallback humano;
35. provenance photo_id;
36. provenance source_text;
37. confidence null;
38. SERIAL_MULTIPLE_VALUES;
39. MODEL_MULTIPLE_VALUES;
40. BRAND_CONFLICT;
41. CAPACITY_CONFLICT;
42. LOW_VISIBILITY;
43. NO_TEXT;
44. human review;
45. human correction audit;
46. rename preview;
47. collision reject;
48. rename requires confirmation;
49. rename hash preserved;
50. rename rollback;
51. identification.json;
52. case.json atomic update;
53. identification pending initially;
54. confirm moves to completed;
55. acquisition ready only through policy;
56. API stage;
57. API analyze;
58. API review CSRF;
59. API rename CSRF;
60. API confirm CSRF;
61. web identification page;
62. web conflicts;
63. no vision claims;
64. no color inference;
65. no cloud;
66. no PhysicalDrive;
67. no EWF;
68. no AXIOM;
69. no OpenClaw;
70. `casos/` real intacto en tests.

---

## 46. Fixtures

Crear fixtures sintéticos:

```text
photo_serial.jpg
photo_label.jpg
photo_capacity.png
photo_no_text.jpg
photo_conflict_1.jpg
photo_conflict_2.jpg
```

No usar evidencia real en tests.

---

## 47. Prueba funcional de laboratorio

Después de tests:

usar fotografías de laboratorio no sensibles.

Preferir un objeto propio o fixture físico.

No evidencia real.

Demostrar:

```text
stage
→ hash
→ OCR
→ extracción
→ Qwen textual opcional
→ review
→ rename
→ confirm identification
```

---

## 48. No realizar

Prohibido:

- descargar modelo;
- `ollama pull`;
- cloud;
- VLM inexistente;
- afirmar visión real;
- evidence photos reales;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- OpenClaw;
- Portable;
- RAR;
- Word.

---

## 49. Documentación

Crear:

```text
PHOTO_IDENTIFICATION_ARCHITECTURE.md
IDENTIFICATION_JSON_SCHEMA.md
```

Documentar:

- provider OCR;
- Qwen textual;
- límites visuales;
- política fotos;
- SELF_STORAGE;
- CONTAINED_STORAGE;
- extracción;
- anti-invención;
- provenance;
- conflictos;
- review;
- rename;
- DB;
- API;
- Web;
- orchestrator;
- tool versions.

---

## 50. Criterio de aceptación

R06.1 queda COMPLETO si:

- baseline verde;
- staging seguro;
- hash/inmutabilidad;
- OCR local;
- clasificación textual;
- clasificación humana;
- extracción estructurada;
- Qwen solo textual;
- anti-invención;
- conflicts;
- provenance;
- human review;
- renombrado seguro;
- `identification.json`;
- `case.json`;
- PostgreSQL;
- auditoría;
- API;
- Web;
- CSRF;
- integración State Machine;
- fallback sin Qwen;
- ninguna afirmación de visión real;
- no evidencia real;
- no herramientas forenses;
- suite completa verde.

Estado:

```text
PHOTO_IDENTIFICATION_READY
```

Si falla requisito crítico:

```text
PHOTO_IDENTIFICATION_BLOCKED
```

---

## 51. Reporte final obligatorio

```text
SPRINT R06.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
PHOTO MODULE:
...
SUPPORTED FORMATS:
...
WINDOWS OCR:
...
QWEN:
...
QWEN ROLE:
...
VISION PROVIDER:
NONE
PHOTO COUNT POLICY:
...
SELF_STORAGE:
...
CONTAINED_STORAGE:
...
HASH INTEGRITY:
...
OCR:
...
CLASSIFICATION:
...
ATTRIBUTE EXTRACTION:
...
ANTI-INVENTION:
...
PROVENANCE:
...
CONFLICTS:
...
HUMAN REVIEW:
...
RENAMING:
...
IDENTIFICATION.JSON:
...
CASE.JSON:
...
DATABASE:
...
ORCHESTRATION:
...
API:
...
WEB:
...
CSRF:
...
AUDIT:
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
FUNCTIONAL LAB TEST:
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
RISKS:
...
BLOCKERS:
...
STATUS:
PHOTO_IDENTIFICATION_READY / PHOTO_IDENTIFICATION_BLOCKED
```

---

## 52. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. inspecciona schema DB real;
4. implementa paquete identification;
5. reutiliza Windows OCR;
6. integra Qwen solo sobre texto;
7. implementa anti-invención;
8. implementa provenance;
9. implementa conflictos;
10. implementa review;
11. implementa rename seguro;
12. genera identification.json;
13. sincroniza case.json;
14. integra PostgreSQL;
15. integra orchestrator;
16. integra API/Web/CSRF;
17. agrega tests;
18. ejecuta prueba funcional de laboratorio;
19. ejecuta suite completa;
20. entrega reporte;
21. detente;
22. NO inicies R07.

Comienza ahora.
