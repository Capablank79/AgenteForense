# CONTINUACION_R08_2_1_REV2 — Integración de Topología de Write-Blockers en Plataforma Operativa Localhost

## Estado de partida

Se acepta como validada la topología real observada:

```text
BLOQUEADOR_1
Tableau T34589is
→ \\.\PhysicalDrive7
→ IsReadOnly=True

BLOQUEADOR_2
USB Write Blocker
→ \\.\PhysicalDrive6
→ IsReadOnly=True
```

Correlación:

```text
CONFIRMED
```

Método:

```text
WINDOWS_PNP_CIM_INSPECTION
```

Baseline:

```text
227 passed
```

No repetir la investigación A/B/C/D salvo que cambie hardware.

---

## 1. Objetivo inmediato

Continuar `SPRINT_R08_2_1_REV2.md` desde la fase de implementación de plataforma.

El objetivo es que:

```text
http://127.0.0.1:8085
```

sea la consola operacional principal y muestre/persista la topología:

```text
BLOQUEADOR
→ MEDIO
→ PhysicalDrive
→ DSM
→ BINDING
→ ADQUISICIÓN
```

No ejecutar todavía adquisición real.

---

## 2. Persistencia PostgreSQL

Inspeccionar migraciones reales existentes.

Agregar migración nueva solo si es necesaria para representar:

```text
write_blockers
write_blocker_observations
write_blocker_attachments
write_blocker_selections
```

o estructura equivalente normalizada.

Requisitos:

- append-oriented para observaciones e historial;
- no sobrescribir historia;
- `ON DELETE RESTRICT`;
- timestamps;
- provenance;
- relation_status;
- operator_label separado de identidad técnica.

Registrar como mínimo:

```text
blocker_id
operator_label
manufacturer
model
serial_number
bus
pnp_device_id
device_instance_id
vid
pid
location_path
os_visible
observed_at
provenance
```

Attachment:

```text
blocker_id
disk_number
physical_drive
disk_friendly_name
disk_serial
disk_unique_id
size_bytes
is_read_only
is_system
is_boot
relation_status
observed_at
```

Selection:

```text
case_id
dsm_id
blocker_id
attachment_id
physical_drive
selected_at
operator
status
```

---

## 3. Página HARDWARE

Implementar/actualizar:

```text
GET /hardware
```

Mostrar dos tarjetas reales:

```text
BLOQUEADOR_1
Tableau T34589is
Bus: IEEE 1394 / SBP2
PhysicalDrive7
ReadOnly: YES

BLOQUEADOR_2
USB Write Blocker
Bus: USB
PhysicalDrive6
ReadOnly: YES
```

Cada tarjeta debe mostrar el medio actualmente conectado.

Botón:

```text
ACTUALIZAR HARDWARE
```

debe:

```text
scan
→ persist observation
→ rebuild topology
→ refresh UI
```

No modificar hardware.

---

## 4. Selección desde DSM

En detalle de caso / DSM agregar:

```text
SELECCIONAR BLOQUEADOR DE ADQUISICIÓN
```

Mostrar únicamente canales disponibles con relación:

```text
CONFIRMED
```

y medio válido.

Ejemplo:

```text
[ ] BLOQUEADOR_1 — Tableau T34589is — PhysicalDrive7 — ReadOnly
[ ] BLOQUEADOR_2 — USB Write Blocker — PhysicalDrive6 — ReadOnly
```

El operador selecciona el bloqueador, no el PhysicalDrive directamente.

---

## 5. Resolución automática controlada

Después de seleccionar blocker:

```text
blocker_id
→ current confirmed attachment
→ physical_drive
```

Luego ejecutar las validaciones R07.1:

```text
IsReadOnly=True
IsSystem=False
IsBoot=False
binding current
```

No permitir cross-assignment.

---

## 6. Binding DSM

La UI debe mostrar:

```text
DSM-LAB-001
Selected blocker: BLOQUEADOR_2
Resolved source: \\.\PhysicalDrive6
Binding: CONFIRMED
```

Persistir en PostgreSQL.

Actualizar `case.json` atómicamente con referencia a:

```text
selected_write_blocker
selected_physical_drive
binding_id
```

---

## 7. Dashboard

Actualizar `/` para mostrar:

```text
Write-blockers detected: 2
Read-only media: 2
Active bindings: ...
Acquisition jobs: ...
Warnings: ...
```

---

## 8. Nueva Adquisición

La pantalla debe guiar:

```text
CASO
→ NUE
→ ESPECIE
→ DSM
→ WRITE-BLOCKER
→ MEDIO
→ BINDING
→ DESTINO
→ PREFLIGHT
→ HUMAN GATE
```

No depender del terminal.

---

## 9. Human Gate Web

El resumen debe incluir:

```text
WRITE-BLOCKER
Alias:
Manufacturer:
Model:
Serial:
Bus:
Relation:

MEDIO
PhysicalDrive:
FriendlyName:
Serial:
Size:
ReadOnly:
System:
Boot:

DSM
...
```

