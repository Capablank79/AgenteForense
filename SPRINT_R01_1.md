# SPRINT_R01_1 — Implementación PostgreSQL + File Store + Persistencia Base

## 1. Objetivo

Implementar por primera vez la capa de persistencia REAL del proyecto AGENTE FORENSE sobre la instalación PostgreSQL ya investigada y validada en Sprint R01.

Este sprint crea:

- base de datos dedicada;
- rol de aplicación de mínimo privilegio;
- esquema relacional inicial;
- migraciones SQL versionadas;
- capa Python de conexión/repositorios;
- File Store controlado;
- hashing SHA-256;
- auditoría append-only a nivel de aplicación;
- pruebas automatizadas;
- pruebas de integración PostgreSQL;
- contrato de sincronización futura con `case.json`.

Este sprint NO crea casos forenses reales y NO toca evidencia.

Estado final esperado:

```text
PERSISTENCE_FOUNDATION_READY
```

---

# 2. Fuentes obligatorias

Antes de modificar código o PostgreSQL, TRAE debe leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R00.md
SPRINT_R01.md
RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
SPRINT_R01_1.md
```

También debe revisar los informes finales reales de R00 y R01.

La regla permanente es obligatoria.

---

# 3. Baseline confirmado

## 3.1 Repositorio

```text
J:\AgenteForense\AgenteForense
```

Baseline R00/R01 conocido:

```text
BRANCH:
main

R00 COMMIT BASE:
e1bf43316000f3cea2c997655c41247d8d3edb1f

PYTHON:
3.10.11
C:\Program Files\Python310\python.exe

TESTS:
8 passed
```

Antes de cambios:

```text
git status
git branch --show-current
git log -1 --oneline
pytest
```

Registrar estado real.

Si existe regresión previa:

```text
DETENER
DOCUMENTAR
NO IMPLEMENTAR
```

---

# 4. PostgreSQL real confirmado en R01

Usar exclusivamente la instancia:

```text
PostgreSQL: 18.6
Service: postgresql-x64-18
Port: 5433
Host de aplicación: 127.0.0.1
Encoding: UTF-8
Timezone: America/Santiago
Authentication: scram-sha-256
```

NO utilizar accidentalmente:

```text
PostgreSQL 14.0
Port 5432
AccessData
```

Toda configuración del proyecto debe fijar explícitamente:

```text
host=127.0.0.1
port=5433
```

Nunca depender del puerto por defecto.

---

# 5. Riesgo de escucha externa

R01 detectó:

```text
listen_addresses = '*'
```

Este sprint:

- NO modifica `postgresql.conf`;
- NO reinicia PostgreSQL;
- NO altera `pg_hba.conf`.

La aplicación debe conectarse únicamente a:

```text
127.0.0.1:5433
```

Registrar el riesgo para un sprint posterior de hardening.

---

# 6. Gobierno documental

Antes de implementar:

1. inspeccionar `PROMPT_MAESTRO.md`;
2. comprobar que las reglas de seguridad, trazabilidad y no invención siguen siendo compatibles;
3. documentar las referencias históricas a `G:\` que no representen la ruta operativa actual;
4. no reescribir historia silenciosamente.

Si existe conflicto entre una referencia histórica y el entorno actual:

```text
PROMPT_MAESTRO
→ principio vigente

ROADMAP + R00/R01 reales
→ implementación actual

