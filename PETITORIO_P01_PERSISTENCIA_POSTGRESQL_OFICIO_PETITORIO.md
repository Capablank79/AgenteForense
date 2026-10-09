# PETITORIO P01 — Persistencia PostgreSQL del Oficio Petitorio

## 1. Objetivo

Implementar la persistencia estructurada del **Oficio Petitorio** en PostgreSQL a partir del diseño validado en PETITORIO P00.

Este sprint debe crear la base persistente para:

```text
OFICIO PETITORIO
→ documento
→ evidencias declaradas
→ diligencias solicitadas
→ actas/anexos
→ revisiones humanas por campo
→ estado de revisión/aprobación
```

El objetivo NO es crear todavía el caso definitivo ni ejecutar adquisición.

El Oficio Petitorio debe quedar almacenado como entidad propia e independiente del caso.

## 2. Estado de partida validado por P00

Baseline:

```text
243 passed
```

Entorno:

```text
DB operacional: agente_forense_db
DB test:        agente_forense_test
PostgreSQL:     127.0.0.1:5433
Schema:         forensic
```

Aislamiento de tests:

```text
PASS
```

Implementación actual relevante:

```text
src/agente_forense/petition/
```

Componentes existentes:

```text
PetitionService
FieldExtractor
ConflictDetector
WindowsOcrProvider
PdfRendererOcr
DraftMapper
PetitionPersistenceService
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

Actualmente NO existen tablas PostgreSQL específicas de Petitorio.

## 3. Reglas obligatorias antes de implementar

TRAE debe leer:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
PETITORIO_P00_INVESTIGACION_MODELO_OFICIO_PETITORIO.md
```

Después:

1. ejecutar la suite completa;
2. inspeccionar el número real de la última migración;
3. inspeccionar convenciones reales de modelos SQLAlchemy;
4. inspeccionar repositories existentes;
5. inspeccionar patrón transaccional actual;
6. inspeccionar política real de FK y `ON DELETE`;
7. inspeccionar auditoría actual;
8. inspeccionar `FileStore` / tabla `files`;
9. confirmar aislamiento de DB de tests;
10. no asumir nombres de migración ni helpers inexistentes.

Si aparece una discrepancia material entre P00 y el código real:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de continuar.

## 4. Regla de idioma

Los nombres internos pueden estar en inglés.

Ejemplo:

```text
petition_number
petition_date
requesting_unit
prosecutor_name
evidence_items
requested_actions
attachments
```

Toda interfaz visible al operador debe permanecer en español.

P01 es principalmente de persistencia, pero cualquier mensaje o pantalla que se modifique debe cumplir:

```text
UI OPERADOR = ESPAÑOL
```

No mostrar al operador nombres técnicos internos como sustituto de etiquetas en español.

## 5. Principio arquitectónico obligatorio

Mantener:

```text
OFICIO PETITORIO != CASO
```

La entidad Petitorio debe poder existir en PostgreSQL sin que exista todavía un registro definitivo en:

```text
cases
```

Relación futura:

```text
PETITION APPROVED
→ CaseStructureDraft
→ creación del caso
```

No crear automáticamente `cases`, `nues`, `species` ni `dsms` en P01.

## 6. Migración PostgreSQL

Crear la **siguiente migración real disponible**, determinada después de inspeccionar el repositorio.

NO hardcodear número de migración desde este documento.

La migración debe crear las tablas necesarias dentro de:

```text
forensic
```

Como mínimo:

```text
petitions
petition_evidence_items
petition_requested_actions
petition_attachments
petition_field_reviews
```

Los nombres pueden ajustarse únicamente si las convenciones reales del repositorio justifican otro nombre.

Documentar cualquier diferencia.

## 7. Tabla principal `petitions`

Implementar una tabla principal equivalente a:

```text
forensic.petitions
```

Campos mínimos:

```text
id
file_id

document_type
petition_number
petition_date
city
log_reference

ruc
crime_context
other_references

requesting_unit
prosecutor_office
prosecutor_name
investigator_name
investigator_rank
contact_details
addressee
informed_copies

processing_status
review_status

sha256

created_at
updated_at
```

