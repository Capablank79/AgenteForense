# SPRINT_R08_1 — Implementación del Motor de Adquisición E01 con ewfacquire

## 1. Objetivo

Implementar el motor productivo de adquisición física E01 del AGENTE FORENSE sobre las capacidades verificadas en R08, manteniendo seguridad fail-closed, trazabilidad, revalidación del origen, Human Gate y persistencia durable del job.

Flujo:

```text
ACQUISITION_READY
→ PRE-FLIGHT
→ REVALIDATE DSM ↔ PhysicalDrive
→ VALIDATE DESTINATION
→ BUILD COMMAND
→ HUMAN GATE
→ START JOB
→ ACQUIRING
→ MONITOR
→ INSPECT OUTPUT
→ ACQUISITION_COMPLETED
```

R08.1 implementa ejecución real-capable, pero las pruebas automatizadas NO usarán `PhysicalDrive` real.

El sprint debe quedar listo para una prueba física controlada posterior.

Estado esperado:

```text
EWF_ACQUISITION_ENGINE_READY
```

No marcar `ACQUISITION_VERIFIED`; eso corresponde a R09.

---

## 2. Documentación obligatoria

Leer completos antes de modificar código:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md

SPRINT_R04.md
SPRINT_R07.md
SPRINT_R07_1.md
SPRINT_R08.md
SPRINT_R08_1.md

ORCHESTRATION_ARCHITECTURE.md
STATE_MACHINE.md
POLICY_ENGINE.md
DISK_BINDING_ARCHITECTURE.md
DISK_BINDING_SCHEMA.md
EWFACQUIRE_CAPABILITIES.md
```

Revisar reportes finales R07, R07.1 y R08.

---

## 3. Baseline

Esperado:

```text
Python: 3.10.11
Windows: Windows 10 Pro build 19045
PostgreSQL: 18.6
Tests: 208 passed
R07.1: DISK_BINDING_READY
R08: EWFACQUIRE_CAPABILITIES_VERIFIED
```

Ejecutar:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe -m pytest
```

Si hay regresión:

```text
DETENER
DOCUMENTAR
NO IMPLEMENTAR
```

---

## 4. Binario autorizado

Usar exactamente:

```text
J:\AgenteForense\ewftools-x64\ewfacquire.exe
```

Versión verificada:

```text
ewfacquire 20230405
```

SHA-256 verificado en R08:

```text
3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791
```

Antes de cada ejecución real-capable:

- confirmar que el archivo existe;
- recalcular SHA-256;
- comparar con el hash esperado/configurado;
- si cambia, bloquear.

Error:

```text
EWFACQUIRE_BINARY_CHANGED
```

---

## 5. Configuración obligatoria

Formato:

```text
encase6
```

Compresión:

```text
-c best
```

No usar `fast` como default.

Segmentación:

```text
-S 0
```

Objetivo:

```text
single E01
```

Modo no interactivo:

```text
-u
```

Hash nativo:

```text
MD5 default
SHA256 adicional mediante -d sha256
```

No inventar flags.

---

## 6. Paquete acquisition

Crear paquete equivalente:

```text
src/agente_forense/acquisition/
    __init__.py
    models.py
    errors.py
    capabilities.py
    preflight.py
    destination.py
    command_builder.py
    runner.py
    jobs.py
    output_parser.py
    artifacts.py
    service.py
```

Puede ajustarse a la arquitectura real.

No colocar lógica crítica dentro de routes.

---

## 7. EwfAcquireCommandBuilder

Implementar clase cerrada y testeable.

Entrada:

```text
case context
DSM
confirmed disk binding
validated destination
verified capabilities
metadata fields
```

Salida:

```text
List[str]
```

Nunca string de shell.

Nunca `shell=True`.

No aceptar flags libres desde Web/API.

---

## 8. Comando base

El builder debe reflejar capacidades verificadas.

Conceptualmente:

```text
ewfacquire.exe
-u
-f encase6
-c best
-d sha256
-S 0
-t <target_basename>
-C <case_number>
-E <evidence_number>
-e <examiner>
-D <description>
-N <notes>
<source>
```

IMPORTANTE:

La sintaxis exacta debe corresponder al help real capturado en R08.

Si algún metadata flag no tiene valor real disponible:

- omitirlo si es opcional;
- no inventar contenido.

---

## 9. Source

Fuente exclusivamente:

```text
\\.\PhysicalDriveN
```

tomada desde un binding `CONFIRMED` y `CURRENT`.

Nunca aceptar:

```text
E:\
F:\
partición
volumen lógico
carpeta
```

---

## 10. DSM requerido

Toda adquisición debe tener:

```text
case_id
nue
species
dsm_id
binding_id
```

No adquirir PhysicalDrive huérfano.

---

## 11. Revalidación inmediata del origen

Justo antes de `Popen`:

reconsultar Windows y comparar contra el binding confirmado.

Verificar:

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

Condiciones obligatorias:

```text
IsReadOnly=True
IsSystem=False
IsBoot=False
```

Cualquier cambio crítico:

```text
SOURCE_CHANGED
```

Bloquear antes de iniciar proceso.

---

## 12. Privilegios

Antes de start real:

detectar si el proceso tiene permisos suficientes para abrir el dispositivo físico.

No auto-elevar.

Si falta privilegio:

```text
ADMIN_PRIVILEGES_REQUIRED
```

Detener antes de ejecutar.

---

## 13. Validación de destino

Implementar:

```text
exists
is directory
writable
filesystem known
free bytes
physical disk resolved
source disk != destination disk
target basename absent
```

No formatear ni preparar automáticamente.

---

## 14. Regla de espacio

Distinguir dos conceptos.

### Requisito técnico base

```text
destination_free_bytes >= source_size_bytes
```

→ suficiente para escenario sin compresión.

### Margen operacional

Puede existir:

```text
safety_margin_ratio
```

pero:

- debe ser configurable;
- debe documentarse;
- no debe confundirse con requisito de ewfacquire;
- no usar 1.05 como verdad forense fija.

Si `free < source_size`:

```text
SPACE_BELOW_RAW_SIZE
```

La política vigente debe bloquear para R08.1 salvo que exista una decisión posterior formalizada.

No confiar en compresión para declarar espacio suficiente.

---

## 15. Filesystem

Detectar filesystem real.

Bloquear FAT32 si el E01 único esperado puede exceder su límite de archivo.

No hardcodear otras incompatibilidades sin justificación.

---

## 16. Mismo disco físico

Resolver el disco físico del destino.

Si:

```text
source_physical_drive == destination_physical_drive
```

bloquear sin override:

```text
DESTINATION_ON_SOURCE_DISK
```

---

## 17. Target path

Nombre oficial:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>
```

Pasar a `-t` SIN `.E01`.

ewfacquire agregará extensión.

Target final esperado:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

---

## 18. Collision policy

Antes de start, buscar:

```text
.E01
.E02
.E03...
stdout.log
stderr.log
native log
acquisition.json
```

para el target correspondiente.

No sobrescribir.

No borrar.

Error:

```text
ACQUISITION_TARGET_EXISTS
```

---

## 19. Estructura de salida

Usar jerarquía oficial:

```text
ADQUISICION\
└── NUE_<NUE>\
    └── NUE_<NUE>_ESPECIE<n>\
        └── NUE_<NUE>_ESPECIE<n>_DSM<m>\
            ├── NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
            ├── logs\
            ├── hashes\
            └── metadata\
```

No crear estructura paralela en raíz.

---

## 20. Human Gate obligatorio

Antes de start real mostrar:

```text
RUC
NUE
ESPECIE
DSM

PhysicalDrive
FriendlyName
Serial
Size
BusType
IsReadOnly
IsSystem
IsBoot

Destination
Destination physical disk
Filesystem
Free bytes

