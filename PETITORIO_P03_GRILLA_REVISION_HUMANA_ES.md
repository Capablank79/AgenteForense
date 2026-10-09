# PETITORIO P03 — Grilla de Revisión Humana y Aprobación del Oficio Petitorio

## 1. Objetivo

Implementar la interfaz web operativa para que el perito revise, confirme, corrija o marque como no encontrado/no aplicable cada dato extraído del Oficio Petitorio.

El sprint debe convertir el pipeline actual en un flujo completo y controlado:

```text
OFICIO PETITORIO
→ OCR / extracción estructurada
→ grilla de revisión humana
→ resolución de conflictos
→ aprobación del Oficio Petitorio
```

**NO crear todavía el caso definitivo.**
**NO crear todavía ESPECIE ni DSM.**
**NO iniciar adquisición.**

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

PETITORIO P02:
```text
ACCEPTED
```

Baseline validado al cierre de P02:

```text
249 passed
```

Estados reales vigentes para campos revisados:

```text
FieldStatus.CONFIRMED
FieldStatus.CORRECTED_BY_HUMAN
```

Persistencia PostgreSQL existente:

```text
forensic.petitions
forensic.petition_evidence_items
forensic.petition_requested_actions
forensic.petition_attachments
forensic.petition_field_reviews
```

OCR estructurado actual capaz de producir:

```text
ruc
nue
oficio_number
petition_date
city
prosecutor_office
prosecutor_name
investigator_name
crime_context
log_reference
evidence_items
requested_actions
attachments
```

---

## 3. Reglas obligatorias antes de implementar

TRAE debe leer:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
PETITORIO_P00_INVESTIGACION_MODELO_OFICIO_PETITORIO.md
PETITORIO_P01_PERSISTENCIA_POSTGRESQL_OFICIO_PETITORIO.md
PETITORIO_P02_EXTRACCION_OCR_ESTRUCTURADA.md
```

Luego debe:

1. ejecutar baseline completo;
2. inspeccionar estado real de `case_new.html`;
3. inspeccionar endpoints reales de Petitorio;
4. inspeccionar modelos reales de revisión;
5. inspeccionar enums reales;
6. inspeccionar persistencia de `petition_field_reviews`;
7. inspeccionar manejo CSRF actual;
8. inspeccionar JavaScript actual;
9. inspeccionar respuesta JSON actual de extracción/revisión;
10. no asumir nombres o contratos no presentes en el código.

Si hay discrepancia material:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de cerrar el sprint.

---

## 4. Regla permanente de idioma

Toda la interfaz visible al operador debe estar en español.

Los identificadores internos pueden estar en inglés.

Ejemplos internos:

```text
petition_number
requesting_unit
prosecutor_name
requested_actions
attachments
CONFIRMED
CORRECTED_BY_HUMAN
```

Ejemplos visibles:

```text
Número de oficio
Unidad solicitante
Fiscal
Diligencias solicitadas
Actas y anexos
Confirmado
Corregido por el operador
```

No mostrar nombres técnicos internos como texto principal de UI.

---

## 5. Principio de revisión humana

Cada campo extraído debe distinguir claramente:

```text
VALOR OBSERVADO
VALOR PROPUESTO
VALOR CONFIRMADO
FUENTE
PÁGINA
ESTADO
ACCIÓN HUMANA
```

Nunca reemplazar silenciosamente el valor OCR original.

Debe conservarse trazabilidad de:

```text
observed_value
proposed_value
confirmed_value
source_page
source_excerpt
extraction_method
review_action
reviewed_by
reviewed_at
```

---

## 6. Pantalla principal de revisión

La interfaz debe mostrar una sección titulada:

```text
Revisión del Oficio Petitorio
```

Debe estar organizada por bloques comprensibles para el operador.

### 6.1. Datos del documento

Mostrar:

```text
Tipo de documento
Número de oficio
Fecha del oficio
Ciudad
Número de bitácora
Nombre del archivo
Cantidad de páginas
SHA-256
```

### 6.2. Datos de la causa

Mostrar:

```text
RUC
Delito / contexto
Otras referencias
```

### 6.3. Solicitante

Mostrar:

```text
Unidad solicitante
Fiscalía
Fiscal
Encargado de la investigación
Cargo / grado
Datos de contacto
Destinatario
Copias informadas
```

### 6.4. Evidencias declaradas

Grilla repetible.

Columnas visibles sugeridas:

```text
NUE
Cantidad
Descripción
Tipo
Marca
Modelo
Número de serie
Capacidad
Página
Estado
Acciones
```

### 6.5. Diligencias solicitadas

Grilla repetible.

Mostrar:

```text
Orden
Texto fuente
Descripción normalizada
Página
Estado
Acciones
```

### 6.6. Actas y anexos

Grilla repetible.

Mostrar:

```text
Tipo
Descripción
Número de referencia
Página
Recibido físicamente
Estado
Acciones
```

---

## 7. Acciones de revisión por campo

Cada campo o fila revisable debe permitir:

```text
Confirmar
Corregir
Marcar no encontrado
Marcar no aplica
```

### 7.1. Confirmar

Debe producir:

```text
FieldStatus.CONFIRMED
```

Conservar:

```text
observed_value
confirmed_value
source_page
source_excerpt
reviewed_by
reviewed_at
```

### 7.2. Corregir

Debe permitir ingresar un valor manual.

Resultado:

```text
FieldStatus.CORRECTED_BY_HUMAN
```

Debe conservar:

```text
observed_value original
human corrected value
review action
timestamp
operator
```

Nunca borrar la observación original.

### 7.3. Marcar no encontrado

Usar el enum real existente si ya está implementado.

Si no existe, investigar antes de agregar uno.

La UI debe mostrar:

```text
No encontrado
```

### 7.4. Marcar no aplica

Usar enum real existente si está disponible.

No inventar un estado nuevo sin revisar los modelos actuales.

La UI debe mostrar:

```text
No aplica
```

---

## 8. Edición de listas repetibles

El operador debe poder agregar manualmente elementos que el OCR no detectó.

Como mínimo:

```text
Agregar NUE / evidencia
Agregar diligencia
Agregar acta o anexo
```

La incorporación manual debe registrarse como proveniencia humana.

No simular que fue OCR.

Persistir:

```text
source = HUMAN_INPUT
```

o equivalente real según modelo.

---

## 9. Eliminación y corrección de filas

No borrar silenciosamente elementos extraídos.

Si una fila OCR fue incorrecta:

preferir:

```text
marcar como descartada / no corresponde
```

o mecanismo equivalente auditable.

Si el modelo actual no contempla descarte:

investigar e implementar la mínima extensión necesaria.

Debe quedar rastro de:

```text
valor original
acción humana
motivo opcional
timestamp
operador
```

---

## 10. Conflictos

La UI debe mostrar claramente los conflictos detectados.

Como mínimo:

```text
MULTIPLE_OFICIO
AMBIGUOUS_DATE
INCOMPLETE_SERIAL
DUPLICATE_NUE_CONFLICT
```

No resolver conflictos automáticamente.

Cada conflicto debe:

- indicar qué campos afecta;
- mostrar valores candidatos;
- mostrar provenance;
- requerir decisión humana;
- quedar resuelto antes de aprobar el Petitorio.

---

## 11. Estados visuales en español

Mapear estados internos a etiquetas españolas.

Ejemplo:

```text
EXTRACTED
→ Extraído

