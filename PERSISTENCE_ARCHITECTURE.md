# Arquitectura de Persistencia — Agente Forense (Sprint R01.1)

## 1. Resumen Ejecutivo
El presente documento describe la arquitectura final de la capa de persistencia real del sistema **AGENTE FORENSE**, implementada y verificada exitosamente en el Sprint R01.1. Esta arquitectura conecta el dominio Python con una base de datos relacional PostgreSQL 18.6 dedicada y un almacenamiento de archivos en disco (**File Store**) estrictamente aislado.

## 2. Componentes Principales

```text
                               +----------------------------------+
                               |     AGENTE FORENSE (Python)      |
                               +----------------------------------+
                                  /                            \
                                 /                              \
               +--------------------------------+   +---------------------------------+
               |  Capa de Persistencia (ORM)    |   |      Capa Storage / FileStore   |
               |  SQLAlchemy 2.x + psycopg 3.3   |   |  Hashing SHA-256 / Anti-Traversal|
               +--------------------------------+   +---------------------------------+
                                |                                   |
                                v                                   v
               +--------------------------------+   +---------------------------------+
               |  PostgreSQL 18.6 (Port 5433)   |   |   File Store Controlado         |
               |  DB: agente_forense_db         |   |   (Directorios de Prueba/Casos) |
               |  Schema: forensic              |   |   Sin tocar evidencia real      |
               +--------------------------------+   +---------------------------------+
```

### 2.1 Instancia y Rol de Base de Datos PostgreSQL
- **Instancia**: PostgreSQL 18.6 corriendo exclusivamente en `127.0.0.1:5433` (`service: postgresql-x64-18`).
- **Base de Datos**: `agente_forense_db`.
- **Rol de Aplicación**: `agente_forense_app` con permisos de mínimo privilegio:
  - `LOGIN` con autenticación `SCRAM-SHA-256`.
  - `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOREPLICATION`.
  - Privilegios limitados exclusivamente a `forensic.*`.

### 2.2 Esquema Relacional (`forensic`)
Todas las tablas del sistema residen aisladas bajo el esquema `forensic`:
1. `cases`: Registro principal de expedientes / causas forenses (`ruc` con restricción `UNIQUE`).
2. `nues`: Numerales Únicos de Evidencia (`case_id` + `nue_number` con restricción `UNIQUE`).
3. `species`: Especies/Muestras físicas asociadas a una NUE (`storage_relation IN ('SELF_STORAGE', 'CONTAINED_STORAGE')`).
4. `dsms`: Dispositivos de Almacenamiento Masivo asociados a una especie (`capacity_bytes >= 0`).
5. `files`: Registro de metadatos de archivos controlados (`file_role`, `sha256`, `size_bytes >= 0`).
6. `documents`: Metadatos documentales especializados (Petitorios, Informes).
7. `photos`: Metadatos de fijación fotográfica.
8. `hashes`: Registro multi-algoritmo de comprobaciones de integridad.
9. `case_events`: Trazabilidad de transiciones de workflow por caso.
10. `audit_events`: Registro de auditoría append-only a nivel de aplicación (sin operaciones UPDATE/DELETE).
11. `tool_versions`: Registro de versiones exactas de ejecutables e infraestructura utilizada.
12. `schema_migrations`: Registro idempotente de scripts DDL aplicados.

### 2.3 Seguridad e Integridad Relacional
- **Relaciones con `ON DELETE RESTRICT`**: Todas las FKs entre entidades forenses principales impiden borrados en cascada accidentales.
- **Auditoría Append-Only**: La API `AuditRepository` únicamente implementa el método `append()`. No existen métodos `update()` ni `delete()` para la bitácora de auditoría.
- **Timestamps**: Todos los campos temporales emplean `TIMESTAMPTZ` (UTC awareness).

### 2.4 File Store y Seguridad de Storage
- **Módulo `agente_forense.storage`**:
  - `FileStore`: Administra copias y almacenamiento seguro en directorios aislados.
  - `paths`: Bloquea activamente Path Traversal (`..`, `/`, `\`), unidades relativas/absolutas y nombres reservados de Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
  - `hashing`: Cálculo de SHA-256 en bloques de 64KB en formato hexadecimal minúsculas.
  - **Verificación Pre y Post Copy**: Si el hash post-copia difiere del origen, el archivo corrupto es eliminado y se emite `SafetyViolationError`.

### 2.5 Contrato de Sincronización con `case.json`
- **PostgreSQL**: Funciona como la memoria relacional central e índice operacional global.
- **`case.json`**: Representa el snapshot portátil e inmutable por caso.
- **`CaseSnapshotRepository`**: Define la interfaz preliminar que permite exportar datos desde la base de datos relacional hacia estructuras compatibles con el snapshot portátil de dominio.

## 3. Verificación de Seguridad y Tests
- **Suite de Pruebas**: 45 tests automatizados pasados exitosamente en `pytest`.
- **Aislamiento**: Pruebas ejecutadas contra PostgreSQL 18.6 (puerto 5433) y archivos temporales sin tocar la carpeta real `casos/` ni la evidencia física.
- **Resguardo y Backup**: Verificado con `pg_dump -Fc` de la base de datos sintética.