ewfacquire path
binary SHA256
version
format
compression
segment option
hashes
E01 expected path
```

Confirmación exacta:

```text
ADQUIRIR
```

Cualquier otro input:

```text
ABORTED
```

Registrar confirmación.

---

## 21. No autonomía plena todavía

R08.1 NO cambia el Prompt Maestro.

La adquisición real exige Human Gate explícito.

No implementar auto-start basado solo en policy.

---

## 22. Job persistente

Crear modelo de job persistido.

Campos mínimos:

```text
job_id
case_id
dsm_id
binding_id
status
pid
command_json
stdout_path
stderr_path
native_log_path
started_at
finished_at
exit_code
error_code
created_at
updated_at
```

---

## 23. PostgreSQL

Crear migración nueva:

```text
forensic.acquisition_jobs
```

y si es necesario:

```text
forensic.acquisitions
```

No editar migraciones previas.

`ON DELETE RESTRICT`.

---

## 24. Estado del job

Estados:

```text
PREPARED
WAITING_CONFIRMATION
STARTING
RUNNING
COMPLETED
FAILED
ABORTED
```

Separar job status de case state.

---

## 25. Runner

Usar:

```text
subprocess.Popen
shell=False
```

Redirigir stdout/stderr a archivos.

Capturar:

```text
PID
started_at
finished_at
exit_code
```

No depender del proceso HTTP request.

---

## 26. Browser independence

Cerrar navegador NO debe detener adquisición.

El estado debe poder reconstruirse desde:

```text
PostgreSQL
PID/process state
logs
filesystem
```

---

## 27. Polling

Implementar consulta del job:

```text
GET job
```

con:

```text
state
pid
elapsed
last known output
exit_code
generated artifacts
```

No prometer progreso porcentual si ewfacquire no lo entrega de forma estable.

---

## 28. Cancelación

Implementar cancelación humana explícita.

Flujo:

```text
cancel request
→ terminate controlled
→ wait
→ kill only if necessary and documented
→ ABORTED
```

Preservar artefactos parciales.

No borrar E01 parcial.

---

## 29. Restart / recovery

Si la aplicación reinicia:

- leer jobs RUNNING;
- verificar PID;
- verificar existencia de proceso;
- reconciliar status;
- no inventar resultado.

Estados posibles:

```text
RUNNING
PROCESS_MISSING_REVIEW_REQUIRED
COMPLETED_PENDING_INSPECTION
```

---

## 30. stdout/stderr

Guardar:

```text
logs\stdout.log
logs\stderr.log
```

No perder salida por cierre de navegador.

---

## 31. Native log

Usar `-l` solo según sintaxis real de R08.

Guardar dentro de:

```text
logs\
```

---

## 32. Output parser

Parsear únicamente datos cuya sintaxis haya sido observada.

Puede extraer:

```text
bytes acquired
MD5
SHA256
SUCCESS marker
timestamps si aparecen
```

No depender solo del texto de `SUCCESS`.

---

## 33. Success criteria

Una adquisición se considera `ACQUISITION_COMPLETED` solamente si:

```text
exit_code == 0
E01 exists
E01 size > 0
exactly one E01 segment
no E02/E03...
no critical runner error
source remained valid through pre-start revalidation
```

No marcar VERIFIED.

---

## 34. Unexpected segmentation

Si aparecen:

```text
.E02
.E03
...
```

registrar:

```text
UNEXPECTED_SEGMENTATION
```

No borrar.

No concatenar.

Estado:

```text
FAILED
```

o `REVIEW_REQUIRED` solo si la política vigente lo justifica; por defecto fail-closed.

---

## 35. Hashes

Registrar los hashes reportados por ewfacquire:

```text
MD5
SHA256
```

con provenance:

```text
tool
version
source
method
timestamp
```

No recalcular media hash por otro método en R08.1 salvo necesidad explícita.

---

## 36. acquisition.json

Crear de forma atómica.

Debe incluir:

```text
schema_version
case_id
ruc
nue
species
dsm
binding_id
source_snapshot
destination
ewfacquire
command
format
compression
hashes_requested
segment_strategy
human_confirmation
job_id
pid
started_at
finished_at
exit_code
generated_files
generated_segment_count
reported_hashes
status
errors
tool_versions
```

No guardar secretos.

---

## 37. case.json

Actualizar atómicamente.

Al preparar:

```text
acquisition.status = READY
```

Al start:

```text
ACQUIRING
```

Al éxito:

```text
ACQUISITION_COMPLETED
```

Al fallo:

```text
FAILED
```

Al cancel:

```text
ABORTED
```

Nunca `VERIFIED`.

---

## 38. State Machine

Habilitar:

```text
ACQUISITION_READY
→ ACQUIRING
→ ACQUISITION_COMPLETED
```

y caminos:

```text
ACQUIRING → FAILED
ACQUIRING → ABORTED
```

No avanzar a `ACQUISITION_VERIFIED`.

---

## 39. Policy Engine

Antes de start exigir ALLOW en:

```text
DSM_SELECTED
DISK_BINDING_CONFIRMED
DISK_BINDING_CURRENT
SOURCE_READ_ONLY
SOURCE_NOT_SYSTEM
SOURCE_NOT_BOOT
DESTINATION_VALID
DESTINATION_NOT_SOURCE_DISK
SPACE_SUFFICIENT
TARGET_NOT_EXISTS
EWF_BINARY_VALID
EWF_SINGLE_FILE_CONFIGURED
HUMAN_CONFIRMATION_PRESENT
```

---

## 40. API

Implementar:

```text
GET  /api/cases/{case_id}/dsms/{dsm_id}/acquisition/readiness
POST /api/cases/{case_id}/dsms/{dsm_id}/acquisition/prepare
POST /api/acquisition/jobs/{job_id}/confirm
POST /api/acquisition/jobs/{job_id}/start
GET  /api/acquisition/jobs/{job_id}
POST /api/acquisition/jobs/{job_id}/cancel
```

Mutaciones con CSRF.

---

## 41. Web

Agregar panel de adquisición:

```text
Readiness
Source
Destination
EWF config
Warnings
Human Gate
Job status
Logs
Output artifacts
```

No mostrar botón Start si policy crítica falla.

---

## 42. Auditoría

Registrar:

```text
ACQUISITION_PREPARED
ACQUISITION_CONFIRMATION_REQUESTED
ACQUISITION_CONFIRMED
ACQUISITION_START_REQUESTED
ACQUISITION_STARTED
ACQUISITION_REVALIDATION_FAILED
ACQUISITION_COMPLETED
ACQUISITION_FAILED
ACQUISITION_ABORT_REQUESTED
ACQUISITION_ABORTED
UNEXPECTED_SEGMENTATION
```

Incluir:

```text
tool/version
source
destination
job_id
pid
exit_code
operator
human confirmation
```

---

## 43. No borrar parciales

Ante fallo/cancelación:

- conservar E01 parcial;
- conservar logs;
- conservar acquisition.json;
- conservar stdout/stderr;
- conservar audit.

No cleanup silencioso.

---

## 44. Tests automatizados

No usar `PhysicalDrive` real.

Usar mocks/fake executable/fixtures.

Mantener 208 tests.

Agregar cobertura al menos para:

1. binary exists.
2. binary hash match.
3. binary hash changed.
4. builder uses list args.
5. shell=False.
6. `-u`.
7. encase6.
8. `-c best`.
9. `-d sha256`.
10. `-S 0`.
11. target without extension.
12. physical source format.
13. DSM required.
14. confirmed binding required.
15. current binding required.
16. read-only required.
17. system blocked.
18. boot blocked.
19. destination exists.
20. writable.
21. filesystem captured.
22. FAT32 incompatible large file.
23. same physical disk blocked.
24. target collision.
25. free >= raw passes.
26. free < raw blocks.
27. optional margin does not redefine technical requirement.
28. human gate exact `ADQUIRIR`.
29. wrong confirmation aborts.
30. acquisition job persisted.
31. PID persisted.
32. stdout persisted.
33. stderr persisted.
34. runner success.
35. nonzero exit.
36. missing E01.
37. zero-byte E01.
38. single E01 success.
39. E02 detected.
40. partial preserved.
41. cancel.
42. restart recovery.
43. missing PID review.
44. acquisition.json.
45. hashes parsed.
46. case.json READY.
47. case.json ACQUIRING.
48. case.json COMPLETED.
49. case.json FAILED.
50. case.json ABORTED.
51. audit prepared.
52. audit confirmed.
53. audit started.
54. audit completed.
55. API readiness.
56. prepare CSRF.
57. confirm CSRF.
58. start CSRF.
59. cancel CSRF.
60. Web hides start when blocked.
61. Web shows active job.
62. no ewfverify.
63. no AXIOM.
64. no Ollama.
65. no OpenClaw.
66. no Set-Disk.
67. no DiskPart.
68. no real PhysicalDrive in tests.
69. casos/ real intacto.

---

## 45. Fake ewfacquire

Crear executable/script de prueba que simule:

```text
success
failure
partial file
multiple segments
slow process
cancel
stdout/stderr
hash output
```

Nunca sustituir binario real fuera de tests.

---

## 46. Prueba funcional segura

Se permite prueba end-to-end con archivo sintético normal si ewfacquire admite archivo regular como source y la prueba no involucra evidencia real.

Debe ejecutarse fuera de `casos/` real.

Si no es técnicamente apropiado:

usar fake runner.

No usar `\\.\PhysicalDriveN`.

---

## 47. Prueba física real

R08.1 debe terminar:

```text
READY_FOR_CONTROLLED_REAL_ACQUISITION_TEST
```

pero NO ejecutar adquisición real automáticamente.

La prueba real con write-blocker y medio de laboratorio debe realizarse en sprint de validación separado o bajo instrucción explícita.

---

## 48. Documentación

Crear:

```text
EWF_ACQUISITION_ARCHITECTURE.md
ACQUISITION_JOB_SCHEMA.md
ACQUISITION_JSON_SCHEMA.md
```

---

## 49. Criterio de aceptación

R08.1 queda COMPLETO si:

- baseline verde;
- command builder implementado;
- `best` por defecto;
- `-S 0`;
- SHA256 nativo solicitado;
- binary hash verified;
- preflight completo;
- destination checks;
- origin/destination different physical disks;
- binding revalidation;
- Human Gate;
- job persistente;
- runner durable;
- cancelación;
- recovery;
- logs;
- hashes;
- acquisition.json;
- case.json;
- policies;
- state machine hasta ACQUISITION_COMPLETED;
- API/Web/CSRF;
- parciales preservados;
- no real PhysicalDrive en tests;
- no ewfverify;
- suite verde.

Estado:

```text
EWF_ACQUISITION_ENGINE_READY
```

---

## 50. Reporte final obligatorio

```text
SPRINT R08.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
ACQUISITION MODULE:
...
EWFACQUIRE:
Path:
Version:
SHA256:
Binary hash verified:
...
COMMAND BUILDER:
...
FORMAT:
...
COMPRESSION:
...
HASHES:
...
SEGMENT STRATEGY:
...
PRE-FLIGHT:
...
SOURCE REVALIDATION:
...
DESTINATION:
...
SPACE POLICY:
...
SAME DISK POLICY:
...
TARGET COLLISION:
...
HUMAN GATE:
...
JOB MODEL:
...
DATABASE:
...
RUNNER:
...
CANCEL:
...
RECOVERY:
...
STDOUT/STDERR:
...
NATIVE LOG:
...
OUTPUT PARSER:
...
HASH RESULTS:
...
ACQUISITION.JSON:
...
CASE.JSON:
...
POLICY ENGINE:
...
STATE MACHINE:
...
API:
...
WEB:
...
CSRF:
...
AUDIT:
...
TESTS ADDED:
...
TESTS FINAL:
...
FUNCTIONAL SAFE TEST:
...
READY FOR REAL LAB TEST:
YES / NO

