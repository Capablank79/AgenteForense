# SPRINT_R03 — Dominio RUC → NUE → ESPECIE → DSM + case.json

## 1. Objetivo
Implementar el modelo operacional central del AGENTE FORENSE:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

integrado con PostgreSQL, File Store, `case.json`, Web/API y auditoría.

Este sprint debe permitir crear y consultar estructuras de caso sintéticas completas, persistidas de manera coherente tanto en PostgreSQL como en `case.json`.

NO se ejecutará ninguna operación forense real.

Estado esperado:

```text
FORENSIC_DOMAIN_FOUNDATION_READY
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
RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
PERSISTENCE_ARCHITECTURE.md
WEB_STACK_CAPABILITIES.md
WEB_ARCHITECTURE.md
SPRINT_R03.md
```

Revisar además los reportes reales de R00, R01, R01.1, R02 y R02.1.

Los sprints históricos previos a la reconstrucción sirven solo como referencia conceptual del dominio, nunca como evidencia de código existente.

## 3. Baseline
Esperado:

```text
PYTHON: 3.10.11
POSTGRESQL: 18.6
DB HOST: 127.0.0.1
DB PORT: 5433
DB: agente_forense_db
WEB: FastAPI + Uvicorn en 127.0.0.1:8085
TESTS: 66 passed
```

Ejecutar antes de cambios:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Si hay regresión: detener, documentar y no implementar.

## 4. Jerarquía oficial
```text
RUC → NUE → ESPECIE → DSM
```

Definiciones:
- RUC = identificador/caso principal.
- NUE = evidencia asociada al caso.
- ESPECIE = objeto físico.
- DSM = dispositivo/medio de almacenamiento digital.

## 5. No invención
Campos desconocidos deben quedar `null`, `PENDING`, `NOT_PROVIDED`, `NOT_VISIBLE` o `UNKNOWN` según semántica.

No inventar marca, modelo, serial, capacidad, color, PhysicalDrive, E01, hashes, fechas no observadas, unidad solicitante, diligencias ni contenido del petitorio.

## 6. Relaciones físicas
Valores permitidos:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

SELF_STORAGE:
```text
storage_relation = SELF_STORAGE
same_physical_object_as_species = true
DSM count = 1
DSM number = 1
```

CONTAINED_STORAGE:
```text
storage_relation = CONTAINED_STORAGE
same_physical_object_as_species = false
DSM count >= 1
```

## 7. Identificadores
Persistencia primaria: UUID interno.

Identidad forense visible:
```text
RUC
NUE
species_number
dsm_number
```

Labels determinísticas:
```text
RUC_<RUC>
NUE_<NUE>
NUE_<NUE>_ESPECIE<n>
NUE_<NUE>_ESPECIE<n>_DSM<m>
```

El usuario no escribe manualmente labels derivadas.

## 8. Validación RUC/NUE
No inventar validación jurídica/formal.

Aplicar solo validación técnica segura:
- no vacío;
- sin path traversal;
- sin separadores de ruta;
- sin nombres Windows reservados;
- normalización documentada;
- NUE única dentro del RUC.

## 9. Numeración
ESPECIE dentro de cada NUE: correlativa desde 1.

DSM dentro de cada ESPECIE: correlativa desde 1.

SELF_STORAGE exige exactamente DSM1.

CONTAINED_STORAGE exige uno o más DSM.

## 10. Modelo de dominio Python
Crear paquete equivalente a:

```text
src/agente_forense/domain/
    __init__.py
    cases.py
    hierarchy.py
    enums.py
    validation.py
    errors.py
```

Usar type hints, enums, invariantes explícitas y errores específicos.

No acoplar dominio directamente a FastAPI.

## 11. CaseStructureDraft
Implementar `CaseStructureDraft`.

Debe representar una propuesta antes de persistir y poder construirse desde:
```text
entrada manual
futuro PetitorioParser
futuro OCR
futuro agente conversacional
```

Debe incluir al menos:
```text
ruc
nues[]
species[]
dsms[]
```

## 12. Draft vs persistido
Flujo:

```text
INPUT
↓
CaseStructureDraft
↓
VALIDATION
↓
SUMMARY
↓
CONFIRMATION / TEST ACCEPT
↓
TRANSACTION
↓
POSTGRESQL
↓
case.json
```

No persistir parcialmente durante la construcción del draft.

## 13. Persistencia transaccional
La creación de case, nues, species y dsms debe ser atómica.

Cualquier fallo => `ROLLBACK`.

