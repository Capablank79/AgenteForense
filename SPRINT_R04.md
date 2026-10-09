# SPRINT_R04 — State Machine + Policy Engine + Orchestrator Base

## 1. Objetivo

Implementar el núcleo de orquestación del AGENTE FORENSE:

```text
STATE MACHINE
+
POLICY ENGINE
+
ORCHESTRATOR
+
AUDIT
+
HUMAN GATE
```

sobre el dominio:

```text
RUC → NUE → ESPECIE → DSM
```

Este sprint NO ejecuta operaciones forenses reales.

Debe permitir conocer estado actual, calcular transiciones válidas, bloquear transiciones inválidas, registrar eventos, ejecutar acciones simuladas, persistir y recuperar estado tras reinicio, exponer estado/acciones vía API/Web y preparar integración futura con adquisición, verificación y AXIOM.

Estado esperado:

```text
ORCHESTRATION_FOUNDATION_READY
```

## 2. Documentación obligatoria

Leer completos antes de modificar código:

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
RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
PERSISTENCE_ARCHITECTURE.md
WEB_STACK_CAPABILITIES.md
WEB_ARCHITECTURE.md
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
SPRINT_R04.md
```

Revisar además reportes finales de R00 a R03.

## 3. Baseline esperado

```text
PYTHON: 3.10.11
POSTGRESQL: 18.6
DB: agente_forense_db
DB HOST: 127.0.0.1
DB PORT: 5433
WEB: 127.0.0.1:8085
TESTS: 83 passed
```

Ejecutar antes:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Si hay regresión: detener y documentar.

## 4. Verificación previa obligatoria — DSM

Antes de crear código nuevo, inspeccionar el schema PostgreSQL REAL y resolver la discrepancia documental:

R01.1 reportó:
```text
forensic.dsms
```

R03 reportó:
```text
storage_devices
```

Determinar:
- nombre real de tabla;
- nombre real del modelo ORM;
- nombre real del repository;
- si existió migración;
- si ambos son aliases;
- si hay duplicación accidental.

No modificar datos para “hacer coincidir” documentación.

Registrar resultado en `ORCHESTRATION_ARCHITECTURE.md`.

## 5. Máquina de estados

Estados conceptuales permitidos:

```text
NEW
IDENTIFICATION_PENDING
IDENTIFICATION_COMPLETED
ACQUISITION_READY
ACQUIRING
ACQUISITION_COMPLETED
ACQUISITION_VERIFIED
ANALYSIS_PENDING
PROCESSING_AXIOM
ANALYSIS_COMPLETED
RESULTS_PENDING
PORTABLE_CREATED
REPORT_PENDING
REPORT_GENERATED
COMPLETED
FAILED
ABORTED
```

R04 debe distinguir:
- estados conocidos;
- estados operativos ahora;
- estados reservados para fases futuras;
- transiciones legales;
- transiciones ilegales;
- estados terminales;
- recuperación desde error.

## 6. Estados operativos R04

Implementar realmente como mínimo:

```text
NEW
IDENTIFICATION_PENDING
IDENTIFICATION_COMPLETED
ACQUISITION_READY
FAILED
ABORTED
```

No permitir simular como reales:

```text
ACQUISITION_COMPLETED
ACQUISITION_VERIFIED
ANALYSIS_COMPLETED
PORTABLE_CREATED
REPORT_GENERATED
COMPLETED
```

## 7. Paquete orchestration

Crear equivalente a:

```text
src/agente_forense/orchestration/
    __init__.py
    states.py
    transitions.py
    policies.py
    orchestrator.py
    actions.py
    context.py
    errors.py
