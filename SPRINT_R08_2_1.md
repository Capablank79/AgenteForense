# SPRINT_R08_2_1 — Detección y Selección del Write-Blocker como Canal de Adquisición

## 1. Objetivo

Formalizar la selección de origen para escenarios con múltiples write-blockers y múltiples medios conectados simultáneamente.

Flujo objetivo:

```text
WRITE-BLOCKERS PRESENTES
→ DISPOSITIVOS DETECTADOS DETRÁS DE CADA BLOQUEADOR
→ MOSTRAR TOPOLOGÍA
→ OPERADOR SELECCIONA BLOQUEADOR / CANAL
→ RESOLVER DISPOSITIVO / PHYSICALDRIVE ASOCIADO
→ VINCULAR CON DSM
→ VALIDAR IsReadOnly / IsSystem / IsBoot
→ REVALIDAR
→ HUMAN GATE
→ ADQUISICIÓN
```

Este sprint NO debe ejecutar adquisición real hasta validar la topología write-blocker → medio → PhysicalDrive en hardware real.

Estado esperado:

```text
WRITE_BLOCKER_SOURCE_SELECTION_READY
```

o:

```text
WRITE_BLOCKER_TOPOLOGY_BLOCKED
```

## 2. Regla previa

Leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
SPRINT_R07.md
SPRINT_R07_1.md
SPRINT_R08.md
SPRINT_R08_1.md
SPRINT_R08_2.md
SPRINT_R08_2_1.md
DISK_BINDING_ARCHITECTURE.md
EWF_ACQUISITION_ARCHITECTURE.md
```

No inventar correlaciones entre blocker y PhysicalDrive.

## 3. Problema

El sistema actual ve el disco y sus flags, pero no representa de forma explícita:

```text
WRITE-BLOCKER A
    └── DISPOSITIVO A
        └── PhysicalDriveN

WRITE-BLOCKER B
    └── DISPOSITIVO B
        └── PhysicalDriveM
```

Con dos medios simultáneos, seleccionar solo `PhysicalDriveN` no entrega suficiente contexto operacional.

## 4. Regla de selección

La primera decisión humana debe ser:

```text
¿DESDE QUÉ BLOQUEADOR DESEA REALIZAR LA ADQUISICIÓN?
```

Después se resuelve el PhysicalDrive asociado.

## 5. Modelos

Diseñar `WriteBlockerChannel` con campos observables:

```text
blocker_id
display_name
operator_label
manufacturer
model
serial_number
device_instance_id
pnp_device_id
vid
pid
bus
location_path
os_visible
operator_confirmed_present
operator_confirmed_powered
observed_at
provenance
```

Diseñar `WriteBlockerAttachment`:

```text
blocker_id
disk_number
physical_drive
friendly_name
disk_serial
disk_unique_id
size_bytes
is_read_only
is_system
is_boot
relation_status
observed_at
provenance
```

Campos no observables = `null`.

## 6. Estado de relación

Valores:

```text
CONFIRMED
PROBABLE
UNRESOLVED
NOT_ATTACHED
```

Solo `CONFIRMED` permite resolver automáticamente el PhysicalDrive desde un blocker.

## 7. Investigación real

Con ambos write-blockers encendidos:

1. Estado A: ambos blockers encendidos, sin medios.
2. Estado B: pendrive A solo en blocker A.
3. Estado C: pendrive B solo en blocker B.
4. Estado D: ambos pendrives conectados simultáneamente.

Capturar inventario en cada estado y comparar deltas.

No ejecutar `ewfacquire`.

## 8. Fuentes Windows

Inspeccionar según disponibilidad:

```text
Get-PnpDevice -PresentOnly
Get-CimInstance Win32_PnPEntity
Get-CimInstance Win32_USBController
Get-CimInstance Win32_USBControllerDevice
Get-CimInstance Win32_DiskDrive
Get-CimInstance Win32_DiskDriveToDiskPartition
Get-Disk
Get-PhysicalDisk
```

Inspeccionar también, si existen:

```text
InstanceId
Parent
Children
LocationPaths
BusReportedDeviceDesc
HardwareIds
CompatibleIds
Manufacturer
Service
Class
ClassGuid
```

## 9. Topología PnP

Intentar reconstruir:

```text
WRITE-BLOCKER DEVICE NODE
→ CHILD / DOWNSTREAM DEVICE
→ USB STORAGE DEVICE
→ Win32_DiskDrive
→ Disk Number
→ PhysicalDriveN
```

Registrar exactamente qué propiedades permiten o no la relación.

## 10. Alias operacional

Si Windows no expone identidad suficiente, permitir aliases:

```text
BLOQUEADOR_1
BLOQUEADOR_2
```

pero registrarlos como `operator_label`, no como identidad técnica.

## 11. UX objetivo

```text
BLOQUEADORES DISPONIBLES

[1] BLOQUEADOR_1
    Dispositivo conectado:
        Generic Flash Disk
        Serial: ...
        Size: ...
        PhysicalDrive6
        ReadOnly: TRUE

[2] BLOQUEADOR_2
    Dispositivo conectado:
        Kingston DataTraveler
        Serial: ...
        Size: ...
        PhysicalDrive7
        ReadOnly: TRUE

¿DESDE QUÉ BLOQUEADOR DESEA REALIZAR LA ADQUISICIÓN?

> 1
```

Después:

```text
CANAL SELECCIONADO:
BLOQUEADOR_1

