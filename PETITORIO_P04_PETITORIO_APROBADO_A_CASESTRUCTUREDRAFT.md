# PETITORIO P04 — Oficio Petitorio Aprobado a CaseStructureDraft

## 1. Objetivo

Implementar la transición controlada desde un **Oficio Petitorio aprobado** hacia un `CaseStructureDraft` persistente y utilizable por el flujo de creación del caso.

El objetivo de este sprint es:

```text
PETITION APPROVED
→ VALIDACIÓN
→ CaseStructureDraft
→ RUC
→ 1..N NUE
```

Sin crear todavía automáticamente:

```text
ESPECIE
DSM
StorageRelation
Acquisition Job
```

Este sprint debe consolidar correctamente la información documental ya revisada y aprobada, preparándola para el siguiente paso donde el operador completará la topología física real.

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

Baseline validado al cierre de P03:

```text
262 passed
```

El flujo actual ya dispone de:

```text
Petitorio persistido en PostgreSQL
OCR estructurado
revisión humana
resolución de conflictos
aprobación explícita
CSRF activo
auditoría
persistencia tras recarga
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
```

También debe inspeccionar el código real vigente de:

```text
CaseStructureDraft
DraftMapper
PetitionService
PetitionPersistenceService
CaseService / Case creator
NUE models
repositories
api_petitions.py
case_new.html
```

Antes de cambios:

1. ejecutar suite completa;
2. registrar baseline real;
3. inspeccionar contrato actual de `CaseStructureDraft`;
4. inspeccionar cómo se crean hoy casos manuales;
5. inspeccionar cómo se crean hoy NUE;
6. inspeccionar cómo se persiste `case.json`;
7. inspeccionar si existe ya un vínculo petition → case;
8. no asumir rutas ni helpers inexistentes.

Si aparece una discrepancia:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de cerrar el sprint.

---

## 4. Principio arquitectónico obligatorio

Mantener:

```text
OFICIO PETITORIO != CASO
```

Y también:

```text
PETITORIO APROBADO
→ FUENTE DOCUMENTAL CONFIRMADA
```

no significa:

```text
TOPOLOGÍA FÍSICA CONFIRMADA
```

Por tanto:

```text
CaseStructureDraft
```

debe contener solamente información documental confirmada.

No debe contener hechos físicos no inspeccionados.

---

## 5. Requisito de aprobación previa

Solo un Petitorio con estado real equivalente a:

```text
APPROVED
```

puede generar un `CaseStructureDraft`.

Si el Petitorio está:

```text
STAGED
FIELDS_EXTRACTED
REVIEW_REQUIRED
REVIEW_COMPLETED
FAILED
```

o cualquier estado no aprobado:

```text
BLOQUEAR
```

Código de error conceptual:

```text
PETITION_NOT_APPROVED
```

o equivalente real del proyecto.

---

## 6. Validaciones previas a generar Draft

Antes de generar el draft validar:

```text
RUC confirmado
>= 1 NUE confirmada
sin conflictos abiertos
sin campos críticos pendientes
revisión persistida
Petitorio aprobado
```

Si falla cualquiera:

```text
NO GENERAR DRAFT
```

No intentar completar valores automáticamente.

---

## 7. CaseStructureDraft

Reutilizar el modelo real existente.

No crear un segundo modelo paralelo si el actual es extensible.

Debe representar como mínimo:

```text
ruc
nues
requesting_unit
requesting_rut
oficio_number
requested_diligence
status
notes
```

Pero P04 debe evaluar si el modelo actual requiere ampliación controlada para vincular correctamente el Petitorio aprobado.

Campos candidatos:

```text
petition_id
petition_sha256
petition_number
petition_date
source = PETITION
```

No agregarlos si ya existe una forma equivalente real.

Documentar cualquier extensión.

---

## 8. NUEs derivadas del Petitorio

Debe soportar:

```text
1 RUC
→ 1..N NUE
```