histórico
→ conservar como histórico
```

No eliminar reglas forenses vigentes.

---

# 7. Entorno Python aislado

R00 utilizó Python del sistema.

En R01.1 se debe establecer un entorno reproducible para desarrollo.

Preferir:

```text
J:\AgenteForense\AgenteForense\.venv
```

con:

```text
C:\Program Files\Python310\python.exe -m venv .venv
```

Verificar primero que la creación de venv funciona.

No usar Python 3.12.9 accidentalmente.

Después:

```text
.venv\Scripts\python.exe --version
```

debe mostrar Python 3.10.x.

---

# 8. Dependencias

## 8.1 Requerida

R01 determinó que no existe driver PostgreSQL Python.

Instalar dentro de `.venv`:

```text
psycopg[binary]
```

Solo después de confirmar disponibilidad real del paquete.

Registrar versión instalada.

## 8.2 SQLAlchemy

R01 observó:

```text
SQLAlchemy 2.0.49
```

pero fuera del nuevo entorno puede no estar disponible.

Determinar si se utilizará SQLAlchemy.

### Decisión preferida

Usar:

```text
SQLAlchemy 2.x
+
psycopg 3
```

si ambas dependencias pueden instalarse correctamente en `.venv`.

Motivos:

- modelo relacional explícito;
- transacciones;
- separación repositorio/dominio;
- tests;
- compatibilidad PostgreSQL;
- futura evolución.

No agregar frameworks innecesarios.

## 8.3 Migraciones

En este sprint preferir migraciones SQL explícitas y versionadas:

```text
migrations\
  0001_initial_schema.sql