### 7.1. `id`

Usar UUID siguiendo las convenciones actuales del proyecto.

### 7.2. `file_id`

FK hacia:

```text
forensic.files.id
```

Debe vincular el Petitorio con el archivo ingresado/controlado por el sistema.

No duplicar binarios dentro de PostgreSQL.

### 7.3. Hash

Persistir SHA-256 del archivo fuente.

El SHA-256 almacenado debe corresponder al artefacto staged validado.

No recalcular un valor diferente silenciosamente.

Si existe discrepancia:

```text
PETITION_HASH_MISMATCH
```

o error equivalente controlado.

### 7.4. Metadata de archivo

Los siguientes datos deben obtenerse preferentemente desde el registro de archivo asociado cuando ya estén persistidos allí:

```text
original_filename
mime_type
size_bytes
```

No duplicar innecesariamente información si el modelo `files` ya la representa de forma canónica.

Si P00 propuso esos campos pero el repositorio ya dispone de ellos en `files`, documentar la normalización.

## 8. Estados del Petitorio

Inspeccionar primero los enums existentes.

Definir estados claros y centralizados.

El modelo debe poder representar como mínimo el ciclo conceptual:

```text
STAGED
TEXT_EXTRACTED
FIELDS_EXTRACTED
REVIEW_REQUIRED
REVIEW_COMPLETED
APPROVED
FAILED
```

No usar strings dispersos si existen enums/modelos apropiados.

No duplicar estados semánticamente equivalentes si el código actual ya los posee.

### Regla

`APPROVED` solo puede alcanzarse cuando la revisión humana requerida esté resuelta.

P01 debe persistir el estado, pero no necesita rediseñar todavía toda la UI de revisión; eso corresponde a P03.

## 9. Tabla `petition_evidence_items`

Crear relación:

```text
1 Petition
→ N Evidence Items
```

Campos mínimos:

```text
id
petition_id
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
created_at
```

### Reglas

- permitir múltiples NUE;
- permitir múltiples evidencias para una misma NUE;
- no asumir una sola evidencia;
- no crear `species`;
- no crear `dsms`;
- no convertir automáticamente descripción documental en identificación física.

Toda información de esta tabla significa:

```text
DECLARADO EN EL PETITORIO
```

No:

```text
CONFIRMADO FÍSICAMENTE
```

## 10. Tabla `petition_requested_actions`

Crear relación:

```text
1 Petition
→ N Requested Actions
```

Campos mínimos:

```text
id
petition_id
action_order
source_text
normalized_action
source_page
created_at
```

### Regla crítica

`source_text` debe preservar el texto documental.

`normalized_action` puede ser null.

No reemplazar ni sobrescribir `source_text` mediante normalización.

No inventar acciones no sustentadas por el documento.

## 11. Tabla `petition_attachments`

Crear relación:

```text
1 Petition
→ N Attachments / Actas / Referencias documentales
```

Campos mínimos:

```text
id
petition_id
attachment_type
description
reference_number
source_page
physically_received
created_at
```

### `attachment_type`

No imponer un catálogo cerrado si el diseño actual no lo justifica.

Como mínimo debe poder representar conceptualmente:

```text
ACTA
ANEXO
CADENA_CUSTODIA
OTRO_DOCUMENTO
REFERENCIA_DOCUMENTAL
```

Si se implementa Enum:

- permitir evolución controlada;
- no inventar categorías;
- documentar exactamente las soportadas.

### `physically_received`

Debe diferenciar:

```text
documento mencionado en el oficio
```

de:

```text
documento efectivamente recibido
```

No marcar `true` automáticamente por el solo hecho de aparecer en OCR.

## 12. Tabla `petition_field_reviews`

Crear relación:

```text
1 Petition
→ N Field Reviews
```

Debe conservar trazabilidad de revisión humana.

Campos mínimos:

```text
id
petition_id
field_name
observed_value
proposed_value
confirmed_value
source_page
source_excerpt
extraction_method
status
review_action
reviewed_by
reviewed_at
created_at
```