El operador debe escribir:

```text
ADQUIRIR
```

pero durante esta continuación NO ejecutar `ewfacquire` real.

Validar únicamente que el gate y la preparación funcionan.

---

## 10. Página ADQUISICIONES

Implementar/validar:

```text
/acquisitions
```

Mostrar jobs persistidos:

```text
job_id
case
DSM
blocker
physical_drive
status
PID
started_at
exit_code
```

---

## 11. Página AUDITORÍA

Mostrar y filtrar:

```text
WRITE_BLOCKER_OBSERVED
WRITE_BLOCKER_TOPOLOGY_OBSERVED
WRITE_BLOCKER_SELECTED
WRITE_BLOCKER_SOURCE_RESOLVED
BINDING_PROPOSED
BINDING_CONFIRMED
ACQUISITION_PREPARED
HUMAN_GATE_DISPLAYED
```

Filtros:

```text
case
DSM
blocker
job
event
date
result
```

---

## 12. Página SISTEMA

Mostrar:

```text
Web status
Git commit
Python
PostgreSQL
schema version
admin privilege
ewfacquire path/version/hash
write-blockers detected
last hardware scan
```

---

## 13. Persistencia y recuperación

Prueba obligatoria:

1. seleccionar blocker para un DSM;
2. cerrar navegador;
3. volver a abrir;
4. confirmar que la selección sigue visible;
5. reiniciar aplicación web;
6. confirmar reconstrucción desde PostgreSQL.

La UI no es fuente de verdad.

---

## 14. API

Implementar o completar:

```text
GET  /api/system/write-blockers
POST /api/system/write-blockers/scan
GET  /api/system/write-blockers/{blocker_id}/media
POST /api/cases/{case_id}/dsms/{dsm_id}/write-blocker/select
GET  /api/cases/{case_id}/dsms/{dsm_id}/source-selection
```

Mutaciones con CSRF.

---

## 15. Tests mínimos nuevos

Mantener 227 tests.

Agregar cobertura para:

1. 2 blockers persistidos.
2. blocker A muestra PhysicalDrive7.
3. blocker B muestra PhysicalDrive6.
4. no cross-assignment.
5. selección blocker A.
6. selección blocker B.
7. selección persistida.
8. selección recuperada tras restart.
9. case.json sync.
10. audit selection.
11. hardware page.
12. hardware refresh.
13. case detail selection.
14. dashboard blocker counters.
15. acquisitions page.
16. audit filters.
17. system page.
18. Human Gate includes blocker.
19. CSRF scan/select.
20. unresolved relation blocks.
21. IsReadOnly false blocks.
22. system/boot blocks.
23. no ewfacquire real.
24. no raw PhysicalDrive open.
25. full regression.

---

## 16. Smoke test real localhost

Levantar:

```text
127.0.0.1:8085
```

Validar manualmente:

```text
/
 /cases
 /hardware
 /acquisitions
 /audit
 /system
```

Registrar:

```text
HTTP status
contenido visible
acciones principales
errores
```

---

## 17. Criterio de cierre

No declarar REV2 completa hasta que desde navegador se pueda:

- ver los 2 blockers;
- ver sus medios/PhysicalDrive;
- abrir caso;
- abrir DSM;
- seleccionar blocker;
- persistir selección;
- ver binding;
- ver readiness;
- ver audit;
- cerrar/reabrir navegador y conservar estado.

Estado esperado:

```text
LOCALHOST_OPERATIONAL_PLATFORM_READY
```

---

## 18. Reporte final

```text
SPRINT R08.2.1 REV2:
COMPLETADO / INCOMPLETO / BLOCKED

TOPOLOGY INVESTIGATION:
ACCEPTED

BASELINE:
...

TESTS BEFORE:
...

POSTGRESQL:
Tables added:
Tables reused:
Migration:

LOCALHOST:
URL:
Status:

DASHBOARD:
...

CASES:
...

CASE DETAIL:
...

HARDWARE:
Blocker 1:
Blocker 2:

BLOCKER SELECTION:
...

DSM BINDING:
...

PERSISTENCE:
...

CASE.JSON:
...

ACQUISITIONS:
...

HUMAN GATE WEB:
...

AUDIT:
...

SYSTEM:
...

BROWSER REOPEN RECOVERY:
...

APP RESTART RECOVERY:
...

CSRF:
...

SMOKE TEST:
...

TESTS ADDED:
...

TESTS FINAL:
...

EWFACQUIRE REAL:
NO

PHYSICALDRIVE RAW OPEN:
NO

EWFVERIFY:
NO

STATUS:
LOCALHOST_OPERATIONAL_PLATFORM_READY / LOCALHOST_OPERATIONAL_PLATFORM_BLOCKED
```

No iniciar R09.

No ejecutar adquisición real todavía.