Por cada NUE confirmada:

```text
DraftNue
```

debe incluir como mínimo:

```text
nue_number
description_from_petition
```

Si el modelo real ya admite más metadata documental, puede incluirse:

```text
quantity
declared_evidence_type
brand_declared
model_declared
serial_declared
capacity_declared
```

solo si existe soporte real y sin convertir esos datos en identificación física.

---

## 9. No crear especies automáticamente

Aunque el Petitorio contenga una descripción como:

```text
01 Computador portátil marca Lenovo...
```

P04 NO debe convertir eso automáticamente en:

```text
ESPECIE1
```

definitiva.

La razón es conceptual:

```text
DESCRIPCIÓN DOCUMENTAL
!=
INSPECCIÓN FÍSICA
```

El siguiente sprint será responsable de permitir al operador:

```text
NUE
→ ESPECIE
→ SELF_STORAGE / CONTAINED_STORAGE
→ DSM
```

---

## 10. No crear DSM automáticamente

P04 NO debe:

```text
crear DSM
inferir DSM
inferir storage relation
crear PhysicalDrive binding
crear acquisition job
```

Aunque la descripción documental mencione:

```text
pendrive
SSD
HDD
notebook
computador
microSD
```

La topología física se confirma posteriormente.

---

## 11. Evidencia documental dentro del Draft

Los datos declarados por el Petitorio deben conservar su semántica documental.

Ejemplo:

```json
{
  "nue_number": "7746537",
  "description_from_petition": "Computador portátil",
  "attributes_from_petition": {
    "brand": "Lenovo",
    "model": "E-41-55",
    "serial": "MPIZGTX4"
  }
}
```

Estos valores deben ser considerados:

```text
SOURCE = PETITION
```

No:

```text
SOURCE = PHYSICAL_INSPECTION
```

---

## 12. Requested diligence

El draft debe poder transportar las diligencias solicitadas confirmadas.

Preferir preservar:

```text
source_text
```

y opcionalmente:

```text
normalized_action
```

Nunca perder el texto fuente documental.

Si existen múltiples diligencias:

```text
1..N
```

el draft no debe colapsarlas de forma destructiva.

---

## 13. Metadata del Petitorio

El draft debe poder referenciar:

```text
petition_id
file_id
sha256
petition_number
petition_date
```

directamente o mediante referencia estructurada al Petitorio persistido.

No duplicar información si el modelo ya permite referencia por ID.

---

## 14. Estado del Draft

Usar el estado real existente si ya está definido.

Conceptualmente:

```text
DRAFT_PROPOSED
```

o equivalente.

El draft debe reflejar:

```text
PENDING_PHYSICAL_INSPECTION
```

para la topología física aún no confirmada.

No marcar:

```text
READY_FOR_ACQUISITION
```

en P04.

---

## 15. Idempotencia

Generar el draft múltiples veces a partir del mismo Petitorio aprobado no debe producir inconsistencias.

Debe cumplirse:

```text
same petition
→ same logical RUC/NUE structure
```

No duplicar NUE.

No crear múltiples drafts activos incompatibles para el mismo Petitorio salvo diseño explícito.

Si existe un draft previo:

- reutilizar;
- actualizar de forma controlada;
- versionar;
- o bloquear.

Seguir la arquitectura real existente.

Documentar la decisión.

---

## 16. Persistencia del Draft

Inspeccionar si `CaseStructureDraft` hoy:

- vive en memoria;
- se serializa;
- se persiste en PostgreSQL;
- se deriva al vuelo.

P04 debe dejar el draft recuperable tras reinicio/recarga.

No depender únicamente de memoria temporal.

Si no existe persistencia del draft, implementar la mínima necesaria siguiendo los patrones reales del proyecto.

No crear un segundo JSON maestro paralelo.

---

## 17. Relación petition → draft

Debe existir trazabilidad explícita:

```text
Petition
→ CaseStructureDraft
```

Registrar:

```text
petition_id
draft_id o referencia equivalente
created_at
created_by
source_status
```

cuando corresponda.

---

## 18. Relación draft → futuro case

P04 debe preparar, NO ejecutar todavía:

```text
CaseStructureDraft
→ Case creation
```

El siguiente sprint será responsable de la confirmación física y creación definitiva.

No crear todavía:

```text
forensic.cases
forensic.nues definitivas
filesystem case root
case.json definitivo
```

si el diseño real separa esa etapa.

---

## 19. API

Implementar o ajustar endpoint controlado para:

```text
generar draft desde Petitorio aprobado
consultar draft
```

Preferir reutilizar:

```text
POST /api/petitions/{doc_id}/draft
POST /api/petitions/{doc_id}/build-draft
```

si ya existen.

No crear endpoints duplicados innecesarios.

Mantener:

```text
CSRF para mutaciones
errores controlados
respuesta estable
```

---

## 20. UI en español

La interfaz debe mostrar:

```text
Generar estructura preliminar del caso
```

o equivalente.

Después de generar:

```text
Estructura preliminar generada
```

Mostrar resumen:

```text
RUC
NUEs
Descripción documental
Diligencias solicitadas
Estado
```

Y advertencia visible:

```text
La estructura física de especies y dispositivos de almacenamiento aún debe ser confirmada.
```

Toda la UI visible debe permanecer en español.

---

## 21. Human Gate

La generación del Draft NO necesita todavía una confirmación forense crítica tipo adquisición.

Pero debe ser una acción explícita del operador.

No generar automáticamente un draft al subir OCR sin revisión.

Solo después de:

```text
PETITION APPROVED
```

y acción humana explícita.

---

## 22. Auditoría

Registrar como mínimo:

```text
petition_draft_generation_requested
petition_draft_generated
petition_draft_generation_failed
petition_draft_reused
petition_draft_updated
```

Cuando corresponda registrar:

```text
petition_id
ruc
nue_count
operator
timestamp
result
```

No almacenar datos innecesarios en logs.

---

## 23. Caso de RUC ya existente

Inspeccionar comportamiento real actual.

Si el RUC ya existe en `cases`:

NO sobrescribir automáticamente.

Posibles resultados:

```text
CASE_ALREADY_EXISTS
CASE_STRUCTURE_CONFLICT
CASE_DRAFT_REQUIRES_RECONCILIATION
```

Elegir según arquitectura real.

No agregar nuevas NUE al caso existente en P04.

Eso debe ocurrir en un sprint posterior explícito.

---

## 24. NUE duplicada

Si dos evidencias documentales producen la misma NUE:

normalizar según la revisión humana final.

No crear dos `DraftNue` con el mismo `nue_number`.

Si existe información contradictoria:

```text
CONFLICT
```

y bloquear generación automática del draft hasta resolver.

---

## 25. Prueba funcional real

Usar el mismo Petitorio de laboratorio aprobado.

Validar:

```text
Petitorio aprobado
→ Generate Draft
→ RUC correcto
→ NUE(s) correctas
→ metadata documental
→ no species
→ no DSM
→ no acquisition
```

Después:

```text
recargar navegador / reiniciar proceso si aplica
```

y confirmar que el draft sigue recuperable.

---

## 26. Tests obligatorios

Baseline inicial esperado:

```text
262 passed
```

Agregar tests como mínimo para:

1. Petitorio no aprobado bloquea draft;
2. RUC confirmado requerido;
3. al menos una NUE requerida;
4. conflicto abierto bloquea;
5. draft con un NUE;
6. draft con múltiples NUE;
7. NUE duplicada no duplica;
8. descripción documental preservada;
9. attributes_from_petition preservados si aplica;
10. diligencias preservadas;
11. petition_id trazable;
12. petition SHA-256 trazable;
13. draft status correcto;
14. pending physical inspection;
15. no species;
16. no DSM;
17. no StorageRelation;
18. no case definitivo;
19. no acquisition jobs;
20. idempotencia;
21. draft recuperable tras recarga/reinicio;
22. CSRF activo;
23. UI en español;
24. auditoría;
25. RUC existente no sobrescrito;
26. suite completa sin regresión.