```

Desacoplado de FastAPI, PostgreSQL concreto, herramientas externas y UI.

## 8. Transition Model

Cada transición debe declarar:

```text
source_state
target_state
action
preconditions
policy_checks
requires_human_confirmation
audit_event
```

## 9. Policy Engine

Implementar `PolicyEngine` o equivalente con decisiones:

```text
ALLOW
DENY
REQUIRES_CONFIRMATION
```

y razones estructuradas.

No usar LLM para decisiones críticas.

## 10. Policies iniciales

Implementar al menos:

```text
CASE_EXISTS
CASE_STRUCTURE_VALID
HAS_NUE
HAS_SPECIES
HAS_DSM
CASE_JSON_MATCH
NO_CRITICAL_RECONCILIATION_ERROR
STATE_TRANSITION_ALLOWED
```

Reservar para futuro:

```text
SOURCE_READ_ONLY
SOURCE_NOT_SYSTEM
SOURCE_NOT_BOOT
PHYSICAL_DRIVE_BOUND
DESTINATION_SAFE
E01_NOT_EXISTS
HUMAN_CONFIRMATION_PRESENT
```

sin acceder a hardware en R04.

## 11. Human Gate

Implementar mecanismo genérico de confirmación humana con:

```text
confirmation_id
case_id
requested_action
summary
requested_at
confirmed_at
operator
status
request_id
```

Estados:

```text
PENDING
CONFIRMED
REJECTED
EXPIRED
```

## 12. Regla de confirmación vigente

Mientras `PROMPT_MAESTRO.md` no sea actualizado formalmente:

```text
mostrar resumen
→ requerir confirmación explícita
→ registrar confirmación
```

antes de operaciones reales sobre evidencia.

R04 debe soportarlo.

No activar todavía política de “autorización amplia + excepciones”.

## 13. Orchestrator

Crear `CaseOrchestrator` o equivalente.

Responsabilidades:

```text
load case
load current state
load reconciliation
evaluate policies
calculate allowed actions
request confirmation if needed
execute action handler
persist event/state
update case.json
audit
return result
```

No SQL directo.

## 14. Action Handlers

Definir interfaz `ActionHandler`.

Ejemplos R04:

```text
StartIdentificationHandler
CompleteIdentificationMockHandler
PrepareAcquisitionHandler
AbortCaseHandler
FailCaseHandler
```

Solo mocks/fakes. Sin OCR, EWF, AXIOM ni hardware.

## 15. Idempotencia

Las acciones deben definir comportamiento ante repetición.

No duplicar eventos/transiciones.

## 16. Concurrencia

Inspeccionar si existe `updated_at`, `version` o `revision`.

Si no existe control suficiente, implementar `state_version` o equivalente para evitar dos cambios simultáneos desde el mismo estado.

Si requiere migración, usar el siguiente número real disponible.

## 17. Persistencia de estado

El estado oficial vive en PostgreSQL.

`case.json` refleja snapshot.

Flujo:

```text
validate transition
↓
transaction
↓
state/event persistence
↓
commit
↓
case.json snapshot
↓
reconciliation
```

Si falla `case.json`, registrar inconsistencia y no declarar MATCH.

## 18. Case Events

Registrar:

```text
case_id
event_type
from_state
to_state
action
timestamp
operator
request_id
result
details
```

## 19. Audit Events

Registrar:

```text
STATE_TRANSITION_REQUESTED
POLICY_EVALUATED
HUMAN_CONFIRMATION_REQUESTED
HUMAN_CONFIRMATION_RECORDED
ACTION_EXECUTED
STATE_TRANSITION_COMPLETED
STATE_TRANSITION_REJECTED
ORCHESTRATION_ERROR
```

`audit_events` sigue append-only a nivel aplicación.

## 20. Recuperación tras reinicio

Probar:

1. crear caso sintético;
2. ejecutar transición;
3. destruir instancia app/service;
4. recrear;
5. consultar;
6. estado y acciones permitidas deben persistir.

## 21. Allowed Actions

Implementar:

```text
get_allowed_actions(case_id)
```

Debe devolver:

```text
action
allowed
requires_confirmation
reason
```

La UI no inventa acciones.

## 22. API

Agregar equivalentes a:

```text
GET  /api/cases/{id}/state
GET  /api/cases/{id}/actions
POST /api/cases/{id}/actions/{action}
POST /api/confirmations/{confirmation_id}/confirm
POST /api/confirmations/{confirmation_id}/reject
```

State-changing endpoints requieren CSRF.

## 23. Web

En `/cases/{id}` mostrar:

```text
estado actual
reconciliation status
acciones disponibles
acciones bloqueadas + razón
últimos eventos
confirmaciones pendientes
```

No mostrar acciones prohibidas como ejecutables.

## 24. Dashboard

Agregar:

```text
case state
last event
pending confirmation
blocked status
```

No implementar todavía `next_action` autónoma avanzada.

## 25. Errores

Crear equivalentes a:

```text
InvalidTransitionError
PolicyDeniedError
ConfirmationRequiredError
ConfirmationNotFoundError
ConfirmationAlreadyResolvedError
ConcurrencyConflictError
OrchestrationPersistenceError
```

Mapear a respuestas HTTP seguras.

## 26. Fail-Closed

Detener ante:

```text
estado desconocido
case.json mismatch crítico
policy no evaluable
confirmación faltante
concurrency conflict
DB error
```

Nunca avanzar por defecto.

## 27. FAILED

Registrar:

```text
failed_action
failed_at
error_code
recoverable
```

No borrar historial.

## 28. ABORTED

Cancelación humana explícita.

Debe preservar datos, registrar operador y motivo opcional y bloquear acciones posteriores salvo recuperación formal futura.

## 29. No saltar estados

Ejemplos prohibidos:

```text
NEW → ACQUISITION_READY
NEW → ACQUISITION_COMPLETED
IDENTIFICATION_PENDING → ANALYSIS_PENDING
```

## 30. No falsificar completitud

R04 no debe marcar fases completadas que dependan de artefactos reales no generados.

## 31. Test Doubles

Preparar interfaces/fakes para:

```text
IdentificationProvider
AcquisitionProvider
VerificationProvider
AnalysisProvider
```

## 32. Tests obligatorios

Mantener los 83 tests y agregar al menos:

1. NEW inicial.
2. NEW → IDENTIFICATION_PENDING válido.
3. transición inválida rechazada.
4. no saltar estados.
5. IDENTIFICATION_PENDING → IDENTIFICATION_COMPLETED mock.
6. IDENTIFICATION_COMPLETED → ACQUISITION_READY si hay DSM.
7. sin DSM => DENY.
8. case.json mismatch => DENY.
9. invalid JSON => DENY.
10. allowed actions correctas.
11. blocked actions con razón.
12. policy ALLOW.
13. policy DENY.
14. policy REQUIRES_CONFIRMATION.
15. confirmation create.
16. confirmation confirm.
17. confirmation reject.
18. double confirmation reject.
19. unknown confirmation reject.
20. transición que requiere confirmación se bloquea antes.
21. confirmada procede.
22. audit request.
23. audit denied.
24. audit completed.
25. case event from/to.
26. request_id preservado.
27. state persisted.
28. restart recovery.
29. idempotent action.
30. concurrency conflict.
31. rollback on DB failure.
32. case.json actualizado.
33. reconciliation MATCH.
34. case.json write failure visible.
35. FAILED preserva historial.
36. ABORTED preserva historial.
37. CSRF required.
38. API state.
39. API actions.
40. API action execute.
41. web state display.
42. web pending confirmation.
43. no forbidden action buttons.
44. no `casos/` real.
45. no PhysicalDrive.
46. no EWF.
47. no AXIOM.
48. no Ollama.
49. no OpenClaw.

## 33. Prueba funcional sintética

Crear caso temporal:

```text
RUC_TEST_R04
NUE_777777
ESPECIE1 SELF_STORAGE
DSM1
```

Ejecutar con mocks:

```text
NEW
→ IDENTIFICATION_PENDING
→ IDENTIFICATION_COMPLETED
→ ACQUISITION_READY
```

Persistir state, case_events, audit_events, case.json y reconciliation MATCH.

No adquirir.

## 34. Migraciones

Solo si son necesarias.

Inspeccionar primero `cases`, `case_events`, `audit_events` y cualquier tabla de confirmaciones.

No editar migraciones aplicadas.

## 35. Documentación

Crear:

```text
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
```

Documentar estados, transiciones, policies, human gate, concurrencia, idempotencia, event log, recuperación, integración DB/case.json, endpoints y limitaciones.

## 36. Fuera de alcance

Prohibido:

- petitorio real;
- OCR;
- fotografías reales;
- visión;
- PhysicalDrive;
- Set-Disk;
- DiskPart;
- CHKDSK;
- ewfacquire;
- ewfverify;
- AXIOM;
- Ollama;
- OpenClaw;
- Portable;
- RAR;
- Word;
- evidencia real;
- `casos/` productivo.

## 37. Criterio de aceptación

R04 queda COMPLETO si:

- baseline 83+ verde;
- discrepancia `dsms` vs `storage_devices` verificada/documentada;
- state machine implementada;
- policy engine implementado;
- orchestrator implementado;
- human gate implementado;
- estado persistente;
- case events;
- audit events;
- allowed actions;
- concurrencia controlada;
- idempotencia;
- recuperación tras restart;
- API;
- web;
- CSRF;
- case.json actualizado;
- reconciliación posterior;
- fail-closed;
- ningún acceso a evidencia;
- ninguna herramienta forense ejecutada;
- suite completa verde.

Estado:

```text
ORCHESTRATION_FOUNDATION_READY
```

Si falla requisito crítico:

```text
ORCHESTRATION_FOUNDATION_BLOCKED
```

## 38. Git

Antes de commit:

```text
pytest
git status
```

Confirmar ausencia de:

```text
.env
secrets
runtime files
test artifacts
casos/
E01
photos
petitorios
```

Commit sugerido:

```text
Sprint R04: implementa state machine policy engine y orchestrator
```

## 39. Reporte final obligatorio

```text
SPRINT R04:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
DSM TABLE VERIFICATION:
...
MIGRATIONS:
...
STATE MACHINE:
...
OPERATIVE STATES:
...
RESERVED STATES:
...
TRANSITIONS:
...
POLICY ENGINE:
...
HUMAN GATE:
...
ORCHESTRATOR:
...
IDEMPOTENCY:
...
CONCURRENCY:
...
CASE EVENTS:
...
AUDIT EVENTS:
...
CASE.JSON:
...
RECONCILIATION:
...
RECOVERY AFTER RESTART:
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
TESTS ADDED:
...
TESTS FINAL:
...
POSTGRESQL MODIFIED:
NO / SI
DETALLE:
...
CASOS/ MODIFIED:
NO / SI
EVIDENCE READ:
NO / SI
PHYSICALDRIVE:
NO / SI
EWFACQUIRE:
NO / SI
EWFVERIFY:
NO / SI
AXIOM:
NO / SI
OLLAMA:
NO / SI
OPENCLAW:
NO / SI
RISKS:
...
BLOCKERS:
...
STATUS:
ORCHESTRATION_FOUNDATION_READY / ORCHESTRATION_FOUNDATION_BLOCKED
```

## 40. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. verifica el schema real y resuelve `dsms` vs `storage_devices`;
4. implementa state machine;
5. implementa policy engine;
6. implementa human gate;
7. implementa orchestrator;
8. persiste eventos/estado;
9. integra case.json;
10. implementa recuperación;
11. integra API/Web;
12. agrega tests;
13. ejecuta suite completa;
14. verifica que `casos/` siga intacto;
15. entrega reporte;
16. detente;
17. NO inicies R05.

Comienza ahora.
