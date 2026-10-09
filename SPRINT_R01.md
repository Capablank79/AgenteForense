# SPRINT_R01 — Investigación real de PostgreSQL y diseño de persistencia

## 1. Objetivo

Investigar y documentar el entorno PostgreSQL REAL instalado en la estación Windows del proyecto AGENTE FORENSE y, con base únicamente en hechos observados, definir el contrato técnico de persistencia que será implementado en el sprint siguiente.

Este sprint es deliberadamente de **investigación y diseño verificable**.

NO debe crear todavía el esquema productivo del Agente Forense.

La razón es la regla permanente del proyecto:

> No fijar requisitos técnicos sobre una herramienta sin conocer primero la versión, instalación, comportamiento y capacidades reales.

Resultado esperado:

```text
POSTGRES_CAPABILITIES_VERIFIED
```

o, ante incompatibilidad/material faltante:

```text
POSTGRES_CAPABILITIES_BLOCKED
```

---

## 2. Documentos obligatorios

Antes de cualquier acción, TRAE debe leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R00.md
RECONSTRUCTION_STATUS.md
SPRINT_R01.md
```

También debe revisar el informe final real de R00.

No usar los sprints históricos `SPRINT_01...SPRINT_05.1` como baseline ejecutable.

---

## 3. Baseline real heredado de R00

Estado informado al cierre de R00:

```text
REPOSITORY:
J:\AgenteForense\AgenteForense

BRANCH:
main

COMMIT:
e1bf43316000f3cea2c997655c41247d8d3edb1f

SOURCE_CODE_PREVIOUS:
ABSENT

TEST_SUITE_PREVIOUS:
ABSENT

PYTHON_PRIMARY:
Python 3.10.11
C:\Program Files\Python310\python.exe

PYTHON_ALSO_DETECTED:
Python 3.12.9

TESTS:
8 passed

CASES_MODIFIED:
NO

FORENSIC_OPERATIONS_EXECUTED:
NO