UNCERTAIN
→ Dudoso

CONFLICT
→ Conflicto

CONFIRMED
→ Confirmado

CORRECTED_BY_HUMAN
→ Corregido por el operador

NOT_FOUND
→ No encontrado

NOT_APPLICABLE
→ No aplica
```

Usar solo estados reales vigentes.

No crear duplicados semánticos.

---

## 12. Regla de completitud

Un Oficio Petitorio puede aprobarse únicamente si:

1. no quedan campos obligatorios en estado sin revisar;
2. no quedan conflictos abiertos;
3. RUC está confirmado;
4. al menos una NUE válida está confirmada;
5. todos los campos detectados que requieren revisión tienen una acción humana explícita;
6. las listas repetibles están revisadas;
7. ningún valor corregido perdió su provenance;
8. persistencia PostgreSQL es coherente.

No exigir valores inventados para campos ausentes.

Un campo ausente debe resolverse mediante:

```text
No encontrado
```

o:

```text
No aplica
```

cuando corresponda.

---

## 13. Botón final de aprobación

Agregar una acción explícita:

```text
Aprobar Oficio Petitorio
```

La aprobación debe requerir confirmación humana explícita.

No usar aprobación implícita por completar campos.

La acción debe:

1. validar completitud;
2. validar conflictos;
3. persistir revisiones pendientes;
4. establecer estado aprobado;
5. registrar auditoría;
6. mostrar resultado al operador en español.

---

## 14. Estado aprobado

Usar el estado real existente si ya existe.

Conceptualmente:

```text
APPROVED
```

La UI debe mostrar:

```text
Oficio Petitorio aprobado
```

La aprobación NO debe:

```text
crear case
crear NUE definitiva
crear species
crear DSM
crear carpetas del caso
crear case.json definitivo
crear acquisition jobs
```

Eso corresponde a sprints posteriores.

---

## 15. Persistencia

Toda acción humana debe quedar en PostgreSQL.

Como mínimo:

```text
petition_field_reviews
petition_evidence_items
petition_requested_actions
petition_attachments
petitions.review_status
```

No depender únicamente del DOM o memoria de proceso.

Si el navegador se recarga:

```text
la revisión debe recuperarse desde PostgreSQL
```

No perder correcciones humanas.

---

## 16. Recuperación de sesión / recarga

Probar:

```text
1. cargar Petitorio
2. corregir varios campos
3. guardar
4. recargar navegador
5. verificar que todos los cambios permanecen
```

No depender exclusivamente de:

```text
_STAGED_DOCUMENTS
_STAGED_EXTRACTIONS
```

para reconstruir la revisión ya persistida.

---

## 17. CSRF

Toda mutación debe mantener protección CSRF.

Incluye:

```text
confirmar campo
corregir campo
marcar no encontrado
marcar no aplica
agregar evidencia
agregar diligencia
agregar anexo
resolver conflicto
aprobar Petitorio
```

No desactivar CSRF.

No crear excepciones globales.

No aceptar token faltante.

---

## 18. API

Reutilizar endpoints existentes cuando sea razonable.

Puede ampliarse:

```text
POST /api/petitions/{doc_id}/review
```

para soportar todas las acciones.

Si se crean nuevos endpoints:

- documentarlos;
- validar CSRF;
- usar respuestas controladas;
- mantener compatibilidad con los endpoints actuales;
- no exponer traceback al operador.

---

## 19. JavaScript / HTMX

Preferir el patrón existente del proyecto.

No introducir framework frontend nuevo.

Mantener:

```text
Jinja2
HTMX / JavaScript existente
```

si corresponde al estado real.

La UI debe ser utilizable desde:

```text
http://127.0.0.1:8085
```

No requerir consola para operar el Petitorio.

---

## 20. Auditoría

Registrar como mínimo:

```text
petition_field_confirmed
petition_field_corrected
petition_field_marked_not_found
petition_field_marked_not_applicable
petition_evidence_added_by_human
petition_action_added_by_human
petition_attachment_added_by_human
petition_conflict_resolved
petition_review_completed
petition_approved
petition_approval_rejected
```

Cada evento debe registrar cuando corresponda:

```text
petition_id
field
operator
timestamp
result
```

No registrar secretos.

---

## 21. No invención

La UI nunca debe prellenar información no sustentada como si fuera observada.

Distinguir:

```text
OCR
HUMAN_INPUT
HUMAN_CORRECTION
```

Si un valor no existe:

```text
No encontrado
```

No completar por plausibilidad.

---

## 22. Caso especial: requesting_unit

Agregar test de regresión basado en el defecto ya observado.

Escenario:

OCR produce un bloque extenso incorrecto.

El operador corrige a:

```text
BRIGADA INVESTIGADORA DE DELITOS SEXUALES METROPOLITANA
```

Debe persistirse:

```text
observed_value = <bloque OCR original>
confirmed_value = BRIGADA INVESTIGADORA DE DELITOS SEXUALES METROPOLITANA
status = CORRECTED_BY_HUMAN
```

Nunca debe parecer que el valor limpio fue extraído automáticamente.

---

## 23. Prueba funcional real con el Petitorio existente

Usar el mismo Oficio Petitorio de laboratorio ya validado.

Flujo:

```text
1. subir / recuperar documento
2. ejecutar extracción
3. abrir grilla
4. revisar campos
5. confirmar campos correctos
6. corregir campos incorrectos
7. revisar evidencias
8. revisar diligencias
9. revisar actas/anexos
10. resolver conflictos
11. aprobar Petitorio
12. recargar navegador
13. comprobar persistencia
```

Registrar:

```text
RUC
NUE
Número de oficio
Fecha
Ciudad
Fiscalía
Fiscal
Investigador
Delito/contexto
Bitácora
Evidencias
Diligencias
Actas/anexos
```

sin inventar los ausentes.

---

## 24. Interfaz obligatoria en español

Verificar visualmente que el operador no vea labels ingleses.

Debe pasar al menos:

```text
Título de página
Secciones
Columnas de tabla
Botones
Estados
Errores
Confirmaciones
Mensajes de éxito
```

Ejemplos válidos:

```text
Confirmar
Corregir
No encontrado
No aplica
Agregar evidencia
Agregar diligencia
Agregar acta o anexo
Aprobar Oficio Petitorio
```

---

## 25. Tests obligatorios

Baseline inicial esperado:

```text
249 passed
```

Agregar tests como mínimo para:

1. render de grilla;
2. UI en español;
3. confirmar campo;
4. corregir campo;
5. preservar observed_value;
6. `CONFIRMED`;
7. `CORRECTED_BY_HUMAN`;
8. no encontrado;
9. no aplica si existe enum;
10. agregar evidencia manual;
11. agregar diligencia manual;
12. agregar anexo manual;
13. provenance humana;
14. múltiples NUE;
15. múltiples evidencias;
16. persistencia al recargar;
17. conflicto visible;
18. conflicto bloquea aprobación;
19. conflicto resuelto permite continuar;
20. RUC sin confirmar bloquea aprobación;
21. NUE sin confirmar bloquea aprobación;
22. campos pendientes bloquean aprobación;
23. aprobación válida;
24. aprobación auditada;
25. aprobación no crea case;
26. aprobación no crea NUE definitiva;
27. aprobación no crea species;
28. aprobación no crea DSM;
29. CSRF requerido;
30. error controlado en español;
31. regression requesting_unit;
32. suite completa sin regresión.

---

## 26. Operaciones prohibidas

Durante P03:

```text
NO PhysicalDrive
NO ewfacquire
NO ewfverify
NO E01
NO AXIOM
NO Portable Case
NO Word
NO creación definitiva del caso
NO species
NO DSM
NO acquisition jobs
```

---

## 27. Criterios de aceptación

P03 queda COMPLETO únicamente si:

- Prompt Maestro leído;
- Regla Permanente leída;
- P00/P01/P02 leídos;
- baseline inicial registrado;
- grilla completa implementada;
- UI visible 100% en español;
- provenance visible;
- corrección humana conserva OCR original;
- listas repetibles editables;
- conflictos visibles y resolubles;
- conflictos abiertos bloquean aprobación;
- aprobación exige revisión completa;
- aprobación explícita funciona;
- PostgreSQL conserva toda la revisión;
- recarga del navegador no pierde datos;
- CSRF permanece activo;
- auditoría registra revisión/aprobación;
- Petitorio aprobado NO crea caso;
- toda la suite pasa;
- prueba funcional real pasa;
- ninguna operación forense real fue ejecutada.

---

## 28. Reporte final obligatorio

TRAE debe entregar:

```text
PETITORIO P03:
COMPLETED / BLOCKED