### 12.1. Historial

No perder el valor observado original cuando el operador corrige un campo.

Ejemplo:

```text
field_name:
requesting_unit

observed_value:
<texto OCR defectuoso>

confirmed_value:
BRIGADA INVESTIGADORA DE DELITOS SEXUALES METROPOLITANA

status:
HUMAN_CORRECTED
```

El valor confirmado no debe sobrescribir silenciosamente la observación histórica.

### 12.2. Estados candidatos

Compatibilizar con los modelos actuales:

```text
EXTRACTED
UNCERTAIN
CONFLICT
NOT_FOUND
NOT_APPLICABLE
HUMAN_CONFIRMED
HUMAN_CORRECTED
```

No duplicar enums existentes sin necesidad.

### 12.3. Acción de revisión

Debe poder distinguir al menos:

```text
CONFIRM
CORRECT
MARK_NOT_FOUND
MARK_NOT_APPLICABLE
```

siempre sujeto a compatibilidad con el modelo real.

## 13. Integridad referencial

Seguir las convenciones reales del schema `forensic`.

No introducir `ON DELETE CASCADE` si contradice la política vigente de preservación/auditoría.

Preferir comportamiento conservador y explícito.

Las filas hijas no deben quedar huérfanas.

Verificar:

```text
petition_evidence_items.petition_id
petition_requested_actions.petition_id
petition_attachments.petition_id
petition_field_reviews.petition_id
```

como FK válidas.

## 14. Índices

Investigar y crear índices útiles para uso operacional.

Como mínimo evaluar:

```text
petitions.ruc
petitions.petition_number
petitions.processing_status
petitions.review_status
petitions.file_id
petition_evidence_items.petition_id
petition_evidence_items.nue_number
petition_requested_actions.petition_id
petition_attachments.petition_id
petition_field_reviews.petition_id
petition_field_reviews.field_name
```

No crear índices redundantes.

Documentar índices implementados.

## 15. Restricciones y validaciones

Implementar constraints únicamente cuando estén justificadas.

Como mínimo:

- PK obligatoria;
- FK válida;
- timestamps coherentes;
- `quantity > 0` cuando quantity no sea null;
- `action_order >= 1` cuando corresponda;
- SHA-256 con formato válido si el proyecto ya dispone de validador;
- estados limitados al enum definido.

No inventar restricciones jurídicas sobre:

```text
RUC
NUE
número de oficio
```

que no estén sustentadas.

Mantener las validaciones seguras ya existentes.

## 16. Repository / Persistence Service

Implementar o ampliar la capa existente:

```text
PetitionPersistenceService
```

siguiendo separación de responsabilidades.

Debe permitir, como mínimo:

```text
create_petition(...)
get_petition(...)
add_evidence_item(...)
add_requested_action(...)
add_attachment(...)
add_field_review(...)
update_review_status(...)
update_processing_status(...)
```

Los nombres exactos pueden variar según arquitectura real.

No exponer SQL directo desde rutas web.

## 17. Persistencia transaccional

La persistencia de un Petitorio aprobado o de una actualización estructurada debe ser transaccional.

Ejemplo conceptual:

```text
BEGIN
  petition
  evidence_items
  requested_actions
  attachments
  field_reviews
  audit event
COMMIT
```

Ante fallo:

```text
ROLLBACK
```

No dejar Petitorio parcialmente persistido cuando la operación debía ser atómica.

Si el modelo actual requiere persistencia incremental durante revisión:

- documentar qué partes son incrementales;
- mantener transacciones unitarias coherentes;
- no mezclar estados imposibles.

## 18. Auditoría

Registrar operaciones relevantes.

Como mínimo:

```text
petition_created
petition_file_linked
petition_evidence_item_added
petition_requested_action_added
petition_attachment_added
petition_field_review_recorded
petition_status_changed
petition_approved
petition_persistence_failed
```

Usar la infraestructura de auditoría existente.

Registrar:

```text
timestamp
petition_id
action
result
operator
error
```

cuando corresponda.