---

## 27. Operaciones prohibidas

Durante P04:

```text
NO PhysicalDrive
NO ewfacquire
NO ewfverify
NO E01
NO write blocker selection
NO adquisición
NO species física definitiva
NO DSM
NO StorageRelation definitiva
NO AXIOM
NO Portable Case
NO Word
```

---

## 28. Criterios de aceptación

P04 queda COMPLETO únicamente si:

- Prompt Maestro leído;
- Regla Permanente leída;
- P00/P01/P02/P03 leídos;
- baseline registrado;
- solo Petitorio aprobado genera draft;
- RUC y NUE se derivan correctamente;
- múltiples NUE soportadas;
- datos documentales preservan provenance;
- diligencias preservadas;
- no se crean especies;
- no se crean DSM;
- no se crea topología física;
- no se crea adquisición;
- idempotencia validada;
- draft recuperable;
- API estable;
- CSRF activo;
- UI en español;
- auditoría integrada;
- prueba funcional real pasa;
- suite completa pasa;
- ninguna operación forense real ejecutada.

---

## 29. Reporte final obligatorio

TRAE debe entregar:

```text
PETITORIO P04:
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

BASELINE BEFORE:
...

TESTS FINAL:
...

APPROVED PETITION REQUIRED:
PASS / FAIL

RUC MAPPING:
PASS / FAIL

MULTIPLE NUE:
PASS / FAIL

DUPLICATE NUE HANDLING:
PASS / FAIL

DOCUMENTAL DESCRIPTION PRESERVED:
PASS / FAIL

DOCUMENTAL ATTRIBUTES PRESERVED:
PASS / FAIL

REQUESTED DILIGENCES PRESERVED:
PASS / FAIL

PETITION TRACEABILITY:
PASS / FAIL

DRAFT STATUS:
...

PENDING PHYSICAL INSPECTION:
PASS / FAIL

IDEMPOTENCY:
PASS / FAIL

DRAFT RECOVERY:
PASS / FAIL

API:
PASS / FAIL

CSRF:
PASS / FAIL

UI ESPAÑOL:
PASS / FAIL

AUDIT:
PASS / FAIL

REAL PETITION TEST:
PASS / FAIL

CASE CREATED:
NO

NUE DEFINITIVE CREATED:
NO

SPECIES CREATED:
NO

DSM CREATED:
NO

STORAGE RELATION CREATED:
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
CASE_STRUCTURE_DRAFT_READY_FOR_P05 /
CASE_STRUCTURE_DRAFT_BLOCKED
```

---

## 30. Instrucción final para TRAE

1. Leer `PROMPT_MAESTRO.md`.
2. Leer `REGLA_PERMANENTE_PRE_SPRINT.md`.
3. Leer P00, P01, P02 y P03.
4. Ejecutar baseline.
5. Inspeccionar contrato real de `CaseStructureDraft`.
6. Inspeccionar `DraftMapper`.
7. Inspeccionar creación manual actual de casos.
8. Inspeccionar persistencia actual del draft.
9. Exigir Petitorio aprobado.
10. Generar draft con RUC y NUE confirmadas.
11. Preservar metadata documental y provenance.
12. No crear especies.
13. No crear DSM.
14. No crear StorageRelation.
15. No crear caso definitivo.
16. No crear acquisition jobs.
17. Implementar idempotencia.
18. Hacer draft recuperable.
19. Mantener CSRF.
20. Mantener UI en español.
21. Integrar auditoría.
22. Agregar tests.
23. Ejecutar prueba funcional real con el Petitorio aprobado.
24. Ejecutar suite completa.
25. Entregar reporte final.
26. **NO iniciar PETITORIO P05.**

Comienza ahora.