DISPOSITIVO:
Generic Flash Disk
PhysicalDrive6
ReadOnly=True
```

## 12. Reglas críticas

La selección del blocker NO reemplaza:

```text
IsReadOnly=True
IsSystem=False
IsBoot=False
```

Si el medio del blocker seleccionado reporta `IsReadOnly=False`:

```text
BLOCKED_NOT_READ_ONLY
```

Sin override.

## 13. DSM

Secuencia:

```text
CASE
→ NUE
→ ESPECIE
→ DSM
→ SELECCIONAR WRITE-BLOCKER
→ RESOLVER MEDIO
→ BIND DSM ↔ PHYSICALDRIVE
```

No adquirir sin DSM.

## 14. Casos ambiguos

Si un blocker presenta más de un downstream device:

```text
MULTIPLE_DOWNSTREAM_DEVICES
```

Si un disco read-only no puede vincularse a un blocker:

```text
WRITE_BLOCKER_RELATION_UNRESOLVED
```

No iniciar adquisición automáticamente.

## 15. Persistencia

Evaluar persistencia equivalente a:

```text
forensic.write_blockers
forensic.write_blocker_observations
forensic.write_blocker_attachments
```

No crear tablas hasta inspeccionar el esquema real y justificar migración.

Historial append-oriented.

## 16. acquisition.json / case.json

Persistir:

```text
selected_write_blocker
selected_dsm
selected_physical_drive
attachment_relation
technical_identity
operator_label
provenance
```

No reducirlo a `write_blocker=true`.

## 17. Auditoría

Eventos:

```text
WRITE_BLOCKER_SCAN_STARTED
WRITE_BLOCKER_OBSERVED
WRITE_BLOCKER_TOPOLOGY_OBSERVED
WRITE_BLOCKER_MEDIA_ATTACHED
WRITE_BLOCKER_MEDIA_DETACHED
WRITE_BLOCKER_SELECTION_REQUESTED
WRITE_BLOCKER_SELECTED
WRITE_BLOCKER_SOURCE_RESOLVED
WRITE_BLOCKER_SOURCE_UNRESOLVED
```

## 18. Human Gate futuro

Mostrar:

```text
WRITE-BLOCKER SELECCIONADO
ID:
Alias:
Manufacturer:
Model:
Serial:
VID/PID:
Location:
Relation status:

DISPOSITIVO DETRÁS DEL BLOQUEADOR
PhysicalDrive:
FriendlyName:
Serial:
Size:
ReadOnly:
System:
Boot:
```

## 19. API futura

Diseñar:

```text
GET  /api/system/write-blockers
GET  /api/system/write-blockers/{blocker_id}/media
POST /api/cases/{case_id}/dsms/{dsm_id}/write-blocker/select
GET  /api/cases/{case_id}/dsms/{dsm_id}/source-selection
```

Mutaciones con CSRF.

## 20. Tests mínimos

Cubrir:

1. 0 blockers.
2. 1 blocker sin medio.
3. 1 blocker + 1 medio.
4. 2 blockers + 1 medio cada uno.
5. ambos medios read-only.
6. blocker A seleccionado → PhysicalDrive A.
7. blocker B seleccionado → PhysicalDrive B.
8. no cross-assignment.
9. reconnect cambia PhysicalDrive pero mantiene identidad verificable.
10. blocker sin identidad OS.
11. alias operador.
12. metadata parcial.
13. multiple downstream devices.
14. unresolved topology.
15. selected blocker + IsReadOnly false bloquea.
16. system disk bloquea.
17. boot disk bloquea.
18. DSM requerido.
19. selection audit.
20. case.json persistence.
21. acquisition.json persistence.
22. no ewfacquire durante investigación.
23. no raw PhysicalDrive open.
24. suite completa verde.

## 21. Criterio de aceptación

Debe demostrarse en hardware real:

```text
BLOQUEADOR_A → PENDRIVE_A → PhysicalDriveN
BLOQUEADOR_B → PENDRIVE_B → PhysicalDriveM
```

con provenance reproducible.

Si Windows no expone suficiente topología:

```text
WRITE_BLOCKER_TOPOLOGY_BLOCKED
```

y se diseña un mecanismo de selección asistida explícita sin inventar relación.

## 22. Reporte obligatorio

```text
SPRINT R08.2.1:
COMPLETADO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...

WRITE BLOCKERS PHYSICAL:
Count:
...

STATE A - BLOCKERS, NO MEDIA:
...

STATE B - MEDIA A ON BLOCKER A:
...

STATE C - MEDIA B ON BLOCKER B:
...

STATE D - BOTH MEDIA:
...

BLOCKER A:
Operator label:
OS identity:
Manufacturer:
Model:
Serial:
VID:
PID:
Location:
Downstream medium:
PhysicalDrive:
Relation:
Provenance:

BLOCKER B:
Operator label:
OS identity:
Manufacturer:
Model:
Serial:
VID:
PID:
Location:
Downstream medium:
PhysicalDrive:
Relation:
Provenance:

TOPOLOGY METHOD:
...

CORRELATION RELIABLE:
YES / NO

UNRESOLVED FIELDS:
...

UX DESIGN:
...

DATABASE DESIGN:
...

API DESIGN:
...

AUDIT DESIGN:
...

EWFACQUIRE EXECUTED:
NO

PHYSICALDRIVE RAW OPENED:
NO

SET-DISK:
NO

DISKPART:
NO

TESTS FINAL:
...

STATUS:
WRITE_BLOCKER_SOURCE_SELECTION_READY / WRITE_BLOCKER_TOPOLOGY_BLOCKED
```

## 23. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. no ejecutes adquisición;
4. identifica ambos write-blockers;
5. realiza Estados A/B/C/D;
6. inspecciona topología PnP;
7. correlaciona blocker → medio → PhysicalDrive;
8. no inventes propiedades;
9. diseña selector por blocker;
10. persiste provenance;
11. agrega tests si corresponde;
12. entrega reporte;
13. detente;
14. NO repitas R08.2 todavía;
15. NO inicies R09.

Comienza ahora.
