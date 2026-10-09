# PETITORIO P00 — Investigación y modelado del Oficio Petitorio

## 1. Objetivo

Antes de modificar el sistema Petitorio, investigar el estado real del repositorio y producir el diseño definitivo para:

```text
OFICIO PETITORIO
→ OCR
→ extracción estructurada
→ revisión humana
→ persistencia PostgreSQL
→ aprobación
→ CaseStructureDraft
```

**NO implementar todavía la nueva base de datos ni modificar el workflow productivo.**

Este sprint existe para fijar correctamente la primera etapa operativa del caso: el ingreso, lectura, estructuración, revisión y aprobación del Oficio Petitorio.

---

## 2. Reglas obligatorias

Antes de cualquier acción, TRAE debe leer:

- `PROMPT_MAESTRO.md`
- `REGLA_PERMANENTE_PRE_SPRINT.md`
- documentación vigente de reconstrucción
- reportes actuales del pipeline Petitorio
- modelos PostgreSQL actuales
- migraciones actuales
- endpoints actuales
- templates actuales
- tests actuales

No asumir nombres de clases, tablas, endpoints, rutas ni migraciones.

Inspeccionar el código real.

Aplicar permanentemente:

> Si hay discrepancia entre diseño, tests y comportamiento real, no asumir. Documentar y resolver antes de cerrar.

---

## 3. Regla permanente de idioma de interfaz

### 3.1. Código interno

Los nombres técnicos internos pueden estar en inglés:

```text
petition
petition_number
petition_date
requesting_unit
prosecutor_name
investigator_name
evidence_items
requested_actions
attachments
review_status
```

También pueden estar en inglés:

- columnas de base de datos;
- modelos SQLAlchemy;
- modelos Pydantic;
- enums;
- servicios;
- repositories;
- rutas internas;
- JSON/API;
- nombres de funciones y clases.

### 3.2. Interfaz visible al operador

**TODA interfaz visible al operador debe estar en español.**

Incluye obligatoriamente:

- títulos;
- subtítulos;
- labels;
- botones;
- ayudas;
- estados;
- mensajes;
- advertencias;
- errores;
- confirmaciones;
- validaciones;
- formularios;
- tablas;
- grillas.

Ejemplos:

```text
petition_number
→ Número de oficio

petition_date
→ Fecha del oficio

requesting_unit
→ Unidad solicitante

prosecutor_name
→ Fiscal

investigator_name
→ Encargado de la investigación

requested_actions
→ Diligencias solicitadas

attachments
→ Actas y anexos

HUMAN_CORRECTED
→ Corregido por el operador

NOT_FOUND
→ No encontrado

APPROVED
→ Aprobado
```

No mostrar identificadores técnicos ingleses al operador salvo vista diagnóstica explícita.

Esta regla debe considerarse transversal para todo el sistema futuro:

```text
Petitorio
Identificación
Adquisición
Análisis
Resultados
Reporte
```

---

## 4. Baseline

Ejecutar suite completa **ANTES de cualquier modificación**.

Baseline conocido:

```text
243 passed
```

Si la suite real contiene más pruebas legítimas:

- registrar el valor real;
- no reducir pruebas;
- no aceptar regresiones.

Confirmar además:

```text
DB operacional = agente_forense_db
DB tests       = agente_forense_test
```

Verificar:

- pytest NO puede escribir en la DB operacional;
- guard de aislamiento sigue activo;
- PostgreSQL operativo está ONLINE;
- localhost sigue disponible;
- no existen casos de prueba contaminando la DB operacional.

---

## 5. Inspeccionar implementación actual del Petitorio

Identificar exactamente la implementación real.

### 5.1. Backend

Inspeccionar:

- modelos Pydantic;
- modelos SQLAlchemy;
- repositories;
- services;
- OCR providers;
- PDF renderer;
- extractores;
- revisión humana;
- `CaseStructureDraft`;
- auditoría;
- staging;
- manejo de hashes;
- persistencia temporal.

