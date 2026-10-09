# SPRINT_R07_1 — Implementación del Vínculo Seguro DSM ↔ PhysicalDrive

## 1. Objetivo

Implementar el módulo productivo que vincula un DSM lógico con un disco físico Windows de forma segura, auditable y revalidable.

```text
CASO
→ NUE
→ ESPECIE
→ DSM
→ SCAN DISCOS
→ CLASIFICAR CANDIDATOS
→ COMPARAR DSM ↔ DISCO
→ PROPONER BINDING
→ CONFIRMACIÓN HUMANA
→ PERSISTIR BINDING
→ REVALIDAR
→ ACQUISITION_READY
```

Este sprint NO ejecuta adquisición. NO ejecutar `ewfacquire`, `ewfverify` ni abrir `\\.\PhysicalDriveN`.

Estado esperado:

```text
DISK_BINDING_READY
```

## 2. Documentación obligatoria

Leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R03.md
SPRINT_R04.md
SPRINT_R05_1.md
SPRINT_R06.md
SPRINT_R06_1.md
SPRINT_R07.md
SPRINT_R07_1.md
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
PHOTO_IDENTIFICATION_ARCHITECTURE.md
IDENTIFICATION_JSON_SCHEMA.md
DISK_BINDING_CAPABILITIES.md
```

## 3. Baseline

Esperado:

```text
Python: 3.10.11
Windows: Windows 10 Pro build 19045
PowerShell: 5.1.19041.6456
Storage Module: 2.0.0.0
PostgreSQL: 18.6
Tests: 203 passed
Identification: PHOTO_IDENTIFICATION_READY
Disk capabilities: DISK_BINDING_CAPABILITIES_VERIFIED
```

Ejecutar baseline completo antes de modificar.

## 4. Reglas críticas

Candidato únicamente si:

```text
IsReadOnly == True
IsSystem   == False
IsBoot     == False
```

Sin override manual ni software.

## 5. Prohibiciones

No ejecutar:

```text
Set-Disk
Set-Partition
DiskPart
Initialize-Disk
Clear-Disk
Format-Volume
Repair-Volume
CHKDSK /F
CHKDSK /R
```

No abrir `\\.\PhysicalDriveN`, no leer sectores, no cambiar online/offline.

## 6. Paquete hardware

Crear equivalente a:

```text
src/agente_forense/hardware/
    __init__.py
    disks.py
    models.py
    errors.py
    matching.py
    bindings.py
    revalidation.py
    service.py