PROMPT MAESTRO:
READ / NOT READ

REGLA PERMANENTE:
READ / NOT READ

P00:
READ / NOT READ

P01:
READ / NOT READ

P02:
READ / NOT READ

BASELINE BEFORE:
...

TESTS FINAL:
...

UI ESPAÑOL:
PASS / FAIL

GRID RENDER:
PASS / FAIL

COMMON FIELDS:
PASS / FAIL

EVIDENCE GRID:
PASS / FAIL

REQUESTED ACTIONS GRID:
PASS / FAIL

ATTACHMENTS GRID:
PASS / FAIL

FIELD CONFIRM:
PASS / FAIL

FIELD CORRECTION:
PASS / FAIL

OBSERVED VALUE PRESERVED:
PASS / FAIL

HUMAN PROVENANCE:
PASS / FAIL

CONFLICT DISPLAY:
PASS / FAIL

CONFLICT RESOLUTION:
PASS / FAIL

APPROVAL GATING:
PASS / FAIL

PETITION APPROVAL:
PASS / FAIL

POSTGRESQL PERSISTENCE:
PASS / FAIL

RELOAD PERSISTENCE:
PASS / FAIL

CSRF:
PASS / FAIL

AUDIT:
PASS / FAIL

REAL PETITION TEST:
PASS / FAIL

