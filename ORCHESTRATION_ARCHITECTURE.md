# Arquitectura de Orquestación — Agente Forense

## 1. Visión General
El núcleo de orquestación implementado en el Sprint R04 articula el ciclo de vida del caso forense desacoplando completamente la lógica de control del dominio de la capa web, la persistencia relacional concreta y las herramientas forenses externas.

```text
+-------------------+      +---------------------+      +---------------------+
|  State Machine    | ---> |    Policy Engine    | ---> |     Human Gate      |
| (Operative/Reserv)|      | (ALLOW/DENY/CONFIRM)|      | (Explicit Approval) |
+-------------------+      +---------------------+      +---------------------+
                                      |
                                      v
                        +---------------------------+
                        |      CaseOrchestrator     |
                        +---------------------------+
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
+---------------+             +---------------+             +----------------+
|  PostgreSQL   |             |   case.json   |             |  Audit Events  |
| (State & Ver) |             |  (Sync Snap)  |             | (Append-Only)  |
+---------------+             +---------------+             +----------------+
```

## 2. Resolución de Discrepancia DSM: `dsms` vs `storage_devices`
Inspeccionado el esquema real de PostgreSQL 18.6 (`migrations/0001_initial_schema.sql`) y los modelos ORM (`src/agente_forense/persistence/models.py`), se determinaron los siguientes hallazgos:

- **Nombre real de tabla relacional:** `forensic.dsms`
- **Modelo ORM SQLAlchemy:** `DsmModel`
- **Repositorio tipado de datos:** `DsmRepository`
- **Diagnóstico:** `dsms` es la tabla relacional real creada y utilizada por PostgreSQL. La mención de `storage_devices` en la documentación del Sprint R03 corresponde a una denominación conceptual del array JSON en el snapshot `case.json` (dentro de cada especie), no a una tabla relacional en base de datos. No existe duplicación accidental ni migración pendiente.

## 3. Componentes del Paquete `agente_forense.orchestration`
- `states.py`: Define `CaseState` (17 estados conceptuales), `OperativeState` (6 estados activos en R04: NEW, IDENTIFICATION_PENDING, IDENTIFICATION_COMPLETED, ACQUISITION_READY, FAILED, ABORTED) y `ReservedState` (11 estados reservados para fases futuras).
- `transitions.py`: Registro global de transiciones legales (`LEGAL_TRANSITIONS`) con estado origen, destino, precondiciones, políticas requeridas y audit event asociadas.
- `policies.py`: Engine estático `PolicyEngine` que evalúa decisiones de tipo `ALLOW`, `DENY` o `REQUIRES_CONFIRMATION` sin uso de LLM.
- `human_gate.py`: Gestor `HumanGate` para la creación, consulta, aprobación y rechazo de confirmaciones humanas explícitas antes de acciones sensibles sobre evidencia.
- `actions.py`: Handlers deterministas desacoplados (`StartIdentificationHandler`, `CompleteIdentificationMockHandler`, `PrepareAcquisitionHandler`, `AbortCaseHandler`, `FailCaseHandler`).
- `orchestrator.py`: `CaseOrchestrator` encargado de cargar contexto, verificar invariantes, evaluar políticas, validar Human Gate, ejecutar la transacción en PostgreSQL, incrementar `state_version` (concurrencia optimista), actualizar atómicamente `case.json` y registrar `case_events` y `audit_events`.
- `errors.py`: Jerarquía de excepciones fail-closed para la orquestación (`InvalidTransitionError`, `PolicyDeniedError`, `ConfirmationRequiredError`, `ConcurrencyConflictError`, etc.).

## 4. Persistencia, Concurrencia e Idempotencia
- **Persistencia en PostgreSQL:** El estado oficial del caso vive en la columna `status` de la tabla `forensic.cases`.
- **Concurrencia Optimista:** Implementado mediante `state_version` (columna entero en `forensic.cases`). Si se provee `expected_version` y no coincide, se rechaza la transacción con `ConcurrencyConflictError`.
- **Idempotencia:** Los Action Handlers definen un comportamiento determinista ante repetición sin duplicar transiciones ilegales.
- **Sincronización `case.json`:** Tras cada transición exitosa en PostgreSQL, el snapshot `case.json` se escribe de manera atómica (mediante archivo `.tmp`, `fsync` y `os.replace`) y se ejecuta una reconciliación inmediata.

## 5. Integración API & Web
- Endpoints expuestos:
  - `GET /api/cases/{id}/state`
  - `GET /api/cases/{id}/actions`
  - `POST /api/cases/{id}/actions/{action}`
  - `POST /api/confirmations/{id}/confirm`
  - `POST /api/confirmations/{id}/reject`
- Protección CSRF: Todas las rutas de modificación `POST` requieren token CSRF válido.
- Dashboard & Vista de Caso: Muestran estado de orquestación, reconciliación `case.json`, acciones permitidas/bloqueadas y confirmaciones pendientes.
