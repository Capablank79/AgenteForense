# SPRINT_R07 — Investigación y Validación del Vínculo Seguro DSM ↔ PhysicalDrive

## 1. Objetivo

Investigar y validar, sobre el entorno REAL del equipo, cómo debe implementarse el vínculo seguro entre un DSM lógico del modelo forense y un disco físico Windows.

Flujo objetivo futuro:

```text
CASO → NUE → ESPECIE → DSM
→ DETECCIÓN DE DISCOS WINDOWS
→ CLASIFICACIÓN FORENSE
→ SELECCIÓN HUMANA DEL CANDIDATO
→ VALIDACIÓN DE IDENTIDAD
→ VÍNCULO DSM ↔ PhysicalDrive
→ REVALIDACIÓN
→ ACQUISITION_READY
```

Este sprint es de INVESTIGACIÓN, VALIDACIÓN LOCAL y DISEÑO.

No ejecuta adquisición E01, no ejecuta `ewfacquire`, no abre `\\.\PhysicalDriveN` y no modifica atributos de ningún disco.

Estado esperado:

```text
DISK_BINDING_CAPABILITIES_VERIFIED
```

o:

```text
DISK_BINDING_BLOCKED
```

## 2. Regla previa

Antes de cualquier cambio, leer completos:

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
FORENSIC_DOMAIN_ARCHITECTURE.md
CASE_JSON_SCHEMA.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
PHOTO_IDENTIFICATION_ARCHITECTURE.md
IDENTIFICATION_JSON_SCHEMA.md
```

Revisar además reportes reales R03–R06.1.

Los sprints históricos pueden usarse solo como referencia.

## 3. Baseline

Esperado:

```text
Python 3.10.11
Windows 10 Pro build 19045
PostgreSQL 18.6
Web 127.0.0.1:8085
203 passed
PHOTO_IDENTIFICATION_READY
```

Ejecutar:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe -m pytest
```

Si hay regresión, detener y documentar.

## 4. Regla forense permanente

Un disco solo puede ser candidato si Windows reporta:

```text
IsReadOnly = True
IsSystem   = False
IsBoot     = False
```

Regla absoluta:

```text
SIN READ-ONLY = NO HAY CANDIDATO
```

No existe override humano ni software.

## 5. Prohibiciones absolutas

R07 NO debe ejecutar:

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

ni equivalentes capaces de modificar el origen.

El agente observa; no corrige ni cambia atributos.

## 6. Fuentes Windows a investigar

Investigar localmente:

```text
Get-Disk
Get-PhysicalDisk
Get-CimInstance Win32_DiskDrive
Get-CimInstance Win32_DiskPartition
Get-CimInstance Win32_LogicalDisk
```

No asumir que son intercambiables.

## 7. Get-Disk

Microsoft define `Get-Disk` como mecanismo para obtener discos visibles al sistema operativo.

Ejecutar y observar:

```powershell
Get-Disk |
Select-Object `
    Number,
    FriendlyName,
    SerialNumber,
    UniqueId,
    Path,
    Size,
    BusType,
    PartitionStyle,
    IsReadOnly,
    IsSystem,
    IsBoot,
    IsOffline,
    OperationalStatus,
    HealthStatus