```

No agregar Alembic todavía salvo necesidad técnica demostrada.

---

# 9. Gestión de credenciales

Nunca:

- password en Git;
- password en `.py`;
- password en Markdown;
- password en test;
- password en `case.json`;
- password en logs.

`.gitignore` debe incluir y mantener:

```text
.env
.env.*
!.env.example
```

Puede crearse:

```text
.env.example
```

SIN secreto real:

```text
AGENTE_FORENSE_DB_HOST=127.0.0.1
AGENTE_FORENSE_DB_PORT=5433
AGENTE_FORENSE_DB_NAME=agente_forense_db
AGENTE_FORENSE_DB_USER=agente_forense_app
AGENTE_FORENSE_DB_PASSWORD=
```

El password real debe proporcionarse localmente durante aprovisionamiento y no quedar impreso.

---

# 10. Aprovisionamiento PostgreSQL

## 10.1 Base

Crear:

```text
agente_forense_db
```

sobre PostgreSQL 18.6 / puerto 5433.

## 10.2 Rol

Crear:

```text
agente_forense_app
```

Reglas:

- `LOGIN`;
- password SCRAM;
- NO SUPERUSER;
- NO CREATEDB;
- NO CREATEROLE;
- NO REPLICATION;
- acceso únicamente a `agente_forense_db`;
- mínimo privilegio necesario.

## 10.3 Separación de propietario y aplicación

Preferir, si el entorno lo permite sin complejidad innecesaria:

```text
owner/migration role
≠
application runtime role
```

Pero NO crear roles adicionales si no son necesarios todavía.

Como mínimo:

- la aplicación no debe operar como `postgres`;
- el rol runtime no debe ser superuser.

Documentar decisión real.

---

# 11. Esquema SQL inicial

Usar esquema dedicado:

```text
forensic
```

Evitar dispersar tablas en `public` si no es necesario.

Configurar permisos explícitos.

---

# 12. Tipos y claves

## 12.1 Identificadores internos

Usar UUID para claves internas si PostgreSQL 18.6 permite el mecanismo elegido sin extensión adicional innecesaria.

Antes de fijarlo:

- comprobar funciones UUID disponibles en PostgreSQL 18;
- no asumir `uuid-ossp` obligatorio;
- no instalar extensiones si no son necesarias.

Si se usa UUID:

```text
UUID
```

como PK interna.

Los identificadores periciales como RUC/NUE NO sustituyen claves internas.

## 12.2 Timestamps

Usar:

```text
TIMESTAMPTZ
```

para eventos.

No almacenar timestamps críticos como texto.

## 12.3 JSON

`JSONB` puede utilizarse para detalles secundarios/auditoría cuando sea apropiado.

No usar JSONB para evitar modelar relaciones principales.

---

# 13. Tablas iniciales obligatorias

Crear al menos:

```text
forensic.cases
forensic.nues
forensic.species
forensic.dsms
forensic.files
forensic.documents
forensic.photos
forensic.hashes
forensic.case_events
forensic.audit_events
forensic.tool_versions
```

---

# 14. `cases`

Campos mínimos conceptuales:

```text
id
ruc
status
requesting_unit
requesting_rut
request_type
case_root
created_at
updated_at
```

Reglas:

- `ruc` UNIQUE cuando exista;
- no inventar validación jurídica del RUC;
- permitir estado inicial sin petitorio completo si el workflow futuro lo necesita.

No implementar todavía lógica OCR.

---

# 15. `nues`

Campos mínimos:

```text
id
case_id
nue_number
description_from_petition
status
created_at
updated_at
```

Restricción:

```text
UNIQUE(case_id, nue_number)
```

---

# 16. `species`

Campos mínimos:

```text
id
nue_id
species_number
label
description
storage_relation
status
created_at
updated_at
```

`storage_relation` debe admitir explícitamente:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

No permitir valores arbitrarios si se define CHECK/enum.

Restricción:

```text
UNIQUE(nue_id, species_number)
```

---

# 17. `dsms`

Campos mínimos:

```text
id
species_id
dsm_number
label
same_physical_object_as_species
device_type
brand
model
serial
capacity_bytes
status
created_at
updated_at
```

Restricción:

```text
UNIQUE(species_id, dsm_number)
```

No exigir marca/modelo/serial si aún no se conocen.

---

# 18. `files`

Tabla general para archivos controlados por el sistema.

Campos mínimos:

```text
id
case_id
nue_id nullable
species_id nullable
dsm_id nullable
file_role
original_filename
stored_filename
relative_path
mime_type
size_bytes
sha256
integrity_status
source
created_at
updated_at
```

Reglas:

- `relative_path`, no ruta absoluta como contrato portable;
- SHA-256 lowercase/normalizado;
- `size_bytes >= 0`;
- no almacenar bytes de E01 en PostgreSQL.

Roles futuros:

```text
PETITION
PHOTO
E01
AXIOM_EXPORT
PROCESS_SHEET
PORTABLE
RAR
REPORT
LOG
METADATA
OTHER
```

No es obligatorio implementar todos los workflows todavía.

---

# 19. `documents`

Metadata documental especializada.

Campos conceptuales:

```text
id
file_id
document_type
ocr_status
ocr_text nullable
created_at
updated_at
```

Tipos futuros:

```text
PETITION
REPORT
OTHER
```

No ejecutar OCR todavía.

---

# 20. `photos`

Metadata de fotografía.

Campos:

```text
id
file_id
photo_type
classification_status
created_at
updated_at
```

No implementar visión todavía.

---

# 21. `hashes`

Debe permitir múltiples algoritmos y múltiples objetos.

Campos mínimos:

```text
id
file_id nullable
case_id nullable
dsm_id nullable
algorithm
hash_value
source
verification_status
created_at
```

No fabricar hashes.

En R01.1, el único hash realmente calculado puede ser SHA-256 de archivos mock creados por tests.

---

# 22. `tool_versions`

Campos mínimos:

```text
id
tool_name
tool_version
executable_path
observed_at
details
```

Puede registrar inicialmente:

```text
PostgreSQL
psql
Python
psycopg
SQLAlchemy
```

No registrar herramientas que no fueron realmente inspeccionadas.

---

# 23. `case_events`

Registro de eventos de workflow por caso.

Campos:

```text
id
case_id
event_type
previous_state
new_state
result
created_at
details JSONB
```

No implementar todavía la State Machine completa de R04.

Esta tabla prepara persistencia para ella.

---

# 24. `audit_events`

Modelo append-only a nivel aplicación.

Campos mínimos:

```text
id
created_at
case_id nullable
nue_id nullable
species_id nullable
dsm_id nullable
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
human_confirmation
details JSONB
```

Regla:

- aplicación puede INSERT;
- repositorio normal NO ofrece UPDATE/DELETE;
- tests deben comprobarlo a nivel de API/repository.

No declarar inmutabilidad criptográfica todavía.

---

# 25. Relaciones y borrado

Preferir:

```text
ON DELETE RESTRICT
```

para entidades forenses.

Evitar `CASCADE` destructivo en jerarquía principal salvo justificación explícita.

El sistema no debe poder borrar accidentalmente un RUC y arrastrar todo el caso.

En tests/desarrollo, la limpieza de fixtures debe realizarse de forma controlada y separada de APIs productivas.

---

# 26. File Store

## 26.1 Raíz

La raíz lógica actual:

```text
J:\AgenteForense\AgenteForense\casos
```

PERO:

durante este sprint NO tocar casos reales.

Para tests usar exclusivamente un directorio temporal fuera de casos reales, por ejemplo generado por pytest:

```text
%TEMP%\agente_forense_tests\...
```

## 26.2 Servicio

Implementar un componente desacoplado:

```text
FileStore
```

Responsabilidades:

- recibir archivo fuente controlado;
- calcular SHA-256;
- obtener tamaño;
- validar nombre seguro;
- evitar path traversal;
- almacenar/copy en destino de prueba;
- devolver metadata estructurada;
- no sobrescribir silenciosamente;
- verificar hash post-copy.

## 26.3 Originales

Para documentos/fotos futuros:

- preservar bytes originales;
- no recomprimir;
- no modificar metadata;
- derivaciones futuras deben ser copias separadas.

---

# 27. Seguridad de paths

Implementar pruebas para:

```text
..
..\..
absolute paths
UNC inesperado
drive switching
reserved Windows names
NUL
CON
PRN
AUX
COM1
LPT1
```

No permitir escape de File Store.

---

# 28. Configuración Python

Crear configuración explícita para DB:

```text
AGENTE_FORENSE_DB_HOST
AGENTE_FORENSE_DB_PORT
AGENTE_FORENSE_DB_NAME
AGENTE_FORENSE_DB_USER
AGENTE_FORENSE_DB_PASSWORD
```

Defaults permitidos únicamente para valores no secretos:

```text
HOST=127.0.0.1
PORT=5433
DB_NAME=agente_forense_db
DB_USER=agente_forense_app
```

Password:

```text
NO DEFAULT
```

Si falta:

```text
ConfigurationError
```

---

# 29. Paquete Python sugerido

Extender estructura a:

```text
src\
  agente_forense\
    persistence\
      __init__.py
      config.py
      database.py
      models.py
      repositories.py
      migrations.py
    storage\
      __init__.py
      filestore.py
      hashing.py
      paths.py