## 14. case.json
Después de commit exitoso en DB, generar/actualizar `case.json` mediante servicio explícito, no desde routes.

Semántica:
```text
PostgreSQL = memoria operacional global / índice / estado vivo
case.json  = snapshot portable por caso / contrato interoperable
```

## 15. schema_version
La reconstrucción debe tomar una decisión explícita.

Preferencia para esta nueva línea:
```text
schema_version = 1
```

No reutilizar automáticamente `schema_version = 2` histórico solo porque existía en código perdido.

Documentar la decisión.

## 16. Contenido mínimo case.json
```json
{
  "schema_version": 1,
  "case_id": "...",
  "ruc": "...",
  "status": "NEW",
  "created_at": "...",
  "updated_at": "...",
  "nues": []
}
```

Cada NUE contiene `nue` y `species`.

Cada ESPECIE contiene:
```text
species_number
label
storage_relation
identification_status=PENDING
storage_devices
```

Cada DSM contiene:
```text
dsm_number
label
same_physical_object_as_species
physical_drive=null
acquisition_status=PENDING
verification_status=PENDING
```

## 17. Escritura atómica
Usar patrón:
```text
write temp
flush
fsync cuando aplique
atomic replace
```

No truncar un snapshot válido antes de tener reemplazo completo.

## 18. Reconciliación DB ↔ case.json
Implementar:
```text
MATCH
MISSING_FILE
INVALID_JSON
SCHEMA_MISMATCH
CONTENT_MISMATCH
```

No corregir silenciosamente.

## 19. Filesystem
Solo usar root temporal/de test.

NO tocar `casos/` real.

Estructura conceptual futura:
```text
RUC_<RUC>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

## 20. E01 futuro
Solo derivar target:
```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

No crear E01.

## 21. Fotografías
NO imponer todavía una cantidad fija como regla normativa de la reconstrucción.

Se puede reservar `photo_count` y `photos_status`, pero no fijar automáticamente `expected=3` hasta formalizarlo en documentación vigente.

## 22. Estados iniciales
```text
case.status = NEW
identification_status = PENDING
acquisition_status = PENDING
verification_status = PENDING
```

No marcar completado sin proceso real.

## 23. Auditoría
Registrar al menos:
```text
CASE_CREATED
NUE_ADDED
SPECIES_ADDED
DSM_ADDED
CASE_JSON_WRITTEN
CASE_JSON_RECONCILED
```

Con timestamp, case_id, module, action, result, operator y request_id cuando provenga de web.

## 24. Web
Actualizar `/cases/new` para construir estructura sintética/manual mínima:
```text
RUC
NUE(s)
ESPECIE(s)
SELF_STORAGE / CONTAINED_STORAGE
DSM count
```

Mantener claro que el flujo definitivo futuro será:
```text
PETITORIO → OCR → CaseStructureDraft
```

## 25. API
Implementar equivalentes a:
```text
POST /api/cases/draft
POST /api/cases
GET  /api/cases
GET  /api/cases/{id}
GET  /api/cases/{id}/reconciliation
```

`POST /api/cases/draft` valida y NO persiste.

`POST /api/cases` valida, persiste transaccionalmente, genera snapshot, escribe `case.json`, audita y responde.

En R03 opera solo sobre root controlado/de test.

## 26. Errores de dominio
Como mínimo:
```text
CASE_ALREADY_EXISTS
DUPLICATE_NUE
DUPLICATE_SPECIES
DUPLICATE_DSM
INVALID_STORAGE_TOPOLOGY
```

## 27. Repositories
Extender repositories existentes.

Prohibido SQL directo en routes, templates o JavaScript.

Operaciones multi-tabla deben vivir en application service / unit of work.

## 28. Migraciones
Inspeccionar schema real R01.1.

Si faltan campos materiales, crear:
```text
migrations/0002_<descripcion>.sql
```

No editar `0001_initial_schema.sql` ya aplicado.

## 29. Constraints
Verificar/implementar:
```text
unique case.ruc
unique (case_id, nue_number)
unique (nue_id, species_number)
unique (species_id, dsm_number)
check storage_relation
```

## 30. Web read models
Las páginas deben mostrar:
```text
RUC
NUE
ESPECIE
DSM
```

No exponer ORM crudo.

## 31. CSRF
Como ahora habrá operaciones state-changing desde web, resolver la deuda de R02.1.

Implementar una protección real compatible con el stack.

No declarar CSRF resuelto si solo existe `SameSite`.