```

## 7. DiskSnapshot

Implementar modelo inmutable con:

```text
disk_number
physical_drive
friendly_name
serial_number
unique_id
path
size_bytes
bus_type
partition_style
is_read_only
is_system
is_boot
is_offline
operational_status
health_status
pnp_device_id
observed_at
source
```

Campos ausentes = `None`.

## 8. Scanner real

Usar exactamente:

```text
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
-NoProfile
```

con `Get-Disk` y salida JSON estructurada.

Usar `subprocess.run`, `shell=False`, `capture_output=True`, timeout configurable.

## 9. Encoding

Soportar salida observada en R07:

```text
windows-1252 / Unicode escapes
```

Agregar tests con caracteres Unicode.

## 10. Get-Disk

Obtener:

```text
Number
FriendlyName
SerialNumber
UniqueId
Path
Size
BusType
PartitionStyle
IsReadOnly
IsSystem
IsBoot
IsOffline
OperationalStatus
HealthStatus
```

## 11. Cross-check Win32_DiskDrive

Verificar:

```text
Get-Disk.Number N
↔ Win32_DiskDrive.Index N
↔ DeviceID \\.\PHYSICALDRIVEN
```

Si no puede verificarse:

```text
UNSUPPORTED_DISK_REPRESENTATION
```

## 12. Dynamic disks

Aplicar fail-closed ante representación LDM/dynamic no segura.

## 13. Clasificación

Implementar:

```text
FORENSIC_CANDIDATE
BLOCKED_NOT_READ_ONLY
BLOCKED_SYSTEM_DISK
BLOCKED_BOOT_DISK
BLOCKED_MULTIPLE_REASONS
UNSUPPORTED_DISK_REPRESENTATION
```

Unknown/null crítico = bloqueado.

## 14. DSM primero

Toda operación requiere `case_id` y `dsm_id`.

No permitir binding sin DSM lógico seleccionado.

## 15. Matching DSM ↔ Disk

Estados:

```text
MATCH
COMPATIBLE
CONFLICT
INSUFFICIENT_DATA
NOT_COMPARABLE
```

Comparar solo campos realmente disponibles.

### Serial
Trim y normalización segura; nunca completar ni truncar.

### Modelo
No usar `FriendlyName` como modelo automáticamente.

### Capacidad
Separar capacidad nominal de bytes exactos; tolerancia explícita y documentada.

## 16. Binding nunca automático

Siempre:

```text
PROPOSED_BINDING
→ HUMAN_CONFIRMATION
→ CONFIRMED_BINDING
```

Múltiples candidatos:

```text
MULTIPLE_CANDIDATES
```

## 17. Human Gate

Mostrar:

```text
CASE / NUE / SPECIES / DSM
Disk Number
PhysicalDrive
FriendlyName
Serial
UniqueId
Size
BusType
IsReadOnly
IsSystem
IsBoot
IsOffline
Matching
Warnings
```

Acción explícita:

```text
CONFIRM_DISK_BINDING
```

## 18. Persistencia

Crear migración nueva:

```text
forensic.dsm_disk_bindings
```

No editar migraciones antiguas.

Diseño mínimo:

```text
id UUID PK
case_id UUID FK
dsm_id UUID FK
disk_number INTEGER
physical_drive VARCHAR
serial_number VARCHAR NULL
unique_id TEXT NULL
friendly_name TEXT NULL
size_bytes BIGINT
bus_type VARCHAR NULL
is_read_only BOOLEAN
is_system BOOLEAN
is_boot BOOLEAN
is_offline BOOLEAN NULL
observed_at TIMESTAMPTZ
confirmed_at TIMESTAMPTZ NULL
status VARCHAR
snapshot_json JSONB
request_id UUID NULL
created_at TIMESTAMPTZ
```

`ON DELETE RESTRICT`.

## 19. Historial append-oriented

Estados:

```text
PROPOSED
CONFIRMED
INVALIDATED
REJECTED
```

No sobreescribir historial. Un solo binding `CONFIRMED` activo por DSM.

## 20. Rebinding

```text
invalidate old
audit
create new proposed
human confirm
```

## 21. Revalidación

Reconsultar antes de adquisición futura y comparar:

```text
disk_number
physical_drive
serial_number cuando exista
unique_id cuando exista
size_bytes
is_read_only
is_system
is_boot
```

Cambio crítico:

```text
SOURCE_CHANGED
```

y bloquear.

## 22. Policy Engine

Agregar:

```text
DSM_SELECTED
PHYSICAL_DRIVE_DETECTED
SOURCE_READ_ONLY
SOURCE_NOT_SYSTEM
SOURCE_NOT_BOOT
DISK_BINDING_CONFIRMED
DISK_BINDING_CURRENT
```

Todas críticas.

## 23. State Machine

Permitir:

```text
IDENTIFICATION_COMPLETED
→ ACQUISITION_READY
```

solo si todas las policies críticas permiten.

R07.1 NO puede marcar `ACQUIRING`.

## 24. Audit events

Registrar:

```text
DISK_SCAN_STARTED
DISK_SCAN_COMPLETED
DISK_CANDIDATE_CLASSIFIED
DSM_DISK_COMPARISON
DISK_BINDING_PROPOSED
DISK_BINDING_CONFIRMATION_REQUESTED
DISK_BINDING_CONFIRMED
DISK_BINDING_REJECTED
DISK_BINDING_REVALIDATED
DISK_BINDING_INVALIDATED
```

## 25. case.json

Sincronizar resumen del binding y estado de revalidación con escritura atómica.

No describir PostgreSQL + `case.json` como una sola transacción ACID.

## 26. API/Web

Implementar:

```text
GET  /api/system/disks
GET  /api/cases/{case_id}/dsms/{dsm_id}/disk-candidates
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/propose
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/confirm
GET  /api/cases/{case_id}/dsms/{dsm_id}/disk-binding
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/revalidate
```

Mutaciones con CSRF.

UI: Caso → DSM → Vincular disco. Mostrar discos bloqueados y motivo.

## 27. Error model

Implementar errores equivalentes a:

```text
PowerShellUnavailableError
StorageModuleUnavailableError
DiskScanTimeoutError
DiskScanParseError
DiskNotFoundError
DiskNotReadOnlyError
SystemDiskBlockedError
BootDiskBlockedError
UnsupportedDiskRepresentationError
DiskIdentityConflictError
MultipleCandidatesError
DiskBindingNotConfirmedError
SourceChangedError
```

## 28. Validación real segura

R07 no observó candidato real read-only.

En R07.1:

- ejecutar scan real;
- confirmar que discos `IsReadOnly=False` quedan `BLOCKED_NOT_READ_ONLY`;
- no confirmar binding sobre ellos;
- probar candidato read-only con fixture/mock.

No inventar candidato real.

## 29. Tests obligatorios

Mantener 203 tests y agregar cobertura de:

```text
PowerShell exacto
shell=False
timeout
encoding
JSON parse
Number↔PhysicalDrive
critical null
read-only true/false
system/boot block
unsupported representation
DSM required
serial/model/capacity matching
multiple candidates
human confirmation
persistence/history
rebind
revalidation
SOURCE_CHANGED
case.json
audit
policies
ACQUISITION_READY
API/Web/CSRF
no Set-Disk
no DiskPart
no PhysicalDrive open
no sector read
no ewfacquire
no ewfverify
no AXIOM
no Ollama
casos/ intacto
```

## 30. Functional smoke test

```text
real disk scan
→ current disks blocked if IsReadOnly=False
```

y con fixture:

```text
synthetic read-only disk
→ candidate
→ proposed
→ confirmed
→ revalidated
→ ACQUISITION_READY
```

Sin adquisición.

## 31. Documentación

Crear:

```text
DISK_BINDING_ARCHITECTURE.md
DISK_BINDING_SCHEMA.md
```

## 32. Criterio de aceptación

R07.1 queda completo si:

- baseline verde;
- scanner real;
- parser robusto;
- policy exacta;
- DSM obligatorio;
- matching;
- binding humano;
- historial append-oriented;
- revalidation;
- SOURCE_CHANGED fail-closed;
- Policy Engine;
- ACQUISITION_READY;
- API/Web/CSRF;
- case.json;
- audit;
- discos reales no read-only bloqueados;
- no PhysicalDrive abierto;
- no adquisición;
- suite completa verde.

Estado:

```text
DISK_BINDING_READY
```

o:

```text
DISK_BINDING_BLOCKED
```

## 33. Reporte final obligatorio

```text
SPRINT R07.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
HARDWARE MODULE:
...
POWERSHELL:
...
STORAGE MODULE:
...
DISK SCANNER:
...
ENCODING:
...
TIMEOUT:
...
DISK SNAPSHOT:
...
NUMBER ↔ PHYSICALDRIVE:
...
FORENSIC CANDIDATE:
...
REAL DISKS:
...
REAL READ-ONLY CANDIDATE:
YES / NO
DSM REQUIREMENT:
...
MATCHING:
...
SERIAL:
...
MODEL:
...
CAPACITY:
...
MULTIPLE CANDIDATES:
...
HUMAN GATE:
...
BINDING:
...
REBINDING:
...
REVALIDATION:
...
SOURCE_CHANGED:
...
DATABASE:
...
MIGRATION:
...
CASE.JSON:
...
POLICY ENGINE:
...
STATE MACHINE:
...
ACQUISITION_READY:
...
API:
...
WEB:
...
CSRF:
...
AUDIT:
...
FILES CREATED:
...
FILES MODIFIED:
...
TESTS ADDED:
...
TESTS FINAL:
...
FUNCTIONAL REAL SCAN:
...
FUNCTIONAL FIXTURE BINDING:
...
POSTGRESQL MODIFIED:
YES / NO
CASOS/ MODIFIED:
NO
PHYSICALDRIVE OPENED:
NO
SECTORS READ:
NO
DISK ATTRIBUTES MODIFIED:
NO
SET-DISK:
NO
DISKPART:
NO
EWFACQUIRE:
NO
EWFVERIFY:
NO
AXIOM:
NO
OLLAMA:
NO
OPENCLAW:
NO
RISKS:
...
BLOCKERS:
...
STATUS:
DISK_BINDING_READY / DISK_BINDING_BLOCKED
```

## 34. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. crea hardware package;
4. implementa scanner PowerShell read-only;
5. implementa parser y correlación PhysicalDrive;
6. implementa classification;
7. implementa matching DSM↔Disk;
8. crea migración `dsm_disk_bindings`;
9. implementa proposed/confirmed/invalidation;
10. implementa revalidation;
11. integra audit;
12. integra Policy Engine;
13. integra State Machine hasta `ACQUISITION_READY`;
14. integra API/Web/CSRF;
15. ejecuta scan real seguro;
16. prueba binding solo con fixture read-only si no existe candidato real;
17. ejecuta suite completa;
18. crea documentación;
19. entrega reporte;
20. detente;
21. NO inicies R08.

Comienza ahora.