```

Los nombres pueden ajustarse si TRAE encuentra una estructura más coherente.

No crear archivo monolítico.

---

# 30. Capa de acceso

La lógica de dominio no debe ejecutar SQL directamente.

Exponer repositorios/servicios tipados, por ejemplo:

```text
CaseRepository
NueRepository
SpeciesRepository
DsmRepository
FileRepository
AuditRepository
ToolVersionRepository
```

No implementar CRUD destructivo completo.

Priorizar:

```text
create
get
list
update controlado
append event
```

---

# 31. Transacciones

Operaciones que involucren varias tablas deben ser atómicas.

Ejemplo test:

```text
crear case
crear NUE
error creando species
→ rollback completo
```

No permitir estructuras parcialmente persistidas por error.

---

# 32. `case.json`

En R01.1 NO implementar todavía sincronización completa bidireccional.

Crear contrato/interfaz futura:

```text
CaseSnapshotRepository
```

o equivalente.

Documentar claramente:

```text
PostgreSQL = índice/memoria operacional global
case.json = snapshot portable por caso
```

La implementación efectiva de sincronización se realizará junto con el modelo de dominio R03, salvo que una parte mínima sea necesaria para tests.

---

# 33. Datos de prueba

Crear SOLO datos sintéticos.

Ejemplo:

```text
RUC_TEST_0001
NUE_TEST_0001
ESPECIE1
DSM1
```

No usar:

- RUC real;
- NUE real;
- fotografías reales;
- petitorios reales;
- E01 real;
- datos de `casos/`.

---

# 34. Integración PostgreSQL de prueba

Las pruebas de integración deben usar la base dedicada creada para el proyecto y datos claramente marcados como test.

Preferir aislamiento mediante:

- transacción con rollback; o
- schema temporal/test dedicado;

sin tocar datos futuros reales.

No crear una segunda instancia PostgreSQL.

---

# 35. Migración inicial

Crear:

```text
migrations\0001_initial_schema.sql
```

Debe ser:

- determinista;
- revisable;
- idempotencia controlada según estrategia elegida;
- sin secretos;
- sin datos forenses;
- versionado en Git.

Registrar versión del esquema, por ejemplo mediante:

```text
forensic.schema_migrations
```

si se considera necesario.

---

# 36. Backup smoke test

Después de crear la base/esquema:

1. insertar únicamente datos sintéticos;
2. ejecutar `pg_dump -Fc` de `agente_forense_db`;
3. verificar que el backup se crea y tiene tamaño > 0;
4. NO restaurar sobre la base productiva.

Puede restaurarse únicamente en una base temporal de test si se puede hacer de forma segura y sin complejidad.

Eliminar/custodiar el backup de test según política de desarrollo.

No incluir dumps en Git.

---

# 37. `.gitignore`

Confirmar inclusión de:

```text
.venv/
.env
.env.*
*.dump
*.backup
casos/
__pycache__/
.pytest_cache/
*.pyc
```

No ignorar `.env.example`.

---

# 38. Tests obligatorios

Mantener los 8 tests R00.

Agregar tests, como mínimo, para:

1. config default host = 127.0.0.1;
2. config default port = 5433;
3. password faltante -> ConfigurationError;
4. no se usa puerto 5432 por default;
5. conexión con PostgreSQL 18.6 dedicada;
6. esquema `forensic` existe;
7. tablas esperadas existen;
8. rol app no es superuser;
9. rol app no tiene CREATEDB;
10. rol app no tiene CREATEROLE;
11. crear case sintético;
12. RUC duplicado bloqueado;
13. múltiples NUE por case;
14. NUE duplicada por case bloqueada;
15. múltiples species;
16. storage_relation inválido rechazado;
17. múltiples DSM;
18. DSM duplicado por species bloqueado;
19. transaction rollback;
20. file metadata insert;
21. SHA-256 correcto;
22. hash post-copy coincide;
23. path traversal bloqueado;
24. archivo existente no overwrite silencioso;
25. audit event insert;
26. AuditRepository no expone delete;
27. AuditRepository no expone update;
28. foreign keys activas;
29. no cascade destructivo inesperado;
30. timestamps timezone-aware;
31. `tool_versions` registra herramienta real de test;
32. tests no acceden `casos/`;
33. tests no acceden PhysicalDrive;
34. no EWF;
35. no AXIOM;
36. no Ollama.

Agregar más si el diseño real lo requiere.

---

# 39. Prueba funcional sintética

Crear dentro de una transacción/test controlado:

```text
CASE:
RUC_TEST_R011