Agregar tests.

## 32. Tests obligatorios
Mantener los 66 tests y agregar como mínimo:

1. RUC válido sintético.
2. RUC vacío rechazado.
3. RUC path traversal rechazado.
4. NUE válida.
5. NUE duplicada rechazada.
6. múltiples NUE.
7. species correlativas.
8. species duplicate reject.
9. SELF_STORAGE crea DSM1.
10. SELF_STORAGE same_physical=true.
11. SELF_STORAGE con >1 DSM rechazado.
12. CONTAINED_STORAGE 1 DSM.
13. CONTAINED_STORAGE múltiples DSM.
14. CONTAINED_STORAGE 0 DSM rechazado.
15. DSM numbering por especie.
16. labels determinísticas.
17. draft no persiste.
18. create case persiste todo.
19. transaction rollback completo.
20. case.json creado en temp.
21. JSON válido.
22. schema_version correcto.
23. no metadata inventada.
24. escritura atómica.
25. reconciliation MATCH.
26. reconciliation missing.
27. reconciliation invalid JSON.
28. reconciliation mismatch.
29. duplicate RUC reject.
30. API draft.
31. API create.
32. API detail jerárquico.
33. web detail jerárquico.
34. audit events.
35. request_id propagado.
36. CSRF state-changing route.
37. PostgreSQL 5433.
38. app role.
39. no `casos/` real.
40. no PhysicalDrive.
41. no EWF.
42. no AXIOM.
43. no Ollama.
44. no OpenClaw.

## 33. Prueba funcional sintética
Crear únicamente en test root:

```text
RUC_TEST_R03

NUE: 777777

ESPECIE1:
CONTAINED_STORAGE
DSM1
DSM2

ESPECIE2:
SELF_STORAGE
DSM1
```

No crear E01.

## 34. Fuera de alcance
Prohibido:
- evidencia real;
- petitorio real;
- OCR;
- fotos reales;
- identificación automática;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- Ollama;
- OpenClaw;
- Portable;
- RAR;
- Word;
- acceso a `casos/` productivo.

## 35. Documentación
Crear:
```text
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
```

Documentar modelo, invariantes, SELF_STORAGE, CONTAINED_STORAGE, labels, estados, DB vs case.json, schema_version, reconciliación, errores, endpoints y limitaciones.

## 36. Criterio de aceptación
R03 queda COMPLETO si:
- baseline verde;
- dominio y Draft implementados;
- jerarquía completa;
- invariantes protegidas;
- PostgreSQL transaccional;
- case.json atómico;
- reconciliación básica;
- API create/draft/read;
- web jerárquica;
- auditoría;
- CSRF real para operaciones state-changing;
- ningún dato inventado;
- ningún acceso a evidencia;
- `casos/` real intacto;
- suite completa verde;
- documentación creada.

Estado:
```text
FORENSIC_DOMAIN_FOUNDATION_READY
```

## 37. Git
Antes de commit:
```text
pytest
git status
```

Confirmar ausencia de:
```text
.env
secrets
runtime data
test artifacts
casos/
fotos
petitorios
E01
```

Commit sugerido:
```text
Sprint R03: implementa dominio RUC NUE ESPECIE DSM y case.json
```

## 38. Reporte final obligatorio
```text
SPRINT R03:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
DOMAIN ARCHITECTURE:
...
RUC:
...
NUE:
...
SPECIES:
...
DSM:
...
SELF_STORAGE:
...
CONTAINED_STORAGE:
...
CASE STRUCTURE DRAFT:
...
DATABASE TRANSACTION:
...
MIGRATION:
...
CASE.JSON:
...
SCHEMA VERSION:
...
ATOMIC WRITE:
...
RECONCILIATION:
...
AUDIT:
...
WEB:
...
API:
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
FORENSIC_DOMAIN_FOUNDATION_READY / FORENSIC_DOMAIN_FOUNDATION_BLOCKED
```

## 39. Instrucción final
TRAE:
1. lee documentación vigente;
2. ejecuta baseline;
3. inspecciona schema real R01.1;
4. implementa dominio;
5. implementa CaseStructureDraft;
6. agrega migración solo si es necesaria;
7. implementa transacción;
8. implementa case.json atómico;
9. implementa reconciliación;
10. integra API/web;
11. resuelve CSRF;
12. agrega tests;
13. verifica que `casos/` productivo siga intacto;
14. ejecuta suite completa;
15. entrega reporte;
16. detente;
17. NO inicies R04.

Comienza ahora.
