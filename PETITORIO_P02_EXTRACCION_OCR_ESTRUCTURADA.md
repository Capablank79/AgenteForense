# PETITORIO P02 — Extracción OCR Estructurada del Oficio Petitorio

## 1. Objetivo

Ampliar el pipeline actual de OCR/extracción para que el sistema pueda identificar y proponer de forma estructurada los campos documentales reales del Oficio Petitorio y alimentar las tablas PostgreSQL creadas en PETITORIO P01.

Flujo objetivo:

```text
ARCHIVO PETITORIO
→ STAGING + SHA-256
→ EXTRACCIÓN TEXTO / WINDOWS OCR
→ DETECCIÓN DE CAMPOS
→ PROVENIENCIA POR CAMPO
→ CONFLICTOS / INCERTIDUMBRE
→ PROPUESTA ESTRUCTURADA
→ PERSISTENCIA DEL PETITORIO
→ REVISIÓN HUMANA POSTERIOR
```

P02 NO crea todavía el caso definitivo.

P02 NO crea todavía ESPECIE ni DSM.

P02 NO ejecuta adquisición.

---

## 2. Estado de partida validado

PETITORIO P00:

```text
ACCEPTED
```

PETITORIO P01:

```text
ACCEPTED
```

Baseline actual:

```text
245 passed
```

Persistencia PostgreSQL disponible:

```text
forensic.petitions
forensic.petition_evidence_items
forensic.petition_requested_actions
forensic.petition_attachments
forensic.petition_field_reviews
```

OCR actual:

```text
WindowsOcrProvider
PdfRendererOcr
pypdf
```

Endpoints actuales:

```text
POST /api/petitions/stage
POST /api/petitions/{doc_id}/extract
GET  /api/petitions/{doc_id}
GET  /api/petitions/{doc_id}/extraction
POST /api/petitions/{doc_id}/review
POST /api/petitions/{doc_id}/draft
POST /api/petitions/{doc_id}/build-draft
```

Campos actuales extraídos:

```text
ruc
nue
oficio_number
requesting_unit
requested_diligence
```

---

## 3. Reglas obligatorias antes de implementar

TRAE debe leer:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
PETITORIO_P00_INVESTIGACION_MODELO_OFICIO_PETITORIO.md
PETITORIO_P01_PERSISTENCIA_POSTGRESQL_OFICIO_PETITORIO.md
```

Después:

1. ejecutar suite completa;
2. confirmar baseline real;
3. inspeccionar `FieldExtractor` actual;
4. inspeccionar `ConflictDetector` actual;
5. inspeccionar modelos Pydantic reales;
6. inspeccionar `PetitionPersistenceService` real;
7. inspeccionar salida OCR real del Oficio Petitorio de laboratorio;
8. inspeccionar cómo se representan actualmente `FieldProvenance`, `ExtractedField` y conflictos;
9. no asumir patrones de texto no observados;
10. no inventar campos o valores.

Si existe discrepancia entre este sprint y el código real:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de continuar.

---

## 4. Regla de idioma

Código interno, modelos, enums, JSON, columnas y API pueden mantenerse en inglés.

Toda interfaz visible al operador debe permanecer en español.

Ejemplos:

```text
petition_date
→ Fecha del oficio

prosecutor_name
→ Fiscal

investigator_name
→ Encargado de la investigación