```

Registrar salida real anonimizada cuando corresponda.

## 8. Limitación de Get-Disk

Microsoft documenta que ciertos discos dinámicos pueden no ser devueltos por `Get-Disk`.

Por lo tanto:

```text
NOT_RETURNED_BY_GET_DISK
```

no significa automáticamente:

```text
DISK_DOES_NOT_EXIST
```

Ante representación insegura, aplicar fail-closed.

## 9. PowerShell real

Registrar:

```powershell
$PSVersionTable
```

y ejecutable real:

```text
powershell.exe
pwsh.exe
```

si existe.

No asumir versión.

## 10. Storage Module

Registrar:

```powershell
Get-Module Storage -ListAvailable |
Select-Object Name, Version, Path
```

No actualizar módulos.

## 11. Get-Command y ayuda

Registrar:

```powershell
Get-Command Get-Disk
Get-Command Get-PhysicalDisk
Get-Help Get-Disk -Full
Get-Help Get-PhysicalDisk -Full
```

No ejecutar `Update-Help`.

## 12. SerialNumber y UniqueId

Investigar:

```text
present
empty
null
trailing spaces
different representation across APIs
```

No usar serial como identificador universal si está ausente.

Investigar también `UniqueId` sin asumir que siempre existe.

## 13. Disk Number ↔ PhysicalDrive

Verificar localmente:

```text
Get-Disk Number = N
```

contra:

```powershell
Get-CimInstance Win32_DiskDrive |
Select-Object Index, DeviceID, Model, SerialNumber, Size, InterfaceType, PNPDeviceID
```

Objetivo:

```text
Index N ↔ DeviceID \\.\PHYSICALDRIVEN
```

Debe observarse antes de formalizarlo.

## 14. No abrir PhysicalDrive

En R07 queda prohibido:

```text
open("\\.\PhysicalDriveN")
```

en lectura o escritura.

Solo metadata del sistema operativo.

## 15. DiskSnapshot

Diseñar modelo:

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

Campos ausentes = `null`.

## 16. Provenance por campo

Registrar:

```text
field
value
source_command
source_property
observed_at
```

Especialmente para:

```text
IsReadOnly
IsSystem
IsBoot
SerialNumber
Size
```

## 17. Clasificación forense

Estados:

```text
FORENSIC_CANDIDATE
BLOCKED_NOT_READ_ONLY
BLOCKED_SYSTEM_DISK
BLOCKED_BOOT_DISK
BLOCKED_MULTIPLE_REASONS
UNSUPPORTED_DISK_REPRESENTATION
```

Solo `FORENSIC_CANDIDATE` cuando:

```text
is_read_only is True
and is_system is False
and is_boot is False
```

Valores unknown/null/parse failure bloquean.

## 18. IsOffline, OperationalStatus y HealthStatus

Investigar valores reales.

No cambiar online/offline.

No convertir HealthStatus automáticamente en criterio de elegibilidad sin justificación.

## 19. BusType

Registrar valores reales observados.

No bloquear por bus sin riesgo demostrado.

## 20. Selección lógica DSM primero

El flujo futuro debe comenzar con un DSM lógico, nunca con PhysicalDrive.

Ejemplo:

```text
RUC
└── NUE_777777
    └── ESPECIE1
        └── DSM1