POSTGRESQL MODIFIED:
YES / NO

CASOS/ MODIFIED:
NO

REAL PHYSICALDRIVE OPENED:
NO

REAL ACQUISITION:
NO

SET-DISK:
NO

DISKPART:
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
EWF_ACQUISITION_ENGINE_READY / EWF_ACQUISITION_ENGINE_BLOCKED
```

---

## 51. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. implementa paquete acquisition;
4. implementa binary verifier;
5. implementa command builder con `encase6`, `best`, `sha256`, `-S 0`, `-u`;
6. implementa preflight;
7. integra revalidation R07.1;
8. implementa destination resolver/checks;
9. implementa Human Gate `ADQUIRIR`;
10. implementa job persistente;
11. implementa runner con `Popen` y `shell=False`;
12. implementa cancel/recovery;
13. implementa output parser;
14. implementa acquisition.json/logs/hashes;
15. integra case.json;
16. integra Policy Engine;
17. integra State Machine hasta ACQUISITION_COMPLETED;
18. integra API/Web/CSRF;
19. agrega tests;
20. ejecuta prueba funcional segura sin PhysicalDrive real;
21. ejecuta suite completa;
22. crea documentación;
23. entrega reporte;
24. detente;
25. NO ejecutes adquisición física real;
26. NO inicies R09.

Comienza ahora.