requested_actions
→ Diligencias solicitadas
```

P02 puede ampliar la UI mínima necesaria para mostrar nuevos campos extraídos, pero no implementa todavía la grilla dinámica final de P03.

---

## 5. Principio de extracción

El extractor debe operar bajo la regla:

```text
EXTRAER SOLO LO QUE EL DOCUMENTO SUSTENTA
```

No completar por plausibilidad.

No deducir por conocimiento externo.

No inventar nombres, fechas, números, marcas, modelos, seriales o diligencias.

Si un valor no puede sostenerse directamente desde el texto fuente:

```text
NOT_FOUND
UNCERTAIN
CONFLICT
```

según corresponda.

---

## 6. Fuentes de texto permitidas

Mantener procesamiento local.

Permitido:

```text
pypdf para PDF con capa de texto
Windows OCR es-ES
PdfRendererOcr para PDF escaneado
```

No usar servicios cloud.

No enviar Petitorios a Internet.

No depender de un LLM para confirmar hechos documentales.

Si se utiliza lógica asistida futura, cualquier valor debe seguir sustentado por texto fuente y revisión humana.

---

## 7. Proveniencia obligatoria por campo

Cada campo extraído debe conservar:

```text
field_name
observed_value
source_page
source_excerpt
extraction_method
status
```

Cuando aplique:

```text
proposed_value
normalization_rule
```

No perder el texto fuente.

Ejemplo:

```json
{
  "field_name": "ruc",
  "observed_value": "2601254545-1",
  "source_page": 1,
  "source_excerpt": "RUC 2601254545-1",
  "extraction_method": "REGEX_LABEL_CONTEXT",
  "status": "EXTRACTED"
}
```

---

## 8. Campos documentales a extraer

P02 debe ampliar el extractor para intentar identificar, cuando estén presentes:

### 8.1. Documento

```text
document_type
petition_number
petition_date
city
log_reference
page_count
```

`original_filename`, `mime_type`, `size_bytes` y `sha256` provienen de ingestión/staging y persistencia, no del OCR.

### 8.2. Causa

```text
ruc
crime_context
other_references
```

### 8.3. Solicitante

```text
requesting_unit
prosecutor_office
prosecutor_name
investigator_name
investigator_rank
contact_details
addressee
informed_copies
```

### 8.4. Evidencias declaradas

```text
nue_number
quantity
description_original
evidence_type_declared
brand_declared
model_declared
serial_number_declared
capacity_declared
source_page
source_text
```

### 8.5. Diligencias solicitadas

```text
source_text
normalized_action
action_order
source_page
```

### 8.6. Actas / anexos / documentos referenciados

```text
attachment_type
description
reference_number
source_page
```

`physically_received` NO debe inferirse desde OCR.

---

## 9. Extracción de número de oficio

Investigar el patrón real del documento de laboratorio.

Aceptar variantes reales observadas como:

```text
OFICIO N°
OFICIO Nº
ORD. N°
N°
NO
```

solo si el contexto documental permite identificar que corresponde efectivamente al número del oficio.

No confundir con:

```text
NUE
RUC
Bitácora
número de teléfono
serial
```

Si existen múltiples candidatos:

```text
CONFLICT
```

No seleccionar uno silenciosamente.

---

## 10. Extracción de fecha del oficio

Detectar fechas asociadas al encabezado o emisión del oficio.

Conservar:

```text
observed_value
normalized_value
source_excerpt
source_page
```

Normalización permitida solo cuando sea inequívoca.

Ejemplo conceptual:

```text
21 AGO. 2026
→ 2026-08-21
```

Pero conservar también el texto original.

Si OCR produce año ambiguo:

```text
UNCERTAIN
```

No completar dígitos faltantes por contexto.

---

## 11. Ciudad / lugar

Extraer solo si está asociado claramente a fecha/encabezado o lugar de emisión.

No asumir Santiago por defecto.

No usar ubicación del equipo ni del operador.

---

## 12. RUC

Mantener el extractor actual si es correcto.

Debe:

- permitir un RUC por Oficio salvo evidencia real contraria;
- conservar forma original;
- detectar múltiples candidatos;
- marcar conflicto si existen candidatos incompatibles;
- no inventar validación jurídica no definida.

---

## 13. NUE y evidencias declaradas

El sistema debe soportar:

```text
1 Petitorio
→ N NUE
```

Y por cada NUE:

```text
N Evidence Items
```

Debe detectar bloques contextuales similares a:

```text
N.U.E. 7746537 : 01 Computador portátil, marca Lenovo, E-41-55, Nro de serie MPIZGTX4
```

La extracción debe intentar separar:

```text
nue_number
quantity
description_original
evidence_type_declared
brand_declared
model_declared
serial_number_declared
capacity_declared
```

pero solo cuando cada valor esté sustentado.

### Regla crítica

No convertir automáticamente:

```text
evidence_type_declared
```

en:

```text
species
```

definitiva.

No crear DSM.

---

## 14. Marca, modelo y número de serie

Buscar patrones explícitos de contexto:

```text
marca
modelo
serie
nro de serie
número de serie
S/N
```

No corregir OCR por plausibilidad.

Ejemplo:

```text
MPIZGTX4
```

si OCR devuelve algo ambiguo:

```text
MPI?GTX4
```

no completar el carácter faltante.

Usar:

```text
UNCERTAIN
```

---

## 15. Cantidad

Extraer cantidad cuando aparezca explícitamente vinculada a la evidencia.

Ejemplo:

```text
01 Computador portátil
```

puede normalizarse a:

```text
quantity = 1
```

conservando `source_text`.

No inferir cantidad 1 solo porque exista un elemento descrito si el documento no lo sustenta de forma suficiente.

---

## 16. Capacidad

Extraer capacidad solo si el Petitorio la declara explícitamente.

Conservar:

```text
capacity_declared
```

como texto documental.

No convertir automáticamente a bytes en P02 salvo que exista una regla de normalización ya validada y sin pérdida semántica.

---

## 17. Unidad solicitante

Corregir el defecto observado anteriormente: el extractor no debe devolver la página completa como `requesting_unit`.

Debe utilizar contexto de encabezado y límites razonables.

Si no puede aislar la unidad con seguridad:

```text
UNCERTAIN
```

El operador podrá corregirla en P03.

No convertir una corrección humana previa en regla automática sin evidencia de patrón documental repetible.

---

## 18. Fiscalía y Fiscal

Extraer de forma separada:

```text
prosecutor_office
prosecutor_name
```

Ejemplo conceptual del documento real:

```text
Fiscalía Metropolitana Centro Norte
Fiscal Javier ...
```

No mezclar ambos campos.

Si solo aparece la Fiscalía pero no el nombre del Fiscal:

```text
prosecutor_office = EXTRACTED
prosecutor_name = NOT_FOUND
```

---

## 19. Encargado de investigación / funcionario

Extraer cuando exista un funcionario claramente vinculado al oficio o investigación.

Separar cuando sea posible:

```text
investigator_name
investigator_rank
contact_details
```

No confundir:

- firmante del oficio;
- destinatario;
- fiscal;
- funcionario de copia;
- encargado de investigación.

Si el rol no es inequívoco:

```text
UNCERTAIN
```

---

## 20. Bitácora u otras referencias

Extraer referencias del tipo:

```text
Bitácora Web N° ...
```

como:

```text
log_reference
```

No confundir con número de oficio o NUE.

---

## 21. Delito / contexto de causa

Extraer únicamente el texto expresamente indicado.

Conservarlo como:

```text
crime_context
```

No inferir calificación jurídica.

No reinterpretar el delito.

---

## 22. Diligencias solicitadas

El sistema debe identificar el bloque de texto que expresa lo solicitado sobre la evidencia.

Preservar siempre:

```text
source_text
```

Puede generar uno o varios registros en:

```text
petition_requested_actions
```

Solo cuando exista segmentación razonablemente sustentada.

Si el documento solicita varias acciones en una sola frase, puede mantenerse un único `source_text` y varias propuestas normalizadas sujetas a revisión.

No inventar acciones.

---

## 23. Actas y anexos

Detectar referencias explícitas a:

```text
Acta
Anexo
Cadena de custodia
Adjunto
Documento
```

Crear propuestas en:

```text
petition_attachments
```

Solo si existe referencia textual.

Nunca marcar automáticamente:

```text
physically_received = true
```

por el solo hecho de aparecer mencionado.

---

## 24. Conflictos

Extender `ConflictDetector` para nuevos campos cuando corresponda.

Ejemplos:

```text
2 RUC distintos
2 números de oficio incompatibles
2 fechas candidatas de emisión
2 seriales asociados al mismo item
NUE duplicada con descripciones contradictorias
```

Resultado:

```text
CONFLICT
```

No elegir un valor automáticamente.

---

## 25. Normalización segura

Permitir normalización únicamente cuando no cambie el hecho documental.

Ejemplos permitidos:

```text
espacios repetidos
saltos de línea internos
mayúsculas/minúsculas para matching
fecha inequívoca
cantidad '01' → 1
```

No permitido:

```text
corregir serial por marca conocida
completar año ilegible
inferir modelo
inferir fiscalía
inventar unidad
```

Siempre conservar el valor observado original.

---

## 26. Persistencia PostgreSQL

Después de la extracción, persistir de forma controlada:

### Tabla principal

```text
forensic.petitions
```

Campos documentales detectados.

### Evidencias

```text
forensic.petition_evidence_items
```

### Diligencias

```text
forensic.petition_requested_actions
```

### Actas / anexos

```text
forensic.petition_attachments
```

### Revisión / provenance

```text
forensic.petition_field_reviews
```

P02 debe generar registros `EXTRACTED`, `UNCERTAIN`, `CONFLICT` o `NOT_FOUND` según corresponda.

No marcar automáticamente como `HUMAN_CONFIRMED`.

---

## 27. Idempotencia

Reejecutar extracción sobre el mismo Petitorio no debe generar duplicados silenciosos.

Investigar e implementar una estrategia segura para:

```text
extract → persist
re-extract → reconcile/update proposals
```

No duplicar evidence items, requested actions o attachments por cada reintento.

No borrar revisión humana ya existente sin decisión explícita.

Si existe revisión humana y se reejecuta OCR:

```text
NO SOBRESCRIBIR confirmed_value
```

Registrar nueva observación o conflicto según arquitectura real.

---

## 28. Auditoría

Registrar como mínimo:

```text
petition_extraction_started
petition_text_extracted
petition_field_extracted
petition_field_uncertain
petition_conflict_detected
petition_evidence_item_extracted
petition_requested_action_extracted
petition_attachment_reference_extracted
petition_extraction_persisted
petition_extraction_failed
```

No registrar datos sensibles completos si no es necesario.

Conservar trazabilidad mediante IDs y provenance.

---

## 29. API

Mantener compatibilidad con:

```text
POST /api/petitions/{doc_id}/extract
GET /api/petitions/{doc_id}/extraction
```

Ampliar respuesta estructurada según sea necesario, sin romper consumidores actuales salvo cambio documentado y testeado.

No crear endpoints de adquisición.

Mantener CSRF en endpoints mutables.

---

## 30. UI mínima en P02

La interfaz puede mostrar los nuevos campos detectados, pero todavía no debe convertirse en la grilla completa de P03.

Debe permanecer en español.

Ejemplos:

```text
Número de oficio
Fecha del oficio
Fiscalía
Fiscal
Encargado de la investigación
Evidencias declaradas
Diligencias solicitadas
Actas y anexos
```

Estados visibles:

```text
Extraído
Incierto
Conflicto
No encontrado
```

No mostrar estados internos ingleses como texto principal.

---

## 31. CaseStructureDraft

P02 puede ampliar el mapper únicamente para aceptar los nuevos datos documentales ya estructurados.

Pero el draft NO debe crear:

```text
species
dsms
storage_relation
```

El draft puede contener referencias del Petitorio aprobado/propuesto.

La creación real del caso sigue bloqueada hasta sprints posteriores.

---

## 32. Pruebas obligatorias

Mantener:

```text
245 passed
```

o más.

Agregar tests como mínimo para:

1. número de oficio válido;
2. múltiples candidatos a número de oficio → CONFLICT;
3. fecha de oficio inequívoca;
4. fecha OCR ambigua → UNCERTAIN;
5. ciudad explícita;
6. no asumir ciudad;
7. RUC actual sin regresión;
8. múltiples RUC → conflicto;
9. una NUE;
10. múltiples NUE;
11. múltiples evidencias por NUE;
12. cantidad explícita;
13. descripción original preservada;
14. marca explícita;
15. modelo explícito;
16. serial explícito;
17. serial incompleto no completado;
18. capacidad declarada;
19. requesting_unit acotada;
20. requesting_unit página completa rechazada/incierta;
21. fiscalía extraída;
22. fiscal extraído;
23. fiscal ausente → NOT_FOUND;
24. investigador separado de firmante cuando el contexto lo permite;
25. bitácora extraída;
26. delito/contexto preservado;
27. diligencia source_text preservado;
28. varias diligencias;
29. acta referenciada;
30. anexo referenciado;
31. physically_received no inferido;
32. provenance por campo;
33. source_page correcto;
34. source_excerpt correcto;
35. conflicto persistido;
36. extracted field persistido;
37. evidence item persistido;
38. requested action persistida;
39. attachment persistido;
40. re-extracción idempotente;
41. revisión humana existente no sobrescrita;
42. confirmed_value preservado;
43. CSRF sin regresión;
44. UI visible modificada en español;
45. no case creado;
46. no NUE definitiva creada;
47. no species creada;
48. no DSM creado;
49. no PhysicalDrive;
50. no ewfacquire;
51. no ewfverify;
52. DB test aislada;
53. suite completa en verde.

---

## 33. Prueba funcional real con el Oficio Petitorio de laboratorio

Después de todos los tests:

usar el mismo Oficio Petitorio real de laboratorio ya utilizado.

Verificar extracción real de tantos campos como el documento efectivamente contenga.

Registrar, como mínimo:

```text
RUC
NUE
Número de oficio
Fecha del oficio
Unidad solicitante
Fiscalía
Fiscal
Bitácora
Descripción de evidencia
Marca
Modelo
Serial
Diligencias
Actas/anexos si existen
```

Si un campo no está presente o el OCR no permite extraerlo con seguridad:

```text
NOT_FOUND
UNCERTAIN
```

No forzar PASS mediante valores manuales durante la prueba automática de extracción.

La corrección manual pertenece a P03.

---

## 34. Evidencia de prueba funcional

El reporte debe incluir por cada campo relevante:

```text
FIELD:
...

