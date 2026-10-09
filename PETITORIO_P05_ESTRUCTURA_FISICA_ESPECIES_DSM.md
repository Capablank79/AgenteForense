# PETITORIO P05 — Estructura Física Confirmada: RUC → NUE → ESPECIE → DSM

## 1. Objetivo

Implementar el flujo web controlado que toma un `CaseStructureDraft` generado desde un Oficio Petitorio aprobado y permite al operador completar y confirmar la **estructura física real** del caso:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

El objetivo de P05 es completar la topología física que el Petitorio, por sí solo, no puede establecer.

Este sprint debe permitir:

```text
CaseStructureDraft
→ revisar NUE
→ agregar / confirmar ESPECIES
→ definir SELF_STORAGE o CONTAINED_STORAGE
→ crear DSM lógicos correspondientes
→ mostrar resumen completo
→ confirmación humana explícita
→ persistir estructura jerárquica
```

P05 NO debe ejecutar adquisición real.

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

PETITORIO P03:
```text
ACCEPTED
```

PETITORIO P04:
```text
ACCEPTED
```

Baseline validado al cierre de P04:

```text
268 passed
```

Estado funcional disponible:

```text
Petitorio persistido
OCR estructurado
revisión humana
Petitorio aprobado
CaseStructureDraft persistente
RUC confirmado
1..N NUE confirmadas
metadata documental preservada
```

Todavía NO existe estructura física definitiva:

```text
SPECIES = NO
DSM = NO
STORAGE RELATION = NO
ACQUISITION JOBS = NO
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
PETITORIO_P03_GRILLA_REVISION_HUMANA_ES.md
PETITORIO_P04_PETITORIO_APROBADO_A_CASESTRUCTUREDRAFT.md
```

Además debe inspeccionar el código real vigente de:

```text
CaseStructureDraft
DraftNue
CaseService
Case creator
hierarchy/domain models
Species models
DSM models
StorageRelation
repositories
case.json persistence
case_new.html
routes de creación de caso
orchestrator / state machine
```

Antes de cualquier cambio:

1. ejecutar la suite completa;
2. registrar baseline real;
3. inspeccionar cómo se crean hoy `species`;
4. inspeccionar cómo se crean hoy `dsms`;
5. inspeccionar constraints reales;
6. inspeccionar cómo se numera ESPECIE;
7. inspeccionar cómo se numera DSM;
8. inspeccionar cómo se persiste `StorageRelation`;
9. inspeccionar transacciones y auditoría;
10. inspeccionar relación actual con `case.json`;
11. no asumir helpers, endpoints o enums inexistentes.

Si hay discrepancia material:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de continuar.

---

## 4. Jerarquía obligatoria

Mantener sin cambios:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

Definiciones:

```text
RUC     = identificador lógico del caso
NUE     = evidencia / identificador documental de evidencia
ESPECIE = objeto físico recibido
DSM     = dispositivo de almacenamiento digital
```

No colapsar estos niveles.

---

## 5. Principio crítico: Petitorio vs realidad física

El Petitorio puede declarar:

```text
"01 Computador portátil marca Lenovo..."
```

Eso es:

```text
SOURCE = PETITION
```

La estructura física se determina mediante:

```text
INSPECCIÓN / CONFIRMACIÓN HUMANA
```

Por tanto:

```text
PETITION DESCRIPTION
!=
PHYSICAL TOPOLOGY
```

No crear automáticamente ESPECIE o DSM solo por texto OCR.

---

## 6. Punto de entrada

Desde un `CaseStructureDraft` válido y recuperable, mostrar una acción visible en español:

```text
Completar estructura física
```

El operador debe poder entrar al flujo desde localhost:

```text
http://127.0.0.1:8085
```

No requerir consola.

---

## 7. Resumen inicial

Antes de solicitar topología, mostrar:

```text
RUC
NUE(s)
Descripción declarada en el Petitorio
Marca/modelo/serie declarados si existen
Diligencias solicitadas
Estado del draft
```

Debe quedar explícito:

```text
Datos declarados por el Petitorio
```

y separado de:

```text
Datos físicos confirmados por el operador
```

---

## 8. ESPECIES por NUE

Por cada NUE, permitir:

```text
1..N ESPECIES
```

La UI debe permitir:

```text
Agregar especie
Editar especie
Descartar propuesta no confirmada
```