No almacenar contenido sensible innecesario en logs.

## 19. Relación con staging actual

Actualmente el staging utiliza:

```text
Path(tempfile.gettempdir())
/ "agente_forense_staged_petitions"
/ doc_id
```

y memoria:

```text
_STAGED_DOCUMENTS
_STAGED_EXTRACTIONS
```

P01 debe integrar persistencia sin destruir todavía el pipeline existente.

Reglas:

1. no romper staging;
2. no eliminar archivo staged antes de persistencia confirmada;
3. conservar SHA-256;
4. no crear caso automáticamente;
5. permitir que P02/P03 continúen usando la extracción actual mientras se migra a persistencia estructurada.

Si se necesita un adaptador temporal:

```text
STAGING
→ PetitionPersistenceService
```

documentarlo.

## 20. No persistir automáticamente como caso

Prohibido en P01:

```text
crear cases
crear nues definitivas
crear species
crear dsms
crear carpetas de caso
crear case.json definitivo
```

El resultado final de P01 es:

```text
OFICIO PETITORIO PERSISTIBLE Y CONSULTABLE
```

No:

```text
CASO CREADO
```

## 21. API mínima de persistencia

No rediseñar toda la API en P01.

Pero adaptar lo mínimo necesario para que el backend pueda:

```text
guardar Petitorio
consultar Petitorio
consultar relaciones hijas
persistir revisión humana
persistir estado
```

Si se crean endpoints nuevos, deben:

- mantener CSRF para mutaciones;
- usar errores controlados;
- no exponer tracebacks;
- no romper endpoints actuales;
- documentarse.

La interfaz avanzada en grilla pertenece a P03.

## 22. UI en P01

No implementar todavía la grilla completa.

Solo si es necesario para validación:

- mostrar estado de persistencia;
- mostrar mensajes en español;
- no mostrar nombres técnicos ingleses como texto principal;
- no alterar el flujo visual existente más de lo necesario.

Ejemplos:

```text
Petitorio guardado correctamente
Petitorio pendiente de revisión
Error al guardar el petitorio
```

No:

```text
PETITION_PERSISTENCE_EXCEPTION
```

como único mensaje visible.

El código técnico puede quedar en logs.

## 23. Tests obligatorios

Mantener:

```text
243 passed
```

o más.

Agregar tests como mínimo para:

1. crear `petitions`;
2. FK a `files`;
3. SHA-256 persistido;
4. múltiples petitions;
5. múltiples evidence items;
6. múltiples NUE dentro de evidence items;
7. múltiples acciones solicitadas;
8. orden de acciones;
9. múltiples attachments;
10. attachment mencionado pero no recibido;
11. múltiples field reviews;
12. preservar `observed_value`;
13. persistir `confirmed_value`;
14. `HUMAN_CORRECTED`;
15. `HUMAN_CONFIRMED`;
16. `NOT_FOUND`;
17. `NOT_APPLICABLE` si se implementa;
18. rollback ante fallo hijo;
19. FK inválida rechazada;
20. petition consultable;
21. estados persistidos;
22. aprobación no crea caso;
23. aprobación no crea NUE definitiva;
24. aprobación no crea species;
25. aprobación no crea DSM;
26. DB test aislada;
27. DB operacional no contaminada;
28. audit event registrado;
29. endpoints existentes sin regresión;
30. CSRF sigue activo;
31. interfaz visible modificada permanece en español;
32. suite completa en verde.

## 24. Prueba funcional controlada

Después de tests:

usar el Petitorio de laboratorio ya utilizado.

Permitido:

```text
staging
hash
OCR existente
review existente
persistencia PostgreSQL de Petitorio
consulta del Petitorio persistido
```

No permitido:

```text
crear caso definitivo
PhysicalDrive
ewfacquire
ewfverify
E01
AXIOM
```

Verificar en DB controlada:

```text
1 petition
>= 1 evidence item
>= 1 field review
```

Persistir únicamente datos realmente revisados/confirmados.

Si todavía algunos campos no son extraídos por P02, pueden quedar:

```text
NULL
NOT_FOUND
PENDING
```

según el modelo.

No inventar valores.

## 25. Criterios de aceptación

P01 queda COMPLETO únicamente si:

- Prompt Maestro leído;
- Regla Permanente leída;
- P00 leído;
- baseline registrado;
- aislamiento DB confirmado;
- migración real creada correctamente;
- tablas Petitorio creadas;
- FKs válidas;
- índices justificados;
- repositories/services implementados;
- persistencia transaccional;
- field review conserva observación y corrección;
- Petitorio puede existir sin Case;
- múltiples NUE/evidence items soportados;
- múltiples diligencias soportadas;
- múltiples actas/anexos soportados;
- auditoría integrada;
- staging no roto;
- endpoints anteriores no rotos;
- CSRF no debilitado;
- UI modificada visible en español;
- DB operacional no contaminada por pytest;
- todos los tests pasan;
- prueba funcional de persistencia pasa;
- ninguna operación forense real ejecutada.

## 26. Fuera de alcance

NO implementar todavía:

```text
extracción OCR ampliada de todos los nuevos campos
grilla dinámica completa
creación definitiva del caso
creación de species
creación de DSM
selección de write blocker
PhysicalDrive
ewfacquire
ewfverify
E01
AXIOM
Portable Case
Word
```

La extracción ampliada corresponde a P02.

La grilla completa corresponde a P03.

## 27. Reporte final obligatorio

TRAE debe entregar:

```text
PETITORIO P01:
COMPLETED / BLOCKED

PROMPT MAESTRO:
READ / NOT READ

REGLA PERMANENTE:
READ / NOT READ

P00:
READ / NOT READ

BASELINE:
...

DB OPERACIONAL:
...

DB TEST:
...

TEST ISOLATION:
PASS / FAIL

MIGRATION CREATED:
...

TABLES CREATED:
...

PETITIONS TABLE:
...

EVIDENCE ITEMS TABLE:
...

REQUESTED ACTIONS TABLE:
...

ATTACHMENTS TABLE:
...

FIELD REVIEWS TABLE:
...

FOREIGN KEYS:
...

ON DELETE POLICY:
...

INDEXES:
...

ENUMS / STATES:
...

PERSISTENCE SERVICE:
...

TRANSACTIONAL PERSISTENCE:
PASS / FAIL

AUDIT:
PASS / FAIL

STAGING COMPATIBILITY:
PASS / FAIL

EXISTING PETITION ENDPOINTS:
PASS / FAIL

CSRF:
PASS / FAIL

UI ESPAÑOL:
PASS / FAIL

REAL LAB PETITION PERSISTED:
YES / NO

CASE CREATED:
NO

NUE DEFINITIVE CREATED:
NO

SPECIES CREATED:
NO

DSM CREATED:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

PHYSICALDRIVE:
NO

TESTS ADDED:
...

TESTS FINAL:
...

RISKS / LIMITATIONS:
...

STATUS:
PETITION_PERSISTENCE_READY_FOR_P02 /
PETITION_PERSISTENCE_BLOCKED
```

## 28. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Leer PETITORIO P00.
4. Ejecutar baseline.
5. Confirmar DB operacional y DB test.
6. Confirmar aislamiento pytest.
7. Inspeccionar última migración real.
8. Inspeccionar patrones SQLAlchemy/repository.
9. Crear siguiente migración válida.
10. Crear tablas Petitorio.
11. Crear relaciones 1:N.
12. Integrar `PetitionPersistenceService`.
13. Implementar persistencia transaccional.
14. Integrar auditoría.
15. Mantener staging actual funcional.
16. No crear caso.
17. No crear NUE definitiva.
18. No crear especies.
19. No crear DSM.
20. No ejecutar adquisición.
21. Mantener CSRF estricto.
22. Mantener cualquier UI visible en español.
23. Agregar tests.
24. Ejecutar suite completa.
25. Ejecutar prueba funcional controlada de persistencia.
26. Entregar reporte final.
27. **NO iniciar PETITORIO P02.**

Comienza ahora.