STATUS:
EXTRACTED / UNCERTAIN / CONFLICT / NOT_FOUND

VALUE:
...

SOURCE PAGE:
...

SOURCE EXCERPT:
...

EXTRACTION METHOD:
...
```

No es necesario incluir el texto OCR completo en el reporte si contiene información sensible innecesaria.

---

## 35. Seguridad y operaciones prohibidas

P02 NO debe:

- crear caso definitivo;
- crear `nues` definitivas;
- crear `species`;
- crear `dsms`;
- abrir PhysicalDrive;
- ejecutar `ewfacquire`;
- ejecutar `ewfverify`;
- crear E01;
- modificar evidencia física;
- integrar AXIOM;
- generar Portable Case;
- generar Word;
- usar cloud;
- desactivar CSRF;
- sobrescribir correcciones humanas existentes.

---

## 36. Criterios de aceptación

P02 queda COMPLETO únicamente si:

- Prompt Maestro leído;
- Regla Permanente leída;
- P00 leído;
- P01 leído;
- baseline ejecutado;
- extractor actual inspeccionado;
- OCR real inspeccionado;
- nuevos campos implementados;
- provenance por campo preservada;
- evidencias declaradas estructuradas;
- diligencias estructuradas;
- actas/anexos estructurados;
- conflictos detectados;
- valores inciertos no inventados;
- persistencia PostgreSQL integrada;
- re-extracción idempotente;
- revisión humana previa no sobrescrita;
- API existente sin regresión;
- CSRF intacto;
- UI modificada visible en español;
- prueba funcional real ejecutada;
- ningún caso definitivo creado;
- ninguna operación forense de adquisición ejecutada;
- suite completa en verde.

---

## 37. Reporte final obligatorio

TRAE debe entregar:

```text
PETITORIO P02:
COMPLETED / BLOCKED