### 5.2. Web

Inspeccionar rutas y templates reales.

Como mínimo revisar si existen o cómo están implementados:

```text
POST /api/petitions/stage
POST /api/petitions/{document_id}/review
POST /api/petitions/{document_id}/build-draft
```

Inspeccionar también:

- página de Nueva Adquisición;
- templates involucrados;
- JavaScript involucrado;
- `csrfFetch`;
- flujo multipart;
- manejo de estados;
- mensajes de error;
- traducciones visibles.

### 5.3. Filesystem

Documentar:

- ruta real de staging;
- cómo se calcula SHA-256;
- cómo se guardan PDFs e imágenes;
- cómo se guardan OCR y derivados;
- temporales;
- política de limpieza;
- política ante error;
- artefactos parciales.

No borrar artefactos parciales silenciosamente.

---

## 6. Inspeccionar PostgreSQL actual

Listar todas las tablas dentro del schema:

```text
forensic
```

Para cada tabla relacionada con Petitorio registrar:

- nombre;
- PK;
- FK;
- columnas;
- tipos;
- constraints;
- índices;
- relaciones;
- `ON DELETE`;
- estados;
- timestamps;
- auditoría.

Determinar si actualmente existe persistencia real del Oficio Petitorio o solamente:

```text
staging
memoria
archivos temporales
propuestas no persistidas
```

**NO crear todavía una migración nueva en P00.**

---

## 7. Principio arquitectónico obligatorio

Mantener permanentemente:

```text
OFICIO PETITORIO != CASO
```

El Oficio Petitorio contiene:

```text
LO QUE EL DOCUMENTO DECLARA
```

El caso contiene:

```text
LO QUE EL OPERADOR Y LA INSPECCIÓN FÍSICA CONFIRMAN
```

El OCR es un mecanismo de extracción.

El OCR **NO es la fuente de verdad final**.

El flujo correcto debe ser:

```text
OFICIO PETITORIO
↓
STAGING + SHA-256
↓
OCR / TEXT EXTRACTION
↓
EXTRACCIÓN DE CAMPOS
↓
REVISIÓN HUMANA
↓
OFICIO PETITORIO APROBADO
↓
PERSISTENCIA POSTGRESQL
↓
CaseStructureDraft
↓
CREACIÓN DEL CASO
```

Nunca crear automáticamente el caso definitivo directamente desde OCR.

---

## 8. Modelo documental base

Usar como muestra principal el Oficio Petitorio real ya procesado por el sistema.

Ese documento es suficiente como molde inicial porque corresponde al formato predominante observado por el operador.

El modelo debe poder representar, como mínimo, las siguientes categorías.

### 8.1. Datos del documento

Investigar y proponer representación para:

```text
Tipo de documento
Número de oficio
Fecha del oficio
Ciudad / lugar
Número de bitácora u otra referencia
Cantidad de páginas
Nombre original del archivo
MIME
Tamaño
SHA-256
```

### 8.2. Datos de la causa

Investigar:

```text
RUC
Delito / contexto de causa
Otras referencias
```

No inventar campos jurídicos adicionales sin evidencia documental.

### 8.3. Solicitante

Investigar:

```text
Unidad solicitante
Fiscalía
Nombre del fiscal
Encargado de la investigación
Cargo / grado
Datos de contacto
Destinatario
Copias informadas
```

Si un dato no existe:

```text
NOT_FOUND
```

o equivalente.

No inventarlo.

---

## 9. Evidencias y NUE

El sistema debe soportar:

```text
1 RUC
→ 1..N NUE
```

Cada NUE puede contener:

```text
1..N especies declaradas
```

El Petitorio puede describir uno o varios elementos de evidencia.

Para cada elemento investigar representación de:

```text
NUE
Cantidad
Descripción original
Tipo de especie si el documento lo indica
Marca
Modelo
Número de serie
Capacidad
Otros identificadores
Página fuente
Texto fuente
```