La etiqueta se genera automáticamente según las reglas reales del dominio:

```text
NUE_<NUE>_ESPECIE1
NUE_<NUE>_ESPECIE2
...
```

El operador no debe escribir manualmente la etiqueta técnica completa.

---

## 9. Datos mínimos de ESPECIE

Cada especie debe poder conservar como mínimo:

```text
species_label
nue_id
description_observed
description_from_petition
source
storage_relation
status
created_at
confirmed_at
confirmed_by
```

Los nombres exactos deben adaptarse al modelo real.

No inventar atributos obligatorios que el dominio actual no soporte.

---

## 10. Fuente de la descripción

Distinguir:

```text
description_from_petition
```

de:

```text
description_observed
```

Ejemplo:

```text
Petitorio:
"Computador portátil marca Lenovo"

Inspección:
"Notebook Lenovo color negro, etiqueta de serie visible"
```

No sobrescribir una fuente con la otra.

---

## 11. StorageRelation

Usar el enum real existente.

Debe mantener conceptualmente:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

No crear variantes semánticamente duplicadas.

---

## 12. SELF_STORAGE

Definición:

```text
La ESPECIE física es el mismo objeto físico que el DSM.
```

Ejemplos posibles:

```text
pendrive
HDD externo
SSD externo
tarjeta SD
microSD
```

No clasificar automáticamente por nombre del Petitorio.

El operador debe confirmar la relación.

Una vez confirmada:

```text
storage_relation = SELF_STORAGE
same_physical_object_as_species = true
```

Debe existir:

```text
DSM1
```

asociado a la especie, de acuerdo con el modelo real.

No duplicar el objeto físico.

---

## 13. CONTAINED_STORAGE

Definición:

```text
La ESPECIE contiene uno o más DSM físicamente diferenciables.
```

Ejemplos posibles:

```text
notebook
desktop
servidor
DVR/NVR
AIO
```

No inferir automáticamente esta relación por tipo de equipo.

El operador debe confirmarla.

Luego indicar:

```text
cantidad de DSM
```

o agregarlos uno a uno, según patrón real de UI.

Persistir:

```text
storage_relation = CONTAINED_STORAGE
same_physical_object_as_species = false
```

---

## 14. DSM por especie

Numeración correlativa reiniciada por especie:

```text
NUE_<NUE>_ESPECIE1_DSM1
NUE_<NUE>_ESPECIE1_DSM2

NUE_<NUE>_ESPECIE2_DSM1
```

No permitir duplicados.

No permitir DSM sin especie padre válida.

---

## 15. Datos mínimos de DSM

Cada DSM debe poder conservar como mínimo:

```text
dsm_label
species_id
storage_relation
same_physical_object_as_species
description_observed
status
created_at
confirmed_at
confirmed_by
```

Si el modelo real ya permite:

```text
brand
model
serial
capacity
interface
```

pueden incorporarse como observaciones físicas, pero no deben rellenarse automáticamente desde el Petitorio como si fueran observados.

Si se copian como referencia documental, deben mantener:

```text
source = PETITION
```

---

## 16. Comparación documental vs física

La UI debe poder mostrar lado a lado:

```text
PETITORIO
vs
INSPECCIÓN FÍSICA
```

Estados conceptuales:

```text
MATCH
CONFLICT
NOT_OBSERVABLE
NOT_APPLICABLE
```

No elegir automáticamente un valor si hay discrepancia.

Ejemplo:

```text
Petitorio serial: MPIZGTX4
Físico observado: MPIZGTX9
→ CONFLICT
```

Debe quedar pendiente de revisión humana.

---

## 17. Conflictos estructurales

Detectar y bloquear confirmación final ante:

```text
NUE sin especie
ESPECIE sin StorageRelation
SELF_STORAGE con más de un DSM
CONTAINED_STORAGE sin DSM
DSM duplicado
etiqueta duplicada
parent inconsistente
conflicto de identidad no resuelto
```

No continuar silenciosamente.

---

## 18. Regla sobre fotografías

### Importante

Los documentos históricos del proyecto contienen una regla antigua de:

```text
EXACTAMENTE 3 FOTOGRAFÍAS
```

Esa regla **NO debe reintroducirse como requisito normativo en P05**.

La arquitectura de reconstrucción vigente considera la cantidad de fotografías como una recomendación operativa, no como una condición rígida universal.