PROMPT MAESTRO:
READ / NOT READ

REGLA PERMANENTE:
READ / NOT READ

P00:
READ / NOT READ

P01:
READ / NOT READ

BASELINE:
...

OCR PROVIDER:
...

PDF TEXT EXTRACTION:
...

PDF RENDER OCR:
...

FIELD EXTRACTOR MODIFIED:
...

CONFLICT DETECTOR MODIFIED:
...

FIELDS IMPLEMENTED:
...

DOCUMENT FIELDS:
...

CASE FIELDS:
...

REQUESTER FIELDS:
...

EVIDENCE FIELDS:
...

REQUESTED ACTIONS:
...

ATTACHMENTS:
...

PROVENANCE:
PASS / FAIL

IDEMPOTENT RE-EXTRACTION:
PASS / FAIL

HUMAN REVIEW PRESERVED:
PASS / FAIL

POSTGRESQL PERSISTENCE:
PASS / FAIL

API COMPATIBILITY:
PASS / FAIL

CSRF:
PASS / FAIL

UI ESPAÑOL:
PASS / FAIL

REAL PETITION TEST:
PASS / FAIL

REAL FIELD RESULTS:
...

CASE CREATED:
NO

NUE DEFINITIVE CREATED:
NO

SPECIES CREATED:
NO