Estos datos deben conservar semántica explícita:

```text
SOURCE = PETITORIO
```

No equivalen todavía a identificación física confirmada.

Ejemplo conceptual:

```json
{
  "nue_number": "7746537",
  "quantity": 1,
  "description_original": "01 Computador portátil, marca Lenovo...",
  "evidence_type": "Computador portátil",
  "brand": "Lenovo",
  "model": "E-41-55",
  "serial_number": "MPIZGTX4",
  "source": "PETITORIO"
}
```

No convertir automáticamente esto en DSM.

---

## 10. Diligencias solicitadas

El Oficio puede contener una o varias diligencias.

No modelar únicamente como un string único si el comportamiento real requiere múltiples items.

Debe preservarse siempre:

```text
source_text
```

Puede existir adicionalmente:

```text
normalized_description
```

pero la normalización:

- no reemplaza el texto original;
- no puede agregar acciones inexistentes;
- debe quedar sujeta a revisión humana.

Ejemplo conceptual:

```text
Texto fuente:
"Se solicita expresamente..."

Items normalizados:
- extraer imágenes;
- extraer conversaciones;
- buscar archivos específicos.
```

Solo si el documento realmente lo sustenta.

---

## 11. Actas, anexos y documentos relacionados

El modelo debe soportar:

```text
0..N actas
0..N anexos
0..N documentos referenciados
```

Investigar estructura apropiada.

No asumir todavía un catálogo cerrado.

Campos candidatos a evaluar:

```text
type
description
reference_number
source_page
physically_received
review_status
```

Tipos candidatos, solo si corresponden al documento real:

```text
ACTA
ANEXO
CADENA_CUSTODIA
OTRO_DOCUMENTO
REFERENCIA_DOCUMENTAL
```

No fijarlos definitivamente sin revisar compatibilidad con el código actual.

---

## 12. Modelo de revisión humana

Cada campo extraído debe conservar trazabilidad completa.

Investigar y proponer un modelo que pueda representar:

```text
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
```

Estados candidatos:

```text
EXTRACTED
UNCERTAIN
CONFLICT
NOT_FOUND
NOT_APPLICABLE
HUMAN_CONFIRMED
HUMAN_CORRECTED
```

Validar primero compatibilidad con enums y estados actuales.

Ejemplo real ya observado:

```text
field_name:
requesting_unit

observed_value:
<texto OCR extenso>

confirmed_value:
BRIGADA INVESTIGADORA DE DELITOS SEXUALES METROPOLITANA

status:
HUMAN_CORRECTED
```

Debe quedar explícito que el valor final fue corregido por el operador.

---

## 13. Grilla dinámica de revisión

Diseñar, pero **NO implementar todavía en P00**, una interfaz basada en grilla/formulario estructurado.

Debe mostrar los campos comunes del Oficio Petitorio y permitir filas repetibles.

### 13.1. Campos comunes

Ejemplo:

```text
Número de oficio
Fecha del oficio
Ciudad
RUC
Delito / contexto
Unidad solicitante
Fiscalía
Fiscal
Encargado de la investigación
Cargo / grado
Bitácora
Destinatario
```

### 13.2. Secciones repetibles

Debe permitir agregar dinámicamente:

```text
NUE
Evidencia
Diligencia
Acta
Anexo
Documento relacionado
Campo adicional
```

### 13.3. Acciones por campo

Cada campo debe permitir:

```text
Confirmar
Corregir
Marcar no encontrado
Marcar no aplicable
```

### 13.4. Datos visibles por campo

La UI debe mostrar:

```text
Nombre del campo
Valor detectado
Página
Fragmento fuente
Método de extracción
Estado
Acción del operador
```

No presentar JSON como interfaz principal al operador.

---

## 14. Regla de aprobación del Oficio

El Oficio no puede pasar a estado aprobado mientras existan campos que requieren decisión humana.