```

Luego se busca/selecciona el disco físico.

## 21. Datos DSM reales

Inspeccionar `forensic.dsms` / `DsmModel`.

Verificar campos realmente disponibles y confirmados, incluyendo cuando existan:

```text
device_type
brand
model
serial
capacity_bytes
same_physical_object_as_species
```

No asumir valores.

## 22. Matching DSM ↔ Disk

Diseñar motor de comparación, no binding automático.

Resultados:

```text
MATCH
COMPATIBLE
CONFLICT
INSUFFICIENT_DATA
NOT_COMPARABLE
```

### Serial
Si ambos existen y están confirmados:

```text
exact normalized match → MATCH
different → CONFLICT
```

No completar ni truncar serial.

### Modelo
No derivar modelo desde FriendlyName salvo regla explícita observada.

### Capacidad
Distinguir capacidad nominal comercial vs bytes exactos del sistema operativo.

No fijar tolerancia sin evidencia real.

## 23. Binding nunca automático

Aunque haya alta compatibilidad:

```text
PROPOSED_BINDING
→ HUMAN_CONFIRMATION
→ CONFIRMED_BINDING
```

Si hay múltiples candidatos:

```text
MULTIPLE_CANDIDATES
```

y bloquear resolución automática.

## 24. Ausencia de serial

No es fallo automático.

Usar:

```text
INSUFFICIENT_DATA
```

y mostrar otros datos.

Selección humana sigue siendo obligatoria.

## 25. Persistencia futura

Diseñar:

```text
binding_id
case_id
dsm_id
disk_number
physical_drive
serial_number
unique_id
size_bytes
bus_type
is_read_only
is_system
is_boot
observed_at
confirmed_at
operator
request_id
snapshot_json
status
```

No crear tabla todavía.

Evaluar:

```text
A) columnas en forensic.dsms
B) tabla append-oriented dsm_disk_bindings
```

Preferir separar identidad lógica DSM de observaciones físicas temporales si la evidencia del diseño lo respalda.

## 26. Rebinding y revalidación

No sobrescribir binding confirmado.

Un cambio debe crear historial/auditoría.

Antes de adquisición futura, revalidar:

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

Si cambia dato crítico:

```text
SOURCE_CHANGED
```

y bloquear.

`Disk Number` no debe tratarse como identidad permanente.

## 27. PhysicalDrive no es letra de unidad

La fuente futura será:

```text
\\.\PhysicalDriveN
```

Nunca:

```text
E:\
F:\
G:\
```

## 28. Bloqueador de escritura

El software solo puede afirmar:

```text
Windows reports IsReadOnly=True
```

No afirmar automáticamente certificación o garantía del bloqueador físico.

## 29. Privilegios

Investigar qué consultas funcionan como usuario actual y cuáles requieren elevación.

No elevar privilegios automáticamente.

## 30. Parser PowerShell

Preferir salida estructurada:

```powershell
... | ConvertTo-Json -Depth 4 -Compress
```

No parsear `Format-Table`.

Verificar encoding real y latencia real.

Diseñar futura ejecución con:

```text
subprocess.run
shell=False
timeout
capture_output=True
text=True
explicit executable
```

## 31. Errores

Diseñar códigos:

```text
POWERSHELL_NOT_FOUND
STORAGE_MODULE_UNAVAILABLE
GET_DISK_FAILED
GET_DISK_TIMEOUT
GET_DISK_PARSE_ERROR
NO_DISKS_RETURNED
DISK_METADATA_INCOMPLETE
DISK_NOT_READ_ONLY
DISK_IS_SYSTEM
DISK_IS_BOOT
DISK_IDENTITY_CONFLICT
MULTIPLE_CANDIDATES
SOURCE_CHANGED
```

## 32. Policy Engine futuro

Preparar:

```text
DSM_SELECTED
PHYSICAL_DRIVE_DETECTED
SOURCE_READ_ONLY
SOURCE_NOT_SYSTEM
SOURCE_NOT_BOOT
DISK_BINDING_CONFIRMED
DISK_BINDING_CURRENT
```

## 33. State Machine

R07 no avanza realmente a adquisición.

Diseñar futura condición:

```text
IDENTIFICATION_COMPLETED
→ ACQUISITION_READY
```

solo con DSM válido, binding confirmado y policies críticas ALLOW.

No marcar `ACQUIRING`.

## 34. Human Gate

Diseñar resumen:

```text
CASO
NUE
ESPECIE
DSM
Disk Number
PhysicalDrive
FriendlyName
Serial
Size
BusType
IsReadOnly
IsSystem
IsBoot
Match result
Warnings
```

Acción:

```text
CONFIRM_DISK_BINDING
```

## 35. Web/API futura

Diseñar:

```text
GET  /api/system/disks
GET  /api/cases/{case_id}/dsms/{dsm_id}/disk-candidates
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/propose
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/confirm
GET  /api/cases/{case_id}/dsms/{dsm_id}/disk-binding
POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/revalidate
```

State-changing requiere CSRF.

## 36. Auditoría futura

Eventos:

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

## 37. Prueba real permitida

Se permite consultar metadata real de discos con comandos read-only.

No:

- abrir PhysicalDrive;
- leer sectores;
- montar/desmontar;
- modificar atributos;
- inicializar;
- formatear;
- adquirir.

Si hay medio de laboratorio, solo observar metadata.

## 38. Cierre sin candidato read-only real

Si no existe disco externo read-only disponible, R07 puede cerrarse si:

- parser y correlaciones se validan con discos actuales;
- candidato read-only se cubre con mocks/fixtures;
- se documenta que la observación real `IsReadOnly=True` queda para R07.1/pre-R08.

No inventar observación real.

## 39. Tests

Baseline:

```text
203 passed
```

Final:

```text
203 passed
```

o más si se agregan utilidades legítimas.

## 40. Entregable obligatorio

Crear:

```text
DISK_BINDING_CAPABILITIES.md
```

Debe incluir:

```text
BASELINE
WINDOWS
POWERSHELL
STORAGE MODULE
GET-DISK COMMAND
GET-DISK REAL OUTPUT SHAPE
GET-PHYSICALDISK
WIN32_DISKDRIVE
DISK NUMBER ↔ PHYSICALDRIVE
ENCODING
LATENCY
PRIVILEGES
FIELD PROVENANCE
DISK SNAPSHOT MODEL
FORENSIC CANDIDATE POLICY
GET-DISK LIMITATIONS
DSM DATA AVAILABLE
MATCHING MODEL
SERIAL POLICY
CAPACITY POLICY
AMBIGUITY POLICY
BINDING MODEL
REBINDING POLICY
REVALIDATION POLICY
HUMAN GATE
DATABASE DESIGN
WEB FLOW
API CONTRACT
POLICY ENGINE IMPACT
STATE MACHINE IMPACT
DEPENDENCIES FOR R07.1
RISKS
BLOCKERS
```

## 41. Criterio de aceptación

R07 queda COMPLETO si:

- baseline verde;
- PowerShell real identificado;
- Storage Module real identificado;
- Get-Disk real probado;
- propiedades reales documentadas;
- Get-PhysicalDisk comparado;
- Win32_DiskDrive comparado;
- Disk Number ↔ PhysicalDrive verificado o bloqueado;
- encoding y latencia observados;
- privilegios observados;
- DiskSnapshot definido;
- regla de candidato definida;
- limitación de discos dinámicos documentada;
- datos DSM reales inspeccionados;
- matching definido;
- binding humano definido;
- revalidación definida;
- persistencia recomendada;
- API/Web/Human Gate diseñados;
- ningún disco modificado;
- PhysicalDrive no abierto;
- no ewfacquire;
- suite verde.

Estado:

```text
DISK_BINDING_CAPABILITIES_VERIFIED
```

o:

```text
DISK_BINDING_BLOCKED
```

## 42. Reporte final obligatorio

```text
SPRINT R07:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
WINDOWS:
...
POWERSHELL:
Executable:
Version:
Edition:
STORAGE MODULE:
...
GET-DISK:
Command:
Version/Source:
Execution:
Latency:
Encoding:
GET-DISK FIELDS OBSERVED:
...
GET-PHYSICALDISK:
...
WIN32_DISKDRIVE:
...
DISK NUMBER ↔ PHYSICALDRIVE:
VERIFIED / NOT VERIFIED
Evidence:
...
DYNAMIC DISK LIMITATION:
...
PRIVILEGES:
...
DISK SNAPSHOT:
...
FORENSIC CANDIDATE POLICY:
...
REAL READ-ONLY EXTERNAL CANDIDATE OBSERVED:
YES / NO
DSM FIELDS AVAILABLE:
...
DSM ↔ DISK MATCHING:
...
SERIAL POLICY:
...
CAPACITY POLICY:
...
AMBIGUITY POLICY:
...
BINDING MODEL:
...
REBINDING:
...
REVALIDATION:
...
HUMAN GATE:
...
DATABASE RECOMMENDATION:
...
WEB FLOW:
...
API:
...
POLICY ENGINE:
...
STATE MACHINE:
...
DEPENDENCIES FOR R07.1:
...
FILES CREATED:
...
FILES MODIFIED:
...
POSTGRESQL MODIFIED:
NO
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
TESTS FINAL:
...
RISKS:
...
BLOCKERS:
...
STATUS:
DISK_BINDING_CAPABILITIES_VERIFIED / DISK_BINDING_BLOCKED
```

## 43. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. identifica PowerShell y Storage Module reales;
4. inspecciona ayuda local;
5. ejecuta solo comandos read-only;
6. captura salida estructurada de Get-Disk;
7. compara Get-PhysicalDisk;
8. compara Win32_DiskDrive;
9. valida Disk Number ↔ PhysicalDrive sin abrir el dispositivo;
10. mide encoding y latencia;
11. inspecciona campos DSM reales;
12. diseña matching;
13. diseña binding humano;
14. diseña revalidación;
15. diseña persistencia/API/Web/Policies;
16. crea `DISK_BINDING_CAPABILITIES.md`;
17. ejecuta suite final;
18. entrega reporte;
19. detente;
20. NO inicies R07.1;
21. NO inicies R08.

Comienza ahora.
