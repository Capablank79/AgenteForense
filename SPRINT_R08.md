# SPRINT_R08 — Investigación y Validación de ewfacquire para Adquisición E01

## 1. Objetivo
Investigar y validar, sobre el binario REAL instalado, cómo debe integrarse `ewfacquire` en AGENTE FORENSE para crear adquisiciones E01 físicas completas de forma determinista, segura, auditable y compatible con el entorno actual.

Este sprint es de INVESTIGACIÓN, CAPABILITY DISCOVERY, VALIDACIÓN DE FLAGS y DISEÑO.

NO debe ejecutar todavía una adquisición física real.
NO debe leer masivamente ningún `PhysicalDrive`.
NO debe modificar evidencia.

Estado esperado:

```text
EWFACQUIRE_CAPABILITIES_VERIFIED
```

o:

```text
EWFACQUIRE_BLOCKED
```

## 2. Dependencia previa
R08 solo puede comenzar si:

```text
R07.1 = DISK_BINDING_READY
```

Baseline esperado:

```text
208 passed
```

## 3. Documentación obligatoria
Leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R03.md
SPRINT_R04.md
SPRINT_R06_1.md
SPRINT_R07.md
SPRINT_R07_1.md
SPRINT_R08.md
ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
DISK_BINDING_ARCHITECTURE.md
DISK_BINDING_SCHEMA.md
```

Revisar reportes R07 y R07.1.

## 4. Ruta real
Usar la ruta vigente:

```text
J:\AgenteForense\ewftools-x64
```

Localizar:

```text
ewfacquire.exe
ewfverify.exe
```

No mover, reemplazar, actualizar ni descargar binarios.

## 5. Baseline
Registrar Python, Windows, PostgreSQL, Git branch/commit, pytest y estado R07.1.

Ejecutar:

```text
.venv\Scripts\python.exe -m pytest
```

Esperado:

```text
208 passed
```

o más si la suite creció legítimamente.

## 6. Binario real
Registrar de `ewfacquire.exe`:

```text
full path
file size
last modified
SHA-256
```

No modificarlo.

## 7. Versión y help reales
Investigar de forma segura:

```text
ewfacquire.exe -h
ewfacquire.exe --help
ewfacquire.exe -V
ewfacquire.exe --version
```

No asumir qué flag funciona.

Registrar:

```text
exit code
stdout
stderr
encoding
latency
```

Capturar help completo y extraer únicamente opciones realmente soportadas.

## 8. Capability model
Diseñar `EwfAcquireCapabilities` con:

```text
version
supported_formats
default_format
compression_methods
compression_levels
hash_algorithms
segment_size_option
segment_size_units
target_option
case_number_option
evidence_number_option
examiner_option
description_option
notes_option
media_type_option
resume_support
verification_support
stdout_behavior
stderr_behavior
exit_code_behavior
```

Campos no observados = null/unsupported.

## 9. Formato E01
Verificar cómo el binario local selecciona el formato E01/EWF.

No asumir nomenclatura histórica.

## 10. Compresión
Investigar niveles reales soportados.

No asumir `best` si el help usa otra nomenclatura.

Registrar método, nivel y valor CLI exacto.

## 11. Hashes
Investigar algoritmos nativos realmente soportados:

```text
MD5
SHA1
SHA256
otros
```

No exigir SHA-256 si no existe.

Separar media hash de container/file hash.

## 12. Segment size
Investigar:

```text
flag
units
minimum
maximum
default
special values
behavior for no-split si existe
```

No fijar valores antes de conocer límites reales.

## 13. Single-E01
Meta del proyecto:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

R08 debe determinar si la versión local puede garantizar un único E01.

Si no:

```text
SINGLE_E01_NOT_GUARANTEED
```

No inventar workaround.

## 14. Target semantics
Investigar si el target es basename, archivo o directorio y cómo se añade `.E01`.

No duplicar extensión.

## 15. Source syntax
Confirmar que el command builder futuro podrá usar:

```text
\\.\PhysicalDriveN
```

sin ejecutar adquisición real en R08.

## 16. Metadata CLI
Investigar soporte para:

```text
case number
evidence number
examiner
description
notes
media type
```

No mapear campos a flags inexistentes.

## 17. Interactive / stdin
Determinar si puede ejecutarse totalmente no-interactivo.

Si existen prompts obligatorios, documentar orden, valores y defaults.

No automatizar respuestas a ciegas.

## 18. Exit codes
Observar de forma segura:

```text
help/version
invalid option
missing source
invalid target
```

Registrar stdout/stderr y exit codes.

## 19. Encoding / progress / errors
Determinar encoding real y cómo informa:

```text
progress
percentage
bytes
ETA
errors
```

No depender de parser de progreso si el formato no es estable.

## 20. subprocess design
Diseñar ejecución futura:

```text
subprocess.Popen
shell=False
explicit executable
args list
stdout pipe
stderr pipe
stdin controlled only if required
```

## 21. Privilegios
Verificar que help/version funcionen sin elevar.

No abrir PhysicalDrive para probar privilegios.

No elevar automáticamente.

## 22. Destination requirements
Diseñar validaciones:

```text
destination exists
destination writable
filesystem
free bytes
source physical disk != destination physical disk
target path absent
parent directory valid
```

No crear E01 real.

## 23. Filesystem y espacio
Diseñar policy basada en límites reales del filesystem.

FAT32 debe bloquear single-E01 mayor que su límite real.

Conservar:

```text
source_size_bytes
destination_free_bytes
```

No asumir ratio de compresión.

## 24. Same physical disk
Regla crítica:

```text
source PhysicalDrive != destination PhysicalDrive
```

Sin override.

Reutilizar R07.1 para resolver destino físico.

## 25. Target collision
Si ya existen artefactos del target, bloquear.

No sobrescribir ni borrar.

## 26. Revalidation contract
Antes de adquisición futura:

```text
binding confirmed
binding current
IsReadOnly=True
IsSystem=False
IsBoot=False
source identity unchanged
destination still valid
```

Definir contrato exacto con R07.1.

## 27. Human Gate
Mostrar antes de adquisición real:

```text
CASE / NUE / SPECIES / DSM
PhysicalDrive
Model / Serial / Size / Bus
ReadOnly / System / Boot
Destination
Destination physical disk
Filesystem
Free space
E01 target
ewfacquire path
version
format
compression
hashes
segment setting
```

Confirmación humana explícita según Prompt Maestro vigente.

## 28. Política de confirmación
R08 NO cambia la política de confirmación humana del Prompt Maestro.

## 29. Command builder
Diseñar `EwfAcquireCommandBuilder` que devuelva lista de argumentos, nunca string de shell.

## 30. Pruebas seguras
Permitido:

```text
help
version
invalid option
missing argument
fixtures y mocks
```

No usar `\\.\PhysicalDriveN`.

## 31. acquisition.json design
Diseñar:

```text
case_id
dsm_id
binding_id
source_snapshot
destination
ewfacquire_path
ewfacquire_sha256
ewfacquire_version
capabilities
format
compression
hash_algorithms
segment_size
command_redacted
started_at
finished_at
exit_code
generated_files
generated_segment_count
status
```

## 32. Logs
Planificar:

```text
ADQUISICION\...\logs\
agent_acquisition.log
native log if supported
stdout capture
stderr capture
```

## 33. Estados
Diseñar:

```text
ACQUISITION_READY
ACQUIRING
ACQUISITION_COMPLETED
FAILED
ABORTED
```

No marcar `ACQUISITION_VERIFIED`; eso corresponde a R09.

## 34. Artefactos parciales
Si falla una adquisición futura:

- conservar parcial;
- conservar logs;
- conservar metadata;
- no borrar silenciosamente.

## 35. Interrupción
Diseñar cancelación controlada:

```text
interrupt
→ terminate process
→ ABORTED
→ preserve partial
→ audit
```

## 36. Long-running job
Diseñar job persistente:

```text
job_id
pid
state
timestamps
stdout/stderr paths
heartbeat/status
recovery after browser close
```

No usar un thread efímero como única fuente de verdad.

## 37. API/Web futuros
Diseñar:

```text
GET acquisition readiness
POST prepare acquisition
POST confirm acquisition
POST start acquisition
GET acquisition job
POST cancel acquisition
```

No ejecutar start real en R08.

## 38. Audit events
Diseñar:

```text
ACQUISITION_PREPARED
ACQUISITION_CONFIRMATION_REQUESTED
ACQUISITION_CONFIRMED
ACQUISITION_STARTED
ACQUISITION_PROGRESS
ACQUISITION_COMPLETED
ACQUISITION_FAILED
ACQUISITION_ABORTED
UNEXPECTED_SEGMENTATION
```

## 39. Tests
Baseline:

```text
208 passed
```

Final:

```text
208 passed
```

o más.

## 40. Prohibiciones
NO:

- adquisición física real;
- abrir PhysicalDrive;
- leer sectores;
- Set-Disk;
- DiskPart;
- CHKDSK;
- format/init/repair;
- ewfverify;
- AXIOM;
- Ollama;
- OpenClaw;
- modificar `casos/`.

## 41. Entregable
Crear:

```text
EWFACQUIRE_CAPABILITIES.md
```

Debe incluir:

```text
BASELINE
BINARY PATH
BINARY SHA256
VERSION
HELP OUTPUT SUMMARY
SUPPORTED FORMATS
E01 FORMAT
COMPRESSION
HASHES
SEGMENT SIZE
TARGET SEMANTICS
SOURCE SEMANTICS
METADATA FLAGS
INTERACTIVE BEHAVIOR
STDIN
STDOUT
STDERR
ENCODING
EXIT CODES
PROGRESS FORMAT
PRIVILEGES
DESTINATION REQUIREMENTS
SINGLE-E01 FEASIBILITY
COMMAND BUILDER DESIGN
HUMAN GATE
JOB MODEL
ACQUISITION.JSON DESIGN
LOG DESIGN
STATE MACHINE IMPACT
POLICY ENGINE IMPACT
API/WEB DESIGN
DEPENDENCIES FOR R08.1
RISKS
BLOCKERS
```

## 42. Criterio de aceptación
R08 queda COMPLETO si:

- baseline verde;
- binario localizado y hasheado;
- versión real identificada;
- help real capturado;
- flags reales documentados;
- formato E01 identificado;
- compresión/hashes/segmentación documentados;
- target semantics real documentada;
- exit codes y encoding observados;
- single-E01 evaluado;
- command builder diseñado;
- destination policies diseñadas;
- revalidation contract definido;
- Human Gate definido;
- job persistente diseñado;
- acquisition.json/logs definidos;
- ninguna adquisición real;
- PhysicalDrive no abierto;
- suite verde.

Estado:

```text
EWFACQUIRE_CAPABILITIES_VERIFIED
```

o:

```text
EWFACQUIRE_BLOCKED
```

## 43. Reporte final obligatorio

```text
SPRINT R08:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
EWFACQUIRE:
Path:
Exists:
Size:
SHA256:
Version:
HELP COMMAND:
...
HELP EXIT CODE:
...
HELP ENCODING:
...
SUPPORTED FORMATS:
...
E01 FORMAT:
...
COMPRESSION:
...
HASH ALGORITHMS:
...
SEGMENT SIZE:
Flag:
Units:
Minimum:
Maximum:
Default:
Single-file strategy:
TARGET SEMANTICS:
...
SOURCE SEMANTICS:
...
METADATA FLAGS:
...
INTERACTIVE:
YES / NO
Details:
...
STDIN:
...
STDOUT:
...
STDERR:
...
EXIT CODES OBSERVED:
...
PROGRESS FORMAT:
...
PRIVILEGES:
...
DESTINATION VALIDATION:
...
SINGLE-E01 FEASIBILITY:
...
COMMAND BUILDER:
...
REVALIDATION WITH R07.1:
...
HUMAN GATE:
...
JOB MODEL:
...
ACQUISITION.JSON:
...
LOG DESIGN:
...
POLICY ENGINE:
...
STATE MACHINE:
...
API/WEB:
...
DEPENDENCIES FOR R08.1:
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
REAL ACQUISITION:
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
EWFACQUIRE_CAPABILITIES_VERIFIED / EWFACQUIRE_BLOCKED
```

## 44. Instrucción final
TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. localiza `ewfacquire.exe`;
4. calcula SHA-256;
5. obtiene versión y help reales;
6. documenta flags;
7. valida formato E01;
8. valida compresión;
9. valida hashes;
10. valida segment size;
11. valida target semantics;
12. observa exit codes/encoding/progress;
13. diseña command builder;
14. diseña destination policies;
15. integra contrato de revalidación R07.1;
16. diseña Human Gate;
17. diseña persisted job model;
18. crea `EWFACQUIRE_CAPABILITIES.md`;
19. ejecuta suite final;
20. entrega reporte;
21. detente;
22. NO ejecutes adquisición real;
23. NO inicies R08.1;
24. NO inicies R09.

Comienza ahora.