Un campo queda resuelto cuando está en uno de estos estados conceptuales:

```text
CONFIRMADO
CORREGIDO
NO ENCONTRADO
NO APLICA
```

No exigir valores ficticios para campos ausentes.

La acción final debe ser explícita:

```text
CONFIRMAR OFICIO PETITORIO
```

Después de confirmación:

```text
PETITION_STATUS = APPROVED
```

o equivalente real según convención del proyecto.

Solo entonces se permite persistencia definitiva y transición hacia creación de caso.

---

## 15. Persistencia PostgreSQL — diseño a proponer

P00 debe entregar diseño, **NO crear todavía las tablas**.

Como mínimo evaluar necesidad de entidades equivalentes a:

```text
forensic.petitions
forensic.petition_evidence_items
forensic.petition_requested_actions
forensic.petition_attachments
forensic.petition_field_reviews
```

Estos nombres son candidatos.

No asumirlos como definitivos hasta inspeccionar convenciones reales del repositorio.

Para el diseño final indicar:

- campos de tabla principal;
- relaciones 1:N;
- PK;
- FK;
- índices;
- constraints;
- estados;
- auditoría;
- timestamps;
- relación futura con `cases`;
- relación futura con `nues`;
- política de borrado;
- política de actualización;
- aislamiento entre casos;
- preservación de staging y hashes.

---

## 16. Derivación futura a CaseStructureDraft

Después de:

```text
OFICIO APROBADO
```

se generará:

```text
CaseStructureDraft
```

El draft debe heredar solamente información confirmada.

Ejemplo:

```text
RUC
NUE
descripción declarada
metadata del Petitorio
```

Pero debe dejar pendiente:

```text
ESPECIE física confirmada
DSM
StorageRelation
```

hasta inspección física.

Nunca deducir automáticamente DSM desde OCR.

---

## 17. Relación futura con estructura del caso

Después de aprobar el Petitorio:

```text
RUC
→ NUE
```

Luego el operador completa:

```text
NUE
→ ESPECIE
→ SELF_STORAGE / CONTAINED_STORAGE
→ DSM
```

Debe permitir:

```text
1 RUC
→ varias NUE

1 NUE
→ varias ESPECIES

1 ESPECIE
→ uno o varios DSM
```

No asumir un DSM por NUE.

Para `SELF_STORAGE`:

```text
ESPECIE = DSM físico
```

Para `CONTAINED_STORAGE`:

```text
ESPECIE
→ 1..N DSM
```

La estructura definitiva requiere confirmación humana antes de persistirla como caso operacional.

---

## 18. Relación posterior con adquisición

**NO implementar adquisición en P00.**

Solo documentar que, una vez confirmada la estructura:

```text
RUC
→ NUE
→ ESPECIE
→ DSM
```

cada DSM podrá generar un `Acquisition Job` independiente.

La futura concurrencia de dos write blockers pertenece al módulo de Adquisición, no al módulo Petitorio.

No ejecutar:

```text
ewfacquire
ewfverify
PhysicalDrive
E01
```

durante P00.

---

## 19. Seguridad

Durante P00 está prohibido:

- ejecutar `ewfacquire`;
- ejecutar `ewfverify`;
- abrir `PhysicalDrive`;
- crear E01;
- modificar evidencia;
- cambiar atributos de discos;
- ejecutar `Set-Disk`;
- ejecutar CHKDSK;
- ejecutar DiskPart;
- integrar AXIOM;
- generar Word;
- crear casos operacionales reales;
- aplicar nuevas migraciones productivas;
- desactivar CSRF;
- debilitar aislamiento de DB de tests.

---

## 20. Tests

No modificar tests salvo que sea estrictamente necesario para investigación.

Ejecutar:

```text
pytest
```

antes y después.

Esperado:

```text
>= baseline
0 failed
0 errors
```

Confirmar además:

```text
pytest → agente_forense_test
```

Nunca:

```text
pytest → agente_forense_db
```