REQUESTING_UNIT REGRESSION:
PASS / FAIL

CASE CREATED:
NO

NUE DEFINITIVE CREATED:
NO

SPECIES CREATED:
NO

DSM CREATED:
NO

ACQUISITION JOBS CREATED:
NO

PHYSICALDRIVE:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

RISKS / LIMITATIONS:
...

STATUS:
PETITION_REVIEW_READY_FOR_P04 /
PETITION_REVIEW_BLOCKED
```

---

## 29. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Leer P00, P01 y P02.
4. Ejecutar baseline.
5. Inspeccionar UI, endpoints, enums y persistencia reales.
6. Implementar la grilla de revisión humana.
7. Mantener toda la interfaz en español.
8. Mostrar provenance por campo.
9. Implementar confirmar/corregir/no encontrado/no aplica.
10. Implementar listas repetibles.
11. Implementar resolución de conflictos.
12. Implementar gating de aprobación.
13. Implementar botón `Aprobar Oficio Petitorio`.
14. Persistir todas las acciones humanas.
15. Mantener CSRF estricto.
16. Integrar auditoría.
17. Agregar tests.
18. Ejecutar prueba real con el Petitorio de laboratorio.
19. Confirmar persistencia tras recarga.
20. No crear caso.
21. No crear NUE definitiva.
22. No crear especies.
23. No crear DSM.
24. No ejecutar adquisición.
25. Ejecutar suite completa.
26. Entregar reporte final.
27. **NO iniciar PETITORIO P04.**

Comienza ahora.