STATUS:
RECONSTRUCTION_BASELINE_READY
```

Antes de investigar PostgreSQL:

1. ejecutar `git status`;
2. confirmar branch `main`;
3. ejecutar la suite completa;
4. registrar resultado real;
5. detenerse si R00 presenta regresión.

No asumir que el commit sigue siendo el mismo si hubo cambios legítimos posteriores.

---

## 4. Gobierno documental

Existe una transición entre documentación histórica y arquitectura nueva.

Antes de fijar cualquier diseño de persistencia, TRAE debe identificar en:

```text
PROMPT_MAESTRO.md
```

referencias históricas incompatibles con el estado actual, especialmente:

```text
G:\
rutas antiguas
ZIP conceptual
supuestos de código perdido
supuestos de suite histórica
```

NO reescribir silenciosamente el historial.

Entregar una lista:

```text
DOCUMENTATION_CONFLICTS_FOUND:
- ...
```

y una propuesta concreta de actualización del Prompt Maestro para la reconstrucción.

En este sprint, salvo instrucción explícita adicional, NO modificar todavía `PROMPT_MAESTRO.md`; documentar el delta requerido.

---

# 5. Investigación PostgreSQL obligatoria

## 5.1 Detectar instalación real

Investigar sin instalar ni actualizar nada.

Registrar:

```text
PostgreSQL version
psql version
installation path
service name
service status
server executable path
data directory if discoverable safely
```

Usar fuentes locales reales.

Ejemplos de inspección aceptables, ajustados al entorno real:

```text
where psql
psql --version
Get-Service *postgres*
Get-CimInstance Win32_Service
```

No inventar rutas.

No detener ni reiniciar el servicio.

---

## 5.2 Puerto y escucha

Determinar:

```text
port
listen_addresses
localhost availability
IPv4/IPv6 behavior
```

Preferir inspección local y mecanismos no invasivos.

Si el servidor está escuchando fuera de localhost:

- registrarlo;
- NO cambiarlo todavía;
- evaluar riesgo para el futuro backend local.

---

## 5.3 Autenticación

Determinar el mecanismo real aplicable al proyecto:

```text
SCRAM-SHA-256
MD5 legacy
SSPI
trust
password
otro
```

Inspeccionar, si es accesible sin exponer secretos:

```text
pg_hba.conf
postgresql.conf
```

Nunca imprimir ni versionar contraseñas.

Nunca almacenar credenciales en:

```text
.py
.md
git
tests
case.json
logs
```

---

## 5.4 Roles

Descubrir, únicamente si existen credenciales/autorización local válida:

- roles existentes relevantes;
- si existe un rol apropiado para una aplicación;
- privilegios efectivos;
- capacidad de crear base/schema;
- capacidad de crear tablas;
- capacidad de ejecutar migrations.

No modificar roles todavía.

No cambiar passwords.

No crear superusuarios.

---

## 5.5 Bases existentes

Enumerar bases disponibles si el acceso autorizado lo permite.

Registrar:

```text
database name
owner
encoding
collation
ctype/locale
```

No leer tablas de aplicaciones ajenas salvo que sea imprescindible para evitar colisiones de nombres.

No modificar ninguna base existente.

---

## 5.6 Encoding y locale

Determinar:

```text
server_encoding
client_encoding
lc_collate
lc_ctype
timezone
```

Evaluar compatibilidad con:

- texto español;
- nombres propios;
- rutas Windows;
- caracteres acentuados;
- documentos OCR;
- timestamps auditables.

---

## 5.7 Timezone

Definir qué entrega realmente PostgreSQL y qué estrategia futura conviene.

El diseño deberá distinguir:

```text
TIMESTAMP REAL DEL EVENTO
ZONA HORARIA
REPRESENTACIÓN EN UI
```

No fijar todavía una política final si no se ha validado el comportamiento real.

Recomendación a evaluar:

```text
timestamptz
```

para eventos/auditoría.

---

## 5.8 Extensiones instaladas/disponibles

Consultar únicamente si está autorizado.

Determinar al menos si están disponibles o instaladas extensiones potencialmente relevantes:

```text
pgcrypto
uuid-ossp
vector / pgvector
```

No instalar ninguna extensión en este sprint.

No asumir que `pgvector` existe.

La futura RAG puede usar otro almacenamiento si PostgreSQL no dispone de capacidades vectoriales adecuadas.

---

# 6. Python ↔ PostgreSQL

Investigar el entorno Python 3.10.11 real.

Determinar si existe actualmente un driver PostgreSQL compatible, por ejemplo:

```text
psycopg
psycopg2
asyncpg
```

No instalar dependencias automáticamente salvo que el sprint sea ampliado mediante decisión explícita.

Registrar:

```text
DRIVER_DETECTED
VERSION
PYTHON_COMPATIBILITY
```

Si no existe driver:

```text
DRIVER_STATUS = NOT_INSTALLED
```

Eso NO es fallo del sprint.

Debe producir una recomendación para el sprint de implementación.

---

# 7. Decisión de arquitectura de persistencia

Con hechos ya verificados, proponer el contrato para el sprint de implementación.

## 7.1 PostgreSQL

PostgreSQL será la memoria estructurada global de:

```text
cases
nues
species
dsms
documents metadata
photos metadata
hashes
acquisitions
verification
axiom jobs
results
reports
workflow state
feedback
audit events
tool versions
```

NO guardar la E01 dentro de PostgreSQL.

---

## 7.2 File Store

Diseñar el File Store, sin crear aún estructura productiva.

Debe poder almacenar:

```text
petitorios originales
fotografías originales
metadata derivada
XLS/XLSX
logs
informes DOCX
Portable Case
RAR
exportaciones
archivos auxiliares
```

La E01 permanece en:

```text
ADQUISICION
```

y PostgreSQL guarda su referencia.

Determinar la futura raíz recomendada basándose en el entorno real de `J:`.

No tocar `casos/` durante este sprint.

---

## 7.3 E01

Contrato mínimo futuro:

```text
e01_filename
relative_path
size_bytes
hashes
acquisition_status
verification_status
created_at
verified_at
ewfacquire_version
ewfverify_version
dsm_id
```

No crear ni leer E01 en R01.

---

## 7.4 Archivos

Proponer una tabla lógica futura `files` con campos equivalentes a:

```text
id
case_id
file_role
original_filename
stored_filename
relative_path
size_bytes
sha256
mime_type
created_at
source
integrity_status
```

No fijar tipos SQL definitivos hasta conocer capacidades reales del servidor.

---

# 8. Diseño relacional conceptual

El diseño debe soportar:

```text
CASE / RUC
└── NUE
    └── ESPECIE
        └── DSM