---

## 21. Resultado obligatorio de P00

P00 debe terminar con un diseño técnico verificable, no con implementación productiva.

Debe entregar:

1. mapa real del pipeline Petitorio actual;
2. modelos reales actuales;
3. endpoints reales actuales;
4. staging real;
5. OCR real;
6. mecanismo actual de revisión;
7. `CaseStructureDraft` real;
8. inventario de campos actuales;
9. inventario de campos faltantes;
10. diseño de tablas;
11. relaciones 1:N;
12. diseño de estados;
13. diseño de auditoría;
14. diseño de grilla;
15. regla de aprobación;
16. plan de migración para P01;
17. riesgos y dependencias.

---

## 22. Criterios de aceptación

P00 queda completo solo si:

- `PROMPT_MAESTRO.md` fue leído;
- `REGLA_PERMANENTE_PRE_SPRINT.md` fue leída;
- baseline fue ejecutado;
- DB operacional y test están aisladas;
- pipeline actual fue inspeccionado;
- endpoints reales fueron inspeccionados;
- modelos reales fueron inspeccionados;
- staging real fue documentado;
- OCR real fue documentado;
- revisión humana real fue documentada;
- `CaseStructureDraft` real fue documentado;
- campos faltantes fueron identificados;
- relaciones 1:N fueron modeladas;
- diseño de tablas fue propuesto;
- grilla dinámica fue diseñada;
- aprobación fue diseñada;
- UI en español quedó como regla obligatoria;
- no se ejecutaron operaciones forenses reales;
- toda la suite sigue en verde;
- no se inició P01.

---

## 23. Reporte final obligatorio

TRAE debe entregar exactamente:

```text
PETITORIO P00:
COMPLETED / BLOCKED

PROMPT MAESTRO:
READ / NOT READ

REGLA PERMANENTE:
READ / NOT READ

BASELINE:
...

DB OPERACIONAL:
...

DB TEST:
...

TEST ISOLATION:
PASS / FAIL

POSTGRESQL:
ONLINE / ERROR

PETITION BACKEND ACTUAL:
...

PETITION WEB ACTUAL:
...

ENDPOINTS REALES:
...

MODELOS REALES:
...

TABLAS ACTUALES:
...

STAGING ACTUAL:
...

OCR ACTUAL:
...

REVIEW ACTUAL:
...

CASESTRUCTUREDRAFT ACTUAL:
...

CAMPOS ACTUALES:
...

CAMPOS FALTANTES CONFIRMADOS:
...

RELACIONES 1:N:
...

MODELO DB PROPUESTO:
...

MODELO REVIEW PROPUESTO:
...

MODELO UI PROPUESTO:
...

REGLA UI ESPAÑOL:
PASS / FAIL

RIESGOS:
...

TESTS FINAL:
...

OPERACIONES FORENSES:
NINGUNA

STATUS:
PETITION_MODEL_READY_FOR_P01 /
PETITION_MODEL_BLOCKED
```

---

## 24. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Ejecutar baseline completo.
4. Confirmar aislamiento de DB de tests.
5. Inspeccionar implementación real del Petitorio.
6. Inspeccionar modelos, servicios, endpoints y templates.
7. Inspeccionar staging y OCR real.
8. Inspeccionar revisión humana actual.
9. Inspeccionar `CaseStructureDraft` real.
10. Inspeccionar schema PostgreSQL.
11. Levantar inventario real de campos.
12. Diseñar modelo documental completo.
13. Diseñar relaciones 1:N.
14. Diseñar grilla dinámica.
15. Diseñar aprobación.
16. Diseñar tablas PostgreSQL.
17. Diseñar relación futura con `cases` y `nues`.
18. Mantener toda la UI visible en español.
19. No ejecutar adquisición.
20. No aplicar migración productiva.
21. Ejecutar suite final.
22. Entregar reporte.
23. **NO iniciar PETITORIO P01.**

Comienza ahora.