NUE:
NUE_TEST_001

SPECIES:
1
SELF_STORAGE

DSM:
1
same_physical_object_as_species = true
```

Crear un archivo de texto sintético temporal:

```text
test_document.txt
```

Pasarlo por FileStore de prueba.

Verificar:

- ruta segura;
- tamaño;
- SHA-256;
- metadata en DB;
- relaciones;
- auditoría;
- rollback/cleanup.

No tocar `casos/`.

---

# 40. Seguridad

Confirmar:

```text
DB HOST:
127.0.0.1

DB PORT:
5433

APP ROLE:
not superuser

PASSWORD:
not logged

CASES:
untouched

EVIDENCE:
unread

PHYSICALDRIVE:
not accessed
```

---

# 41. No realizar

Prohibido en R01.1:

- usar PostgreSQL 14 / puerto 5432;
- modificar AccessData;
- modificar `listen_addresses`;
- modificar `pg_hba.conf`;
- reiniciar PostgreSQL salvo fallo operacional y autorización explícita;
- instalar pgvector;
- ejecutar OCR;
- iniciar web server;
- crear interfaz web;
- leer petitorio real;
- leer fotos reales;
- leer evidencia;
- crear RUC real;
- acceder PhysicalDrive;
- ejecutar ewfacquire;
- ejecutar ewfverify;
- ejecutar AXIOM;
- ejecutar Ollama;
- crear E01;
- generar Portable;
- ejecutar RAR;
- generar Word;
- tocar `casos/`.

---

# 42. Documentación

Crear:

```text
PERSISTENCE_ARCHITECTURE.md
```

Debe documentar:

- PostgreSQL 18.6;
- 127.0.0.1:5433;
- nombre DB;
- rol de aplicación;
- schema;
- tablas;
- relaciones;
- File Store;
- credenciales;
- transacciones;
- auditoría;
- backup;
- E01 fuera de DB;
- papel futuro de `case.json`.

No incluir password.

---

# 43. Criterio de cierre

R01.1 queda COMPLETO si:

- baseline R00/R01 intacto;
- `.venv` Python 3.10.x reproducible;
- psycopg funcional;
- PostgreSQL 18.6 usado explícitamente;
- `agente_forense_db` creada;
- rol `agente_forense_app` creado sin superuser;
- schema `forensic` creado;
- migration inicial versionada;
- tablas base creadas;
- constraints verificadas;
- repositorios Python funcionan;
- transacciones funcionan;
- FileStore de pruebas funciona;
- SHA-256 funciona;
- auditoría append-only a nivel API;
- backup smoke test realizado;
- documentación creada;
- tests completos verdes;
- `casos/` intacto;
- ninguna operación forense real ejecutada;
- ningún secreto versionado.

Estado final:

```text
PERSISTENCE_FOUNDATION_READY
```

Si falla un requisito material:

```text
PERSISTENCE_FOUNDATION_BLOCKED
```

---

# 44. Git

Antes de commit:

```text
git status
pytest
```

Revisar manualmente staged files.

Confirmar ausencia de:

```text
.env
passwords
dumps
backups
casos/
E01
fotos reales
petitorios reales
```

Commit recomendado:

```text
Sprint R01.1: implementa persistencia PostgreSQL base
```

Push solo si:

- tests verdes;
- no secretos;
- no evidencia;
- criterios completos.

---

# 45. Reporte final obligatorio

```text
SPRINT R01.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...