DSM CREATED:
NO

PHYSICALDRIVE:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

TESTS ADDED:
...

TESTS FINAL:
...

RISKS / LIMITATIONS:
...

STATUS:
PETITION_EXTRACTION_READY_FOR_P03 /
PETITION_EXTRACTION_BLOCKED
```

---

## 38. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Leer P00.
4. Leer P01.
5. Ejecutar baseline.
6. Inspeccionar `FieldExtractor` real.
7. Inspeccionar `ConflictDetector` real.
8. Inspeccionar OCR real del Petitorio de laboratorio.
9. Ampliar campos documentales.
10. Implementar extracción de evidencias declaradas.
11. Implementar extracción de diligencias.
12. Implementar extracción de actas/anexos.
13. Mantener provenance completa.
14. Persistir propuestas en PostgreSQL.
15. Implementar idempotencia de re-extracción.
16. No sobrescribir revisión humana existente.
17. Mantener API compatible.
18. Mantener CSRF.
19. Mantener toda UI visible en español.
20. Agregar tests.
21. Ejecutar suite completa.
22. Ejecutar prueba funcional con el Oficio Petitorio real de laboratorio.
23. Registrar resultados campo por campo.
24. No crear caso.
25. No crear ESPECIE.
26. No crear DSM.
27. No ejecutar adquisición.
28. Entregar reporte final.
29. **NO iniciar PETITORIO P03.**

Comienza ahora.