```

Cardinalidades mínimas:

```text
1 RUC -> N NUE
1 NUE -> N ESPECIE
1 ESPECIE -> N DSM
```

Debe contemplar:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

y no bloquear futuras asociaciones:

```text
PETITORIO
FOTOS
ADQUISICIÓN
AXIOM
RESULTADOS
INFORME
```

---

# 9. Auditoría futura

Diseñar conceptualmente una tabla append-only:

```text
audit_events
```

Campos candidatos:

```text
id
timestamp
case_id
nue_id
species_id
dsm_id
actor
module
tool
tool_version
event_type
action
source
destination
previous_state
new_state
result
exit_code
error
details
human_confirmation
```

No implementar todavía triggers complejos.

Definir qué eventos deberán ser inmutables a nivel de aplicación.

---

# 10. Seguridad de credenciales

El informe debe especificar el mecanismo recomendado para credenciales.

Debe cumplir:

- nunca versionar credenciales;
- nunca imprimir password en logs;
- nunca guardar password en `case.json`;
- nunca guardar password en Markdown;
- preferir variables de entorno/configuración local segura;
- utilizar un rol dedicado con mínimo privilegio en el sprint de implementación;
- no usar superuser para ejecución normal.

No crear `.env` con secretos reales dentro del repositorio.

---

# 11. Backup y recuperación

Investigar las herramientas locales disponibles:

```text
pg_dump
pg_restore
```

Registrar versiones y rutas.

No ejecutar backup de bases ajenas.

Diseñar estrategia futura para:

```text
PostgreSQL backup
File Store backup
case.json portability
rebuild index
```

La pérdida de PostgreSQL NO debe significar pérdida definitiva del significado forense de cada caso.

---

# 12. No realizar en R01

Prohibido:

- crear esquema productivo;
- crear tablas productivas;
- migrar datos;
- escribir en `casos/`;
- leer evidencia;
- acceder a `PhysicalDrive`;
- ejecutar `ewfacquire`;
- ejecutar `ewfverify`;
- iniciar AXIOM;
- iniciar Ollama;
- ejecutar OCR;
- crear servidor web;
- crear RUC real;
- crear NUE real;
- generar E01;
- generar informe;
- instalar PostgreSQL;
- actualizar PostgreSQL;
- reiniciar PostgreSQL;
- cambiar `postgresql.conf`;
- cambiar `pg_hba.conf`;
- crear usuarios con secretos no autorizados;
- instalar extensiones PostgreSQL.

---

# 13. Tests

Antes:

```text
pytest
```

Baseline esperado según cierre de R00:

```text
8 passed
```

Registrar valor real.

Este sprint puede agregar tests únicamente si crea utilidades de inspección puramente no invasivas.

No es obligatorio crear código nuevo.

Al final:

```text
pytest
```

Debe conservarse el baseline sin regresiones.

---

# 14. Entregable técnico obligatorio

Crear:

```text
POSTGRESQL_CAPABILITIES.md
```

Debe contener como mínimo:

```text
POSTGRESQL_VERSION
PSQL_VERSION
INSTALLATION_PATH
SERVICE_NAME
SERVICE_STATUS
SERVER_PORT
LISTEN_ADDRESSES
AUTH_METHOD
DATABASES_OBSERVED
ROLE_STRATEGY
SERVER_ENCODING
CLIENT_ENCODING
COLLATION
TIMEZONE
EXTENSIONS_AVAILABLE
PYTHON_DRIVER_STATUS
PG_DUMP_STATUS
PG_RESTORE_STATUS
FILE_STORE_RECOMMENDATION
SECURITY_NOTES
BACKUP_RECOMMENDATION
RISKS
BLOCKERS
IMPLEMENTATION_RECOMMENDATION
```

No incluir secretos.

---

# 15. Criterio de aceptación

R01 queda COMPLETO únicamente si:

- baseline R00 sigue íntegro;
- PostgreSQL instalado fue identificado realmente;
- versión real registrada;
- servicio real identificado;
- puerto real identificado;
- autenticación caracterizada;
- encoding/locale caracterizados;
- herramientas `psql`, `pg_dump`, `pg_restore` caracterizadas;
- driver Python existente o ausente correctamente documentado;
- File Store futuro diseñado;
- modelo relacional conceptual diseñado;
- seguridad de credenciales definida;
- ningún dato forense fue tocado;
- PostgreSQL no fue modificado;
- no se inventaron capacidades;
- `POSTGRESQL_CAPABILITIES.md` fue creado;
- tests finales pasan.

Estado final:

```text
POSTGRES_CAPABILITIES_VERIFIED
```

Si falta información material indispensable:

```text
POSTGRES_CAPABILITIES_BLOCKED
```

y documentar exactamente qué falta.

---

# 16. Después de R01

NO implementar la base todavía.

NO iniciar R01.1.

El informe de R01 será revisado primero.

Solo con datos reales se redactará:

```text
SPRINT_R01_1 — Implementación PostgreSQL + File Store
```

---

# 17. Reporte final obligatorio de TRAE

```text
SPRINT R01:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE R00:
...