Por tanto P05 debe:

- soportar futuras referencias fotográficas;
- no bloquear creación de estructura física por no tener exactamente tres fotos;
- no crear lógica normativa fija basada en cantidad 3;
- no borrar ni duplicar fotos;
- dejar la gestión fotográfica al módulo de identificación vigente.

Si el código actual conserva restricciones históricas incompatibles, documentarlas y reconciliarlas explícitamente antes de cerrar P05.

---

## 19. Confirmación previa

Antes de persistir la estructura física definitiva, mostrar resumen completo.

Ejemplo:

```text
RUC: 2601254545-1

NUE_7746537
  ESPECIE1
    Descripción: Notebook Lenovo
    Relación: CONTAINED_STORAGE

    DSM1
      Descripción: SSD interno

    DSM2
      Descripción: NVMe interno

NUE_8888888
  ESPECIE1
    Descripción: Pendrive Kingston
    Relación: SELF_STORAGE

    DSM1
      mismo objeto físico que ESPECIE1
```

---

## 20. Human Gate estructural

La persistencia definitiva debe requerir una acción humana explícita.

UI visible:

```text
Confirmar estructura física
```

Puede utilizar confirmación textual exacta si el patrón actual del proyecto lo exige.

Conceptualmente:

```text
CONFIRMAR_ESTRUCTURA
```

No persistir estructura parcial antes de la confirmación final si la operación se diseñó como atómica.

---

## 21. Persistencia transaccional

Persistir en una transacción coherente:

```text
RUC / case context
NUE
ESPECIES
DSM
StorageRelation
audit events
```

Ante fallo:

```text
ROLLBACK
```

No dejar:

```text
species sin DSM requerido
DSM huérfano
estructura incompleta marcada como confirmada
```

---

## 22. PostgreSQL

Usar las tablas reales ya existentes:

```text
cases
nues
species
dsms
```

y modelos actuales.

No crear nuevas tablas si las existentes ya representan correctamente la jerarquía.

Crear migración solo si existe una necesidad material demostrada.

Si se requiere migración:

- inspeccionar número real siguiente;
- justificarla;
- mantener `ON DELETE RESTRICT`;
- agregar tests.

---

## 23. Creación del caso

P05 puede crear el **caso estructural definitivo** únicamente después de:

```text
Petitorio aprobado
CaseStructureDraft válido
estructura física completa
confirmación humana explícita
```

La creación debe ser atómica y trazable.

No debe implicar adquisición.

---

## 24. case.json

Después de confirmación estructural:

generar o actualizar el `case.json` portable del caso según contrato vigente.

Debe incluir referencia al Petitorio:

```json
{
  "petition": {
    "petition_id": "...",
    "sha256": "...",
    "status": "APPROVED"
  }
}
```

y jerarquía:

```text
RUC
NUE
ESPECIES
DSM
StorageRelation
```

No duplicar OCR bruto innecesariamente.

---

## 25. Fuente de verdad

Mantener:

```text
PostgreSQL = fuente operacional estructurada
case.json = snapshot / contrato portable
```

No usar `case.json` como reemplazo de PostgreSQL operacional.

Las actualizaciones deben permanecer coherentes.

---

## 26. Idempotencia

Repetir la confirmación o recargar la página no debe duplicar:

```text
case
NUE
species
DSM
```

Debe existir protección contra doble submit.

---

## 27. RUC existente

Si el RUC ya existe:

NO sobrescribir.

Determinar según arquitectura real:

```text
CASE_ALREADY_EXISTS
CASE_STRUCTURE_CONFLICT
RECONCILIATION_REQUIRED
```

No fusionar silenciosamente información.

P05 se enfoca en creación controlada desde un draft aprobado.

---

## 28. UI completamente en español

Toda interfaz visible:

```text
Completar estructura física
Agregar especie
Relación de almacenamiento
La especie es el mismo dispositivo de almacenamiento
La especie contiene dispositivos de almacenamiento
Agregar DSM
Resumen de estructura
Confirmar estructura física
Conflicto
Pendiente de revisión
```

No mostrar enums ingleses como texto principal.

Puede mostrarse internamente:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

pero el operador debe ver etiquetas explicativas en español.

---

## 29. Auditoría

Registrar como mínimo:

```text
physical_structure_started
species_added
species_updated
storage_relation_selected
dsm_added
dsm_updated
structure_conflict_detected
physical_structure_confirmation_requested
physical_structure_confirmed
case_created_from_petition
case_structure_persist_failed
```

Con:

```text
timestamp
operator
petition_id
draft_id
ruc
nue
species
dsm
action
result
```

cuando aplique.

---

## 30. CSRF

Toda mutación web debe mantener CSRF:

```text
Agregar especie
Editar especie
Seleccionar StorageRelation
Agregar DSM
Editar DSM
Confirmar estructura
Crear caso
```

No desactivar ni relajar protección.

---

## 31. Estado final esperado

Una vez creada y confirmada la estructura:

```text
CASE CREATED
RUC → NUE → ESPECIE → DSM
```

pero todavía:

```text
NO PhysicalDrive binding
NO write blocker selection
NO acquisition job execution
NO E01
```

El estado debe indicar que la estructura está lista para la fase de preparación/adquisición, usando únicamente estados reales del proyecto.

No inventar un nuevo estado si ya existe equivalente.

---

## 32. Relación con adquisición futura

P05 debe dejar disponibles los DSM para el siguiente flujo:

```text
DSM
→ selección de write blocker
→ resolución PhysicalDrive
→ safety validation
→ binding
→ Human Gate
→ acquisition
```

No iniciar esas etapas en P05.

---

## 33. Dos write blockers

El sistema ya debe poder convivir con múltiples write blockers.

P05 no debe seleccionar blockers.

Solo asegurar que cada DSM queda como recurso independiente para futura adquisición.

No crear política de concurrencia todavía.

---

## 34. Prueba funcional real

Usar el Petitorio real aprobado y su `CaseStructureDraft`.

Completar manualmente una topología de laboratorio coherente con la evidencia física disponible.

Flujo:

```text
1. abrir draft
2. completar especies
3. seleccionar relaciones
4. crear DSM
5. revisar comparación documental/física
6. resolver conflictos si existen
7. mostrar resumen
8. confirmar estructura
9. persistir caso
10. recargar navegador
11. comprobar jerarquía
12. comprobar case.json
```

No acceder a `PhysicalDrive`.

No ejecutar adquisición.

---

## 35. Tests obligatorios

Baseline inicial esperado:

```text
268 passed
```

Agregar tests como mínimo para:

1. draft inválido bloquea;
2. draft no aprobado bloquea;
3. NUE sin especie bloquea;
4. múltiples especies por NUE;
5. labels correlativos;
6. SELF_STORAGE;
7. SELF_STORAGE crea un DSM lógico;
8. SELF_STORAGE same physical object;
9. SELF_STORAGE no permite múltiples DSM;
10. CONTAINED_STORAGE;
11. CONTAINED_STORAGE un DSM;
12. CONTAINED_STORAGE múltiples DSM;
13. numeración DSM reinicia por especie;
14. DSM huérfano bloqueado;
15. conflicto documental/físico;
16. conflicto abierto bloquea confirmación;
17. resumen correcto;
18. confirmación humana requerida;
19. cancelación no persiste parcial;
20. persistencia transaccional;
21. case creado una sola vez;
22. NUE no duplicada;
23. species no duplicadas;
24. DSM no duplicados;
25. case.json generado/actualizado;
26. referencia a petition;
27. PostgreSQL coherente con case.json;
28. doble submit idempotente;
29. RUC existente no sobrescrito;
30. CSRF activo;
31. UI en español;
32. auditoría;
33. sin PhysicalDrive;
34. sin ewfacquire;
35. sin ewfverify;
36. sin E01;
37. no regla rígida de exactamente 3 fotos;
38. suite completa sin regresión.

---

## 36. Operaciones prohibidas

Durante P05:

```text
NO PhysicalDrive
NO Get-Disk para adquisición
NO selección de write blocker
NO binding DSM ↔ PhysicalDrive
NO ewfacquire
NO ewfverify
NO E01
NO AXIOM
NO Portable Case
NO Word
NO adquisición real
```

---

## 37. Criterios de aceptación

P05 queda COMPLETO únicamente si:

- Prompt Maestro leído;
- Regla Permanente leída;
- P00–P04 leídos;
- baseline registrado;
- jerarquía RUC→NUE→ESPECIE→DSM implementada;
- múltiples NUE soportadas;
- múltiples especies soportadas;
- múltiples DSM soportados;
- SELF_STORAGE confirmado humanamente;
- CONTAINED_STORAGE confirmado humanamente;
- datos PETITION y PHYSICAL separados;
- conflictos visibles;
- conflictos abiertos bloquean confirmación;
- confirmación estructural explícita;
- persistencia transaccional;
- caso definitivo creado solo tras confirmación;
- PostgreSQL coherente;
- case.json coherente;
- idempotencia;
- UI en español;
- CSRF activo;
- auditoría;
- prueba funcional real pasa;
- NO regla rígida histórica de 3 fotos;
- ninguna adquisición ejecutada;
- suite completa pasa.

---

## 38. Reporte final obligatorio

TRAE debe entregar:

```text
PETITORIO P05:
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

P03:
READ / NOT READ

P04:
READ / NOT READ

BASELINE BEFORE:
...

TESTS FINAL:
...

HIERARCHY:
RUC -> NUE -> SPECIES -> DSM
PASS / FAIL

MULTIPLE NUE:
PASS / FAIL

MULTIPLE SPECIES:
PASS / FAIL

MULTIPLE DSM:
PASS / FAIL

SELF_STORAGE:
PASS / FAIL

CONTAINED_STORAGE:
PASS / FAIL

PETITION VS PHYSICAL SEPARATION:
PASS / FAIL

PHYSICAL DESCRIPTION:
PASS / FAIL

DOCUMENTAL/PHYSICAL CONFLICTS:
PASS / FAIL

OPEN CONFLICT BLOCKING:
PASS / FAIL

STRUCTURE SUMMARY:
PASS / FAIL

HUMAN STRUCTURE CONFIRMATION:
PASS / FAIL

TRANSACTIONAL PERSISTENCE:
PASS / FAIL

CASE CREATED:
YES / NO

CASE CREATION SOURCE:
APPROVED PETITION + CONFIRMED PHYSICAL STRUCTURE

POSTGRESQL:
PASS / FAIL

CASE.JSON:
PASS / FAIL

PETITION REFERENCE IN CASE.JSON:
PASS / FAIL

IDEMPOTENCY:
PASS / FAIL

CSRF:
PASS / FAIL

UI ESPAÑOL:
PASS / FAIL

AUDIT:
PASS / FAIL

REAL PETITION / PHYSICAL STRUCTURE TEST:
PASS / FAIL

FIXED 3-PHOTO RULE:
NOT USED / INCORRECTLY USED

WRITE BLOCKER SELECTED:
NO

PHYSICALDRIVE:
NO

DSM DISK BINDING:
NO

ACQUISITION JOB CREATED:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

E01:
NO

RISKS / LIMITATIONS:
...

STATUS:
PHYSICAL_CASE_STRUCTURE_READY_FOR_P06 /
PHYSICAL_CASE_STRUCTURE_BLOCKED
```

---

## 39. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Leer P00, P01, P02, P03 y P04.
4. Ejecutar baseline.
5. Inspeccionar modelos reales de Case/NUE/Species/DSM.
6. Inspeccionar `StorageRelation` real.
7. Inspeccionar creación/persistencia actual del caso.
8. Inspeccionar `case.json`.
9. Implementar flujo web de estructura física.
10. Separar datos del Petitorio de observaciones físicas.
11. Permitir múltiples especies por NUE.
12. Implementar SELF_STORAGE.
13. Implementar CONTAINED_STORAGE.
14. Crear DSM lógicos correctamente.
15. Mostrar conflictos documentales/físicos.
16. Bloquear confirmación ante conflictos abiertos.
17. Mostrar resumen completo.
18. Requerir confirmación humana explícita.
19. Persistir transaccionalmente.
20. Crear caso definitivo solo después de confirmación.
21. Mantener PostgreSQL y `case.json` coherentes.
22. Mantener CSRF.
23. Mantener UI en español.
24. Integrar auditoría.
25. NO reintroducir regla normativa fija de exactamente 3 fotografías.
26. No seleccionar write blocker.
27. No acceder a PhysicalDrive.
28. No crear bindings.
29. No ejecutar adquisición.
30. Agregar tests.
31. Ejecutar prueba funcional real controlada.
32. Ejecutar suite completa.
33. Entregar reporte final.
34. **NO iniciar PETITORIO P06.**

Comienza ahora.