TESTS BEFORE:
...

PYTHON VENV:
...

DEPENDENCIES:
psycopg:
SQLAlchemy:

POSTGRES INSTANCE:
Version:
Host:
Port:

DATABASE:
...

APPLICATION ROLE:
...

ROLE PRIVILEGES:
Superuser:
CreateDB:
CreateRole:

SCHEMA:
...

MIGRATION:
...

TABLES:
...

CONSTRAINTS:
...

RELATIONSHIPS:
...

FILE STORE:
...

HASHING:
...

TRANSACTIONS:
...

AUDIT:
...

BACKUP SMOKE TEST:
...

CASE.JSON CONTRACT:
...

FILES CREATED:
...

FILES MODIFIED:
...

TESTS ADDED:
...

TESTS FINAL:
...

GIT STATUS:
...

SECRETS VERSIONED:
NO / SI

POSTGRES 14 / PORT 5432 MODIFIED:
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

RISKS / LIMITATIONS:
...

STATUS:
PERSISTENCE_FOUNDATION_READY / PERSISTENCE_FOUNDATION_BLOCKED
```

---

# 46. Instrucción final

TRAE:

1. lee toda la documentación vigente;
2. ejecuta baseline;
3. usa solo PostgreSQL 18.6 en `127.0.0.1:5433`;
4. crea entorno Python 3.10 aislado;
5. instala solo dependencias justificadas;
6. no expongas secretos;
7. crea rol mínimo y DB dedicada;
8. implementa migración inicial;
9. implementa capa Python modular;
10. implementa FileStore solo con datos sintéticos;
11. agrega tests;
12. verifica backup;
13. revisa Git;
14. entrega reporte final;
15. detente;
16. NO inicies R02.

Comienza ahora.