TESTS ANTES:
...

REPOSITORY:
...

COMMIT INICIAL:
...

POSTGRESQL:
Version:
Path:
Service:
Status:

PSQL:
Version:
Path:

PORT:
...

LISTEN_ADDRESSES:
...

AUTHENTICATION:
...

DATABASES OBSERVED:
...

ROLES / PERMISSIONS:
...

ENCODING:
...

COLLATION / LOCALE:
...

TIMEZONE:
...

EXTENSIONS:
pgcrypto:
uuid-ossp:
pgvector:

PYTHON:
...

POSTGRES DRIVER:
...

PG_DUMP:
...

PG_RESTORE:
...

FILE STORE DESIGN:
...

RELATIONAL MODEL:
...

AUDIT MODEL:
...

CREDENTIAL STRATEGY:
...

BACKUP STRATEGY:
...

DOCUMENTATION CONFLICTS FOUND:
...

FILES CREATED:
...

FILES MODIFIED:
...

POSTGRESQL MODIFIED:
NO / SI

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

WEB SERVER:
NO / SI

TESTS FINAL:
...

RISKS:
...

BLOCKERS:
...

IMPLEMENTATION RECOMMENDATION:
...

STATUS:
POSTGRES_CAPABILITIES_VERIFIED / POSTGRES_CAPABILITIES_BLOCKED
```

---

## 18. Instrucción final

TRAE:

1. aplica estrictamente `PROMPT_MAESTRO.md`;
2. aplica estrictamente `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. toma R00 como único baseline técnico vigente;
4. investiga PostgreSQL sin modificarlo;
5. no inventes versión, rutas, roles, puertos ni capacidades;
6. no uses secretos en archivos o logs;
7. diseña persistencia con base en hechos observados;
8. crea `POSTGRESQL_CAPABILITIES.md`;
9. ejecuta tests finales;
10. entrega el reporte;
11. detente;
12. no inicies R01.1.

Comienza ahora.
